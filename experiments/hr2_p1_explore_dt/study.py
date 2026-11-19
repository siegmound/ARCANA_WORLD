import argparse,json,time,math,resource,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.linalg import expm
from hr2_p1_explore.model import Operator,sphere
from hr2_p1_explore.probe import averages

K=405896410000.;T=.0001

def load_case(root,w):
    sub='extra02' if w<=32 else ('attempt03' if w<=128 else 'attempt04')
    p=root/sub/f'{w}x{w//2}';m=sphere(w,w//2)
    with np.load(p/'operator.npz',allow_pickle=False) as z:
        for k in ['areas','first','second','axis','phi','lam']:assert np.array_equal(z[k],getattr(m,k)),k
        G=csr_matrix((z['data'],z['indices'],z['indptr']),shape=tuple(z['shape']))
    op=Operator.__new__(Operator);op.mesh=m;op.kappa=K;op.order=16;op.G=G
    op.c=K*m.length/m.distance
    C=np.bincount(m.first,weights=op.c,minlength=len(m.areas))+np.bincount(m.second,weights=op.c,minlength=len(m.areas))
    op.cfl=.5*float(np.min(m.areas/C));old=json.loads((p/'RESULT.json').read_text());assert op.cfl==old['cfl_year']
    return op,p

def norms(e,A):
    x=np.asarray(e,dtype=np.longdouble);w=A.astype(np.longdouble)/np.sum(A.astype(np.longdouble))
    return {'L1':float(np.sum(w*np.abs(x))),'L2':float(np.sqrt(np.sum(w*x*x))),'Linf':float(np.max(np.abs(x)))}

def reference(op,V0,mode):
    """Independent latitude Fourier block exponential; keep tiny increments extended.

    m=0 for z/q, m=1 for x/y. Remaining initial rounding modes are measured,
    not silently asserted absent. Matrix is derived from archived face rows.
    """
    w=op.mesh.width;h=op.mesh.height;A=op.mesh.areas
    base=np.array([op.G.getrow(b*w).toarray().reshape(h,w) for b in range(2*h-1)])
    coeff=np.fft.ifft(base,axis=2)*w
    def matrix(m):
        C=coeff[:,:,m];L=(np.exp(-2j*math.pi*m/w)-1)*C[:h]
        L[:-1]-=C[h:];L[1:]+=C[h:];return K*L/A.reshape(h,w)[:,0,None]
    L0=matrix(0).real;L1=matrix(1);r=L0@np.ones(h);e=np.zeros(h);e[0]=1
    B=np.zeros((3*h,3*h));B[:h,:h]=L0-np.outer(r,e);B[:h,h:2*h]=-2*np.outer(r,e)
    B[h:2*h,h:2*h]=L1.real;B[h:2*h,2*h:]=-L1.imag;B[2*h:,h:2*h]=L1.imag;B[2*h:,2*h:]=L1.real
    initial=V0.astype(np.longdouble)/A.astype(np.longdouble);pert=np.asarray(initial-8,dtype=float).reshape(h,w)
    ft=np.fft.fft(pert,axis=1)/w;v=np.r_[ft[:,0].real,ft[:,1].real,ft[:,1].imag]
    phase=np.exp(2j*math.pi*np.arange(w)/w)
    representation=ft[:,0].real[:,None]+2*np.real(ft[:,1,None]*phase)
    alias=pert-representation
    # Extended vector Taylor exponential increment, with standard numerical stops.
    M=(T*B).astype(np.longdouble);term=M@v.astype(np.longdouble);dv=term.copy();iterations=1
    for j in range(2,201):
        term=M@term/j;dv+=term;iterations=j
        if np.max(np.abs(term))<1e-27:break
    else:raise ValueError('REFERENCE_TAYLOR')
    delta=dv[:h,None]+2*(dv[h:2*h,None]*phase.real-dv[2*h:,None]*phase.imag)
    # Independent standard dense expm check of the same small block.
    dense=expm(T*B)@v-v
    delta2=dense[:h,None]+2*np.real((dense[h:2*h,None]+1j*dense[2*h:,None])*phase)
    alias_increment=np.zeros((h,w),dtype=np.longdouble);alias_terms=[];alias_norms=[]
    for mm in range(2,w//2+1):
        Mm=(T*matrix(mm)).astype(np.clongdouble);vv=ft[:,mm].astype(np.clongdouble)
        termm=Mm@vv;change=termm.copy()
        for jj in range(2,201):
            termm=Mm@termm/jj;change+=termm
            if np.max(np.abs(termm))<1e-28:break
        else:raise ValueError('ALIAS_TAYLOR')
        pp=np.exp(2j*math.pi*mm*np.arange(w)/w)
        factor=1 if mm==w//2 else 2
        alias_increment+=factor*np.real(change[:,None]*pp)
        alias_terms.append(jj);alias_norms.append(float(np.linalg.norm(Mm,np.inf)))
    out=initial+delta.ravel()+alias_increment.ravel()
    report={'method':'Fourier all longitude modes; extended Taylor; m0/m1 dense expm crosscheck','taylor_terms':iterations,
      'last_term_max':float(np.max(np.abs(term))),'scaled_matrix_norm_inf':float(np.linalg.norm(T*B,np.inf)),
      'dense_vs_extended_increment_Linf_m':float(np.max(np.abs(delta2-delta))),
      'initial_other_modes_Linf_m':float(np.max(np.abs(alias))),
      'all_other_modes_increment_Linf_m':float(np.max(np.abs(alias_increment))),
      'all_modes_included':True,'max_alias_taylor_terms':max(alias_terms),'max_alias_scaled_matrix_norm_inf':max(alias_norms),
      'axisymmetric_anchor_coupling_norm':float(np.max(np.abs(r))),
      'longdouble_bits':int(np.finfo(np.longdouble).nmant+1)}
    return out,report

def smooth_run(op,V0,n,method):
    """Euler smooth branch; records low/high limiter check against full kernel."""
    dt=T/n
    if dt>op.cfl:raise ValueError('CFL')
    A=op.mesh.areas;i=op.mesh.first;j=op.mesh.second
    V=V0.copy();comp=np.zeros_like(V);ld=method=='longdouble'
    if ld:V=V.astype(np.longdouble)
    start=time.perf_counter()
    for _ in range(n):
        h=V/A;rate=op.high(np.asarray(h,dtype=float))
        if method=='longdouble':
            delta=np.zeros(len(V),dtype=np.longdouble);np.add.at(delta,j,rate.astype(np.longdouble)*np.longdouble(dt));np.add.at(delta,i,-rate.astype(np.longdouble)*np.longdouble(dt))
        else:delta=dt*(np.bincount(j,weights=rate,minlength=len(V))-np.bincount(i,weights=rate,minlength=len(V)))
        if method=='kahan':
            y=delta-comp;new=V+y;comp=(new-V)-y;V=new
        else:V=V+delta
    return V,comp,{'wall_s':time.perf_counter()-start,'dt':dt,'steps':n,'method':method}

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--width',type=int,default=256);p.add_argument('--mode',choices=['x','y','z','q'],default='x');p.add_argument('--steps',type=int,nargs='+',default=[64,128,256,512]);p.add_argument('--methods',nargs='+',choices=['plain','kahan','longdouble','original'],default=['original','plain','kahan','longdouble']);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();op,old=load_case(a.archive,a.width);A=op.mesh.areas;mode,eigen=averages(a.width,a.width//2,a.mode)
    # Use exact old arrays for starting height and its original volume expression.
    with np.load(old/(a.mode+'.npz'),allow_pickle=False) as z:h0=z['initial_h'];old64=z['main_h'];continuum=z['exact_h']
    V0=A*h0;ref,refdiag=reference(op,V0,a.mode);np.savez(a.output/'references.npz',V0=V0,areas=A,reference_h=ref,continuum_h=continuum)
    rows=[];previous={}
    for method in a.methods:
        for n in a.steps:
            if method=='original':
                timer=time.perf_counter();V,d=op.advance(V0,T,minimum_steps=n);c=np.zeros_like(V);d.update(wall_s=time.perf_counter()-timer,method=method);trueh=V.astype(np.longdouble)/A
            else:
                V,c,d=smooth_run(op,V0,n,method);trueh=(V.astype(np.longdouble)-c.astype(np.longdouble))/A
            d['steps']=n;d['errors_continuum_m']=norms(trueh-continuum,A);d['errors_semidiscrete_m']=norms(trueh-ref,A)
            d['mass_relative_change']=float((np.sum(V.astype(np.longdouble)-c.astype(np.longdouble))-np.sum(V0.astype(np.longdouble)))/np.sum(V0.astype(np.longdouble)))
            d['minimum_h']=float(np.min(trueh));d['maximum_h']=float(np.max(trueh))
            if method in previous:d['main_half_L2_m']=norms(previous[method]-trueh,A)['L2'];d['fraction_of_coarser_error']=d['main_half_L2_m']/rows[-1]['errors_continuum_m']['L2']
            previous[method]=trueh.copy();rows.append(d)
            np.savez(a.output/f'{method}_{n}.npz',volume_hi=V,compensation=c,height=trueh)
            print(json.dumps({'method':method,'steps':n,'continuum_L2':d['errors_continuum_m']['L2'],'semidiscrete_L2':d['errors_semidiscrete_m']['L2'],'wall_s':d['wall_s']}),flush=True)
    result={'scope':'EXPLORE_DT_ONLY','width':a.width,'mode':a.mode,'geometry':'archived CSR unchanged; all archived mesh fields bitwise matched','reference':refdiag,
      'spatial_reference_error_m':norms(ref-continuum,A),'rows':rows,'wall_s':time.perf_counter()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'limitations':'smooth variants bypass limiter only for diagnostic separation; full original lane logs limiter; Fourier reference includes initial alias modes; negligible alias-to-m0 anchor coupling remains separately estimated'}
    (a.output/'RESULT.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
