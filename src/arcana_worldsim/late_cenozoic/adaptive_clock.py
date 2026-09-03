from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .integrated_provider import (
    IntegratedLateCenozoicProvider,
    age_ma_to_model_seconds,
    model_seconds_to_age_ma,
)

STATUS = "PASS_ADAPTIVE_CLOCK_STRUCTURE_WITH_EXPLICIT_PRODUCTION_REPLAY_BLOCKERS"
D21_CHA2_REQUIREMENTS = (
    (25_000, 15_000, 250),
    (15_000, 11_000, 50),
    (11_000, 8_000, 100),
    (8_000, 0, 500),
)
RECENT_MANDATORY_YEARS_BEFORE_BOOK = (
    120_000,
    25_000,
    15_000,
    14_000,
    12_900,
    12_000,
    11_000,
    8_000,
    0,
)


@dataclass(frozen=True)
class AdaptiveClockConfig:
    max_geological_step_years: int = 2_000_000
    min_secular_step_years: int = 25_000
    secular_activity_threshold: float = 1.0
    recent_background_max_step_years: int = 5_000
    sealed_recent_checkpoint_years: int = 100


def _weighted_mean(field: np.ndarray, support: np.ndarray) -> float:
    w = np.maximum(np.asarray(support, dtype=float), 0.0)
    if float(w.sum()) <= 0:
        return float(np.mean(field))
    return float(np.average(np.asarray(field, dtype=float), weights=w))


def environmental_activity_score(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Dimensionless local activity score used only to choose coupling dt.

    It is a scheduler diagnostic, not a physical law or new state authority.
    Scales are conservative resolution controls chosen so a single accepted
    secular interval does not hide a large environmental change.
    """
    ta = _weighted_mean(a["temperature_c"], a["land_support"])
    tb = _weighted_mean(b["temperature_c"], b["land_support"])
    fa = _weighted_mean(a["total_edible_forage"], a["land_support"])
    fb = _weighted_mean(b["total_edible_forage"], b["land_support"])
    ca = max(float(a["atmospheric_co2_ppm"]), 1e-12)
    cb = max(float(b["atmospheric_co2_ppm"]), 1e-12)
    la = np.asarray(a["land_support"], dtype=float)
    lb = np.asarray(b["land_support"], dtype=float)
    return float(max(
        abs(tb - ta) / 0.50,
        abs(np.log(cb / ca)) / 0.05,
        abs(fb - fa) / max(0.05 * max(abs(fa), abs(fb), 1e-8), 1e-8),
        float(np.mean(np.abs(lb - la))) / 0.01,
    ))


def _next_mandatory_recent_boundary(year_before_book: int) -> int:
    # Input is negative or zero. Return the next larger (closer-to-book) signed year.
    signed = tuple(-int(x) for x in RECENT_MANDATORY_YEARS_BEFORE_BOOK)
    candidates = [y for y in signed if y > year_before_book]
    return min(candidates) if candidates else 0


def recent_max_dt_years(year_before_book: int, cfg: AdaptiveClockConfig | None = None) -> int:
    cfg = cfg or AdaptiveClockConfig()
    ybp = abs(int(year_before_book))
    if ybp > 25_000:
        return cfg.recent_background_max_step_years
    if ybp > 15_000:
        return 200  # largest exact 100-y multiple <= D2.1 250-y envelope
    if ybp > 11_000:
        # D2.1 asks <=50 y, but sealed v0.6.1 has exact states only each 100 y.
        return cfg.sealed_recent_checkpoint_years
    if ybp > 8_000:
        return 100
    return 500


def _build_secular_ages(provider: IntegratedLateCenozoicProvider,
                         cfg: AdaptiveClockConfig) -> tuple[list[float], list[dict[str, Any]]]:
    ages = [30.0]
    interval_diag: list[dict[str, Any]] = []
    candidates = [2_000_000, 1_000_000, 500_000, 250_000, 100_000, 50_000, 25_000]
    current = 30.0
    splice = provider.cfg.splice_age_ma
    while current > splice + 1e-12:
        remaining_years = int(round((current - splice) * 1_000_000.0))
        chosen = min(cfg.min_secular_step_years, remaining_years)
        chosen_score = None
        current_state = provider.state_at(current)
        for dt in candidates:
            if dt > cfg.max_geological_step_years or dt > remaining_years:
                continue
            target = current - dt / 1_000_000.0
            trial = provider.state_at(target) if target > splice + 1e-12 else None
            # Exact 120 ka is a governed restart boundary. We do not use the
            # eustatic restart jump as if it were secular environmental activity.
            if trial is None:
                score = 0.0
            else:
                score = environmental_activity_score(current_state, trial)
            if score <= cfg.secular_activity_threshold or dt == cfg.min_secular_step_years:
                chosen = dt
                chosen_score = score
                break
        if chosen > remaining_years:
            chosen = remaining_years
        nxt = current - chosen / 1_000_000.0
        if nxt < splice:
            nxt = splice
        interval_diag.append({
            "age_hi_ma": float(current),
            "age_lo_ma": float(nxt),
            "dt_years": int(round((current - nxt) * 1_000_000.0)),
            "activity_score": None if chosen_score is None else float(chosen_score),
            "domain": "SECULAR_30MA_TO_120KA",
        })
        ages.append(float(nxt))
        current = float(nxt)
    return ages, interval_diag


def _build_recent_ages(cfg: AdaptiveClockConfig) -> tuple[list[float], list[dict[str, Any]]]:
    # Starts at -120 ka in signed years and walks to 0, always on sealed 100-y checkpoints.
    years = [-120_000]
    diag: list[dict[str, Any]] = []
    current = -120_000
    while current < 0:
        max_dt = recent_max_dt_years(current, cfg)
        boundary = _next_mandatory_recent_boundary(current)
        to_boundary = boundary - current
        dt = min(max_dt, to_boundary)
        # Every requested recent state must remain an exact sealed 100-y checkpoint.
        if dt % cfg.sealed_recent_checkpoint_years != 0:
            # Mandatory boundaries are all on the 100-y grid; this is defensive.
            dt = (dt // cfg.sealed_recent_checkpoint_years) * cfg.sealed_recent_checkpoint_years
        if dt <= 0:
            raise RuntimeError("adaptive recent clock could not advance on sealed checkpoint grid")
        nxt = current + dt
        diag.append({
            "year_hi_before_book": int(-current),
            "year_lo_before_book": int(-nxt),
            "dt_years": int(dt),
            "domain": "SEALED_RECENT_120KA_TO_BOOK",
            "d21_requested_max_dt_years": (
                250 if 15_000 < abs(current) <= 25_000 else
                50 if 11_000 < abs(current) <= 15_000 else
                100 if 8_000 < abs(current) <= 11_000 else
                500 if abs(current) <= 8_000 else None
            ),
        })
        years.append(nxt)
        current = nxt
    return [abs(y) / 1_000_000.0 for y in years], diag


def build_adaptive_late_cenozoic_clock(
    provider: IntegratedLateCenozoicProvider,
    cfg: AdaptiveClockConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or AdaptiveClockConfig()
    secular_ages, secular_diag = _build_secular_ages(provider, cfg)
    recent_ages, recent_diag = _build_recent_ages(cfg)
    ages = secular_ages + recent_ages[1:]
    seconds = [int(age_ma_to_model_seconds(a)) for a in ages]
    intervals = secular_diag + recent_diag
    validation = validate_adaptive_late_cenozoic_clock(provider, ages, intervals, cfg)
    return {
        "status": STATUS,
        "age_ma": np.asarray(ages, dtype=float),
        "model_seconds": np.asarray(seconds, dtype=np.int64),
        "intervals": intervals,
        "validation": validation,
    }


def validate_adaptive_late_cenozoic_clock(
    provider: IntegratedLateCenozoicProvider,
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
    if not np.any(np.isclose(a, 0.12, atol=1e-12, rtol=0)):
        errors.append("MISSING_120KA_RESTART_BOUNDARY")

    unsupported = [float(x) for x in a if not provider.supports_age(float(x))]
    if unsupported:
        errors.append("PROVIDER_UNSUPPORTED_CHECKPOINTS")

    # Exact int64 time roundtrip.
    roundtrip_max = 0.0
    for age in a:
        s = age_ma_to_model_seconds(float(age))
        rt = model_seconds_to_age_ma(s)
        roundtrip_max = max(roundtrip_max, abs(rt - float(age)))
    if roundtrip_max > 1e-12:
        errors.append("EXACT_TIME_ROUNDTRIP_FAILURE")

    # The 120 ka boundary is a governed provider/reconstruction restart. The
    # sealed recent state contains eustatically exposed shelf support that the
    # older secular A1 representation does not materialize. Because no pre-120
    # ka eustatic chronology is claimed, a production biology replay must not
    # interpret this representation jump as an instantaneous physical event.
    restart_older = provider.state_at(provider.cfg.splice_age_ma + 0.0001)
    restart_exact = provider.state_at(provider.cfg.splice_age_ma)
    restart_land_jump = float(
        np.asarray(restart_exact["land_support"], dtype=float).sum()
        - np.asarray(restart_older["land_support"], dtype=float).sum()
    )
    restart_forcing_jump = float(
        np.asarray(restart_exact["total_edible_forage"], dtype=float).sum()
        - np.asarray(restart_older["total_edible_forage"], dtype=float).sum()
    )
    restart_requires_rebase = not np.array_equal(
        np.asarray(restart_older["land_support"], dtype=float),
        np.asarray(restart_exact["land_support"], dtype=float),
    )
    if restart_requires_rebase:
        blockers.append(
            "120KA_EFFECTIVE_LAND_RESTART_REQUIRES_NONPHYSICAL_REBASE_OR_PRE120KA_EUSTATIC_HISTORY"
        )

    # D2.1 forced recent windows. All but the 50-y core can be satisfied by the
    # sealed 100-y checkpoint provider. Record the mismatch as a blocker rather
    # than weakening D2.1 or interpolating v0.6.1.
    recent_dts = []
    window_results = []
    for hi, lo, requested in D21_CHA2_REQUIREMENTS:
        vals = []
        for row in intervals:
            if row.get("domain") != "SEALED_RECENT_120KA_TO_BOOK":
                continue
            start = int(row["year_hi_before_book"])
            if lo < start <= hi:
                vals.append(int(row["dt_years"]))
        actual = max(vals) if vals else None
        ok = actual is not None and actual <= requested
        window_results.append({
            "window_year_before_book": [hi, lo],
            "requested_max_dt_years": requested,
            "actual_max_dt_years": actual,
            "pass": bool(ok),
        })
        if vals:
            recent_dts.extend(vals)
        if not ok:
            code = f"D2_1_CHA2_{hi}_{lo}_MAX_DT_UNSATISFIED"
            if requested < cfg.sealed_recent_checkpoint_years:
                blockers.append(code + "_SEALED_PROVIDER_RESOLUTION_LIMIT")
            else:
                errors.append(code)

    mandatory = [x / 1_000_000.0 for x in RECENT_MANDATORY_YEARS_BEFORE_BOOK]
    missing_mandatory = [x for x in mandatory if not np.any(np.isclose(a, x, atol=1e-12, rtol=0))]
    if missing_mandatory:
        errors.append("MISSING_RECENT_MANDATORY_BOUNDARIES")

    recent_ages = a[a <= 0.12 + 1e-12]
    recent_years = np.rint(recent_ages * 1_000_000.0).astype(np.int64)
    recent_on_grid = bool(np.all(recent_years % cfg.sealed_recent_checkpoint_years == 0))
    if not recent_on_grid:
        errors.append("RECENT_CLOCK_OFF_SEALED_100Y_GRID")

    secular_dts = [int(r["dt_years"]) for r in intervals if r.get("domain") == "SECULAR_30MA_TO_120KA"]
    if secular_dts and max(secular_dts) > cfg.max_geological_step_years:
        errors.append("SECULAR_MAX_DT_EXCEEDED")
    if secular_dts and len(set(secular_dts)) < 2:
        errors.append("SECULAR_CLOCK_NOT_ADAPTIVE")

    return {
        "pass_without_blockers": len(errors) == 0 and len(blockers) == 0,
        "structural_pass": len(errors) == 0,
        "errors": errors,
        "blockers": blockers,
        "checkpoint_count": int(a.size),
        "interval_count": int(a.size - 1),
        "min_dt_years": int(min(int(r["dt_years"]) for r in intervals)),
        "max_dt_years": int(max(int(r["dt_years"]) for r in intervals)),
        "median_dt_years": float(np.median([int(r["dt_years"]) for r in intervals])),
        "secular_unique_dt_years": sorted(set(secular_dts), reverse=True),
        "recent_unique_dt_years": sorted(set(recent_dts), reverse=True),
        "d21_cha2_window_results": window_results,
        "recent_checkpoint_grid_years": int(cfg.sealed_recent_checkpoint_years),
        "recent_all_on_exact_sealed_grid": recent_on_grid,
        "exact_time_roundtrip_max_abs_age_ma": float(roundtrip_max),
        "restart_boundary_120ka_present": bool(np.any(np.isclose(a, 0.12, atol=1e-12, rtol=0))),
        "restart_boundary_is_not_catastrophe": True,
        "restart_effective_land_support_sum_jump_vs_100y_older": float(restart_land_jump),
        "restart_total_forage_sum_jump_vs_100y_older": float(restart_forcing_jump),
        "restart_requires_nonphysical_rebase_or_pre120ka_eustatic_history": bool(restart_requires_rebase),
        "pre_120ka_eustatic_chronology_claimed": False,
        "biology_modified": False,
        "canonical_catastrophes_added": 0,
    }
