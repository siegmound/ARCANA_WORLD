from __future__ import annotations

from typing import Any
import numpy as np

from .adaptive_clock import (
    AdaptiveClockConfig,
    D21_CHA2_REQUIREMENTS,
    RECENT_MANDATORY_YEARS_BEFORE_BOOK,
    _build_secular_ages,
    _next_mandatory_recent_boundary,
)
from .cha2_nested_50y import IntegratedLateCenozoicProviderC1
from .integrated_provider import age_ma_to_model_seconds, model_seconds_to_age_ma

STATUS = "PASS_ADAPTIVE_CLOCK_WITH_AUTHORIZED_CHA2_50Y_NESTED_STATES_CANDIDATE"


def recent_max_dt_years_c1(year_before_book: int, cfg: AdaptiveClockConfig | None = None) -> int:
    cfg = cfg or AdaptiveClockConfig()
    ybp = abs(int(year_before_book))
    if ybp > 25_000:
        return cfg.recent_background_max_step_years
    if ybp > 15_000:
        return 200
    if ybp > 11_000:
        return 50
    if ybp > 8_000:
        return 100
    return 500


def _build_recent_ages_c1(cfg: AdaptiveClockConfig) -> tuple[list[float], list[dict[str, Any]]]:
    years = [-120_000]
    diag: list[dict[str, Any]] = []
    current = -120_000
    while current < 0:
        max_dt = recent_max_dt_years_c1(current, cfg)
        boundary = _next_mandatory_recent_boundary(current)
        to_boundary = boundary - current
        dt = min(max_dt, to_boundary)
        if dt <= 0:
            raise RuntimeError("C1 adaptive recent clock could not advance")
        nxt = current + dt
        diag.append({
            "year_hi_before_book": int(-current),
            "year_lo_before_book": int(-nxt),
            "dt_years": int(dt),
            "domain": "RECENT_WITH_CHA2_50Y_NESTED_AUTHORITY",
            "checkpoint_authority": (
                "DERIVED_NESTED_50Y" if (abs(nxt) >= 11_000 and abs(nxt) <= 15_000 and nxt % 100 != 0)
                else "SEALED_v0.6.1_EXACT_100Y_OR_COARSER_CHECKPOINT"
            ),
        })
        years.append(nxt)
        current = nxt
    return [abs(y) / 1_000_000.0 for y in years], diag


def build_adaptive_late_cenozoic_clock_c1(
    provider: IntegratedLateCenozoicProviderC1,
    cfg: AdaptiveClockConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or AdaptiveClockConfig()
    secular_ages, secular_diag = _build_secular_ages(provider.base, cfg)
    recent_ages, recent_diag = _build_recent_ages_c1(cfg)
    ages = secular_ages + recent_ages[1:]
    intervals = secular_diag + recent_diag
    validation = validate_adaptive_late_cenozoic_clock_c1(provider, ages, intervals, cfg)
    return {
        "status": STATUS,
        "age_ma": np.asarray(ages, dtype=float),
        "model_seconds": np.asarray([int(age_ma_to_model_seconds(a)) for a in ages], dtype=np.int64),
        "intervals": intervals,
        "validation": validation,
    }


def validate_adaptive_late_cenozoic_clock_c1(
    provider: IntegratedLateCenozoicProviderC1,
    ages: list[float] | np.ndarray,
    intervals: list[dict[str, Any]],
    cfg: AdaptiveClockConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or AdaptiveClockConfig()
    a = np.asarray(ages, dtype=float)
    errors: list[str] = []
    blockers: list[str] = []
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

    # D2.1 envelopes.
    window_metrics = []
    for older, younger, required in D21_CHA2_REQUIREMENTS:
        dts = []
        for row in intervals:
            if not row.get("domain", "").startswith("RECENT") and row.get("domain") != "SEALED_RECENT_120KA_TO_BOOK":
                continue
            hi = int(row["year_hi_before_book"])
            lo = int(row["year_lo_before_book"])
            if hi <= older and lo >= younger:
                dts.append(int(row["dt_years"]))
        actual = max(dts) if dts else None
        passed = actual is not None and actual <= required
        if not passed:
            errors.append(f"D21_WINDOW_{older}_{younger}_DT_FAILURE")
        window_metrics.append({"older_year": older, "younger_year": younger, "required_max_dt": required, "actual_max_dt": actual, "pass": passed})

    # C's -120 ka representation restart remains a production replay blocker.
    older = provider.state_at(provider.cfg.splice_age_ma + 0.0001)
    exact = provider.state_at(provider.cfg.splice_age_ma)
    restart_land_jump = float(np.asarray(exact["land_support"]).sum() - np.asarray(older["land_support"]).sum())
    if not np.array_equal(np.asarray(older["land_support"]), np.asarray(exact["land_support"])):
        blockers.append("120KA_EFFECTIVE_LAND_RESTART_REQUIRES_NONPHYSICAL_REBASE_OR_PRE120KA_EUSTATIC_HISTORY")

    core_intervals = [
        row for row in intervals
        if row.get("domain") == "RECENT_WITH_CHA2_50Y_NESTED_AUTHORITY"
        and row["year_hi_before_book"] <= 15_000 and row["year_lo_before_book"] >= 11_000
    ]
    max_core_dt = max([int(x["dt_years"]) for x in core_intervals], default=None)
    if max_core_dt != 50:
        errors.append("CHA2_CORE_NOT_RESOLVED_AT_50Y")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "production_replay_blockers": blockers,
        "production_replay_ready": not errors and not blockers,
        "d21_windows": window_metrics,
        "cha2_core_max_dt_years": max_core_dt,
        "time_roundtrip_max_abs_age_ma": float(roundtrip_max),
        "checkpoint_count": int(a.size),
        "interval_count": int(max(a.size - 1, 0)),
        "120ka_effective_land_restart_jump": restart_land_jump,
        "C1_closes_C_clock_blocker": max_core_dt == 50,
        "C1_does_not_close_120ka_restart_blocker": True,
    }
