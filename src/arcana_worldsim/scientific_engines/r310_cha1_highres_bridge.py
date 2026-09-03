from __future__ import annotations

"""R3.10 — rebased CHA-1 high-resolution event bridge.

This module deliberately distinguishes two authorities:

1. R3.9 supplies the exact rebased World-1 H0 state at 66.0 Ma, event-left.
2. Historical D2.2 supplies CHA-1 *event semantics* and recovered quantitative
   anchors, but its original executable solver bytes are not present in the
   rebased package.  R3.10 therefore does not claim bit-identical D2.2 source
   reuse.  It implements a governed, RAW-anchored event-provider transfer.

The implementation is intentionally fail-closed around the impact boundary:
ordinary 125 kyr biology never crosses 66 Ma; the dedicated bridge moves the
state from 66.0 Ma PRE_IMPACT to 65.5 Ma POST_CHA1_500KY.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math

import numpy as np
from scipy.integrate import cumulative_trapezoid, solve_ivp
from scipy.interpolate import PchipInterpolator

from . import r38_restartable_checkpoint as r38
from .r39_precha1_continuation import (
    PRE_CHA1_AGE_MA,
    PRE_CHA1_SCHEMA,
    load_precha1_checkpoint,
)
from .segregation_potential_lifecycle import ReducedGeneticLifecycleState

STAGE = "v0.6D1-R3.10"
PARENT_STAGE = "v0.6D1-R3.9_SEALED"
SCHEMA = "ARCANA_R310_WORLD1_H0_POST_CHA1_500KY_CHECKPOINT_V1"
SUMMARY_SCHEMA = "ARCANA_R310_CHA1_HIGH_RES_REBASED_EVENT_BRIDGE_V1"
IMPACT_AGE_MA = 66.0
POST_EVENT_YEARS = 500_000.0
POST_EVENT_AGE_MA = 65.5
REPORTING_CHECKPOINTS = 917
CANONICAL_SEED = 917231

# D2.2 recovered aggregate survivor authority.  These are *not* target counts
# for R3.10.  They define transferred guild-level cumulative hazard scale.
D22_GUILD_COUNTS = {
    1: (24, 8),
    2: (16, 1),
    3: (20, 5),
    4: (24, 12),
    5: (24, 3),
    6: (12, 2),
}
D22_GUILD_CUMULATIVE_HAZARD = {
    g: -math.log(surv / initial) for g, (initial, surv) in D22_GUILD_COUNTS.items()
}

# Recovered physical anchors.  Values are from D2.2 RAW / parent evidence.
PHYSICAL_ANCHORS = {
    "impact": {
        "relative_year": 0.0,
        "par_fraction": 0.0030275547453758,
        "temperature_anomaly_c": -16.0,
        "npp_multiplier": 0.0055720068149199,
        "extinction_pressure_index": 0.9812281358795112,
        "atmospheric_co2_ppm": 862.2641509433962,
    },
    "y0p01": {
        "relative_year": 0.01,
        "par_fraction": 0.0031808327064871,
        "temperature_anomaly_c": -15.856592895823772,
        "npp_multiplier": 0.0058289939695832,
        "extinction_pressure_index": 0.981058517281962,
        "atmospheric_co2_ppm": 862.2641332547176,
    },
    "y0p57": {
        "relative_year": 0.57,
        "temperature_anomaly_c": -10.299751523328938,
        "extinction_pressure_index": 0.9616086308896024,
    },
    "y3": {
        "relative_year": 3.0,
        "par_fraction": 0.295817958817466,
        "temperature_anomaly_c": -3.899458205962532,
        "npp_multiplier": 0.3143216873281967,
        "extinction_pressure_index": 0.6310382210688728,
        "atmospheric_co2_ppm": 862.2588444059546,
    },
    "y5": {
        "relative_year": 5.0,
        "par_fraction": 0.5166542649554388,
        "npp_multiplier": 0.5290106212980823,
    },
    "y30": {
        "relative_year": 30.0,
        "par_fraction": 0.9983296210911083,
        "npp_multiplier": 0.9990809435959179,
    },
    "y32": {
        "relative_year": 32.0,
        "par_fraction": 0.998935089920642,
        "temperature_anomaly_c": 1.1520720375933535,
        "npp_multiplier": 0.9994141590474308,
        "extinction_pressure_index": 0.1129194058174602,
        "atmospheric_co2_ppm": 862.2075547163104,
    },
    "y100_pressure": {
        "relative_year": 100.0,
        "extinction_pressure_index": 0.11565077809772965,
    },
    "y800": {
        "relative_year": 800.0,
        "temperature_anomaly_c": 1.277630501139,
        "extinction_pressure_index": 0.1150046372754049,
        "atmospheric_co2_ppm": 860.8537631201724,
    },
    "y5000": {
        "relative_year": 5_000.0,
        "temperature_anomaly_c": 1.239157989327738,
        "extinction_pressure_index": 0.111180406026717,
        "atmospheric_co2_ppm": 853.6015357071284,
    },
    "y40000": {
        "relative_year": 40_000.0,
        "temperature_anomaly_c": 0.9561270327867472,
        "extinction_pressure_index": 0.0837846128922036,
        "atmospheric_co2_ppm": 802.0939102633043,
    },
    "y200000": {
        "relative_year": 200_000.0,
        "temperature_anomaly_c": 0.2721763461717298,
        "extinction_pressure_index": 0.0225688400962163,
        "atmospheric_co2_ppm": 690.0915194702371,
    },
    "y500000": {
        "relative_year": 500_000.0,
        "temperature_anomaly_c": 0.02296564096772675,
        "extinction_pressure_index": 0.001867540311443205,
    },
}

# Analytic RAW-anchored fit constants.  They are calculated from the anchors,
# not tuned against the R3.9 outcome.
PAR_SHAPE = 1.2155495473697007
PAR_TAU_Y = 6.521744795559547
NPP_SHAPE = 1.247509003057912
NPP_TAU_Y = 6.314822167256032
PRESSURE_LONG_A = 0.11565077809772965
PRESSURE_LONG_TAU_Y = 121_184.12714634456
PRESSURE_FAST_SHAPE = 1.877841582534036
PRESSURE_FAST_TAU_Y = 4.25635076086636
TEMP_LONG_A_C = 1.2858854113242046
TEMP_LONG_TAU_Y = 124_217.32007916941
TEMP_WINTER_SHAPE = 0.6633694997588736
TEMP_WINTER_TAU_Y = 2.267502081401679
CO2_BASELINE_PPM = 650.0
CO2_TAU_Y = 120_000.0

# A bounded species-risk transfer amplitude.  This is deliberately fixed
# *before* R3.10 outcome generation.  A sensitivity audit should vary it, but
# the canonical run must not select a value based on survivor desirability.
SPECIES_RISK_AMPLITUDE = 0.25
KEYED_FRAILTY_LOG_SIGMA = 0.25

# D2.2 trophic-chain reduced-order timescales.  Because the historical source
# code is unavailable, these four values are fitted only to the recovered D2.2
# minimum states (plant=.395, herbivore=.433, mesopredator=.782, apex=.974).
# They are an external event-oracle calibration and are not tuned to R3.9 or
# to any R3.10 survivor outcome.
FOODWEB_TAU_Y = np.asarray([2.36488546, 1.15173065, 18.69022931, 231.52114321], dtype=float)


@dataclass(frozen=True)
class R310Config:
    impact_age_ma: float = IMPACT_AGE_MA
    post_event_years: float = POST_EVENT_YEARS
    reporting_checkpoints: int = REPORTING_CHECKPOINTS
    canonical_seed: int = CANONICAL_SEED
    species_risk_amplitude: float = SPECIES_RISK_AMPLITUDE
    keyed_frailty_log_sigma: float = KEYED_FRAILTY_LOG_SIGMA
    guild_hazard_scale: float = 1.0
    frozen_tectonics: bool = True
    impact_distance_mortality_enabled: bool = False
    deep_biological_coupling: bool = False
    adaptive_radiation_enabled: bool = False
    ordinary_speciation_enabled: bool = False

    def __post_init__(self) -> None:
        if abs(self.impact_age_ma - IMPACT_AGE_MA) > 1e-12:
            raise ValueError("R3.10 CHA-1 impact is fixed to exactly 66.0 Ma")
        if abs(self.post_event_years - POST_EVENT_YEARS) > 1e-9:
            raise ValueError("R3.10 event bridge is fixed to +500 kyr")
        if self.reporting_checkpoints != REPORTING_CHECKPOINTS:
            raise ValueError("R3.10 preserves 917 materialized event checkpoints")
        if not self.frozen_tectonics:
            raise ValueError("R3.10 freezes the 66 Ma tectonic raster across the 0.5 Myr event")
        if self.impact_distance_mortality_enabled:
            raise ValueError("exact impact paleocoordinates are provisional; distance mortality is forbidden")
        if self.deep_biological_coupling:
            raise ValueError("R3.10 is the H0 Deep-OFF event bridge")
        if self.adaptive_radiation_enabled or self.ordinary_speciation_enabled:
            raise ValueError("speciation/radiation are disabled inside the dedicated CHA-1 bridge")
        if self.species_risk_amplitude < 0 or self.keyed_frailty_log_sigma < 0:
            raise ValueError("risk amplitudes must be non-negative")
        if not (0.5 <= self.guild_hazard_scale <= 1.5):
            raise ValueError("guild hazard sensitivity scale must remain within [0.5,1.5]")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _stable_uniform(label: str, species_id: str, seed: int = CANONICAL_SEED) -> float:
    raw = hashlib.sha256(f"{seed}|{label}|{species_id}".encode("utf-8")).digest()
    n = int.from_bytes(raw[:8], "big")
    # Strictly inside (0,1), deterministic and independent of Python hash randomization.
    return (n + 0.5) / (2**64)


def _stable_standard_normal(label: str, species_id: str, seed: int = CANONICAL_SEED) -> float:
    u1 = _stable_uniform(label + "|U1", species_id, seed)
    u2 = _stable_uniform(label + "|U2", species_id, seed)
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def _entropy_normalized(weights: Iterable[float]) -> float:
    w = np.asarray(list(weights), dtype=float)
    w = w[np.isfinite(w) & (w > 0)]
    if w.size <= 1:
        return 0.0
    p = w / w.sum()
    return float(-(p * np.log(p)).sum() / math.log(len(p)))


def reporting_schedule() -> np.ndarray:
    """Return exactly 917 D2.2-compatible event-relative reporting times.

    The historical count is preserved.  The exact historical time-grid bytes
    were not recovered, so R3.10 uses a deterministic log-dense positive grid
    while preserving the documented pre-impact witness checkpoints.
    """
    pre = np.asarray([
        -100_000.0, -50_000.0, -25_000.0, -10_000.0, -5_000.0,
        -2_000.0, -1_000.0, -500.0, -250.0, -100.0, -50.0, -25.0,
        -10.0, -5.0, -2.0, -1.0, -0.1,
    ], dtype=float)
    positive = np.geomspace(0.01, POST_EVENT_YEARS, REPORTING_CHECKPOINTS - len(pre) - 1)
    out = np.concatenate([pre, np.asarray([0.0]), positive])
    if len(out) != REPORTING_CHECKPOINTS or not np.all(np.diff(out) > 0):
        raise RuntimeError("R3.10 reporting schedule construction failure")
    return out


def _pchip_field(field: str, extra: list[tuple[float, float]] | None = None) -> PchipInterpolator:
    pts: list[tuple[float, float]] = []
    for anchor in PHYSICAL_ANCHORS.values():
        if field in anchor:
            pts.append((float(anchor["relative_year"]), float(anchor[field])))
    if extra:
        pts.extend(extra)
    # last declaration wins if the same time is present twice
    by_t = {t: v for t, v in pts}
    xy = sorted(by_t.items())
    return PchipInterpolator(
        np.asarray([x for x, _ in xy], dtype=float),
        np.asarray([y for _, y in xy], dtype=float),
        extrapolate=False,
    )


_PAR_PCHIP = _pchip_field(
    "par_fraction",
    extra=[(100.0, 0.9999999996744151), (1000.0, 1.0), (POST_EVENT_YEARS, 1.0)],
)
_NPP_PCHIP = _pchip_field(
    "npp_multiplier",
    extra=[(100.0, 0.9999999998209282), (1000.0, 1.0), (POST_EVENT_YEARS, 1.0)],
)
_TEMP_PCHIP = _pchip_field("temperature_anomaly_c")
_PRESSURE_PCHIP = _pchip_field("extinction_pressure_index")


def physical_forcing(relative_year: float | np.ndarray) -> dict[str, np.ndarray | float]:
    """Recovered-RAW-anchored deterministic CHA-1 forcing provider.

    PCHIP is used because the original D2.2 analytic source bytes are not
    available.  Every recovered RAW anchor is reproduced exactly (to floating
    arithmetic), monotonic shape is preserved between anchors, and no new
    physical extrema are introduced by polynomial overshoot.
    """
    t0 = np.asarray(relative_year, dtype=float)
    scalar = t0.ndim == 0
    t = np.maximum(t0, 0.0)

    par = np.asarray(_PAR_PCHIP(t), dtype=float)
    npp = np.asarray(_NPP_PCHIP(t), dtype=float)
    temperature = np.asarray(_TEMP_PCHIP(np.minimum(t, POST_EVENT_YEARS)), dtype=float)
    pressure = np.asarray(_PRESSURE_PCHIP(np.minimum(t, POST_EVENT_YEARS)), dtype=float)

    # The long pressure tail is separately identifiable from recovered 100-y
    # and +500-kyr anchors.  The residual is the acute impact component used
    # by the direct-extinction hazard; it is clipped only against roundoff.
    pressure_long = PRESSURE_LONG_A * np.exp(-t / PRESSURE_LONG_TAU_Y)
    pressure_fast = np.maximum(pressure - pressure_long, 0.0)

    co20 = PHYSICAL_ANCHORS["impact"]["atmospheric_co2_ppm"]
    co2 = CO2_BASELINE_PPM + (co20 - CO2_BASELINE_PPM) * np.exp(-t / CO2_TAU_Y)

    pre = t0 < 0.0
    if np.any(pre):
        par = np.where(pre, 1.0, par)
        npp = np.where(pre, 1.0, npp)
        pressure = np.where(pre, 0.0, pressure)
        pressure_long = np.where(pre, 0.0, pressure_long)
        pressure_fast = np.where(pre, 0.0, pressure_fast)
        temperature = np.where(pre, 0.0, temperature)
        co2 = np.where(pre, CO2_BASELINE_PPM, co2)

    # PCHIP receives only in-range positive times. Guard microscopic numerical
    # departures from the physical [0,1] multipliers.
    par = np.clip(par, 0.0, 1.0)
    npp = np.clip(npp, 0.0, 1.0)
    pressure = np.clip(pressure, 0.0, 1.0)

    result = {
        "par_fraction": par,
        "temperature_anomaly_c": temperature,
        "npp_multiplier": npp,
        "extinction_pressure_index": pressure,
        "pressure_long_tail": pressure_long,
        "pressure_fast_impact": pressure_fast,
        "atmospheric_co2_ppm": co2,
    }
    if scalar:
        return {k: float(np.asarray(v)) for k, v in result.items()}
    return result


def physical_anchor_audit() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name, anchor in PHYSICAL_ANCHORS.items():
        t = float(anchor["relative_year"])
        pred = physical_forcing(t)
        for key, observed in anchor.items():
            if key == "relative_year":
                continue
            predicted = float(pred[key])
            abs_error = abs(predicted - float(observed))
            denom = max(abs(float(observed)), 1e-12)
            rows.append({
                "anchor": name,
                "relative_year": t,
                "field": key,
                "observed": float(observed),
                "predicted": predicted,
                "abs_error": abs_error,
                "relative_error": abs_error / denom,
            })
    by_field: dict[str, float] = {}
    for r in rows:
        by_field[r["field"]] = max(by_field.get(r["field"], 0.0), r["relative_error"])
    return {
        "provider_semantics": "D2_2_RAW_ANCHORED_REBASED_ANALYTIC_PROVIDER_NOT_BIT_IDENTICAL_HISTORICAL_SOURCE",
        "rows": rows,
        "max_relative_error_by_field": by_field,
        "impact_exact": all(
            abs(float(physical_forcing(0.0)[k]) - float(PHYSICAL_ANCHORS["impact"][k])) <= 5e-13
            for k in ("par_fraction", "temperature_anomaly_c", "npp_multiplier", "extinction_pressure_index", "atmospheric_co2_ppm")
        ),
    }


def foodweb_states(times_year: np.ndarray) -> np.ndarray:
    """Integrate normalized NPP -> plant -> herbivore -> meso -> apex chain."""
    times = np.asarray(times_year, dtype=float)
    if np.any(times < 0):
        raise ValueError("foodweb integration is post-impact only")
    if len(times) == 0:
        return np.empty((0, 4), dtype=float)
    order = np.argsort(times)
    ts = times[order]

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        npp = float(physical_forcing(t)["npp_multiplier"])
        target = np.asarray([npp, y[0], y[1], y[2]], dtype=float)
        return (target - y) / FOODWEB_TAU_Y

    if ts[-1] == 0.0:
        vals = np.ones((len(ts), 4), dtype=float)
    else:
        # The trophic chain has sub-year to ~8-y time constants and is already
        # numerically indistinguishable from baseline long before the 500-kyr
        # physical tail ends.  Integrating a non-stiff explicit solver across
        # the full 500 kyr would waste millions of tiny stability-limited
        # steps.  Solve only the ecological transient and set the recovered
        # tail to exactly baseline once all drivers are effectively unity.
        ECOLOGY_INTEGRATION_END_Y = 2_000.0
        transient_mask = ts <= ECOLOGY_INTEGRATION_END_Y
        eval_t = np.unique(np.concatenate(([0.0], ts[transient_mask])))
        sol = solve_ivp(
            rhs,
            (0.0, float(ECOLOGY_INTEGRATION_END_Y)),
            np.ones(4, dtype=float),
            t_eval=eval_t,
            rtol=2e-10,
            atol=2e-12,
            method="DOP853",
        )
        if not sol.success:
            raise RuntimeError(f"R3.10 food-web integration failed: {sol.message}")
        lut = {float(t): sol.y[:, i] for i, t in enumerate(sol.t)}
        vals = np.ones((len(ts), 4), dtype=float)
        for j, t in enumerate(ts):
            if t <= ECOLOGY_INTEGRATION_END_Y:
                vals[j] = lut[float(t)]
    out = np.empty_like(vals)
    out[order] = vals
    return out


def _hazard_exposure_curve() -> tuple[np.ndarray, np.ndarray]:
    """Normalized cumulative acute impact exposure.

    The long 300–500 kyr climate/pressure tail remains physical state but does
    not create new direct CHA-1 extinction after ecological recovery.  Direct
    CHA-1 hazard is integrated only over the first 20 years, the independently
    recovered acute-collapse window; this is deliberately broader than the
    historical D2.2 last extinction at 14.41 y and therefore is not a lookup
    or hard-coded reproduction of that survivor realization.
    """
    # Dense near t=0 and through the recovered <=14.41-y direct extinction window.
    t = np.unique(np.concatenate([
        np.linspace(0.0, 0.2, 2001),
        np.linspace(0.2, 2.0, 3601),
        np.linspace(2.0, 20.0, 7201),
    ]))
    q = np.asarray(physical_forcing(t)["pressure_fast_impact"], dtype=float)
    c = cumulative_trapezoid(q, t, initial=0.0)
    total = float(c[-1])
    if not total > 0:
        raise RuntimeError("R3.10 acute hazard exposure has non-positive integral")
    return t, c / total


_HAZARD_T, _HAZARD_CDF = _hazard_exposure_curve()


def exposure_at(relative_year: float | np.ndarray) -> np.ndarray | float:
    x = np.asarray(relative_year, dtype=float)
    y = np.interp(np.maximum(x, 0.0), _HAZARD_T, _HAZARD_CDF, left=0.0, right=1.0)
    y = np.where(x < 0.0, 0.0, y)
    return float(y) if x.ndim == 0 else y


def _root_metadata_map(metadata_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(r["species_id"]): r for r in metadata_rows}


def _frame_index(a1: np.lib.npyio.NpzFile, age_ma: float) -> int:
    ages = np.asarray(a1["age_ma"], dtype=float)
    idx = np.where(np.isclose(ages, age_ma, atol=1e-12, rtol=0.0))[0]
    if len(idx) != 1:
        raise RuntimeError(f"A1 reference does not contain exact {age_ma} Ma frame")
    return int(idx[0])


def _species_spatial_metrics(
    st: r38.R38RuntimeState,
    a1: np.lib.npyio.NpzFile,
    metadata_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    md = _root_metadata_map(metadata_rows)
    idx66 = _frame_index(a1, IMPACT_AGE_MA)
    plate = np.asarray(a1["plate_code"][idx66], dtype=int)
    wetland = np.asarray(a1["wetland_forage"][idx66], dtype=float)
    accessible = np.asarray(st.current_accessible, dtype=bool)
    accessible_cells = max(int(np.count_nonzero(accessible)), 1)
    plate_ids = sorted(int(x) for x in np.unique(plate[accessible]) if int(x) >= 0)

    species = sorted(set(st.current_species))
    rows: list[dict[str, Any]] = []
    for sid in species:
        comp_idx = np.asarray([i for i, s in enumerate(st.current_species) if s == sid], dtype=int)
        if comp_idx.size == 0:
            continue
        spatial = np.asarray(st.pop[comp_idx], dtype=float).sum(axis=0)
        total = float(spatial.sum())
        if total <= 0:
            raise RuntimeError(f"R3.10 current species {sid} has non-positive pre-impact population")
        root_weights: dict[str, float] = {}
        for i in comp_idx:
            root_weights[st.root_species[i]] = root_weights.get(st.root_species[i], 0.0) + float(st.pop[i].sum())
        root_sid = max(root_weights.items(), key=lambda kv: (kv[1], kv[0]))[0]
        m = md[root_sid]
        masses = np.asarray([float(st.pop[i].sum()) for i in comp_idx], dtype=float)
        body = float(np.average(st.trait[comp_idx, 2], weights=masses))
        reproduction = float(np.average([md[st.root_species[i]]["relative_reproduction_rate"] for i in comp_idx], weights=masses))
        occupied = spatial > 1e-12
        occupancy_fraction = float(np.count_nonzero(occupied & accessible) / accessible_cells)
        wetland_refuge = float((spatial * np.maximum(wetland, 0.0)).sum() / total)
        plate_w = []
        for pid in plate_ids:
            plate_w.append(float(spatial[plate == pid].sum()))
        plate_entropy = _entropy_normalized(plate_w)
        dw = m.get("diet_weights", {})
        diet_entropy = _entropy_normalized(float(v) for v in dw.values())
        rows.append({
            "species_id": sid,
            "guild_id": int(st.guild[comp_idx[0]]),
            "root_species_for_metadata": root_sid,
            "preimpact_population": total,
            "component_count": int(comp_idx.size),
            "body": body,
            "reproduction": reproduction,
            "occupancy_fraction": occupancy_fraction,
            "plate_entropy": plate_entropy,
            "wetland_refuge": wetland_refuge,
            "diet_entropy": diet_entropy,
        })
    return rows


def _standardize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    mu = float(values.mean())
    sd = float(values.std(ddof=0))
    if sd <= 1e-14:
        return np.zeros_like(values)
    return (values - mu) / sd


def build_species_hazard_table(
    st: r38.R38RuntimeState,
    a1: np.lib.npyio.NpzFile,
    metadata_rows: list[dict[str, Any]],
    cfg: R310Config,
) -> list[dict[str, Any]]:
    rows = _species_spatial_metrics(st, a1, metadata_rows)
    by_guild: dict[int, list[int]] = {}
    for i, r in enumerate(rows):
        by_guild.setdefault(int(r["guild_id"]), []).append(i)

    for guild_id, idxs in sorted(by_guild.items()):
        if guild_id not in D22_GUILD_CUMULATIVE_HAZARD:
            raise RuntimeError(f"unknown CHA-1 guild {guild_id}")
        idx = np.asarray(idxs, dtype=int)
        body = _standardize(np.asarray([rows[i]["body"] for i in idx]))
        repro = _standardize(np.asarray([rows[i]["reproduction"] for i in idx]))
        occ = _standardize(np.asarray([rows[i]["occupancy_fraction"] for i in idx]))
        plate = _standardize(np.asarray([rows[i]["plate_entropy"] for i in idx]))
        wet = _standardize(np.asarray([rows[i]["wetland_refuge"] for i in idx]))
        diet = _standardize(np.asarray([rows[i]["diet_entropy"] for i in idx]))
        # Positive body size increases vulnerability.  Higher reproduction,
        # occupancy, plate diversity, wetland refuge and diet diversity protect.
        composite = (body - repro - occ - plate - wet - diet) / math.sqrt(6.0)
        log_v = cfg.species_risk_amplitude * composite
        for local, i in enumerate(idx):
            sid = rows[i]["species_id"]
            log_v[local] += cfg.keyed_frailty_log_sigma * _stable_standard_normal("CHA1_FRAILTY", sid, cfg.canonical_seed)
        # Preserve D2.2 guild-scale authority exactly: current-state modifiers
        # are centered to geometric mean 1 and therefore cannot silently
        # retune the guild's cumulative hazard magnitude.
        log_v -= float(log_v.mean())
        vulnerability = np.exp(log_v)
        coeff = float(D22_GUILD_CUMULATIVE_HAZARD[guild_id]) * float(cfg.guild_hazard_scale)
        for local, i in enumerate(idx):
            sid = rows[i]["species_id"]
            threshold = -math.log(_stable_uniform("CHA1_THRESHOLD", sid, cfg.canonical_seed))
            total_hazard = coeff * float(vulnerability[local])
            survived = threshold > total_hazard
            if survived:
                ext_time = None
            else:
                target = threshold / total_hazard
                ext_time = float(np.interp(target, _HAZARD_CDF, _HAZARD_T))
            rows[i].update({
                "frailty": float(math.exp(cfg.keyed_frailty_log_sigma * _stable_standard_normal("CHA1_FRAILTY", sid, cfg.canonical_seed))),
                "vulnerability": float(vulnerability[local]),
                "guild_cumulative_hazard": coeff,
                "hazard_threshold": float(threshold),
                "total_cumulative_hazard": total_hazard,
                "extinction_time_year": ext_time,
                "survived_cha1": bool(survived),
            })
    return rows


def _filter_pair_state(d: dict[tuple[str, str], Any], keep_component_ids: set[str]) -> dict[tuple[str, str], Any]:
    return {
        (a, b): v for (a, b), v in d.items()
        if a in keep_component_ids and b in keep_component_ids
    }


def _filter_component_dict(d: dict[str, Any], keep_component_ids: set[str]) -> dict[str, Any]:
    # Vicariance state is component keyed. Founder-state keys can be compound;
    # preserve only records whose explicit component tokens are all still live.
    out: dict[str, Any] = {}
    for k, v in d.items():
        tokens = [tok for tok in str(k).replace("|", ";").split(";") if tok]
        component_like = [tok for tok in tokens if "_C" in tok]
        if not component_like or all(tok in keep_component_ids for tok in component_like):
            out[k] = v
    return out


def _endpoint_population(
    st: r38.R38RuntimeState,
    survivor_species: set[str],
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Recover abundance within pre-impact guild/cell capacity without N>K.

    Species-level extinction removes all components of extinct species.  At
    +500 kyr, surviving components refill only cells they already occupied at
    impact, proportional to their pre-impact within-cell abundance.  The cell
    guild total can never exceed the R3.9 pre-impact guild total.
    """
    keep = np.asarray([sid in survivor_species for sid in st.current_species], dtype=bool)
    if not np.any(keep):
        raise RuntimeError("CHA-1 bridge produced zero surviving components")
    final = np.asarray(st.pop[keep], dtype=float).copy()
    keep_guild = np.asarray(st.guild[keep], dtype=np.uint8)
    pre = np.asarray(st.pop, dtype=float)
    diagnostics: dict[str, Any] = {"guilds": {}}
    for g in sorted(set(int(x) for x in st.guild.tolist())):
        all_i = np.where(st.guild == g)[0]
        kept_local = np.where(keep_guild == g)[0]
        target = pre[all_i].sum(axis=0)
        if kept_local.size == 0:
            diagnostics["guilds"][str(g)] = {
                "preimpact_population": float(target.sum()),
                "endpoint_population": 0.0,
                "recovery_fraction": 0.0,
                "cells_without_survivor_support": int(np.count_nonzero(target > 0)),
            }
            continue
        base = final[kept_local]
        support_sum = base.sum(axis=0)
        supported = support_sum > 0.0
        scale = np.zeros_like(target)
        scale[supported] = target[supported] / support_sum[supported]
        final[kept_local] = base * scale[None, :, :]
        endpoint = final[kept_local].sum(axis=0)
        # Tight closure against the pre-impact guild/cell carrying proxy.
        if np.any(endpoint - target > 2e-10):
            raise RuntimeError("R3.10 endpoint population exceeds pre-impact event carrying proxy")
        pre_total = float(target.sum())
        end_total = float(endpoint.sum())
        diagnostics["guilds"][str(g)] = {
            "preimpact_population": pre_total,
            "endpoint_population": end_total,
            "recovery_fraction": (end_total / pre_total) if pre_total > 0 else 1.0,
            "cells_without_survivor_support": int(np.count_nonzero((target > 0) & (~supported))),
        }
    return final, keep, diagnostics


def run_event_bridge(
    pre_state: r38.R38RuntimeState,
    a1: np.lib.npyio.NpzFile,
    metadata_rows: list[dict[str, Any]],
    cfg: R310Config | None = None,
) -> tuple[r38.R38RuntimeState, dict[str, Any]]:
    cfg = cfg or R310Config()
    if abs(pre_state.age_ma - IMPACT_AGE_MA) > 1e-12:
        raise RuntimeError("R3.10 requires the exact 66.0 Ma PRE_IMPACT checkpoint")
    if len(set(pre_state.current_species)) != 305:
        # Fail closed against accidentally feeding the historical D2.2 120-species state.
        raise RuntimeError("R3.10 requires the rebased R3.9 305-species pre-impact state")
    if np.any(pre_state.pop < -1e-14):
        raise RuntimeError("negative pre-impact population")

    schedule = reporting_schedule()
    post_times = schedule[schedule >= 0.0]
    forcing = physical_forcing(schedule)
    foodweb = foodweb_states(post_times)
    hazard_rows = build_species_hazard_table(pre_state, a1, metadata_rows, cfg)
    survivors = {r["species_id"] for r in hazard_rows if r["survived_cha1"]}
    extinct = sorted({r["species_id"] for r in hazard_rows if not r["survived_cha1"]})

    final_pop, keep, pop_diag = _endpoint_population(pre_state, survivors)
    keep_idx = np.where(keep)[0]
    keep_ids = [pre_state.component_ids[i] for i in keep_idx]
    keep_id_set = set(keep_ids)
    final_current_species = [pre_state.current_species[i] for i in keep_idx]

    registry = {str(k): dict(v) for k, v in pre_state.registry.items()}
    hazard_by_sid = {r["species_id"]: r for r in hazard_rows}
    for sid in extinct:
        if sid in registry:
            registry[sid]["semantic_status"] = "EXTINCT_CHA1"
            registry[sid]["extinction_age_ma"] = IMPACT_AGE_MA - float(hazard_by_sid[sid]["extinction_time_year"]) / 1e6
            registry[sid]["extinction_cause"] = "continuous_CHA1_environmental_extinction_hazard"
    for sid in survivors:
        if sid in registry:
            registry[sid]["cha1_survivor"] = True

    events = list(pre_state.events)
    for sid in extinct:
        r = hazard_by_sid[sid]
        events.append({
            "event": "CHA1_species_extinction",
            "event_type": "CHA1_species_extinction",
            "relative_year": float(r["extinction_time_year"]),
            "absolute_age_ma": IMPACT_AGE_MA - float(r["extinction_time_year"]) / 1e6,
            "species_id": sid,
            "guild_id": int(r["guild_id"]),
            "vulnerability": float(r["vulnerability"]),
            "hazard_threshold": float(r["hazard_threshold"]),
            "cause": "continuous_CHA1_environmental_extinction_hazard",
        })
    events.sort(key=lambda e: (
        -float(e.get("age_ma", e.get("absolute_age_ma", 1e99))) if ("age_ma" in e or "absolute_age_ma" in e) else 0.0,
        str(e.get("event", "")),
        str(e.get("species_id", "")),
    ))
    events.append({
        "event": "CHA1_high_resolution_event_bridge_complete",
        "age_ma": POST_EVENT_AGE_MA,
        "relative_year": POST_EVENT_YEARS,
        "survivor_species": len(survivors),
        "direct_cha1_extinctions": len(extinct),
    })

    # Keep all historical species baselines/registry provenance; extinct species
    # can remain historical keys.  Active pair/component lifecycle state is
    # pruned to live components and otherwise frozen during the special event.
    final_state = r38.R38RuntimeState(
        age_ma=POST_EVENT_AGE_MA,
        elapsed_year=float(pre_state.elapsed_year + POST_EVENT_YEARS),
        component_ids=keep_ids,
        root_species=[pre_state.root_species[i] for i in keep_idx],
        current_species=final_current_species,
        guild=np.asarray(pre_state.guild[keep_idx], dtype=np.uint8),
        pop=np.asarray(final_pop, dtype=float),
        trait=np.asarray(pre_state.trait[keep_idx], dtype=float).copy(),
        va=np.asarray(pre_state.va[keep_idx], dtype=float).copy(),
        gen=np.asarray(pre_state.gen[keep_idx], dtype=float).copy(),
        registry=registry,
        child_counters=dict(pre_state.child_counters),
        current_accessible=np.asarray(pre_state.current_accessible, dtype=bool).copy(),
        baselines=json.loads(json.dumps(r38._jsonable(pre_state.baselines))),
        ri_state=_filter_pair_state(pre_state.ri_state, keep_id_set),
        clock_state=_filter_pair_state(pre_state.clock_state, keep_id_set),
        ext_state={k: v for k, v in pre_state.ext_state.items() if k in survivors},
        founder_state=_filter_component_dict(pre_state.founder_state, keep_id_set),
        vicariance_state={k: v for k, v in pre_state.vicariance_state.items() if k in keep_id_set},
        reconnection_state=_filter_pair_state(pre_state.reconnection_state, keep_id_set),
        events=events,
        snapshots=list(pre_state.snapshots) + [{
            "age_ma": POST_EVENT_AGE_MA,
            "elapsed_myr": (pre_state.elapsed_year + POST_EVENT_YEARS) / 1e6,
            "species_richness": len(survivors),
            "component_count": len(keep_ids),
            "total_population": float(final_pop.sum()),
            "event_side": "POST_CHA1_500KY",
        }],
        founder_stats_last=[],
        gene_flow_closure=dict(pre_state.gene_flow_closure),
        topology_remap_mass=float(pre_state.topology_remap_mass),
        initial_total_population=float(pre_state.initial_total_population),
        reduced_state=ReducedGeneticLifecycleState(
            np.asarray(pre_state.reduced_state.va_within[keep_idx], dtype=float).copy(),
            np.asarray(pre_state.reduced_state.ancestry_covariance[keep_idx], dtype=float).copy(),
            np.asarray(pre_state.reduced_state.neutral_segregation_potential[np.ix_(keep_idx, keep_idx, np.arange(pre_state.reduced_state.neutral_segregation_potential.shape[2]))], dtype=float).copy(),
            np.asarray(pre_state.reduced_state.adaptive_coordinate[keep_idx], dtype=float).copy(),
        ),
    )
    final_state._lat = np.asarray(pre_state._lat, dtype=float).copy()
    final_state._lon = np.asarray(pre_state._lon, dtype=float).copy()

    # Event endpoint invariants.
    if np.any(final_state.pop < -1e-14):
        raise RuntimeError("negative post-CHA1 population")
    if not np.all(final_state.pop[:, ~final_state.current_accessible] == 0.0):
        raise RuntimeError("post-CHA1 population exists on inaccessible cells")
    if not np.allclose(final_state.va, final_state.reduced_state.va_within, atol=1e-13, rtol=0.0):
        raise RuntimeError("post-CHA1 VA/reduced-state binding diverged")
    s = final_state.reduced_state.neutral_segregation_potential
    s_sym = float(np.max(np.abs(s - np.swapaxes(s, 0, 1)))) if s.size else 0.0
    s_diag = float(np.max(np.abs(np.diagonal(s, axis1=0, axis2=1)))) if s.size else 0.0
    if s_sym > 2e-12 or s_diag > 2e-12 or float(np.min(s)) < -2e-12:
        raise RuntimeError("post-CHA1 segregation-potential invariants failed")

    extinct_times = sorted(float(r["extinction_time_year"]) for r in hazard_rows if r["extinction_time_year"] is not None)
    f_at_post = physical_forcing(post_times)
    report = {
        "reporting_checkpoints": int(len(schedule)),
        "reporting_time_min_year": float(schedule[0]),
        "reporting_time_max_year": float(schedule[-1]),
        "preimpact_species": len(set(pre_state.current_species)),
        "postimpact_survivor_species": len(survivors),
        "direct_cha1_extinctions": len(extinct),
        "extinction_fraction": len(extinct) / len(set(pre_state.current_species)),
        "survivor_species_ids": sorted(survivors),
        "extinct_species_ids": extinct,
        "extinction_time": {
            "min_year": extinct_times[0] if extinct_times else None,
            "median_year": float(np.median(extinct_times)) if extinct_times else None,
            "max_year": extinct_times[-1] if extinct_times else None,
            "all_within_20_year_acute_window": bool((not extinct_times) or extinct_times[-1] <= 20.0 + 1e-12),
        },
        "guilds": {},
        "population_recovery": pop_diag,
        "preimpact_total_population": float(pre_state.pop.sum()),
        "postevent_total_population": float(final_state.pop.sum()),
        "physical_endpoint": {k: float(np.asarray(v)[-1]) for k, v in f_at_post.items()},
        "foodweb_minimum": {
            "plant": float(foodweb[:, 0].min()),
            "herbivore": float(foodweb[:, 1].min()),
            "mesopredator": float(foodweb[:, 2].min()),
            "apex": float(foodweb[:, 3].min()),
        },
        "foodweb_endpoint": {
            "plant": float(foodweb[-1, 0]),
            "herbivore": float(foodweb[-1, 1]),
            "mesopredator": float(foodweb[-1, 2]),
            "apex": float(foodweb[-1, 3]),
        },
        "segregation_potential_symmetry_max_abs": s_sym,
        "segregation_potential_diagonal_max_abs": s_diag,
        "ordinary_speciation_events_during_bridge": 0,
        "adaptive_radiation_events_during_bridge": 0,
        "deep_biological_coupling": False,
        "impact_distance_mortality_enabled": False,
        "ordinary_lifecycle_timers_frozen_during_cha1": True,
        "hazard_table": hazard_rows,
    }
    for g in range(1, 7):
        rr = [r for r in hazard_rows if int(r["guild_id"]) == g]
        surv = sum(bool(r["survived_cha1"]) for r in rr)
        report["guilds"][str(g)] = {
            "initial_species": len(rr),
            "survivors": surv,
            "extinctions": len(rr) - surv,
            "survival_fraction": surv / len(rr) if rr else None,
            "transferred_D22_cumulative_hazard": D22_GUILD_CUMULATIVE_HAZARD[g],
            "historical_D22_survival_fraction": D22_GUILD_COUNTS[g][1] / D22_GUILD_COUNTS[g][0],
        }
    return final_state, report


def save_postcha1_checkpoint(
    st: r38.R38RuntimeState,
    out_dir: Path,
    parent_authority: dict[str, Any],
    cfg: R310Config,
    event_report: dict[str, Any],
) -> dict[str, Any]:
    if abs(st.age_ma - POST_EVENT_AGE_MA) > 1e-12:
        raise ValueError("R3.10 post-CHA1 checkpoint must be exactly 65.5 Ma")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "WORLD1_H0_65P5Ma_POST_CHA1_500KY_CANONICAL_CHECKPOINT_v0_6D1_R3_10"
    jp = out_dir / f"{stem}.json"
    npzp = out_dir / f"{stem}.npz"
    np.savez_compressed(
        npzp,
        guild=st.guild,
        population=st.pop,
        trait=st.trait,
        va=st.va,
        generation_time=st.gen,
        current_accessible=st.current_accessible.astype(np.uint8),
        reduced_va_within=st.reduced_state.va_within,
        reduced_ancestry_covariance=st.reduced_state.ancestry_covariance,
        reduced_neutral_segregation_potential=st.reduced_state.neutral_segregation_potential,
        reduced_adaptive_coordinate=st.reduced_state.adaptive_coordinate,
        lat=np.asarray(st._lat, dtype=float),
        lon=np.asarray(st._lon, dtype=float),
    )
    meta = {
        "schema": SCHEMA,
        "stage": STAGE,
        "parent_stage": PARENT_STAGE,
        "age_ma": float(st.age_ma),
        "event_side": "POST_CHA1_500KY",
        "elapsed_year": float(st.elapsed_year),
        "parent_r39_authority": parent_authority,
        "cha1_event_authority": {
            "historical_reference": "v0.6.3D2.2 CHA-1 High-Resolution Replay",
            "historical_archive_sha256": "42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8",
            "historical_solver_bytes_recovered": False,
            "implementation_semantics": "D2_2_RAW_ANCHORED_REBASED_EVENT_PROVIDER",
            "event_window_year": [-100000.0, 500000.0],
            "materialized_reporting_checkpoints": REPORTING_CHECKPOINTS,
            "frozen_tectonics": True,
            "impact_distance_mortality": "DISABLED_EXACT_SITE_PROVISIONAL",
            "no_per_step_bernoulli": True,
            "no_forced_guild_survivor": True,
            "no_historical_survivor_lookup": True,
        },
        "nominal_reduced_order_reference": {
            "label": "K_CENTER",
            "K_eff": r38.NOMINAL_K,
            "semantic_role": "OPERATIONAL_REDUCED_ORDER_COORDINATE_REFERENCE_NOT_PHYSICAL_CONSTANT",
        },
        "component_ids": st.component_ids,
        "root_species": st.root_species,
        "current_species": st.current_species,
        "registry": st.registry,
        "child_counters": st.child_counters,
        "baselines": st.baselines,
        "ri_state": r38._pair_dict_rows(st.ri_state),
        "clock_state": r38._pair_dict_rows(st.clock_state),
        "ext_state": st.ext_state,
        "founder_state": st.founder_state,
        "vicariance_state": st.vicariance_state,
        "reconnection_state": r38._pair_dict_rows(st.reconnection_state),
        "events": r38._jsonable(st.events),
        "snapshots": r38._jsonable(st.snapshots),
        "founder_stats_last": r38._jsonable(st.founder_stats_last),
        "gene_flow_closure": r38._jsonable(st.gene_flow_closure),
        "topology_remap_mass": st.topology_remap_mass,
        "initial_total_population": st.initial_total_population,
        "config": asdict(cfg),
        "event_summary": {
            k: v for k, v in event_report.items()
            if k not in {"hazard_table", "survivor_species_ids", "extinct_species_ids"}
        },
        "npz_file": npzp.name,
        "governance": {
            "cha1_applied": True,
            "deep_biological_coupling": False,
            "ordinary_125kyr_crossing_of_66ma_used": False,
            "ordinary_speciation_inside_event": False,
            "adaptive_radiation_inside_event": False,
            "historical_survivor_ids_used_as_lookup": False,
            "scalar_k_physical_constant_authorized": False,
            "mu_b_or_ceiling_change_authorized": False,
            "next_stage_may_restart_ordinary_h0_from_65p5ma": True,
        },
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {
        "json": str(jp),
        "npz": str(npzp),
        "json_sha256": _sha256(jp),
        "npz_sha256": _sha256(npzp),
    }


def load_postcha1_checkpoint(json_path: Path) -> r38.R38RuntimeState:
    jp = Path(json_path)
    m = json.loads(jp.read_text(encoding="utf-8"))
    if m.get("schema") != SCHEMA or m.get("stage") != STAGE or m.get("event_side") != "POST_CHA1_500KY":
        raise RuntimeError("R3.10 checkpoint metadata mismatch")
    if abs(float(m["age_ma"]) - POST_EVENT_AGE_MA) > 1e-12:
        raise RuntimeError("R3.10 checkpoint age mismatch")
    gov = m.get("governance", {})
    if gov.get("cha1_applied") is not True or gov.get("deep_biological_coupling") is not False:
        raise RuntimeError("R3.10 checkpoint governance mismatch")
    z = np.load(jp.parent / m["npz_file"], allow_pickle=False)
    st = r38.R38RuntimeState(
        age_ma=float(m["age_ma"]),
        elapsed_year=float(m["elapsed_year"]),
        component_ids=list(m["component_ids"]),
        root_species=list(m["root_species"]),
        current_species=list(m["current_species"]),
        guild=z["guild"].astype(np.uint8),
        pop=z["population"].astype(float),
        trait=z["trait"].astype(float),
        va=z["va"].astype(float),
        gen=z["generation_time"].astype(float),
        registry={str(k): dict(v) for k, v in m["registry"].items()},
        child_counters={str(k): int(v) for k, v in m["child_counters"].items()},
        current_accessible=z["current_accessible"].astype(bool),
        baselines=m["baselines"],
        ri_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["ri_state"]).items()},
        clock_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["clock_state"]).items()},
        ext_state=m["ext_state"],
        founder_state=m["founder_state"],
        vicariance_state=m["vicariance_state"],
        reconnection_state={k: dict(v) for k, v in r38._pair_dict_from_rows(m["reconnection_state"]).items()},
        events=list(m["events"]),
        snapshots=list(m["snapshots"]),
        founder_stats_last=list(m["founder_stats_last"]),
        gene_flow_closure=dict(m["gene_flow_closure"]),
        topology_remap_mass=float(m["topology_remap_mass"]),
        initial_total_population=float(m["initial_total_population"]),
        reduced_state=ReducedGeneticLifecycleState(
            z["reduced_va_within"].astype(float),
            z["reduced_ancestry_covariance"].astype(float),
            z["reduced_neutral_segregation_potential"].astype(float),
            z["reduced_adaptive_coordinate"].astype(float),
        ),
    )
    st._lat = z["lat"].astype(float)
    st._lon = z["lon"].astype(float)
    return st


def validate_parent_r39_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    d = root / "references" / "v0_6D1_R3_9"
    summary_path = d / "R3_9_PRE_CHA1_CONTINUATION_SUMMARY.json"
    checkpoint_path = d / "WORLD1_H0_66Ma_PRE_CHA1_CANONICAL_CHECKPOINT_v0_6D1_R3_9.json"
    if not summary_path.exists() or not checkpoint_path.exists():
        raise RuntimeError("R3.10 requires materialized R3.9 run evidence")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("verdict") != "PASS_CANONICAL_150_TO_66_H0_CONTINUATION__PRE_CHA1_66MA_CHECKPOINT_READY__CHA1_NOT_APPLIED":
        raise RuntimeError("R3.9 parent verdict is not authoritative")
    cp = summary.get("checkpoint", {})
    expected_j = cp.get("json_sha256")
    expected_n = cp.get("npz_sha256")
    npz_path = checkpoint_path.with_suffix(".npz")
    if _sha256(checkpoint_path) != expected_j or _sha256(npz_path) != expected_n:
        raise RuntimeError("R3.9 parent checkpoint hash mismatch")
    st = load_precha1_checkpoint(checkpoint_path)
    if len(set(st.current_species)) != 305 or abs(st.age_ma - 66.0) > 1e-12:
        raise RuntimeError("R3.9 parent state cardinality/boundary mismatch")
    return {
        "state": st,
        "checkpoint_json": str(checkpoint_path.relative_to(root)),
        "checkpoint_npz": str(npz_path.relative_to(root)),
        "checkpoint_json_sha256": expected_j,
        "checkpoint_npz_sha256": expected_n,
        "summary_sha256": _sha256(summary_path),
    }


def deterministic_hazard_identity(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]]) -> bool:
    def projection(rows: list[dict[str, Any]]) -> dict[str, tuple[float, float, float | None, bool]]:
        return {
            r["species_id"]: (
                float(r["vulnerability"]),
                float(r["hazard_threshold"]),
                None if r["extinction_time_year"] is None else float(r["extinction_time_year"]),
                bool(r["survived_cha1"]),
            )
            for r in rows
        }
    return projection(rows_a) == projection(rows_b)
