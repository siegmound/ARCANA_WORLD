"""Logical shared epochs over independent existing R6 thermal controllers/stores."""
from pathlib import Path
import copy,json,time,sys,math
import thermal
from bounded import DenseController,IndexedSession
from reader import stamp,query_state
from adapter import dump,sha
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.state import DomainStateEnvelope,TimeSupport,SpatialSupport,SupportClass,AuthorityClass
from arcana_worldsim.r6.identity import HistoryId,BranchId,thaw_json
from arcana_worldsim.r6.temporal import HistoricalSnapshot
from arcana_worldsim.r6.provenance import ProvenanceRecord
DOMAIN='EXPERIMENTAL_SHARED_THERMAL_EPOCH'
def policy():return {p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))}

class Scheduler:
 @classmethod
 def create(cls,root,plan,statics):
  root=Path(root);root.mkdir();(root/'columns').mkdir();dump(root/'PLAN.json',plan)
  for k,v in plan['columns'].items():DenseController.create(root/'columns'/k,v['job'],statics[k])
  return cls(root,sha(root/'PLAN.json'))
 def __init__(self,root,expected_plan_sha):
  self.root=Path(root)
  if sha(self.root/'PLAN.json')!=expected_plan_sha:raise ValueError('PLAN_SHA')
  self.plan=json.loads((self.root/'PLAN.json').read_text());self.plan_sha=expected_plan_sha
  if self.plan['scheduler_policy_sha256']!=thermal.digest(policy()):raise ValueError('SCHEDULER_SOURCE')
  self.keys=tuple(sorted(self.plan['columns']))
  if self.keys!=('C028','C139') or self.plan['steps']!=564 or self.plan['duration_s']!=10*thermal.YEAR:raise ValueError('PLAN_SCOPE')
  marks=self.plan['snapshot_steps']
  if not marks or any(type(x)is not int for x in marks) or marks!=sorted(set(marks)) or marks[0]!=0 or marks[-1]!=564:raise ValueError('PLAN_SNAPSHOT_ORDER')
  self.controllers={k:DenseController(self.root/'columns'/k,self.plan['columns'][k]['job']) for k in self.keys}
  for k,c in self.controllers.items():
   if c.ctx['column']!=self.plan['columns'][k]['column_id'] or c.ctx['steps']!=564 or c.ctx['duration_s']!=self.plan['duration_s'] or c.static['dt_s']!=self.plan['dt_s'] or c.job['snapshot_steps']!=self.plan['snapshot_steps']:raise ValueError('COLUMN_TIME_OR_IDENTITY')
  if len({c.ctx['column'] for c in self.controllers.values()})!=2:raise ValueError('DUPLICATE_COLUMN')
  self.registry=HistoryStore(self.root/'epochs');self.history_id=str(HistoryId.from_payload({'thermal_scheduler_plan':self.plan_sha}));self.branch_id=str(BranchId.from_payload({'scheduler_history':self.history_id}));self.metrics=[];self.reused_publications=0;self.reused_epochs=0
 def epochs(self,store=None):
  store=self.registry if store is None else store
  with store.read_view():rows=store.find_states(history_id=self.history_id,branch_id=self.branch_id,domain=DOMAIN)
  rows=sorted(rows,key=lambda r:thaw_json(r.value)['step']);parent=None
  for ordinal,r in enumerate(rows):
   v=thaw_json(r.value);step=v['step']
   if ordinal>=len(self.plan['snapshot_steps']) or step!=self.plan['snapshot_steps'][ordinal] or v['plan_sha256']!=self.plan_sha or r.time_support.time_key!=str(step*self.plan['dt_s']) or tuple(r.parent_state_ids)!=(() if parent is None else (parent,)):raise ValueError('EPOCH_ORDER_CLOCK_PARENT')
   if set(v['columns'])!=set(self.keys):raise ValueError('INCOMPLETE_EPOCH_RECORD')
   parent=str(r.state_id)
  return rows
 def _verify_ref(self,k,ref,step,native=None):
  c=self.controllers[k]
  if ref['column_id']!=c.ctx['column'] or ref['static_sha256']!=c.job['static_sha256'] or ref['history_id']!=c.history_id or ref['branch_id']!=c.branch_id:raise ValueError('COLUMN_REFERENCE')
  with c.store.read_view() as view:
   if ref['state_id'] not in view.records['states']:raise ValueError('COLUMN_NOT_COMMITTED')
   r=c.store.read_state(ref['state_id'])
  value=thaw_json(r.value);dyn=value['dynamic']
  if r.history_id!=c.history_id or r.branch_id!=c.branch_id or tuple(r.spatial_support.cell_ids)!=(c.ctx['column'],) or dyn['step']!=step or dyn['time_s']!=step*self.plan['dt_s'] or r.time_support.time_key!=str(dyn['time_s']) or value['native_sha256']!=ref['native_sha256'] or value['static_sha256']!=c.job['static_sha256']:raise ValueError('COLUMN_CLOCK_OR_NATIVE')
  if native is not None:
   thermal.validate(native,c.ctx)
   if native['step']!=step or thermal.digest(native)!=value['native_sha256']:raise ValueError('NATIVE_VERIFICATION')
   expected={k:v for k,v in native.items() if k not in ('schema','context','geometry','initial_T_K','dt_s','CFL_s','ledger')}
   if dyn!=expected or value['ledger_segment']!=native['ledger'][value['ledger_start_step']:]:raise ValueError('PUBLISHED_PAYLOAD')
  return r
 def reconcile(self):
  epochs=self.epochs()
  for r in epochs:
   v=thaw_json(r.value)
   for k in self.keys:self._verify_ref(k,v['columns'][k],v['step'])
  last=thaw_json(epochs[-1].value)['step'] if epochs else -1;idx=len(epochs);nextstep=self.plan['snapshot_steps'][idx] if idx<len(self.plan['snapshot_steps']) else last
  for k,c in self.controllers.items():
   rows=c.records()
   if rows:
    c.recover()
    if c.state['step']<last or c.state['step']>nextstep:raise ValueError('COLUMN_OUTSIDE_RECONCILIATION_WINDOW')
   elif last>=0:raise ValueError('MISSING_PUBLISHED_COLUMN')
  return len(epochs)
 def _ensure_column(self,k,target):
  c=self.controllers[k];rows=c.records();by_step={thaw_json(r.value)['dynamic']['step']:r for r in rows}
  if target in by_step:
   self.reused_publications+=1
   if c.state is None or c.state['step']!=target:c.recover()
   if c.state['step']!=target:raise ValueError('COLUMN_AHEAD')
   return by_step[target]
  if target==0:
   if rows:raise ValueError('MISSING_T0')
   c.start()
  else:
   if c.state is None:c.recover()
   c.advance()
   if c.state['step']!=target:raise ValueError('UNCOORDINATED_ACCEPTED_STEP')
   c.publish()
  return c.store.read_state(c.last_id)
 def register_epoch(self,step):
  t=time.perf_counter();rows=self.epochs();existing=[r for r in rows if thaw_json(r.value)['step']==step]
  if existing:
   v=thaw_json(existing[0].value)
   for k in self.keys:self._verify_ref(k,v['columns'][k],step)
   self.reused_epochs+=1;return 'ALREADY_AVAILABLE'
  if len(rows)>=len(self.plan['snapshot_steps']) or step!=self.plan['snapshot_steps'][len(rows)]:raise ValueError('EPOCH_PUBLICATION_ORDER')
  refs={}
  for k,c in self.controllers.items():
   found=[r for r in c.records() if thaw_json(r.value)['dynamic']['step']==step]
   if len(found)!=1 or c.state is None or c.state['step']!=step:raise ValueError('EPOCH_INCOMPLETE')
   r=found[0];value=thaw_json(r.value)
   with c.store.read_view() as view:viewid=view.view_id
   ref=dict(column_id=c.ctx['column'],state_id=str(r.state_id),native_sha256=value['native_sha256'],static_sha256=c.job['static_sha256'],history_id=c.history_id,branch_id=c.branch_id,verified_column_view=viewid)
   self._verify_ref(k,ref,step,c.state);refs[k]=ref
  prov=ProvenanceRecord.create(activity='EXPERIMENTAL_LOGICAL_THERMAL_EPOCH',source_refs=('sha256:'+self.plan['scheduler_policy_sha256'],),input_refs=('sha256:'+self.plan_sha,),attributes={'cross_column_atomic':False})
  rec=DomainStateEnvelope.create(history_id=self.history_id,branch_id=self.branch_id,domain=DOMAIN,time_support=TimeSupport(str(step*self.plan['dt_s']),'MODEL_SECONDS_SINCE_T0','SNAPSHOT'),spatial_support=SpatialSupport('TWO_INDEPENDENT_PRE_COLUMNS',tuple(c.ctx['column'] for c in self.controllers.values()),'independent vertical supports'),support_class=SupportClass.DERIVED_SUPPORTED,authority_class=AuthorityClass.DERIVED_AUTHORITY,value=dict(step=step,plan_sha256=self.plan_sha,columns=refs,coordination='LOGICAL_COMPLETE_EPOCH_NOT_CROSS_STORE_ATOMIC'),uncertainty={'scope':'EXPERIMENTAL_AUTHORIAL_MODEL'},parent_state_ids=() if not rows else (str(rows[-1].state_id),),provenance_ids=(str(prov.record_id),),model_derived=True,applicability={'scientific_validation':False,'max_model_years':10})
  snap=HistoricalSnapshot.create(history_id=self.history_id,branch_id=self.branch_id,time_key=str(step*self.plan['dt_s']),domain_ids=(DOMAIN,),state_ids=(str(rec.state_id),),validation_status='BOTH_COLUMN_REFERENCES_VERIFIED',details={'step':step,'cross_column_atomic':False})
  self.registry.append_transaction((prov,rec,snap));self.metrics.append(dict(service='register_epoch',step=step,wall_s=time.perf_counter()-t,state_id=str(rec.state_id)));return 'AVAILABLE'
 def run(self,interrupt_after_first=None):
  ordinal=self.reconcile()
  for step in self.plan['snapshot_steps'][ordinal:]:
   for i,k in enumerate(self.keys):
    t=time.perf_counter();self._ensure_column(k,step);self.metrics.append(dict(service='column_ready',column=k,step=step,wall_s=time.perf_counter()-t))
    if i==0 and step==interrupt_after_first:return 'INTERRUPTED_BETWEEN_COLUMNS'
   self.register_epoch(step)
  return 'COMPLETE'

class CoordinatedReader:
 def __init__(self,scheduler,budget_bytes=768*1024):
  if type(budget_bytes)is not int or budget_bytes<0:raise ValueError('AGGREGATE_CACHE_BUDGET')
  self.s=scheduler;self.budget=budget_bytes;self.sessions={};self.active=False;self.registry=HistoryStore(self.s.root/'epochs')
 def __enter__(self):
  self.cm=self.registry.read_view();self.view=self.cm.__enter__();self.active=True
  try:
   n=len(self.s.keys);base,extra=divmod(self.budget,n)
   for i,k in enumerate(self.s.keys):self.sessions[k]=IndexedSession(self.s.controllers[k],base+(i<extra));self.sessions[k].__enter__()
   self._load_epochs();return self
  except BaseException:self.__exit__(*__import__('sys').exc_info());raise
 def _load_epochs(self):
  self.rows=self.s.epochs(self.registry);self.by_step={thaw_json(r.value)['step']:r for r in self.rows};self.fp={self.s.root/'epochs/states'/(str(r.state_id)+'.json'):stamp(self.s.root/'epochs/states'/(str(r.state_id)+'.json')) for r in self.rows};self.source_stamps={p:stamp(p) for p in Path(__file__).parent.glob('*.py')}
 def _check(self):
  if not self.active:raise ValueError('READER_CLOSED')
  if any(stamp(p)!=v for p,v in self.source_stamps.items()):raise ValueError('SCHEDULER_SOURCE_CHANGED')
  if any(stamp(p)!=v for p,v in self.fp.items()):self._load_epochs()
 def refresh(self):
  old=self.view.view_id;self.__exit__(None,None,None);self.__enter__();return old!=self.view.view_id
 def __exit__(self,*args):
  for session in reversed(list(self.sessions.values())):
   if session.active:session.__exit__(*args)
  self.sessions={}
  if self.active:self.cm.__exit__(*args)
  self.active=False
 def cache_report(self):
  per={k:v.cache_report() for k,v in self.sessions.items()};charge=sum(x['charged_bytes'] for x in per.values());upper=sum(x['peak_charged_bytes'] for x in per.values());assert charge<=self.budget and upper<=self.budget
  return dict(total_budget_bytes=self.budget,total_current_charge_bytes=charge,sum_per_column_peak_upper_bound_bytes=upper,per_column=per,allocation='deterministic equal reservations; no borrowing; prefix accounting only, not RSS')
 def query_column(self,key,step,low=0.,high=8.):
  self._check()
  if key not in self.sessions:return {'status':'COLUMN_NOT_SCHEDULED'}
  if type(step)is not int:return {'status':'ACCEPTED_INTEGER_STEP_REQUIRED'}
  session=self.sessions[key];session.ensure_index();entry=session.by_time.get(step*self.s.plan['dt_s']/thermal.YEAR)
  if entry is None:return {'status':'STEP_NOT_ARCHIVED','step':step}
  result=session.query(session.c.ctx['column'],entry['year'],low,high);result.update(step=step,shared_epoch_published=step in self.by_step);self.cache_report();return result
 def query_epoch(self,step,low=0.,high=8.):
  start=time.perf_counter();self._check()
  if not all(math.isfinite(x) for x in (low,high)) or low>high:raise ValueError('DEPTH_QUERY')
  if type(step)is not int or step not in self.s.plan['snapshot_steps']:return {'status':'EPOCH_STEP_NOT_PLANNED','step':step}
  rec=self.by_step.get(step)
  if rec is None:
   ready=[]
   for k,session in self.sessions.items():
    session.ensure_index()
    if step*self.s.plan['dt_s']/thermal.YEAR in session.by_time:ready.append(k)
   status='EPOCH_INCOMPLETE' if 0<len(ready)<len(self.sessions) else ('EPOCH_UNREGISTERED' if ready else 'EPOCH_NOT_IN_VIEW')
   return dict(status=status,step=step,column_publications_present=ready,shared_epoch_published=False,epoch_registry_view=self.view.view_id)
  value=thaw_json(rec.value);answers={}
  for k,session in self.sessions.items():
   ref=value['columns'][k];state=session.restore(ref['state_id'])
   if ref['column_id']!=session.c.ctx['column'] or ref['static_sha256']!=session.c.job['static_sha256'] or ref['history_id']!=session.c.history_id or ref['branch_id']!=session.c.branch_id or thermal.digest(state)!=ref['native_sha256'] or state['step']!=step or state['time_s']!=step*self.s.plan['dt_s']:raise ValueError('COORDINATED_REFERENCE_OR_CLOCK')
   answers[k]=query_state(state,ref['state_id'],ref['column_id'],state['time_s']/thermal.YEAR,low,high,start)
  cache=self.cache_report()
  return dict(status='AVAILABLE',shared_epoch_published=True,coordination='LOGICAL_NOT_CROSS_STORE_ATOMIC',epoch_state_id=str(rec.state_id),epoch_registry_view=self.view.view_id,step=step,time_s=step*self.s.plan['dt_s'],model_years=step*self.s.plan['dt_s']/thermal.YEAR,columns=answers,cache_current_charge_bytes=cache['total_current_charge_bytes'],query_s=time.perf_counter()-start)
