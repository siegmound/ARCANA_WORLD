"""Opt-in physical thermal history prototype and bounded child/query CLI."""
from pathlib import Path
import argparse,copy,json,hashlib,subprocess,time,resource,sys,math
import numpy as np
from thermal import properties,initial,step,validate,source_identity,runtime,encoded,digest,YEAR
from history import create,publish,read_index,load_snapshot,query,hashfile

BASE=Path(__file__).resolve().parents[3];REPO=BASE/'ARCANA_WORLD_R6_GEOMETRY_R1_WORK'
def write(p,x):
 with Path(p).open('xb') as f:f.write(encoded(x))
def job_read(p,sha):
 if hashfile(p)!=sha:raise ValueError('JOB_SHA')
 j=json.loads(Path(p).read_text())
 if j['context']['sources']!=source_identity() or j['context']['runtime']!=runtime():raise ValueError('JOB_SOURCE_RUNTIME')
 return j

def advance_to(s,target,archive,j):
 telemetry=[];start=time.perf_counter()
 while s['step']<target:
  step(s)
  if s['step'] in j['snapshot_steps']:telemetry.append(publish(archive,s,j['context']))
 return s,dict(wall_s=time.perf_counter()-start,writes=telemetry)

def energy(s):
 C=np.array(s['geometry']['capacity_J_m2_K'],np.longdouble);S=np.array(s['geometry']['source_W_m2'],np.longdouble);hi=np.array(s['T_hi_K'],np.longdouble);co=np.array(s['T_correction_K'],np.longdouble);ini=np.array(s['initial_T_K'],np.longdouble)
 change=np.sum(C[1:-1]*((hi[1:-1]-ini[1:-1])-co[1:-1]));ledger=s['ledger']
 sums={key:math.fsum(row[key] for row in ledger) for key in ['internal_deltaE_J_m2','radiogenic_internal_J_m2','Dirichlet_top_exchange_J_m2','Dirichlet_base_exchange_J_m2','residual_J_m2','roundoff_bound_J_m2']}
 supplied=sums['radiogenic_internal_J_m2']+sums['Dirichlet_top_exchange_J_m2']+sums['Dirichlet_base_exchange_J_m2']
 return dict(internal_energy_J_m2_decimal=str(np.sum(C[1:-1]*(hi[1:-1]-co[1:-1]))),internal_change_J_m2=float(change),ledger_sums=sums,net_supplied_J_m2=supplied,global_residual_J_m2=float(change-np.longdouble(supplied)),radiogenic_interior_W_m2=float(sum(S[1:-1])),radiogenic_reservoir_W_m2=float(S[0]+S[-1]),reservoir_energy_change_J_m2=0.,scope='fixed Dirichlet endpoint half volumes excluded from evolved energy',compensation_nonzero_nodes=int(np.count_nonzero(co)))

def campaign(out):
 out.mkdir();start=time.perf_counter();before=json.loads((out.parent/'BEFORE.json').read_text());old=before['preserved']
 for p,h in {**old['pins'],**old['sources'],**old['thermal_v1'],**before['thermal_v2']}.items():
  if hashfile(REPO/p)!=h:raise ValueError('PRESERVED_SOURCE:'+p)
 previous=out.parent.parent/'THERMAL_1D_EXPLORE2_20261102_01';a=np.load(previous/'run02/hot_C028_boundary_dx2.npz');records=json.loads((previous/'SELECTED_INPUTS.json').read_text());rec=records['hot_C028'];m=[[rec[p+'_conductivity_w_m_k'],rec[p+'_density_kg_m3'],rec[p+'_cp_j_kg_k'],rec[p+'_heat_production_w_m3']] for p in ('crust','mantle')]
 geom=properties(a['z'],rec['crust_thickness_m'],m);T=a['T0'];context=dict(column='R6G1D-R091-C028',schema='THERMAL_HISTORY_CONTEXT_V1',sources=source_identity(),runtime=runtime(),geometry_sha256=digest(geom),initial_T_sha256=digest(T.tolist()),Dirichlet_K=[float(T[0]),float(T[-1])],duration_s=10*YEAR,steps=564,parameter_authority='PRE_ORBDATA_AUTHORED_T0_FIXED_GEOMETRY_DIRICHLET',origin_world_age_Ma=210.,input_npz_sha256=hashfile(previous/'run02/hot_C028_boundary_dx2.npz'),PRE_DAT_sha256=hashfile(REPO/'R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat'),temperature_representation='hi-correction',energy_domain='interior dual volumes per unit horizontal area; endpoint half volumes are fixed reservoirs')
 j=dict(context=context,snapshot_steps=[0,141,282,423,564]);write(out/'JOB.json',j);jobsha=hashfile(out/'JOB.json');s0=initial(geom,T,context)
 direct=out/'direct';create(direct);t0write=publish(direct,s0,context);directstate,dtel=advance_to(copy.deepcopy(s0),564,direct,j)
 outcomes={};metrics={'direct':dtel,'T0_write':t0write}
 for name in ('local_restart','child_restart'):
  root=out/name;create(root);publish(root,s0,context);s,tel=advance_to(copy.deepcopy(s0),282,root,j);index=read_index(root,context);cp=index[-1];readstart=time.perf_counter();loaded=load_snapshot(root/cp['file'],cp['sha256'],context);readwall=time.perf_counter()-readstart
  assert encoded(s)==encoded(loaded)
  if name=='local_restart':
   final,continued=advance_to(loaded,564,root,j);childwall=None
  else:
   childstart=time.perf_counter();p=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'resume','--root',str(root),'--job',str(out/'JOB.json'),'--job-sha',jobsha,'--checkpoint-sha',cp['sha256'],'--receipt',str(out/'CHILD_RECEIPT.json')],capture_output=True,text=True)
   childwall=time.perf_counter()-childstart;(out/'child_stdout.log').write_text(p.stdout);(out/'child_stderr.log').write_text(p.stderr)
   if p.returncode:raise RuntimeError('CHILD_FAILED:'+p.stderr)
   index=read_index(root,context);last=index[-1];final=load_snapshot(root/last['file'],last['sha256'],context);continued=json.loads((out/'CHILD_RECEIPT.json').read_text())
  equal=encoded(final)==encoded(directstate);assert equal
  outcomes[name]=dict(complete_state_bit_equal=equal,all_snapshot_SHA_equal=[e['sha256'] for e in read_index(root,context)]==[e['sha256'] for e in read_index(direct,context)],read_restore_s=readwall,child_launch_through_finish_s=childwall,energy=energy(final))
  assert outcomes[name]['all_snapshot_SHA_equal']
  metrics[name]=dict(first_half=tel,continuation=continued)
 # Negative cases authenticate modified files against their NEW SHA so identity checks cannot hide behind old checksum.
 negatives=[];negroot=out/'negative';negroot.mkdir();validfile=direct/read_index(direct,context)[-1]['file'];raw=validfile.read_bytes()
 for kind in ['corrupt','source','geometry','boundary','clock','missing_correction']:
  s=copy.deepcopy(directstate)
  if kind=='source':s['context']['sources']['thermal.py']='0'*64
  elif kind=='geometry':s['geometry']['z_m'][100]+=.1
  elif kind=='boundary':s['context']['Dirichlet_K'][0]+=1;s['T_hi_K'][0]+=1
  elif kind=='clock':s['time_s']+=1
  elif kind=='missing_correction':del s['T_correction_K']
  file=negroot/(kind+'.json');file.write_bytes(raw+b'!' if kind=='corrupt' else encoded(s))
  try:load_snapshot(file,hashfile(validfile) if kind=='corrupt' else hashfile(file),context)
  except (ValueError,KeyError) as ex:negatives.append(dict(case=kind,status='REJECTED',reason=str(ex)))
  else:raise AssertionError('NEGATIVE_ACCEPTED:'+kind)
 # Fully copied archive with a valid-looking unindexed snapshot is never adopted.
 import shutil
 tail=out/'negative_tail';shutil.copytree(direct,tail);(tail/'snapshot_999999.json').write_bytes(raw)
 try:read_index(tail,context)
 except ValueError as ex:negatives.append(dict(case='unconfirmed_tail',status='REJECTED',reason=str(ex)))
 else:raise AssertionError('TAIL_ADOPTED')
 examples=[]
 for year in (0.,2.5,5.,7.5,10.):examples.append(query(direct,context,context['column'],year,0.,16.))
 missing=query(direct,context,context['column'],1.,0.,16.);assert missing['status']=='TIME_NOT_ARCHIVED'
 unknown=query(direct,context,'R6G1D-R091-C029',10.,0.,16.);assert unknown['status']=='COLUMN_NOT_ARCHIVED'
 gap=query(direct,context,context['column'],10.,.1,.9);assert gap['status']=='NO_STORED_NODES_IN_INTERVAL'
 write(out/'QUERY_EXAMPLES.json',dict(surface_history=examples,missing_time=missing,unknown_column=unknown,depth_without_stored_nodes=gap,Moho=query(direct,context,context['column'],10.,27900.,28100.)))
 # New compensation has an independent existing same-grid semidiscrete reference; no old campaign repeated.
 final=directstate;physical=np.array(final['T_hi_K'],np.longdouble)-np.array(final['T_correction_K'],np.longdouble);inc=(np.array(final['T_hi_K'],np.longdouble)-T.astype(np.longdouble))-np.array(final['T_correction_K'],np.longdouble);ref=a['semidiscrete_increment'];err=inc-ref;oldcontrol=np.load(previous/'extra01/resolved_dx2_564.npz');oldresidual=float(sum(oldcontrol['ledger'][:,2]));oldtemporal=float(max(abs(oldcontrol['T'].astype(np.longdouble)-T.astype(np.longdouble)-ref)))
 energies=energy(final);assert abs(energies['global_residual_J_m2'])<energies['ledger_sums']['roundoff_bound_J_m2']
 result=dict(marker='THERMAL_1D_HISTORY_EXPLORE=PASS_SHORT_COMPLETE_STATE_CAUSAL_ARCHIVE',column=context['column'],nodes=len(T),steps=564,years=10,snapshots=5,restart=outcomes,negative_tests=negatives,energy=energies,dt_s=final['dt_s'],CFL_s=final['CFL_s'],CFL_ratio=final['dt_s']/final['CFL_s'],delta_T_linf_K=float(max(abs(inc))),semidiscrete_temporal_Linf_K=float(max(abs(err))),old_plain_same_plan_temporal_Linf_K=oldtemporal,old_plain_cumulative_ledger_residual_J_m2=oldresidual,min_K=float(min(physical)),max_K=float(max(physical)),services=metrics,wall_s=time.perf_counter()-start,cpu_user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,cpu_system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,child_user_s=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime,child_system_s=resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 write(out/'RESULT.json',result);print(json.dumps({k:result[k] for k in ['marker','wall_s','nodes','semidiscrete_temporal_Linf_K']}))

def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest='mode',required=True);c=sp.add_parser('campaign');c.add_argument('--output',type=Path,required=True)
 for mode in ('resume','query'):
  q=sp.add_parser(mode);q.add_argument('--root',type=Path,required=True);q.add_argument('--job',type=Path,required=True);q.add_argument('--job-sha',required=True)
  if mode=='resume':q.add_argument('--checkpoint-sha',required=True);q.add_argument('--receipt',type=Path,required=True)
  else:
   q.add_argument('--column',required=True);q.add_argument('--year',type=float,required=True);q.add_argument('--depth-min',type=float,required=True);q.add_argument('--depth-max',type=float,required=True)
 args=p.parse_args()
 if args.mode=='campaign':campaign(args.output)
 else:
  j=job_read(args.job,args.job_sha);ctx=j['context']
  if args.mode=='query':print(json.dumps(query(args.root,ctx,args.column,args.year,args.depth_min,args.depth_max),indent=2));return
  start=time.perf_counter();entries=read_index(args.root,ctx);e=entries[-1]
  if e['sha256']!=args.checkpoint_sha:raise ValueError('EXPECTED_LAST_CHECKPOINT')
  s=load_snapshot(args.root/e['file'],e['sha256'],ctx);s,telemetry=advance_to(s,ctx['steps'],args.root,j)
  write(args.receipt,dict(telemetry=telemetry,total_child_wall_s=time.perf_counter()-start,user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,final_state_sha256=digest(s)))
if __name__=='__main__':main()
