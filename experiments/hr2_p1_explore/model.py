"""Rotationally shared quartic finite volumes with numerical quadrature and FCT.

Independent EXPLORE namespace; no historical numerical module is imported.
No final-stock clipping, mass rescaling, or harmonic-specific coefficients.
"""
import math,time
from dataclasses import dataclass
import numpy as np
from scipy.sparse import csr_matrix
POWERS=tuple((a,d-a) for d in range(5) for a in range(d+1))

def point(phi,lam):
    phi,lam=np.broadcast_arrays(phi,lam)
    return np.stack((np.cos(phi)*np.cos(lam),np.cos(phi)*np.sin(lam),np.sin(phi)),axis=-1)

def chart(p,u,e,n,rho):
    q=p@u
    s=np.linalg.norm(np.cross(p,u),axis=-1)
    angle=np.arctan2(s,q)
    a=np.divide(angle,s,out=np.ones_like(s),where=s>1e-15)
    return np.stack((a*(p@e)/rho,a*(p@n)/rho),axis=-1)

@dataclass
class Mesh:
    width:int
    height:int
    radius:float
    areas:np.ndarray
    first:np.ndarray
    second:np.ndarray
    axis:np.ndarray
    phi:np.ndarray
    lam:np.ndarray
    length:np.ndarray
    distance:np.ndarray
    centers:np.ndarray

def sphere(width,height,radius=6371000.):
    if type(width)is not int or type(height)is not int or height<4 or width!=2*height:raise ValueError('GRID')
    if not math.isfinite(radius) or radius<=0:raise ValueError('RADIUS')
    d=math.pi/height;edges=np.linspace(-math.pi/2,math.pi/2,height+1);pc=(edges[:-1]+edges[1:])/2;lc=-math.pi+(np.arange(width)+.5)*d
    ids=np.arange(width*height).reshape(height,width)
    first=np.r_[ids.ravel(),ids[:-1].ravel()];second=np.r_[np.roll(ids,-1,axis=1).ravel(),ids[1:].ravel()]
    return Mesh(width,height,radius,np.repeat(radius**2*d*np.diff(np.sin(edges)),width),first,second,
      np.r_[np.zeros(width*height,dtype='i1'),np.ones(width*(height-1),dtype='i1')],
      np.r_[np.repeat(pc,width),np.repeat(edges[1:-1],width)],
      np.r_[np.tile(-math.pi+(np.arange(width)+1)*d,height),np.tile(lc,height-1)],
      np.r_[np.full(width*height,radius*d),np.repeat(radius*d*np.cos(edges[1:-1]),width)],
      np.r_[np.repeat(2*radius*np.arcsin(np.cos(pc)*math.sin(d/2)),width),np.full(width*(height-1),radius*d)],
      point(pc[:,None],lc[None,:]).reshape(-1,3))

def packet(mesh,face,order):
    d=math.pi/mesh.height;rho=3*d;phi0=mesh.phi[face];lam0=mesh.lam[face]
    u=point(phi0,lam0);e=np.array([-math.sin(lam0),math.cos(lam0),0.]);n=np.cross(u,e)
    angles=np.arctan2(np.linalg.norm(np.cross(mesh.centers,u),axis=1),mesh.centers@u)
    patch=np.union1d(np.flatnonzero(angles<=3*d+32*np.finfo(float).eps),[mesh.first[face],mesh.second[face]])
    nodes,w=np.polynomial.legendre.leggauss(order);M=[]
    for cell in patch:
        row,col=divmod(int(cell),mesh.width);pm=-math.pi/2+(row+.5)*d;lm=-math.pi+(col+.5)*d
        phi=pm+nodes[:,None]*d/2;lam=lm+nodes[None,:]*d/2
        x=chart(point(phi,lam),u,e,n,rho);measure=w[:,None]*w[None,:]*np.cos(phi)*(d/2)**2
        # Exact-domain area expression, evaluated numerically; true-mean target.
        area=d*(math.sin(pm+d/2)-math.sin(pm-d/2))
        M.append([np.sum(x[...,0]**a*x[...,1]**b*measure)/area for a,b in POWERS])
    M=np.array(M)
    if mesh.axis[face]==0:
        phi=phi0+nodes*d/2;lam=np.full(order,lam0);normal=np.broadcast_to(e,(order,3));ds=w*d/2
    else:
        phi=np.full(order,phi0);lam=lam0+nodes*d/2;normal=np.stack((-np.sin(phi)*np.cos(lam),-np.sin(phi)*np.sin(lam),np.cos(phi)),axis=-1);ds=w*d/2*math.cos(phi0)
    p=point(phi,lam);q=p@u;s=np.linalg.norm(np.cross(p,u),axis=1);theta=np.arctan2(s,q);a=theta/s
    # Cancellation-free series near zero for derivative of theta/sin(theta).
    derivative=np.empty_like(s);small=s<1e-3
    derivative[small]=-1/3-2*s[small]**2/15-8*s[small]**4/105
    derivative[~small]=(a[~small]*q[~small]-1)/s[~small]**2
    x=chart(p,u,e,n,rho)
    gx=(a*(normal@e)+derivative*(p@e)*(normal@u))/rho
    gy=(a*(normal@n)+derivative*(p@n)*(normal@u))/rho
    J=[]
    for aa,bb in POWERS:
        v=np.zeros(order)
        if aa:v+=aa*x[:,0]**(aa-1)*x[:,1]**bb*gx
        if bb:v+=bb*x[:,0]**aa*x[:,1]**(bb-1)*gy
        J.append(float(ds@v))
    J=np.array(J);weights=mesh.areas[patch]/math.fsum(map(float,mesh.areas[patch]));B=np.sqrt(weights)[:,None]*M
    U,sing,VT=np.linalg.svd(B,full_matrices=False)
    rank=int(np.count_nonzero(sing>sing[0]*max(B.shape)*np.finfo(float).eps))
    if rank!=15:raise ValueError('RANK')
    R=(VT.T/sing)@U.T*np.sqrt(weights)[None,:];g=-J@R
    g[0]-=math.fsum(map(float,g)) # coefficient anchor form, never stock correction
    return {'patch':patch,'M':M,'J':J,'R':R,'g':g,'basis':np.array([u,e,n]),'singular':sing,
      'condition':float(sing[0]/sing[-1]),'reproduction':float(np.max(np.abs(R@M-np.eye(15))))}

class Operator:
    def __init__(self,mesh,kappa=405896410000.,order=16):
        if not math.isfinite(kappa) or kappa<0:raise ValueError('KAPPA')
        start=time.perf_counter();self.mesh=mesh;self.kappa=kappa;self.order=order;self.packets=[]
        rows=[];cols=[];vals=[];width=mesh.width
        # On a longitude-uniform sphere each face in a band is a rigid rotation.
        # Cache one generic polynomial packet per axis/latitude, not per harmonic.
        for band in range(2*mesh.height-1):
            p=packet(mesh,band*width,order);self.packets.append(p)
            rr,cc=np.divmod(p['patch'],width)
            for col in range(width):
                rows.extend([band*width+col]*len(rr));cols.extend(rr*width+(cc+col)%width);vals.extend(p['g'])
        self.G=csr_matrix((vals,(rows,cols)),shape=(len(mesh.first),len(mesh.areas)))
        self.c=kappa*mesh.length/mesh.distance
        C=np.bincount(mesh.first,weights=self.c,minlength=len(mesh.areas))+np.bincount(mesh.second,weights=self.c,minlength=len(mesh.areas))
        self.cfl=.5*float(np.min(mesh.areas[C>0]/C[C>0])) if (C>0).any() else math.inf
        self.assembly_s=time.perf_counter()-start
    def high(self,h):return self.kappa*(self.G@(np.asarray(h)-h[0]))
    def step(self,V,dt,limited=True):
        A=self.mesh.areas;i=self.mesh.first;j=self.mesh.second
        if not math.isfinite(dt) or dt<=0 or dt>self.cfl:raise ValueError('CFL')
        V=np.asarray(V,dtype=float)
        if V.shape!=A.shape or not np.isfinite(V).all() or (V<0).any():raise ValueError('STATE')
        h=V/A;low=self.c*(h[i]-h[j]);high=self.high(h);alpha=np.ones(len(i))
        def gather(t):return np.bincount(j,weights=t,minlength=len(A))-np.bincount(i,weights=t,minlength=len(A))
        if limited:
            UL=V+gather(dt*low);corr=-dt*(high-low)
            pp=np.bincount(i,weights=np.maximum(corr,0),minlength=len(A))+np.bincount(j,weights=np.maximum(-corr,0),minlength=len(A))
            pm=np.bincount(i,weights=np.maximum(-corr,0),minlength=len(A))+np.bincount(j,weights=np.maximum(corr,0),minlength=len(A))
            range_slack=128*np.finfo(float).eps*max(1.,float(np.max(np.abs(V))))
            if (UL < A*h.min()-range_slack).any() or (UL > A*h.max()+range_slack).any():raise ValueError('LOW_RANGE')
            # Only roundoff-negative budget slack is floored, never physical stocks.
            qp=np.maximum(A*h.max()-UL,0);qm=np.maximum(UL-A*h.min(),0)
            rp=np.minimum(1,np.divide(qp,pp,out=np.ones_like(A),where=pp>0));rm=np.minimum(1,np.divide(qm,pm,out=np.ones_like(A),where=pm>0))
            alpha=np.where(corr>=0,np.minimum(rp[i],rm[j]),np.minimum(rm[i],rp[j]))
            alpha=np.where(alpha<1,alpha*(1-64*np.finfo(float).eps),alpha)
        transfer=dt*(low+alpha*(high-low));new=V+gather(transfer)
        if not np.isfinite(new).all() or (new<0).any():raise ValueError('NEGATIVE_OR_NONFINITE')
        tolerance=128*np.finfo(float).eps*max(1.,float(np.max(h)))
        if limited and ((new/A).min()<h.min()-tolerance or (new/A).max()>h.max()+tolerance):raise ValueError('RANGE')
        residual=math.fsum(map(float,new))-math.fsum(map(float,V))
        degree=np.bincount(i,minlength=len(A))+np.bincount(j,minlength=len(A));operations=2*int(degree.max())+6
        gamma=operations*np.finfo(float).eps/(1-operations*np.finfo(float).eps)
        bound=8*gamma*(math.fsum(map(abs,V))+math.fsum(map(abs,new))+2*math.fsum(map(abs,transfer)))
        if abs(residual)>bound:raise ValueError('CONSERVATION')
        return new,{'limited_faces':int(np.count_nonzero(alpha<1-1e-12)),'min_alpha':float(alpha.min()),'residual_m3':residual,'roundoff_bound_m3':bound,
          'min_h':float((new/A).min()),'max_h':float((new/A).max()),'roundoff_range_tolerance_m':tolerance}
    def advance(self,V,end,minimum_steps=1,limited=True):
        count=max(minimum_steps,math.ceil(end/self.cfl)) if math.isfinite(self.cfl) else minimum_steps
        dt=end/count;rows=[]
        for _ in range(count):V,d=self.step(V,dt,limited);rows.append(d)
        return V,{'steps':count,'dt':dt,'cfl':self.cfl,'limited_faces_total':sum(x['limited_faces'] for x in rows),
         'min_alpha':min(x['min_alpha'] for x in rows),'max_step_residual_m3':max(abs(x['residual_m3']) for x in rows),
         'minimum_h':min(x['min_h'] for x in rows),'maximum_h':max(x['max_h'] for x in rows)}
