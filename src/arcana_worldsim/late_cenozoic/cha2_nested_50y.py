from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import math
import hashlib

import numpy as np

from .integrated_provider import (
    IntegratedLateCenozoicProvider,
    IntegratedProviderConfig,
    SealedRecentA1Provider,
    _bridge_recent_relative_eustatic_anomaly,
    age_ma_to_model_seconds,
)
from .sealed_120ka_boundary import conservative_nested_remap

STATUS = "PASS_CHA2_50Y_NESTED_PHYSICAL_STATE_RECONSTRUCTION_CANDIDATE"
AUTHORITY = (
    "DERIVED_NESTED_50Y_STATE_BETWEEN_EXACT_v0.6.1_100Y_ANCHORS; "
    "SEALED_100Y_CHECKPOINTS_REMAIN_AUTHORITATIVE"
)
CORE_OLDER_YEAR = -15_000
CORE_YOUNGER_YEAR = -11_000
OUTER_STEP_YEARS = 100
NESTED_STEP_YEARS = 50
FIRE_SUSCEPTIBILITY = 0.06111385180931255
FIRE_SOURCE_ECOLOGY_SHA256 = "16c03fda947e80595ceb0377f00aba46384743c6ac1b3e7f9e1663ebf0b67d30"
FIRE_SOURCE_SHORELINE_SHA256 = "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85"
SEED = 617231

# Cross-platform replay tolerance for derived transcendental calculations.
# The sealed NPZ payloads and their hashes remain byte-authoritative.  The
# current C1 implementation re-evaluates cos/log/exp terms on the host libm;
# therefore formula replay is required to be numerically equivalent rather
# than byte-identical across operating systems / NumPy builds.
FORMULA_EQ_RTOL = 1.0e-10
FORMULA_EQ_ATOL = 1.0e-12


@dataclass(frozen=True)
class Nested50YConfig:
    core_older_year_before_book: int = CORE_OLDER_YEAR
    core_younger_year_before_book: int = CORE_YOUNGER_YEAR
    outer_step_years: int = OUTER_STEP_YEARS
    nested_step_years: int = NESTED_STEP_YEARS
    fire_susceptibility: float = FIRE_SUSCEPTIBILITY
    seed: int = SEED
    pet_temperature_sensitivity_per_c: float = 0.045
    positive_floor: float = 1e-8


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _orbital_raw(time_years: np.ndarray | float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    t = np.asarray(time_years, dtype=float)
    p23 = 9603.793806550066
    p41 = 553.7494246332965
    p100 = 5799.933923448708
    w23, w41, w100 = 0.21944756078334268, 0.4712668524115561, 0.30928558680510126
    precession = np.cos(2.0 * np.pi * (t + p23) / 23000.0)
    obliquity = np.cos(2.0 * np.pi * (t + p41) / 41000.0)
    eccentricity = np.cos(2.0 * np.pi * (t + p100) / 100000.0)
    raw = w23 * precession + w41 * obliquity + w100 * eccentricity
    return precession, obliquity, eccentricity, raw


def _numeric_equivalence(label: str, candidate: np.ndarray, sealed: np.ndarray) -> dict[str, float | bool | str]:
    a = np.asarray(candidate, dtype=float)
    b = np.asarray(sealed, dtype=float)
    if a.shape != b.shape:
        raise ValueError(f"C1 {label} shape mismatch: {a.shape} != {b.shape}")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError(f"C1 {label} contains non-finite values")
    diff = np.abs(a - b)
    scale = np.maximum(np.abs(b), 1.0)
    rel = diff / scale
    max_abs = float(np.max(diff)) if diff.size else 0.0
    max_scaled_rel = float(np.max(rel)) if rel.size else 0.0
    ok = bool(np.allclose(a, b, rtol=FORMULA_EQ_RTOL, atol=FORMULA_EQ_ATOL, equal_nan=False))
    if not ok:
        idx = int(np.argmax(diff)) if diff.size else 0
        raise ValueError(
            f"C1 {label} numerical reconstruction mismatch: "
            f"max_abs={max_abs:.17g}, max_scaled_rel={max_scaled_rel:.17g}, "
            f"rtol={FORMULA_EQ_RTOL:.1e}, atol={FORMULA_EQ_ATOL:.1e}, flat_index={idx}"
        )
    return {
        "label": label,
        "platform_stable_numeric_equivalence": True,
        "max_abs_error": max_abs,
        "max_scaled_relative_error": max_scaled_rel,
        "rtol": FORMULA_EQ_RTOL,
        "atol": FORMULA_EQ_ATOL,
    }

def _canonical_freshwater_pulse(time_years: np.ndarray | float) -> np.ndarray:
    t = np.asarray(time_years, dtype=float)
    return (
        0.190 * np.exp(-0.5 * ((t + 12_900.0) / 180.0) ** 2)
        + 0.045 * np.exp(-0.5 * ((t + 13_600.0) / 350.0) ** 2)
    )


class CHA2Nested50YRecentProvider:
    """Derived 50-year physical states inside the D2.1 CHA-2 core.

    Exact v0.6.1 100-year checkpoints are never replaced. Each 50-year midpoint
    is reconstructed locally from the exact preceding sealed checkpoint using
    the same v0.6.1 state equations. The stochastic volcanic realization is
    frozen from the sealed outer 100-year interval; it is never re-sampled.

    Local anchoring is deliberate: a reconstructed midpoint may be used as a
    coupling state, but accumulated 50-year numerical drift is not allowed to
    overwrite the independently sealed 100-year trajectory.
    """

    def __init__(
        self,
        a1: Mapping[str, Any],
        sealed_recent_root: Path,
        cfg: IntegratedProviderConfig | None = None,
        nested_cfg: Nested50YConfig | None = None,
    ) -> None:
        self.cfg = cfg or IntegratedProviderConfig()
        self.nested_cfg = nested_cfg or Nested50YConfig()
        self.root = Path(sealed_recent_root)
        self.base = SealedRecentA1Provider(a1, self.root, self.cfg)
        self.history = self.base.history
        self.time_years = np.asarray(self.history["time_year_before_book"], dtype=float)
        self._year_to_index = {int(round(float(y))): i for i, y in enumerate(self.time_years)}
        if int(self.nested_cfg.outer_step_years) != 100 or int(self.nested_cfg.nested_step_years) != 50:
            raise ValueError("C1 authority is calibrated specifically for 100-y sealed anchors and 50-y nested midpoints")

        # Verify source/payload provenance available in the minimal sealed root.
        recent_path = self.root / "outputs/hybrid1/paleoclimate_v0_6_1/recent_paleoclimate_history.npz"
        shoreline_path = self.root / "inputs/v0_5_5I_SEALED/shoreline_state_I.npz"
        self.source_hashes = {
            "recent_history": _sha256(recent_path),
            "shoreline": _sha256(shoreline_path),
            "ecology_state_parent_declared": FIRE_SOURCE_ECOLOGY_SHA256,
        }
        if self.source_hashes["shoreline"] != FIRE_SOURCE_SHORELINE_SHA256:
            raise ValueError("sealed shoreline hash mismatch for C1 fire-susceptibility provenance")

        # The original orbital proxy normalizes its weighted sum over the exact
        # sealed -120 ka -> 0, 100-year grid. Reuse those normalization constants
        # at arbitrary substeps so every 100-y forcing checkpoint remains exact.
        raw = _orbital_raw(self.time_years)[3]
        self._orbital_mean = float(np.mean(raw))
        self._orbital_std = float(np.std(raw))
        reconstructed_summer = (raw - self._orbital_mean) / self._orbital_std
        self.formula_replay_equivalence = {
            "orbital_forcing": _numeric_equivalence(
                "orbital forcing", reconstructed_summer,
                np.asarray(self.history["summer_ablation_forcing_index"], dtype=float),
            )
        }

        # Re-evaluate the v0.6.1 equations only as a provenance/equivalence
        # check.  Do not use that host-dependent float replay as the anchor
        # authority.  Once equivalence is proven, load every available 100-y
        # state variable from the SHA-verified sealed history itself.
        formula_raw = self._reconstruct_exact_raw_100y_history()
        self.formula_replay_equivalence.update(self._verify_formula_raw_reconstruction(formula_raw))
        self._raw = self._seal_backed_raw_100y_history(formula_raw)
        self._sealed_book_raw_temp = float(self._raw["temperature_raw_c"][-1])
        self._sealed_book_raw_sea = float(self._raw["sea_level_raw_m"][-1])

    def _summer_at(self, year: float) -> float:
        raw = float(np.asarray(_orbital_raw(float(year))[3]))
        return (raw - self._orbital_mean) / self._orbital_std

    def _volcanic_for_outer_interval(self, outer_end_year: int) -> float:
        i = self._year_to_index[int(outer_end_year)]
        return float(self.history["volcanic_aerosol_index"][i])

    def _reconstruct_exact_raw_100y_history(self) -> dict[str, np.ndarray]:
        t = self.time_years
        n = t.size
        dt = 100.0
        atm = np.zeros(n); ocean = np.zeros(n); biosphere = np.zeros(n); geo = np.zeros(n)
        temp = np.zeros(n); ice = np.zeros(n); overturning = np.ones(n); freshwater = np.zeros(n)
        flux_volcanic = np.zeros(n); flux_weathering = np.zeros(n); flux_airsea = np.zeros(n)
        flux_biosphere = np.zeros(n); flux_fire = np.zeros(n)
        atm[0] = 594.0; ocean[0] = 38_000.0; biosphere[0] = 2_200.0; geo[0] = 5_000_000.0
        ice[0] = 0.15
        volcanic = np.asarray(self.history["volcanic_aerosol_index"], dtype=float)
        summer = np.asarray(self.history["summer_ablation_forcing_index"], dtype=float)
        canonical = np.asarray(self.history["canonical_freshwater_pulse_sv"], dtype=float)

        for i in range(1, n):
            melt_rate = max(0.0, (ice[i - 2] - ice[i - 1]) / dt) if i > 1 else 0.0
            freshwater[i] = canonical[i] + min(0.08, melt_rate * 100.0)
            overturning_eq = np.clip(1.0 - 3.3 * freshwater[i], 0.25, 1.0)
            tau_m = 150.0 if overturning_eq < overturning[i - 1] else 650.0
            overturning[i] = np.clip(
                overturning[i - 1] + dt * (overturning_eq - overturning[i - 1]) / tau_m,
                0.20, 1.05,
            )
            ppm = max(atm[i - 1] / 2.12, 80.0)
            f_co2 = 5.35 * np.log(ppm / 280.0)
            f_ice = -3.8 * ice[i - 1]
            f_orbit = 0.42 * summer[i]
            f_overturning = -1.15 * (1.0 - overturning[i])
            f_aerosol = -4.0 * volcanic[i]
            t_eq = 0.85 * (f_co2 + f_ice + f_orbit + f_overturning + f_aerosol)
            temp[i] = temp[i - 1] + dt * (t_eq - temp[i - 1]) / 650.0
            cold_index = -1.55 * summer[i] - 0.50 * temp[i] - 0.15
            ice_eq = 1.0 / (1.0 + np.exp(-cold_index / 0.50))
            tau_i = 6000.0 if ice_eq > ice[i - 1] else 950.0
            ice[i] = np.clip(ice[i - 1] + dt * (ice_eq - ice[i - 1]) / tau_i, 0.0, 1.0)
            flux_volcanic[i] = 0.080 * (1.0 + 0.30 * volcanic[i])
            flux_weathering[i] = 0.080 * (ppm / 280.0) ** 0.32 * np.exp(0.040 * temp[i])
            atm_eq_ocean = 594.0 + 30.0 * temp[i] + 10.0 * (1.0 - overturning[i])
            flux_airsea[i] = (atm[i - 1] - atm_eq_ocean) / 900.0
            atm_eq_bio = 594.0 + 6.0 * temp[i]
            flux_biosphere[i] = (atm[i - 1] - atm_eq_bio) / 1000.0
            flux_fire[i] = max(
                0.0,
                0.008 * (temp[i] + 1.0) * (0.5 + self.nested_cfg.fire_susceptibility),
            )
            d_airsea = flux_airsea[i] * dt
            d_bio = flux_biosphere[i] * dt
            d_geo_atm = (flux_volcanic[i] - flux_weathering[i]) * dt
            d_fire = flux_fire[i] * dt
            atm[i] = atm[i - 1] - d_airsea - d_bio + d_geo_atm + d_fire
            ocean[i] = ocean[i - 1] + d_airsea
            biosphere[i] = biosphere[i - 1] + d_bio - d_fire
            geo[i] = geo[i - 1] - d_geo_atm

        sea_raw = -125.0 * ice + 0.40 * temp
        return {
            "time_year_before_book": t.copy(),
            "atmospheric_carbon_gtc": atm,
            "ocean_carbon_gtc": ocean,
            "biosphere_soil_carbon_gtc": biosphere,
            "active_geologic_carbon_gtc": geo,
            "temperature_raw_c": temp,
            "ice_volume_index": ice,
            "overturning_strength": overturning,
            "freshwater_forcing_sv": freshwater,
            "sea_level_raw_m": sea_raw,
            "carbon_flux_volcanic_gtc_yr": flux_volcanic,
            "carbon_flux_weathering_gtc_yr": flux_weathering,
            "carbon_flux_airsea_gtc_yr": flux_airsea,
            "carbon_flux_biosphere_gtc_yr": flux_biosphere,
            "carbon_flux_fire_gtc_yr": flux_fire,
        }

    def _verify_formula_raw_reconstruction(self, formula_raw: Mapping[str, np.ndarray]) -> dict[str, dict[str, float | bool | str]]:
        mapping = {
            "atmospheric_carbon_gtc": "atmospheric_carbon_gtc",
            "ocean_carbon_gtc": "ocean_carbon_gtc",
            "biosphere_soil_carbon_gtc": "biosphere_soil_carbon_gtc",
            "active_geologic_carbon_gtc": "active_geologic_carbon_gtc",
            "ice_volume_index": "ice_volume_index",
            "overturning_strength": "overturning_strength",
            "freshwater_forcing_sv": "freshwater_forcing_sv",
            "carbon_flux_volcanic_gtc_yr": "carbon_flux_volcanic_gtc_yr",
            "carbon_flux_weathering_gtc_yr": "carbon_flux_weathering_gtc_yr",
            "carbon_flux_airsea_gtc_yr": "carbon_flux_airsea_gtc_yr",
            "carbon_flux_biosphere_gtc_yr": "carbon_flux_biosphere_gtc_yr",
            "carbon_flux_fire_gtc_yr": "carbon_flux_fire_gtc_yr",
        }
        metrics: dict[str, dict[str, float | bool | str]] = {}
        for raw_key, sealed_key in mapping.items():
            metrics[raw_key] = _numeric_equivalence(
                f"100-y formula replay {raw_key}",
                np.asarray(formula_raw[raw_key], dtype=float),
                np.asarray(self.history[sealed_key], dtype=float),
            )
        temp_anom = np.asarray(formula_raw["temperature_raw_c"], dtype=float) - float(formula_raw["temperature_raw_c"][-1])
        sea_anom = np.asarray(formula_raw["sea_level_raw_m"], dtype=float) - float(formula_raw["sea_level_raw_m"][-1])
        metrics["global_temperature_anomaly_c"] = _numeric_equivalence(
            "100-y formula replay global_temperature_anomaly_c",
            temp_anom, np.asarray(self.history["global_temperature_anomaly_c"], dtype=float),
        )
        metrics["sea_level_anomaly_m"] = _numeric_equivalence(
            "100-y formula replay sea_level_anomaly_m",
            sea_anom, np.asarray(self.history["sea_level_anomaly_m"], dtype=float),
        )
        return metrics

    def _seal_backed_raw_100y_history(self, formula_raw: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
        # Exact sealed values are the authority at every 100-y checkpoint.
        # temperature_raw_c itself was not serialized; preserve its absolute
        # book offset from the validated formula replay while imposing the
        # sealed temperature anomaly exactly at all anchors.
        out: dict[str, np.ndarray] = {}
        direct = (
            "atmospheric_carbon_gtc", "ocean_carbon_gtc", "biosphere_soil_carbon_gtc",
            "active_geologic_carbon_gtc", "ice_volume_index", "overturning_strength",
            "freshwater_forcing_sv", "carbon_flux_volcanic_gtc_yr",
            "carbon_flux_weathering_gtc_yr", "carbon_flux_airsea_gtc_yr",
            "carbon_flux_biosphere_gtc_yr", "carbon_flux_fire_gtc_yr",
        )
        for key in direct:
            out[key] = np.asarray(self.history[key], dtype=float).copy()
        out["time_year_before_book"] = np.asarray(self.history["time_year_before_book"], dtype=float).copy()
        book_raw_temp = float(np.asarray(formula_raw["temperature_raw_c"], dtype=float)[-1])
        out["temperature_raw_c"] = np.asarray(self.history["global_temperature_anomaly_c"], dtype=float).copy() + book_raw_temp
        out["sea_level_raw_m"] = -125.0 * out["ice_volume_index"] + 0.40 * out["temperature_raw_c"]
        return out

    def supports_year(self, year_before_book: int | float) -> bool:
        y = float(year_before_book)
        if y < -120_000.0 - 1e-9 or y > 1e-9:
            return False
        yi = int(round(y))
        if abs(y - yi) > 1e-9:
            return False
        if yi in self._year_to_index:
            return True
        return (
            self.nested_cfg.core_older_year_before_book < yi < self.nested_cfg.core_younger_year_before_book
            and yi % self.nested_cfg.nested_step_years == 0
            and yi % self.nested_cfg.outer_step_years != 0
        )

    def supports_age(self, age_ma: float) -> bool:
        y = -float(age_ma) * 1_000_000.0
        return abs(y - round(y)) <= 1e-7 and self.supports_year(int(round(y)))

    def _exact_state_vector(self, year: int) -> dict[str, float]:
        i = self._year_to_index[int(year)]
        return {
            "atmospheric_carbon_gtc": float(self._raw["atmospheric_carbon_gtc"][i]),
            "ocean_carbon_gtc": float(self._raw["ocean_carbon_gtc"][i]),
            "biosphere_soil_carbon_gtc": float(self._raw["biosphere_soil_carbon_gtc"][i]),
            "active_geologic_carbon_gtc": float(self._raw["active_geologic_carbon_gtc"][i]),
            "temperature_raw_c": float(self._raw["temperature_raw_c"][i]),
            "ice_volume_index": float(self._raw["ice_volume_index"][i]),
            "overturning_strength": float(self._raw["overturning_strength"][i]),
        }

    def _advance(
        self,
        state: dict[str, float],
        previous_ice: float,
        previous_dt_years: float,
        target_year: float,
        dt_years: float,
        outer_end_year: int,
    ) -> tuple[dict[str, float], dict[str, float]]:
        summer = self._summer_at(target_year)
        canonical = float(np.asarray(_canonical_freshwater_pulse(target_year)))
        volcanic = self._volcanic_for_outer_interval(outer_end_year)
        melt_rate = max(0.0, (previous_ice - state["ice_volume_index"]) / previous_dt_years)
        freshwater = canonical + min(0.08, melt_rate * 100.0)
        overturning_eq = np.clip(1.0 - 3.3 * freshwater, 0.25, 1.0)
        tau_m = 150.0 if overturning_eq < state["overturning_strength"] else 650.0
        overturning = float(np.clip(
            state["overturning_strength"]
            + dt_years * (overturning_eq - state["overturning_strength"]) / tau_m,
            0.20,
            1.05,
        ))
        ppm = max(state["atmospheric_carbon_gtc"] / 2.12, 80.0)
        f_co2 = 5.35 * math.log(ppm / 280.0)
        f_ice = -3.8 * state["ice_volume_index"]
        f_orbit = 0.42 * summer
        f_overturning = -1.15 * (1.0 - overturning)
        f_aerosol = -4.0 * volcanic
        t_eq = 0.85 * (f_co2 + f_ice + f_orbit + f_overturning + f_aerosol)
        temp = state["temperature_raw_c"] + dt_years * (t_eq - state["temperature_raw_c"]) / 650.0
        cold_index = -1.55 * summer - 0.50 * temp - 0.15
        ice_eq = 1.0 / (1.0 + math.exp(-cold_index / 0.50))
        tau_i = 6000.0 if ice_eq > state["ice_volume_index"] else 950.0
        ice = float(np.clip(
            state["ice_volume_index"] + dt_years * (ice_eq - state["ice_volume_index"]) / tau_i,
            0.0,
            1.0,
        ))
        flux_volcanic = 0.080 * (1.0 + 0.30 * volcanic)
        flux_weathering = 0.080 * (ppm / 280.0) ** 0.32 * math.exp(0.040 * temp)
        atm_eq_ocean = 594.0 + 30.0 * temp + 10.0 * (1.0 - overturning)
        flux_airsea = (state["atmospheric_carbon_gtc"] - atm_eq_ocean) / 900.0
        atm_eq_bio = 594.0 + 6.0 * temp
        flux_biosphere = (state["atmospheric_carbon_gtc"] - atm_eq_bio) / 1000.0
        flux_fire = max(
            0.0,
            0.008 * (temp + 1.0) * (0.5 + self.nested_cfg.fire_susceptibility),
        )
        d_airsea = flux_airsea * dt_years
        d_bio = flux_biosphere * dt_years
        d_geo_atm = (flux_volcanic - flux_weathering) * dt_years
        d_fire = flux_fire * dt_years
        out = {
            "atmospheric_carbon_gtc": state["atmospheric_carbon_gtc"] - d_airsea - d_bio + d_geo_atm + d_fire,
            "ocean_carbon_gtc": state["ocean_carbon_gtc"] + d_airsea,
            "biosphere_soil_carbon_gtc": state["biosphere_soil_carbon_gtc"] + d_bio - d_fire,
            "active_geologic_carbon_gtc": state["active_geologic_carbon_gtc"] - d_geo_atm,
            "temperature_raw_c": float(temp),
            "ice_volume_index": ice,
            "overturning_strength": overturning,
        }
        diag = {
            "summer_ablation_forcing_index": float(summer),
            "canonical_freshwater_pulse_sv": float(canonical),
            "freshwater_forcing_sv": float(freshwater),
            "volcanic_aerosol_index": float(volcanic),
            "carbon_flux_volcanic_gtc_yr": float(flux_volcanic),
            "carbon_flux_weathering_gtc_yr": float(flux_weathering),
            "carbon_flux_airsea_gtc_yr": float(flux_airsea),
            "carbon_flux_biosphere_gtc_yr": float(flux_biosphere),
            "carbon_flux_fire_gtc_yr": float(flux_fire),
        }
        return out, diag

    def nested_state_vector(self, year_before_book: int, *, substep_years: float = 50.0) -> dict[str, float]:
        y = int(year_before_book)
        if y % 100 == 0:
            i = self._year_to_index[y]
            state = self._exact_state_vector(y)
            return self._decorate_global_state(state, y, i, exact_anchor=True, diag=None, substep_years=100.0)
        if not (
            self.nested_cfg.core_older_year_before_book < y < self.nested_cfg.core_younger_year_before_book
            and y % 50 == 0
        ):
            raise ValueError("requested C1 nested state lies outside the 15-11 ka 50-year midpoint grid")
        if substep_years <= 0 or abs(50.0 / substep_years - round(50.0 / substep_years)) > 1e-10:
            raise ValueError("diagnostic substep must divide the 50-year midpoint interval exactly")
        outer_start = (y // 100) * 100
        if outer_start == y:
            outer_start -= 100
        outer_end = outer_start + 100
        if y != outer_start + 50:
            raise ValueError("C1 exposes one 50-year midpoint per sealed 100-year interval")
        i0 = self._year_to_index[outer_start]
        state = self._exact_state_vector(outer_start)
        previous_ice = float(self._raw["ice_volume_index"][i0 - 1])
        previous_dt = 100.0
        n = int(round(50.0 / substep_years))
        diag: dict[str, float] | None = None
        for q in range(1, n + 1):
            target = outer_start + q * substep_years
            old_ice = state["ice_volume_index"]
            state, diag = self._advance(
                state,
                previous_ice,
                previous_dt,
                target,
                substep_years,
                outer_end,
            )
            previous_ice = old_ice
            previous_dt = substep_years
        return self._decorate_global_state(
            state,
            y,
            None,
            exact_anchor=False,
            diag=diag,
            substep_years=float(substep_years),
        )

    def predicted_outer_endpoint(self, outer_start_year: int, *, substep_years: float = 50.0) -> dict[str, float]:
        y0 = int(outer_start_year)
        if y0 not in self._year_to_index or y0 + 100 not in self._year_to_index:
            raise ValueError("outer interval must lie on sealed 100-year checkpoints")
        if y0 < self.nested_cfg.core_older_year_before_book or y0 >= self.nested_cfg.core_younger_year_before_book:
            raise ValueError("outer interval outside C1 core")
        if substep_years <= 0 or abs(100.0 / substep_years - round(100.0 / substep_years)) > 1e-10:
            raise ValueError("diagnostic substep must divide 100 years exactly")
        i0 = self._year_to_index[y0]
        state = self._exact_state_vector(y0)
        previous_ice = float(self._raw["ice_volume_index"][i0 - 1])
        previous_dt = 100.0
        diag: dict[str, float] | None = None
        n = int(round(100.0 / substep_years))
        for q in range(1, n + 1):
            target = y0 + q * substep_years
            old_ice = state["ice_volume_index"]
            state, diag = self._advance(
                state,
                previous_ice,
                previous_dt,
                target,
                substep_years,
                y0 + 100,
            )
            previous_ice = old_ice
            previous_dt = substep_years
        return self._decorate_global_state(
            state,
            y0 + 100,
            None,
            exact_anchor=False,
            diag=diag,
            substep_years=float(substep_years),
        )

    def _decorate_global_state(
        self,
        state: dict[str, float],
        year: int,
        sealed_index: int | None,
        *,
        exact_anchor: bool,
        diag: dict[str, float] | None,
        substep_years: float,
    ) -> dict[str, float]:
        raw_sea = -125.0 * state["ice_volume_index"] + 0.40 * state["temperature_raw_c"]
        out = dict(state)
        out.update({
            "year_before_book": int(year),
            "atmospheric_co2_ppm": state["atmospheric_carbon_gtc"] / 2.12,
            "global_temperature_anomaly_c": state["temperature_raw_c"] - self._sealed_book_raw_temp,
            "sea_level_anomaly_m": raw_sea - self._sealed_book_raw_sea,
            "total_tracked_carbon_gtc": (
                state["atmospheric_carbon_gtc"] + state["ocean_carbon_gtc"]
                + state["biosphere_soil_carbon_gtc"] + state["active_geologic_carbon_gtc"]
            ),
            "exact_sealed_100y_anchor": bool(exact_anchor),
            "nested_integration_substep_years": float(substep_years),
        })
        if exact_anchor and sealed_index is not None:
            out.update({
                "summer_ablation_forcing_index": float(self.history["summer_ablation_forcing_index"][sealed_index]),
                "canonical_freshwater_pulse_sv": float(self.history["canonical_freshwater_pulse_sv"][sealed_index]),
                "freshwater_forcing_sv": float(self.history["freshwater_forcing_sv"][sealed_index]),
                "volcanic_aerosol_index": float(self.history["volcanic_aerosol_index"][sealed_index]),
            })
        elif diag is not None:
            out.update(diag)
        return out

    def _spatial_from_global(self, global_state: dict[str, float]) -> dict[str, np.ndarray | float]:
        year = int(global_state["year_before_book"])
        # Exact anchors delegate to the existing C adapter byte-for-byte.
        if global_state["exact_sealed_100y_anchor"]:
            return self.base.state_at(abs(year) / 1_000_000.0)

        yd = np.clip((1.0 - global_state["overturning_strength"]) / 0.65, 0.0, 1.25)
        circulation_anom = (
            -5.5 * yd * self.base.north_zone * (0.35 + 0.65 * self.base.ocean_influence)
            + 0.45 * yd * self.base.south_zone
        )
        orbital_regional = 0.35 * (
            global_state["summer_ablation_forcing_index"] - self.base._summer_book
        ) * self.base.orbital_lat_factor
        dt_local = (
            global_state["global_temperature_anomaly_c"] * self.base.polar_amp
            + circulation_anom
            + orbital_regional
        )
        precip_hi = np.exp(0.035 * dt_local)
        precip_hi *= 1.0 - 0.27 * yd * self.base.north_zone + 0.08 * yd * self.base.south_zone
        precip_hi = np.clip(precip_hi, 0.45, 1.45)
        npp_hi = np.clip(np.exp(-np.abs(dt_local) / 12.0) * (precip_hi ** 0.45), 0.05, 1.35)
        land_hi = (self.base.elevation_m > global_state["sea_level_anomaly_m"]).astype(float)
        dt = conservative_nested_remap(
            dt_local.astype(np.float32), self.base.src_lat, self.base.src_lon, self.base.dst_lat, self.base.dst_lon
        )
        precip = conservative_nested_remap(
            precip_hi.astype(np.float32), self.base.src_lat, self.base.src_lon, self.base.dst_lat, self.base.dst_lon
        )
        npp = conservative_nested_remap(
            npp_hi.astype(np.float32), self.base.src_lat, self.base.src_lon, self.base.dst_lat, self.base.dst_lon
        )
        target_fraction = conservative_nested_remap(
            land_hi, self.base.src_lat, self.base.src_lon, self.base.dst_lat, self.base.dst_lon
        )
        bridge = _bridge_recent_relative_eustatic_anomaly(
            self.base.book_land,
            self.base.book_v061_fraction,
            target_fraction,
            self.base.dst_lat,
        )
        support = bridge.effective_land_support
        temp = self.base.book_temp + dt
        pet = np.exp(self.nested_cfg.pet_temperature_sensitivity_per_c * dt)
        aridity = np.maximum(
            self.base.book_aridity * np.maximum(precip, 0.0) / np.maximum(pet, self.nested_cfg.positive_floor),
            0.0,
        )
        browse = self.base.book_browse * np.maximum(npp, 0.0) * support
        low = self.base.book_low * np.maximum(npp, 0.0) * support
        wet = self.base.book_wet * np.maximum(npp, 0.0) * support
        total = browse + low + wet
        shelf = np.maximum(support - self.base.book_land, 0.0)
        return {
            "age_ma": abs(year) / 1_000_000.0,
            "model_seconds": int(age_ma_to_model_seconds(abs(year) / 1_000_000.0)),
            "year_before_book": year,
            "provider": "CHA2_NESTED_50Y_A1_ENVIRONMENTAL_PROVIDER_v0_6_4C1",
            "subprovider": "DERIVED_PHYSICAL_50Y_MIDPOINT_BETWEEN_SEALED_100Y_ANCHORS",
            "authority": AUTHORITY,
            "temperature_c": temp,
            "aridity_index": aridity,
            "browse_forage": browse,
            "low_forage": low,
            "wetland_forage": wet,
            "total_edible_forage": total,
            "land_support": support,
            "colonizable_shelf_support": shelf,
            "atmospheric_co2_ppm": float(global_state["atmospheric_co2_ppm"]),
            "global_temperature_anomaly_c": float(global_state["global_temperature_anomaly_c"]),
            "ice_volume_index": float(global_state["ice_volume_index"]),
            "sea_level_anomaly_m": float(global_state["sea_level_anomaly_m"]),
            "overturning_strength": float(global_state["overturning_strength"]),
            "freshwater_forcing_sv": float(global_state["freshwater_forcing_sv"]),
            "canonical_freshwater_pulse_sv": float(global_state["canonical_freshwater_pulse_sv"]),
            "summer_ablation_forcing_index": float(global_state["summer_ablation_forcing_index"]),
            "volcanic_aerosol_index": float(global_state["volcanic_aerosol_index"]),
            "exact_sealed_100y_anchor": False,
            "nested_50y_state": True,
            "stochastic_volcanism_resampled": False,
            "interpolated_from_sealed_checkpoints": False,
            "effective_land_bridge_diagnostics": bridge.diagnostics,
            "canonical_catastrophes_added": 0,
            "biology_modified": False,
            "Deep_adaptation_enabled": False,
            "sapience_enabled": False,
            "civilization_enabled": False,
        }

    def state_at_year(self, year_before_book: int) -> dict[str, Any]:
        y = int(year_before_book)
        if not self.supports_year(y):
            raise ValueError("C1 provider supports exact sealed 100-y recent checkpoints plus 50-y midpoints in 15-11 ka")
        if y % 100 == 0:
            return self.base.state_at(abs(y) / 1_000_000.0)
        return self._spatial_from_global(self.nested_state_vector(y, substep_years=50.0))

    def state_at(self, age_ma: float) -> dict[str, Any]:
        year = int(round(-float(age_ma) * 1_000_000.0))
        if abs(-float(age_ma) * 1_000_000.0 - year) > 1e-7:
            raise ValueError("C1 recent provider requires exact integer-year timestamps")
        return self.state_at_year(year)


class IntegratedLateCenozoicProviderC1:
    """v0.6.4C provider with only the CHA-2 50-y capability upgraded."""

    def __init__(
        self,
        a1: Mapping[str, Any],
        sealed_recent_root: Path,
        boundary_npz: Path,
        eustatic_npz: Path,
        cfg: IntegratedProviderConfig | None = None,
        nested_cfg: Nested50YConfig | None = None,
    ) -> None:
        self.base = IntegratedLateCenozoicProvider(a1, sealed_recent_root, boundary_npz, eustatic_npz, cfg)
        self.cfg = self.base.cfg
        self.nested = CHA2Nested50YRecentProvider(a1, sealed_recent_root, self.cfg, nested_cfg)

    def supports_age(self, age_ma: float) -> bool:
        age = float(age_ma)
        if age <= self.cfg.splice_age_ma + 1e-12:
            return self.nested.supports_age(age)
        return self.base.supports_age(age)

    def state_at(self, age_ma: float) -> dict[str, Any]:
        age = float(age_ma)
        if age <= self.cfg.splice_age_ma + 1e-12:
            out = self.nested.state_at(age)
            out = dict(out)
            out["restart_boundary_at_120ka"] = bool(abs(age - self.cfg.splice_age_ma) < 1e-12)
            out["pre_120ka_eustatic_chronology_claimed"] = False
            return out
        return self.base.state_at(age)
