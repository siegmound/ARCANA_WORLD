from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import math
import numpy as np

import d3_paleogeographic_history_v0_6_3D3_2C as pgh

R3_PROVIDER_STAGE_ID = "v0.6D1-R3"
R3_PROVIDER_STATUS = "PASS_MULTI_BRACKET_D3_2C_BARRIER_HISTORY_BINDING_CANDIDATE"

CONTINUOUS_KEYS = (
    "temperature_c", "aridity_index", "browse_forage", "low_forage",
    "wetland_forage", "total_edible_forage",
)
REFERENCE_KEYS = (("population", "reference_population"), ("carrying_capacity", "reference_capacity"))


@dataclass(frozen=True)
class BarrierHistoryConfig:
    phase_min: float = 0.05
    phase_max: float = 0.95
    transition_width_years: float = 1_000_000.0
    accessibility_floor: float = 1e-9
    connectivity_land_support_threshold: float = 0.25
    connectivity_softness: float = 0.10
    habitat_connectivity_power: float = 0.50
    effective_connectivity_core_threshold: float = 0.20


def validate_a1(a1: Any) -> None:
    ages = np.asarray(a1["age_ma"], dtype=float)
    if len(ages) < 2:
        raise ValueError("A1 must contain at least two age keyframes")
    if not np.all(np.diff(ages) < 0):
        raise ValueError("A1 age_ma must be strictly descending")
    shape = tuple(np.asarray(a1["land_mask"]).shape)
    if len(shape) != 3 or shape[0] != len(ages):
        raise ValueError("land_mask must be [age,lat,lon]")
    for key in ("plate_code",) + CONTINUOUS_KEYS:
        if tuple(np.asarray(a1[key]).shape) != shape:
            raise ValueError(f"{key} shape must match land_mask")
    for key, _ in REFERENCE_KEYS:
        arr = np.asarray(a1[key])
        if arr.ndim != 4 or arr.shape[0] != len(ages) or arr.shape[2:] != shape[1:]:
            raise ValueError(f"{key} must be [age,guild,lat,lon]")


def bracket_for_age(a1: Any, age_ma: float) -> tuple[int, int, float, float]:
    ages = np.asarray(a1["age_ma"], dtype=float)
    age = float(age_ma)
    if age >= float(ages[0]) - 1e-12:
        return 0, 1, float(ages[0]), float(ages[1])
    if age <= float(ages[-1]) + 1e-12:
        return len(ages)-2, len(ages)-1, float(ages[-2]), float(ages[-1])
    for i in range(len(ages)-1):
        older, younger = float(ages[i]), float(ages[i+1])
        if older + 1e-12 >= age >= younger - 1e-12:
            return i, i+1, older, younger
    raise RuntimeError("could not resolve A1 age bracket")


def _alpha(age: float, older: float, younger: float) -> float:
    return float(np.clip((older - float(age)) / max(older-younger, 1e-15), 0.0, 1.0))


def _lerp(a1: Any, key: str, i0: int, i1: int, alpha: float) -> np.ndarray:
    return (1.0-alpha) * np.asarray(a1[key][i0], dtype=float) + alpha * np.asarray(a1[key][i1], dtype=float)


def _event_plate_code(a1: Any, age: float, i0: int, i1: int, older: float, younger: float,
                      sched: dict) -> np.ndarray:
    p0 = np.asarray(a1["plate_code"][i0], dtype=np.uint8)
    p1 = np.asarray(a1["plate_code"][i1], dtype=np.uint8)
    if age >= older - 1e-12:
        return p0.copy()
    if age <= younger + 1e-12:
        return p1.copy()
    alpha = _alpha(age, older, younger)
    phase = np.asarray(sched["phase"], dtype=float)
    out = p0.copy()
    changed = np.asarray(sched["kind"]) != 0
    after = changed & (alpha >= phase)
    out[after] = p1[after]
    # For persistent land cells where plate codes differ, use bracket midpoint.
    persistent = np.asarray(sched["persistent_land"], dtype=bool)
    pp = persistent & (p0 != p1)
    out[pp & (alpha >= 0.5)] = p1[pp & (alpha >= 0.5)]
    return out


def environment_at(age_ma: float, a1: Any, cfg: BarrierHistoryConfig = BarrierHistoryConfig()) -> dict:
    validate_a1(a1)
    i0, i1, older, younger = bracket_for_age(a1, age_ma)
    age = float(np.clip(age_ma, younger, older))
    a = _alpha(age, older, younger)
    land_support, sched = pgh.event_reconstructed_land_support(
        a1, age, older_ma=older, younger_ma=younger,
        phase_min=cfg.phase_min, phase_max=cfg.phase_max,
        transition_width_years=cfg.transition_width_years,
    )
    land_support = np.clip(np.asarray(land_support, dtype=float), 0.0, 1.0)
    accessible = land_support > float(cfg.accessibility_floor)
    out = {
        "age_ma": age,
        "older_ma": older,
        "younger_ma": younger,
        "older_index": i0,
        "younger_index": i1,
        "phase": a,
        "land_support": land_support,
        "accessible": accessible,
        "land": accessible,  # compatibility alias for the R2/R2.1 raster runtime
        "plate": _event_plate_code(a1, age, i0, i1, older, younger, sched),
        "topology": f"EVENT_RECONSTRUCTED_{older:g}_{younger:g}Ma",
        "paleogeographic_history_provider": "D3_2C_PLATE_CORE_CONSTRAINED_ENDPOINT_EVENT_RECONSTRUCTION_MULTI_BRACKET_ADAPTER",
        "paleogeographic_event_schedule_status": pgh.STATUS,
        "paleogeographic_event_diagnostics": dict(sched["diagnostics"]),
    }
    # Match the already-validated D3.1/D3.2C substrate semantics: continuous
    # physical/resource/reference fields are interpolated between A1 endpoints;
    # fractional land support enters habitat/resource accessibility separately.
    for key in CONTINUOUS_KEYS:
        arr = _lerp(a1, key, i0, i1, a)
        out[key] = np.maximum(arr, 0.0) if "forage" in key else np.asarray(arr, dtype=float)

    for src, name in REFERENCE_KEYS:
        out[name] = np.maximum(_lerp(a1, src, i0, i1, a), 0.0)
    return out


def connectivity_permeability(land_support: np.ndarray, cfg: BarrierHistoryConfig = BarrierHistoryConfig()) -> np.ndarray:
    x = (np.asarray(land_support, dtype=float) - float(cfg.connectivity_land_support_threshold)) / max(float(cfg.connectivity_softness), 1e-12)
    p = 1.0 / (1.0 + np.exp(-x))
    p[np.asarray(land_support) <= 1e-9] = 0.0
    return p


def effective_barrier_connectivity(habitat: np.ndarray, land_support: np.ndarray,
                                   cfg: BarrierHistoryConfig = BarrierHistoryConfig()) -> np.ndarray:
    p = connectivity_permeability(land_support, cfg)
    h = np.clip(np.asarray(habitat, dtype=float), 0.0, 1.0)
    return p[None, :, :] * np.power(h, max(float(cfg.habitat_connectivity_power), 0.0))


def build_all_transition_schedules(a1: Any, cfg: BarrierHistoryConfig = BarrierHistoryConfig()) -> dict:
    validate_a1(a1)
    ages = np.asarray(a1["age_ma"], dtype=float)
    brackets = []
    events = []
    for older, younger in zip(ages[:-1], ages[1:]):
        sched = pgh.build_transition_schedule(a1, float(older), float(younger), cfg.phase_min, cfg.phase_max)
        row = {"older_ma": float(older), "younger_ma": float(younger), **dict(sched["diagnostics"])}
        brackets.append(row)
        for e in sched["event_catalog"]:
            ee = dict(e)
            ee["bracket_older_ma"] = float(older)
            ee["bracket_younger_ma"] = float(younger)
            events.append(ee)
    return {
        "stage": R3_PROVIDER_STAGE_ID,
        "status": R3_PROVIDER_STATUS,
        "config": asdict(cfg),
        "brackets": brackets,
        "events": events,
        "summary": {
            "bracket_count": len(brackets),
            "event_cluster_count": len(events),
            "transition_cells_counted_across_brackets": int(sum(x["drowning_cells"] + x["emerging_cells"] for x in brackets)),
        },
    }
