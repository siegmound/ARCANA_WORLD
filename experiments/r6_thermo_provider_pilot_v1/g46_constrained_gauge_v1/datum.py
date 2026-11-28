"""Constant pressure volume and surface increments at fixed u; no solve correction."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import spsolve
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
sys.path.insert(0,str(c.CODE));import oracle
sys.path.insert(0,str(c.prior.CODE));import audit

def pressure_preflight(case,ids,act):
 spec=c.read(case/'CASE_SPEC.json');c.need(spec.get('pressure_increment_expression','10')=='10','DATUM_NONCONSTANT_SHIFT')
 v=np.vstack([oracle.numeric(p,2) for p in sorted((case/'output').glob('G46_s0_r*_PV3.dat'))]);v=v[np.argsort(v[:,0])]
 c.need(np.array_equal(v[:,0],ids),'DATUM_OWNER_IDENTITY')
 c.need(np.linalg.norm(v[:,1]-act[:,1])/max(np.linalg.norm(act[:,1]),1.)<=1e-10,'DATUM_NATIVE_PRESSURE_LOAD')
 return True

def evaluate(case):
 a,Z,act,C,ci,H,hi,summary,faces,allstate=oracle.load(case);ids=a[:,0].astype(int);pressure_preflight(case,ids,act)
 def vector(suffix):
  x=np.vstack([oracle.numeric(p,2) for p in sorted((case/'output').glob('G46_s0_r*_'+suffix+'.dat'))]);x=x[np.argsort(x[:,0])];c.need(np.array_equal(ids,x[:,0]),'DATUM_OWNER_IDENTITY');return x[:,1]
 data=audit.load(case);d=data['dofs'];d=d[np.argsort(d[:,0])];c.need(np.array_equal(d[:,0],ids),'G45_G46_SAME_RUN_IDENTITY')
 # Rectangular H from independent rows; same full GLL mass, not lumped condensed mass.
 from scipy import sparse
 M=(H.T@sparse.diags(d[:,9])@H).tocsr();sel=np.flatnonzero(M.diagonal()>1e-20);A=M[sel,:][:,sel].tocsr();off=np.setdiff1d(np.arange(H.shape[1]),sel)
 vec={x:vector(x) for x in ['PV3','PV5','PV7','PS0','PS3','PS5','PS7']};rhs={k:np.asarray(H.T@v).ravel() for k,v in vec.items()};sol={k:spsolve(A,b[sel]) for k,b in rhs.items()}
 def massnorm(x):return float(np.sqrt(max(float(x@(A@x)),0.)))
 rows=[]
 for v in ['PV3','PV5','PV7']:
  for s in ['PS0','PS3','PS5','PS7']:
   dv=rhs[v]-rhs[s];rel=massnorm(sol[v]-sol[s])/max(massnorm(sol[s]),1e-300)
   rows.append({'volume':v,'surface':s,'rhs_relative':float(np.linalg.norm(dv)/max(np.linalg.norm(rhs[s]),1e-300)),'trace_mass_L2_relative':rel,'original_projected_traction_gate_pass':rel<=.005,'interior_condensed_increment_l2':float(np.linalg.norm(dv[off])),'mechanical_constant_pressure_action_l2':float(np.linalg.norm(C.T@vec[v]))})
 result={'case':case.name,'constant_pressure_Pa':10,'fixed_u':True,'mapping_unchanged':True,'native_operator_quadrature_unchanged':True,'native_volume_Gauss_points':summary[:,3].tolist(),'comparisons':rows,'projected_native_G45_reference':next(r for r in rows if r['volume']=='PV3' and r['surface']=='PS0'),'higher_order_diagnostic':next(r for r in rows if r['volume']=='PV7' and r['surface']=='PS7'),'surface_vs_GLL':{k:massnorm(sol[k]-sol['PS0'])/max(massnorm(sol[k]),1e-300) for k in ['PS3','PS5','PS7']},'status':'INDEPENDENT_QUADRATURE_DIAGNOSIS_NOT_OPERATOR_REPLACEMENT',**c.SCOPE}
 # Actual forced/datum G45 pair compared with the fixed-u pressure operator using stable incidence.
 spec=c.read(case/'CASE_SPEC.json')
 if spec['family']=='forced' and spec.get('gauge')=='unremoved' and spec['adaptive_cycles']==1:
  n=spec['ranks'];l=spec['base_refinement'];oldf=c.PARENT/f'G45R1_forced_l{l}_a1_p{n}_unremoved_NEW01';oldd=c.PARENT/f'G45R1_datum_l{l}_a1_p{n}_unremoved_NEW01'
  def stable(data):
   pos={int(k):j for j,k in enumerate(data['dofs'][:,0])};keys={}
   for cell,b in zip(data['basiskeys'],data['basis']):
    j=pos[int(b[1])];key=cell+'/'+str(int(b[0]));keys[j]=min(keys.get(j,key),key)
   return {key:data['dofs'][j] for j,key in keys.items()}
  g0=stable(data);f0=stable(audit.load(oldf));f1=stable(audit.load(oldd));c.need(set(g0)==set(f0)==set(f1),'DATUM_STABLE_MESH_IDENTITY');pmap={int(v):i for i,v in enumerate(ids)};dr=np.zeros(len(ids));du=np.zeros(len(ids))
  for key in g0:
   j=pmap[int(g0[key][0])];dr[j]=f1[key][7]-f0[key][7];du[j]=f1[key][5]-f0[key][5]
  actual=spsolve(A,np.asarray(H.T@dr)[sel]);delta=actual-sol['PV3'];result['actual_G45_pair']={'forced':oldf.name,'datum':oldd.name,'actual_vs_fixed_u_pressure_trace_mass_relative':massnorm(delta)/max(massnorm(sol['PV3']),1e-300),'full_velocity_historical_absolute_scaled':float(np.linalg.norm(du)/max(np.linalg.norm(np.array([f0[key][5] for key in sorted(f0)])),1.)),'original_G45_pair_gate':audit.datum(oldf,oldd,require_pass=False)}
 c.write(case/'G46_DATUM_ORACLE.json',result);print('G46_DATUM',case.name,'native-vsGLL',result['projected_native_G45_reference']['trace_mass_L2_relative'],'highorder',result['higher_order_diagnostic']['trace_mass_L2_relative'],flush=True);return result
if __name__=='__main__':evaluate(Path(sys.argv[1]))
