"""Compare identical template-to-CSR construction services in fresh processes."""
import argparse,json,time,resource,math,hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--method',choices=['lists','preallocated'],required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    src=a.archive/'attempt04/256x128';w=256;h=128
    with np.load(src/'coefficients.npz',allow_pickle=False) as z:packets=[(z[f'{b}_patch'],z[f'{b}_g']) for b in range(2*h-1)]
    initial=resource.getrusage(resource.RUSAGE_SELF);timer=time.perf_counter();nnz=sum(len(x[0])*w for x in packets)
    if a.method=='lists':
        rows=[];cols=[];values=[]
        for band,(patch,g) in enumerate(packets):
            rr,cc=np.divmod(patch,w)
            for col in range(w):rows.extend([band*w+col]*len(rr));cols.extend(rr*w+(cc+col)%w);values.extend(g)
        G=csr_matrix((values,(rows,cols)),shape=(w*(2*h-1),w*h))
    else:
        data=np.empty(nnz,dtype='<f8');indices=np.empty(nnz,dtype='<i4');ptr=np.empty(w*(2*h-1)+1,dtype='<i4');offset=0;ptr[0]=0
        for band,(patch,g) in enumerate(packets):
            rr,cc=np.divmod(patch,w)
            for col in range(w):
                ids=rr*w+(cc+col)%w;order=np.argsort(ids);n=len(ids)
                data[offset:offset+n]=g[order];indices[offset:offset+n]=ids[order];offset+=n;ptr[band*w+col+1]=offset
        G=csr_matrix((data,indices,ptr),shape=(w*(2*h-1),w*h),copy=False)
    wall=time.perf_counter()-timer;usage=resource.getrusage(resource.RUSAGE_SELF)
    hashes={k:hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for k,v in [('data',G.data),('indices',G.indices),('indptr',G.indptr)]}
    # Compare hashes to the authoritative archived geometry without retaining a second G.
    with np.load(src/'operator.npz',allow_pickle=False) as z:expected={k:hashlib.sha256(np.ascontiguousarray(z[k]).tobytes()).hexdigest() for k in hashes}
    assert hashes==expected
    result={'method':a.method,'build_s':wall,'cpu_user_s':usage.ru_utime-initial.ru_utime,'cpu_system_s':usage.ru_stime-initial.ru_stime,
      'build_peak_rss_kib':usage.ru_maxrss,'csr_bytes':G.data.nbytes+G.indices.nbytes+G.indptr.nbytes,'nnz':G.nnz,
      'template_bytes':sum(x.nbytes+y.nbytes for x,y in packets),'hashes':hashes,'archived_CSR_bitwise_equal':True,
      'scope':'identical saved template-to-CSR expansion only; quadrature excluded from both'}
    (a.output/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
