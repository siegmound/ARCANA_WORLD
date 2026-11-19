"""Preallocated CSR construction: same packets and exact same archived geometry."""
import math,time
import numpy as np
from scipy.sparse import csr_matrix
from hr2_p1_explore.model import Operator,packet

def build(packets,width,height):
    nnz=sum(len(p[0])*width for p in packets);faces=width*(2*height-1)
    data=np.empty(nnz,dtype='<f8');indices=np.empty(nnz,dtype='<i4');ptr=np.empty(faces+1,dtype='<i4')
    offset=0;ptr[0]=0
    for band,(patch,g) in enumerate(packets):
        rr,cc=np.divmod(patch,width)
        for col in range(width):
            ids=rr*width+(cc+col)%width;sort=np.argsort(ids);n=len(ids)
            data[offset:offset+n]=g[sort];indices[offset:offset+n]=ids[sort];offset+=n;ptr[band*width+col+1]=offset
    return csr_matrix((data,indices,ptr),shape=(faces,width*height),copy=False)

class CompactOperator(Operator):
    def __init__(self,mesh,kappa=405896410000.,order=16):
        if not math.isfinite(kappa) or kappa<0:raise ValueError('KAPPA')
        start=time.perf_counter();self.mesh=mesh;self.kappa=kappa;self.order=order
        self.packets=[packet(mesh,b*mesh.width,order) for b in range(2*mesh.height-1)]
        self.G=build([(p['patch'],p['g']) for p in self.packets],mesh.width,mesh.height)
        self.c=kappa*mesh.length/mesh.distance
        C=np.bincount(mesh.first,weights=self.c,minlength=len(mesh.areas))+np.bincount(mesh.second,weights=self.c,minlength=len(mesh.areas))
        self.cfl=.5*float(np.min(mesh.areas[C>0]/C[C>0])) if (C>0).any() else math.inf
        self.assembly_s=time.perf_counter()-start
