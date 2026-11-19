"""Exact source PRE cubic temperature extrema for G2 laboratory applicability.

Finite Gauss points cannot certify a flow law over the *entire* cold or warm
lithosphere. Check each cubic thermal profile analytically before creep use.
Source temperatures are preserved; no artificial material law is fitted.
"""
from __future__ import annotations

import math
import numpy as np


class ThermalValidityError(ValueError):
    pass


def exact_layer_temperature_bounds_k(pre, layer):
    """Return exact min/max of the cubic PRE profile over layer depth.

    PRE uses local depth x=z-z0 and c0+c1*x+c2*x²+c3*x³.
    Endpoints and all real stationary points inside [0,z1-z0] are evaluated.
    """
    if layer not in (1,2):
        raise ThermalValidityError("G2_EXACT_THERMAL_LAYER_INVALID")
    prefix = f"layer{layer}_"
    names=("z0_m","z1_m","c0_k","c1_k_m","c2_k_m2","c3_k_m3")
    try:
        z0,z1,c0,c1,c2,c3=(float(pre[prefix+k]) for k in names)
    except (KeyError,TypeError,ValueError) as exc:
        raise ThermalValidityError("G2_EXACT_THERMAL_PRE_MISSING") from exc
    if not all(math.isfinite(v) for v in (z0,z1,c0,c1,c2,c3)) or z0<0 or z1<=z0:
        raise ThermalValidityError("G2_EXACT_THERMAL_PRE_INVALID")
    # Dimensionless t in [0,1] improves conditioning on ~100-km depth scales.
    L=z1-z0
    a=c3*L**3
    b=c2*L**2
    c=c1*L
    if not all(math.isfinite(v) for v in (a,b,c)):
        raise ThermalValidityError("G2_EXACT_THERMAL_COEFFICIENT_OVERFLOW")
    candidates=[0.0,1.0]
    # Derivative wrt dimensionless t: c + 2*b*t + 3*a*t**2.
    coeff=np.array([3*a,2*b,c],dtype=float)
    scale=float(np.max(np.abs(coeff)))
    if scale>0:
        q=coeff/scale
        if abs(q[0])>1e-14:
            roots=np.roots(q)
        elif abs(q[1])>1e-14:
            roots=np.array([-q[2]/q[1]])
        else:
            roots=[]
        for root in roots:
            if abs(float(np.imag(root)))<1e-11:
                t=float(np.real(root))
                if 0<t<1:
                    candidates.append(t)
    temps=[((a*t+b)*t+c)*t+c0 for t in candidates]
    if not all(math.isfinite(v) and v>0 for v in temps):
        raise ThermalValidityError("G2_EXACT_THERMAL_INVALID_TEMPERATURE")
    return float(min(temps)),float(max(temps))


def require_laboratory_temperature_coverage(pre, layer, creep_law):
    """Block whole-column extrapolation before sampling Gauss points.

    A passed interval does not prove rock identity or validity of pressure,
    water fugacity, stress convention or strain rate; those remain separate.
    """
    try:
        interval=creep_law["valid_temperature_k"]
        lo,hi=map(float,interval)
    except (KeyError,TypeError,ValueError) as exc:
        raise ThermalValidityError("G2_EXACT_THERMAL_LAB_RANGE_MISSING") from exc
    if len(interval)!=2 or not all(math.isfinite(v) for v in (lo,hi)) or not 0<lo<hi:
        raise ThermalValidityError("G2_EXACT_THERMAL_LAB_RANGE_INVALID")
    tmin,tmax=exact_layer_temperature_bounds_k(pre,layer)
    if tmin<lo or tmax>hi:
        raise ThermalValidityError("G2_VP_CREEP_LAB_PT_RATE_OUTSIDE_VALIDITY")
    return {"whole_layer_temperature_min_max_k":[tmin,tmax],
            "laboratory_valid_temperature_min_max_k":[lo,hi],
            "whole_layer_temperature_covered":True,
            "rock_identity_author_ratified":False}
