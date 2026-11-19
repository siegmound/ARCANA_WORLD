"""Conservative shared-flux update with exact-rational budget checks."""
from fractions import Fraction as F
import math
import numpy as np


def need(ok, message):
    if not ok:raise ValueError(message)


def limited_step(areas, volumes, first, second, conductance, dt, high_rate=None):
    A=np.array(areas,dtype='<f8',copy=True);V=np.array(volumes,dtype='<f8',copy=True)
    i=np.asarray(first);j=np.asarray(second);c=np.asarray(conductance,dtype='<f8')
    need(A.ndim==V.ndim==1 and A.shape==V.shape,'SHAPE')
    need(i.dtype.kind in 'iu' and j.dtype.kind in 'iu','INDICES')
    need(i.shape==j.shape==c.shape and i.ndim==1,'FACE_SHAPE')
    need(np.isfinite(A).all() and (A>0).all() and np.isfinite(V).all() and (V>=0).all(),'STATE')
    need((i>=0).all() and (j>=0).all() and (i<len(A)).all() and (j<len(A)).all() and (i!=j).all(),'ENDPOINTS')
    need(len(set(zip(np.minimum(i,j),np.maximum(i,j))))==len(i),'DUPLICATE')
    need(np.isfinite(c).all() and (c>=0).all(),'CONDUCTANCE')
    need(isinstance(dt,(int,float)) and not isinstance(dt,bool) and math.isfinite(dt) and dt>0,'DT')
    C=np.bincount(i,weights=c,minlength=len(A))+np.bincount(j,weights=c,minlength=len(A))
    limit=.5*float(np.min(A[C>0]/C[C>0])) if (C>0).any() else None
    need(limit is None or dt<=limit,'CFL')
    def gather(x):return np.bincount(j,weights=x,minlength=len(A))-np.bincount(i,weights=x,minlength=len(A))
    low=c*((V/A)[i]-(V/A)[j]);high=low.copy() if high_rate is None else np.asarray(high_rate,dtype='<f8')
    need(high.shape==low.shape and np.isfinite(high).all(),'HIGH_RATE')
    t_low=low*dt;a_first=-(high-low)*dt
    # Exact fractions of represented binary64 volumes/transfers; no stock correction.
    Af=list(map(F.from_float,map(float,A)));Vf=list(map(F.from_float,map(float,V)))
    heights=[v/a for v,a in zip(Vf,Af)];m=min(heights);M=max(heights)
    UL=Vf.copy();Pplus=[F(0) for _ in A];Pminus=[F(0) for _ in A]
    for k,(src,dst) in enumerate(zip(i,j)):
        t=F.from_float(float(t_low[k]));UL[src]-=t;UL[dst]+=t
        a=F.from_float(float(a_first[k]))
        for endpoint,amount in [(src,a),(dst,-a)]:
            if amount>0:Pplus[endpoint]+=amount
            elif amount<0:Pminus[endpoint]-=amount
    plus=[];minus=[]
    for a,u,pp,pm in zip(Af,UL,Pplus,Pminus):
        qp=a*M-u;qm=u-a*m
        need(qp>=0 and qm>=0,'UNCERTIFIED_LOW_RANGE')
        plus.append(F(1) if pp==0 else min(F(1),qp/pp))
        minus.append(F(1) if pm==0 else min(F(1),qm/pm))
    alpha=np.ones(len(i))
    for k,(src,dst) in enumerate(zip(i,j)):
        exact=min(plus[src],minus[dst]) if a_first[k]>=0 else min(minus[src],plus[dst])
        value=float(exact)
        if F.from_float(value)>exact:value=math.nextafter(value,0.)
        alpha[k]=value
    transfer=(low+alpha*(high-low))*dt
    updated=V+gather(transfer)
    need(np.isfinite(updated).all() and (updated>=0).all(),'NONNEGATIVITY')
    for a,v in zip(Af,map(float,updated)):
        need(a*m<=F.from_float(v)<=a*M,'FLOAT_RANGE_UNCERTIFIED')
    degree=np.bincount(i,minlength=len(A))+np.bincount(j,minlength=len(A));op=2*int(degree.max())+6
    eps=np.finfo(float).eps;gamma=op*eps/(1-op*eps)
    budget=8*gamma*(math.fsum(map(abs,V))+math.fsum(map(abs,updated))+2*math.fsum(map(abs,transfer)))
    residual=math.fsum(map(float,updated))-math.fsum(map(float,V))
    need(abs(residual)<=budget,'CONSERVATION')
    return updated,{'alpha':alpha,'transfer':transfer,'low_rate':low,'high_rate':high,'limit_years':limit,
        'activated_faces':int(np.count_nonzero(alpha<1)),'residual_m3':residual,'roundoff_bound_m3':budget,
        'minimum_h':float(np.min(updated/A)),'maximum_h':float(np.max(updated/A)),
        'budgets_exact_rational':True,'state_clipping_or_normalization':False}
