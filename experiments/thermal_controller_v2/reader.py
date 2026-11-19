"""Session-only verified prefix cache on the existing local R6 file store."""
from pathlib import Path
import copy,json,time,sys
import numpy as np
import thermal
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.identity import thaw_json
from adapter import ThermalController as Original,sha,DOMAIN

def stamp(p):
 s=Path(p).stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def query_state(s,state_id,column,year,low,high,started):
 z=np.array(s['geometry']['z_m']);ids=np.flatnonzero((z>=low)&(z<=high));hi=s['T_hi_K'];co=s['T_correction_K']
 return dict(status='STORED_NODES' if len(ids) else 'NO_STORED_NODES_IN_INTERVAL',state_id=state_id,column=column,model_years=year,interpolated=False,nodes=[dict(depth_m=float(z[i]),T_hi_K=hi[i],T_correction_K=co[i],temperature_K_display=float(np.longdouble(hi[i])-co[i])) for i in ids],read_restore_query_s=time.perf_counter()-started)

class ReadSession:
 def __init__(self,controller):
  self.c=controller;self.store=HistoryStore(controller.root/'history');self.stats={'hits':0,'full_loads':0,'invalidations':0};self.active=False
 def __enter__(self):
  self.cm=self.store.read_view();self.view=self.cm.__enter__();self.active=True;self.clear();self._load_static();paths=list(Path(thermal.__file__).parent.glob('*.py'))+list(Path(sys.modules[Original.__module__].__file__).parent.glob('*.py'))+list(Path(__file__).parent.glob('*.py'));self.code_stamps={p:stamp(p) for p in paths};return self
 def clear(self):self.rows=None;self.prefix={};self.fingerprints={}
 def _load_static(self):
  p=self.c.root/'STATIC.json'
  if sha(p)!=self.c.job['static_sha256']:raise ValueError('STATIC_REFERENCE')
  self.static=json.loads(p.read_text());self.static_stamp=stamp(p)
  self.key=(str(self.c.root.resolve()),self.view.view_id,self.c.job['static_sha256'],thermal.digest(self.c.job['binding']))
 def _check(self):
  if not self.active:raise ValueError('SESSION_CLOSED')
  if any(stamp(p)!=v for p,v in self.code_stamps.items()):self.clear();raise ValueError('SESSION_SOURCE_CHANGED')
  if stamp(self.c.root/'STATIC.json')!=self.static_stamp or any(stamp(p)!=v for p,v in self.fingerprints.items()):
   self.stats['invalidations']+=1;self.clear();self._load_static()
 def records(self):
  self._check()
  if self.rows is None:
   rows=sorted(self.store.find_states(history_id=self.c.history_id,branch_id=self.c.branch_id,domain=DOMAIN),key=lambda x:thaw_json(x.value)['dynamic']['step']);parent=None;last=-1
   for r in rows:
    v=thaw_json(r.value);st=v['dynamic']['step']
    if tuple(r.parent_state_ids)!=(() if parent is None else (parent,)) or st<=last or v['static_sha256']!=self.c.job['static_sha256'] or st not in self.c.job['snapshot_steps']:raise ValueError('PUBLICATION_CHAIN')
    parent=str(r.state_id);last=st
   self.rows=tuple(rows);paths=[self.c.root/'history/states'/(str(r.state_id)+'.json') for r in rows]
   paths.append(self.c.root/'history/.history_visibility/views'/(self.view.view_id+'.json'))
   self.fingerprints={p:stamp(p) for p in paths};self.stats['full_loads']+=1
  return self.rows
 def restore(self,state_id):
  rows=self.records()
  if state_id in self.prefix:self.stats['hits']+=1;return copy.deepcopy(self.prefix[state_id])
  s=copy.deepcopy(self.static);s['ledger']=[];prev=None;last=0
  for r in rows:
   rid=str(r.state_id)
   if rid in self.prefix:s=copy.deepcopy(self.prefix[rid]);v=thaw_json(r.value);prev=v['native_sha256'];last=s['step']
   else:
    v=thaw_json(r.value);dyn=v['dynamic']
    if v['ledger_start_step']!=last or len(v['ledger_segment'])!=dyn['step']-last:raise ValueError('LEDGER_SEGMENT')
    s.update(copy.deepcopy(dyn));s['ledger'].extend(copy.deepcopy(v['ledger_segment']))
    if s['parent_snapshot_sha256']!=prev or thermal.digest(s)!=v['native_sha256']:raise ValueError('NATIVE_PARENT_OR_DIGEST')
    thermal.validate(s,self.static['context'])
    if r.time_support.time_key!=str(s['time_s']) or r.time_support.coordinate_system!='MODEL_SECONDS_SINCE_T0':raise ValueError('CLOCK_ENVELOPE')
    self.prefix[rid]=copy.deepcopy(s);prev=v['native_sha256'];last=s['step']
   if rid==state_id:return copy.deepcopy(s)
  raise ValueError('STATE_NOT_PUBLISHED')
 def query(self,column,year,low,high):
  start=time.perf_counter()
  if not np.isfinite([year,low,high]).all() or low>high:raise ValueError('QUERY')
  if column!=self.c.ctx['column']:return {'status':'COLUMN_NOT_ARCHIVED'}
  rows=self.records();matches=[r for r in rows if thaw_json(r.value)['dynamic']['time_s']/thermal.YEAR==year]
  if not matches:return {'status':'TIME_NOT_ARCHIVED','available_years':[thaw_json(r.value)['dynamic']['time_s']/thermal.YEAR for r in rows],'interpolated':False}
  rid=str(matches[0].state_id);return query_state(self.restore(rid),rid,column,year,low,high,start)
 def force_verify(self):self.stats['invalidations']+=1;self.clear();self._load_static()
 def refresh(self):
  old=self.view.view_id;self.cm.__exit__(None,None,None);self.cm=self.store.read_view();self.view=self.cm.__enter__();self.clear();self._load_static();self.stats['invalidations']+=1;return old!=self.view.view_id
 def __exit__(self,*args):
  self.cm.__exit__(*args);self.clear();self.active=False

class FastController(Original):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self._head_rows=None;self._head_view=None;self._head_fp={}
 def records(self):
  with self.store.read_view() as v:
   if self.root/'STATIC.json' in self._head_fp and stamp(self.root/'STATIC.json')!=self._head_fp[self.root/'STATIC.json'] and sha(self.root/'STATIC.json')!=self.job['static_sha256']:raise ValueError('STATIC_REFERENCE')
   if self._head_rows is not None and self._head_view==v.view_id and all(stamp(p)==s for p,s in self._head_fp.items()):return self._head_rows
   rows=super().records();self._remember(rows,v);return rows
 def _remember(self,rows,view):
  self._head_rows=rows;self._head_view=view.view_id;self._head_fp={self.root/'STATIC.json':stamp(self.root/'STATIC.json')}
  self._head_fp.update({self.root/'history/states'/(str(r.state_id)+'.json'):stamp(self.root/'history/states'/(str(r.state_id)+'.json')) for r in rows})
 def publish(self):
  rec=super().publish()
  with self.store.read_view() as view:
   rows=tuple(self._head_rows)+(rec,)
   if {str(x.state_id) for x in rows}==set(view.records['states']):self._remember(rows,view)
   else:self._head_rows=None
  return rec
 def restore_record(self,state_id):
  with ReadSession(self) as s:return s.restore(state_id)
