from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence
import math

import numpy as np

from .cha2_nested_50y import (
    CHA2Nested50YRecentProvider,
    CORE_OLDER_YEAR,
    CORE_YOUNGER_YEAR,
    NESTED_STEP_YEARS,
)

STAGE = "v0.6D1-R3.20"
SCHEMA = "ARCANA_R320_CHA2_YD_CLASS_MAGNITUDE_AND_HYDROLOGICAL_HAZARD_V1"
AUDIT_REVISION = "R1_METRIC_AND_PARENT_SCHEMA_REPAIR"
AUTHORITY = (
    "DERIVED_DIAGNOSTIC_LAYER_OVER_SEALED_CHA2_C1; "
    "CHA2_NESTED_50Y_AUTHORITY_AND_R319_H0_STATE_REMAIN_UNMODIFIED"
)


@dataclass(frozen=True)
class YoungerDryasClassEnvelope:
    """Broad class gate, not a target curve.

    R1 distinguishes three different quantities that were conflated in the
    first audit draft:

    * the regional/high-latitude temperature response used for the YD-class
      magnitude gate;
    * the low-order scalar ``global_temperature_anomaly_c`` used by the sealed
      climate/carbon/ice state equations, retained as a diagnostic but not
      interpreted as an area-weighted observed global-mean temperature; and
    * event exit from the strong-overturning-suppression regime, distinct from
      near-complete (90%) circulation recovery.

    No bound is fitted to human, cultural, settlement, myth, religion or
    extinction outcomes.
    """

    audit_older_year: int = -15_000
    audit_younger_year: int = -11_000
    baseline_older_year: int = -14_700
    baseline_younger_year: int = -14_000
    principal_peak_older_year: int = -13_800
    principal_peak_younger_year: int = -12_300
    min_freshwater_peak_sv: float = 0.08
    max_freshwater_peak_sv: float = 0.30
    max_overturning_fraction_of_baseline: float = 0.65
    min_overturning_fraction_of_baseline: float = 0.20
    strong_suppression_fraction_of_baseline: float = 0.80
    min_strong_suppression_years: float = 500.0
    max_strong_suppression_years: float = 1_900.0
    # Event termination is the exit from the same <80% regime used to define
    # strong suppression.  A 90% return is tracked separately as a diagnostic
    # of near-complete circulation recovery and is not a YD-class hard gate.
    event_exit_fraction_of_baseline: float = 0.80
    event_exit_older_year: int = -12_300
    event_exit_younger_year: int = -11_000
    full_recovery_fraction_of_baseline: float = 0.90
    full_recovery_diagnostic_younger_year: int = -9_000
    min_northern_local_cooling_c: float = 2.0
    max_northern_local_cooling_c: float = 12.0
    global_state_cooling_is_diagnostic_only: bool = True


@dataclass(frozen=True)
class HydrologicalHazardConfig:
    """Normalization scales are diagnostic ranking scales, not new physics."""

    step_years: int = NESTED_STEP_YEARS
    positive_floor: float = 1.0e-9
    pluvial_relative_change_scale: float = 0.20
    wetland_relative_change_scale: float = 0.20
    coastal_support_loss_scale: float = 0.10
    severe_candidate_threshold: float = 0.65
    northern_meltwater_latitude_deg: float = 45.0
    human_population_used: bool = False
    settlement_target_used: bool = False
    flood_myth_target_used: bool = False
    religion_target_used: bool = False
    impact_origin_required: bool = False

    def __post_init__(self) -> None:
        if self.step_years != 50:
            raise ValueError("R3.20 CHA-2 hazard cadence is fixed to the existing 50-y C1 core")
        if any((self.human_population_used, self.settlement_target_used,
                self.flood_myth_target_used, self.religion_target_used,
                self.impact_origin_required)):
            raise ValueError("R3.20 may not calibrate CHA-2 to human/cultural outcomes or require an impact origin")


def _weighted_mean(field: np.ndarray, weights: np.ndarray) -> float:
    x = np.asarray(field, dtype=float)
    w = np.asarray(weights, dtype=float)
    good = np.isfinite(x) & np.isfinite(w) & (w > 0)
    if not np.any(good):
        return float("nan")
    return float(np.sum(x[good] * w[good]) / np.sum(w[good]))


def _north_mask_from_a1(a1: Mapping[str, Any], shape: tuple[int, int]) -> np.ndarray:
    lat = np.asarray(a1.get("lat"), dtype=float)
    if lat.ndim != 1 or lat.size != shape[0]:
        raise ValueError("A1 latitude vector required for R3.20 northern cooling audit")
    return np.broadcast_to((lat[:, None] >= 45.0), shape)


def _sample_years(env: YoungerDryasClassEnvelope) -> list[int]:
    return list(range(env.audit_older_year, env.audit_younger_year + 1, 50))


def _event_duration_years(mask: np.ndarray, step_years: float) -> float:
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return 0.0
    # Legacy helper retained for callers/tests; the YD classifier below uses
    # the contiguous strong-suppression episode containing the AMOC minimum.
    return float((idx[-1] - idx[0] + 1) * step_years)


def _contiguous_event_span(
    mask: np.ndarray, center_index: int, step_years: float
) -> tuple[float, int | None, int | None]:
    m = np.asarray(mask, dtype=bool)
    c = int(center_index)
    if c < 0 or c >= m.size or not m[c]:
        return 0.0, None, None
    left = c
    right = c
    while left > 0 and m[left - 1]:
        left -= 1
    while right + 1 < m.size and m[right + 1]:
        right += 1
    return float((right - left + 1) * step_years), left, right


def audit_younger_dryas_class_magnitude(
    provider: CHA2Nested50YRecentProvider,
    a1: Mapping[str, Any],
    env: YoungerDryasClassEnvelope | None = None,
) -> dict[str, Any]:
    """Classify the sealed CHA-2 response without re-tuning it.

    R1 repair notes:
    1. ``global_temperature_anomaly_c`` is retained as a low-order climate-state
       diagnostic.  It is not treated as a directly comparable area-weighted
       global-mean surface-temperature reconstruction.
    2. YD-like event exit is defined by leaving the same strong-suppression
       regime (<80% baseline overturning) used to measure event duration.
       A later 90% recovery is reported diagnostically on exact sealed 100-y
       anchors after the 15-11 ka nested core when needed.
    """
    env = env or YoungerDryasClassEnvelope()
    years = _sample_years(env)
    states = [provider.state_at_year(y) for y in years]
    freshwater = np.asarray([float(s["freshwater_forcing_sv"]) for s in states], dtype=float)
    overturning = np.asarray([float(s["overturning_strength"]) for s in states], dtype=float)
    global_temp = np.asarray([float(s["global_temperature_anomaly_c"]) for s in states], dtype=float)

    baseline_mask = np.asarray([
        env.baseline_older_year <= y <= env.baseline_younger_year for y in years
    ], dtype=bool)
    if not np.any(baseline_mask):
        raise RuntimeError("R3.20 baseline window not represented on 50-y grid")
    baseline_m = float(np.median(overturning[baseline_mask]))
    baseline_gt = float(np.mean(global_temp[baseline_mask]))

    peak_i = int(np.argmax(freshwater))
    min_m_i = int(np.argmin(overturning))
    global_cooling = baseline_gt - global_temp
    min_gt_i = int(np.argmax(global_cooling))
    strong = overturning < env.strong_suppression_fraction_of_baseline * baseline_m
    strong_years, strong_first_i, strong_last_i = _contiguous_event_span(strong, min_m_i, 50.0)

    event_exit_i: int | None = None
    event_exit_threshold = env.event_exit_fraction_of_baseline * baseline_m
    if strong_last_i is not None and strong_last_i + 1 < len(years):
        candidate = strong_last_i + 1
        if overturning[candidate] >= event_exit_threshold:
            event_exit_i = candidate

    # Near-complete circulation recovery is deliberately diagnostic.  Search
    # the 50-y core first, then continue only on exact sealed 100-y anchors.
    full_recovery_threshold = env.full_recovery_fraction_of_baseline * baseline_m
    full_recovery_year: int | None = None
    for i in range(min_m_i + 1, len(years)):
        if overturning[i] >= full_recovery_threshold:
            full_recovery_year = int(years[i])
            break
    if full_recovery_year is None:
        for y in range(env.audit_younger_year + 100, env.full_recovery_diagnostic_younger_year + 1, 100):
            if not provider.supports_year(y):
                continue
            if float(provider.state_at_year(y)["overturning_strength"]) >= full_recovery_threshold:
                full_recovery_year = int(y)
                break

    # Baseline northern temperature field is a support-weighted spatial state
    # from the sealed provider.  Severity is a robust local 5th-percentile
    # cooling among >=45N active cells, never population-weighted.
    temp_stack = np.stack([np.asarray(s["temperature_c"], dtype=float) for s in states], axis=0)
    support_stack = np.stack([np.asarray(s["land_support"], dtype=float) for s in states], axis=0)
    base_temp = np.mean(temp_stack[baseline_mask], axis=0)
    north = _north_mask_from_a1(a1, base_temp.shape)
    local_delta = temp_stack - base_temp[None, :, :]
    northern_local_cooling = []
    northern_cooling_ge2_fraction = []
    for i in range(len(years)):
        mask = north & (support_stack[i] > 0.05) & np.isfinite(local_delta[i])
        if np.any(mask):
            vals = local_delta[i][mask]
            northern_local_cooling.append(float(-np.percentile(vals, 5.0)))
            northern_cooling_ge2_fraction.append(float(np.mean(vals <= -2.0)))
        else:
            northern_local_cooling.append(float("nan"))
            northern_cooling_ge2_fraction.append(float("nan"))
    northern_local_cooling = np.asarray(northern_local_cooling, dtype=float)
    northern_cooling_ge2_fraction = np.asarray(northern_cooling_ge2_fraction, dtype=float)
    north_i = int(np.nanargmax(northern_local_cooling))

    max_global_state_cooling = float(np.max(global_cooling))
    max_north_cooling = float(northern_local_cooling[north_i])
    min_m_frac = float(overturning[min_m_i] / baseline_m)

    checks: dict[str, bool] = {
        "freshwater_peak_magnitude": bool(env.min_freshwater_peak_sv <= freshwater[peak_i] <= env.max_freshwater_peak_sv),
        "freshwater_peak_timing": bool(env.principal_peak_older_year <= years[peak_i] <= env.principal_peak_younger_year),
        "overturning_suppression_magnitude": bool(env.min_overturning_fraction_of_baseline <= min_m_frac <= env.max_overturning_fraction_of_baseline),
        "overturning_minimum_timing": bool(env.principal_peak_older_year <= years[min_m_i] <= env.principal_peak_younger_year),
        "suppression_duration": bool(env.min_strong_suppression_years <= strong_years <= env.max_strong_suppression_years),
        "northern_cooling_magnitude": bool(env.min_northern_local_cooling_c <= max_north_cooling <= env.max_northern_local_cooling_c),
        "northern_cooling_timing": bool(env.principal_peak_older_year <= years[north_i] <= env.principal_peak_younger_year),
        "event_exit_detected": event_exit_i is not None,
        "global_state_cooling_direction": bool(max_global_state_cooling > 0.0),
    }
    event_exit_timing_diagnostic = bool(
        event_exit_i is not None
        and env.event_exit_older_year <= years[event_exit_i] <= env.event_exit_younger_year
    )

    return {
        "schema": "ARCANA_R320_YD_CLASS_MAGNITUDE_AUDIT_V2",
        "audit_revision": AUDIT_REVISION,
        "classification": "YOUNGER_DRYAS_CLASS" if all(checks.values()) else "OUTSIDE_YOUNGER_DRYAS_CLASS_ENVELOPE",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "reference_envelope": asdict(env),
        "metrics": {
            "baseline_overturning_strength": baseline_m,
            "freshwater_peak_sv": float(freshwater[peak_i]),
            "freshwater_peak_year_before_book": int(years[peak_i]),
            "minimum_overturning_strength": float(overturning[min_m_i]),
            "minimum_overturning_fraction_of_baseline": min_m_frac,
            "minimum_overturning_year_before_book": int(years[min_m_i]),
            "strong_suppression_duration_years": strong_years,
            "strong_suppression_start_year_before_book": None if strong_first_i is None else int(years[strong_first_i]),
            "strong_suppression_end_year_before_book": None if strong_last_i is None else int(years[strong_last_i]),
            "event_exit_fraction_of_baseline": float(env.event_exit_fraction_of_baseline),
            "event_exit_year_before_book": None if event_exit_i is None else int(years[event_exit_i]),
            "event_exit_timing_within_reference_window_diagnostic": event_exit_timing_diagnostic,
            "full_recovery_fraction_of_baseline_diagnostic": float(env.full_recovery_fraction_of_baseline),
            "full_recovery_year_before_book_diagnostic": full_recovery_year,
            "full_recovery_detected_by_diagnostic_horizon": full_recovery_year is not None,
            "maximum_northern_local_cooling_c": max_north_cooling,
            "maximum_northern_local_cooling_year_before_book": int(years[north_i]),
            "northern_active_land_fraction_cooling_at_least_2c_at_peak": float(northern_cooling_ge2_fraction[north_i]),
            "maximum_global_state_cooling_c_diagnostic": max_global_state_cooling,
            "maximum_global_state_cooling_year_before_book_diagnostic": int(years[min_gt_i]),
            # Backward-readable aliases: explicitly diagnostic in V2.
            "maximum_global_cooling_c": max_global_state_cooling,
            "maximum_global_cooling_year_before_book": int(years[min_gt_i]),
            "recovery_year_before_book": None if event_exit_i is None else int(years[event_exit_i]),
        },
        "governance": {
            "impact_origin_required": False,
            "human_population_used": False,
            "settlement_target_used": False,
            "flood_myth_target_used": False,
            "religion_target_used": False,
            "biology_modified": False,
            "cha2_c1_modified": False,
            "global_temperature_scalar_magnitude_is_hard_gate": False,
            "global_temperature_scalar_role": "LOW_ORDER_CLIMATE_STATE_DIAGNOSTIC_NOT_AREA_WEIGHTED_GLOBAL_MEAN_RECONSTRUCTION",
            "full_90pct_overturning_recovery_is_hard_gate": False,
            "event_exit_uses_same_80pct_threshold_as_strong_suppression": True,
        },
    }


def hydrological_hazard_snapshot(
    provider: CHA2Nested50YRecentProvider,
    a1: Mapping[str, Any],
    year_before_book: int,
    cfg: HydrologicalHazardConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or HydrologicalHazardConfig()
    y = int(year_before_book)
    if y <= CORE_OLDER_YEAR or y > CORE_YOUNGER_YEAR:
        raise ValueError("R3.20 hazard snapshots are defined for (-15 ka, -11 ka] on the C1 50-y grid")
    if y % cfg.step_years != 0:
        raise ValueError("R3.20 hazard snapshot must lie on the existing 50-y C1 grid")
    older = y - cfg.step_years
    prev = provider.state_at_year(older)
    cur = provider.state_at_year(y)

    ar_prev = np.asarray(prev["aridity_index"], dtype=float)
    ar_cur = np.asarray(cur["aridity_index"], dtype=float)
    wet_prev = np.asarray(prev["wetland_forage"], dtype=float)
    wet_cur = np.asarray(cur["wetland_forage"], dtype=float)
    land_prev = np.asarray(prev["land_support"], dtype=float)
    land_cur = np.asarray(cur["land_support"], dtype=float)
    total_prev = np.asarray(prev["total_edible_forage"], dtype=float)
    total_cur = np.asarray(cur["total_edible_forage"], dtype=float)

    eps = cfg.positive_floor
    # In the existing biology, lower `aridity_index` maps to stronger drought;
    # therefore a positive relative change is a rapid-moistening signal.
    moisture_rel = (ar_cur - ar_prev) / np.maximum(np.abs(ar_prev), eps)
    wetland_rel = (wet_cur - wet_prev) / np.maximum(np.abs(wet_prev), eps)
    forage_shock = np.abs(total_cur - total_prev) / np.maximum(np.abs(total_prev), eps)
    support_loss = np.maximum(land_prev - land_cur, 0.0)
    support_gain = np.maximum(land_cur - land_prev, 0.0)

    pluvial_component = np.clip(
        0.65 * np.maximum(moisture_rel, 0.0) / cfg.pluvial_relative_change_scale
        + 0.35 * np.maximum(wetland_rel, 0.0) / cfg.wetland_relative_change_scale,
        0.0,
        1.0,
    ) * np.clip(land_cur, 0.0, 1.0)
    coastal_component = np.clip(support_loss / cfg.coastal_support_loss_scale, 0.0, 1.0)
    compound_flood = 1.0 - (1.0 - pluvial_component) * (1.0 - coastal_component)

    drying_component = np.clip(
        np.maximum(-moisture_rel, 0.0) / cfg.pluvial_relative_change_scale,
        0.0,
        1.0,
    ) * np.clip(land_cur, 0.0, 1.0)
    ecosystem_shock = np.clip(forage_shock / 0.25, 0.0, 1.0) * np.clip(land_cur, 0.0, 1.0)
    hydro_disruption = np.maximum.reduce((compound_flood, drying_component, ecosystem_shock))

    lat = np.asarray(a1.get("lat"), dtype=float)
    if lat.ndim != 1 or lat.size != land_cur.shape[0]:
        raise ValueError("A1 latitude vector required for R3.20 hazard layer")
    north_weight = np.broadcast_to(
        np.clip((lat[:, None] - cfg.northern_meltwater_latitude_deg) / 20.0, 0.0, 1.0),
        land_cur.shape,
    )
    freshwater_system_pressure = float(np.clip(float(cur["freshwater_forcing_sv"]) / 0.20, 0.0, 1.5))
    meltwater_system_pressure = freshwater_system_pressure * north_weight * np.clip(land_cur, 0.0, 1.0)

    severe = compound_flood >= cfg.severe_candidate_threshold
    active_land = land_cur > 0.05
    severe_fraction = float(np.count_nonzero(severe & active_land) / max(np.count_nonzero(active_land), 1))

    return {
        "schema": "ARCANA_R320_CHA2_HYDROLOGICAL_HAZARD_SNAPSHOT_V1",
        "authority": AUTHORITY,
        "year_before_book": y,
        "age_ma": abs(y) / 1_000_000.0,
        "dt_years": float(cfg.step_years),
        "pluvial_flood_potential_index": pluvial_component,
        "coastal_inundation_potential_index": coastal_component,
        "compound_flood_hazard_index": compound_flood,
        "drying_hazard_index": drying_component,
        "ecosystem_hydrological_shock_index": ecosystem_shock,
        "hydrological_disruption_index": hydro_disruption,
        "meltwater_system_pressure_index": meltwater_system_pressure,
        "raw_moisture_relative_change": moisture_rel,
        "raw_wetland_relative_change": wetland_rel,
        "raw_support_loss_fraction": support_loss,
        "raw_support_gain_fraction": support_gain,
        "freshwater_forcing_sv": float(cur["freshwater_forcing_sv"]),
        "sea_level_anomaly_m": float(cur["sea_level_anomaly_m"]),
        "overturning_strength": float(cur["overturning_strength"]),
        "severe_flood_candidate_fraction_of_active_land": severe_fraction,
        "human_population_used": False,
        "settlement_target_used": False,
        "flood_myth_target_used": False,
        "religion_target_used": False,
        "impact_origin_required": False,
    }


def build_hazard_timeseries(
    provider: CHA2Nested50YRecentProvider,
    a1: Mapping[str, Any],
    cfg: HydrologicalHazardConfig | None = None,
) -> dict[str, Any]:
    cfg = cfg or HydrologicalHazardConfig()
    years = list(range(CORE_OLDER_YEAR + cfg.step_years, CORE_YOUNGER_YEAR + 1, cfg.step_years))
    snapshots = [hydrological_hazard_snapshot(provider, a1, y, cfg) for y in years]
    fields = (
        "pluvial_flood_potential_index",
        "coastal_inundation_potential_index",
        "compound_flood_hazard_index",
        "drying_hazard_index",
        "ecosystem_hydrological_shock_index",
        "hydrological_disruption_index",
        "meltwater_system_pressure_index",
        "raw_support_loss_fraction",
    )
    arrays = {k: np.stack([np.asarray(s[k], dtype=np.float32) for s in snapshots], axis=0) for k in fields}
    severe_fraction = np.asarray([s["severe_flood_candidate_fraction_of_active_land"] for s in snapshots], dtype=float)
    peak_i = int(np.argmax(severe_fraction))
    return {
        "schema": "ARCANA_R320_CHA2_HYDROLOGICAL_HAZARD_TIMESERIES_V1",
        "authority": AUTHORITY,
        "years_before_book": np.asarray(years, dtype=np.int32),
        "fields": arrays,
        "severe_flood_candidate_fraction": severe_fraction,
        "peak_severe_fraction": float(severe_fraction[peak_i]),
        "peak_severe_fraction_year_before_book": int(years[peak_i]),
        "governance": {
            "hazard_indices_are_diagnostic_rankings_not_flood_depths": True,
            "human_population_used": False,
            "settlement_target_used": False,
            "flood_myth_target_used": False,
            "religion_target_used": False,
            "biology_modified": False,
            "cha2_c1_modified": False,
        },
    }
