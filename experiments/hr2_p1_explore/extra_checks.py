"""Small temporal, directional, native restart and negative EXPLORE checks."""
import argparse,json,time,math,resource,subprocess,sys
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.linalg import expm
from .model import Operator,sphere,packet
from .probe import averages,norm,run_case
from .native import save,load

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--resume',type=Path);p.add_argument('--sha');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    if a.resume:
        start=time.perf_counter();op,V,meta=load(a.resume,a.sha)
        for _ in range(4):V,d=op.step(V,meta['dt'])
        np.save(a.output/'final.npy',V,allow_pickle=False);(a.output/'RESULT.json').write_text(json.dumps({'restore_and_4_steps_s':time.perf_counter()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2));return
    start=time.perf_counter();m=sphere(16,8);op=Operator(m);result={}
    # Independent-in-time dense exponential of the same numerical spatial matrix.
    inc=csr_matrix((np.r_[-np.ones(len(m.first)),np.ones(len(m.first))],(np.r_[m.first,m.second],np.r_[np.arange(len(m.first)),np.arange(len(m.first))])),shape=(len(m.areas),len(m.first)))
    L=(op.kappa*(inc@op.G)).toarray()/m.areas[:,None]
    H=np.eye(len(m.areas));H[:,0]-=1.;L=L@H # include the runtime global anchor exactly in the reference definition
    mode,e=averages(16,8,'y');T=.2
    reference=8+expm(T*L)@mode;V0=m.areas*(8+mode);counts=[2,4,8];temporal=[]
    for count in counts:
        V,d=op.advance(V0,T,minimum_steps=count)
        temporal.append({'steps':d['steps'],'L2_m':norm(V/m.areas-reference,m.areas)['L2'],'limited_faces':d['limited_faces_total']})
    orders=[math.log(temporal[j]['L2_m']/temporal[j+1]['L2_m'],2) for j in range(2)]
    assert all(x['limited_faces']==0 for x in temporal) and all(.9<v<1.2 for v in orders)
    result['temporal']={'T_year':T,'rows':temporal,'observed_orders':orders,'reference':'scipy.linalg.expm of same spatial operator; standard numeric, not interval-certified'}
    # Fresh face builds test the cache/longitude rotation using generic coefficients.
    cache=[]
    for face in [15,7,16*8+15]:
        direct=packet(m,face,16);band,col=divmod(face,m.width);base=op.packets[band]
        ids=(base['patch']//m.width)*m.width+(base['patch']%m.width+col)%m.width
        mapping=dict(zip(map(int,ids),base['g']));assert set(mapping)==set(map(int,direct['patch']))
        error=float(np.max(np.abs(direct['g']-np.array([mapping[int(x)] for x in direct['patch']]))))
        assert error<5e-12;cache.append({'face':face,'max_coefficient_rotation_error':error})
    result['fresh_face_rotation']=cache
    dt=op.cfl/4;h=np.random.default_rng(213).uniform(.1,1,len(m.areas));initial=m.areas*h;direct=initial.copy()
    for _ in range(8):direct,d=op.step(direct,dt)
    mid=initial.copy()
    for _ in range(4):mid,d=op.step(mid,dt)
    cp=a.output/'native.npz';timer=time.perf_counter();sha=save(cp,op,mid,4,dt);write=time.perf_counter()-timer
    op2,restored,meta=load(cp,sha)
    for _ in range(4):restored,d=op2.step(restored,dt)
    assert np.array_equal(restored,direct)
    child=a.output/'child';timer=time.perf_counter();code=subprocess.run([sys.executable,'-B','-m','hr2_p1_explore.extra_checks','--output',str(child),'--resume',str(cp),'--sha',sha],capture_output=True,text=True)
    (a.output/'child.stdout').write_text(code.stdout);(a.output/'child.stderr').write_text(code.stderr)
    assert code.returncode==0;assert np.array_equal(np.load(child/'final.npy',allow_pickle=False),direct)
    negatives=[]
    try:load(cp,'0'*64)
    except ValueError as e:negatives.append(str(e))
    else:raise AssertionError('BAD_SHA_ADMITTED')
    bad=a.output/'corrupt_native.npz';raw=bytearray(cp.read_bytes());raw[len(raw)//2]^=1;bad.write_bytes(raw)
    try:load(bad,sha)
    except ValueError as e:negatives.append(str(e))
    else:raise AssertionError('CORRUPTION_ADMITTED')
    result['native']={'direct_split_child_bitwise_equal':True,'steps':8,'dt_year':dt,'wall_write_s':write,'child_wall_s':time.perf_counter()-timer,
      'native_bytes':cp.stat().st_size,'sha256':sha,'negative_rejections':negatives,'B0_qualified':False}
    zero=Operator(m,kappa=0);Z,diagn=zero.advance(initial,.001,minimum_steps=1);assert np.array_equal(Z,initial)
    result['zero_kappa_exact']=True
    # Recheck the final model bytes on initial meshes after diagnostic hardening.
    result['final_small_meshes']=[run_case(a.output,h,16,32) for h in [8,16]]
    result['wall_s']=time.perf_counter()-start;result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result['status']='COMPLETED_EXPLORE_NOT_VALIDATE';(a.output/'RESULT.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
