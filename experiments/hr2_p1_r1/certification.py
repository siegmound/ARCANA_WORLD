"""Independent range enclosures. Agreement of Gauss orders is not certification.

This first implementation uses conservative whole-cell analytic interval ranges.
It deliberately never substitutes quadrature agreement for the sealed widths.
"""
from decimal import Decimal as D, localcontext, ROUND_FLOOR, ROUND_CEILING
import math
import numpy as np

PI=D('3.141592653589793238462643383279502884197169399375105820974944592307816406')


class Interval:
    def __init__(self,a,b=None):self.lo=D(a);self.hi=D(a if b is None else b)
    def __add__(self,o):
        o=o if isinstance(o,Interval) else Interval(o)
        with localcontext() as c:
            c.prec=60;c.rounding=ROUND_FLOOR;lo=self.lo+o.lo;c.rounding=ROUND_CEILING;hi=self.hi+o.hi
        return Interval(lo,hi)
    def __mul__(self,o):
        o=o if isinstance(o,Interval) else Interval(o)
        with localcontext() as c:
            c.prec=60;c.rounding=ROUND_FLOOR;lo=min(a*b for a in [self.lo,self.hi] for b in [o.lo,o.hi]);c.rounding=ROUND_CEILING;hi=max(a*b for a in [self.lo,self.hi] for b in [o.lo,o.hi])
        return Interval(lo,hi)
    def power(self,n):
        result=Interval(1)
        for _ in range(n):result=result*self
        return result


def sin_point(x):
    with localcontext() as c:
        c.prec=70;term=x;value=x
        for n in range(1,80):term*=-x*x/D(2*n*(2*n+1));value+=term
        # |x|<=3pi/2 for this audit. Taylor tail plus70-digit arithmetic <1e-60.
        return value


def trig_band(a,b,cosine=False):
    if cosine:a+=PI/2;b+=PI/2
    mid=(a+b)/2;half=(b-a)/2;value=sin_point(mid)
    return Interval(max(D(-1),value-half-D('1e-60')),min(D(1),value+half+D('1e-60')))


def cell_ranges(mesh,packet):
    from .geometry import POWERS
    output=[]
    with localcontext() as ctx:
        ctx.prec=60;d=PI/D(mesh.height);rho=D.from_float(3*math.pi/mesh.height)
        for cell in packet['patch']:
            row,col=divmod(int(cell),mesh.width);a=-PI/2+D(row)*d;b=a+d;l=-PI+D(col)*d;u=l+d
            cp=trig_band(a,b,True);sp=trig_band(a,b);cl=trig_band(l,u,True);sl=trig_band(l,u)
            xyz=[cp*cl,cp*sl,sp];coordinates=[]
            for tangent in packet['basis'][1:]:
                dot=Interval(0)
                for x,c in zip(xyz,tangent):dot=dot+x*D.from_float(float(c))
                # theta/sin(theta) lies in[1,2] for the certified chart cone.
                coordinates.append(dot*Interval(1,2)*(D(1)/rho))
            output.append([(coordinates[0].power(aa)*coordinates[1].power(bb)) for aa,bb in POWERS])
    def lower(x):
        y=float(x)
        return math.nextafter(y,-math.inf) if D.from_float(y)>x else y
    def upper(x):
        y=float(x)
        return math.nextafter(y,math.inf) if D.from_float(y)<x else y
    return np.array([[lower(x.lo) for x in row] for row in output]),np.array([[upper(x.hi) for x in row] for row in output])


def certify(mesh,packet):
    from .geometry import POWERS
    lo,hi=cell_ranges(mesh,packet);M=packet['M'];delta=np.maximum(np.abs(M-lo),np.abs(hi-M))
    weighted_error=float(np.linalg.norm(np.sqrt(packet['weights'])[:,None]*delta,ord='fro'))
    B=np.sqrt(packet['weights'])[:,None]*M
    svd_roundoff=64*np.finfo(float).eps*max(B.shape)*float(np.linalg.norm(B,ord=2))
    signed_sigma_lower=float(packet['singular_values'][-1])-weighted_error-svd_roundoff
    # On the face, |log coordinate|<=1/6 and |rho*d_n(log coordinate)|<=3.
    # Normalized J enclosures are valid conservative ranges, not sharp quadrature bounds.
    normalized_radius=np.array([0. if a+b==0 else 3*(a+b)*(1/6)**(a+b-1) for a,b in POWERS])
    normalized_radius=np.nextafter(normalized_radius,math.inf)
    widths=2*normalized_radius
    widthM=float(np.max(hi-lo));widthJ=float(np.max(widths))
    passed=widthM<=2**-50 and widthJ<=2**-45 and signed_sigma_lower>0
    packet['moment_lower']=lo;packet['moment_upper']=hi;packet['J_normalized_interval_radius']=normalized_radius
    packet['certificate_status']='CERTIFIED' if passed else 'BLOCKED_ENCLOSURE_WIDTH_AND_RANK_UNCERTIFIED'
    return {'certificate_status':packet['certificate_status'],'observed_rank':packet['observed_rank'],
        'observed_condition':packet['observed_condition'],'observed_sigma_min':float(packet['singular_values'][-1]),
        'weighted_moment_perturbation_upper':weighted_error,'svd_roundoff_allowance':svd_roundoff,
        'signed_sigma_lower':signed_sigma_lower,'rank_certified':signed_sigma_lower>0,
        'max_moment_enclosure_width':widthM,'required_moment_width':2**-50,
        'max_normalized_face_enclosure_width':widthJ,'required_normalized_face_width':2**-45,
        'observed_16_32_moment_difference':packet['observed_moment_order_difference'],
        'observed_16_32_normalized_face_difference':packet['observed_normalized_J_order_difference'],
        'observed_monomial_reproduction_error':packet['observed_monomial_reproduction'],
        'derivative_constant_certified':False if not passed else None,
        'enclosure_method':'independent Decimal60 analytic range enclosure, whole-cell/range face; rigorous for ideal chart assumptions, not a high-order validated quadrature rule',
        'scope':'Observed SVD and two Gauss orders alone never certify geometry or inverse/derivative accuracy.'}
