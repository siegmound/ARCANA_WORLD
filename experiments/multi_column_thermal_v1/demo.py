from pathlib import Path
import argparse,json,time,copy,subprocess,sys,statistics,resource,shutil
import thermal
from adapter import dump,sha
from scheduler import Scheduler,CoordinatedReader,policy
from arcana_worldsim.r6.identity import thaw_json
BASE=Path(__file__).resolve().parents[3]
def storage(root):
 fs=[p for p in Path(root).rglob('*') if p.is_file()];return dict(files=len(fs),logical_bytes=sum(p.stat().st_size for p in fs),allocated_bytes=sum(p.stat().st_blocks*512 for p in fs))
def normalize(q):
 q=copy.deepcopy(q);q.pop('query_s',None)
 for v in q.get('columns',{}).values():v.pop('read_restore_query_s',None)
 return q

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True);a=sp.add_parser('campaign');a.add_argument('--output',type=Path,required=True)
 for name in ['resume','query']:
  a=sp.add_parser(name);a.add_argument('--root',type=Path,required=True);a.add_argument('--plan-sha',required=True)
  if name=='resume':a.add_argument('--receipt',type=Path,required=True)
  else:a.add_argument('--step',type=int,required=True);a.add_argument('--cache-bytes',type=int,default=768*1024)
 args=ap.parse_args()
 if args.mode!='campaign':
  t=time.perf_counter();s=Scheduler(args.root,args.plan_sha)
  if args.mode=='query':
   with CoordinatedReader(s,args.cache_bytes) as r:print(json.dumps(r.query_epoch(args.step),indent=2));return
  status=s.run();dump(args.receipt,dict(status=status,wall_s=time.perf_counter()-t,reused_column_publications=s.reused_publications,epoch_ids=[str(x.state_id) for x in s.epochs()],metrics=s.metrics,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss));return
 out=args.output;out.mkdir();started=time.perf_counter();prev=BASE/'ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_EXPLORE_V3_20261102_01/run02';statics={};basejobs={}
 for k in ['C028','C139']:
  basejobs[k]=json.loads((prev/(k+'_DENSE_JOB.json')).read_text());statics[k]=json.loads((prev/(k+'_dense/STATIC.json')).read_text())
 results={};negatives=[];audit=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,FileNotFoundError) as ex:negatives.append(dict(case=name,status='REJECTED',reason=str(ex)))
  else:raise AssertionError('NEGATIVE_ACCEPTED:'+name)
 for count,marks,cut in [(5,[0,141,282,423,564],282),(48,list(range(0,565,12)),288)]:
  print('begin',count,flush=True);plans={k:copy.deepcopy(basejobs[k]) for k in basejobs}
  for j in plans.values():j['snapshot_steps']=marks
  plan=dict(schema='THERMAL_LOGICAL_SCHEDULER_V1',scheduler_policy_sha256=thermal.digest(policy()),steps=564,duration_s=10*thermal.YEAR,dt_s=10*thermal.YEAR/564,snapshot_steps=marks,columns={k:dict(column_id=statics[k]['context']['column'],job=plans[k]) for k in sorted(plans)})
  root=out/str(count);root.mkdir();direct=Scheduler.create(root/'direct',plan,statics);t=time.perf_counter();assert direct.run()=='COMPLETE';directwall=time.perf_counter()-t
  split=Scheduler.create(root/'split',plan,statics);assert split.run(interrupt_after_first=cut)=='INTERRUPTED_BETWEEN_COLUMNS';before_ids={k:[str(r.state_id) for r in c.records()] for k,c in split.controllers.items()};before_epochs=len(split.epochs());assert len(before_ids['C028'])==len(before_ids['C139'])+1
  reader=CoordinatedReader(split);reader.__enter__();partial=reader.query_epoch(cut);assert partial['status']=='EPOCH_INCOMPLETE' and partial['column_publications_present']==['C028'];column=reader.query_column('C028',cut);assert column['status']=='STORED_NODES' and not column['shared_epoch_published']
  reject(str(count)+'_register_incomplete',lambda:split.register_epoch(cut));reject(str(count)+'_register_out_of_order',lambda:split.register_epoch(564));reject(str(count)+'_duplicate_column_publish',split.controllers['C028'].publish);assert len(split.epochs())==before_epochs
  t=time.perf_counter();reopened=Scheduler(root/'split',sha(root/'split/PLAN.json'));reopened.reconcile();recover_s=time.perf_counter()-t
  assert {k:[str(r.state_id) for r in c.records()] for k,c in reopened.controllers.items()}==before_ids
  childstart=time.perf_counter();p=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'resume','--root',str(root/'split'),'--plan-sha',sha(root/'split/PLAN.json'),'--receipt',str(root/'CHILD.json')],capture_output=True,text=True);childwall=time.perf_counter()-childstart;(root/'child.stdout').write_text(p.stdout);(root/'child.stderr').write_text(p.stderr)
  if p.returncode:raise RuntimeError(p.stderr)
  child=json.loads((root/'CHILD.json').read_text());assert child['reused_column_publications']==1
  assert reader.query_epoch(cut)['status']=='EPOCH_INCOMPLETE';assert reader.refresh();completed=reader.query_epoch(cut);assert completed['status']=='AVAILABLE';reader.__exit__(None,None,None)
  resumed=Scheduler(root/'split',sha(root/'split/PLAN.json'));resumed.reconcile();left=direct.epochs();right=resumed.epochs();assert [r.to_dict() for r in left]==[r.to_dict() for r in right] and len(left)==count
  for k in direct.keys:
   d=direct.controllers[k];r=resumed.controllers[k];assert thermal.encoded(d.state)==thermal.encoded(r.state);assert [x.to_dict() for x in d.records()]==[x.to_dict() for x in r.records()]
  n=len(resumed.epochs());assert resumed.register_epoch(cut)=='ALREADY_AVAILABLE' and len(resumed.epochs())==n;assert resumed.run()=='COMPLETE' and len(resumed.epochs())==n
  # Shared-epoch query verifies references against both independent pinned views.
  t=time.perf_counter();session=CoordinatedReader(direct);session.__enter__();open_s=time.perf_counter()-t;cold=session.query_epoch(564);assert cold['status']=='AVAILABLE';warm=[]
  for _ in range(3):
   q=session.query_epoch(564);warm.append(q['query_s']);assert normalize(q)==normalize(cold)
  cache=session.cache_report();single=session.query_column('C139',564);assert single['status']=='STORED_NODES' and single['shared_epoch_published'];session.__exit__(None,None,None)
  with CoordinatedReader(direct,384*1024) as small:
   low=small.query_epoch(564);assert low['status']=='AVAILABLE' and low['epoch_state_id']==cold['epoch_state_id'];small_cache=small.cache_report();assert sum(x['budget_bytes'] for x in small_cache['per_column'].values())==384*1024
  dump(root/'INCOMPLETE_AND_RECOVERY.json',dict(partial=partial,independent_column=column,after_refresh=completed,initial_column_ids=before_ids,partial_epoch_count=before_epochs,no_duplicate_after_resume=True))
  dump(root/'QUERY_EXAMPLE.json',cold)
  for e in left:
   v=thaw_json(e.value);audit.append(dict(snapshot_count=count,step=v['step'],epoch_id=str(e.state_id),parent=list(e.parent_state_ids),references=v['columns']))
  results[str(count)]=dict(epoch_count=count,column_state_count={k:len(c.records()) for k,c in direct.controllers.items()},direct_wall_s=directwall,metrics=direct.metrics,recover_partial_s=recover_s,child_launch_to_exit_s=childwall,epoch_and_native_identity=True,partial_epoch_hidden=True,pinned_view_then_refresh=True,reader_open_s=open_s,query_cold_s=cold['query_s'],query_warm_s=warm,query_warm_median_s=statistics.median(warm),cache=cache,smaller_budget_cache=small_cache,storage=storage(root/'direct'),column_storage={k:storage(root/'direct/columns'/k) for k in direct.keys},registry_storage=storage(root/'direct/epochs'))
  dump(root/'RESULT.json',results[str(count)]);print('done',count,flush=True)
 # Cache/registry corruption and configuration compatibility use copies only.
 chosen=out/'48/direct';s=Scheduler(chosen,sha(chosen/'PLAN.json'));reject('negative_aggregate_budget',lambda:CoordinatedReader(s,-1));reject('wrong_plan_SHA',lambda:Scheduler(chosen,'0'*64))
 shutil.copytree(chosen,out/'corrupt_epoch');s=Scheduler(out/'corrupt_epoch',sha(out/'corrupt_epoch/PLAN.json'))
 with CoordinatedReader(s) as rd:
  q=rd.query_epoch(564);rid=q['epoch_state_id'];p=s.root/'epochs/states'/(rid+'.json');v=json.loads(p.read_text());v['value']['step']-=1;p.write_text(json.dumps(v));reject('warm_corrupt_epoch',lambda:rd.query_epoch(564))
 shutil.copytree(chosen,out/'corrupt_column');s=Scheduler(out/'corrupt_column',sha(out/'corrupt_column/PLAN.json'))
 with CoordinatedReader(s) as rd:
  q=rd.query_epoch(564);rid=q['columns']['C028']['state_id'];p=s.root/'columns/C028/history/states'/(rid+'.json');v=json.loads(p.read_text());v['value']['dynamic']['time_s']+=1;p.write_text(json.dumps(v));reject('warm_corrupt_column',lambda:rd.query_epoch(564))
 s=Scheduler(chosen,sha(chosen/'PLAN.json'));ref=thaw_json(s.epochs()[-1].value)['columns']['C028'];ref['column_id']=s.controllers['C139'].ctx['column'];reject('incompatible_spatial_reference',lambda:s._verify_ref('C028',ref,564))
 shutil.copytree(chosen,out/'bad_plan');p=out/'bad_plan/PLAN.json';v=json.loads(p.read_text());v['dt_s']+=1;p.write_bytes(thermal.encoded(v));reject('incompatible_common_dt',lambda:Scheduler(out/'bad_plan',sha(p)))
 dump(out/'EPOCH_AUDIT.json',audit);dump(out/'NEGATIVE_TESTS.json',negatives);dump(out/'RESULT.json',dict(marker='MULTI_COLUMN_THERMAL_SCHEDULER_EXPLORE=PASS_LOGICAL_SHARED_EPOCHS_AND_RECONCILED_RESTART',cases=results,negative_tests=negatives,wall_s=time.perf_counter()-started,user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_policy=policy()))
 print('completed',time.perf_counter()-started,flush=True)
if __name__=='__main__':main()
