"""Thermal lifecycle adapter over existing R6 state/retention/store interfaces."""
from pathlib import Path
import copy,json,hashlib,os,time
import numpy as np
import thermal  # exact preserved thermal_1d_history_v1 numerical module
from arcana_worldsim.r6.state import DomainStateEnvelope,TimeSupport,SpatialSupport,SupportClass,AuthorityClass
from arcana_worldsim.r6.identity import HistoryId,BranchId,thaw_json
from arcana_worldsim.r6.temporal import HistoricalSnapshot
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.retention import MinimalStateContract,RetentionItem,RetentionAction,InformationRole,MinimalStateExtractionResult,extract_minimal_state

STATIC_KEYS=('schema','context','geometry','initial_T_K','dt_s','CFL_s')
DOMAIN='EXPERIMENTAL_THERMAL_1D'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
 with Path(p).open('xb') as f:f.write(thermal.encoded(x));f.flush();os.fsync(f.fileno())
def binding():
 import arcana_worldsim.r6.state as state
 core=Path(state.__file__).parent
 return dict(adapter={p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))},core={n:sha(core/n) for n in ('state.py','identity.py','store.py','retention.py','temporal.py','provenance.py')},thermal=thermal.source_identity(),runtime=thermal.runtime())

class Extractor:
 adapter_id='THERMAL_CONTROLLER_HISTORY_V1'
 def __init__(self,static_sha):self.static_sha=static_sha
 def extract(self,raw_output,contract):
  return MinimalStateExtractionResult(contract.contract_id,{'dynamic':(raw_output['record'],)},static_identities=(self.static_sha,),omitted_item_ids=('static',))

class ThermalController:
 def __init__(self,root,job):
  self.root=Path(root);self.job=copy.deepcopy(job)
  if job['binding']!=binding():raise ValueError('CONTROLLER_SOURCE_RUNTIME')
  p=self.root/'STATIC.json'
  if not p.is_file() or sha(p)!=job['static_sha256']:raise ValueError('STATIC_REFERENCE')
  self.static=json.loads(p.read_text());self.ctx=self.static['context'];self.store=HistoryStore(self.root/'history')
  self.history_id=str(HistoryId.from_payload({'thermal_controller_static':job['static_sha256'],'binding':job['binding']}));self.branch_id=str(BranchId.from_payload({'history':self.history_id,'scenario':'C028_PRE_FIXED_DIRICHLET'}))
  self.retention=MinimalStateContract(Extractor.adapter_id,(RetentionItem('dynamic',RetentionAction.MATERIALIZE,InformationRole.SYSTEM_MEMORY),RetentionItem('static',RetentionAction.STATIC,InformationRole.SYSTEM_MEMORY,reconstruction_refs=('static:'+job['static_sha256'],))))
  self.state=None;self.last_id=None;self.published_step=-1;self.previous_native=None;self.phase='NEW';self.metrics=[]
 @classmethod
 def create(cls,root,job,static):
  root=Path(root);root.mkdir();dump(root/'STATIC.json',static);return cls(root,job)
 def records(self):
  with self.store.read_view():rows=self.store.find_states(history_id=self.history_id,branch_id=self.branch_id,domain=DOMAIN)
  rows=sorted(rows,key=lambda x:thaw_json(x.value)['dynamic']['step']);parent=None;last=-1
  for r in rows:
   v=thaw_json(r.value);st=v['dynamic']['step']
   if tuple(r.parent_state_ids)!=(() if parent is None else (parent,)) or st<=last or v['static_sha256']!=self.job['static_sha256'] or st not in self.job['snapshot_steps']:raise ValueError('PUBLICATION_CHAIN')
   parent=str(r.state_id);last=st
  return rows
 def restore_record(self,record_id):
  s=copy.deepcopy(self.static);s['ledger']=[];s.update({})
  prev=None;previous_step=0;found=False
  for r in self.records():
   v=thaw_json(r.value);dyn=v['dynamic']
   if v['ledger_start_step']!=previous_step or len(v['ledger_segment'])!=dyn['step']-previous_step:raise ValueError('LEDGER_SEGMENT')
   s.update(copy.deepcopy(dyn));s['ledger'].extend(copy.deepcopy(v['ledger_segment']))
   if s['parent_snapshot_sha256']!=prev or thermal.digest(s)!=v['native_sha256']:raise ValueError('NATIVE_PARENT_OR_DIGEST')
   thermal.validate(s,self.ctx)
   if r.time_support.time_key!=str(s['time_s']) or r.time_support.coordinate_system!='MODEL_SECONDS_SINCE_T0':raise ValueError('CLOCK_ENVELOPE')
   prev=v['native_sha256'];previous_step=s['step']
   if str(r.state_id)==record_id:found=True;break
  if not found:raise ValueError('STATE_NOT_PUBLISHED')
  return s
 def start(self):
  if self.records() or self.phase!='NEW':raise ValueError('ALREADY_STARTED')
  self.state=thermal.initial(self.static['geometry'],self.static['initial_T_K'],self.ctx);self.phase='READY';self.publish();return self
 def recover(self):
  rows=self.records()
  if not rows:raise ValueError('NO_PUBLISHED_STATE')
  self.state=self.restore_record(str(rows[-1].state_id));self.last_id=str(rows[-1].state_id);self.published_step=self.state['step'];self.previous_native=thermal.digest(self.state);self.phase='PUBLISHED';return self
 def advance(self):
  if self.phase!='PUBLISHED':raise ValueError('ADVANCE_REQUIRES_PUBLICATION')
  marks=[x for x in self.job['snapshot_steps'] if x>self.state['step']]
  if not marks:raise ValueError('PLAN_EXHAUSTED')
  start=time.perf_counter()
  while self.state['step']<marks[0]:thermal.step(self.state)
  self.phase='READY';self.metrics.append(dict(service='accepted_steps',wall_s=time.perf_counter()-start,step=self.state['step']));return self
 def publish(self):
  start=time.perf_counter()
  if self.phase!='READY':raise ValueError('PUBLISH_NOT_READY')
  s=self.state;thermal.validate(s,self.ctx)
  if {k:s[k] for k in STATIC_KEYS}!=self.static:raise ValueError('IMMUTABLE_STATIC')
  rows=self.records();actual_parent=str(rows[-1].state_id) if rows else None
  expected_marks=[x for x in self.job['snapshot_steps'] if x>self.published_step]
  if actual_parent!=self.last_id or not expected_marks or s['step']!=expected_marks[0]:raise ValueError('PUBLICATION_ORDER')
  candidate=copy.deepcopy(s);candidate['parent_snapshot_sha256']=self.previous_native
  dyn={k:v for k,v in candidate.items() if k not in STATIC_KEYS and k!='ledger'}
  segment=candidate['ledger'][self.published_step if self.published_step>=0 else 0:]
  prov=ProvenanceRecord.create(activity='EXPERIMENTAL_PRE_THERMAL_CONTROLLER',input_refs=('sha256:'+self.ctx['PRE_DAT_sha256'],),source_refs=('sha256:'+thermal.digest(self.job['binding']),),attributes={'authority':'AUTHORIAL_MODEL_T0_NOT_OBSERVATION','static_sha256':self.job['static_sha256']})
  value=dict(static_sha256=self.job['static_sha256'],dynamic=dyn,ledger_start_step=max(0,self.published_step),ledger_segment=segment,native_sha256=thermal.digest(candidate))
  record=DomainStateEnvelope.create(history_id=self.history_id,branch_id=self.branch_id,domain=DOMAIN,time_support=TimeSupport(str(s['time_s']),'MODEL_SECONDS_SINCE_T0','SNAPSHOT'),spatial_support=SpatialSupport('PRE_C028_VERTICAL_FIXED', (self.ctx['column'],),'545 nodes; local2m boundary spacing'),support_class=SupportClass.DERIVED_SUPPORTED,authority_class=AuthorityClass.DERIVED_AUTHORITY,value=value,uncertainty={'scope':'AUTHORIAL_THERMAL_MODEL; NOT_SCIENTIFIC_VALIDATION'},provenance_ids=(str(prov.record_id),),parent_state_ids=() if self.last_id is None else (self.last_id,),model_derived=True,applicability={'single_column':True,'max_years':10,'experimental':True})
  extracted=extract_minimal_state({'record':record},self.retention,Extractor(self.job['static_sha256']),history_id=self.history_id,branch_id=self.branch_id)
  if extracted.validation_status!='PASS':raise ValueError('EXTRACTION:'+str(extracted.validation_errors))
  snap=HistoricalSnapshot.create(history_id=self.history_id,branch_id=self.branch_id,time_key=str(s['time_s']),domain_ids=(DOMAIN,),state_ids=(str(record.state_id),),authority_refs=('sha256:'+self.job['static_sha256'],),provenance_refs=(str(prov.record_id),),validation_status='EXPERIMENTAL_COMPLETE_STATE',details={'step':s['step'],'column':self.ctx['column'],'model_years':s['time_s']/thermal.YEAR,'interpolated':False})
  self.store.append_transaction((prov,record,snap)) # existing R6 implementation; no new transaction/CAS code
  self.state=candidate;self.last_id=str(record.state_id);self.previous_native=value['native_sha256'];self.published_step=s['step'];self.phase='PUBLISHED'
  self.metrics.append(dict(service='publish_existing_store',step=s['step'],wall_s=time.perf_counter()-start,state_id=self.last_id));return record
 def query(self,column,year,zmin,zmax):
  start=time.perf_counter()
  if not np.isfinite([year,zmin,zmax]).all() or zmin>zmax:raise ValueError('QUERY')
  if column!=self.ctx['column']:return {'status':'COLUMN_NOT_ARCHIVED'}
  rows=self.records();matches=[r for r in rows if thaw_json(r.value)['dynamic']['time_s']/thermal.YEAR==year]
  if not matches:return {'status':'TIME_NOT_ARCHIVED','available_years':[thaw_json(r.value)['dynamic']['time_s']/thermal.YEAR for r in rows],'interpolated':False}
  r=matches[0];s=self.restore_record(str(r.state_id));z=np.array(s['geometry']['z_m']);ids=np.flatnonzero((z>=zmin)&(z<=zmax));hi=s['T_hi_K'];co=s['T_correction_K']
  return dict(status='STORED_NODES' if len(ids) else 'NO_STORED_NODES_IN_INTERVAL',state_id=str(r.state_id),column=column,model_years=year,interpolated=False,nodes=[dict(depth_m=float(z[i]),T_hi_K=hi[i],T_correction_K=co[i],temperature_K_display=float(np.longdouble(hi[i])-co[i])) for i in ids],read_restore_query_s=time.perf_counter()-start)
