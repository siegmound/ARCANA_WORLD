"""Separate per-cell divergence theorem from cancellation across hanging geometry."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
sys.path.insert(0,str(c.CODE));import oracle,datum

def main():
 case=c.ROOT/'forced_l2_a1_p1_interior_flux_NEW01';a,z,act,C,ci,H,hi,*_=oracle.load(case);ids=a[:,0].astype(int)
 def read(s):
  x=np.loadtxt(case/'output'/('G46_s0_r0_'+s+'.dat'),ndmin=2);x=x[np.argsort(x[:,0])];c.need(np.array_equal(ids,x[:,0]),'FLUX_IDENTITY');return x[:,1]
 rows=[]
 for n in [3,7]:
  pv=read('PV'+str(n));surface=read('PS'+str(n));allfaces=read('PSALL'+str(n));interior=read('PSINT'+str(n));scale=max(np.linalg.norm(H.T@surface),1e-300)
  rows.append({'order':n,'cellwise_volume_vs_all_faces_relative':float(np.linalg.norm(pv-allfaces)/max(np.linalg.norm(allfaces),1e-300)),'H_condensed_volume_vs_all_faces_relative':float(np.linalg.norm(H.T@(pv-allfaces))/scale),'H_condensed_interior_face_flux_relative':float(np.linalg.norm(H.T@interior)/scale),'H_condensed_volume_vs_exterior_relative':float(np.linalg.norm(H.T@(pv-surface))/scale),'decomposition_replay_relative':float(np.linalg.norm(H.T@(allfaces-surface-interior))/scale),'C_constant_pressure_action_l2':float(np.linalg.norm(C.T@pv)),'mechanical_boundary_surface_action_l2':float(np.linalg.norm(C.T@surface))})
 c.write(c.ROOT/'DATUM_INTERIOR_GEOMETRY_ADJUDICATION.json',{'case':case.name,'rows':rows,'interpretation':'higher-order cellwise theorem and cancellation of interior AMR faces are distinct. Nonzero H-condensed internal flux is retained; do not call all mismatch quadrature or assume a constant pressure kernel under C. No native operator quadrature, geometry or force changed.','strict_identity_relative_threshold':1e-10,'higher_order_cellwise_identity_pass':rows[-1]['cellwise_volume_vs_all_faces_relative']<=1e-10,'interior_flux_identity_pass':rows[-1]['H_condensed_interior_face_flux_relative']<=1e-10,**c.SCOPE});print('FLUX_DECOMPOSITION',rows,flush=True)
if __name__=='__main__':main()
