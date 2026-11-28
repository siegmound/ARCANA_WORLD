"""Read-only G45 comparison; rotation fits are diagnostics, never acceptance."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]))
import arcana_g46_campaign as c
sys.path.insert(0,str(c.prior.CODE));import audit

def main():
 c.check();rows=[]
 groups={}
 for p in sorted(c.PARENT.glob('G45R1_*/G45R1_AUDIT_REPORT.json')):
  case=p.parent;s=c.read(case/'CASE_SPEC.json')
  if s['family'] not in ('forced','datum'):continue
  groups.setdefault((s['family'],s['base_refinement']),[]).append(case)
 for key,cases in groups.items():
  ref=next(p for p in cases if c.read(p/'CASE_SPEC.json')['ranks']==1)
  # Native IDs only join inside each case; CellId/local basis creates cross-run identity.
  def values(p):
   d=audit.load(p);a=d['dofs'];pos={int(x):i for i,x in enumerate(a[:,0])};keys={}
   for cell,b in zip(d['basiskeys'],d['basis']):
    j=pos[int(b[1])];k=cell+'/'+str(int(b[0]));keys[j]=min(keys.get(j,k),k)
   order=sorted(keys,key=keys.get);return [keys[j] for j in order],a[order],d
  keys,a,da=values(ref);x=a[:,2:5];component=a[:,1].astype(int)
  Z=np.column_stack([np.cross(np.eye(3)[k],x)[np.arange(len(x)),component] for k in range(3)])
  for p in cases:
   kb,b,db=values(p);c.need(kb==keys,'RETAINED_IDENTITY');du=b[:,5]-a[:,5];omega=np.linalg.lstsq(Z,du,rcond=None)[0];orth=du-Z@omega
   f=db['faces'];w=f[:,3];normal=f[:,7:10];u=f[:,10:13]
   rows.append({'reference':ref.name,'case':p.name,'ranks':c.read(p/'CASE_SPEC.json')['ranks'],'historical_velocity_relative':float(np.linalg.norm(du)/max(np.linalg.norm(a[:,5]),1.)),'rotation_fit_diagnostic_only':omega.tolist(),'rotation_fit_residual_fraction':float(np.linalg.norm(orth)/max(np.linalg.norm(du),1e-300)),'surface_normal_velocity_L2':float(np.sqrt(w@np.sum(u*normal,axis=1)**2)),'D_volume':float(db['cells'][:,27].sum()),'pressure_work_volume':float(db['cells'][:,29].sum()),'native_force_screen':c.read(p/'G45R1_AUDIT_REPORT.json')['reactions']['native']['force_balance_relative'],'volume_mass_norm':'NOT_EXPORTED_G45_REQUIRES_INSTRUMENTATION','C_admissibility_and_K_B_nullity':'NOT_EXPORTED_G45_REQUIRES_INSTRUMENTATION'})
 c.write(c.ROOT/'RETAINED_G45_DIAGNOSIS.json',{'status':'DIAGNOSTIC_ONLY_NO_GAUGE_ACCEPTANCE','rows':rows,'independent_native_solves':0,'join':'CellId/localbasis with case-local IDs only','quotient_velocity_never_used_for_acceptance':True,**c.SCOPE})
 print('G46_RETAINED_DATA',len(rows),'maximum historical delta',max(x['historical_velocity_relative'] for x in rows),flush=True)
if __name__=='__main__':main()
