from pathlib import Path
import argparse,copy,json,sys,time,subprocess,resource,math,os
import numpy as np
import thermal
from adapter import ThermalController,STATIC_KEYS,binding,dump,sha
from arcana_worldsim.r6.identity import thaw_json
BASE=Path(__file__).resolve().parents[3]

def cost(root):
 files=[p for p in Path(root).rglob('*') if p.is_file()];return dict(files=len(files),logical_bytes=sum(p.stat().st_size for p in files),allocated_bytes=sum(p.stat().st_blocks*512 for p in files))
def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True);c=sp.add_parser('campaign');c.add_argument('--output',type=Path,required=True)
 for name in ['resume','query']:
  a=sp.add_parser(name);a.add_argument('--root',type=Path,required=True);a.add_argument('--job',type=Path,required=True);a.add_argument('--job-sha',required=True)
  if name=='resume':a.add_argument('--receipt',type=Path,required=True)
  else:a.add_argument('--year',type=float,required=True);a.add_argument('--min-depth',type=float,required=True);a.add_argument('--max-depth',type=float,required=True)
 args=p.parse_args()
 if args.cmd!='campaign':
  if sha(args.job)!=args.job_sha:raise ValueError('JOB_IDENTITY')
  job=json.loads(args.job.read_text());ctl=ThermalController(args.root,job);start=time.perf_counter()
  if args.cmd=='query':print(json.dumps(ctl.query(ctl.ctx['column'],args.year,args.min_depth,args.max_depth),indent=2));return
  ctl.recover()
  while ctl.state['step']<564:ctl.advance();ctl.publish()
  dump(args.receipt,dict(wall_s=time.perf_counter()-start,metrics=ctl.metrics,native_digest=thermal.digest(ctl.state),user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss));return
 out=args.output;out.mkdir();start=time.perf_counter();prev=BASE/'ARCANA_WORLD_EVIDENCE/R6/THERMAL_1D_HISTORY_EXPLORE_20261102_01/run02';initial=json.loads((prev/'direct/snapshot_000000.json').read_text());static={k:initial[k] for k in STATIC_KEYS};job=dict(binding=binding(),static_sha256=thermal.digest(static),snapshot_steps=[0,141,282,423,564]);dump(out/'JOB.json',job)
 direct=ThermalController.create(out/'direct',job,static).start()
 while direct.state['step']<564:direct.advance();direct.publish()
 split=ThermalController.create(out/'split',job,static).start()
 for _ in range(2):split.advance();split.publish()
 restore_start=time.perf_counter();probe=ThermalController(out/'split',job).recover();restore_s=time.perf_counter()-restore_start;assert thermal.encoded(probe.state)==thermal.encoded(split.state)
 argschild=[sys.executable,'-B',str(Path(__file__).resolve()),'resume','--root',str(out/'split'),'--job',str(out/'JOB.json'),'--job-sha',sha(out/'JOB.json'),'--receipt',str(out/'CHILD_RECEIPT.json')]
 childstart=time.perf_counter();child=subprocess.run(argschild,capture_output=True,text=True);childwall=time.perf_counter()-childstart;(out/'child_stdout.log').write_text(child.stdout);(out/'child_stderr.log').write_text(child.stderr)
 if child.returncode:raise RuntimeError('CHILD:'+child.stderr)
 split=ThermalController(out/'split',job).recover();assert thermal.encoded(direct.state)==thermal.encoded(split.state)
 ids=[str(s.state_id) for s in direct.records()];assert ids==[str(s.state_id) for s in split.records()]
 oldfinal=json.loads((prev/'direct/snapshot_000564.json').read_text());current=copy.deepcopy(direct.state);current.pop('parent_snapshot_sha256');oldfinal.pop('parent_snapshot_sha256');assert thermal.encoded(current)==thermal.encoded(oldfinal)
 # Controller-specific failure-before-publication cases; no old numerical suite repeated.
 neg=ThermalController.create(out/'negative',job,static).start();valid=direct.restore_record(ids[1]);bad_results=[]
 def reject(name,fn):
  count=len(neg.records())
  try:fn()
  except (ValueError,KeyError) as ex:bad_results.append(dict(case=name,status='REJECTED',reason=str(ex)))
  else:raise AssertionError('NEGATIVE_ACCEPTED:'+name)
  assert len(neg.records())==count
 reject('duplicate_publication',lambda:neg.publish())
 neg.state=copy.deepcopy(valid);neg.phase='READY';neg.state['time_s']+=1;reject('inconsistent_clock',lambda:neg.publish())
 neg.state=direct.restore_record(ids[3]);neg.phase='READY';reject('skipped_publication',lambda:neg.publish())
 neg.state=copy.deepcopy(valid);neg.phase='READY';neg.last_id='r6state_'+'0'*64;reject('stale_parent',lambda:neg.publish())
 neg.last_id=str(neg.records()[0].state_id);neg.state=copy.deepcopy(valid);del neg.state['T_correction_K'];reject('incomplete_temperature',lambda:neg.publish())
 bad=copy.deepcopy(job);bad['static_sha256']='0'*64;reject('wrong_static_reference',lambda:ThermalController(out/'direct',bad))
 bad2=copy.deepcopy(job);bad2['binding']['adapter']['adapter.py']='0'*64;reject('wrong_controller_source',lambda:ThermalController(out/'direct',bad2))
 queries=[direct.query(direct.ctx['column'],t,0,8) for t in [0,2.5,5,7.5,10]];dump(out/'QUERY_HISTORY.json',queries)
 missing=direct.query(direct.ctx['column'],1,0,8);gap=direct.query(direct.ctx['column'],10,.1,.9);assert missing['status']=='TIME_NOT_ARCHIVED' and gap['status']=='NO_STORED_NODES_IN_INTERVAL'
 dump(out/'QUERY_NEGATIVES.json',dict(missing_time=missing,gap=gap))
 # Exactly one copy of static data; each ledger entry appears in one dynamic record.
 rows=direct.records();ledger_rows=sum(len(thaw_json(x.value)['ledger_segment']) for x in rows);assert ledger_rows==564
 components=dict(static=(out/'direct/STATIC.json').stat().st_size,dynamic_records=sum(len(thermal.encoded(x.to_dict())) for x in rows),ledger_rows=ledger_rows)
 ledger=direct.state['ledger'];energy={k:math.fsum(x[k] for x in ledger) for k in ['internal_deltaE_J_m2','radiogenic_internal_J_m2','Dirichlet_top_exchange_J_m2','Dirichlet_base_exchange_J_m2','residual_J_m2']}
 dump(out/'RESULT.json',dict(marker='THERMAL_CONTROLLER_HISTORY_EXPLORE=PASS_EXISTING_R6_INTERFACES_FIVE_STATES',published=[dict(state_id=str(x.state_id),seconds=float(x.time_support.time_key),year=float(x.time_support.time_key)/thermal.YEAR,parent=list(x.parent_state_ids)) for x in rows],native_restart_bit_equal=True,all_state_ids_equal=True,numerical_state_equal_previous_history=True,negative_tests=bad_results,restore_s=restore_s,child_launch_to_exit_s=childwall,direct_metrics=direct.metrics,storage=cost(out/'direct'),split_storage=cost(out/'split'),components=components,old_full_snapshot_bytes=sum(x.stat().st_size for x in (prev/'direct').glob('snapshot_*.json')),energy=energy,wall_s=time.perf_counter()-start,user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
 print('completed',time.perf_counter()-start)
if __name__=='__main__':main()
