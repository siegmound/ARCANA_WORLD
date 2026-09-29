"""Governed deterministic PRE_ORBDATA heat-flow production (no OrbData calls)."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

import numpy as np

OCEAN = 1
CONTINENTAL_IDS = frozenset({2, 3, 4, 5, 6})
RIDGE_Q = 0.3
MA_PER_S = 1.0e6 * 365.25 * 24.0 * 3600.0
HWR_N = 256
HWR_TOL = 1.0e-12


@dataclass(frozen=True)
class HWR2:
    k_w_m_k: float = 3.3
    rho_kg_m3: float = 3300.0
    cp_j_kg_k: float = 1200.0
    tb_k: float = 1680.0
    t0_k: float = 280.0
    zp_m: float = 100_000.0
    n_modes: int = HWR_N
    convergence_tolerance: float = HWR_TOL

    def validate(self) -> None:
        values = (self.k_w_m_k, self.rho_kg_m3, self.cp_j_kg_k,
                  self.tb_k, self.t0_k, self.zp_m, self.convergence_tolerance)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("HWR2_NONFINITE_PARAMETER")
        if min(self.k_w_m_k, self.rho_kg_m3, self.cp_j_kg_k,
               self.zp_m, self.convergence_tolerance) <= 0 or self.tb_k <= self.t0_k:
            raise ValueError("HWR2_PARAMETER_OUT_OF_DOMAIN")
        bounds=((self.k_w_m_k,3.0,4.1),(self.rho_kg_m3,3200.0,3400.0),
                (self.cp_j_kg_k,1100.0,1250.0),(self.tb_k,1523.0,1737.0),
                (self.t0_k,250.0,300.0),(self.zp_m,80000.0,140000.0))
        if any(not lo <= value <= hi for value,lo,hi in bounds):
            raise ValueError("HWR2_PARAMETER_OUTSIDE_GOVERNED_SENSITIVITY_RANGE")
        if self.n_modes != HWR_N or self.convergence_tolerance != HWR_TOL:
            raise ValueError("HWR2_NUMERICAL_CONTROL_NOT_GOVERNED")

    @property
    def kappa(self) -> float:
        return self.k_w_m_k / (self.rho_kg_m3 * self.cp_j_kg_k)

    def _exponents(self, age_ma: float) -> np.ndarray:
        self.validate()
        if not math.isfinite(age_ma) or age_ma <= 0:
            raise ValueError("HWR2_AGE_OUTSIDE_GOVERNED_DOMAIN")
        if not 1.1491667412337465 <= age_ma <= 160.0:
            raise ValueError("HWR2_AGE_OUTSIDE_GOVERNED_DOMAIN")
        n = np.arange(1, self.n_modes + 1, dtype=np.float64)
        return np.exp(-self.kappa * n*n * math.pi**2 * age_ma * MA_PER_S / self.zp_m**2)

    def flux(self, age_ma: float) -> float:
        ex = self._exponents(age_ma)
        q = self.k_w_m_k * (self.tb_k - self.t0_k) / self.zp_m * (1.0 + 2.0 * float(ex.sum()))
        if not math.isfinite(q) or q <= 0:
            raise ValueError("HWR2_INVALID_FLUX")
        return q

    def flux_many(self, ages_ma: np.ndarray) -> np.ndarray:
        ages=np.asarray(ages_ma,dtype=np.float64)
        self.validate()
        if np.any(~np.isfinite(ages)) or np.any(ages<1.1491667412337465) or np.any(ages>160.0):
            raise ValueError("HWR2_AGE_MUST_BE_STRICTLY_POSITIVE")
        n=np.arange(1,self.n_modes+1,dtype=np.float64)
        out=np.empty(ages.shape,dtype=np.float64)
        flat=ages.ravel(); target=out.ravel()
        scale=self.kappa*math.pi**2*MA_PER_S/self.zp_m**2
        for start in range(0,len(flat),1024):
            a=flat[start:start+1024,None]
            target[start:start+len(a)]=self.k_w_m_k*(self.tb_k-self.t0_k)/self.zp_m*(
                1+2*np.exp(-scale*a*n[None,:]**2).sum(axis=1))
        if np.any(~np.isfinite(out)) or np.any(out<=0):
            raise ValueError("HWR2_INVALID_FLUX")
        return out

    def temperature(self, age_ma: float, z_m: float) -> float:
        ex = self._exponents(age_ma)
        if not math.isfinite(z_m) or not 0 <= z_m <= self.zp_m:
            raise ValueError("HWR2_DEPTH_OUT_OF_DOMAIN")
        n = np.arange(1, self.n_modes + 1, dtype=np.float64)
        delta = self.tb_k - self.t0_k
        t = self.t0_k + delta*z_m/self.zp_m + (2.0*delta/math.pi)*float(
            np.sum(np.sin(n*math.pi*z_m/self.zp_m)*ex/n))
        if not math.isfinite(t) or t < self.t0_k - 1e-8 or t > self.tb_k + 1e-8:
            raise ValueError("HWR2_TEMPERATURE_OUT_OF_BOUNDS")
        return t

    def depth_flux(self, age_ma: float, z_m: float) -> float:
        ex = self._exponents(age_ma)
        if not math.isfinite(z_m) or not 0 <= z_m <= self.zp_m:
            raise ValueError("HWR2_DEPTH_OUT_OF_DOMAIN")
        n = np.arange(1, self.n_modes + 1, dtype=np.float64)
        q = self.k_w_m_k * (self.tb_k - self.t0_k) / self.zp_m * (
            1.0 + 2.0*float(np.sum(np.cos(n*math.pi*z_m/self.zp_m)*ex)))
        if not math.isfinite(q):
            raise ValueError("HWR2_NONFINITE_DEPTH_FLUX")
        return q

    def positive_equivalent_age(self, q_w_m2: float, *, bracket_ma=(1.1491667412337465, 160.0)) -> float:
        if not math.isfinite(q_w_m2) or q_w_m2 <= 0:
            raise ValueError("HWR2_INVERSE_FLUX_INVALID")
        lo, hi = map(float, bracket_ma)
        qlo, qhi = self.flux(lo), self.flux(hi)
        if not (qlo >= q_w_m2 >= qhi):
            raise ValueError("HWR2_INVERSE_OUTSIDE_GOVERNED_AGE_ENVELOPE")
        for _ in range(80):
            mid = (lo + hi) / 2
            if self.flux(mid) > q_w_m2:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2


@dataclass(frozen=True)
class HeatFlowCell:
    value_w_m2: float
    source_branch: str
    parent_lineage: Mapping[str, str]
    model_identity: str | None
    applicability: str
    uncertainty: Mapping[str, object]


def produce_heat_flow(*, physical_domain: np.ndarray, age_ma: np.ndarray,
                      continental_q_w_m2: np.ndarray, ridge_support: np.ndarray,
                      parent_lineage: Mapping[str, str], model: HWR2 | None = None
                      ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return q, branch codes (1 continent, 2 ridge, 3 ocean), and known mask.

    Sensitivity bounds are configuration metadata, not per-cell probability
    distributions. The returned deterministic field remains replayable state.
    """
    domain = np.asarray(physical_domain)
    age = np.asarray(age_ma, dtype=np.float64)
    cq = np.asarray(continental_q_w_m2, dtype=np.float64)
    ridge = np.asarray(ridge_support, dtype=bool)
    if not (domain.shape == age.shape == cq.shape == ridge.shape):
        raise ValueError("HEAT_FLOW_PARENT_SHAPE_MISMATCH")
    if not parent_lineage or any(not k or not v for k, v in parent_lineage.items()):
        raise ValueError("HEAT_FLOW_LINEAGE_MISSING")
    if model is None:
        model = HWR2()
    model.validate()
    q = np.full(domain.shape, np.nan, dtype=np.float64)
    branch = np.zeros(domain.shape, dtype=np.uint8)
    ocean = domain == OCEAN
    continent = np.isin(domain, tuple(CONTINENTAL_IDS))
    if np.any(~(ocean | continent)):
        raise ValueError("HEAT_FLOW_UNKNOWN_PHYSICAL_DOMAIN")
    if np.any(ridge & ~ocean):
        raise ValueError("RIDGE_SUPPORT_OUTSIDE_OCEAN_DOMAIN")
    if np.any(~np.isfinite(age[ocean])) or np.any(age[ocean] < 0):
        raise ValueError("HEAT_FLOW_INVALID_OCEAN_AGE")
    if np.any(~np.isfinite(cq[continent])):
        raise ValueError("HEAT_FLOW_CONTINENTAL_REFERENCE_MISSING")
    if np.any(cq[continent] < .045-1e-12) or np.any(cq[continent] > .085+1e-12):
        raise ValueError("HEAT_FLOW_CONTINENTAL_REFERENCE_OUT_OF_AUTHORITY")
    zero = ocean & (age == 0)
    if not np.array_equal(zero, ridge):
        raise ValueError("HEAT_FLOW_ZERO_AGE_RIDGE_MASK_MISMATCH")
    pos = ocean & (age > 0)
    if np.any(pos & ridge):
        raise ValueError("HEAT_FLOW_RIDGE_POSITIVE_AGE_OVERLAP")
    if np.any(pos & ((age < 1.1491667412337465) | (age > 160.0))):
        raise ValueError("HEAT_FLOW_AGE_OUTSIDE_GOVERNED_SUPPORT")
    q[continent] = cq[continent]; branch[continent] = 1
    q[zero] = RIDGE_Q; branch[zero] = 2
    # Explicit positive-age loop prevents accidental t=0 HWR evaluation.
    q[pos] = model.flux_many(age[pos])
    branch[pos] = 3
    if np.any(~np.isfinite(q[ocean])) or np.any(q[ocean] <= 0):
        raise ValueError("HEAT_FLOW_OCEAN_OUTPUT_INVALID")
    return q, branch, np.ones(domain.shape, dtype=bool)


def cell_provenance_record(value_w_m2: float, branch_code: int,
                           parent_lineage: Mapping[str, str]) -> HeatFlowCell:
    """Create a per-cell lineage record without promoting values to authored state."""
    if not math.isfinite(value_w_m2) or value_w_m2 <= 0:
        raise ValueError("HEAT_FLOW_CELL_VALUE_INVALID")
    names={1:("CONTINENTAL_AUTHORED_REFERENCE",None),
           2:("GOVERNED_RIDGE_BOUNDARY",None),
           3:("POSITIVE_AGE_HWR2","HWR2_FINITE_PLATE_CONSTANT_PROPERTY_SURFACE_FLUX")}
    if branch_code not in names:
        raise ValueError("HEAT_FLOW_CELL_BRANCH_UNKNOWN")
    branch,model=names[branch_code]
    return HeatFlowCell(value_w_m2,branch,dict(parent_lineage),model,
                        "APPLICABLE_GOVERNED_SUPPORT",
                        {"numeric_interval":"SEE_CONFIGURED_GLOBAL_SENSITIVITY_ENVELOPE",
                         "authored_uncertainty_distribution":"NOT_GOVERNED"})
