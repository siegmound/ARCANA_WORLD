"""Column-general metadata adapter; original numerical kernel and R6 store unchanged."""
from reader import FastController,ReadSession
from adapter import STATIC_KEYS,DOMAIN,Extractor,sha,dump
from adapter import DomainStateEnvelope,TimeSupport,SpatialSupport,SupportClass,AuthorityClass,HistoryId,BranchId,HistoricalSnapshot,ProvenanceRecord,HistoryStore,MinimalStateContract,RetentionItem,RetentionAction,InformationRole,extract_minimal_state
from pathlib import Path
import copy,json,time
import thermal
import adapter as legacy

def source_binding():
 b=legacy.binding();b['adapter']={p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))};b['policy']='THERMAL_CONTROLLER_V2';return b

class ColumnController(FastController):
 def __init__(self,root,job):
  self.root=Path(root);self.job=copy.deepcopy(job)
  if job['binding']!=source_binding():raise ValueError('CONTROLLER_SOURCE_RUNTIME')
  if sha(self.root/'STATIC.json')!=job['static_sha256']:raise ValueError('STATIC_REFERENCE')
  self.static=json.loads((self.root/'STATIC.json').read_text());self.ctx=self.static['context'];self.store=HistoryStore(self.root/'history')
  self.history_id=str(HistoryId.from_payload({'thermal_controller_static':job['static_sha256'],'binding':job['binding']}));self.branch_id=str(BranchId.from_payload({'history':self.history_id,'scenario':self.ctx['column']+'_PRE_FIXED_DIRICHLET'}))
  self.retention=MinimalStateContract(Extractor.adapter_id,(RetentionItem('dynamic',RetentionAction.MATERIALIZE,InformationRole.SYSTEM_MEMORY),RetentionItem('static',RetentionAction.STATIC,InformationRole.SYSTEM_MEMORY,reconstruction_refs=('static:'+job['static_sha256'],))))
  self.state=None;self.last_id=None;self.published_step=-1;self.previous_native=None;self.phase='NEW';self.metrics=[];self._head_rows=None;self._head_view=None;self._head_fp={}
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
  record=DomainStateEnvelope.create(history_id=self.history_id,branch_id=self.branch_id,domain=DOMAIN,time_support=TimeSupport(str(s['time_s']),'MODEL_SECONDS_SINCE_T0','SNAPSHOT'),spatial_support=SpatialSupport('PRE_'+self.ctx['column']+'_VERTICAL_FIXED', (self.ctx['column'],),str(len(self.static['initial_T_K']))+' nodes; local2m boundary spacing'),support_class=SupportClass.DERIVED_SUPPORTED,authority_class=AuthorityClass.DERIVED_AUTHORITY,value=value,uncertainty={'scope':'AUTHORIAL_THERMAL_MODEL; NOT_SCIENTIFIC_VALIDATION'},provenance_ids=(str(prov.record_id),),parent_state_ids=() if self.last_id is None else (self.last_id,),model_derived=True,applicability={'single_column':True,'max_years':10,'experimental':True})
  extracted=extract_minimal_state({'record':record},self.retention,Extractor(self.job['static_sha256']),history_id=self.history_id,branch_id=self.branch_id)
  if extracted.validation_status!='PASS':raise ValueError('EXTRACTION:'+str(extracted.validation_errors))
  snap=HistoricalSnapshot.create(history_id=self.history_id,branch_id=self.branch_id,time_key=str(s['time_s']),domain_ids=(DOMAIN,),state_ids=(str(record.state_id),),authority_refs=('sha256:'+self.job['static_sha256'],),provenance_refs=(str(prov.record_id),),validation_status='EXPERIMENTAL_COMPLETE_STATE',details={'step':s['step'],'column':self.ctx['column'],'model_years':s['time_s']/thermal.YEAR,'interpolated':False})
  self.store.append_transaction((prov,record,snap)) # existing R6 implementation; no new transaction/CAS code
  self.state=candidate;self.last_id=str(record.state_id);self.previous_native=value['native_sha256'];self.published_step=s['step'];self.phase='PUBLISHED'
  self.metrics.append(dict(service='publish_existing_store',step=s['step'],wall_s=time.perf_counter()-start,state_id=self.last_id));
  with self.store.read_view() as view:self._remember(tuple(rows)+(record,),view)
  return record
