"""Pinned R6 temporal-metadata index and byte-accounted deterministic LRU."""
from pathlib import Path
from collections import OrderedDict
import copy,json,sys,time
import numpy as np
import thermal
from reader import ReadSession,stamp,query_state
from adapter import DOMAIN,sha
from arcana_worldsim.r6.identity import thaw_json,HistoryId,BranchId
from column import ColumnController

def policy():return {p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))}
class DenseController(ColumnController):
 def __init__(self,root,job):
  super().__init__(root,job)
  if job['dense_policy_sha256']!=thermal.digest(policy()):raise ValueError('DENSE_POLICY_SOURCE')
  self.history_id=str(HistoryId.from_payload({'base_history':self.history_id,'publication_steps':job['snapshot_steps'],'dense_policy':job['dense_policy_sha256']}));self.branch_id=str(BranchId.from_payload({'history':self.history_id,'column':self.ctx['column']}))

 def restore_record(self,state_id):
  with IndexedSession(self) as s:return s.restore(state_id)

class IndexedSession(ReadSession):
 def __init__(self,controller,budget_bytes=384*1024):
  if type(budget_bytes)is not int or budget_bytes<0:raise ValueError('CACHE_BUDGET')
  self.budget=budget_bytes;super().__init__(controller)
  self.stats.update(evictions=0,skipped_oversize=0,record_reads=0,index_lookups=0,peak_charged_bytes=0)
  self.evicted=[]
 def clear(self):
  super().clear();self.prefix=OrderedDict();self.index=None;self.by_time={};self.by_id={};self.charged=0
 def __enter__(self):
  super().__enter__();self.code_stamps.update({p:stamp(p) for p in Path(__file__).parent.glob('*.py')});return self
 def _charge(self):return sys.getsizeof(self.prefix)-sys.getsizeof(OrderedDict())+sum(sys.getsizeof(k)+sys.getsizeof(v) for k,v in self.prefix.items())
 def _put(self,rid,s):
  blob=thermal.encoded(s);single=OrderedDict([(rid,blob)])
  minimum=sys.getsizeof(single)-sys.getsizeof(OrderedDict())+sys.getsizeof(rid)+sys.getsizeof(blob)
  if minimum>self.budget:self.stats['skipped_oversize']+=1;return
  if rid in self.prefix:del self.prefix[rid]
  while True:
   candidate=OrderedDict(self.prefix.items());candidate[rid]=blob
   predicted=sys.getsizeof(candidate)-sys.getsizeof(OrderedDict())+sum(sys.getsizeof(k)+sys.getsizeof(v) for k,v in candidate.items())
   if predicted<=self.budget:self.prefix=candidate;break
   key,_=self.prefix.popitem(last=False);self.evicted.append(key);self.stats['evictions']+=1
   self.prefix=OrderedDict(self.prefix.items())
  self.charged=self._charge();assert self.charged<=self.budget
  self.stats['peak_charged_bytes']=max(self.stats['peak_charged_bytes'],self.charged)
 def ensure_index(self):
  self._check()
  if self.index is not None:return
  entries=[];paths=[]
  # Existing lighter R6 temporal records, rather than loading every dynamic state body.
  for tr in self.store.temporal_records(role='HISTORICAL_SNAPSHOT'):
   if tr['history_id']!=self.c.history_id or tr['branch_id']!=self.c.branch_id:continue
   detail=tr['details'];ids=tr['state_ids']
   if len(ids)!=1 or ids[0] not in self.view.records['states'] or tr['domain_ids']!=[DOMAIN] or detail['column']!=self.c.ctx['column']:raise ValueError('TEMPORAL_INDEX_SCOPE')
   st=detail['step'];seconds=float(tr['time_key'])
   if type(st)is not int or st not in self.c.job['snapshot_steps'] or seconds!=st*self.static['dt_s'] or detail['model_years']!=seconds/thermal.YEAR:raise ValueError('TEMPORAL_INDEX_CLOCK')
   if tr['authority_refs']!=['sha256:'+self.c.job['static_sha256']]:raise ValueError('TEMPORAL_INDEX_STATIC')
   entries.append(dict(state_id=ids[0],step=st,seconds=seconds,year=seconds/thermal.YEAR,temporal_id=tr['record_id'],provenance=tr['provenance_refs']))
   paths.append(self.c.root/'history/temporal'/(tr['record_id']+'.json'))
  entries.sort(key=lambda x:x['step'])
  if [x['step'] for x in entries]!=self.c.job['snapshot_steps'][:len(entries)] or len({x['state_id'] for x in entries})!=len(entries):raise ValueError('TEMPORAL_INDEX_ORDER')
  self.index=tuple(entries);self.by_time={e['year']:e for e in entries};self.by_id={e['state_id']:i for i,e in enumerate(entries)}
  paths.extend(self.c.root/'history/states'/(e['state_id']+'.json') for e in entries);paths.append(self.c.root/'history/.history_visibility/views'/(self.view.view_id+'.json'))
  self.fingerprints={p:stamp(p) for p in paths};self.stats['full_loads']+=1
 def _apply(self,entry,s,prior_state,prior_native):
  r=self.store.read_state(entry['state_id']);self.stats['record_reads']+=1;v=thaw_json(r.value);dyn=v['dynamic'];last=s.get('step',0)
  if r.history_id!=self.c.history_id or r.branch_id!=self.c.branch_id or r.domain!=DOMAIN or tuple(r.spatial_support.cell_ids)!=(self.c.ctx['column'],) or tuple(r.parent_state_ids)!=(() if prior_state is None else (prior_state,)):raise ValueError('STATE_SCOPE_PARENT')
  if v['static_sha256']!=self.c.job['static_sha256'] or list(r.provenance_ids)!=entry['provenance']:raise ValueError('STATE_REFERENCE')
  if v['ledger_start_step']!=last or len(v['ledger_segment'])!=dyn['step']-last:raise ValueError('LEDGER_SEGMENT')
  s.update(copy.deepcopy(dyn));s['ledger'].extend(copy.deepcopy(v['ledger_segment']))
  if s['step']!=entry['step'] or s['time_s']!=entry['seconds'] or r.time_support.time_key!=str(s['time_s']) or r.time_support.coordinate_system!='MODEL_SECONDS_SINCE_T0':raise ValueError('CLOCK_ENVELOPE')
  if s['parent_snapshot_sha256']!=prior_native or thermal.digest(s)!=v['native_sha256']:raise ValueError('NATIVE_PARENT_OR_DIGEST')
  thermal.validate(s,self.static['context']);self._put(entry['state_id'],s);return s,v['native_sha256']
 def _restore(self,rid):
  if rid not in self.by_id:raise ValueError('STATE_NOT_PUBLISHED_IN_VIEW')
  if rid in self.prefix:
   self.stats['hits']+=1;blob=self.prefix[rid];self.prefix.move_to_end(rid);return json.loads(blob)
  target=self.by_id[rid];prior=[(self.by_id[k],k) for k in self.prefix if self.by_id[k]<target]
  if prior:
   ordinal,key=max(prior);s=json.loads(self.prefix[key]);prev=thermal.digest(s);prior_state=key;begin=ordinal+1;self.prefix.move_to_end(key)
  else:s=copy.deepcopy(self.static);s['ledger']=[];prev=None;prior_state=None;begin=0
  for i in range(begin,target+1):
   e=self.index[i];s,prev=self._apply(e,s,prior_state,prev);prior_state=e['state_id']
  return s
 def restore(self,rid):self.ensure_index();return self._restore(rid)
 def records(self):
  self.ensure_index();return tuple(self.store.read_state(e['state_id']) for e in self.index)
 def query(self,column,year,low,high):
  t=time.perf_counter()
  if not np.isfinite([year,low,high]).all() or low>high:raise ValueError('QUERY')
  if column!=self.c.ctx['column']:return {'status':'COLUMN_NOT_ARCHIVED'}
  self.ensure_index();self.stats['index_lookups']+=1;e=self.by_time.get(year)
  if e is None:return {'status':'TIME_NOT_ARCHIVED','available_years':list(self.by_time),'interpolated':False}
  return query_state(self._restore(e['state_id']),e['state_id'],column,year,low,high,t)
 def force_verify(self):
  super().force_verify();self.ensure_index();s=copy.deepcopy(self.static);s['ledger']=[];prev=parent=None
  for e in self.index:s,prev=self._apply(e,s,parent,prev);parent=e['state_id']
  return len(self.index)
 def cache_report(self):
  return dict(budget_bytes=self.budget,charged_bytes=self._charge(),payload_bytes=sum(len(x) for x in self.prefix.values()),entries=len(self.prefix),peak_charged_bytes=self.stats['peak_charged_bytes'],index_serialized_bytes=len(thermal.encoded(self.index or [])),static_serialized_bytes=len(thermal.encoded(self.static)),stats=copy.deepcopy(self.stats),evicted=list(self.evicted),accounting='incremental OrderedDict + owned keys + bytes buffers by sys.getsizeof; excludes empty container, statics/index, transient decode and returned caller-owned states')
