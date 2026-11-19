"""Opt-in single-version reduced validation; numerical, not scientific admission."""
import argparse,json,time,math,resource,hashlib,subprocess,sys,traceback
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from hr2_p1_explore.model import sphere
from hr2_p1_explore.probe import face_reference
from hr2_p1_explore_dt.compact import CompactOperator
from hr2_p1_explore_dt.compensated import step,physical,save,load
from hr2_p1_explore_dt.study import norms,reference,load_case
from .fixtures import harmonic,cell_reference,nonharmonic_flux

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(contract,expected):
    if sha(contract)!=expected:raise ValueError('FROZEN_VERSION_SHA')
    c=json.loads(contract.read_text());root=Path(c['repository'])
    for k,v in c['files'].items():
        if sha(root/k)!=v:raise ValueError('FROZEN_SOURCE_CHANGED:'+k)
    return c

def evolve(op,V0,count,T):
    hi=V0.copy();c=np.zeros_like(hi);diags=[];start=time.perf_counter()
    for _ in range(count):hi,c,d=step(op,hi,c,T/count);diags.append(d)
    end=physical(hi,c);ratio=max(abs(d['residual_m3'])/max(d['roundoff_bound_m3'],np.finfo(float).tiny) for d in diags)
    return hi,c,{'steps':count,'dt':T/count,'wall_s':time.perf_counter()-start,'limited_faces':sum(d['limited_faces'] for d in diags),
      'minimum_h':min(d['minimum_h'] for d in diags),'maximum_h':max(d['maximum_h'] for d in diags),'max_residual_to_bound':ratio,
      'max_step_residual_m3':max(abs(d['residual_m3']) for d in diags),'total_relative_mass_residual':float((np.sum(end)-np.sum(V0.astype(np.longdouble)))/max(1,np.sum(V0.astype(np.longdouble))))}

def reference_crosscheck(op,V0,ref,T):
    m=op.mesh;n=len(m.areas);f=len(m.first);idx=np.arange(f)
    D=csr_matrix((np.r_[-np.ones(f),np.ones(f)],(np.r_[m.first,m.second],np.r_[idx,idx])),shape=(n,f))
    L=(op.kappa*(D@op.G)).toarray()/m.areas[:,None];H=np.eye(n);H[:,0]-=1;L=L@H
    initial=V0.astype(np.longdouble)/m.areas;M=(T*L).astype(np.longdouble);term=M@(initial-8);delta=term.copy()
    for j in range(2,101):
        term=M@term/j;delta+=term
        if np.max(np.abs(term))<1e-27:break
    return norms(initial+delta-ref,m.areas)

def restart_tests(op,archive,output,contract,expected,width):
    m=op.mesh;A=m.areas;rng=np.random.default_rng(778);V0=A*rng.uniform(.1,1,len(A));dt=op.cfl/4
    hi=V0.copy();c=np.zeros_like(hi)
    for _ in range(16):hi,c,d=step(op,hi,c,dt)
    mid=V0.copy();mc=np.zeros_like(mid)
    for _ in range(8):mid,mc,d=step(op,mid,mc,dt)
    _,src=load_case(archive,width);geometry=sha(src/'operator.npz');cp=output/'checkpoint.npz';digest=save(cp,mid,mc,8,dt,geometry)
    restore,rc,meta=load(cp,digest,geometry)
    for _ in range(8):restore,rc,d=step(op,restore,rc,dt)
    ok=np.array_equal(restore,hi) and np.array_equal(rc,c)
    cmd=[sys.executable,'-B','-m','hr2_p1_reduced_validate_v1.run','--contract',str(contract),'--expected-sha',expected,'--archive',str(archive),
      '--output',str(output/'child'),'--resume',str(cp),'--checkpoint-sha',digest,'--width',str(width)]
    timer=time.perf_counter();child=subprocess.run(cmd,capture_output=True,text=True);elapsed=time.perf_counter()-timer
    (output/'child.stdout').write_text(child.stdout);(output/'child.stderr').write_text(child.stderr)
    childok=False
    if child.returncode==0:
        with np.load(output/'child/final.npz',allow_pickle=False) as z:childok=np.array_equal(z['hi'],hi) and np.array_equal(z['correction'],c)
    rejected={}
    def expect(name,func):
        try:func()
        except Exception as err:rejected[name]={'rejected':True,'error':str(err)}
        else:rejected[name]={'rejected':False}
    bad=output/'corrupt.npz';raw=bytearray(cp.read_bytes());raw[len(raw)//2]^=1;bad.write_bytes(raw)
    expect('corrupt',lambda:load(bad,digest,geometry));expect('wrong_geometry_argument',lambda:load(cp,digest,'0'*64))
    for key in ['source_sha','geometry_sha']:
        with np.load(cp,allow_pickle=False) as z:metadata=json.loads(z['metadata'].tobytes());hh=z['hi'];cc=z['correction']
        metadata[key]='0'*64;wrong=output/(key+'_wrong.npz')
        with wrong.open('xb') as f:np.savez(f,hi=hh,correction=cc,metadata=np.frombuffer(json.dumps(metadata).encode(),dtype='u1'))
        expect(key+'_wrong_with_fresh_outer_SHA',lambda p=wrong:load(p,sha(p),geometry))
    expect('wrong_frozen_version',lambda:verify(contract,'0'*64))
    return {'in_process_both_arrays_bitwise':bool(ok),'child_both_arrays_bitwise':bool(childok),'child_exit':child.returncode,
      'child_wall_s':elapsed,'checkpoint_bytes':cp.stat().st_size,'checkpoint_sha':digest,'negative_tests':rejected,
      'completed_steps':16,'dt_year':dt,'geometry_companion_required':True,'B0_qualified':False,
      'PASS':bool(ok and childok and all(v['rejected'] for v in rejected.values()))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--contract',type=Path,required=True);ap.add_argument('--expected-sha',required=True);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--execute-reduced-validate',action='store_true');ap.add_argument('--resume',type=Path);ap.add_argument('--checkpoint-sha');ap.add_argument('--width',type=int,choices=[16,32,128,256]);a=ap.parse_args()
    contract=verify(a.contract,a.expected_sha);a.output.mkdir(parents=True,exist_ok=False)
    if a.resume:
        op,src=load_case(a.archive,a.width);hi,c,meta=load(a.resume,a.checkpoint_sha,sha(src/'operator.npz'))
        for _ in range(8):hi,c,d=step(op,hi,c,meta['dt'])
        np.savez(a.output/'final.npz',hi=hi,correction=c)
        (a.output/'RESTORE.json').write_text(json.dumps({'final_steps':meta['steps']+8,'final_year':(meta['steps']+8)*meta['dt'],'version':a.expected_sha}));return
    if not a.execute_reduced_validate:ap.error('Explicit --execute-reduced-validate required')
    criteria=json.loads((Path(contract['repository'])/'experiments/hr2_p1_reduced_validate_v1/acceptance.json').read_text());root=a.output
    start=time.perf_counter();usage0=resource.getrusage(resource.RUSAGE_SELF);result={'version_sha':a.expected_sha,'status':'RUNNING','criteria':criteria,'cases':[],'areas':{}}
    result['invocation']={'argv':sys.argv,'numpy':np.__version__,'python':sys.version,'source_version_verified':True}
    try:
        reference_pass=True;numeric_pass=True;flux_pass=True;time_pass=True
        for w,h in criteria['grids']:
            case_dir=root/f'{w}x{h}';case_dir.mkdir();timer=time.perf_counter();m=sphere(w,h);op=CompactOperator(m);assembly=time.perf_counter()-timer
            oldop,oldsrc=load_case(a.archive,w)
            matrix_equal=np.array_equal(op.G.data,oldop.G.data) and np.array_equal(op.G.indices,oldop.G.indices) and np.array_equal(op.G.indptr,oldop.G.indptr)
            if not matrix_equal:raise ValueError('FRESH_GEOMETRY_MISMATCH')
            del oldop
            case={'width':w,'height':h,'assembly_s':assembly,'matrix_bytes':int(op.G.data.nbytes+op.G.indices.nbytes+op.G.indptr.nbytes),
              'matrix_bitwise_archived':matrix_equal,'matrix_nnz':op.G.nnz,'max_condition':max(p['condition'] for p in op.packets),'cfl_year':op.cfl,'fields':[]}
            for mode in criteria['fields']:
                timer=time.perf_counter()
                if mode=='exp_rotated':
                    h0=np.asarray(cell_reference(w,h,0,32,initial_exp=True),dtype=float)
                    continuum=cell_reference(w,h,.0001,32);comparison=cell_reference(w,h,.0001,48)
                    initial_check=cell_reference(w,h,0,32)
                    refdiff=norms(continuum-comparison,m.areas);initialdiff=norms(h0.astype(np.longdouble)-initial_check,m.areas)
                    exact_flux=nonharmonic_flux(m,op.kappa,32);other_flux=nonharmonic_flux(m,op.kappa,48)
                    flux_sensitivity=float(np.max(np.abs(exact_flux-other_flux))/op.kappa)
                    reference_pass &= refdiff['Linf']<=criteria['reference_quadrature_Linf_m_max'] and initialdiff['Linf']<=2e-15 and flux_sensitivity<=2e-12
                else:
                    with np.load(oldsrc/(mode+'.npz'),allow_pickle=False) as z:h0=z['initial_h'];continuum=z['exact_h']
                    # Separate formula evaluation preserves original analytic fixture identity.
                    check=harmonic(w,h,mode,.0001);refdiff=norms(check-continuum,m.areas);initialdiff={'Linf':0.}
                    exact_flux=face_reference(m,mode,op.kappa);flux_sensitivity=0.;reference_pass &= refdiff['Linf']<=2e-15
                V0=m.areas*h0;semidiscrete,refdiag=reference(op,V0,mode)
                cross=None
                if w<=32 and mode in ['x','exp_rotated']:
                    cross=reference_crosscheck(op,V0,semidiscrete,.0001);reference_pass &= cross['Linf']<=criteria['full_space_Fourier_reference_Linf_m_max']
                rates=op.high(np.asarray(V0/m.areas,dtype=float));error=rates-exact_flux;faces={}
                for label,mask in [('EW',m.axis==0),('NS',m.axis==1),('polar_EW',(m.axis==0)&(np.abs(m.phi)>math.pi/2-math.pi/h)),('polar_NS',(m.axis==1)&(np.abs(m.phi)>math.pi/2-1.5*math.pi/h))]:
                    faces[label]={'max_error_over_kappa':float(np.max(np.abs(error[mask]))/op.kappa),'max_reference_over_kappa':float(np.max(np.abs(exact_flux[mask]))/op.kappa)}
                    if faces[label]['max_reference_over_kappa']<1e-14:flux_pass &= faces[label]['max_error_over_kappa']<=criteria['zero_reference_flux_error_over_kappa_max']
                seam=np.arange(h)*w+w-1
                seam_ok=True
                if mode in ['y','exp_rotated']:seam_ok=bool((exact_flux[seam]>0).all() and (rates[seam]>0).all());flux_pass &= seam_ok
                row={'mode':mode,'reference_quadrature_difference_m':refdiff,'initial_reference_difference_m':initialdiff,'flux_reference_sensitivity_over_kappa':flux_sensitivity,
                  'semidiscrete_diagnostic':refdiag,'full_reference_crosscheck_m':cross,'faces':faces,'nonzero_seam_sign_PASS':seam_ok,'runs':[]}
                previous=None;preverr=None;previous_timeerr=None;counts=[128,256,512] if w==256 else [128,256]
                for n in counts:
                    hi,c,d=evolve(op,V0,n,.0001);heights=physical(hi,c)/m.areas;err=norms(heights-continuum,m.areas);terr=norms(heights-semidiscrete,m.areas)
                    rr={'steps':n,'error_m':err,'temporal_error_m':terr,'diagnostic':d}
                    if previous is not None:
                        rr['main_half_L2_m']=norms(previous-heights,m.areas)['L2'];rr['main_half_fraction']=rr['main_half_L2_m']/preverr
                        if w==256:
                            time_pass &= rr['main_half_fraction']<=criteria['main_half_fraction_max']
                            rr['temporal_order']=math.log(previous_timeerr/terr['L2'],2)
                            time_pass &= .9<=rr['temporal_order']<=1.2
                    numeric_pass &= d['minimum_h']>=0 and d['max_residual_to_bound']<=1
                    time_pass &= d['limited_faces']==0
                    row['runs'].append(rr);previous=heights.copy();preverr=err['L2'];previous_timeerr=terr['L2']
                    np.savez(case_dir/f'{mode}_{n}.npz',hi=hi,correction=c,height=heights,continuum=continuum,semidiscrete=semidiscrete)
                np.savez(case_dir/f'{mode}_initial_flux.npz',initial_volume=V0,initial_h=h0,rate=rates,exact_rate=exact_flux,area=m.areas,axis=m.axis,phi=m.phi,lam=m.lam)
                row['field_total_wall_s']=time.perf_counter()-timer;case['fields'].append(row)
                print(json.dumps({'grid':[w,h],'mode':mode,'fine_L2':row['runs'][1]['error_m']['L2'],'fraction':row['runs'][1]['main_half_fraction']}),flush=True)
            controls={};rng=np.random.default_rng(67031)
            for label,values in [('spike',np.eye(1,len(m.areas),0).ravel()),('random',rng.uniform(0,1,len(m.areas))),('constant',np.full(len(m.areas),8.)),('zero',np.zeros(len(m.areas)))]:
                V0=m.areas*values;hi,c,d=evolve(op,V0,16,16*op.cfl);end=physical(hi,c)/m.areas
                good=bool((end>=0).all() and end.min()>=values.min()-128*np.finfo(float).eps*max(1,float(values.max())) and end.max()<=values.max()+128*np.finfo(float).eps*max(1,float(values.max())))
                if label in ['spike','random']:good &= d['limited_faces']>0
                else:good &= np.array_equal(hi,V0) and np.array_equal(c,np.zeros_like(c))
                d['PASS']=bool(good);numeric_pass &= good;controls[label]=d
                np.savez(case_dir/f'control_{label}.npz',initial=V0,hi=hi,correction=c)
            case['controls']=controls
            if w in [32,256]:
                dest=case_dir/'restart';dest.mkdir();case['restart']=restart_tests(op,a.archive,dest,a.contract,a.expected_sha,w)
            case['process_cumulative_peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            result['cases'].append(case);(case_dir/'RESULT.json').write_text(json.dumps(case,indent=2))
        # Nonuniform refinement ratios: compare actual width ratio, not assumed doubling.
        spatial_pass=True;flux_convergence=True;orders=[]
        for mode in criteria['fields']:
            sequence=[next(f for f in c['fields'] if f['mode']==mode) for c in result['cases']]
            for j in range(3):
                coarse=sequence[j];fine=sequence[j+1];ratio=criteria['grids'][j+1][0]/criteria['grids'][j][0]
                vals={key:math.log(coarse['runs'][1]['error_m'][key]/fine['runs'][1]['error_m'][key])/math.log(ratio) for key in ['L1','L2','Linf']}
                spatial_pass &= all(v>=criteria['spatial_order_min'] for v in vals.values());orders.append({'mode':mode,'coarse_width':criteria['grids'][j][0],'fine_width':criteria['grids'][j+1][0],'orders':vals})
                for label in ['EW','NS','polar_EW','polar_NS']:
                    if coarse['faces'][label]['max_reference_over_kappa']>1e-14:flux_convergence &= fine['faces'][label]['max_error_over_kappa']<coarse['faces'][label]['max_error_over_kappa']
        restart_pass=all(c['restart']['PASS'] for c in result['cases'] if 'restart'in c)
        result['spatial_orders']=orders;result['areas']={
          'independent_references':'PASS' if reference_pass else 'BLOCKED','spatial_convergence':'PASS' if spatial_pass else 'BLOCKED',
          'temporal_precision':'PASS' if time_pass else 'BLOCKED','conservation_positivity_limiter':'PASS' if numeric_pass else 'BLOCKED',
          'polar_seam_flux':'PASS' if flux_pass and flux_convergence else 'BLOCKED','restart_and_identity':'PASS' if restart_pass else 'BLOCKED',
          'measured_resources':'PASS'}
        verify(a.contract,a.expected_sha);result['status']='PASS_REDUCED_NUMERICAL_VALIDATE' if all(v=='PASS' for v in result['areas'].values()) else 'BLOCKED_REDUCED_NUMERICAL_VALIDATE'
    except Exception as err:
        result.update(status='BLOCKED_SOFTWARE_OR_NUMERICAL_ERROR',error=repr(err),traceback=traceback.format_exc());raise
    finally:
        u=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
        result.update(wall_s=time.perf_counter()-start,cpu_user_s=u.ru_utime-usage0.ru_utime,cpu_system_s=u.ru_stime-usage0.ru_stime,
          child_cpu_user_s=child.ru_utime,child_cpu_system_s=child.ru_stime,process_peak_rss_kib=u.ru_maxrss,old_Q1_complete=False,scientific_authority=False)
        (root/'RESULT.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
