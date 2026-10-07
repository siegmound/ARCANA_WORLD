"""Fail-closed transient thermal columns governed by PRE_ORBDATA A0.6 contracts."""
from __future__ import annotations

from dataclasses import dataclass
import math

from .pre_orbdata_heat_flow import HWR2

G = 9.82
ADIABAT_KM = 100_000.0


@dataclass(frozen=True)
class LayerMaterial:
    k: float
    rho: float
    cp: float
    radiogenic_w_m3: float

    def validate(self) -> None:
        if not all(math.isfinite(v) for v in (self.k,self.rho,self.cp,self.radiogenic_w_m3)):
            raise ValueError("THERMAL_MATERIAL_NONFINITE")
        if min(self.k,self.rho,self.cp) <= 0 or self.radiogenic_w_m3 < 0:
            raise ValueError("THERMAL_MATERIAL_OUT_OF_DOMAIN")


@dataclass(frozen=True)
class Column:
    kind: str
    age_ma: float | None
    q_surface_w_m2: float
    crust_m: float
    mantle_m: float
    lab_m: float
    moho_temperature_k: float
    moho_flux_w_m2: float
    lab_temperature_k: float
    lab_flux_w_m2: float
    transient_rate_k_s: float | None
    effective_age_ma: float | None
    # (z0, z1, c2, c1, c0); local coordinate is (z-z0) for quadratic
    # layers and normalized s=(z-z0)/(z1-z0) for cubic Hermite layers.
    profile_coefficients: tuple[tuple[float, ...], ...] = ()


def _finite(*values: float) -> None:
    if not all(math.isfinite(v) for v in values):
        raise ValueError("THERMAL_COLUMN_NONFINITE")


def _within_material_bounds(material: LayerMaterial, *, k, rho, cp, production, label: str) -> None:
    bounds=((material.k,*k),(material.rho,*rho),(material.cp,*cp),
            (material.radiogenic_w_m3,*production))
    if any(not low <= value <= high for value,low,high in bounds):
        raise ValueError(f"{label}_OUTSIDE_GOVERNED_SENSITIVITY_RANGE")


def _adiabat(model: HWR2, z_m: float, alpha=3.0e-5, gravity=G, cp=1200.0) -> float:
    tp = model.tb_k * math.exp(-alpha*gravity*model.zp_m/cp)
    return tp * math.exp(alpha*gravity*z_m/cp)


def continental_column(*, q_surface: float, crust_m: float, total_lithosphere_m: float,
                       crust: LayerMaterial = LayerMaterial(2.5,2800,1000,8e-7),
                       mantle: LayerMaterial = LayerMaterial(3.3,3300,1200,2e-8),
                      model: HWR2 = HWR2(), mantle_alpha_k_1: float = 3.0e-5,
                      gravity_m_s2: float = G) -> Column:
    model.validate()
    crust.validate(); mantle.validate()
    _within_material_bounds(crust,k=(2.0,3.0),rho=(2700,2900),cp=(800,1200),
                            production=(4e-7,1.2e-6),label="CONTINENTAL_CRUST")
    _within_material_bounds(mantle,k=(3.0,4.1),rho=(3200,3400),cp=(1100,1250),
                            production=(0.0,4e-8),label="LITHOSPHERIC_MANTLE")
    hm = total_lithosphere_m - crust_m
    _finite(q_surface, crust_m, total_lithosphere_m, hm)
    if q_surface <= 0 or crust_m <= 0 or hm <= 0:
        raise ValueError("THERMAL_COLUMN_INVALID_LAYER_THICKNESS_OR_FLUX")
    h, m = crust_m, hm
    if not math.isfinite(mantle_alpha_k_1) or mantle_alpha_k_1 <= 0:
        raise ValueError("THERMAL_COLUMN_ALPHA_INVALID")
    if not math.isfinite(gravity_m_s2) or gravity_m_s2 <= 0:
        raise ValueError("THERMAL_COLUMN_GRAVITY_INVALID")
    target = _adiabat(model, total_lithosphere_m, alpha=mantle_alpha_k_1,
                      gravity=gravity_m_s2, cp=mantle.cp)
    steady = (model.t0_k + q_surface*h/crust.k - crust.radiogenic_w_m3*h*h/(2*crust.k)
              + (q_surface-crust.radiogenic_w_m3*h)*m/mantle.k
              - mantle.radiogenic_w_m3*m*m/(2*mantle.k))
    b = (crust.rho*crust.cp*(h*h/(2*crust.k)+h*m/mantle.k)
         + mantle.rho*mantle.cp*m*m/(2*mantle.k))
    if not math.isfinite(b) or b <= 0:
        raise ValueError("THERMAL_COLUMN_RATE_DENOMINATOR_INVALID")
    rate = (target-steady)/b
    qmoho = q_surface + (crust.rho*crust.cp*rate-crust.radiogenic_w_m3)*h
    tmoho = (model.t0_k+q_surface*h/crust.k
             +(crust.rho*crust.cp*rate-crust.radiogenic_w_m3)*h*h/(2*crust.k))
    qlab = qmoho+(mantle.rho*mantle.cp*rate-mantle.radiogenic_w_m3)*m
    _finite(rate,qmoho,tmoho,qlab,target)
    if max(tmoho,target) >= 1900.0:
        raise ValueError("THERMAL_COLUMN_NUMERICAL_CEILING_REACHED")
    # Endpoints and critical point checks enforce the governed monotone profile.
    if min(q_surface,qmoho,qlab) <= 0:
        raise ValueError("THERMAL_COLUMN_NONMONOTONE_OR_NEGATIVE_FLUX")
    if tmoho < model.t0_k or tmoho > target:
        raise ValueError("THERMAL_COLUMN_INTERNAL_TEMPERATURE_EXTREMUM")
    crust_r=crust.rho*crust.cp*rate-crust.radiogenic_w_m3
    mantle_r=mantle.rho*mantle.cp*rate-mantle.radiogenic_w_m3
    coefficients=((0.0,h,crust_r/(2*crust.k),q_surface/crust.k,model.t0_k),
                  (h,total_lithosphere_m,mantle_r/(2*mantle.k),qmoho/mantle.k,tmoho))
    return Column("CONTINENT",None,q_surface,h,m,total_lithosphere_m,tmoho,qmoho,
                  target,qlab,rate,None,coefficients)


def ocean_column(*, age_ma: float, crust_m: float, q_surface: float | None = None,
                 model: HWR2 = HWR2(), ridge: bool = False,
                 crust: LayerMaterial = LayerMaterial(2.2,2890,1000,3e-7),
                 mantle_alpha_k_1: float = 3.0e-5,
                 gravity_m_s2: float = G) -> Column:
    model.validate()
    crust.validate()
    _within_material_bounds(crust,k=(1.8,2.8),rho=(2850,2930),cp=(800,1200),
                            production=(0.0,5e-7),label="OCEANIC_CRUST")
    if ridge:
        if age_ma != 0:
            raise ValueError("RIDGE_AUTHORED_AGE_MUST_REMAIN_ZERO")
        effective_age = model.positive_equivalent_age(.3)
        age_eval, q = effective_age, .3
    else:
        if not math.isfinite(age_ma) or age_ma <= 0:
            raise ValueError("OCEAN_AGE_MUST_BE_POSITIVE")
        if not 1.1491667412337465 <= age_ma <= 160.0:
            raise ValueError("OCEAN_AGE_OUTSIDE_GOVERNED_DOMAIN")
        age_eval = age_ma
        q = model.flux(age_ma)
        if q_surface is not None and not math.isclose(q_surface,q,rel_tol=0,abs_tol=1e-12):
            raise ValueError("OCEAN_SURFACE_FLUX_DOES_NOT_MATCH_HWR")
    if not math.isfinite(crust_m) or crust_m <= 0:
        raise ValueError("OCEAN_CRUST_THICKNESS_INVALID")
    if crust_m >= model.zp_m:
        raise ValueError("OCEAN_CRUST_SUBTRACTED_PLATE_THICKNESS_NONPOSITIVE")
    if not math.isfinite(mantle_alpha_k_1) or mantle_alpha_k_1 <= 0:
        raise ValueError("THERMAL_COLUMN_ALPHA_INVALID")
    if not math.isfinite(gravity_m_s2) or gravity_m_s2 <= 0:
        raise ValueError("THERMAL_COLUMN_GRAVITY_INVALID")
    # Find the first HWR/adiabat intersection after Moho. Use fixed spatial
    # scan, then bisection; if absent, the governed coupled basal boundary is zp.
    previous_z = crust_m
    previous_f = model.temperature(age_eval, previous_z)-_adiabat(
        model, previous_z, alpha=mantle_alpha_k_1, gravity=gravity_m_s2,
        cp=model.cp_j_kg_k)
    lab = None
    for i in range(1,257):
        z = crust_m+(model.zp_m-crust_m)*i/256
        f = model.temperature(age_eval,z)-_adiabat(
            model, z, alpha=mantle_alpha_k_1, gravity=gravity_m_s2,
            cp=model.cp_j_kg_k)
        if previous_f < 0 <= f:
            lo,hi=previous_z,z
            for _ in range(64):
                mid=(lo+hi)/2
                if model.temperature(age_eval,mid)-_adiabat(
                        model, mid, alpha=mantle_alpha_k_1,
                        gravity=gravity_m_s2, cp=model.cp_j_kg_k) >= 0: hi=mid
                else: lo=mid
            lab=(lo+hi)/2
            break
        previous_z,previous_f=z,f
    if lab is None:
        lab=model.zp_m
    if lab <= crust_m or lab > model.zp_m:
        raise ValueError("OCEAN_LAB_OUTSIDE_GOVERNED_GEOMETRY")
    tmoho=model.temperature(age_eval,crust_m)
    qmoho=model.depth_flux(age_eval,crust_m)
    tlab=_adiabat(model,lab,alpha=mantle_alpha_k_1,
                  gravity=gravity_m_s2,cp=model.cp_j_kg_k)
    qlab=model.depth_flux(age_eval,lab)
    _finite(tmoho,qmoho,tlab,qlab,q)
    if max(tmoho,tlab) >= 1900.0:
        raise ValueError("THERMAL_COLUMN_NUMERICAL_CEILING_REACHED")
    # Check cubic Hermite temperature segment monotonicity with derivative
    # extrema; endpoints are the exact governed temperature/flux states.
    crust_poly=_validate_hermite(0,crust_m,model.t0_k,tmoho,q/crust.k,qmoho/crust.k)
    mantle_poly=_validate_hermite(crust_m,lab,tmoho,tlab,qmoho/model.k_w_m_k,qlab/model.k_w_m_k)
    return Column("RIDGE" if ridge else "POSITIVE_AGE_OCEAN",0.0 if ridge else age_ma,
                  q,crust_m,lab-crust_m,lab,tmoho,qmoho,tlab,qlab,None,
                  effective_age if ridge else None,(crust_poly,mantle_poly))


def _validate_hermite(x0,x1,y0,y1,d0,d1) -> tuple[float,...]:
    dx=x1-x0
    if not math.isfinite(dx) or dx <= 0:
        raise ValueError("HERMITE_LAYER_THICKNESS_INVALID")
    # p(s)=a*s^3+b*s^2+c*s+d; derivative roots in [0,1] are checked.
    a=2*y0-2*y1+dx*(d0+d1)
    b=-3*y0+3*y1-dx*(2*d0+d1)
    c=dx*d0
    points=[0.0,1.0]
    disc=4*b*b-12*a*c
    if abs(a)>1e-30 and disc>=0:
        points.extend(x for x in ((-2*b-math.sqrt(disc))/(6*a),(-2*b+math.sqrt(disc))/(6*a)) if 0<x<1)
    elif abs(b)>1e-30:
        x=-c/(2*b)
        if 0<x<1: points.append(x)
    vals=[((a*s+b)*s+c)*s+y0 for s in points]
    deriv=[(3*a*s*s+2*b*s+c)/dx for s in points]
    if min(vals)<min(y0,y1)-1e-7 or max(vals)>max(y0,y1)+1e-7 or min(deriv)<-1e-12:
        raise ValueError("HERMITE_PROFILE_NONMONOTONE_OR_OVERSHOOT")
    return (x0,x1,a,b,c,y0)
