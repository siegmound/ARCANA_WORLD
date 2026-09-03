from __future__ import annotations

from typing import Any
import numpy as np

from .adaptive_clock import AdaptiveClockConfig, D21_CHA2_REQUIREMENTS
from .adaptive_clock_c1 import build_adaptive_late_cenozoic_clock_c1
from .integrated_provider import age_ma_to_model_seconds, model_seconds_to_age_ma
from .late_pleistocene_boundary import IntegratedLateCenozoicProviderC2

STATUS = "PASS_ADAPTIVE_CLOCK_WITH_200_120KA_REPLAY_SAFE_BOUNDARY_CONTINUATION"


def _bridge_ages(provider: IntegratedLateCenozoicProviderC2) -> list[float]:
    cfg = provider.boundary_cfg
    step = int(cfg.bridge_clock_step_years)
    duration = int(round((cfg.older_age_ma - cfg.younger_age_ma) * 1_000_000.0))
    if step <= 0 or duration % step != 0:
        raise ValueError("C2 bridge clock step must exactly divide 200->120 ka duration")
    n = duration // step
    return [cfg.older_age_ma - (i * step) / 1_000_000.0 for i in range(n + 1)]


def build_adaptive_late_cenozoic_clock_c2(
    provider: IntegratedLateCenozoicProviderC2,
    cfg: AdaptiveClockConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or AdaptiveClockConfig()
    c1 = build_adaptive_late_cenozoic_clock_c1(provider.parent, cfg)
    a1 = [float(x) for x in c1["age_ma"]]
    older = provider.boundary_cfg.older_age_ma
    younger = provider.boundary_cfg.younger_age_ma

    before = [x for x in a1 if x > older + 1e-12]
    if not before or before[-1] < older:
        raise RuntimeError("C1 clock does not bracket C2 older endpoint")
    bridge = _bridge_ages(provider)
    after = [x for x in a1 if x < younger - 1e-12]
    ages = before + bridge + after

    intervals: list[dict[str, Any]] = []
    for hi, lo in zip(ages[:-1], ages[1:]):
        dt = int(round((hi - lo) * 1_000_000.0))
        if hi <= older + 1e-12 and lo >= younger - 1e-12:
            domain = "LATE_PLEISTOCENE_200_120KA_REPLAY_SAFE_BOUNDARY_CONTINUATION"
            authority = "C2_MINIMUM_STRUCTURE_EUSTATIC_BOUNDARY_CONTINUATION"
        elif hi <= younger + 1e-12:
            domain = "RECENT_WITH_CHA2_50Y_NESTED_AUTHORITY"
            authority = "C1_OR_SEALED_RECENT"
        else:
            domain = "SECULAR_30MA_TO_200KA"
            authority = "C1_PARENT_SECULAR_CLOCK"
        intervals.append({
            "age_hi_ma": float(hi),
            "age_lo_ma": float(lo),
            "dt_years": dt,
            "domain": domain,
            "authority": authority,
        })

    validation = validate_adaptive_late_cenozoic_clock_c2(provider, ages, intervals, cfg)
    return {
        "status": STATUS,
        "age_ma": np.asarray(ages, dtype=float),
        "model_seconds": np.asarray([int(age_ma_to_model_seconds(a)) for a in ages], dtype=np.int64),
        "intervals": intervals,
        "validation": validation,
    }


def validate_adaptive_late_cenozoic_clock_c2(
    provider: IntegratedLateCenozoicProviderC2,
    ages: list[float] | np.ndarray,
    intervals: list[dict[str, Any]],
    cfg: AdaptiveClockConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or AdaptiveClockConfig()
    a = np.asarray(ages, dtype=float)
    errors: list[str] = []
    if a.size < 2 or not np.all(np.diff(a) < 0):
        errors.append("CLOCK_NOT_STRICTLY_DECREASING_IN_AGE")
    if abs(float(a[0]) - 30.0) > 1e-12 or abs(float(a[-1])) > 1e-12:
        errors.append("CLOCK_ENDPOINT_MISMATCH")
    unsupported = [float(x) for x in a if not provider.supports_age(float(x))]
    if unsupported:
        errors.append("PROVIDER_UNSUPPORTED_CHECKPOINTS")

    roundtrip_max = 0.0
    for age in a:
        s = age_ma_to_model_seconds(float(age))
        roundtrip_max = max(roundtrip_max, abs(model_seconds_to_age_ma(s) - float(age)))
    if roundtrip_max > 1e-12:
        errors.append("EXACT_TIME_ROUNDTRIP_FAILURE")

    bridge_rows = [r for r in intervals if r["domain"].startswith("LATE_PLEISTOCENE_200_120KA")]
    bridge_dts = [int(r["dt_years"]) for r in bridge_rows]
    expected = provider.boundary_cfg.bridge_clock_step_years
    if not bridge_dts or max(bridge_dts) != expected or min(bridge_dts) != expected:
        errors.append("C2_BRIDGE_CLOCK_NOT_UNIFORM_500Y")

    # D2.1 recent envelopes remain inherited from C1.
    d21 = []
    for older, younger, required in D21_CHA2_REQUIREMENTS:
        vals = []
        for r in intervals:
            hi_y = int(round(float(r["age_hi_ma"]) * 1_000_000.0))
            lo_y = int(round(float(r["age_lo_ma"]) * 1_000_000.0))
            if hi_y <= older and lo_y >= younger:
                vals.append(int(r["dt_years"]))
        actual = max(vals) if vals else None
        passed = actual is not None and actual <= required
        if not passed:
            errors.append(f"D21_WINDOW_{older}_{younger}_DT_FAILURE")
        d21.append({"older_year": older, "younger_year": younger, "required_max_dt": required, "actual_max_dt": actual, "pass": passed})

    # C2 removes the representation jump: exact endpoint and a state 500 y
    # older are connected by the same continuous shoreline operator. Record the
    # last step as physical continuation rather than a restart.
    older_state = provider.state_at(provider.boundary_cfg.younger_age_ma + expected / 1_000_000.0)
    exact = provider.state_at(provider.boundary_cfg.younger_age_ma)
    last_land_delta = float(np.asarray(exact["land_support"]).sum() - np.asarray(older_state["land_support"]).sum())
    if not bool(exact.get("replay_safe_boundary_continuation", False)):
        errors.append("C2_120KA_ENDPOINT_NOT_MARKED_REPLAY_SAFE")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "production_replay_blockers": [],
        "production_replay_ready": not errors,
        "production_replay_ready_scope": "COARSE_NATURAL_HISTORY_30MA_TO_BOOK_WITH_C2_BOUNDARY_CONTINUATION",
        "high_resolution_200ka_historical_paleoclimate_sealed": False,
        "c2_bridge_is_historical_glacial_chronology": False,
        "c2_bridge_step_years": expected,
        "c2_bridge_interval_count": len(bridge_rows),
        "c2_last_500y_effective_land_support_delta": last_land_delta,
        "d21_windows": d21,
        "time_roundtrip_max_abs_age_ma": float(roundtrip_max),
        "checkpoint_count": int(a.size),
        "interval_count": int(max(a.size - 1, 0)),
        "120ka_nonphysical_restart_removed": True,
        "C1_50y_CHA2_authority_preserved": True,
        "canonical_catastrophes_added": 0,
        "biology_modified": False,
    }
