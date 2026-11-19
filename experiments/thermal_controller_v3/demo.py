from pathlib import Path
import json,sys,argparse,copy,time,subprocess,statistics,shutil,resource,hashlib
import numpy as np
import thermal
import adapter as legacy
from reader import ReadSession,FastController
from column import ColumnController,source_binding
from bounded import IndexedSession,DenseController,policy
BASE=Path(__file__).resolve().parents[3]
def timed(fn):
 t=time.perf_counter();x=fn();return x,time.perf_counter()-t
clean=lambda q:{k:v for k,v in q.items() if k!='read_restore_query_s'}
def storage(root):
 f=[p for p in Path(root).rglob('*') if p.is_file()];return dict(files=len(f),logical_bytes=sum(p.stat().st_size for p in f),allocated_bytes=sum(p.stat().st_blocks*512 for p in f))
def bench(c,label,budget=384*1024,baseline=True):
 if baseline:
  with ReadSession(c) as old:
   q,oq=timed(lambda:old.query(c.ctx['column'],10,0,8));rid=q['state_id'];native,orr=timed(lambda:old.restore(rid));oldtimes=[]
   for _ in range(3):_,t=timed(lambda:old.query(c.ctx['column'],10,0,8));oldtimes.append(t)
   oldprefix=sum(len(thermal.encoded(x)) for x in old.prefix.values())
 else:
  with IndexedSession(c,0) as old:
   q=old.query(c.ctx['column'],10,0,8);rid=q['state_id'];native=old.restore(rid)
  oq=orr=oldprefix=None;oldtimes=[]
 with IndexedSession(c,budget) as s:
  _,it=timed(s.ensure_index);query,cq=timed(lambda:s.query(c.ctx['column'],10,0,8));assert clean(query)==clean(q);warmq=[];warmr=[];reads0=s.stats['record_reads']
  for _ in range(3):
   qq,t=timed(lambda:s.query(c.ctx['column'],10,0,8));warmq.append(t);st,t=timed(lambda:s.restore(rid));warmr.append(t);assert clean(qq)==clean(q) and thermal.encoded(st)==thermal.encoded(native)
  cache=s.cache_report();newreads=s.stats['record_reads']-reads0
 with IndexedSession(c,budget) as s:st,cr=timed(lambda:s.restore(rid));assert thermal.encoded(st)==thermal.encoded(native)
 return dict(label=label,budget_bytes=budget,V2_cold_query_s=oq,V2_restore_after_query_s=orr,V2_warm_query_s=oldtimes,V2_serialized_prefix_bytes=oldprefix,index_build_s=it,V3_cold_query_after_index_s=cq,V3_cold_restore_including_index_s=cr,V3_warm_query_s=warmq,V3_warm_restore_s=warmr,V3_warm_query_median_s=statistics.median(warmq),V3_warm_restore_median_s=statistics.median(warmr),warm_dynamic_record_reads=newreads,cache=cache)
def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='mode',required=True);a=sp.add_parser('campaign');a.add_argument('--output',type=Path,required=True)
 a=sp.add_parser('resume');a.add_argument('--root',type=Path,required=True);a.add_argument('--job',type=Path,required=True);a.add_argument('--job-sha',required=True);a.add_argument('--receipt',type=Path,required=True)
 a=sp.add_parser('query');a.add_argument('--root',type=Path,required=True);a.add_argument('--job',type=Path,required=True);a.add_argument('--job-sha',required=True);a.add_argument('--year',type=float,required=True);a.add_argument('--column',required=True);a.add_argument('--budget-bytes',type=int,default=384*1024)
 args=p.parse_args()
 if args.mode!='campaign':
  if legacy.sha(args.job)!=args.job_sha:raise ValueError('JOB_SHA')
  j=json.loads(args.job.read_text());c=DenseController(args.root,j);t=time.perf_counter()
  if args.mode=='query':
   with IndexedSession(c,args.budget_bytes) as s:print(json.dumps(s.query(args.column,args.year,0,8),indent=2));return
  c.recover()
  while c.state['step']<564:c.advance();c.publish()
  legacy.dump(args.receipt,dict(wall_s=time.perf_counter()-t,native_digest=thermal.digest(c.state),IDs=[str(x.state_id) for x in c.records()],peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss));return
 out=args.output;out.mkdir();start=time.perf_counter();prev=BASE/'ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_EXPLORE_V2_20261102_01/run01';reports=[];results={};pinned={}
 for col,klass,sparseroot in [('C028',FastController,'cached_publish'),('C139',ColumnController,'C139_direct')]:
  print('begin',col,flush=True);shutil.copytree(prev/sparseroot,out/(col+'_five'));oldjob=json.loads((prev/(col+'_JOB.json')).read_text());sparse=klass(out/(col+'_five'),oldjob)
  reports.append(bench(sparse,col+'_5'))
  with IndexedSession(sparse) as r:five=[r.restore(str(x.state_id)) for x in r.records()];fiveIDs=[str(x.state_id) for x in r.records()]
  static={k:five[0][k] for k in legacy.STATIC_KEYS};job=dict(binding=source_binding(),static_sha256=thermal.digest(static),snapshot_steps=list(range(0,565,12)),dense_policy_sha256=thermal.digest(policy()));legacy.dump(out/(col+'_DENSE_JOB.json'),job)
  d=DenseController.create(out/(col+'_dense'),job,static).start()
  with IndexedSession(DenseController(out/(col+'_dense'),job)) as fixed:
   fixed.ensure_index();oldview=fixed.view.view_id;assert len(fixed.index)==1;d.advance();d.publish();fixed.ensure_index();assert len(fixed.index)==1;changed=fixed.refresh();fixed.ensure_index();assert changed and len(fixed.index)==2;pinned[col]=dict(before_view=oldview,after_view=fixed.view.view_id,pinned_count=1,after_refresh=2)
  while d.state['step']<564:d.advance();d.publish()
  split=DenseController.create(out/(col+'_split'),job,static).start()
  while split.state['step']<288:split.advance();split.publish()
  childstart=time.perf_counter();cp=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'resume','--root',str(out/(col+'_split')),'--job',str(out/(col+'_DENSE_JOB.json')),'--job-sha',legacy.sha(out/(col+'_DENSE_JOB.json')),'--receipt',str(out/(col+'_CHILD.json'))],capture_output=True,text=True);childwall=time.perf_counter()-childstart;(out/(col+'_child.stdout')).write_text(cp.stdout);(out/(col+'_child.stderr')).write_text(cp.stderr)
  if cp.returncode:raise RuntimeError(cp.stderr)
  split=DenseController(out/(col+'_split'),job).recover();assert thermal.encoded(d.state)==thermal.encoded(split.state)
  denseIDs=[str(x.state_id) for x in d.records()];assert denseIDs==[str(x.state_id) for x in split.records()] and len(denseIDs)==48
  sparsefinal=copy.deepcopy(five[-1]);densefinal=copy.deepcopy(d.state);sparsefinal.pop('parent_snapshot_sha256');densefinal.pop('parent_snapshot_sha256');assert thermal.encoded(sparsefinal)==thermal.encoded(densefinal)
  reports.append(bench(d,col+'_48'))
  queries=[]
  with IndexedSession(d) as s:
   for year in (0.,10.):queries.append(s.query(d.ctx['column'],year,0,8))
   assert s.query('R6G1D-R013-C139' if col=='C028' else 'R6G1D-R091-C028',10,0,8)['status']=='COLUMN_NOT_ARCHIVED'
   assert s.query(d.ctx['column'],2.5,0,8)['status']=='TIME_NOT_ARCHIVED'
   assert s.query(d.ctx['column'],10,.1,.9)['status']=='NO_STORED_NODES_IN_INTERVAL'
  legacy.dump(out/(col+'_QUERIES.json'),queries)
  # Replay LRU sequence in two fresh sessions: deterministic admission/eviction and full fallback.
  traces=[]
  for trial in range(2):
   with IndexedSession(d,384*1024) as s:
    s.ensure_index()
    for ordinal in (47,12,36,47):s.restore(s.index[ordinal]['state_id']);assert s.charged<=s.budget
    if trial==0:
     s.force_verify();assert len(s.index)==48
    # Compare deterministic sequence before force_verify separately below.
   traces.append(s.evicted)
  with IndexedSession(d,384*1024) as s:
   s.ensure_index()
   for ordinal in (47,12,36,47):s.restore(s.index[ordinal]['state_id'])
   trace=s.evicted.copy()
  assert traces[1]==trace
  results[col]=dict(snapshot_count=48,steps=564,years=10,resume_step=288,complete_native_restart_equal=True,all48IDs_equal=True,numerical_5_vs48_equal_except_retention_parent=True,dense_state_ids=denseIDs,sparse_state_ids=fiveIDs,static_sha256=job['static_sha256'],column=d.ctx['column'],Moho_m=d.state['geometry']['Moho_m'],base_m=d.state['geometry']['z_m'][-1],storage_5=storage(out/(col+'_five')),storage_48=storage(out/(col+'_dense')),publish_48=d.metrics,child_wall_s=childwall,deterministic_evictions=True)
  legacy.dump(out/(col+'_PROGRESS.json'),dict(result=results[col],benchmarks=reports));print('done',col,flush=True)
 # Budget sensitivity only on C028 dense, no numerical reruns.
 d=DenseController(out/'C028_dense',json.loads((out/'C028_DENSE_JOB.json').read_text()))
 for budget in (0,128*1024,1024*1024):reports.append(bench(d,'C028_48_budget',budget,baseline=False))
 negatives=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,FileNotFoundError) as ex:negatives.append(dict(case=name,status='REJECTED',reason=str(ex)))
  else:raise AssertionError(name)
 reject('negative_budget',lambda:IndexedSession(d,-1))
 shutil.copytree(out/'C028_dense',out/'tamper');tc=DenseController(out/'tamper',d.job)
 with IndexedSession(tc) as s:
  s.ensure_index();rid=s.index[-1]['state_id'];s.restore(rid);p=tc.root/'history/states'/(rid+'.json');x=json.loads(p.read_text());x['value']['dynamic']['time_s']+=1;p.write_text(json.dumps(x));reject('warm_corrupt_record',lambda:s.restore(rid));assert s.stats['invalidations']>0
 shutil.copytree(out/'C028_dense',out/'tamper_time');tc=DenseController(out/'tamper_time',d.job)
 with IndexedSession(tc) as s:
  s.ensure_index();rid=s.index[-1]['state_id'];s.restore(rid);p=tc.root/'history/temporal'/(s.index[-1]['temporal_id']+'.json');x=json.loads(p.read_text());x['details']['model_years']+=1;p.write_text(json.dumps(x));reject('warm_corrupt_time_index',lambda:s.query(tc.ctx['column'],10,0,8))
 bad=copy.deepcopy(d.job);bad['static_sha256']='0'*64;reject('wrong_static',lambda:DenseController(out/'C028_dense',bad))
 bad=copy.deepcopy(d.job);bad['dense_policy_sha256']='0'*64;reject('wrong_policy_source',lambda:DenseController(out/'C028_dense',bad))
 d.recover();count=len(d.records());reject('duplicate_publish',d.publish);d.state['time_s']+=1;d.phase='READY';reject('invalid_clock_publish',d.publish);assert len(d.records())==count
 legacy.dump(out/'READ_BENCHMARKS.json',reports);legacy.dump(out/'RESULT.json',dict(marker='THERMAL_CONTROLLER_EXPLORE_V3=PASS_INDEXED_BOUNDED_CACHE_48_STATES',columns=results,pinned_views=pinned,negative_tests=negatives,wall_s=time.perf_counter()-start,user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_policy=policy()))
 print('completed',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
