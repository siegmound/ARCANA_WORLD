from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from .paleogeography import (
    LateCenozoicPaleogeographyConfig,
    land_support_at_age,
)

STATUS = "PASS_LATE_CENOZOIC_PHYSICAL_CLIMATE_FLORA_PROVIDER_CANDIDATE_SPLICE_BINDING_REQUIRED"
PROVIDER = "ENDPOINT_CONSTRAINED_REDUCED_ORDER_LATE_CENOZOIC_ENVIRONMENT_v0_6_4B"
RECENT_AUTHORITY = "v0.6.1 SEALED_PALEOCLIMATE_HISTORY"

# Exact payload hashes frozen by the v0.6.1 authorial seal manifest.
SEALED_RECENT_HISTORY_SHA256 = "be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1"
SEALED_SPATIAL_SNAPSHOTS_SHA256 = "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd"

# v0.6.2-C is a candidate prior, not an authority.  Only its 30 Ma secular
# greenhouse anchor is reused here as a prior calibration point.
CO2_30MA_PRIOR_PPM = 380.63601734093106
BOOK_ERA_CO2_REFERENCE_PPM = 286.1


@dataclass(frozen=True)
class LateCenozoicEnvironmentConfig:
    older_ma: float = 30.0
    splice_ma: float = 0.12
    secular_relaxation_timescale_ma: float = 20.0
    co2_30ma_prior_ppm: float = CO2_30MA_PRIOR_PPM
    co2_preview_splice_ppm: float = BOOK_ERA_CO2_REFERENCE_PPM
    pet_temperature_sensitivity_per_c: float = 0.045
    positive_floor: float = 1e-8
    recent_history_sha256: str = SEALED_RECENT_HISTORY_SHA256
    recent_spatial_sha256: str = SEALED_SPATIAL_SNAPSHOTS_SHA256


@dataclass(frozen=True)
class RecentBoundaryState:
    """Exact/derived environmental state at the governed -120 ka splice.

    The climate scalars/maps must originate from the sealed v0.6.1 payload.
    The aridity/forage arrays are allowed to be deterministic bridge fields
    derived from the sealed climate multipliers and the frozen v0.6 ecological
    reference, but their provenance must remain explicit.
    """

    age_ma: float
    atmospheric_co2_ppm: float
    temperature_c: np.ndarray
    aridity_index: np.ndarray
    browse_forage: np.ndarray
    low_forage: np.ndarray
    wetland_forage: np.ndarray
    total_edible_forage: np.ndarray
    paleo_land_mask: np.ndarray
    source_history_sha256: str
    source_spatial_sha256: str
    exact_payload_verified: bool = False
    provenance: str = "SEALED_V0_6_1_BOUNDARY_DERIVED_BRIDGE"


def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_sealed_recent_payload(history_path: Path, spatial_path: Path,
                                 cfg: LateCenozoicEnvironmentConfig | None = None) -> dict[str, Any]:
    cfg = cfg or LateCenozoicEnvironmentConfig()
    history_path = Path(history_path)
    spatial_path = Path(spatial_path)
    if not history_path.is_file() or not spatial_path.is_file():
        raise FileNotFoundError("Both sealed v0.6.1 NPZ payload files are required for the exact 120 ka splice")
    hh = _sha256_file(history_path)
    sh = _sha256_file(spatial_path)
    if hh != cfg.recent_history_sha256:
        raise ValueError(f"recent_paleoclimate_history.npz SHA256 mismatch: {hh}")
    if sh != cfg.recent_spatial_sha256:
        raise ValueError(f"paleoclimate_spatial_snapshots.npz SHA256 mismatch: {sh}")
    return {
        "history_sha256": hh,
        "spatial_sha256": sh,
        "authority": RECENT_AUTHORITY,
        "exact_payload_verified": True,
    }


def _find_key(npz: Mapping[str, Any], aliases: tuple[str, ...]) -> str:
    keys = set(npz.keys())
    for k in aliases:
        if k in keys:
            return k
    raise KeyError(f"None of required aliases present: {aliases}; available={sorted(keys)}")


def _select_time_index(values: np.ndarray, target_year: float) -> int:
    vals = np.asarray(values, dtype=float).reshape(-1)
    # Accept either years relative to book era (-120000..0), years before book
    # (120000..0), or age Ma (0.12..0).
    candidates = [target_year, abs(target_year), abs(target_year) / 1e6]
    errors = [np.abs(vals - c) for c in candidates]
    which = np.argmin([float(e.min()) for e in errors])
    idx = int(np.argmin(errors[which]))
    if float(errors[which][idx]) > (1e-6 if which == 2 else 1.0):
        raise ValueError("Sealed payload does not expose an exact -120 ka boundary checkpoint")
    return idx


def bind_recent_boundary_from_sealed_payload(
    a1: Mapping[str, Any], history_path: Path, spatial_path: Path,
    cfg: LateCenozoicEnvironmentConfig | None = None,
) -> RecentBoundaryState:
    """Bind the exact v0.6.1 -120 ka climate checkpoint to the 2-degree ecology grid.

    This is intentionally schema-tolerant but hash-strict.  If the sealed NPZ
    schema does not expose the documented fields, the adapter fails rather than
    inventing them.
    """
    cfg = cfg or LateCenozoicEnvironmentConfig()
    proof = verify_sealed_recent_payload(history_path, spatial_path, cfg)
    h = np.load(history_path, allow_pickle=False)
    s = np.load(spatial_path, allow_pickle=False)

    hk_time = _find_key(h, ("year", "years", "relative_year", "year_before_book", "years_before_book", "age_ma"))
    hi = _select_time_index(h[hk_time], -120_000.0)
    hk_co2 = _find_key(h, ("atmospheric_co2_ppm", "co2_ppm", "CO2_ppm"))
    co2 = float(np.asarray(h[hk_co2])[hi])

    sk_time = _find_key(s, ("year", "years", "relative_year", "year_before_book", "years_before_book", "age_ma", "snapshot_year"))
    si = _select_time_index(s[sk_time], -120_000.0)
    k_t = _find_key(s, ("local_temperature_anomaly_c", "temperature_anomaly_c", "local_temp_anomaly_c"))
    k_p = _find_key(s, ("precipitation_multiplier", "precip_multiplier"))
    k_npp = _find_key(s, ("potential_npp_multiplier", "npp_multiplier"))
    k_land = _find_key(s, ("paleo_land_mask", "land_mask"))

    ages = np.asarray(a1["age_ma"], dtype=float)
    i0 = int(np.where(np.isclose(ages, 0.0))[0][0])
    t0 = np.asarray(a1["temperature_c"][i0], dtype=float)
    a0 = np.asarray(a1["aridity_index"][i0], dtype=float)
    b0 = np.asarray(a1["browse_forage"][i0], dtype=float)
    l0 = np.asarray(a1["low_forage"][i0], dtype=float)
    w0 = np.asarray(a1["wetland_forage"][i0], dtype=float)

    dt = np.asarray(s[k_t][si], dtype=float)
    precip = np.asarray(s[k_p][si], dtype=float)
    npp = np.asarray(s[k_npp][si], dtype=float)
    land = np.asarray(s[k_land][si], dtype=float)
    target_shape = t0.shape
    for name, arr in (("temperature anomaly", dt), ("precipitation multiplier", precip),
                      ("NPP multiplier", npp), ("paleo land", land)):
        if arr.shape != target_shape:
            raise ValueError(
                f"Sealed v0.6.1 {name} shape {arr.shape} cannot be silently resampled to A1 {target_shape}; "
                "an explicit conservative remap stage is required"
            )

    temp = t0 + dt
    pet_mult = np.exp(cfg.pet_temperature_sensitivity_per_c * dt)
    aridity = np.clip(a0 * np.maximum(precip, 0.0) / np.maximum(pet_mult, cfg.positive_floor), 0.0, 3.0)
    npp = np.maximum(npp, 0.0)
    browse = b0 * npp * land
    low = l0 * npp * land
    wet = w0 * npp * land
    total = browse + low + wet
    return RecentBoundaryState(
        age_ma=cfg.splice_ma,
        atmospheric_co2_ppm=co2,
        temperature_c=temp,
        aridity_index=aridity,
        browse_forage=browse,
        low_forage=low,
        wetland_forage=wet,
        total_edible_forage=total,
        paleo_land_mask=land,
        source_history_sha256=proof["history_sha256"],
        source_spatial_sha256=proof["spatial_sha256"],
        exact_payload_verified=True,
    )


def preview_boundary_from_book_reference(a1: Mapping[str, Any],
                                         cfg: LateCenozoicEnvironmentConfig | None = None) -> RecentBoundaryState:
    """Non-authoritative development boundary used only for local calibration tests."""
    cfg = cfg or LateCenozoicEnvironmentConfig()
    ages = np.asarray(a1["age_ma"], dtype=float)
    i0 = int(np.where(np.isclose(ages, 0.0))[0][0])
    return RecentBoundaryState(
        age_ma=cfg.splice_ma,
        atmospheric_co2_ppm=cfg.co2_preview_splice_ppm,
        temperature_c=np.asarray(a1["temperature_c"][i0], dtype=float).copy(),
        aridity_index=np.asarray(a1["aridity_index"][i0], dtype=float).copy(),
        browse_forage=np.asarray(a1["browse_forage"][i0], dtype=float).copy(),
        low_forage=np.asarray(a1["low_forage"][i0], dtype=float).copy(),
        wetland_forage=np.asarray(a1["wetland_forage"][i0], dtype=float).copy(),
        total_edible_forage=np.asarray(a1["total_edible_forage"][i0], dtype=float).copy(),
        paleo_land_mask=np.asarray(a1["land_mask"][i0], dtype=float).copy(),
        source_history_sha256="UNBOUND_PREVIEW",
        source_spatial_sha256="UNBOUND_PREVIEW",
        exact_payload_verified=False,
        provenance="NON_AUTHORITATIVE_BOOK_ERA_PROXY_FOR_CALIBRATION_ONLY",
    )


def secular_relaxation_phase(age_ma: float, cfg: LateCenozoicEnvironmentConfig | None = None) -> float:
    """Normalized solution phase of a first-order secular relaxation process.

    0 at 30 Ma and 1 at 120 ka. It is deliberately not linear in frame/time.
    """
    cfg = cfg or LateCenozoicEnvironmentConfig()
    age = float(age_ma)
    if age < cfg.splice_ma - 1e-12 or age > cfg.older_ma + 1e-12:
        raise ValueError("secular phase is defined only on 30 Ma -> 120 ka")
    elapsed = cfg.older_ma - age
    duration = cfg.older_ma - cfg.splice_ma
    tau = cfg.secular_relaxation_timescale_ma
    if tau <= 0:
        raise ValueError("secular_relaxation_timescale_ma must be positive")
    den = 1.0 - np.exp(-duration / tau)
    return float((1.0 - np.exp(-elapsed / tau)) / den)


def _positive_relax(old: np.ndarray, new: np.ndarray, phase: float, floor: float) -> np.ndarray:
    """First-order relaxation in positive log-state space, endpoint exact."""
    old = np.asarray(old, dtype=float)
    new = np.asarray(new, dtype=float)
    # Preserve exact zero topology through a separate land-support multiplication;
    # this interpolation is only for positive environmental amplitudes.
    lo = np.log(np.maximum(old, floor))
    ln = np.log(np.maximum(new, floor))
    return np.exp((1.0 - phase) * lo + phase * ln)


def _co2_at_age(age_ma: float, boundary: RecentBoundaryState,
                cfg: LateCenozoicEnvironmentConfig) -> float:
    p = secular_relaxation_phase(age_ma, cfg)
    # Secular weathering/outgassing-regulator relaxation in log concentration.
    return float(np.exp((1.0 - p) * np.log(cfg.co2_30ma_prior_ppm) + p * np.log(boundary.atmospheric_co2_ppm)))


def late_cenozoic_environment_state(
    a1: Mapping[str, Any], age_ma: float,
    boundary: RecentBoundaryState | None = None,
    cfg: LateCenozoicEnvironmentConfig | None = None,
    recent_provider: Callable[[float], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Materialize 30 Ma -> 120 ka environment, then hand off to v0.6.1.

    For ages <=120 ka this function refuses to extrapolate the secular provider:
    it delegates to the supplied recent provider or returns a strict handoff
    marker. This protects the sealed v0.6.1 trajectory from silent replacement.
    """
    cfg = cfg or LateCenozoicEnvironmentConfig()
    age = float(age_ma)
    if age < -1e-12 or age > cfg.older_ma + 1e-12:
        raise ValueError(f"Age {age} Ma outside 30 Ma -> book era vertical-provider domain")
    if age <= cfg.splice_ma + 1e-12:
        if recent_provider is not None:
            out = dict(recent_provider(age))
            out.setdefault("age_ma", age)
            out["authority"] = RECENT_AUTHORITY
            out["provider"] = "DELEGATED_SEALED_RECENT_PALEOCLIMATE"
            out["v0_6_4B_secular_provider_used"] = False
            return out
        return {
            "age_ma": age,
            "provider": "STRICT_120KA_HANDOFF",
            "status": STATUS,
            "authority": RECENT_AUTHORITY,
            "exact_recent_payload_required": True,
            "v0_6_4B_secular_provider_used": False,
        }

    if boundary is None:
        boundary = preview_boundary_from_book_reference(a1, cfg)
    phase = secular_relaxation_phase(age, cfg)
    support, sched = land_support_at_age(a1, age, LateCenozoicPaleogeographyConfig())
    ages = np.asarray(a1["age_ma"], dtype=float)
    i30 = int(np.where(np.isclose(ages, 30.0))[0][0])

    t30 = np.asarray(a1["temperature_c"][i30], dtype=float)
    a30 = np.asarray(a1["aridity_index"][i30], dtype=float)
    b30 = np.asarray(a1["browse_forage"][i30], dtype=float)
    l30 = np.asarray(a1["low_forage"][i30], dtype=float)
    w30 = np.asarray(a1["wetland_forage"][i30], dtype=float)

    co2 = _co2_at_age(age, boundary, cfg)
    c30 = cfg.co2_30ma_prior_ppm
    cb = boundary.atmospheric_co2_ppm
    forcing30 = 5.35 * np.log(c30 / cb)
    forcing = 5.35 * np.log(co2 / cb)
    land30 = np.asarray(a1["land_mask"][i30], dtype=float)
    landb = np.asarray(boundary.paleo_land_mask, dtype=float)
    if float(land30.sum()) > 0 and float(landb.sum()) > 0 and abs(forcing30) > 1e-12:
        mean30 = float(np.average(t30, weights=land30))
        mean_boundary = float(np.average(boundary.temperature_c, weights=landb))
        lambda_eff = (mean30 - mean_boundary) / forcing30
    else:
        lambda_eff = 0.0
        mean_boundary = float(np.mean(boundary.temperature_c))
    # CO2 radiative component + decaying spatial/geographic residual.  The
    # residual carries spatial structure but is recentered at every age so it
    # cannot create an unsupported global-temperature overshoot/undershoot.
    co2_base = boundary.temperature_c + lambda_eff * forcing
    residual30 = t30 - (boundary.temperature_c + lambda_eff * forcing30)
    raw_temp = co2_base + (1.0 - phase) * residual30
    weight = np.maximum(support, 0.0)
    target_mean = mean_boundary + lambda_eff * forcing
    if float(weight.sum()) > 0:
        raw_mean = float(np.average(raw_temp, weights=weight))
        temp = raw_temp + (target_mean - raw_mean)
    else:
        temp = raw_temp

    # Hydrology/flora use the same first-order secular phase, but the spatial
    # endpoint patterns are mixed in amplitude space rather than cellwise log
    # space.  This avoids a false global productivity collapse when a 30 Ma
    # hotspot and its recent analogue occupy different Eulerian cells. Global
    # means are explicitly constrained to the endpoint relaxation trajectory.
    land30 = np.asarray(a1["land_mask"][i30], dtype=float)
    landb = np.asarray(boundary.paleo_land_mask, dtype=float)

    raw_aridity = ((1.0 - phase) * a30 + phase * boundary.aridity_index) * support
    mean_a30 = float(np.average(a30, weights=land30))
    mean_ab = float(np.average(boundary.aridity_index, weights=landb))
    target_aridity_mean = (1.0 - phase) * mean_a30 + phase * mean_ab
    raw_a_mean = float(np.average(raw_aridity, weights=support)) if float(support.sum()) > 0 else 0.0
    if raw_a_mean > cfg.positive_floor:
        raw_aridity *= target_aridity_mean / raw_a_mean
    aridity = np.maximum(raw_aridity, 0.0)

    raw_browse = ((1.0 - phase) * b30 + phase * boundary.browse_forage) * support
    raw_low = ((1.0 - phase) * l30 + phase * boundary.low_forage) * support
    raw_wet = ((1.0 - phase) * w30 + phase * boundary.wetland_forage) * support
    raw_total = raw_browse + raw_low + raw_wet
    f30 = np.asarray(a1["total_edible_forage"][i30], dtype=float)
    mean_f30 = float(np.average(f30, weights=land30))
    mean_fb = float(np.average(boundary.total_edible_forage, weights=landb))
    target_forage_mean = float(np.exp((1.0 - phase) * np.log(max(mean_f30, cfg.positive_floor))
                                      + phase * np.log(max(mean_fb, cfg.positive_floor))))
    raw_f_mean = float(np.average(raw_total, weights=support)) if float(support.sum()) > 0 else 0.0
    scale = target_forage_mean / raw_f_mean if raw_f_mean > cfg.positive_floor else 0.0
    browse = raw_browse * scale
    low = raw_low * scale
    wet = raw_wet * scale
    total = browse + low + wet

    # Exact 30 Ma endpoint override avoids floor pollution in ocean cells.
    if abs(age - cfg.older_ma) < 1e-12:
        support = np.asarray(a1["land_mask"][i30], dtype=float).copy()
        temp = t30.copy(); aridity = a30.copy()
        browse = b30.copy(); low = l30.copy(); wet = w30.copy()
        total = np.asarray(a1["total_edible_forage"][i30], dtype=float).copy()
        co2 = cfg.co2_30ma_prior_ppm

    bound = bool(boundary.exact_payload_verified)
    return {
        "age_ma": age,
        "provider": PROVIDER,
        "status": STATUS,
        "authority": "v0.6.4B CANDIDATE",
        "land_support": support,
        "temperature_c": temp,
        "aridity_index": aridity,
        "browse_forage": browse,
        "low_forage": low,
        "wetland_forage": wet,
        "total_edible_forage": total,
        "atmospheric_co2_ppm": co2,
        "secular_relaxation_phase": phase,
        "effective_co2_temperature_response_c_per_wm2": lambda_eff,
        "event_diagnostics": sched["diagnostics"],
        "exact_v0_6_1_boundary_bound": bound,
        "boundary_provenance": boundary.provenance,
        "splice_age_ma": cfg.splice_ma,
        "canonical_catastrophes_added": 0,
        "biology_modified": False,
        "Deep_adaptation_enabled": False,
        "sapience_enabled": False,
        "civilization_enabled": False,
    }
