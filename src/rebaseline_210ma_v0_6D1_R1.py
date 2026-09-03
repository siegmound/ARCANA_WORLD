from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json
import math
import numpy as np

STATUS = "PASS_210MA_CANONICAL_REBASELINE_AND_PAIRED_H0_HX_INITIALIZATION_CANDIDATE"
MODES = ("E", "th", "p", "I", "N")
LATENT_TRAITS = (
    "coupling_E", "coupling_th", "coupling_p", "coupling_I", "coupling_N",
    "uptake", "regulation", "tolerance", "plasticity", "repair",
)

@dataclass(frozen=True)
class RebaselineConfig:
    age_ma: float = 210.0
    compatibility_radius_km: float = 6371.0088
    compact_range_sigma: float = 3.25
    patch_floor: float = 0.05
    latent_va_equilibrium: float = 0.045
    photo_additive_share_E_th: float = 0.05
    paired_rng_seed: int = 917231
    mutation_variance_supply_per_myr: float = 0.002
    nonlinear_variance_depletion_per_myr_per_q: float = 0.9876543209876544

    def validate(self) -> None:
        if not math.isclose(self.age_ma, 210.0, abs_tol=1e-12):
            raise ValueError("R1 is defined only at 210 Ma")
        if self.compatibility_radius_km <= 0 or self.compact_range_sigma <= 0:
            raise ValueError("invalid spatial compatibility parameters")
        if not 0 < self.patch_floor <= 1:
            raise ValueError("invalid patch floor")
        if not 0 <= self.latent_va_equilibrium <= 0.05:
            raise ValueError("invalid latent VA")
        if not 0 <= self.photo_additive_share_E_th <= 1:
            raise ValueError("invalid photo share")
        qstar = math.sqrt(self.mutation_variance_supply_per_myr / self.nonlinear_variance_depletion_per_myr_per_q)
        if not math.isclose(qstar, self.latent_va_equilibrium, rel_tol=0, abs_tol=1e-15):
            raise ValueError("latent VA must equal the D3.3A zero-selection homeostatic equilibrium")


def _stable_json(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def semantic_hash(arrays: Mapping[str, np.ndarray], metadata: Mapping[str, Any]) -> str:
    h = hashlib.sha256()
    h.update(_stable_json(metadata))
    for name in sorted(arrays):
        a = np.ascontiguousarray(np.asarray(arrays[name]))
        h.update(name.encode("utf-8") + b"\0")
        h.update(str(a.dtype).encode("ascii") + b"\0")
        h.update(_stable_json(list(a.shape)))
        h.update(a.tobytes(order="C"))
    return h.hexdigest()


def validate_d1_metadata(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(rows) != 120:
        raise RuntimeError(f"D1 metadata must contain 120 species, got {len(rows)}: FAIL_CLOSED")
    ids = []
    guild_counts: dict[int, int] = {}
    for row in rows:
        sid = str(row.get("species_id", ""))
        gid = int(row.get("guild_id", 0))
        if not sid or gid not in range(1, 7):
            raise RuntimeError("invalid D1 species identity/guild: FAIL_CLOSED")
        if row.get("ancestral_status") != "initial_effective_species":
            raise RuntimeError(f"{sid} is not an initial D1 effective species: FAIL_CLOSED")
        if bool(row.get("Deep_adapted", False)):
            raise RuntimeError(f"{sid} is pre-labelled Deep-adapted: FAIL_CLOSED")
        for key in (
            "thermal_optimum_c", "thermal_niche_sigma_c", "aridity_optimum", "aridity_niche_sigma",
            "range_center_lat", "range_center_lon", "range_scale_km", "patch_amplitude",
            "patch_k_lat", "patch_k_lon", "patch_phase_lat", "patch_phase_lon", "patch_phase_mix",
            "relative_log_body_mass", "dispersal_scale_km", "relative_reproduction_rate",
        ):
            if key not in row:
                raise RuntimeError(f"{sid} missing {key}: FAIL_CLOSED")
        if float(row["thermal_niche_sigma_c"]) <= 0 or float(row["aridity_niche_sigma"]) <= 0 or float(row["range_scale_km"]) <= 0:
            raise RuntimeError(f"{sid} has invalid niche/range scale: FAIL_CLOSED")
        ids.append(sid)
        guild_counts[gid] = guild_counts.get(gid, 0) + 1
    if len(set(ids)) != 120:
        raise RuntimeError("duplicate D1 species id: FAIL_CLOSED")
    expected = {1: 24, 2: 16, 3: 20, 4: 24, 5: 24, 6: 12}
    if guild_counts != expected:
        raise RuntimeError(f"D1 guild counts changed: {guild_counts}: FAIL_CLOSED")
    return {"species_count": 120, "guild_counts": guild_counts, "species_ids": ids}


def area_weights_from_lat(lat_deg: np.ndarray, nlon: int) -> np.ndarray:
    lat = np.asarray(lat_deg, float)
    w = np.maximum(np.cos(np.deg2rad(lat)), 0.0)[:, None] * np.ones((1, int(nlon)))
    s = float(w.sum())
    if s <= 0:
        raise ValueError("invalid latitude grid")
    return w / s


def great_circle_distance_km(lat_grid: np.ndarray, lon_grid: np.ndarray, lat0: float, lon0: float, radius_km: float) -> np.ndarray:
    p1 = np.deg2rad(np.asarray(lat_grid, float))
    p2 = math.radians(float(lat0))
    dlat = p1 - p2
    dlon = (np.deg2rad(np.asarray(lon_grid, float) - float(lon0)) + math.pi) % (2 * math.pi) - math.pi
    h = np.sin(dlat / 2) ** 2 + np.cos(p1) * math.cos(p2) * np.sin(dlon / 2) ** 2
    return 2.0 * float(radius_km) * np.arcsin(np.minimum(1.0, np.sqrt(np.maximum(h, 0.0))))


def species_allocation_scores(metadata: Sequence[Mapping[str, Any]], a1: Mapping[str, np.ndarray], cfg: RebaselineConfig) -> np.ndarray:
    cfg.validate()
    lat = np.asarray(a1["lat"], float)
    lon = np.asarray(a1["lon"], float)
    temp = np.asarray(a1["temperature_c"], float)
    arid = np.asarray(a1["aridity_index"], float)
    land = np.asarray(a1["land_mask"], bool)
    LAT, LON = np.meshgrid(lat, lon, indexing="ij")
    lr = np.deg2rad(LAT)
    lor = np.deg2rad(LON)
    out = np.zeros((len(metadata), len(lat), len(lon)), dtype=np.float64)
    for i, row in enumerate(metadata):
        zt = (temp - float(row["thermal_optimum_c"])) / float(row["thermal_niche_sigma_c"])
        za = (arid - float(row["aridity_optimum"])) / float(row["aridity_niche_sigma"])
        eco = np.exp(-0.5 * np.clip(zt * zt + za * za, 0.0, 140.0))
        dist = great_circle_distance_km(LAT, LON, float(row["range_center_lat"]), float(row["range_center_lon"]), cfg.compatibility_radius_km)
        rscale = float(row["range_scale_km"])
        range_weight = np.exp(-0.5 * (dist / rscale) ** 2)
        range_weight = np.where(dist <= cfg.compact_range_sigma * rscale, range_weight, 0.0)
        p1 = np.sin(int(row["patch_k_lat"]) * lr + float(row["patch_phase_lat"])) * np.cos(int(row["patch_k_lon"]) * lor + float(row["patch_phase_lon"]))
        p2 = np.cos(int(row["patch_k_lat"]) * lr + int(row["patch_k_lon"]) * lor + float(row["patch_phase_mix"]))
        patch = np.maximum(cfg.patch_floor, 1.0 + float(row["patch_amplitude"]) * (0.70 * p1 + 0.30 * p2))
        out[i] = np.where(land, eco * range_weight * patch, 0.0)
    return out


def decompose_guild_state(metadata: Sequence[Mapping[str, Any]], a1: Mapping[str, np.ndarray], cfg: RebaselineConfig) -> dict[str, np.ndarray]:
    info = validate_d1_metadata(metadata)
    scores = species_allocation_scores(metadata, a1, cfg)
    guild_population = np.asarray(a1["guild_population"], float)
    guild_capacity = np.asarray(a1["guild_carrying_capacity"], float)
    if guild_population.shape != (6, len(a1["lat"]), len(a1["lon"])) or guild_capacity.shape != guild_population.shape:
        raise RuntimeError("A1 210 Ma guild state has unexpected shape: FAIL_CLOSED")
    if np.any(guild_population < 0) or np.any(guild_capacity < -1e-15) or np.any(guild_population > guild_capacity + 1e-12):
        raise RuntimeError("A1 population/capacity invariant violated: FAIL_CLOSED")
    pop = np.zeros_like(scores)
    cap = np.zeros_like(scores)
    frac = np.zeros_like(scores)
    guild_ids = np.asarray([int(r["guild_id"]) for r in metadata], dtype=np.uint8)
    for gid in range(1, 7):
        ix = np.where(guild_ids == gid)[0]
        den = np.sum(scores[ix], axis=0)
        occupied = guild_population[gid - 1] > 0
        if np.any(occupied & (den <= 0)):
            raise RuntimeError(f"allocation kernel leaves occupied A1 cells unsupported for guild {gid}: FAIL_CLOSED")
        fg = np.divide(scores[ix], den[None, :, :], out=np.zeros((len(ix), *den.shape), float), where=den[None, :, :] > 0)
        frac[ix] = fg
        pop[ix] = fg * guild_population[gid - 1]
        cap[ix] = fg * guild_capacity[gid - 1]
    if np.any(pop < -1e-15) or np.any(cap < -1e-15) or np.any(pop > cap + 1e-12):
        raise RuntimeError("species population/capacity invariant violated: FAIL_CLOSED")
    return {
        "species_id": np.asarray(info["species_ids"], dtype="U16"),
        "guild_id": guild_ids,
        "allocation_score": scores,
        "allocation_fraction": frac,
        "species_population": pop,
        "species_carrying_capacity": cap,
    }


def _deep_210_state(deep: Mapping[str, np.ndarray], cal: Mapping[str, Any], cfg: RebaselineConfig) -> dict[str, np.ndarray]:
    lat = np.asarray(deep["lat"], float)
    lon = np.asarray(deep["lon"], float)
    area = area_weights_from_lat(lat, len(lon))
    u = np.asarray(deep["free_energy_excess_DFEU"], float)
    if u.shape != (5,):
        raise RuntimeError("invalid v0.5 210 Ma free-energy vector: FAIL_CLOSED")
    photo_u = np.zeros(5, float)
    photo_u[:2] = cfg.photo_additive_share_E_th * u[:2]
    j_per = float(cal["cha1_reference"]["joule_per_global_dfeu"])
    total_per_mode = float(cal["background_total_reservoir_j"]["E"])
    bg = (u * j_per)[:, None, None] * area[None, :, :]
    photo = (photo_u * j_per)[:, None, None] * area[None, :, :]
    buf = np.maximum(total_per_mode - u * j_per, 0.0)[:, None, None] * area[None, :, :]
    ax = np.stack([np.asarray(deep[f"A_X_{m}"], float) for m in MODES])
    mode_opp = ax * (u + photo_u)[:, None, None]
    return {
        "deep_u_base_DFEU": u,
        "deep_photo_u_DFEU": photo_u,
        "deep_mode_opportunity_equilibrium": mode_opp,
        "deep_surface_background_energy_j": bg,
        "deep_photo_energy_j": photo,
        "deep_source_buffer_j": buf,
    }


def _traits(metadata: Sequence[Mapping[str, Any]]) -> dict[str, np.ndarray]:
    float_fields = (
        "thermal_optimum_c", "thermal_niche_sigma_c", "aridity_optimum", "aridity_niche_sigma",
        "drought_tolerance_index", "relative_log_body_mass", "dispersal_scale_km", "relative_reproduction_rate",
        "range_center_lat", "range_center_lon", "range_scale_km",
    )
    out = {f"trait_{k}": np.asarray([float(r[k]) for r in metadata], dtype=np.float64) for k in float_fields}
    out["guild_name"] = np.asarray([str(r["guild"]) for r in metadata], dtype="U40")
    return out


def build_common_state(metadata: Sequence[Mapping[str, Any]], a1: Mapping[str, np.ndarray], deep: Mapping[str, np.ndarray], cal: Mapping[str, Any], cfg: RebaselineConfig) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    cfg.validate()
    dec = decompose_guild_state(metadata, a1, cfg)
    deep_state = _deep_210_state(deep, cal, cfg)
    n = len(metadata)
    arrays: dict[str, np.ndarray] = {
        "age_ma": np.asarray(cfg.age_ma, dtype=np.float64),
        "lat": np.asarray(a1["lat"], dtype=np.float32),
        "lon": np.asarray(a1["lon"], dtype=np.float32),
        "land_mask": np.asarray(a1["land_mask"], dtype=np.uint8),
        "plate_code": np.asarray(a1["plate_code"], dtype=np.uint8),
        "temperature_c": np.asarray(a1["temperature_c"], dtype=np.float32),
        "aridity_index": np.asarray(a1["aridity_index"], dtype=np.float32),
        "browse_forage": np.asarray(a1["browse_forage"], dtype=np.float32),
        "low_forage": np.asarray(a1["low_forage"], dtype=np.float32),
        "wetland_forage": np.asarray(a1["wetland_forage"], dtype=np.float32),
        "total_edible_forage": np.asarray(a1["total_edible_forage"], dtype=np.float32),
        "guild_population_A1": np.asarray(a1["guild_population"], dtype=np.float64),
        "guild_carrying_capacity_A1": np.asarray(a1["guild_carrying_capacity"], dtype=np.float64),
        **dec,
        **_traits(metadata),
        "deep_latent_mean": np.zeros((n, 10), dtype=np.float64),
        "deep_latent_additive_variance": np.full((n, 10), cfg.latent_va_equilibrium, dtype=np.float64),
        "deep_acclimatization": np.zeros(n, dtype=np.float64),
        "deep_remodeling": np.zeros(n, dtype=np.float64),
        "deep_recoverable_load": np.zeros(n, dtype=np.float64),
        "deep_injury": np.zeros(n, dtype=np.float64),
        **deep_state,
    }
    metadata_out = {
        "schema": "ARCANA_WORLD1_210MA_REBASELINE_COMMON_STATE_v0_6D1_R1",
        "status": STATUS,
        "config": asdict(cfg),
        "allocation_semantics": "CELLWISE_GUILD_TO_SPECIES_PARTITION_USING_D1_NICHE_RANGE_PATCH_WEIGHTS_WITH_EXACT_A1_POPULATION_AND_CAPACITY_CLOSURE",
        "capacity_semantics": "SAME_CELLWISE_SPECIES_FRACTION_AS_POPULATION_TO_AVOID_INITIAL_WITHIN_GUILD_N_OVER_K_BIAS",
        "deep_initialization": "Z_X_ZERO; V_A_X_EQUALS_D3_3A_ZERO_SELECTION_HOMEOSTATIC_EQUILIBRIUM_0_045; PHYSIOLOGY_ZERO",
        "paired_counterfactual_semantics": "H0_AND_HX_REFERENCE_THE_EXACT_SAME_COMMON_STATE; ONLY_BIOLOGICAL_DEEP_COUPLING_AUTHORITY_DIFFERS",
        "photo_deep": "ADDITIVE_5_PERCENT_ON_E_AND_TH_PHYSICAL_FIELD_PRESENT_IN_BOTH_H0_AND_HX",
        "rng_policy": "BASE_SEED_917231; R2_MUST_USE_EVENT_KEYED_COMMON_RANDOM_NUMBERS_TO_PREVENT_DRAW_ORDER_DESYNCHRONIZATION_AFTER_BRANCH_DIVERGENCE",
        "not_claimed": ["BIT_IDENTITY_WITH_LOST_D1_D2", "RECOVERY_OF_LOST_210MA_SPECIES_RASTER", "HISTORICAL_HSG025_PRE_CHA1_STATE"],
    }
    return arrays, metadata_out


def conservation_diagnostics(arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    pop = np.asarray(arrays["species_population"], float)
    cap = np.asarray(arrays["species_carrying_capacity"], float)
    gids = np.asarray(arrays["guild_id"], int)
    gp = np.asarray(arrays["guild_population_A1"], float)
    gk = np.asarray(arrays["guild_carrying_capacity_A1"], float)
    per_guild = {}
    max_pop = 0.0
    max_cap = 0.0
    for gid in range(1, 7):
        ix = np.where(gids == gid)[0]
        ep = pop[ix].sum(axis=0) - gp[gid - 1]
        ek = cap[ix].sum(axis=0) - gk[gid - 1]
        max_pop = max(max_pop, float(np.max(np.abs(ep))))
        max_cap = max(max_cap, float(np.max(np.abs(ek))))
        per_guild[str(gid)] = {
            "species_count": int(len(ix)),
            "population_A1": float(gp[gid - 1].sum()),
            "population_species": float(pop[ix].sum()),
            "capacity_A1": float(gk[gid - 1].sum()),
            "capacity_species": float(cap[ix].sum()),
        }
    totals = pop.sum(axis=(1, 2))
    occupancy = np.sum(pop > 1e-12, axis=(1, 2))
    return {
        "max_cell_population_closure_abs": max_pop,
        "max_cell_capacity_closure_abs": max_cap,
        "global_population_A1": float(gp.sum()),
        "global_population_species": float(pop.sum()),
        "global_capacity_A1": float(gk.sum()),
        "global_capacity_species": float(cap.sum()),
        "species_population_min": float(totals.min()),
        "species_population_median": float(np.median(totals)),
        "species_population_max": float(totals.max()),
        "species_occupied_cells_min": int(occupancy.min()),
        "species_occupied_cells_median": float(np.median(occupancy)),
        "species_occupied_cells_max": int(occupancy.max()),
        "population_exceeds_capacity_count": int(np.sum(pop > cap + 1e-12)),
        "nonland_population_cells": int(np.sum((pop > 0) & (np.asarray(arrays["land_mask"], bool)[None, :, :] == 0))),
        "per_guild": per_guild,
    }


def paired_manifests(common_semantic_sha256: str, cfg: RebaselineConfig) -> tuple[dict[str, Any], dict[str, Any]]:
    common = {
        "schema": "ARCANA_PAIRED_REPLAY_INITIALIZATION_v0_6D1_R1",
        "initial_age_ma": 210.0,
        "common_state_semantic_sha256": common_semantic_sha256,
        "paired_rng_seed": cfg.paired_rng_seed,
        "physical_deep_present": True,
        "photo_deep_additive_share_E_th": cfg.photo_additive_share_E_th,
        "active_magic": False,
        "sapience": False,
        "civilization": False,
    }
    h0 = {**common, "branch_id": "H0_REBASELINED_NATURAL_CONTROL", "counterfactual_role": "CONTROL", "deep_biological_coupling_enabled": False}
    hx = {**common, "branch_id": "HX_REBASELINED_DEEP_COUPLED", "counterfactual_role": "TREATMENT", "deep_biological_coupling_enabled": True}
    return h0, hx


def allowed_branch_delta(h0: Mapping[str, Any], hx: Mapping[str, Any]) -> dict[str, Any]:
    keys = sorted(set(h0) | set(hx))
    delta = {k: [h0.get(k), hx.get(k)] for k in keys if h0.get(k) != hx.get(k)}
    allowed = {"branch_id", "counterfactual_role", "deep_biological_coupling_enabled"}
    unexpected = sorted(set(delta) - allowed)
    return {"delta": delta, "unexpected_delta_keys": unexpected, "pass": not unexpected}
