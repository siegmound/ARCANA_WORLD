from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .environment import (
    LateCenozoicEnvironmentConfig,
    RecentBoundaryState,
    late_cenozoic_environment_state,
)
from .eustatic_land_bridge import (
    EustaticLandBridgeResult,
    bridge_relative_eustatic_anomaly,
    spherical_cell_weights,
)
from .sealed_120ka_boundary import (
    EXPECTED,
    conservative_nested_remap,
    load_materialized_a1_boundary,
    verify_v061_sealed_root,
)

STATUS = "PASS_INTEGRATED_LATE_CENOZOIC_PROVIDER_CANDIDATE_WITH_EXPLICIT_REPLAY_READINESS_BLOCKERS"
PROVIDER = "INTEGRATED_LATE_CENOZOIC_ENVIRONMENTAL_PROVIDER_v0_6_4C"
SECULAR_AUTHORITY = "v0.6.4A+B+B1+B2 CANDIDATE COMPOSITION"
RECENT_AUTHORITY = "v0.6.1 SEALED_PALEOCLIMATE_HISTORY"
SECONDS_PER_YEAR = 31_556_952  # exact D2.1.1 model-year convention (365.2425 d)


@dataclass(frozen=True)
class IntegratedProviderConfig:
    splice_age_ma: float = 0.12
    older_age_ma: float = 30.0
    recent_checkpoint_years: int = 100
    pet_temperature_sensitivity_per_c: float = 0.045
    positive_floor: float = 1e-8


def age_ma_to_model_seconds(age_ma: float) -> np.int64:
    """Signed exact model seconds relative to book era for integer-year ages.

    The late-Cenozoic/recent clock uses integer years at every materialized
    synchronization boundary, so conversion is exact and does not accumulate
    floating-point time drift.
    """
    years = float(age_ma) * 1_000_000.0
    rounded = int(round(years))
    if abs(years - rounded) > 1e-7:
        raise ValueError("age cannot be represented as an integer model year")
    seconds = -rounded * SECONDS_PER_YEAR
    return np.int64(seconds)


def model_seconds_to_age_ma(seconds: int | np.integer) -> float:
    s = int(seconds)
    if s > 0:
        raise ValueError("late-Cenozoic past state must have model seconds <= 0")
    if (-s) % SECONDS_PER_YEAR != 0:
        raise ValueError("model seconds do not lie on an exact model-year boundary")
    return ((-s) // SECONDS_PER_YEAR) / 1_000_000.0




def _bridge_recent_relative_eustatic_anomaly(
    book_land: np.ndarray,
    book_fraction: np.ndarray,
    target_fraction: np.ndarray,
    lat: np.ndarray,
) -> EustaticLandBridgeResult:
    """Apply B2 exactly when representable, retaining an explicit sub-grid ledger otherwise.

    B2 was calibrated on the -120 ka sea-level-fall boundary, where the full
    relative anomaly is representable on A1 shelf cells. The sealed recent
    history contains one very small sea-level-rise checkpoint (-100 y) whose
    high-resolution shoreline loss occurs wholly inside cells that A1 already
    classifies as ocean. A binary/coarse A1 support cannot become negative, so
    inventing distant land loss would be worse than retaining that component as
    an unresolved sub-grid shoreline ledger. All representable checkpoints still
    use the exact B2 conservative bridge.
    """
    try:
        return bridge_relative_eustatic_anomaly(book_land, book_fraction, target_fraction, lat)
    except ValueError as exc:
        base = np.asarray(book_land, dtype=float)
        f0 = np.asarray(book_fraction, dtype=float)
        ft = np.asarray(target_fraction, dtype=float)
        d = ft - f0
        w = spherical_cell_weights(np.asarray(lat, dtype=float), base.shape[1], normalize_mean=False)
        pos = np.maximum(d, 0.0)
        neg = np.maximum(-d, 0.0)
        pos_target = float((pos * w).sum())
        neg_target = float((neg * w).sum())
        representable_pos = bool(np.any((base < 0.5) & (pos > 0.0)))
        representable_neg = bool(np.any((base >= 0.5) & (neg > 0.0)))
        # The only lawful fallback is a purely sub-grid component with no A1
        # compatible cell. Never redistribute it to a remote coarse coastline.
        if pos_target > 1e-12 or neg_target <= 1e-12 or representable_neg:
            raise
        effective = base.copy()
        diagnostics = {
            "status": "PASS_SUBGRID_EUSTATIC_LEDGER_NO_COARSE_TOPOLOGY_EFFECT",
            "authority": "A1_TOPOLOGY_PLUS_v0.6.1_SUBGRID_SHORELINE_LEDGER",
            "book_endpoint_exact_by_construction": True,
            "positive_highres_area_anomaly": pos_target,
            "negative_highres_area_anomaly": neg_target,
            "positive_effective_area_anomaly": 0.0,
            "negative_effective_area_anomaly": 0.0,
            "positive_conservation_error": pos_target,
            "negative_conservation_error": neg_target,
            "net_conservation_error": neg_target,
            "unrepresented_subgrid_negative_area_anomaly": neg_target,
            "unrepresented_subgrid_positive_area_anomaly": 0.0,
            "coarse_topology_effect": False,
            "subgrid_ledger_preserved": True,
            "reason": str(exc),
            "absolute_v061_coastline_substituted": False,
            "canonical_events_added": 0,
            "biology_modified": False,
        }
        zeros = np.zeros_like(base)
        return EustaticLandBridgeResult(
            effective_land_support=effective,
            book_fraction=f0,
            target_fraction=ft,
            relative_fraction_anomaly=d,
            emergence_activation=zeros,
            submergence_activation=zeros,
            emergence_scale=0.0,
            submergence_scale=0.0,
            diagnostics=diagnostics,
        )

def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


def _periodic_distance_cells_to_true(mask: np.ndarray) -> np.ndarray:
    try:
        from scipy.ndimage import distance_transform_edt
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("scipy>=1.12 is required by the sealed recent spatial equations") from exc
    tiled = np.concatenate((mask, mask, mask), axis=1)
    d = distance_transform_edt(~tiled)
    nlon = mask.shape[1]
    return d[:, nlon:2*nlon]


class SealedRecentA1Provider:
    """Efficient exact-checkpoint adapter for the sealed v0.6.1 recent history.

    It caches only static geometry/factors. Dynamic equations and constants are
    identical to the sealed v0.6.1 spatial snapshot equations. No interpolation
    between the 100-year sealed history checkpoints is authorized here.
    """

    def __init__(
        self,
        a1: Mapping[str, Any],
        sealed_root: Path,
        cfg: IntegratedProviderConfig | None = None,
    ) -> None:
        self.cfg = cfg or IntegratedProviderConfig()
        self.a1 = a1
        self.root = Path(sealed_root)
        self.hashes = verify_v061_sealed_root(self.root)
        self.history = np.load(
            self.root / "outputs/hybrid1/paleoclimate_v0_6_1/recent_paleoclimate_history.npz",
            allow_pickle=False,
        )
        sh = np.load(self.root / "inputs/v0_5_5I_SEALED/shoreline_state_I.npz", allow_pickle=False)
        self.src_lat = np.asarray(sh["lat"], dtype=float)
        self.src_lon = np.asarray(sh["lon"], dtype=float)
        self.elevation_m = np.asarray(sh["elevation_m"], dtype=float)
        book_ocean = sh["ocean_mask"].astype(bool)

        dcell = _periodic_distance_cells_to_true(book_ocean)
        dy_km = 111.195 * 0.25
        coslat = np.maximum(np.cos(np.deg2rad(self.src_lat))[:, None], 0.08)
        distance_ocean_km = dcell * dy_km * np.sqrt(coslat)
        self.ocean_influence = np.exp(-distance_ocean_km / 900.0)
        lat2 = self.src_lat[:, None]
        abs_lat = np.abs(lat2)
        self.polar_amp = 1.0 + 0.55 * (abs_lat / 90.0) ** 1.5
        self.north_zone = _sigmoid((lat2 - 28.0) / 6.0) * _sigmoid((79.0 - lat2) / 7.0)
        self.south_zone = _sigmoid((-lat2 - 32.0) / 9.0) * _sigmoid((72.0 + lat2) / 8.0)
        self.orbital_lat_factor = (abs_lat / 90.0) ** 1.2

        self.dst_lat = np.asarray(a1["lat"], dtype=float)
        self.dst_lon = np.asarray(a1["lon"], dtype=float)
        ages = np.asarray(a1["age_ma"], dtype=float)
        self.i0 = int(np.where(np.isclose(ages, 0.0))[0][0])
        self.book_land = np.asarray(a1["land_mask"][self.i0], dtype=float)
        self.book_temp = np.asarray(a1["temperature_c"][self.i0], dtype=float)
        self.book_aridity = np.asarray(a1["aridity_index"][self.i0], dtype=float)
        self.book_browse = np.asarray(a1["browse_forage"][self.i0], dtype=float)
        self.book_low = np.asarray(a1["low_forage"][self.i0], dtype=float)
        self.book_wet = np.asarray(a1["wetland_forage"][self.i0], dtype=float)

        self.time_years = np.asarray(self.history["time_year_before_book"], dtype=float)
        if self.time_years.size < 2 or not np.allclose(np.diff(self.time_years), self.cfg.recent_checkpoint_years):
            raise ValueError("sealed v0.6.1 recent history is not on the expected 100-year grid")
        self._year_to_index = {int(round(float(y))): i for i, y in enumerate(self.time_years)}
        self._summer_book = float(self.history["summer_ablation_forcing_index"][-1])

        # Book-era shoreline fraction in A1 cells is the reference for every
        # relative eustatic bridge operation.
        land_book_hi = (self.elevation_m > float(self.history["sea_level_anomaly_m"][-1])).astype(float)
        self.book_v061_fraction = conservative_nested_remap(
            land_book_hi, self.src_lat, self.src_lon, self.dst_lat, self.dst_lon
        )

    def supports_age(self, age_ma: float, *, tol_years: float = 1e-6) -> bool:
        if age_ma < -1e-12 or age_ma > self.cfg.splice_age_ma + 1e-12:
            return False
        years = -float(age_ma) * 1_000_000.0
        y = int(round(years))
        return abs(years - y) <= tol_years and y in self._year_to_index

    def _index_for_age(self, age_ma: float) -> tuple[int, int]:
        if not self.supports_age(age_ma):
            raise ValueError(
                "v0.6.1 SEALED recent provider exposes exact state only on its 100-year checkpoints; "
                "intermediate-time interpolation is not authorized"
            )
        year = int(round(-float(age_ma) * 1_000_000.0))
        return self._year_to_index[year], year

    def _spatial_highres(self, i: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        summer = self.history["summer_ablation_forcing_index"]
        m = self.history["overturning_strength"]
        global_t = self.history["global_temperature_anomaly_c"]
        sea = self.history["sea_level_anomaly_m"]
        yd = np.clip((1.0 - m[i]) / 0.65, 0.0, 1.25)
        circulation_anom = (
            -5.5 * yd * self.north_zone * (0.35 + 0.65 * self.ocean_influence)
            + 0.45 * yd * self.south_zone
        )
        orbital_regional = 0.35 * (summer[i] - self._summer_book) * self.orbital_lat_factor
        dt_local = global_t[i] * self.polar_amp + circulation_anom + orbital_regional
        pf = np.exp(0.035 * dt_local)
        pf *= 1.0 - 0.27 * yd * self.north_zone + 0.08 * yd * self.south_zone
        pf = np.clip(pf, 0.45, 1.45)
        nf = np.clip(np.exp(-np.abs(dt_local) / 12.0) * (pf ** 0.45), 0.05, 1.35)
        land = (self.elevation_m > sea[i]).astype(float)
        return (
            dt_local.astype(np.float32),
            pf.astype(np.float32),
            nf.astype(np.float32),
            land,
        )

    def state_at(self, age_ma: float) -> dict[str, Any]:
        i, year = self._index_for_age(age_ma)
        dt_hi, precip_hi, npp_hi, land_hi = self._spatial_highres(i)
        dt = conservative_nested_remap(dt_hi, self.src_lat, self.src_lon, self.dst_lat, self.dst_lon)
        precip = conservative_nested_remap(precip_hi, self.src_lat, self.src_lon, self.dst_lat, self.dst_lon)
        npp = conservative_nested_remap(npp_hi, self.src_lat, self.src_lon, self.dst_lat, self.dst_lon)
        target_fraction = conservative_nested_remap(
            land_hi, self.src_lat, self.src_lon, self.dst_lat, self.dst_lon
        )
        bridge = _bridge_recent_relative_eustatic_anomaly(
            self.book_land,
            self.book_v061_fraction,
            target_fraction,
            self.dst_lat,
        )
        support = bridge.effective_land_support
        temp = self.book_temp + dt
        pet = np.exp(self.cfg.pet_temperature_sensitivity_per_c * dt)
        # B1 used a provisional upper cap of 3.0 on this derived A1 aridity
        # bridge. C removes that non-authoritative cap because it is not
        # endpoint-compatible with the A1 book-era field (whose valid range
        # extends above 3). This remains a derived bridge; v0.6.1 SEALED is
        # untouched.
        aridity = np.maximum(
            self.book_aridity * np.maximum(precip, 0.0) / np.maximum(pet, self.cfg.positive_floor),
            0.0,
        )
        # Environmental forage on established A1 land follows the sealed NPP
        # factor. Newly activated shelves are exposed/colonizable support but do
        # not receive invented mature vegetation. Their colonization belongs to
        # the later ecology/replay layer.
        browse = self.book_browse * np.maximum(npp, 0.0) * support
        low = self.book_low * np.maximum(npp, 0.0) * support
        wet = self.book_wet * np.maximum(npp, 0.0) * support
        total = browse + low + wet
        shelf = np.maximum(support - self.book_land, 0.0)

        # Book era is an independently authoritative A1 spatial endpoint.
        # The sealed v0.6.1 spatial equations approach it to floating-point
        # roundoff, but their stored global state is not intended to replace
        # A1's exact book-era raster. Force exact endpoint identity here, just
        # as the secular provider preserves the exact 30 Ma endpoint.
        book_endpoint_override = (year == 0)
        if book_endpoint_override:
            temp = self.book_temp.copy()
            aridity = self.book_aridity.copy()
            browse = self.book_browse.copy()
            low = self.book_low.copy()
            wet = self.book_wet.copy()
            total = browse + low + wet
            support = self.book_land.copy()
            shelf = np.zeros_like(self.book_land, dtype=float)

        return {
            "age_ma": float(age_ma),
            "model_seconds": int(age_ma_to_model_seconds(age_ma)),
            "year_before_book": int(year),
            "provider": PROVIDER,
            "subprovider": "SEALED_v0_6_1_EXACT_100Y_CHECKPOINT_A1_ADAPTER",
            "authority": RECENT_AUTHORITY,
            "temperature_c": temp,
            "aridity_index": aridity,
            "browse_forage": browse,
            "low_forage": low,
            "wetland_forage": wet,
            "total_edible_forage": total,
            "land_support": support,
            "colonizable_shelf_support": shelf,
            "atmospheric_co2_ppm": float(self.history["atmospheric_co2_ppm"][i]),
            "global_temperature_anomaly_c": float(self.history["global_temperature_anomaly_c"][i]),
            "sea_level_anomaly_m": float(self.history["sea_level_anomaly_m"][i]),
            "overturning_strength": float(self.history["overturning_strength"][i]),
            "freshwater_forcing_sv": float(self.history["freshwater_forcing_sv"][i]),
            "canonical_freshwater_pulse_sv": float(self.history["canonical_freshwater_pulse_sv"][i]),
            "summer_ablation_forcing_index": float(self.history["summer_ablation_forcing_index"][i]),
            "recent_checkpoint_spacing_years": int(self.cfg.recent_checkpoint_years),
            "intermediate_recent_state_interpolated": False,
            "book_era_A1_spatial_endpoint_override": bool(book_endpoint_override),
            "B1_provisional_aridity_cap_used": False,
            "effective_land_bridge_diagnostics": bridge.diagnostics,
            "canonical_catastrophes_added": 0,
            "biology_modified": False,
            "Deep_adaptation_enabled": False,
            "sapience_enabled": False,
            "civilization_enabled": False,
        }


class IntegratedLateCenozoicProvider:
    """Single environmental API for 30 Ma -> book era.

    30 Ma > age > 120 ka uses the v0.6.4A/B reduced-order secular provider
    bound to the exact B1/B2 restart boundary. At and after 120 ka authority is
    delegated to exact checkpoints of sealed v0.6.1, remapped conservatively to
    A1 and with only relative eustatic shoreline change transferred to A1.
    """

    def __init__(
        self,
        a1: Mapping[str, Any],
        sealed_recent_root: Path,
        boundary_npz: Path,
        eustatic_npz: Path,
        cfg: IntegratedProviderConfig | None = None,
    ) -> None:
        self.cfg = cfg or IntegratedProviderConfig()
        self.a1 = a1
        self.recent = SealedRecentA1Provider(a1, sealed_recent_root, self.cfg)
        boundary = load_materialized_a1_boundary(boundary_npz)
        ez = np.load(Path(eustatic_npz), allow_pickle=False)
        eff = np.asarray(ez["effective_land_support_120ka"], dtype=float)
        if eff.shape != boundary.paleo_land_mask.shape:
            raise ValueError("B2 effective-land boundary shape mismatch")
        # Reconstruct the exact recent state at 120 ka through the integrated
        # provider and use it as the governed secular restart boundary. This
        # prevents divergent duplicate formulas in C.
        recent_boundary_state = self.recent.state_at(self.cfg.splice_age_ma)
        self.boundary = RecentBoundaryState(
            age_ma=self.cfg.splice_age_ma,
            atmospheric_co2_ppm=float(recent_boundary_state["atmospheric_co2_ppm"]),
            temperature_c=np.asarray(recent_boundary_state["temperature_c"], dtype=float),
            aridity_index=np.asarray(recent_boundary_state["aridity_index"], dtype=float),
            browse_forage=np.asarray(recent_boundary_state["browse_forage"], dtype=float),
            low_forage=np.asarray(recent_boundary_state["low_forage"], dtype=float),
            wetland_forage=np.asarray(recent_boundary_state["wetland_forage"], dtype=float),
            total_edible_forage=np.asarray(recent_boundary_state["total_edible_forage"], dtype=float),
            paleo_land_mask=eff,
            source_history_sha256=EXPECTED["recent_history"],
            source_spatial_sha256=EXPECTED["spatial_snapshots"],
            exact_payload_verified=True,
            provenance="v0.6.4C_GOVERNED_120KA_RESTART_BOUNDARY_FROM_B1+B2+SEALED_v0.6.1",
        )
        if not np.array_equal(np.asarray(recent_boundary_state["land_support"]), eff):
            if float(np.max(np.abs(np.asarray(recent_boundary_state["land_support"]) - eff))) > 1e-12:
                raise ValueError("integrated recent 120 ka effective land does not reproduce materialized B2 boundary")

    def supports_age(self, age_ma: float) -> bool:
        age = float(age_ma)
        if age < -1e-12 or age > self.cfg.older_age_ma + 1e-12:
            return False
        if age <= self.cfg.splice_age_ma + 1e-12:
            return self.recent.supports_age(age)
        return True

    def state_at(self, age_ma: float) -> dict[str, Any]:
        age = float(age_ma)
        if age < -1e-12 or age > self.cfg.older_age_ma + 1e-12:
            raise ValueError("age outside integrated late-Cenozoic provider domain")
        if age <= self.cfg.splice_age_ma + 1e-12:
            out = self.recent.state_at(age)
            out["restart_boundary_at_120ka"] = bool(abs(age - self.cfg.splice_age_ma) < 1e-12)
            out["pre_120ka_eustatic_chronology_claimed"] = False
            return out
        out = late_cenozoic_environment_state(
            self.a1,
            age,
            boundary=self.boundary,
            cfg=LateCenozoicEnvironmentConfig(splice_ma=self.cfg.splice_age_ma),
        )
        out = dict(out)
        out["provider"] = PROVIDER
        out["subprovider"] = "v0.6.4A+B_SECULAR_ENVIRONMENT"
        out["authority"] = SECULAR_AUTHORITY
        out["model_seconds"] = int(age_ma_to_model_seconds(age))
        out["restart_boundary_at_120ka"] = False
        out["pre_120ka_eustatic_chronology_claimed"] = False
        return out
