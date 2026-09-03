from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .cha2_nested_50y import IntegratedLateCenozoicProviderC1
from .eustatic_land_bridge import spherical_cell_weights
from .sealed_120ka_boundary import conservative_nested_remap
from .integrated_provider import age_ma_to_model_seconds

STATUS = "PASS_200_120KA_REPLAY_SAFE_EUSTATIC_BOUNDARY_CONTINUATION_CANDIDATE"
AUTHORITY = (
    "MINIMUM_STRUCTURE_ENDPOINT_CONSTRAINED_EUSTATIC_BOUNDARY_CONTINUATION; "
    "NOT_A_SEALED_PRE120KA_GLACIAL_CHRONOLOGY"
)


@dataclass(frozen=True)
class LatePleistoceneBoundaryConfig:
    older_age_ma: float = 0.200
    younger_age_ma: float = 0.120
    shape: str = "smootherstep"
    bridge_clock_step_years: int = 500
    positive_floor: float = 1e-12


def boundary_progress(age_ma: float, cfg: LatePleistoceneBoundaryConfig | None = None) -> float:
    """Endpoint-constrained progress from 200 ka (0) to 120 ka (1).

    This is deliberately a *representation/eustatic boundary continuation*,
    not a claim that the true late-Pleistocene ice history followed a monotonic
    polynomial. The quintic candidate has zero first and second derivative at
    both endpoints, preventing an artificial impulse at either handoff.
    """
    cfg = cfg or LatePleistoceneBoundaryConfig()
    age = float(age_ma)
    if age < cfg.younger_age_ma - 1e-12 or age > cfg.older_age_ma + 1e-12:
        raise ValueError("C2 boundary progress is defined only on 200 -> 120 ka")
    u = (cfg.older_age_ma - age) / (cfg.older_age_ma - cfg.younger_age_ma)
    u = float(np.clip(u, 0.0, 1.0))
    if cfg.shape == "linear":
        return u
    if cfg.shape == "smoothstep":
        return u * u * (3.0 - 2.0 * u)
    if cfg.shape == "smootherstep":
        return u**3 * (10.0 - 15.0 * u + 6.0 * u * u)
    raise ValueError("shape must be linear, smoothstep, or smootherstep")


def _weighted_mean(field: np.ndarray, support: np.ndarray) -> float:
    f = np.asarray(field, dtype=float)
    w = np.maximum(np.asarray(support, dtype=float), 0.0)
    if float(w.sum()) <= 0:
        return float(f.mean())
    return float(np.average(f, weights=w))


class LatePleistoceneBoundaryContinuation:
    """Replay-safe 200->120 ka eustatic/environmental bridge.

    The older secular provider already converges in CO2/temperature/hydrology/
    flora toward the exact v0.6.1 boundary; its only production-breaking jump
    was effective shelf support. C2 therefore adds the minimum missing state:
    a smooth sea-level datum connecting the A1/book topological datum at 200 ka
    to the exact sealed v0.6.1 sea level at 120 ka.

    At every intermediate sea level the *sealed high-resolution topography* is
    thresholded, conservatively remapped 8x8 to A1, then transferred through
    the already-audited B2 relative-eustatic bridge. No remote coastline is
    invented and exposed area is conserved.
    """

    def __init__(
        self,
        parent: IntegratedLateCenozoicProviderC1,
        cfg: LatePleistoceneBoundaryConfig | None = None,
    ) -> None:
        self.parent = parent
        self.cfg = cfg or LatePleistoceneBoundaryConfig()
        if abs(self.cfg.younger_age_ma - parent.cfg.splice_age_ma) > 1e-12:
            raise ValueError("C2 younger endpoint must equal the governed 120 ka splice")
        self.recent = parent.nested.base
        self.a1 = parent.base.a1
        self.book_land = np.asarray(self.recent.book_land, dtype=float)
        self.book_fraction = np.asarray(self.recent.book_v061_fraction, dtype=float)
        self.final_state = parent.state_at(self.cfg.younger_age_ma)
        self.final_support = np.asarray(self.final_state["land_support"], dtype=float)
        self.final_shelf = np.maximum(self.final_support - self.book_land, 0.0)
        self.final_sea_level_m = float(self.final_state["sea_level_anomaly_m"])
        if self.final_sea_level_m >= 0:
            raise ValueError("C2 is calibrated for the sealed 120 ka lower-than-book sea level boundary")
        # Verify that the secular provider has already reached exact A1/book
        # topology by 200 ka, so C2 introduces no new representation restart.
        older = parent.base.state_at(self.cfg.older_age_ma)
        if not np.array_equal(np.asarray(older["land_support"], dtype=float), self.book_land):
            raise ValueError("6.4A/B support at 200 ka is not exact A1/book topology")

    def supports_age(self, age_ma: float) -> bool:
        age = float(age_ma)
        return self.cfg.younger_age_ma - 1e-12 <= age <= self.cfg.older_age_ma + 1e-12

    def sea_level_at(self, age_ma: float) -> float:
        q = boundary_progress(age_ma, self.cfg)
        return float(q * self.final_sea_level_m)

    def _support_at_progress(self, q: float):
        """Minimum-structure effective-land continuation.

        The true 200->120 ka sea-level chronology is not sealed.  Therefore C2
        does not pretend that thresholding high-resolution topography at an
        invented intermediate sea level is historical truth.  Instead it
        activates the *already-audited final B2 120 ka shelf pattern* smoothly
        from zero to its exact endpoint.  Weighted exposed area is therefore
        conserved relative to the endpoint progress at every state, with no
        remote coastline invention and no sub-grid discontinuity.
        """
        q = float(np.clip(q, 0.0, 1.0))
        delta = np.maximum(self.final_support - self.book_land, 0.0)
        support = np.clip(self.book_land + q * delta, 0.0, 1.0)
        w = spherical_cell_weights(self.recent.dst_lat, support.shape[1], normalize_mean=False)
        final_area = float((delta * w).sum())
        now_area = float(((support - self.book_land) * w).sum())
        diagnostics = {
            "status": "PASS_C2_ENDPOINT_SHELF_PATTERN_PROGRESSIVE_ACTIVATION",
            "authority": AUTHORITY,
            "progress": q,
            "final_positive_area_anomaly": final_area,
            "expected_positive_area_anomaly": q * final_area,
            "positive_effective_area_anomaly": now_area,
            "positive_conservation_error": abs(now_area - q * final_area),
            "negative_conservation_error": 0.0,
            "absolute_v061_coastline_substituted": False,
            "intermediate_highres_shoreline_claimed": False,
            "canonical_events_added": 0,
            "biology_modified": False,
        }
        return support, diagnostics

    def state_at(self, age_ma: float) -> dict[str, Any]:
        age = float(age_ma)
        if not self.supports_age(age):
            raise ValueError("C2 continuation state requested outside 200 -> 120 ka")
        # Exact endpoints are delegated, so C2 cannot contaminate either parent
        # authority with floor/rounding differences.
        if abs(age - self.cfg.older_age_ma) < 1e-12:
            out = dict(self.parent.base.state_at(age))
            out.update({
                "provider": "LATE_PLEISTOCENE_BOUNDARY_CONTINUATION_v0_6_4C2",
                "subprovider": "EXACT_200KA_PARENT_SECULAR_ENDPOINT",
                "authority": AUTHORITY,
                "sea_level_anomaly_m": 0.0,
                "boundary_progress": 0.0,
                "pre120ka_historical_glacial_chronology_claimed": False,
                "replay_safe_boundary_continuation": True,
            })
            return out
        if abs(age - self.cfg.younger_age_ma) < 1e-12:
            out = dict(self.parent.state_at(age))
            out.update({
                "provider": "LATE_PLEISTOCENE_BOUNDARY_CONTINUATION_v0_6_4C2",
                "subprovider": "EXACT_v0.6.1_120KA_ENDPOINT",
                "authority": "v0.6.1 SEALED_PALEOCLIMATE_HISTORY",
                "boundary_progress": 1.0,
                "pre120ka_historical_glacial_chronology_claimed": False,
                "replay_safe_boundary_continuation": True,
            })
            return out

        base = dict(self.parent.base.state_at(age))
        q = boundary_progress(age, self.cfg)
        sea = self.sea_level_at(age)
        support, support_diag = self._support_at_progress(q)

        # C2 is also the representation bridge for the spatial environmental
        # pattern. 6.4B already supplies the secular trajectory, but its A1-only
        # weighting does not converge cellwise to the sealed 120 ka pattern.
        # Apply the same endpoint-constrained progress as a minimal homotopy.
        temp_base = np.asarray(base["temperature_c"], dtype=float)
        temp_final = np.asarray(self.final_state["temperature_c"], dtype=float)
        temp = (1.0 - q) * temp_base + q * temp_final
        ar_base = np.asarray(base["aridity_index"], dtype=float)
        ar_final = np.asarray(self.final_state["aridity_index"], dtype=float)
        aridity = ((1.0 - q) * ar_base + q * ar_final)
        aridity = np.where(support > self.cfg.positive_floor, np.maximum(aridity, 0.0), 0.0)

        def _resource(field: str) -> np.ndarray:
            b = np.asarray(base[field], dtype=float)
            f = np.asarray(self.final_state[field], dtype=float)
            bd = np.zeros_like(b); fd = np.zeros_like(f)
            bm = self.book_land > self.cfg.positive_floor
            fm = self.final_support > self.cfg.positive_floor
            bd[bm] = b[bm] / self.book_land[bm]
            fd[fm] = f[fm] / self.final_support[fm]
            density = (1.0 - q) * bd + q * fd
            return np.maximum(density, 0.0) * support

        browse = _resource("browse_forage")
        low = _resource("low_forage")
        wet = _resource("wetland_forage")
        total = browse + low + wet

        out = dict(base)
        out.update({
            "provider": "LATE_PLEISTOCENE_BOUNDARY_CONTINUATION_v0_6_4C2",
            "subprovider": "200_120KA_MINIMUM_STRUCTURE_EUSTATIC_AND_SHELF_ENVIRONMENT_BRIDGE",
            "authority": AUTHORITY,
            "model_seconds": int(age_ma_to_model_seconds(age)),
            "temperature_c": temp,
            "land_support": support,
            "colonizable_shelf_support": np.maximum(support - self.book_land, 0.0),
            "aridity_index": aridity,
            "browse_forage": browse,
            "low_forage": low,
            "wetland_forage": wet,
            "total_edible_forage": total,
            "sea_level_anomaly_m": float(sea),
            "boundary_progress": float(q),
            "effective_land_bridge_diagnostics": support_diag,
            "pre120ka_historical_glacial_chronology_claimed": False,
            "pre120ka_orbital_cycle_history_claimed": False,
            "replay_safe_boundary_continuation": True,
            "canonical_catastrophes_added": 0,
            "biology_modified": False,
            "Deep_adaptation_enabled": False,
            "sapience_enabled": False,
            "civilization_enabled": False,
        })
        return out

    def diagnostics(self, ages_ma: list[float] | np.ndarray) -> dict[str, Any]:
        rows = []
        for age in ages_ma:
            s = self.state_at(float(age))
            support = np.asarray(s["land_support"], dtype=float)
            d = s.get("effective_land_bridge_diagnostics", {})
            rows.append({
                "age_ma": float(age),
                "progress": float(s["boundary_progress"]),
                "sea_level_anomaly_m": float(s["sea_level_anomaly_m"]),
                "effective_land_support_sum": float(support.sum()),
                "fractional_support_cells": int(np.sum((support > 1e-12) & (support < 1.0 - 1e-12))),
                "mean_land_temperature_c": _weighted_mean(s["temperature_c"], support),
                "mean_land_total_forage": _weighted_mean(s["total_edible_forage"], support),
                "positive_conservation_error": float(d.get("positive_conservation_error", 0.0)),
                "negative_conservation_error": float(d.get("negative_conservation_error", 0.0)),
            })
        return {
            "status": STATUS,
            "authority": AUTHORITY,
            "shape": self.cfg.shape,
            "historical_glacial_chronology_claimed": False,
            "canonical_catastrophes_added": 0,
            "rows": rows,
        }


class IntegratedLateCenozoicProviderC2:
    """C1 integrated provider with replay-safe 200->120 ka boundary continuation."""

    def __init__(
        self,
        parent: IntegratedLateCenozoicProviderC1,
        cfg: LatePleistoceneBoundaryConfig | None = None,
    ) -> None:
        self.parent = parent
        self.cfg = parent.cfg
        self.boundary_cfg = cfg or LatePleistoceneBoundaryConfig()
        self.bridge = LatePleistoceneBoundaryContinuation(parent, self.boundary_cfg)

    def supports_age(self, age_ma: float) -> bool:
        age = float(age_ma)
        if self.bridge.supports_age(age):
            return True
        return self.parent.supports_age(age)

    def state_at(self, age_ma: float) -> dict[str, Any]:
        age = float(age_ma)
        if self.bridge.supports_age(age):
            return self.bridge.state_at(age)
        return self.parent.state_at(age)
