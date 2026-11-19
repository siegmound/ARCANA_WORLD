"""EXPLORE: double-double represented volumes, unchanged archived flux geometry."""
import math,json,hashlib
from pathlib import Path
import numpy as np

def physical(hi,correction):return hi.astype(np.longdouble)-correction.astype(np.longdouble)

def step(op,hi,correction,dt,limited=True):
    if not math.isfinite(dt) or dt<=0 or dt>op.cfl:raise ValueError('CFL')
    A=op.mesh.areas;i=op.mesh.first;j=op.mesh.second
    v=physical(hi,correction)
    if not np.isfinite(v).all() or (v<0).any():raise ValueError('STATE')
    h=np.asarray(v/A.astype(np.longdouble),dtype=float)
    low=op.c*(h[i]-h[j]);high=op.high(h)
    def gather(x):return np.bincount(j,weights=x,minlength=len(A))-np.bincount(i,weights=x,minlength=len(A))
    alpha=np.ones(len(i))
    if limited:
        UL=v+gather(dt*low);corr=-dt*(high-low)
        pp=np.bincount(i,weights=np.maximum(corr,0),minlength=len(A))+np.bincount(j,weights=np.maximum(-corr,0),minlength=len(A))
        pm=np.bincount(i,weights=np.maximum(-corr,0),minlength=len(A))+np.bincount(j,weights=np.maximum(corr,0),minlength=len(A))
        slack=128*np.finfo(float).eps*max(1.,float(np.max(np.abs(v))))
        if (UL<A*h.min()-slack).any() or (UL>A*h.max()+slack).any():raise ValueError('LOW_RANGE')
        qp=np.asarray(np.maximum(A.astype(np.longdouble)*h.max()-UL,0),dtype=float)
        qm=np.asarray(np.maximum(UL-A.astype(np.longdouble)*h.min(),0),dtype=float)
        rp=np.minimum(1,np.divide(qp,pp,out=np.ones_like(A),where=pp>0));rm=np.minimum(1,np.divide(qm,pm,out=np.ones_like(A),where=pm>0))
        alpha=np.where(corr>=0,np.minimum(rp[i],rm[j]),np.minimum(rm[i],rp[j]))
        alpha=np.where(alpha<1,alpha*(1-64*np.finfo(float).eps),alpha)
    transfer=dt*(low+alpha*(high-low));increment=gather(transfer)
    y=increment-correction;new=hi+y;next_c=(new-hi)-y
    out=physical(new,next_c)
    if not np.isfinite(out).all() or (out<0).any():raise ValueError('NONNEGATIVE')
    hnew=out/A;tol=128*np.finfo(float).eps*max(1.,float(np.max(h)))
    if limited and (hnew.min()<h.min()-tol or hnew.max()>h.max()+tol):raise ValueError('RANGE')
    residual=float(np.sum(out)-np.sum(v));degree=np.bincount(i,minlength=len(A))+np.bincount(j,minlength=len(A))
    count=2*int(degree.max())+6;gamma=count*np.finfo(float).eps/(1-count*np.finfo(float).eps)
    bound=8*gamma*float(np.sum(np.abs(v))+np.sum(np.abs(out))+2*np.sum(np.abs(transfer)))
    if abs(residual)>bound:raise ValueError('CONSERVATION')
    return new,next_c,{'limited_faces':int(np.count_nonzero(alpha<1-1e-12)),'min_alpha':float(alpha.min()),
      'residual_m3':residual,'roundoff_bound_m3':bound,'minimum_h':float(hnew.min()),'maximum_h':float(hnew.max())}

def advance(op,V0,steps,end=.0001):
    hi=V0.copy();c=np.zeros_like(hi);rows=[];dt=end/steps
    for _ in range(steps):hi,c,d=step(op,hi,c,dt);rows.append(d)
    return hi,c,{'steps':steps,'dt':dt,'limited_faces_total':sum(x['limited_faces'] for x in rows),
      'max_residual_m3':max(abs(x['residual_m3']) for x in rows),'minimum_h':min(x['minimum_h'] for x in rows),
      'maximum_h':max(x['maximum_h'] for x in rows)}

def save(path,hi,c,steps,dt,geometry_sha):
    metadata={'schema':'EXPLORE_COMPENSATED_VOLUME_1','source_sha':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'geometry_sha':geometry_sha,'steps':steps,'dt':dt,'year':steps*dt,'physical_state':'hi-correction; correction MUST be retained'}
    with Path(path).open('xb') as f:np.savez(f,hi=hi,correction=c,metadata=np.frombuffer(json.dumps(metadata,sort_keys=True).encode(),dtype='u1'))
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path,expected,geometry_sha):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise ValueError('CHECKPOINT_SHA')
    with np.load(path,allow_pickle=False) as z:meta=json.loads(z['metadata'].tobytes());hi=z['hi'];c=z['correction']
    if meta['schema']!='EXPLORE_COMPENSATED_VOLUME_1' or meta['geometry_sha']!=geometry_sha or meta['source_sha']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise ValueError('CHECKPOINT_IDENTITY')
    return hi,c,meta
