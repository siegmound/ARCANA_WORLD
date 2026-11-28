"""Independent near-null constrained saddle candidate. Rejected if it changes equations."""
import sys
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
sys.path.insert(0,str(c.CODE));import oracle

def run(case,output='NEAR_NULL_SADDLE_CANDIDATE_AMR.json'):
 a,Z,actions,C,ci,H,hi,summary,faces,allstate=oracle.load(case);ids=a[:,0].astype(int);pos={int(k):i for i,k in enumerate(ids)}
 km=np.vstack([oracle.numeric(p,4) for p in (case/'output').glob('G46_s0_r*_KM.dat')]);ii=[pos[int(k)] for k in km[:,0]];jj=[pos[int(k)] for k in km[:,1]]
 A0=sparse.coo_matrix((km[:,2],(ii,jj)),shape=(len(ids),len(ids))).tocsr();M0=sparse.coo_matrix((km[:,3],(ii,jj)),shape=A0.shape).tocsr();A=(C.T@A0@C).tocsr();M=(C.T@M0@C).tocsr()
 ba=np.vstack([oracle.numeric(p,3) for p in (case/'output').glob('G46_s0_r*_B.dat')]);pids=sorted(set(ba[:,0].astype(int)));pp={k:i for i,k in enumerate(pids)};B0=sparse.coo_matrix((ba[:,2],([pp[int(k)] for k in ba[:,0]],[pos[int(k)] for k in ba[:,1]])),shape=(len(pids),len(ids))).tocsr();B=B0@C
 G=sparse.csr_matrix(M@Z[ci,6:9]);w=sparse.csr_matrix(np.ones((len(pids),1))/np.sqrt(len(pids)));npres=len(pids);nu=A.shape[0];zpp=sparse.csr_matrix((npres,npres));z11=sparse.csr_matrix((1,1));z33=sparse.csr_matrix((3,3));z13=sparse.csr_matrix((1,3));z31=z13.T;zu1=sparse.csr_matrix((nu,1));zp3=sparse.csr_matrix((npres,3))
 F=np.asarray(C.T@actions[:,0]);old=sparse.bmat([[A,B.T,zu1],[B,zpp,w],[zu1.T,w.T,z11]],format='csc');rhs=np.r_[F,np.zeros(npres+1)];x=spsolve(old,rhs)
 aug=sparse.bmat([[A,B.T,G,zu1],[B,zpp,zp3,w],[G.T,zp3.T,z33,z31],[zu1.T,w.T,z13,z11]],format='csc');b=np.r_[F,np.zeros(npres+4)];y=spsolve(aug,b);c.need(np.isfinite(x).all() and np.isfinite(y).all(),'SADDLE_SOLVE_FINITE')
 u=x[:nu];v=y[:nu];p=y[nu:nu+npres];lm=y[nu+npres:nu+npres+3];added=np.asarray(G@lm);res=A@v+B.T@p-F;scale=max(np.linalg.norm(F),1e-300);du=v-u;energy=float(du@(A@du));work=abs(float(v@added));oldwork=max(abs(float(u@F)),1e-300)
 row={'case':case.name,'candidate':'[A B^T MZ; B 0 0; Z^T M 0 0] on actual reduced C space; auxiliary Euclidean pressure mean explicitly fixed for this independent oracle only','not_native_ASPECT_solution':True,'near_null_rotations_not_claimed_exact_gauge':True,'saddle_relative_residual':float(np.linalg.norm(aug@y-b)/max(np.linalg.norm(b),1.)),'original_ungauged_momentum_residual_relative':float(np.linalg.norm(res)/scale),'mass_gauge_multiplier':lm.tolist(),'added_load_relative':float(np.linalg.norm(added)/scale),'added_work_relative':work/oldwork,'velocity_change_M_norm':float(np.sqrt(max(du@(M@du),0.))),'strain_energy_of_velocity_change':energy,'pressure_mean_multiplier_before':float(x[-1]),'pressure_mean_multiplier_after':float(y[-1]),'pressure_auxiliary_policy':'independent oracle, not native surface normalization; does not qualify native pressure/datum','acceptance':False,'status':'NOT_ADMITTED_AS_EXACT_GAUGE_NON_NULL_MODES',**c.SCOPE}
 c.write(c.ROOT/output,row);print('SADDLE_REJECTED',row['original_ungauged_momentum_residual_relative'],row['added_work_relative'],flush=True)
if __name__=='__main__':run(Path(sys.argv[1]))
