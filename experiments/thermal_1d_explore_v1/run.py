"""Bounded original-T0 thermal exploration; no lateral solver or tectonic forcing."""
from pathlib import Path
import json,hashlib,time,resource,sys
import numpy as np
from scipy.linalg import expm
from arcana_worldsim.r6 import functional_development as fd

ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT.parent
OUT=Path(sys.argv[1]); OUT.mkdir()
def write(p,o):p.write_text(json.dumps(o,indent=2,allow_nan=False))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=time.perf_counter()
before=json.loads((OUT.parent/'BEFORE.json').read_text())
for p,h in before['pins'].items():assert sha(ROOT/p)==h
for p,h in before['sources'].items():assert sha(ROOT/p)==h
original=BASE/'ARCANA_WORLD_EVIDENCE/R6/INT10K_E1_R2_I6OODuU9/original_inputs/RESULT.json'
d=json.loads(original.read_text()); states=next(c for c in d['cases'] if c['case_id']=='UNCoupled_reference')['state_initial']
meta=json.loads((ROOT/'R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json').read_text()); fields=meta['field_order']; selected=[]
with (ROOT/meta['runtime_data_filename']).open() as f:
 next(f)
 for line in f:
  a=line.split()
  if int(float(a[1]))==91 and int(float(a[2])) in (28,29):selected.append(dict(zip(fields,map(float,a))))
write(OUT/'PRE_ORBDATA_MATCHES.json',selected)
results=[]
for sid,p in states.items():
 s=fd.state_from_payload(p); z=np.array(p['z_m']); T=np.array(p['temperature_k']); n=len(z); H=p['crust_m']
 assert s.time_s==0 and len(T)==73 and z[24]==H
 assert T[0]==s.surface_temperature_k and T[-1]==s.base_temperature_k
 mats=[s.materials[0],s.materials[-1]]
 assert all(m.k_w_m_k>0 and m.rho_kg_m3>0 and m.cp_j_kg_k>0 and m.radiogenic_w_m3>=0 for m in mats)
 profile=fd.T0Profile(sid,'CONTINENTAL_AUTHORED_REFERENCE','FIXED_GEOMETRY_ORIGINAL_DIRICHLET',H,z[-1],T[0],T[-1],float(mats[0].k_w_m_k*np.polynomial.polynomial.polyfit(z[:3],T[:3],2)[1]),tuple(z),tuple(T),s.materials,tuple(m.role_id for m in mats),{'origin':'E0 archived T0; q_surface not a prescribed boundary in this experiment'})
 # Surface-flux metadata reconstructed from original quadratic samples; not a prescribed boundary.
 duration=10*fd.SECONDS_PER_YEAR
 # Physical interface exactly at node24: integrate each dual control volume's two materials.
 edges=np.r_[z[0],.5*(z[:-1]+z[1:]),z[-1]]
 lC=np.maximum(0,np.minimum(edges[1:],H)-np.minimum(edges[:-1],H)); lM=np.diff(edges)-lC
 cap=lC*mats[0].rho_kg_m3*mats[0].cp_j_kg_k+lM*mats[1].rho_kg_m3*mats[1].cp_j_kg_k
 src=lC*mats[0].radiogenic_w_m3+lM*mats[1].radiogenic_w_m3
 R=np.maximum(0,np.minimum(z[1:],H)-np.minimum(z[:-1],H))/mats[0].k_w_m_k+np.maximum(0,z[1:]-np.maximum(z[:-1],H))/mats[1].k_w_m_k
 conduct=1/R
 # Original provider's independent geometric reconstruction, retained as baseline.
 k=np.array([m.k_w_m_k for m in s.materials]); rhocp=np.array([m.rho_kg_m3*m.cp_j_kg_k for m in s.materials]); A=np.array([m.radiogenic_w_m3 for m in s.materials]); dz=np.diff(z)
 g_old=1/(.5*dz/k[:-1]+.5*dz/k[1:]); c_old=rhocp*np.diff(edges); a_old=A*np.diff(edges)
 limit=float(np.min(cap[1:-1]/(conduct[:-1]+conduct[1:]))); oldlimit=fd._diffusion_stability_limit(z,s.materials)
 # Analytic T0 polynomial curvature, fitted independently within each layer.
 fits=[np.polynomial.polynomial.polyfit(z[:25],T[:25],2),np.polynomial.polynomial.polyfit(z[24:]-H,T[24:],2)]
 qmoho=[mats[0].k_w_m_k*(fits[0][1]+2*fits[0][2]*H),mats[1].k_w_m_k*fits[1][1]]
 rates=[(2*m.k_w_m_k*c[2]+m.radiogenic_w_m3)/(m.rho_kg_m3*m.cp_j_kg_k) for m,c in zip(mats,fits)]
 row={'support':sid,'nodes':n,'materials':[m.__dict__ for m in mats],'boundary_K':[float(T[0]),float(T[-1])],'depth_m':float(z[-1]),'moho_m':H,'duration_years':10,'original_CFL_s':oldlimit,'interface_corrected_CFL_s':limit,'analytic_initial_layer_rate_K_per_year':[r*fd.SECONDS_PER_YEAR for r in rates],'analytic_initial_Moho_upward_flux_W_m2':qmoho,'runs':[]}
 for method,g,c,a in [('original_provider',g_old,c_old,a_old),('interface_integrated',conduct,cap,src)]:
  # Independently assemble affine thermal ODE, reference by augmented matrix exponential.
  L=np.zeros((n-2,n-2)); b=a[1:-1]/c[1:-1]
  for j,i in enumerate(range(1,n-1)):
   L[j,j]=-(g[i-1]+g[i])/c[i]
   if j>0:L[j,j-1]=g[i-1]/c[i]
   else:b[j]+=g[i-1]*T[0]/c[i]
   if j<n-3:L[j,j+1]=g[i]/c[i]
   else:b[j]+=g[i]*T[-1]/c[i]
  aug=np.zeros((n-1,n-1));aug[:-1,:-1]=L;aug[:-1,-1]=L@T[1:-1]+b
  # Evolve increments to avoid subtracting large background temperatures.
  exact=T.copy();exact[1:-1]+=(expm(aug*duration)@np.r_[np.zeros(n-2),1])[:-1]
  temporal=[]
  for steps in (16,32,64):
   dt=duration/steps; assert dt<.8*(oldlimit if method=='original_provider' else limit)
   values=T.copy(); trajectory=[values.copy()]; fluxes=[]; balances=[]; inputs=[]
   for it in range(steps):
    q=g*np.diff(values) # upward flux, z positive downward
    if method=='original_provider':
     values2=np.array(fd._explicit_thermal_update(tuple(values),tuple(z),s.materials,dt,T[0],T[-1]))
    else:
     values2=values.copy();values2[1:-1]+=dt*(q[1:]-q[:-1]+a[1:-1])/c[1:-1]
    dE=np.sum(c[1:-1].astype(np.longdouble)*(values2[1:-1].astype(np.longdouble)-values[1:-1]))
    supply=np.longdouble(dt)*(np.longdouble(q[-1])-q[0]+sum(a[1:-1].astype(np.longdouble)))
    balances.append(float(dE-supply));inputs.append(float(supply));fluxes.append(q);trajectory.append(values2.copy());values=values2
   err=float(np.sqrt(np.mean((values-exact)**2)));temporal.append(err)
   np.savez(OUT/f'{sid}_{method}_{steps}.npz',z_m=z,T0_K=T,T_K=values,reference_K=exact,trajectory_K=np.array(trajectory),upward_flux_W_m2=np.array(fluxes),capacity_J_m2_K=c,production_W_m2=a,energy_residual_J_m2=balances,energy_input_J_m2=inputs)
   result={'method':method,'steps':steps,'dt_s':dt,'CFL_ratio':dt/(oldlimit if method=='original_provider' else limit),'delta_T_linf_K':float(np.max(abs(values-T))),'temporal_RMS_K':err,'min_K':float(min(values)),'max_K':float(max(values)),'max_step_energy_residual_J_m2':max(map(abs,balances)),'integrated_energy_input_J_m2':sum(inputs),'cumulative_energy_residual_J_m2':sum(balances),'radiogenic_interior_W_m2':float(sum(a[1:-1])),'radiogenic_full_column_W_m2':float(sum(a)),'initial_upward_flux_top_interior_W_m2':float(fluxes[0][0]),'initial_upward_flux_base_interior_W_m2':float(fluxes[0][-1]),'initial_Moho_adjacent_fluxes_W_m2':[float(fluxes[0][23]),float(fluxes[0][24])]}
   assert result['min_K']>0 and result['delta_T_linf_K']<.1
   budget=float(8*np.finfo(float).eps*np.sum(c[1:-1].astype(np.longdouble)*(np.abs(T[1:-1])+np.abs(values[1:-1]))))
   result['roundoff_energy_budget_J_m2']=budget
   assert result['max_step_energy_residual_J_m2']<budget
   row['runs'].append(result)
  row[method+'_temporal_orders']=[float(np.log2(temporal[i]/temporal[i+1])) for i in (0,1)]
 # Public provider function must match baseline private-step sequence.
 public,diag=fd.evolve_fixed_geometry_thermal_profile(profile,duration_s=duration,maximum_substep_s=duration/16)
 saved=np.load(OUT/f'{sid}_original_provider_16.npz');assert np.array_equal(public,saved['T_K'])
 row['public_provider_parity']=True
 row['initial_Moho_rate_original_K_per_year']=float((g_old[24]*(T[25]-T[24])-g_old[23]*(T[24]-T[23])+a_old[24])/c_old[24]*fd.SECONDS_PER_YEAR)
 row['initial_Moho_rate_integrated_K_per_year']=float((conduct[24]*(T[25]-T[24])-conduct[23]*(T[24]-T[23])+src[24])/cap[24]*fd.SECONDS_PER_YEAR)
 results.append(row)
write(OUT/'RESULT.json',{'status':'THERMAL_1D_EXPLORE_COMPLETED_MODEL_INPUT_SCOPE','results':results,'PRE_ORBDATA_owner_matches':len(selected),'wall_s':time.perf_counter()-start,'cpu_user_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime,'cpu_system_s':resource.getrusage(resource.RUSAGE_SELF).ru_stime,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'scope':'authorial T0, fixed original Dirichlet; no deformation, lateral coupling or scientific validation'})
print(json.dumps({'status':'completed','columns':len(results),'wall_s':time.perf_counter()-start}))
