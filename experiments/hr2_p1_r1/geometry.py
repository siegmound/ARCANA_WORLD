"""Original lat/lon topology; integrated quartic log-chart face reconstruction."""
from dataclasses import dataclass
import math
import numpy as np
from .limiter import need

POWERS=tuple((a,d-a) for d in range(5) for a in range(d+1))


def point(phi,lam):
    phi,lam=np.broadcast_arrays(phi,lam)
    return np.stack([np.cos(phi)*np.cos(lam),np.cos(phi)*np.sin(lam),np.sin(phi)],axis=-1)


@dataclass
class Sphere:
    width:int
    height:int
    radius:float
    areas:np.ndarray
    first:np.ndarray
    second:np.ndarray
    axis:np.ndarray
    length:np.ndarray
    distance:np.ndarray
    face_phi:np.ndarray
    face_lam:np.ndarray
    centers:np.ndarray


def sphere(width,height,radius=6371000.):
    need(type(width) is int and type(height) is int and height>=2 and width==2*height,'GRID')
    need(math.isfinite(radius) and radius>0,'RADIUS')
    d=math.pi/height;phi=np.linspace(-math.pi/2,math.pi/2,height+1);pc=(phi[:-1]+phi[1:])/2
    lc=-math.pi+(np.arange(width)+.5)*d
    centers=point(pc[:,None],lc[None,:]).reshape(-1,3);ids=np.arange(width*height).reshape(height,width)
    i=np.r_[ids.ravel(),ids[:-1].ravel()];j=np.r_[np.roll(ids,-1,axis=1).ravel(),ids[1:].ravel()]
    axis=np.r_[np.zeros(width*height,dtype='u1'),np.ones(width*(height-1),dtype='u1')]
    fp=np.r_[np.repeat(pc,width),np.repeat(phi[1:-1],width)]
    fl=np.r_[np.tile(-math.pi+(np.arange(width)+1)*d,height),np.tile(lc,height-1)]
    length=np.r_[np.full(width*height,radius*d),np.repeat(radius*d*np.cos(phi[1:-1]),width)]
    distance=np.r_[np.repeat(2*radius*np.arcsin(np.cos(pc)*math.sin(d/2)),width),np.full(width*(height-1),radius*d)]
    return Sphere(width,height,radius,np.repeat(radius**2*d*np.diff(np.sin(phi)),width),i,j,axis,length,distance,fp,fl,centers)


def frame(mesh,face):
    u=point(mesh.face_phi[face],mesh.face_lam[face]);axis=np.eye(3)[int(np.argmin(np.abs(u)))]
    e=axis-u*np.dot(axis,u);e=e/np.linalg.norm(e);other=np.cross(u,e)
    return u,e,other


def chart(p,u,e1,e2,rho):
    q=p@u;s=np.linalg.norm(np.cross(p,u),axis=-1);theta=np.arctan2(s,q)
    a=np.divide(theta,s,out=np.ones_like(theta),where=s>0)
    return np.stack([a*(p@e1)/rho,a*(p@e2)/rho],axis=-1)


def monomials(x):
    return np.stack([x[...,0]**a*x[...,1]**b for a,b in POWERS],axis=-1)


def moments(mesh,patch,basis,order):
    nodes,weights=np.polynomial.legendre.leggauss(order);d=math.pi/mesh.height;u,e1,e2=basis;rho=3*d
    result=[]
    for cell in patch:
        row,col=divmod(int(cell),mesh.width);pm=-math.pi/2+(row+.5)*d;lm=-math.pi+(col+.5)*d
        phi=pm+nodes[:,None]*d/2;lam=lm+nodes[None,:]*d/2
        xyz=point(phi,lam);values=monomials(chart(xyz,u,e1,e2,rho))
        measure=weights[:,None]*weights[None,:]*np.cos(phi)*(d/2)**2
        area=d*(math.sin(pm+d/2)-math.sin(pm-d/2))
        result.append(np.sum(values*measure[...,None],axis=(0,1))/area)
    return np.array(result)


def face_integrals(mesh,face,basis,order):
    nodes,weights=np.polynomial.legendre.leggauss(order);d=math.pi/mesh.height;rho=3*d;u,e1,e2=basis
    phi0=mesh.face_phi[face];lam0=mesh.face_lam[face]
    if mesh.axis[face]==0:
        phi=phi0+nodes*d/2;lam=np.full(order,lam0);normal=np.stack([-np.sin(lam),np.cos(lam),np.zeros(order)],axis=-1);ds=weights*d/2
    else:
        phi=np.full(order,phi0);lam=lam0+nodes*d/2;normal=np.stack([-np.sin(phi)*np.cos(lam),-np.sin(phi)*np.sin(lam),np.cos(phi)],axis=-1);ds=weights*d/2*math.cos(phi0)
    p=point(phi,lam);q=p@u;s=np.linalg.norm(np.cross(p,u),axis=-1);theta=np.arctan2(s,q);a=theta/s
    derivative=(a*q-1)/(s*s)
    xi=chart(p,u,e1,e2,rho)
    grad1=(a*(normal@e1)+derivative*(p@e1)*(normal@u))/rho
    grad2=(a*(normal@e2)+derivative*(p@e2)*(normal@u))/rho
    answer=[]
    for aa,bb in POWERS:
        g=np.zeros(order)
        if aa:g+=aa*xi[:,0]**(aa-1)*xi[:,1]**bb*grad1
        if bb:g+=bb*xi[:,0]**aa*xi[:,1]**(bb-1)*grad2
        answer.append(float(np.sum(ds*g)))
    return np.array(answer)


def prepare_face(mesh,face,order=16,independent_order=32):
    u,e1,e2=frame(mesh,face);d=math.pi/mesh.height
    angles=np.arctan2(np.linalg.norm(np.cross(mesh.centers,u),axis=1),mesh.centers@u)
    patch=np.union1d(np.flatnonzero(angles<=3*d),[mesh.first[face],mesh.second[face]])
    basis=(u,e1,e2);M=moments(mesh,patch,basis,order);M2=moments(mesh,patch,basis,independent_order)
    J=face_integrals(mesh,face,basis,order);J2=face_integrals(mesh,face,basis,independent_order)
    weights=mesh.areas[patch]/math.fsum(map(float,mesh.areas[patch]));B=np.sqrt(weights)[:,None]*M
    U,s,VT=np.linalg.svd(B,full_matrices=False)
    need(len(s)==15 and s[-1]>0,'OBSERVED_RANK')
    inverse=(VT.T/s)@U.T*np.sqrt(weights)[None,:]
    g=-J@inverse
    return {'patch':patch,'basis':np.stack(basis),'M':M,'M_independent_order':M2,'J':J,'J_independent_order':J2,
        'weights':weights,'inverse':inverse,'flux_weights':g,'singular_values':s,
        'observed_condition':float(s[0]/s[-1]),'observed_rank':int(np.linalg.matrix_rank(B)),
        'observed_moment_order_difference':float(np.max(np.abs(M-M2))),
        'observed_normalized_J_order_difference':float(np.max(np.abs(J-J2))*3*mesh.radius*d/mesh.length[face]),
        'observed_monomial_reproduction':float(np.max(np.abs(inverse@M-np.eye(15)))),
        'certificate_status':'NOT_CHECKED','face':face}


def shared_flux(packet,heights,kappa):
    need(packet.get('certificate_status')=='CERTIFIED','UNCERTIFIED_GEOMETRY')
    values=np.asarray(heights)[packet['patch']]
    return float(kappa*np.dot(packet['flux_weights'],values-values[0]))
