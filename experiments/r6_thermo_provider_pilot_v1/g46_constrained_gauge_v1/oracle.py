"""Independent sparse C/H and true discrete operator diagnostic. Never adjusts state."""
import sys,json
from pathlib import Path
import numpy as np
from scipy import sparse,linalg
from scipy.sparse.linalg import eigsh
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
T=c.read(c.CODE/'contract.json')['tolerances']

def numeric(p,n):
 if not p.stat().st_size:return np.empty((0,n))
 a=np.loadtxt(p,ndmin=2);c.need(a.shape[1]==n and np.isfinite(a).all(),'SCHEMA:'+p.name);return a

def constraint(rows,ids):
 pos={int(k):i for i,k in enumerate(ids)};slaves={};inh={}
 for a,b,w in rows:
  a,b=int(a),int(b);c.need(a in pos,'C_MISSING_SLAVE')
  if b==-1:c.need(a not in inh,'C_DUPLICATE_ROW');inh[a]=w;slaves.setdefault(a,[])
  else:c.need(b in pos,'C_MISSING_MASTER');slaves.setdefault(a,[]).append((b,w))
 c.need(set(slaves)==set(inh),'C_ROW_COVERAGE')
 independent=[int(x) for x in ids if int(x) not in slaves];col={k:i for i,k in enumerate(independent)};r=[];s=[];v=[]
 for a in ids:
  a=int(a)
  for b,w in slaves.get(a,[(a,1.)]):c.need(b in col,'C_NOT_CLOSED');r.append(pos[a]);s.append(col[b]);v.append(w)
 return sparse.coo_matrix((v,(r,s)),shape=(len(ids),len(independent))).tocsr(),np.array([pos[k] for k in independent]),np.array([inh.get(int(k),0.) for k in ids])

def exact_gauge_admission(mode):
 required=['C_defect','H_defect','operator_relative','divergence_operator_relative','energy_relative','forcing_compatibility_relative']
 c.need(all(k in mode and np.isfinite(mode[k]) for k in required),'GAUGE_MISSING_FINITE_PROOF')
 c.need(mode['C_defect']<=T['C_H_constraint_relative'] and mode['H_defect']<=T['C_H_constraint_relative'],'GAUGE_UNCONSTRAINED_MODE')
 c.need(mode['operator_relative']<=T['operator_null_relative'] and mode['divergence_operator_relative']<=T['divergence_null_relative'] and mode['energy_relative']<=T['null_energy_relative'],'GAUGE_NON_NULL_MODE')
 c.need(mode['forcing_compatibility_relative']<=T['forcing_compatibility_relative'],'GAUGE_INCOMPATIBLE_FORCING')
 return True

def load(case):
 spec=c.read(case/'CASE_SPEC.json');states=[];modes=[];acts=[];cr=[];hr=[];summ=[];bounds=[]
 for rank in range(spec['ranks']):
  p=case/'output'/f'G46_s0_r{rank}'
  states.append(numeric(Path(str(p)+'_STATE.dat'),8));modes.append(numeric(Path(str(p)+'_MODES.dat'),11));acts.append(numeric(Path(str(p)+'_ACTION.dat'),13));cr.append(numeric(Path(str(p)+'_C.dat'),3));hr.append(numeric(Path(str(p)+'_H.dat'),3));summ.append(np.loadtxt(str(p)+'_SUMMARY.dat',ndmin=2)[0]);bounds.append(np.array([[float(v) for v in line.split()[1:]] for line in Path(str(p)+'_BOUNDARY.dat').read_text().splitlines()]).reshape(-1,14))
 allstate=np.vstack(states);c.need(len(set(allstate[:,0]))==len(allstate) and len(allstate)==int(summ[0][5]),'GLOBAL_STATE_COVERAGE');c.need(np.array_equal(np.array(summ)[:,0],np.arange(spec['ranks'])),'RANK_IDENTITY');a=allstate[allstate[:,1]<3];a=a[np.argsort(a[:,0])];ids=a[:,0].astype(int);c.need(len(set(ids))==len(ids),'OWNERSHIP')
 def align(arr):
  v=np.vstack(arr);v=v[np.argsort(v[:,0])];c.need(np.array_equal(v[:,0],ids),'ID_MISMATCH');return v[:,1:]
 C,ci,clift=constraint(np.vstack(cr),ids);H,hi,hlift=constraint(np.vstack(hr),ids);c.need(np.max(abs(H@np.ones(H.shape[1])-1))<=T['C_H_constraint_relative'],'H_PARTITION_OF_UNITY');c.need(np.linalg.norm(align(modes)[:,6:9]-C@align(modes)[ci,6:9])/max(np.linalg.norm(align(modes)[:,6:9]),1.)<=T['C_H_constraint_relative'],'EXPORTED_C_MODE_VIOLATION');return a,align(modes),align(acts),C,ci,H,hi,np.vstack(summ),np.vstack(bounds),allstate

def evaluate(case):
 a,Z,actions,C,ci,H,hi,summary,faces,allstate=load(case);ids=a[:,0].astype(int);u=a[:,5];stateC=float(np.linalg.norm(u-C@u[ci])/max(np.linalg.norm(u),1.));stateH=float(np.linalg.norm(u-H@u[hi])/max(np.linalg.norm(u),1.))
 total=summary[:,6:].sum(axis=0);rows=[];pos={int(k):i for i,k in enumerate(ids)};K=M=B=None;normK=normB=None;spectrum=None
 paths=sorted((case/'output').glob('G46_s0_r*_KM.dat'))
 if any(p.stat().st_size for p in paths):
  km=np.vstack([numeric(p,4) for p in paths]);ii=np.array([pos[int(k)] for k in km[:,0]]);jj=np.array([pos[int(k)] for k in km[:,1]])
  K=sparse.coo_matrix((km[:,2],(ii,jj)),shape=(len(ids),len(ids))).tocsr();M=sparse.coo_matrix((km[:,3],(ii,jj)),shape=K.shape).tocsr();K.sum_duplicates();M.sum_duplicates()
  ba=np.vstack([numeric(p,3) for p in sorted((case/'output').glob('G46_s0_r*_B.dat'))]);pids=sorted(set(ba[:,0].astype(int)));pp={k:i for i,k in enumerate(pids)};B=sparse.coo_matrix((ba[:,2],([pp[int(k)] for k in ba[:,0]],[pos[int(k)] for k in ba[:,1]])),shape=(len(pids),len(ids))).tocsr()
  Kr=(C.T@K@C).tocsr();Mr=(C.T@M@C).tocsr();Br=B@C;normK=float(sparse.linalg.norm(Kr));normB=float(sparse.linalg.norm(Br))
  ev,v=eigsh(Kr,k=8,M=Mr,sigma=0.,which='LM',tol=1e-10,maxiter=4000);order=np.argsort(ev);ev=ev[order];v=v[:,order]
  spectral_res=[float(np.linalg.norm(Kr@v[:,j]-ev[j]*Mr@v[:,j])/max(np.linalg.norm(Kr@v[:,j]),np.linalg.norm(ev[j]*Mr@v[:,j]),1e-30)) for j in range(len(ev))]
  spectrum={'operator':'C^T A C against C^T M C, strain operator only; B separately tested; no assumption three saddle nulls','smallest_eigenvalues_synthetic_eta_over_length_squared':ev.tolist(),'relative_eigen_residuals':spectral_res,'separation_lambda4_over_lambda3':float(ev[3]/ev[2]),'exact_nullity_under_frozen_energy_relative':int(sum(abs(ev)<T['null_energy_relative']))}
 for j in range(10):
  z=Z[:,j];reduced=ci;cz=C@z[ci];hz=H@z[hi];kr=np.asarray(C.T@actions[:,2+j]);force=np.asarray(C.T@actions[:,0]);energy=float(total[12*j+1]);mass=float(total[12*j]);div=float(total[12*j+2]);Cdef=float(np.linalg.norm(z-cz)/max(np.linalg.norm(z),1.));Hdef=float(np.linalg.norm(z-hz)/max(np.linalg.norm(z),1.));bnormal=float(np.sqrt(faces[:,2]@faces[:,4+j]**2));r={'mode':j,'type':'raw' if j<3 else 'H' if j<6 else 'C' if j<9 else 'native_copy_delta','axis':j%3 if j<9 else None,'mass_L2_sq':mass,'strain_energy':energy,'divergence_L2_sq':div,'K_reduced_action_l2':float(np.linalg.norm(kr)),'C_defect':Cdef,'H_defect':Hdef,'boundary_normal_L2_Gauss5':bnormal,'force_virtual_work':float(total[12*j+3]),'angular_momentum':total[12*j+4:12*j+7].tolist(),'energy_over_mass':energy/max(mass,1e-300)}
  if K is not None:
   c.need(np.linalg.norm(K@z-actions[:,2+j])/max(np.linalg.norm(actions[:,2+j]),1.)<1e-10,'NATIVE_K_ORACLE')
   r.update(operator_relative=float(np.linalg.norm(kr)/max(normK*np.linalg.norm(z[ci]),1e-300)),divergence_operator_relative=float(np.linalg.norm(B@z)/max(normB*np.linalg.norm(z),1e-300)),energy_relative=energy/max(normK*float(z[ci]@z[ci]),1e-300),forcing_compatibility_relative=abs(float(z[ci]@force))/max(np.linalg.norm(z[ci])*np.linalg.norm(force),1e-300))
   try:r['exact_kernel_admitted']=bool(j<9 and mass>1e-20 and exact_gauge_admission(r))
   except RuntimeError as error:r['exact_kernel_admitted']=False;r['gauge_rejection']=str(error)
  else:r['exact_kernel_admitted']=False;r['exact_kernel_scope']='NOT_PROVEN_WITHOUT_FULL_OPERATOR_NORM; positive strain and normal velocity remain independent counterevidence'
  rows.append(r)
 result={'case':case.name,'native_convergence':c.read(case/'EXECUTION_REPORT.json')['native_convergence'],'live_solution_C_defect':stateC,'live_solution_H_defect':stateH,'modes':rows,'spectrum':spectrum,'full_operator_exported':K is not None,'gauge_status':'BLOCKED_NON_NULL_OR_UNPROVEN_ROTATIONS','saddle_or_velocity_correction_performed':False,'volume_quadrature_points':summary[:,3].tolist(),'pressure_scaling':summary[:,4].tolist(),'live_volume_norm_sq':float(total[121]),'live_D':float(total[122]),'live_divergence_sq':float(total[123]),**c.SCOPE}
 c.write(case/'G46_OPERATOR_ORACLE.json',result);print('G46_OPERATOR_ORACLE',case.name,'C/H defects',stateC,stateH,'spectrum',spectrum['smallest_eigenvalues_synthetic_eta_over_length_squared'] if spectrum else 'not exported',flush=True);return result
if __name__=='__main__':evaluate(Path(sys.argv[1]))
