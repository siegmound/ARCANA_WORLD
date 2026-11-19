"""Short full-FCT corrected timestep sweeps, regressions and compensated restart."""
import argparse,json,time,math,resource,subprocess,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.linalg import expm
from .study import load_case,reference,norms,T
from .compensated import advance,step,physical,save,load

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--resume',type=Path);p.add_argument('--sha');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    if a.resume:
        op,src=load_case(a.archive,16);gsha=hashlib.sha256((src/'operator.npz').read_bytes()).hexdigest();hi,c,meta=load(a.resume,a.sha,gsha)
        for _ in range(4):hi,c,d=step(op,hi,c,meta['dt'])
        np.savez(a.output/'final.npz',hi=hi,correction=c);return
    start=time.perf_counter();result={'scope':'EXPLORE_CORRECTED_FULL_FCT_NOT_VALIDATE','rows':[]};reference_checks=[]
    for w in [16,32,64,128,256]:
        op,src=load_case(a.archive,w);A=op.mesh.areas
        for mode in ['x','y','z','q']:
            with np.load(src/(mode+'.npz'),allow_pickle=False) as z:V0=A*z['initial_h'];continuum=z['exact_h']
            ref,rd=reference(op,V0,mode)
            if w<=32 and mode=='x':
                n=len(A);f=len(op.mesh.first);idx=np.arange(f)
                D=csr_matrix((np.r_[-np.ones(f),np.ones(f)],(np.r_[op.mesh.first,op.mesh.second],np.r_[idx,idx])),shape=(n,f))
                L=(op.kappa*(D@op.G)).toarray()/A[:,None];H=np.eye(n);H[:,0]-=1;L=L@H
                # Small full-space extended vector Taylor gives independent FFT check.
                initial=V0.astype(np.longdouble)/A;M=(T*L).astype(np.longdouble);term=M@(initial-8);dv=term.copy()
                for j in range(2,100):
                    term=M@term/j;dv+=term
                    if np.max(np.abs(term))<1e-27:break
                difference=norms(initial+dv-ref,A)
                assert difference['Linf']<2e-15;reference_checks.append({'width':w,'full_space_vs_Fourier_m':difference})
            counts=[32,64] if w<256 else ([64,128,256,512] if mode=='x' else [128,256,512])
            previous=None;preverror=None
            for n in counts:
                timer=time.perf_counter();hi,c,diag=advance(op,V0,n);elapsed=time.perf_counter()-timer;heights=physical(hi,c)/A
                errors=norms(heights-continuum,A);row={'width':w,'mode':mode,'steps':n,'dt':T/n,'errors_continuum_m':errors,
                  'errors_semidiscrete_m':norms(heights-ref,A),'wall_s':elapsed,'diagnostic':diag,'reference_diagnostic':rd,
                  'mass_relative_residual':float((np.sum(physical(hi,c))-np.sum(V0.astype(np.longdouble)))/np.sum(V0.astype(np.longdouble)))}
                if previous is not None:
                    row['main_half_L2_m']=norms(previous-heights,A)['L2'];row['main_half_fraction']=row['main_half_L2_m']/preverror
                previous=heights.copy();preverror=errors['L2'];result['rows'].append(row)
                assert diag['limited_faces_total']==0
                np.savez(a.output/f'w{w}_{mode}_{n}.npz',volume_hi=hi,correction=c,height=heights,reference_h=ref,continuum_h=continuum)
                print(json.dumps({k:row[k] for k in ['width','mode','steps','errors_continuum_m','errors_semidiscrete_m','wall_s']}),flush=True)
        # Positivity/range controls use real limiter and persisted correction.
        controls={};rng=np.random.default_rng(67031)
        for label,h in [('spike',np.eye(1,len(A),0).ravel()),('random',rng.uniform(0,1,len(A))),('constant',np.full(len(A),8.)),('zero',np.zeros(len(A)))]:
            V0=A*h;hi,c,d=advance(op,V0,8,end=op.cfl*8);eff=physical(hi,c)
            assert (eff>=0).all();assert (eff/A).min()>=h.min()-3e-13 and (eff/A).max()<=h.max()+3e-13
            if label in ['constant','zero']:assert np.array_equal(hi,V0) and np.array_equal(c,np.zeros_like(c))
            controls[label]=d;controls[label]['relative_mass_residual']=float((np.sum(eff)-np.sum(V0.astype(np.longdouble)))/max(1,np.sum(V0.astype(np.longdouble))))
        result.setdefault('controls',{})[str(w)]=controls
        if w==16:
            V0=A*rng.uniform(.1,1,len(A));dt=op.cfl/4;direct=V0.copy();dc=np.zeros_like(V0)
            for _ in range(8):direct,dc,d=step(op,direct,dc,dt)
            mid=V0.copy();mc=np.zeros_like(V0)
            for _ in range(4):mid,mc,d=step(op,mid,mc,dt)
            gsha=hashlib.sha256((src/'operator.npz').read_bytes()).hexdigest();cp=a.output/'compensated_checkpoint.npz';digest=save(cp,mid,mc,4,dt,gsha)
            hi,c,meta=load(cp,digest,gsha)
            for _ in range(4):hi,c,d=step(op,hi,c,meta['dt'])
            assert np.array_equal(hi,direct) and np.array_equal(c,dc)
            child=a.output/'child';cmd=[sys.executable,'-B','-m','hr2_p1_explore_dt.checks','--archive',str(a.archive),'--output',str(child),'--resume',str(cp),'--sha',digest]
            res=subprocess.run(cmd,capture_output=True,text=True);(a.output/'child.stderr').write_text(res.stderr);assert res.returncode==0
            with np.load(child/'final.npz',allow_pickle=False) as z:assert np.array_equal(z['hi'],direct) and np.array_equal(z['correction'],dc)
            negatives=[]
            for htest,ctest,dtest in [(-V0,np.zeros_like(V0),dt),(V0,np.zeros_like(V0),2*op.cfl),(V0,np.zeros_like(V0),float('nan'))]:
                try:step(op,htest,ctest,dtest)
                except ValueError as err:negatives.append(str(err))
                else:raise AssertionError('BAD_INPUT')
            try:load(cp,'0'*64,gsha)
            except ValueError as err:negatives.append(str(err))
            else:raise AssertionError('BAD_CHECKPOINT')
            result['restart']={'direct_split_child_hi_and_correction_bitwise_equal':True,'native_bytes':cp.stat().st_size,'negative_rejections':negatives,'correction_required_for_exact_resume':True,'B0_qualified':False}
    result['reference_crosschecks']=reference_checks;result['wall_s']=time.perf_counter()-start;result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result['status']='COMPLETED_EXPLORE_CORRECTED_NOT_VALIDATE';(a.output/'RESULT.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
