"""Independent I0 oracles written before implementation; explicit discovery only."""
from fractions import Fraction as Q
import math
import numpy as np


def rational_flux_oracle():
    from hr2_p1_r1.limiter import limited_step
    A=np.array([1.,2.,3.,4.]);V=np.array([1.,4.,9.,16.])
    first=np.array([0,0,1,2]);second=np.array([1,2,3,3]);c=np.array([1.,2.,3.,4.])
    expected=[Q(3,2),Q(9,2),Q(9),Q(15)]
    actual,d=limited_step(A,V,first,second,c,.1,None)
    np.testing.assert_allclose(actual,list(map(float,expected)),rtol=0,atol=2e-14)
    np.testing.assert_allclose(d['transfer'],[-.1,-.4,-.6,-.4],rtol=0,atol=2e-15)
    assert math.fsum(actual)==30 and d['limit_years']==float(Q(1,6))
    assert np.array_equal(V,[1,4,9,16])
    return d


def rational_limiter_oracle():
    from hr2_p1_r1.limiter import limited_step
    A=np.array([1.,2.,3.,4.]);V=np.array([1.,4.,9.,16.])
    first=np.array([0,0,1,2]);second=np.array([1,2,3,3]);c=np.array([1.,2.,3.,4.])
    actual,d=limited_step(A,V,first,second,c,.1,np.array([19.,-4.,-6.,-4.]))
    np.testing.assert_allclose(actual,[1.,5.,9.,15.],rtol=0,atol=2e-14)
    assert abs(d['alpha'][0]-float(Q(1,4)))<=2e-15
    assert math.fsum(actual)==30 and (actual>=0).all()
    assert (actual/A>=1).all() and (actual/A<=4).all()
    return d


def cfl_constant_zero_and_negative_oracles():
    from hr2_p1_r1.limiter import limited_step
    A=np.array([1.,2.,3.,4.]);f=np.array([0,0,1,2]);s=np.array([1,2,3,3]);c=np.array([1.,2.,3.,4.])
    for values,coef in [(8*A,c),(np.zeros(4),c),(np.array([1.,4.,9.,16.]),np.zeros(4))]:
        actual,d=limited_step(A,values,f,s,coef,.1,None)
        assert np.array_equal(actual,values)
    V=np.array([1.,4.,9.,16.]);before=V.copy()
    for dt in [.2,-1.,math.nan]:
        try:limited_step(A,V,f,s,c,dt,None)
        except ValueError:pass
        else:raise AssertionError('BAD_DT_ADMITTED')
    assert np.array_equal(V,before)
    try:limited_step(A,-V,f,s,c,.1,None)
    except ValueError:pass
    else:raise AssertionError('NEGATIVE_ADMITTED')
    return {'constant_zero_kappa_zero':'PASS','invalid_dt_negative':'PASS'}


def analytic_faces(mesh, mode):
    """Independent exact continuum integrals; no reconstruction coefficients."""
    k=405896410000.;d=math.pi/mesh.height;rates=[]
    for axis,phi,lam in zip(mesh.axis,mesh.face_phi,mesh.face_lam):
        if axis==0:
            val=0. if mode=='z' else k*d*(math.sin(lam) if mode=='x' else -math.cos(lam))
        else:
            a,b=lam-d/2,lam+d/2
            if mode=='z':val=-k*d*math.cos(phi)**2
            else:val=k*math.cos(phi)*math.sin(phi)*((math.sin(b)-math.sin(a)) if mode=='x' else (math.cos(a)-math.cos(b)))
        rates.append(val)
    return np.array(rates)


def sphere_admission_oracle(mesh):
    assert math.isclose(math.fsum(mesh.areas),4*math.pi*mesh.radius**2,rel_tol=64*np.finfo(float).eps)
    pairs={tuple(sorted((int(a),int(b)))) for a,b in zip(mesh.first,mesh.second)}
    assert len(pairs)==len(mesh.first)==mesh.width*(2*mesh.height-1)
    for j in range(mesh.height):assert (j*mesh.width,j*mesh.width+mesh.width-1) in pairs
    assert (0,mesh.width//2) not in pairs
    assert (mesh.length>0).all() and (mesh.distance>0).all()
