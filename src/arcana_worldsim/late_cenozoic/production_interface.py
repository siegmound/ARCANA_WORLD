from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .cha2_nested_50y import IntegratedLateCenozoicProviderC1
from .late_pleistocene_boundary import IntegratedLateCenozoicProviderC2

STATUS = "PASS_v0_6_4D_PRODUCTION_SUBSTRATE_INTERFACE_CANDIDATE"
AUTHORITY = "v0.6.4D_ENVIRONMENTAL_STACK_PLUS_SEALED_D3_REFERENCE_ABUNDANCE_CHANNEL"


def _a1_index(a1: Mapping[str, Any], age_ma: float) -> int:
    ages = np.asarray(a1["age_ma"], dtype=float)
    ii = np.where(np.isclose(ages, float(age_ma), atol=1e-12))[0]
    if len(ii) != 1:
        raise ValueError(f"A1 endpoint {age_ma} Ma not found exactly")
    return int(ii[0])


class D3LateCenozoicSubstrateAdapter:
    """Non-invasive v0.6.4D adapter from C2 environment to SEALED D3 substrate.

    Environmental fields are owned by the v0.6.4A..C2 stack.  The D3-only
    `reference_population` field remains the pre-existing A1 reference-abundance
    / opportunity anchor.  It is deliberately *not* A1 carrying_capacity and is
    not a target physical population state.
    """

    def __init__(self, a1: Mapping[str, Any], provider: IntegratedLateCenozoicProviderC2):
        self.a1 = a1
        self.provider = provider
        self.i30 = _a1_index(a1, 30.0)
        self.i0 = _a1_index(a1, 0.0)
        self.p30 = np.asarray(a1["population"][self.i30], dtype=float)
        self.p0 = np.asarray(a1["population"][self.i0], dtype=float)
        if self.p30.shape != self.p0.shape:
            raise ValueError("A1 30/0 Ma reference-population shapes differ")

    @staticmethod
    def age_from_relative_year(relative_year: float) -> float:
        return 66.0 - float(relative_year) / 1_000_000.0

    def reference_population_at(self, age_ma: float) -> np.ndarray:
        age = float(age_ma)
        if age < -1e-12 or age > 30.0 + 1e-12:
            raise ValueError("v0.6.4D production reference-abundance channel is scoped to 30->0 Ma")
        if abs(age - 30.0) < 1e-12:
            return self.p30.copy()
        if abs(age) < 1e-12:
            return self.p0.copy()
        alpha = (30.0 - age) / 30.0
        return (1.0 - alpha) * self.p30 + alpha * self.p0

    def state_at_age(self, age_ma: float) -> dict[str, Any]:
        age = float(age_ma)
        env = dict(self.provider.state_at(age))
        support = np.asarray(env["land_support"], dtype=float)
        ref = self.reference_population_at(age)
        out = dict(env)
        out.update({
            "accessible": support > 1e-9,
            "reference_population": ref,
            "reference_population_semantics": "A1_REFERENCE_ABUNDANCE_OPPORTUNITY_ANCHOR_NOT_CARRYING_CAPACITY_NOT_N_TARGET",
            "reference_population_interpolation_semantics": "LEGACY_D3_LINEAR_30_TO_0_A1_REFERENCE_ABUNDANCE_CHANNEL",
            "carrying_capacity_used_as_reference_population": False,
            "production_substrate_adapter": "D3LateCenozoicSubstrateAdapter_v0_6_4D",
            "production_interface_authority": AUTHORITY,
        })
        return out

    def for_d3(self, a1: Mapping[str, Any], relative_year: float, cfg: Any) -> dict[str, Any]:
        # Signature intentionally matches D3 diversification_adequacy._substrate_for_cfg.
        age = self.age_from_relative_year(relative_year)
        if age < -1e-9 or age > 30.0 + 1e-9:
            raise ValueError(f"Production late-Cenozoic adapter requested at {age} Ma outside 30->0 Ma")
        return self.state_at_age(age)


def build_production_adapter(root: Path) -> D3LateCenozoicSubstrateAdapter:
    root = Path(root)
    z = np.load(root / "inputs/A1_REFERENCE/fauna_baseline_state_A1.npz", allow_pickle=False)
    a1 = {k: z[k] for k in z.files}
    c1 = IntegratedLateCenozoicProviderC1(
        a1,
        root / "inputs/v0_6_1_SEALED_MINIMAL",
        root / "outputs/v0_6_4B1/exact_120ka_A1_boundary_state.npz",
        root / "outputs/v0_6_4B2/relative_eustatic_shoreline_anomaly_120ka_A1.npz",
    )
    c2 = IntegratedLateCenozoicProviderC2(c1)
    return D3LateCenozoicSubstrateAdapter(a1, c2)


@contextmanager
def patched_sealed_d3_substrate(adapter: D3LateCenozoicSubstrateAdapter):
    """Runtime-only injection; restores the SEALED D3 function on exit."""
    from arcana_worldsim.post_cha1 import diversification_adequacy as da
    original = da._substrate_for_cfg
    da._substrate_for_cfg = adapter.for_d3
    try:
        yield
    finally:
        da._substrate_for_cfg = original
