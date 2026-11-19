"""Independent continuum heat and integrated flux references, not FV reconstruction."""
import math
import numpy as np
from hr2_p1_explore.probe import averages,face_reference

DIRECTION=np.array([1,2,3],dtype=np.longdouble)/np.sqrt(np.longdouble(14))
BETA=np.longdouble('.5')
END_YEAR=.0001

def coefficients():
    power=np.array([BETA**n/np.longdouble(math.factorial(n)) for n in range(17)],dtype=np.longdouble)
    return np.polynomial.legendre.poly2leg(power)

def cell_reference(width,height,year,order=32,initial_exp=False):
    """Area means via separate spherical Gauss quadrature, longdouble reductions.

    Nonharmonic: 8+exp(0.5*a dot r). Heat evolution uses degree16 Legendre
    expansion, decay l(l+1); pointwise Taylor remainder < exp(.5)*.5^17/17!.
    """
    x,weight=np.polynomial.legendre.leggauss(order);x=x.astype(np.longdouble);weight=weight.astype(np.longdouble)
    pe=np.linspace(-math.pi/2,math.pi/2,height+1).astype(np.longdouble);le=np.linspace(-math.pi,math.pi,width+1).astype(np.longdouble)
    coeff=coefficients();ell=np.arange(len(coeff));coeff=coeff*np.exp(-ell*(ell+1)*np.longdouble('.01')*np.longdouble(year))
    out=[]
    for row in range(height):
        p=(pe[row]+pe[row+1])/2+x*(pe[row+1]-pe[row])/2
        # One latitude row at a time, independent of FV patches/cache.
        lam=(le[:-1]+le[1:])[:,None]/2+x[None,:]*(le[1:]-le[:-1])[:,None]/2
        cp=np.cos(p);sp=np.sin(p)
        dot=DIRECTION[0]*cp[None,:,None]*np.cos(lam)[:,None,:]+DIRECTION[1]*cp[None,:,None]*np.sin(lam)[:,None,:]+DIRECTION[2]*sp[None,:,None]
        if initial_exp:values=np.expm1(BETA*dot);constant=np.longdouble(1)
        else:values=np.polynomial.legendre.legval(dot,coeff)-coeff[0];constant=coeff[0]
        weighted=np.sum(values*cp[None,:,None]*weight[None,:,None]*weight[None,None,:],axis=(1,2))
        normalized=weighted*(pe[row+1]-pe[row])/4/(np.sin(pe[row+1])-np.sin(pe[row]))
        out.append(8+constant+normalized)
    return np.asarray(out,dtype=np.longdouble).ravel()

def harmonic(width,height,mode,year):
    values,eigen=averages(width,height,mode)
    return 8+math.exp(-eigen*.01*year)*values

def nonharmonic_flux(mesh,kappa,order=32):
    nodes,weights=np.polynomial.legendre.leggauss(order);nodes=nodes.astype(np.longdouble);weights=weights.astype(np.longdouble)
    d=np.longdouble(math.pi/mesh.height);out=np.empty(len(mesh.first),dtype=np.longdouble)
    for band in range(2*mesh.height-1):
        sl=slice(band*mesh.width,(band+1)*mesh.width);p0=mesh.phi[sl].astype(np.longdouble);l0=mesh.lam[sl].astype(np.longdouble)
        if mesh.axis[band*mesh.width]==0:
            p=p0[:,None]+nodes*d/2;l=l0[:,None]+np.zeros_like(nodes);ds=weights*d/2
            ndot=-DIRECTION[0]*np.sin(l)+DIRECTION[1]*np.cos(l)
        else:
            p=p0[:,None]+np.zeros_like(nodes);l=l0[:,None]+nodes*d/2;ds=weights*d/2*np.cos(p0[:,None])
            ndot=-DIRECTION[0]*np.sin(p)*np.cos(l)-DIRECTION[1]*np.sin(p)*np.sin(l)+DIRECTION[2]*np.cos(p)
        dot=DIRECTION[0]*np.cos(p)*np.cos(l)+DIRECTION[1]*np.cos(p)*np.sin(l)+DIRECTION[2]*np.sin(p)
        out[sl]=-np.longdouble(kappa)*np.sum(BETA*np.exp(BETA*dot)*ndot*ds,axis=1)
    return out
