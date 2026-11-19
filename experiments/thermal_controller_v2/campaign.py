from pathlib import Path
import argparse,json,copy,time,sys,shutil,statistics,subprocess,resource,tracemalloc,os
import numpy as np
import thermal
import adapter as old
from reader import ReadSession,FastController
from column import ColumnController,source_binding
BASE=Path(__file__).resolve().parents[3];REPO=BASE/'ARCANA_WORLD_R6_GEOMETRY_R1_WORK'
def measure(fn):
 t=time.perf_counter();x=fn();return x,time.perf_counter()-t
def logical(root):
 fs=[p for p in Path(root).rglob('*') if p.is_file()];return dict(files=len(fs),logical_bytes=sum(p.stat().st_size for p in fs),allocated_bytes=sum(p.stat().st_blocks*512 for p in fs))
def clean_query(x):return {k:v for k,v in x.items() if k!='read_restore_query_s'}
def continue_child(root,jobpath,receipt,kind):
 t=time.perf_counter();p=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'resume','--root',str(root),'--job',str(jobpath),'--job-sha',old.sha(jobpath),'--receipt',str(receipt),'--kind',kind],capture_output=True,text=True)
 receipt.with_suffix('.stdout').write_text(p.stdout);receipt.with_suffix('.stderr').write_text(p.stderr)
 if p.returncode:raise RuntimeError(p.stderr)
 return time.perf_counter()-t

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True);a=sp.add_parser('campaign');a.add_argument('--output',type=Path,required=True)
 a=sp.add_parser('resume');a.add_argument('--root',type=Path,required=True);a.add_argument('--job',type=Path,required=True);a.add_argument('--job-sha',required=True);a.add_argument('--receipt',type=Path,required=True);a.add_argument('--kind',choices=['legacy','column'],required=True)
 a=sp.add_parser('query');a.add_argument('--root',type=Path,required=True);a.add_argument('--job',type=Path,required=True);a.add_argument('--job-sha',required=True);a.add_argument('--kind',choices=['legacy','column'],required=True);a.add_argument('--year',type=float,required=True)
 args=ap.parse_args()
 if args.mode!='campaign':
  if old.sha(args.job)!=args.job_sha:raise ValueError('JOB_SHA')
  job=json.loads(args.job.read_text())
  if job['cache_policy_sha256']!=thermal.digest(source_binding()):raise ValueError('CACHE_SOURCE')
  c=(FastController if args.kind=='legacy' else ColumnController)(args.root,job);t=time.perf_counter()
  if args.mode=='query':
   with ReadSession(c) as s:print(json.dumps(s.query(c.ctx['column'],args.year,0,8),indent=2))
   return
  c.recover()
  while c.state['step']<c.ctx['steps']:c.advance();c.publish()
  old.dump(args.receipt,dict(wall_s=time.perf_counter()-t,complete_native_sha256=thermal.digest(c.state),state_ids=[str(r.state_id) for r in c.records()],peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss));return
 out=args.output;out.mkdir();started=time.perf_counter();prior=BASE/'ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_HISTORY_EXPLORE_20261102_01/run01';shutil.copytree(prior/'direct',out/'existing_copy');job=json.loads((prior/'JOB.json').read_text());job['cache_policy_sha256']=thermal.digest(source_binding());old.dump(out/'C028_JOB.json',job)
 base=old.ThermalController(out/'existing_copy',job);rows=base.records();ids=[str(r.state_id) for r in rows];native=[base.restore_record(i) for i in ids]
 base_query,tbaseq=measure(lambda:base.query(base.ctx['column'],10,0,8));_,tbaser=measure(lambda:base.restore_record(ids[-1]));tracemalloc.start();tracemalloc.reset_peak()
 c,open_s=measure(lambda:FastController(out/'existing_copy',job));s=ReadSession(c);t=time.perf_counter();s.__enter__();enter_s=time.perf_counter()-t
 q,coldq=measure(lambda:s.query(c.ctx['column'],10,0,8));assert clean_query(q)==clean_query(base_query)
 timesq=[];timesr=[]
 for _ in range(5):
  q,dt=measure(lambda:s.query(c.ctx['column'],10,0,8));timesq.append(dt);v,dt=measure(lambda:s.restore(ids[-1]));timesr.append(dt);assert thermal.encoded(v)==thermal.encoded(native[-1])
 _,peak_cache=tracemalloc.get_traced_memory();prefix_payload=sum(len(thermal.encoded(x)) for x in s.prefix.values());stats=copy.deepcopy(s.stats);v=s.restore(ids[-1]);v['T_hi_K'][1]=-1;assert thermal.encoded(s.restore(ids[-1]))==thermal.encoded(native[-1]);s.force_verify();v,fallback=measure(lambda:s.restore(ids[-1]));assert thermal.encoded(v)==thermal.encoded(native[-1]);s.__exit__(None,None,None);tracemalloc.stop()
 with ReadSession(c) as fresh:_,coldrestore=measure(lambda:fresh.restore(ids[-1]))
 phase1=dict(legacy_query_s=tbaseq,legacy_restore_s=tbaser,controller_open_s=open_s,session_enter_s=enter_s,cache_cold_query_s=coldq,cache_cold_restore_s=coldrestore,warm_query_s=timesq,warm_restore_s=timesr,warm_query_median_s=statistics.median(timesq),warm_restore_median_s=statistics.median(timesr),force_full_verify_s=fallback,cache_serialized_prefix_bytes=prefix_payload,tracemalloc_session_peak_bytes=peak_cache,stats=stats,query_equal=True,all_native_restore_equal=True)
 if statistics.median(timesq)>=tbaseq:raise ValueError('NO_MEASURABLE_CACHE_BENEFIT_PHASE2_NOT_STARTED')
 # Publication of existing actual states, no physical trajectory repeated for this comparison.
 pub={};pinned={}
 for label,klass in [('legacy_publish',old.ThermalController),('cached_publish',FastController)]:
  w=klass.create(out/label,job,{k:native[0][k] for k in old.STATIC_KEYS}).start()
  if label=='cached_publish':
   reader=ReadSession(FastController(out/label,job));reader.__enter__();before_view=reader.view.view_id;assert len(reader.records())==1
  for i,st in enumerate(native[1:]):
   w.state=copy.deepcopy(st);w.phase='READY';w.publish()
   if label=='cached_publish' and i==0:
    assert len(reader.records())==1;changed=reader.refresh();assert changed and len(reader.records())==2;pinned=dict(old_view=before_view,new_view=reader.view.view_id,pinned_old_count=1,refreshed_count=2);reader.__exit__(None,None,None)
  assert [str(r.state_id) for r in w.records()]==ids
  pub[label]=[x for x in w.metrics if x['service']=='publish_existing_store']
 # Reopen a partial fast archive and continue its actual kernel in another process.
 w=FastController.create(out/'C028_split',job,{k:native[0][k] for k in old.STATIC_KEYS}).start()
 for st in native[1:3]:w.state=copy.deepcopy(st);w.phase='READY';w.publish()
 childwall=continue_child(out/'C028_split',out/'C028_JOB.json',out/'C028_CHILD.json','legacy');final=FastController(out/'C028_split',job).recover();assert thermal.encoded(final.state)==thermal.encoded(native[-1]);assert [str(r.state_id) for r in final.records()]==ids
 negatives=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,FileNotFoundError) as ex:negatives.append(dict(case=name,status='REJECTED',reason=str(ex)))
  else:raise AssertionError('ACCEPTED:'+name)
 # Warm cached prefix cannot hide an altered immutable record.
 shutil.copytree(out/'existing_copy',out/'tamper_record');tc=FastController(out/'tamper_record',job)
 with ReadSession(tc) as rs:
  rs.restore(ids[-1]);p=out/'tamper_record/history/states'/(ids[-1]+'.json');x=json.loads(p.read_text());x['value']['dynamic']['T_hi_K'][1]+=1;p.write_text(json.dumps(x));reject('warm_record_tamper',lambda:rs.restore(ids[-1]));assert rs.stats['invalidations']==1
 shutil.copytree(out/'existing_copy',out/'tamper_static');tc=FastController(out/'tamper_static',job)
 with ReadSession(tc) as rs:
  rs.restore(ids[-1]);p=out/'tamper_static/STATIC.json';p.write_bytes(p.read_bytes()+b' ');reject('warm_static_tamper',lambda:rs.restore(ids[-1]))
 bad=copy.deepcopy(job);bad['binding']['adapter']['adapter.py']='0'*64;reject('wrong_source',lambda:FastController(out/'existing_copy',bad))
 w=FastController.create(out/'order_negative',job,{k:native[0][k] for k in old.STATIC_KEYS}).start();reject('duplicate_publish',w.publish);w.state=copy.deepcopy(native[1]);w.state['time_s']+=1;w.phase='READY';reject('clock_mismatch',w.publish);w.state=copy.deepcopy(native[3]);reject('skipped_snapshot',w.publish);assert len(w.records())==1
 with ReadSession(final) as rs:
  assert rs.query(final.ctx['column'],1,0,8)['status']=='TIME_NOT_ARCHIVED';assert rs.query(final.ctx['column'],10,.1,.9)['status']=='NO_STORED_NODES_IN_INTERVAL'
 old.dump(out/'PHASE1.json',dict(benchmarks=phase1,publication=pub,pinned_view=pinned,child_restart_wall_s=childwall,negative_tests=negatives,identity='all five C028 IDs and complete native states unchanged'))
 print('phase1 complete',flush=True)
 # Phase2 only after phase1 succeeded: actual cold-continent T0 record and resolving grid.
 src=BASE/'ARCANA_WORLD_EVIDENCE/R6/THERMAL_1D_EXPLORE2_20261102_01';record=json.loads((src/'SELECTED_INPUTS.json').read_text())['distinct_continent'];a=np.load(src/'run02/distinct_continent_boundary_dx2.npz');z=a['z'];T=a['T0'].copy();raw_end=T[-1];T[0]=record['surface_temperature_k'];T[-1]=record['lab_temperature_k'];m=[[record[p+'_conductivity_w_m_k'],record[p+'_density_kg_m3'],record[p+'_cp_j_kg_k'],record[p+'_heat_production_w_m3']] for p in ('crust','mantle')];geom=thermal.properties(z,40000.,m)
 ctx=copy.deepcopy(native[0]['context']);ctx.update(column='R6G1D-R013-C139',geometry_sha256=thermal.digest(geom),initial_T_sha256=thermal.digest(T.tolist()),Dirichlet_K=[float(T[0]),float(T[-1])],input_npz_sha256=old.sha(src/'run02/distinct_continent_boundary_dx2.npz'),PRE_node_id=int(record['node_id']))
 st=thermal.initial(geom,T,ctx);static={k:st[k] for k in old.STATIC_KEYS};j2=dict(binding=source_binding(),cache_policy_sha256=thermal.digest(source_binding()),static_sha256=thermal.digest(static),snapshot_steps=[0,141,282,423,564]);old.dump(out/'C139_JOB.json',j2)
 d=ColumnController.create(out/'C139_direct',j2,static).start();ss=ColumnController.create(out/'C139_split',j2,static).start()
 while d.state['step']<564:d.advance();d.publish()
 for _ in range(2):ss.advance();ss.publish()
 child2=continue_child(out/'C139_split',out/'C139_JOB.json',out/'C139_CHILD.json','column');ss=ColumnController(out/'C139_split',j2).recover();assert thermal.encoded(d.state)==thermal.encoded(ss.state);ids2=[str(x.state_id) for x in d.records()];assert ids2==[str(x.state_id) for x in ss.records()];assert not set(ids2)&set(ids)
 with ReadSession(d) as rs:
  qs=[rs.query(ctx['column'],t,0,8) for t in (0,2.5,5,7.5,10)];assert rs.query('R6G1D-R091-C028',10,0,8)['status']=='COLUMN_NOT_ARCHIVED';cw=rs.restore(ids2[-1])
 hi=np.array(cw['T_hi_K'],np.longdouble);co=np.array(cw['T_correction_K'],np.longdouble);inc=(hi-T.astype(np.longdouble))-co;ledger=cw['ledger'];summary=dict(column=ctx['column'],Moho_m=geom['Moho_m'],base_m=geom['z_m'][-1],PRE_node=record['node_id'],boundary_K=ctx['Dirichlet_K'],nodes=len(z),steps=564,years=10,CFL_ratio=cw['dt_s']/cw['CFL_s'],endpoint_polynomial_vs_declared_K=float(raw_end-T[-1]),delta_T_linf_K=float(max(abs(inc))),temporal_vs_saved_semidiscrete_Linf_K=float(max(abs(inc-a['semidiscrete_increment']))),radiogenic_internal_J_m2=sum(x['radiogenic_internal_J_m2'] for x in ledger),ledger_residual_J_m2=sum(x['residual_J_m2'] for x in ledger),net_energy_change_J_m2=sum(x['internal_deltaE_J_m2'] for x in ledger),child_restart_wall_s=child2,full_native_and_ID_parity=True,distinct_IDs_and_supports=True,storage=logical(out/'C139_direct'),state_ids=ids2)
 old.dump(out/'C139_QUERY_HISTORY.json',qs);old.dump(out/'PHASE2.json',summary)
 old.dump(out/'RESULT.json',dict(marker='THERMAL_CONTROLLER_EXPLORE_V2=PASS_PINNED_CACHE_AND_TWO_SEPARATE_COLUMNS',phase1=True,phase2=True,wall_s=time.perf_counter()-started,user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,C028_storage=logical(out/'cached_publish'),C139_storage=logical(out/'C139_direct'),source_binding=source_binding()))
 print('completed',time.perf_counter()-started)
if __name__=='__main__':main()
