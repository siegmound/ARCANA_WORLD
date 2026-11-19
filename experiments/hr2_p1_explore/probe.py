"""Explicit short manufactured EXPLORE probe with independent spherical oracles."""
import argparse,math,json,time,resource,hashlib,sys,os
from pathlib import Path
import numpy as np
import scipy
from .model import Operator,sphere,packet

def averages(w,h,mode):
    phi=np.linspace(-math.pi/2,math.pi/2,h+1);lam=np.linspace(-math.pi,math.pi,w+1);u=np.sin(phi);d=2*math.pi/w
    z=np.repeat((u[:-1]+u[1:])/2,w)
    lat=np.diff(phi/2+np.sin(2*phi)/4)/np.diff(u)
    x=(lat[:,None]*np.diff(np.sin(lam))[None,:]/d).ravel()
    y=(lat[:,None]*(-np.diff(np.cos(lam)))[None,:]/d).ravel()
    if mode=='z':return z,2
    if mode=='x':return x,2
    if mode=='y':return y,2
    if mode=='rotated':return (x+2*y+3*z)/math.sqrt(14),2
    if mode=='q':return np.repeat((u[:-1]**2+u[:-1]*u[1:]+u[1:]**2)/3-1/3,w),6
    raise ValueError(mode)

def face_reference(m,mode,k):
    p=m.phi;l=m.lam;d=math.pi/m.height;ew=m.axis==0
    z=np.where(ew,0.,-k*d*np.cos(p)**2)
    x=np.where(ew,k*d*np.sin(l),k*np.cos(p)*np.sin(p)*(np.sin(l+d/2)-np.sin(l-d/2)))
    y=np.where(ew,-k*d*np.cos(l),k*np.cos(p)*np.sin(p)*(np.cos(l-d/2)-np.cos(l+d/2)))
    if mode=='z':return z
    if mode=='x':return x
    if mode=='y':return y
    if mode=='rotated':return (x+2*y+3*z)/math.sqrt(14)
    if mode=='q':return np.where(ew,0.,-2*k*d*np.sin(p)*np.cos(p)**2)
    raise ValueError(mode)

def norm(e,A):
    weights=A/math.fsum(map(float,A))
    return {'L1':math.fsum(map(float,weights*np.abs(e))),'L2':math.sqrt(math.fsum(map(float,weights*e*e))),'Linf':float(np.abs(e).max())}

def local_controls():
    from types import SimpleNamespace
    op=Operator.__new__(Operator);A=np.array([1.,2.,3.,4.]);V=np.array([1.,4.,9.,16.]);i=np.array([0,0,1,2]);j=np.array([1,2,3,3])
    op.mesh=SimpleNamespace(areas=A,first=i,second=j);op.c=np.array([1.,2.,3.,4.]);op.cfl=1/6
    op.high=lambda h:op.c*(h[i]-h[j])
    actual,d=op.step(V,.1);np.testing.assert_allclose(actual,[1.5,4.5,9,15],rtol=0,atol=3e-14)
    op.high=lambda h:np.array([19.,-4.,-6.,-4.]);limited,ld=op.step(V,.1)
    np.testing.assert_allclose(limited,[1.,5.,9.,15.],rtol=0,atol=5e-14)
    rejects=[]
    for state,dt in [(V,.2),(-V,.1),(V,float('nan'))]:
        try:op.step(state,dt)
        except ValueError as e:rejects.append(str(e))
        else:raise AssertionError('NEGATIVE_CONTROL')
    assert np.array_equal(V,[1.,4.,9.,16.])
    return {'rational_low':actual.tolist(),'rational_limited':limited.tolist(),'limiter':ld,'rejected':rejects}

def run_case(root,height,order,minimum_steps):
    start=time.perf_counter();cpu0=resource.getrusage(resource.RUSAGE_SELF);w=2*height;m=sphere(w,height);op=Operator(m,order=order);p=root/f'{w}x{height}';p.mkdir()
    packets={}
    for n,pkt in enumerate(op.packets):
        for key in ['patch','M','J','R','g','basis','singular']:packets[f'{n}_{key}']=pkt[key]
    np.savez(p/'coefficients.npz',**packets)
    np.savez(p/'operator.npz',data=op.G.data,indices=op.G.indices,indptr=op.G.indptr,shape=op.G.shape,
      areas=m.areas,first=m.first,second=m.second,axis=m.axis,phi=m.phi,lam=m.lam)
    # Quadrature comparison is a numerical sensitivity observation only.
    comparison=packet(m,0,order+8);base=op.packets[0]
    assert np.array_equal(comparison['patch'],base['patch'])
    quadrature={'orders':[order,order+8],'M_max_difference':float(np.abs(base['M']-comparison['M']).max()),
      'J_max_difference':float(np.abs(base['J']-comparison['J']).max()),'g_max_difference':float(np.abs(base['g']-comparison['g']).max())}
    rows=[];totalstep=0.
    for mode in ['z','x','y','rotated','q']:
        modearr,eigen=averages(w,height,mode);h0=8+modearr;V0=m.areas*h0;T=.0001
        exact=8+math.exp(-eigen*.01*T)*modearr
        rates=op.high(h0);ref=face_reference(m,mode,op.kappa);div=np.bincount(m.second,weights=rates,minlength=len(h0))-np.bincount(m.first,weights=rates,minlength=len(h0))
        defect=div/m.areas+eigen*.01*modearr
        row={'mode':mode,'tendency_errors':norm(defect,m.areas),'flux_error_max_over_kappa':float(np.abs(rates-ref).max()/op.kappa)}
        for label,mask in [('EW',m.axis==0),('NS',m.axis==1),('first_polar_EW',(m.axis==0)&(np.abs(m.phi)>math.pi/2-math.pi/height))]:
            row[label+'_max_error_over_kappa']=float(np.max(np.abs(rates[mask]-ref[mask]))/op.kappa)
        # Main/half schedule fixed explicitly rather than borrowed from output cadence.
        timer=time.perf_counter();main,d=op.advance(V0,T,minimum_steps=minimum_steps);half,dh=op.advance(V0,T,minimum_steps=2*d['steps']);elapsed=time.perf_counter()-timer;totalstep+=elapsed
        row.update({'end_year':T,'errors_m':norm(main/m.areas-exact,m.areas),'half_errors_m':norm(half/m.areas-exact,m.areas),
          'main_half_L2_m':norm((main-half)/m.areas,m.areas)['L2'],'integration_s':elapsed,'main':d,'half':dh,
          'total_volume_residual_m3':math.fsum(map(float,main))-math.fsum(map(float,V0))})
        np.savez(p/(mode+'.npz'),initial_h=h0,exact_h=exact,main_h=main/m.areas,half_h=half/m.areas,
          high_rate=rates,exact_rate=ref,tendency_defect=defect,errors=main/m.areas-exact)
        rows.append(row)
    # Independent topology / rotational equivariance / constants / spike/random positivity.
    assert len(set(zip(np.minimum(m.first,m.second),np.maximum(m.first,m.second))))==len(m.first)==w*(2*height-1)
    assert abs(math.fsum(map(float,m.areas))/(4*math.pi*m.radius**2)-1)<2e-14
    assert np.array_equal(op.high(np.full(len(m.areas),8.)),np.zeros(len(m.first)))
    unshifted=op.high(8+averages(w,height,'x')[0]);shifted=op.high(np.roll((8+averages(w,height,'x')[0]).reshape(height,w),1,axis=1).ravel())
    equiv=float(np.max(np.abs(shifted-np.roll(unshifted.reshape(2*height-1,w),1,axis=1).ravel()))/op.kappa)
    rng=np.random.default_rng(67031);controls={}
    for label,h in [('spike',np.eye(1,len(m.areas),0).ravel()),('random',rng.uniform(0,1,len(m.areas))),('constant',np.full(len(m.areas),8.)),('zero',np.zeros(len(m.areas)))]:
        initial=m.areas*h;final,diagnostic=op.advance(initial,8*op.cfl,minimum_steps=8)
        assert (final>=0).all();np.testing.assert_array_equal(final,initial) if label in ['constant','zero'] else None
        controls[label]=diagnostic;controls[label]['total_relative_mass_residual']=float((math.fsum(map(float,final))-math.fsum(map(float,initial)))/max(1,math.fsum(map(float,initial))))
    # The shifted sine mode has a physically nonzero seam flux.
    seam=np.arange(height)*w+w-1;yrate=op.high(8+averages(w,height,'y')[0]);yref=face_reference(m,'y',op.kappa)
    assert (yref[seam]>0).all();seam_relative=float(np.max(np.abs(yrate[seam]-yref[seam]))/np.max(yref[seam]))
    cpu=resource.getrusage(resource.RUSAGE_SELF)
    result={'width':w,'height':height,'cells':len(m.areas),'faces':len(m.first),'quadrature':quadrature,'mode_results':rows,'controls':controls,
      'rotational_equivariance_error_over_kappa':equiv,'shifted_sine_seam_max_relative_error':seam_relative,
      'packet_count':len(op.packets),'max_condition':max(x['condition'] for x in op.packets),'max_reproduction':max(x['reproduction'] for x in op.packets),
      'G_nnz':int(op.G.nnz),'G_bytes':int(op.G.data.nbytes+op.G.indices.nbytes+op.G.indptr.nbytes),'assembly_s':op.assembly_s,
      'integrations_main_half_s':totalstep,'case_wall_s':time.perf_counter()-start,'case_cpu_user_s':cpu.ru_utime-cpu0.ru_utime,
      'case_cpu_system_s':cpu.ru_stime-cpu0.ru_stime,'cumulative_peak_rss_kib':cpu.ru_maxrss,'cfl_year':op.cfl,
      'authority':'EXPLORE_MANUFACTURED_NOT_VALIDATE','stock_clipping_or_mass_renormalization':False}
    (p/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps({'mesh':[w,height],'assembly_s':op.assembly_s,'mode_L2':{x['mode']:x['errors_m']['L2'] for x in rows},'controls':'PASS'}),flush=True)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--heights',nargs='+',type=int,choices=[8,16,32,64,128],required=True);ap.add_argument('--order',type=int,choices=[12,16,24],default=16);ap.add_argument('--minimum-steps',type=int,default=32);args=ap.parse_args()
    if not 1<=args.minimum_steps<=128:ap.error('minimum steps1..128')
    args.output.mkdir(parents=True,exist_ok=False);root=args.output
    start=time.perf_counter();result={'scope':'EXPLORE_ONLY','numpy':np.__version__,'scipy':scipy.__version__,'python':sys.version,'argv':sys.argv,
      'environment_threads':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']},'source_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in Path(__file__).parent.glob('*.py')}}
    (root/'INVOCATION.json').write_text(json.dumps(result,indent=2))
    try:
        result['local_controls']=local_controls();result['cases']=[]
        for h in args.heights:result['cases'].append(run_case(root,h,args.order,args.minimum_steps))
        result['status']='COMPLETED_EXPLORE_NOT_VALIDATED'
    except Exception as e:
        import traceback
        result.update(status='FAILED_EXPLORATORY_ATTEMPT',error=repr(e),traceback=traceback.format_exc());raise
    finally:
        result['wall_s']=time.perf_counter()-start;(root/'RESULT.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
