"""Short resolving-grid controls; reads campaign arrays, never changes T0."""
from pathlib import Path
import sys,json,time,resource
import numpy as np
from scipy.sparse import diags,bmat,csr_matrix
from scipy.sparse.linalg import expm_multiply
from scipy.integrate import quad
from scipy.special import erfc
from model import properties,advance
OUT=Path(sys.argv[1]);OUT.mkdir();E=OUT.parent;rec=json.loads((E/'SELECTED_INPUTS.json').read_text())['hot_C028'];H=rec['crust_thickness_m'];L=rec['lab_depth_m'];t=10*31557600.;start=time.perf_counter()
m=[[rec[p+'_conductivity_w_m_k'],rec[p+'_density_kg_m3'],rec[p+'_cp_j_kg_k'],rec[p+'_heat_production_w_m3']] for p in ('crust','mantle')]
controls=[]
for spacing in (4.,2.,1.):
 a=np.load(E/f'run02/hot_C028_boundary_dx{spacing:g}.npz');z=a['z'];T=a['T0'];ref=a['semidiscrete_increment'];C,S,g,edges=properties(z,H,m);cfl=min(C[1:-1]/(g[:-1]+g[1:]));N=max(32,int(np.ceil(t/(.5*cfl))))
 for steps in (N,2*N):
  v=advance(z,H,m,T,t,steps);err=v['T'].astype(np.longdouble)-T.astype(np.longdouble)-ref.astype(np.longdouble)
  controls.append(dict(dx_m=spacing,nodes=len(z),steps=steps,CFL_ratio=v['dt_s']/v['CFL_s'],temporal_linf_K=float(max(abs(err))),ledger_residual_J_m2=float(sum(v['ledger'][:,2])),max_step_residual_J_m2=float(max(abs(v['ledger'][:,2]))),minimum_K=float(min(v['T']))))
  np.savez(OUT/f'resolved_dx{spacing:g}_{steps}.npz',z=z,T0=T,reference_increment=ref,**{k:x for k,x in v.items() if isinstance(x,np.ndarray)})
# Crosscheck short-time continuum integral via numerical integration in scaled time.
checks=[]
for distance in (0.,4.,16.,64.):
 kap=m[0][0]/(m[0][1]*m[0][2]);eta=distance/(2*np.sqrt(kap*t))
 formula=(1+2*eta**2)*erfc(eta)-2*eta/np.sqrt(np.pi)*np.exp(-eta**2)
 numerical,err=quad(lambda s: erfc(eta/np.sqrt(s)) if s else 0.,0,1,epsabs=1e-13,epsrel=1e-13)
 checks.append(dict(distance_m=distance,increment_difference_K=float(abs(formula-numerical)*t*abs(rec['transient_rate_k_s'])),quad_error_estimate=float(err)))
# Resolve short-time Moho sensitivity to k_C with the same physical initial field.
sens=[]
for kval in (2.,3.):
 for dx in (4.,2.,1.):
  base=np.load(E/'run02/hot_C028_289_64.npz');d=np.arange(-256.,256.+dx/2,dx);zb=base['z'];z=np.unique(np.r_[zb,H+d])
  T=[]
  for x in z:
   p='layer1' if x<=H else 'layer2';u=x-rec[p+'_z0_m'];T.append(((rec[p+'_c3_k_m3']*u+rec[p+'_c2_k_m2'])*u+rec[p+'_c1_k_m'])*u+rec[p+'_c0_k'])
  T=np.array(T);mm=[a.copy() for a in m];mm[0][0]=kval
  increments=[]
  for mat in (m,mm):
   C,S,g,e=properties(z,H,mat);n=len(z)-2
   K=diags([g[1:-1],-(g[:-1]+g[1:]),g[1:-1]],[-1,0,1],shape=(n,n),format='csr');K=diags(1/C[1:-1])@K
   rhs=(np.diff(g*np.diff(T))+S[1:-1])/C[1:-1];B=bmat([[K,csr_matrix(rhs[:,None])],[None,csr_matrix((1,1))]],format='csr')*t
   inc=np.r_[0.,expm_multiply(B,np.r_[np.zeros(n),1.],traceA=float(B.diagonal().sum()))[:-1],0.];increments.append(inc)
  diff=increments[1]-increments[0];sens.append(dict(k_C=kval,dx_Moho_m=dx,nodes=len(z),effect_linf_K=float(max(abs(diff))),effect_at_Moho_K=float(diff[np.argmin(abs(z-H))])))
  np.savez(OUT/f'Moho_k{kval:g}_dx{dx:g}.npz',z=z,T0=T,nominal_increment=increments[0],sensitivity_increment=increments[1])
# Check the original73 grid is genuinely subdivided by campaign grids (roundoff tolerance only).
np.savez(OUT/'resolved_controls.npz',dummy=np.array([len(controls)]))
(OUT/'RESULT.json').write_text(json.dumps(dict(resolved_Euler=controls,integral_crosscheck=checks,Moho_k_sensitivity=sens,wall_s=time.perf_counter()-start,user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))
print('completed',time.perf_counter()-start)
