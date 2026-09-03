from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import math
import statistics
import time

import numpy as np

STAGE = "v0.6D1-R4.3"
R42_SEALED = "PASS_R42_FROZEN_HISTORICAL_WINDOW_BASELINE_MATERIALIZATION_ADAPTER_CONTRACT_AND_MULTI_ENGINE_EXECUTION_FREEZE_SEALED"
PREPARED = "PASS_R43_FROZEN_23_JOB_CONTRACT_AND_UNIT_MAPPING_PREPARED"
EXECUTION_COMPLETE = "PASS_R43_FROZEN_23_ENGINE_WINDOW_EXECUTION_COMPLETE"
SEALED = "PASS_R43_FROZEN_23_ENGINE_WINDOW_HISTORICAL_REVALIDATION_EXECUTION_AND_NORMALIZATION_SEALED"
BLOCKED = "BLOCKED_R43_JOB_EXECUTION_OR_MAPPING_FAILURE"

CFG_REL = Path("configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json")
R42_CFG_REL = Path("configs/world1_r42_historical_window_materialization_v0_6D1_R4_2.json")
R42_SEAL_REL = Path("outputs/v0_6D1_R4_2_SEAL/R4_2_FINAL_SEAL_AUDIT.json")
R42_JOBS_REL = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
R42_ARTIFACTS_REL = Path("outputs/v0_6D1_R4_2/R4_2_BASELINE_ARTIFACT_REGISTRY.json")
R42_MAPPING_REL = Path("outputs/v0_6D1_R4_2/R4_2_SEMANTIC_MAPPING_CONTRACT.json")
R41_AUTH_REL = Path("outputs/v0_6D1_R4_1/R4_1_SEMANTIC_AUTHORITY_MATRIX.json")
R41_RUNTIME_REL = Path("outputs/v0_6D1_R4_1/R4_1_RUNTIME_IDENTITY_EVIDENCE.json")
OUT_REL = Path("outputs/v0_6D1_R4_3")
SEAL_REL = Path("outputs/v0_6D1_R4_3_SEAL/R4_3_FINAL_SEAL_AUDIT.json")


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: str | Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def root_path(root: Path, rel: str | Path) -> Path:
    # R4.2 artifacts were emitted on Windows; preserve their strings but normalize for host access.
    s = str(rel).replace("\\", "/")
    return root / Path(s)


def finite_or_none(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _summary(values: np.ndarray | list[float]) -> dict[str, float | None]:
    a = np.asarray(values, dtype=float).ravel()
    a = a[np.isfinite(a)]
    if not a.size:
        return {"n": 0, "mean": None, "median": None, "q10": None, "q90": None, "min": None, "max": None}
    return {
        "n": int(a.size),
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "q10": float(np.quantile(a, 0.10)),
        "q90": float(np.quantile(a, 0.90)),
        "min": float(np.min(a)),
        "max": float(np.max(a)),
    }


def _ratio(end: Any, start: Any) -> float | None:
    a, b = finite_or_none(start), finite_or_none(end)
    if a is None or b is None or abs(a) < 1e-15:
        return None
    return b / a


def _delta(end: Any, start: Any) -> float | None:
    a, b = finite_or_none(start), finite_or_none(end)
    if a is None or b is None:
        return None
    return b - a


def _window_duration_years(window: dict[str, Any]) -> float:
    if "start_ma" in window:
        return (float(window["start_ma"]) - float(window["end_ma"])) * 1_000_000.0
    return (float(window["start_ka"]) - float(window["end_ka"])) * 1_000.0


def _window_ages(window: dict[str, Any]) -> tuple[str, float, float]:
    if "start_ma" in window:
        return "Ma", float(window["start_ma"]), float(window["end_ma"])
    return "ka", float(window["start_ka"]), float(window["end_ka"])


def _artifact_row(artifact_registry: dict[str, Any], window_id: str, rel: str) -> dict[str, Any] | None:
    target = rel.replace("/", "\\").lower()
    alt = rel.replace("\\", "/").lower()
    for row in artifact_registry["windows"].get(window_id, []):
        p = str(row.get("path", ""))
        if p.lower() == target or p.replace("\\", "/").lower() == alt:
            return row
    return None


def _verify_artifact(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    p = root_path(root, row["path"])
    exists = p.exists()
    observed = sha256_file(p) if exists else None
    return {
        "path": row["path"],
        "registered_sha256": row.get("sha256"),
        "observed_sha256": observed,
        "exists": exists,
        "hash_match": exists and observed == row.get("sha256"),
        "bytes": p.stat().st_size if exists else None,
    }


def _find_h0_snapshot_artifact(root: Path, artifact_registry: dict[str, Any], window: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Select by temporal coverage only, never by scientific result value."""
    rows = artifact_registry["windows"][window["id"]]
    start, end = float(window["start_ma"]), float(window["end_ma"])
    candidates: list[tuple[tuple[float, float, str], dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for row in rows:
        if not str(row["path"]).lower().endswith(".json"):
            continue
        p = root_path(root, row["path"])
        if not p.exists():
            continue
        try:
            d = load_json(p)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        snaps = d.get("snapshots")
        if not isinstance(snaps, list) or not snaps:
            continue
        available = [s for s in snaps if isinstance(s, dict) and finite_or_none(s.get("age_ma")) is not None]
        if not available:
            continue
        ss = min(available, key=lambda s: abs(float(s["age_ma"]) - start))
        ee = min(available, key=lambda s: abs(float(s["age_ma"]) - end))
        start_gap = abs(float(ss["age_ma"]) - start)
        end_gap = abs(float(ee["age_ma"]) - end)
        # Prefer exact coverage; tie break by total temporal error then path, not by result value.
        key = (start_gap + end_gap, max(start_gap, end_gap), str(row["path"]))
        candidates.append((key, row, ss, ee))
    if not candidates:
        raise RuntimeError(f"No frozen R4.2 JSON artifact with snapshots for {window['id']}")
    _, row, ss, ee = sorted(candidates, key=lambda x: x[0])[0]
    return row, ss, ee


def _h0_descriptor(root: Path, artifact_registry: dict[str, Any], window: dict[str, Any]) -> dict[str, Any]:
    row, ss, ee = _find_h0_snapshot_artifact(root, artifact_registry, window)
    selected = _verify_artifact(root, row)
    if not selected["hash_match"]:
        raise RuntimeError(f"Frozen artifact hash mismatch: {row['path']}")
    fields = [
        "species_richness", "component_count", "total_population", "median_normalized_va",
        "max_intrinsic_ri", "max_isolation_clock_generations", "speciation_events_cumulative",
        "extinction_events_cumulative", "fission_events_cumulative", "coalescence_events_cumulative",
        "fractional_support_cells",
    ]
    start_state = {k: ss.get(k) for k in fields if k in ss}
    end_state = {k: ee.get(k) for k in fields if k in ee}
    target_start = float(window["start_ma"])
    target_end = float(window["end_ma"])
    return {
        "descriptor_type": "H0_SNAPSHOT_WINDOW",
        "selected_frozen_artifact": selected,
        "selection_rule": "TEMPORAL_COVERAGE_ONLY_PRE_RESULT_NO_SCIENTIFIC_VALUE_SELECTION",
        "target": {"unit": "Ma", "start": target_start, "end": target_end},
        "materialized": {"start_age": float(ss["age_ma"]), "end_age": float(ee["age_ma"])},
        "temporal_gap": {"start_ma": abs(float(ss["age_ma"]) - target_start), "end_ma": abs(float(ee["age_ma"]) - target_end)},
        "start_state": start_state,
        "comparison_target_end_state": end_state,
        "comparison_only_derived": {
            "population_ratio": _ratio(end_state.get("total_population"), start_state.get("total_population")),
            "richness_ratio": _ratio(end_state.get("species_richness"), start_state.get("species_richness")),
            "component_ratio": _ratio(end_state.get("component_count"), start_state.get("component_count")),
            "normalized_va_delta": _delta(end_state.get("median_normalized_va"), start_state.get("median_normalized_va")),
        },
    }


def _physical_scalar_at_age(root: Path, age_ma: float) -> dict[str, float | None]:
    p = root / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["age_ma"], dtype=float)
        # age array is descending. Interpolate scalar summaries between the bracketing canonical anchors.
        order = np.argsort(ages)
        ax = ages[order]
        out: dict[str, float | None] = {}
        for key in ("temperature_c", "aridity_index", "total_edible_forage", "carrying_capacity", "population"):
            arr = np.asarray(z[key], dtype=float)[order]
            means = np.nanmean(arr, axis=tuple(range(1, arr.ndim)))
            out[f"mean_{key}"] = float(np.interp(age_ma, ax, means))
        # land is categorical; use nearest canonical anchor for support fraction.
        ni = int(np.argmin(np.abs(ages - age_ma)))
        land = np.asarray(z["land_mask"][ni], dtype=float)
        out["land_fraction_nearest_anchor"] = float(np.mean(land > 0.5))
        out["land_anchor_age_ma"] = float(ages[ni])
        return out


def _physical_forcing(root: Path, window: dict[str, Any]) -> dict[str, Any] | None:
    if "start_ma" not in window:
        return None
    p = root / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
    if not p.exists():
        return None
    a = _physical_scalar_at_age(root, float(window["start_ma"]))
    b = _physical_scalar_at_age(root, float(window["end_ma"]))
    deltas = {k: _delta(b.get(k), a.get(k)) for k in a if k.startswith("mean_")}
    return {
        "source": str(p.relative_to(root)),
        "sha256": sha256_file(p),
        "role": "PREEXISTING_CANONICAL_EXOGENOUS_PHYSICAL_COMPANION_FROZEN_IN_R43_PRE_RESULT",
        "interpolation": "LINEAR_ON_GLOBAL_SCALAR_SUMMARIES_BETWEEN_A1_ANCHORS;_LAND_NEAREST_ANCHOR_ONLY",
        "start": a,
        "end": b,
        "delta": deltas,
    }


def _r327_descriptor(root: Path, artifact_registry: dict[str, Any], window: dict[str, Any]) -> dict[str, Any]:
    rel = "outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz"
    row = _artifact_row(artifact_registry, window["id"], rel)
    if row is None:
        raise RuntimeError("R3.27 trajectories missing from frozen R4.2 registry")
    verified = _verify_artifact(root, row)
    if not verified["hash_match"]:
        raise RuntimeError("R3.27 frozen trajectory hash mismatch")
    with np.load(root / rel, allow_pickle=False) as z:
        ids = z["candidate_ids"].astype(str)
        cohort = ["RPT_010_D02", "RPT_009_D02"]
        cidx = [int(np.where(ids == c)[0][0]) for c in cohort]
        ages = np.asarray(z["age_ma"], dtype=float)
        si = int(np.argmin(np.abs(ages - float(window["start_ma"]))))
        ei = int(np.argmin(np.abs(ages - float(window["end_ma"]))))
        names = z["variable_names"].astype(str).tolist()
        state = np.asarray(z["state"], dtype=float)[:, cidx, :, :]
        start_state, end_state = {}, {}
        for vi, name in enumerate(names):
            start_state[name] = _summary(state[:, :, si, vi])
            end_state[name] = _summary(state[:, :, ei, vi])
        env = np.asarray(z["environmental_stress"], dtype=float)
        conn = np.asarray(z["corridor_connectivity"], dtype=float)
        bott = np.asarray(z["bottleneck_multiplier"], dtype=float)
        exo = {
            "environmental_stress_start": _summary(env[:, si]),
            "environmental_stress_end": _summary(env[:, ei]),
            "corridor_connectivity_start": _summary(conn[:, si]),
            "corridor_connectivity_end": _summary(conn[:, ei]),
            "bottleneck_multiplier_min": _summary(np.min(bott[:, min(si,ei):max(si,ei)+1], axis=1)),
        }
    return {
        "descriptor_type": "R327_SAPIENT_MACRO_ENSEMBLE_WINDOW",
        "selected_frozen_artifact": verified,
        "candidate_cohort": cohort,
        "target": {"unit": "Ma", "start": float(window["start_ma"]), "end": float(window["end_ma"])},
        "materialized": {"start_age": float(ages[si]), "end_age": float(ages[ei]), "ensemble_members": 96},
        "start_state": start_state,
        "exogenous_forcing": exo,
        "comparison_target_end_state": end_state,
        "comparison_only_derived": {
            "population_ratio_median": _ratio(end_state["effective_population"]["median"], start_state["effective_population"]["median"]),
            "genetic_diversity_delta": _delta(end_state["genetic_diversity_proxy"]["median"], start_state["genetic_diversity_proxy"]["median"]),
            "adaptive_integration_delta": _delta(end_state["adaptive_integration"]["median"], start_state["adaptive_integration"]["median"]),
        },
    }


def _r328_descriptor(root: Path, artifact_registry: dict[str, Any], window: dict[str, Any]) -> dict[str, Any]:
    rel = "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz"
    row = _artifact_row(artifact_registry, window["id"], rel)
    if row is None:
        raise RuntimeError("R3.28 replay missing from frozen R4.2 registry")
    verified = _verify_artifact(root, row)
    if not verified["hash_match"]:
        raise RuntimeError("R3.28 frozen trajectory hash mismatch")
    with np.load(root / rel, allow_pickle=False) as z:
        ages = np.asarray(z["age_ka"], dtype=float)
        si = int(np.argmin(np.abs(ages - float(window["start_ka"]))))
        ei = int(np.argmin(np.abs(ages - float(window["end_ka"]))))
        names = z["species_summary_variable_names"].astype(str).tolist()
        ss = np.asarray(z["species_summary"], dtype=float)
        start_state, end_state = {}, {}
        for vi, name in enumerate(names):
            start_state[name] = _summary(ss[:, :, si, vi])
            end_state[name] = _summary(ss[:, :, ei, vi])
        contact = np.asarray(z["contact_index"], dtype=float)
        admixture = np.asarray(z["admixture_opportunity_cumulative"], dtype=float)
        exo = {
            "contact_index_start": _summary(contact[:, si]),
            "contact_index_end": _summary(contact[:, ei]),
            "admixture_opportunity_start": _summary(admixture[:, si]),
            "admixture_opportunity_end": _summary(admixture[:, ei]),
        }
    return {
        "descriptor_type": "R328_SAPIENT_HIGH_RES_ENSEMBLE_WINDOW",
        "selected_frozen_artifact": verified,
        "candidate_cohort": ["RPT_010_D02", "RPT_009_D02"],
        "target": {"unit": "ka", "start": float(window["start_ka"]), "end": float(window["end_ka"])},
        "materialized": {"start_age": float(ages[si]), "end_age": float(ages[ei]), "ensemble_members": 32},
        "start_state": start_state,
        "exogenous_forcing": exo,
        "comparison_target_end_state": end_state,
        "comparison_only_derived": {
            "population_ratio_median": _ratio(end_state["population_proxy"]["median"], start_state["population_proxy"]["median"]),
            "spatial_spread_ratio_median": _ratio(end_state["spatial_spread"]["median"], start_state["spatial_spread"]["median"]),
            "genetic_diversity_delta": _delta(end_state["genetic_diversity_proxy"]["median"], start_state["genetic_diversity_proxy"]["median"]),
            "admixture_delta": _delta(end_state["admixture_fraction_proxy"]["median"], start_state["admixture_fraction_proxy"]["median"]),
        },
    }


def _r334_descriptor(root: Path, artifact_registry: dict[str, Any], window: dict[str, Any]) -> dict[str, Any]:
    rel_t = "outputs/v0_6D1_R3_34/R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz"
    rel_l = "outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"
    row_t = _artifact_row(artifact_registry, window["id"], rel_t)
    row_l = _artifact_row(artifact_registry, window["id"], rel_l)
    if row_t is None or row_l is None:
        raise RuntimeError("R3.34 producer sources missing from frozen R4.2 registry")
    vt, vl = _verify_artifact(root, row_t), _verify_artifact(root, row_l)
    if not vt["hash_match"] or not vl["hash_match"]:
        raise RuntimeError("R3.34 frozen artifact hash mismatch")
    with np.load(root / rel_t, allow_pickle=False) as z:
        ages = np.asarray(z["age_ka"], dtype=float)
        si = int(np.argmin(np.abs(ages - float(window["start_ka"]))))
        ei = int(np.argmin(np.abs(ages - float(window["end_ka"]))))
        names = z["trajectory_variable_names"].astype(str).tolist()
        state = np.asarray(z["trajectory_state"], dtype=float)
        start_state, end_state = {}, {}
        for vi, name in enumerate(names):
            start_state[name] = _summary(state[:, :, :, si, vi])
            end_state[name] = _summary(state[:, :, :, ei, vi])
    with np.load(root / rel_l, allow_pickle=False) as z:
        a = np.asarray(z["anchor_age_ka"], dtype=float)
        asi = int(np.argmin(np.abs(a - float(window["start_ka"]))))
        aei = int(np.argmin(np.abs(a - float(window["end_ka"]))))
        lnames = z["landscape_variable_names"].astype(str).tolist()
        land = np.asarray(z["producer_landscape"], dtype=float)
        landscape = {}
        for vi, name in enumerate(lnames):
            landscape[f"{name}_start"] = _summary(land[:, asi, :, :, vi])
            landscape[f"{name}_end"] = _summary(land[:, aei, :, :, vi])
    return {
        "descriptor_type": "R334_PRODUCER_COEVOLUTION_WINDOW",
        "selected_frozen_artifacts": [vt, vl],
        "target": {"unit": "ka", "start": float(window["start_ka"]), "end": float(window["end_ka"])},
        "materialized": {"start_age": float(ages[si]), "end_age": float(ages[ei]), "ensemble_members": 32, "producer_taxa": 36},
        "start_state": start_state,
        "exogenous_forcing": landscape,
        "comparison_target_end_state": end_state,
        "comparison_only_derived": {
            "selective_divergence_delta": _delta(end_state["selective_divergence"]["median"], start_state["selective_divergence"]["median"]),
            "wild_gene_flow_delta": _delta(end_state["wild_gene_flow_pressure"]["median"], start_state["wild_gene_flow_pressure"]["median"]),
            "domestication_index_delta": _delta(end_state["domestication_index"]["median"], start_state["domestication_index"]["median"]),
        },
    }


def build_window_descriptors(root: Path, r42_cfg: dict[str, Any], artifact_registry: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for w in r42_cfg["windows"]:
        wid = w["id"]
        if wid.startswith("H0_"):
            d = _h0_descriptor(root, artifact_registry, w)
            d["exogenous_physical_forcing"] = _physical_forcing(root, w)
        elif wid == "SAPIENT_3MA_TO_200KA":
            d = _r327_descriptor(root, artifact_registry, w)
        elif wid == "SAPIENT_200KA_TO_0":
            d = _r328_descriptor(root, artifact_registry, w)
        elif wid == "PRODUCER_20KA_TO_0":
            d = _r334_descriptor(root, artifact_registry, w)
        else:
            raise RuntimeError(f"Unknown frozen window: {wid}")
        out[wid] = d
    return out


def _authority_role(authority: dict[str, Any], domain: str, engine: str) -> str | None:
    row = authority["domains"].get(domain, {})
    if engine in row.get("primary", []):
        return "PRIMARY"
    if engine in row.get("secondary", []):
        return "SECONDARY"
    return None


def _time_mapping(cfg: dict[str, Any], window: dict[str, Any], engine: str) -> dict[str, Any]:
    rt = cfg["representative_runtime"][engine]
    duration = _window_duration_years(window)
    steps = int(rt["steps"])
    return {
        "historical_window_duration_years": duration,
        "engine_temporal_unit": rt["unit"],
        "engine_representative_steps": steps,
        "historical_years_per_representative_engine_step": duration / steps,
        "literal_history_replay": False,
        "generation_time_assumption_years": None if rt["unit"] != "generations" else "NOT_USED_AS_LITERAL_CALENDAR_EQUIVALENCE_IN_R43_RESPONSE_EXPERIMENT",
        "mapping_class": "EXPLICIT_COMPRESSED_REPRESENTATIVE_RESPONSE",
        "caveat": "Representative engine time is a response scale, not a claim that one engine step equals the reported historical-year compression factor physically.",
    }


def _space_mapping(engine: str, window_id: str) -> dict[str, Any]:
    if engine == "Madingley":
        return {"engine_basis": "fixed_1_degree_reference_window", "normalized_basis": "functional_response_per_reference_window", "cell_area_mapping": "REFERENCE_EARTH_GRID_PROXY_ONLY", "eligible_habitat_denominator": "ENGINE_LAND_SUPPORT", "comparability_caveat": "Madingley Earth spatial input is a functional ecosystem proxy, not ARCANA geography."}
    if engine == "RangeShifter":
        return {"engine_basis": "25x25_artificial_landscape_100m_resolution", "normalized_basis": "occupied_fraction_of_engine_suitable_support", "cell_area_mapping": "100m_cell_engine_native", "eligible_habitat_denominator": "artificial_suitable_cells", "comparability_caveat": "single-replicate positive-abundance cells are not the engine dedicated multi-replicate occupancy product."}
    if engine == "Geonomics":
        return {"engine_basis": "default_dynamic_landscape_model", "normalized_basis": "occupied_fraction_and_relative_spread", "cell_area_mapping": "MODEL_CELL_NOT_KM2", "eligible_habitat_denominator": "model_landscape_cells", "comparability_caveat": "Geonomics model cells are normalized; no km2 equality is asserted."}
    if engine == "CDMetaPOP":
        return {"engine_basis": "pinned_generic_patch_network", "normalized_basis": "relative_patch_persistence_and_gene_flow", "cell_area_mapping": "PATCH_NETWORK_NO_KM2_EQUIVALENCE", "eligible_habitat_denominator": "configured_patches", "comparability_caveat": "patch-network response only."}
    if engine == "NEMO":
        return {"engine_basis": "two_patch_genetic_response", "normalized_basis": "allele_frequency_and_variance_response", "cell_area_mapping": "PATCHES_NO_KM2_EQUIVALENCE", "eligible_habitat_denominator": "2_patches", "comparability_caveat": "NEMO patch space is a genetic response proxy."}
    return {"engine_basis": "two_population_tree_sequence_response", "normalized_basis": "ancestry_gene_flow_variance_response", "cell_area_mapping": "POPULATIONS_NO_KM2_EQUIVALENCE", "eligible_habitat_denominator": "2_subpopulations", "comparability_caveat": "SLiM subpopulations are not literal ARCANA geographic cells."}


def _population_mapping(engine: str) -> dict[str, Any]:
    semantics = {
        "NEMO": "literal_simulated_individuals_for_engine_only",
        "Geonomics": "individual_agents_for_engine_only",
        "Madingley": "functional_cohorts_and_autotroph_stocks",
        "RangeShifter": "engine_abundance_on_artificial_cells",
        "CDMetaPOP": "patch_population_genetic_demography",
        "SLiM": "diploid_simulated_individuals_for_engine_only",
    }[engine]
    return {
        "engine_raw_semantics": semantics,
        "normalized_semantics": "relative_change_distribution_or_dimensionless_response_only",
        "literal_arcana_N_equivalence": False,
        "transform": "ratios/deltas within engine replicate; never raw-N cross-engine equality",
    }


def _domain_mapping(cfg: dict[str, Any], authority: dict[str, Any], window_id: str, engine: str) -> list[dict[str, Any]]:
    rows = []
    for domain in cfg["window_domain_scope"][window_id]:
        role = _authority_role(authority, domain, engine)
        if role is None:
            continue
        comp = cfg["comparability_policy"]["primary_authority" if role == "PRIMARY" else "secondary_authority"]
        rows.append({"domain": domain, "authority_role": role, "comparability_class": comp, "majority_vote": False})
    return rows


def _driver_values(descriptor: dict[str, Any], engine: str, window_id: str) -> dict[str, float]:
    """Only start-state and exogenous forcing may enter engine configuration."""
    pop0 = None
    conn0 = 0.5
    env_change = 0.0
    diversity0 = 0.35
    selection = 0.0
    gene_flow = 0.02
    habitat_start = 0.5
    habitat_end = 0.5

    if descriptor["descriptor_type"] == "H0_SNAPSHOT_WINDOW":
        pop0 = finite_or_none(descriptor["start_state"].get("total_population"))
        va = finite_or_none(descriptor["start_state"].get("median_normalized_va"))
        if va is not None:
            diversity0 = max(0.05, min(0.95, va / 0.08))
        phys = descriptor.get("exogenous_physical_forcing") or {}
        st, en = phys.get("start", {}), phys.get("end", {})
        ks, ke = finite_or_none(st.get("mean_carrying_capacity")), finite_or_none(en.get("mean_carrying_capacity"))
        fs, fe = finite_or_none(st.get("mean_total_edible_forage")), finite_or_none(en.get("mean_total_edible_forage"))
        ls, le = finite_or_none(st.get("land_fraction_nearest_anchor")), finite_or_none(en.get("land_fraction_nearest_anchor"))
        if ls is not None: habitat_start = max(0.1, min(0.9, ls))
        if le is not None: habitat_end = max(0.1, min(0.9, le))
        terms=[]
        for a,b in ((ks,ke),(fs,fe)):
            if a is not None and b is not None and abs(a)>1e-12:
                terms.append((b-a)/abs(a))
        env_change = float(np.mean(terms)) if terms else 0.0
        conn0 = max(0.05, min(0.95, 0.25 + 0.75*habitat_start))
        gene_flow = max(0.002, min(0.08, 0.002 + 0.05*conn0))
    elif descriptor["descriptor_type"] == "R327_SAPIENT_MACRO_ENSEMBLE_WINDOW":
        pop0 = descriptor["start_state"]["effective_population"]["median"]
        diversity0 = float(descriptor["start_state"]["genetic_diversity_proxy"]["median"] or 0.35)
        conn0 = float(descriptor["exogenous_forcing"]["corridor_connectivity_start"]["median"] or 0.5)
        c1 = float(descriptor["exogenous_forcing"]["corridor_connectivity_end"]["median"] or conn0)
        s0 = float(descriptor["exogenous_forcing"]["environmental_stress_start"]["median"] or 0.0)
        s1 = float(descriptor["exogenous_forcing"]["environmental_stress_end"]["median"] or s0)
        env_change = (c1-conn0) - (s1-s0)
        habitat_start=max(0.1,min(0.9,conn0)); habitat_end=max(0.1,min(0.9,c1))
        gene_flow=max(0.002,min(0.08,0.002+0.06*conn0)); selection=max(0.0,min(0.05,abs(s1-s0)*0.02))
    elif descriptor["descriptor_type"] == "R328_SAPIENT_HIGH_RES_ENSEMBLE_WINDOW":
        pop0 = descriptor["start_state"]["population_proxy"]["median"]
        diversity0 = float(descriptor["start_state"]["genetic_diversity_proxy"]["median"] or 0.35)
        conn0=max(0.05,min(0.95,float(descriptor["exogenous_forcing"]["contact_index_start"]["median"] or 0.2)+0.2))
        c1=max(0.05,min(0.95,float(descriptor["exogenous_forcing"]["contact_index_end"]["median"] or 0.2)+0.2))
        env_change=c1-conn0; habitat_start=conn0; habitat_end=c1
        a0=float(descriptor["exogenous_forcing"]["admixture_opportunity_start"]["median"] or 0.0)
        a1=float(descriptor["exogenous_forcing"]["admixture_opportunity_end"]["median"] or a0)
        gene_flow=max(0.002,min(0.08,0.003+0.05*max(0.0,a1-a0)+0.02*conn0))
        selection=max(0.0,min(0.05,abs(env_change)*0.02))
    else:
        pop0 = 1.0
        s0=float(descriptor["exogenous_forcing"]["suitability_start"]["median"] or 0.5)
        s1=float(descriptor["exogenous_forcing"]["suitability_end"]["median"] or s0)
        habitat_start=max(0.1,min(0.9,s0)); habitat_end=max(0.1,min(0.9,s1))
        wg0=float(descriptor["start_state"]["wild_gene_flow_pressure"]["median"] or 0.5)
        hs0=float(descriptor["start_state"]["harvest_selection"]["median"] or 0.0)
        conn0=max(0.05,min(0.95,wg0)); gene_flow=max(0.002,min(0.08,0.002+0.06*wg0)); selection=max(0.0,min(0.05,hs0*0.04))
        env_change=s1-s0; diversity0=max(0.05,min(0.95,wg0))

    return {
        "arcana_start_population_descriptor": float(pop0 or 1.0),
        "normalized_initial_population_scale": 1.0,
        "normalized_initial_genetic_diversity": max(0.05, min(0.95, float(diversity0))),
        "normalized_connectivity_start": max(0.05, min(0.95, float(conn0))),
        "engine_gene_flow_rate": max(0.001, min(0.10, float(gene_flow))),
        "engine_selection_strength": max(0.0, min(0.05, float(selection))),
        "normalized_environment_change": max(-1.0, min(1.0, float(env_change))),
        "normalized_habitat_fraction_start": max(0.1, min(0.9, float(habitat_start))),
        "normalized_habitat_fraction_end": max(0.1, min(0.9, float(habitat_end))),
    }


def _seed(job_id: str, replicate_index: int) -> int:
    raw = sha256(f"ARCANA_R43|{job_id}|rep={replicate_index}".encode("utf-8")).digest()
    return 1 + int.from_bytes(raw[:4], "big") % 2_000_000_000


def build_job_materialization(root: Path, cfg: dict[str, Any], r42_cfg: dict[str, Any], jobs_doc: dict[str, Any], authority: dict[str, Any], descriptors: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    window_by_id = {w["id"]: w for w in r42_cfg["windows"]}
    mappings, ledger, contracts = [], {"stage": STAGE, "algorithm": "SHA256(ARCANA_R43|R42_JOB_ID|replicate_index)", "jobs": []}, []
    for j in jobs_doc["jobs"]:
        wid, engine = j["window_id"], j["engine"]
        w = window_by_id[wid]
        domains = _domain_mapping(cfg, authority, wid, engine)
        mapping = {
            "window_id": wid,
            "engine": engine,
            "job_id": j["job_id"],
            "r43_execution_id": j["job_id"].replace("R42_", "R43_", 1),
            "baseline_artifacts": descriptors[wid].get("selected_frozen_artifacts", [descriptors[wid].get("selected_frozen_artifact")]),
            "arcana_metrics": [x["domain"] for x in domains],
            "engine_raw_metrics": "ENGINE_SPECIFIC_RAW_EVIDENCE_PRESERVED_UNALTERED",
            "raw_units": "ENGINE_NATIVE",
            "normalized_units": "DIMENSIONLESS_RELATIVE_RESPONSE_OR_DECLARED_DOMAIN_METRIC",
            "time_mapping": _time_mapping(cfg, w, engine),
            "space_mapping": _space_mapping(engine, wid),
            "population_mapping": _population_mapping(engine),
            "domain_mapping": domains,
            "uncertainty_mapping": {"replicates": int(cfg["replicates_by_engine"][engine]), "distribution_required": True, "single_run_promotional": False},
            "comparability_class": sorted(set(x["comparability_class"] for x in domains)),
            "transform_formula": "PER_DOMAIN_IN_NORMALIZER;_RAW_COUNTS_NEVER_CROSS_ENGINE_COMPARED",
            "transform_provenance": "R4.1_SEMANTIC_AUTHORITY_MATRIX_PLUS_R4.3_PRE_RESULT_MAPPING",
            "caveats": ["NORMALIZED_BOUNDARY_RESPONSE_NOT_LITERAL_MULTI_MYR_ENGINE_REPLAY", "ARCANA_END_STATE_IS_COMPARISON_TARGET_ONLY", "NO_MAJORITY_VOTE"],
            "pre_result_frozen": True,
        }
        mappings.append(mapping)
        reps = [{"replicate_index": r, "seed": _seed(j["job_id"], r)} for r in range(int(cfg["replicates_by_engine"][engine]))]
        ledger["jobs"].append({"job_id": j["job_id"], "engine": engine, "replicates": reps})
        contract = {
            "stage": STAGE,
            "frozen_parent_job": j,
            "r43_execution_id": mapping["r43_execution_id"],
            "window": w,
            "historical_duration_years": _window_duration_years(w),
            "execution_semantics": cfg["execution_semantics"],
            "baseline_descriptor": descriptors[wid],
            "engine_input": {
                "derived_from": "ARCANA_START_STATE_AND_EXOGENOUS_FORCING_ONLY",
                "end_state_leakage": False,
                "drivers": _driver_values(descriptors[wid], engine, wid),
                "representative_runtime": cfg["representative_runtime"][engine],
                "replicates": reps,
            },
            "comparison_target": {
                "use": "POST_EXECUTION_NORMALIZATION_AND_R4.4_ADJUDICATION_ONLY",
                "arcana_end_state": descriptors[wid]["comparison_target_end_state"],
                "derived_end_response": descriptors[wid].get("comparison_only_derived", {}),
            },
            "unit_mapping": mapping,
            "canonical_write": False,
            "scientific_agreement_claimed": False,
        }
        contracts.append(contract)
    return mappings, ledger, contracts


def _write_tsv_config(path: Path, contract: dict[str, Any]) -> None:
    d = contract["engine_input"]["drivers"]
    rt = contract["engine_input"]["representative_runtime"]
    rows = {
        "job_id": contract["frozen_parent_job"]["job_id"],
        "engine": contract["frozen_parent_job"]["engine"],
        "runtime_steps": rt["steps"],
        "runtime_unit": rt["unit"],
        "replicate_count": len(contract["engine_input"]["replicates"]),
        **d,
    }
    for rep in contract["engine_input"]["replicates"]:
        rows[f"seed_{int(rep['replicate_index'])}"] = int(rep["seed"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{k}\t{v}" for k, v in rows.items()) + "\n", encoding="utf-8")


def prepare(root: Path) -> tuple[dict[str, Any], list[Check]]:
    cfg = load_json(root / CFG_REL)
    r42_cfg = load_json(root / R42_CFG_REL)
    seal = load_json(root / R42_SEAL_REL) if (root / R42_SEAL_REL).exists() else {}
    jobs_doc = load_json(root / R42_JOBS_REL) if (root / R42_JOBS_REL).exists() else {}
    artifacts = load_json(root / R42_ARTIFACTS_REL) if (root / R42_ARTIFACTS_REL).exists() else {}
    mapping42 = load_json(root / R42_MAPPING_REL) if (root / R42_MAPPING_REL).exists() else {}
    authority = load_json(root / R41_AUTH_REL) if (root / R41_AUTH_REL).exists() else {}
    checks = [
        Check("r42_parent_seal_present", (root / R42_SEAL_REL).exists(), str(R42_SEAL_REL).replace("\\", "/")),
        Check("r42_parent_sealed", seal.get("status") == R42_SEALED, seal.get("status")),
        Check("canonical_owner_arcana", cfg["canonical_state_owner"] == "ARCANA_WorldSim"),
        Check("canonical_state_unchanged", cfg["canonical_state_changed"] is False),
        Check("no_external_direct_write", cfg["external_engine_direct_canonical_write"] is False),
        Check("no_auto_promotion", cfg["automatic_external_evidence_promotion"] is False),
        Check("deep_off", cfg["deep_biological_coupling"] is False),
        Check("exact_23_frozen_jobs", jobs_doc.get("job_count") == 23 and len(jobs_doc.get("jobs", [])) == 23, jobs_doc.get("job_count")),
        Check("frozen_jobs_unique", len({j.get("job_id") for j in jobs_doc.get("jobs", [])}) == 23),
        Check("r42_jobs_still_unexecuted", all(j.get("execution_status") == "FROZEN_NOT_EXECUTED_IN_R42" for j in jobs_doc.get("jobs", []))),
        Check("r42_mapping_pre_result", mapping42.get("status") == "FROZEN_PRE_RESULT", mapping42.get("status")),
        Check("authority_no_majority_vote", authority.get("majority_vote") is False, authority.get("majority_vote")),
        Check("seven_windows_preserved", len(r42_cfg.get("windows", [])) == 7),
    ]
    if any(not c.passed for c in checks):
        report = {"stage": STAGE, "status": BLOCKED, "checks": [c.to_dict() for c in checks], "checks_failed": sum(not c.passed for c in checks)}
        write_json(root / OUT_REL / "R4_3_PREEXECUTION_AUDIT.json", report)
        return report, checks

    try:
        descriptors = build_window_descriptors(root, r42_cfg, artifacts)
        checks.append(Check("all_7_baseline_descriptors_materialized", len(descriptors) == 7, sorted(descriptors)))
        hash_mismatches = []
        for d in descriptors.values():
            refs = d.get("selected_frozen_artifacts", [d.get("selected_frozen_artifact")])
            for ref in refs:
                if ref and not ref.get("hash_match"):
                    hash_mismatches.append(ref.get("path"))
        checks.append(Check("all_selected_frozen_artifact_hashes_match", not hash_mismatches, hash_mismatches))
        phys = root / cfg["physical_companion_source"]
        checks.append(Check("physical_companion_present", phys.exists(), cfg["physical_companion_source"]))
        mappings, ledger, contracts = build_job_materialization(root, cfg, r42_cfg, jobs_doc, authority, descriptors)
        checks.append(Check("exact_23_per_job_mappings", len(mappings) == 23, len(mappings)))
        checks.append(Check("all_mappings_pre_result", all(x["pre_result_frozen"] for x in mappings)))
        checks.append(Check("every_job_has_domain_authority_mapping", all(len(x["domain_mapping"]) >= 1 for x in mappings), {x["job_id"]: len(x["domain_mapping"]) for x in mappings}))
        checks.append(Check("seed_ledger_exact_23", len(ledger["jobs"]) == 23))
        checks.append(Check("no_duplicate_seeds_global", len({r["seed"] for j in ledger["jobs"] for r in j["replicates"]}) == sum(len(j["replicates"]) for j in ledger["jobs"])))
    except Exception as exc:
        checks.append(Check("materialization_exception", False, repr(exc)))
        descriptors, mappings, ledger, contracts = {}, [], {"stage": STAGE, "jobs": []}, []

    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "R4_3_FROZEN_JOB_REGISTRY.json", {
        "stage": STAGE,
        "source": str(R42_JOBS_REL),
        "source_sha256": sha256_file(root / R42_JOBS_REL),
        "r42_job_matrix_canonical_sha256": canonical_sha256(jobs_doc),
        "job_count": jobs_doc.get("job_count"),
        "jobs": jobs_doc.get("jobs", []),
        "unchanged_from_r42": True,
    })
    write_json(out / "R4_3_WINDOW_BASELINE_DESCRIPTORS.json", {"stage": STAGE, "windows": descriptors})
    write_json(out / "R4_3_PER_JOB_UNIT_MAPPING.json", {"stage": STAGE, "mapping_count": len(mappings), "mappings": mappings})
    write_json(out / "R4_3_SEED_LEDGER.json", ledger)
    for c in contracts:
        job_dir = out / "jobs" / c["frozen_parent_job"]["job_id"]
        job_dir.mkdir(parents=True, exist_ok=True)
        write_json(job_dir / "JOB_CONTRACT.json", c)
        _write_tsv_config(job_dir / "ENGINE_CONFIG.tsv", c)
        # Do not delete raw evidence here; preparation may be safely re-run for auditing.
    failed = [c for c in checks if not c.passed]
    status = PREPARED if not failed else BLOCKED
    report = {
        "stage": STAGE,
        "status": status,
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "job_count": len(contracts),
        "window_count": len(descriptors),
        "replicate_count": sum(len(j["replicates"]) for j in ledger.get("jobs", [])),
        "canonical_state_changed": False,
        "historical_engine_execution_performed": False,
        "next_action": "EXECUTE_FROZEN_R43_23_ENGINE_WINDOW_JOBS" if not failed else "REPAIR_R43_MAPPING_OR_PARENT_GOVERNANCE",
        "checks": [c.to_dict() for c in checks],
    }
    write_json(out / "R4_3_PREEXECUTION_AUDIT.json", report)
    return report, checks


def _load_raw(job_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    p = job_dir / "RAW_EVIDENCE.json"
    if not p.exists():
        return None, "MISSING_EVIDENCE"
    try:
        return load_json(p), None
    except Exception as exc:
        return None, f"RAW_EVIDENCE_PARSE_ERROR:{exc!r}"


def _replicate_metrics(raw: dict[str, Any]) -> list[dict[str, Any]]:
    reps = raw.get("replicates", [])
    return [x.get("metrics", {}) for x in reps if isinstance(x, dict) and x.get("status") == "PASS" and isinstance(x.get("metrics"), dict)]


def _norm_stats(values: list[float]) -> dict[str, Any]:
    return _summary(np.asarray(values, dtype=float))


def normalize_raw(engine: str, raw: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    metrics = _replicate_metrics(raw)
    norm: dict[str, Any] = {}
    # Keep normalization intentionally conservative: only within-engine ratios/deltas.
    pairs = {
        "population_response_ratio": ("initial_abundance", "final_abundance"),
        "occupancy_response_ratio": ("initial_occupied_cells", "final_occupied_cells"),
        "population_agent_response_ratio": ("initial_population", "final_population"),
        "cohort_response_ratio": ("initial_cohort_count", "final_cohort_count"),
        "stock_response_ratio": ("initial_stock_count", "final_stock_count"),
        "heterotroph_biomass_response_ratio": ("initial_heterotroph_biomass", "final_heterotroph_biomass"),
        "autotroph_biomass_response_ratio": ("initial_autotroph_biomass", "final_autotroph_biomass"),
        "genetic_gap_response_ratio": ("initial_mean_frequency_gap", "final_mean_frequency_gap"),
        "heterozygosity_response_ratio": ("initial_heterozygosity", "final_heterozygosity"),
        "patch_occupancy_response_ratio": ("initial_occupied_patches", "final_occupied_patches"),
    }
    for out_name, (a, b) in pairs.items():
        vals=[]
        for m in metrics:
            r=_ratio(m.get(b), m.get(a))
            if r is not None: vals.append(r)
        if vals: norm[out_name]=_norm_stats(vals)
    deltas = {
        "allele_frequency_gap_delta": ("initial_mean_frequency_gap", "final_mean_frequency_gap"),
        "ancestry_fraction_delta": ("initial_ancestry_fraction", "final_ancestry_fraction"),
        "trait_mean_delta": ("initial_trait_mean", "final_trait_mean"),
        "genetic_variance_delta": ("initial_genetic_variance", "final_genetic_variance"),
    }
    for out_name,(a,b) in deltas.items():
        vals=[]
        for m in metrics:
            d=_delta(m.get(b),m.get(a))
            if d is not None: vals.append(d)
        if vals: norm[out_name]=_norm_stats(vals)
    return {
        "stage": STAGE,
        "job_id": contract["frozen_parent_job"]["job_id"],
        "engine": engine,
        "normalization_semantics": "WITHIN_ENGINE_DIMENSIONLESS_RESPONSE_ONLY_NO_RAW_N_EQUIVALENCE",
        "successful_replicates": len(metrics),
        "requested_replicates": len(contract["engine_input"]["replicates"]),
        "normalized_metrics": norm,
        "arcana_comparison_target_preserved_not_adjudicated": contract["comparison_target"],
        "discordance_class": None,
        "canonical_write": False,
    }


def collect(root: Path) -> tuple[dict[str, Any], list[Check]]:
    prep = load_json(root / OUT_REL / "R4_3_PREEXECUTION_AUDIT.json") if (root / OUT_REL / "R4_3_PREEXECUTION_AUDIT.json").exists() else {}
    jobs_doc = load_json(root / R42_JOBS_REL)
    checks = [
        Check("r43_prepared", prep.get("status") == PREPARED, prep.get("status")),
        Check("exact_23_frozen_jobs_collect", len(jobs_doc.get("jobs", [])) == 23),
    ]
    rows = []
    for j in jobs_doc["jobs"]:
        job_dir = root / OUT_REL / "jobs" / j["job_id"]
        required = {
            "JOB_CONTRACT.json": job_dir / "JOB_CONTRACT.json",
            "ENGINE_CONFIG.tsv": job_dir / "ENGINE_CONFIG.tsv",
            "RAW_EVIDENCE.json": job_dir / "RAW_EVIDENCE.json",
            "STDOUT.log": job_dir / "STDOUT.log",
            "STDERR.log": job_dir / "STDERR.log",
        }
        missing = [name for name, path in required.items() if not path.exists()]
        if missing:
            rows.append({
                "job_id": j["job_id"], "engine": j["engine"], "terminal_class": "MISSING_EVIDENCE",
                "status": "BLOCKED", "error": "MISSING_REQUIRED_EVIDENCE_BUNDLE_FILES", "missing": missing,
                "scientific_discordance_adjudicated": False,
            })
            continue

        contract = load_json(required["JOB_CONTRACT.json"])
        raw, err = _load_raw(job_dir)
        if raw is None:
            rows.append({
                "job_id": j["job_id"], "engine": j["engine"], "terminal_class": "MISSING_EVIDENCE",
                "status": "BLOCKED", "error": err, "scientific_discordance_adjudicated": False,
            })
            continue

        expected_specs = contract["engine_input"]["replicates"]
        expected = len(expected_specs)
        reps = raw.get("replicates", []) if isinstance(raw, dict) else []
        pass_reps = sum(1 for r in reps if isinstance(r, dict) and r.get("status") == "PASS")
        expected_seed_pairs = sorted((int(x["replicate_index"]), int(x["seed"])) for x in expected_specs)
        observed_seed_pairs = sorted(
            (int(x.get("replicate_index", -999)), int(x.get("seed", -999)))
            for x in reps if isinstance(x, dict)
        )
        identity_ok = raw.get("job_id") == j["job_id"] and raw.get("engine") == j["engine"]
        seed_ledger_ok = observed_seed_pairs == expected_seed_pairs
        no_write_declared = raw.get("canonical_write") is False

        if not identity_ok or not seed_ledger_ok or not no_write_declared:
            terminal = "ADAPTER_FAILURE"
            status = "BLOCKED"
        elif raw.get("adapter_status") == "SEMANTIC_NONCOMPARABILITY":
            # Meaningful noncomparability is admissible evidence only when the governed engine execution itself completed.
            terminal = "SEMANTIC_NONCOMPARABILITY" if pass_reps == expected else "ENGINE_EXECUTION_FAILURE"
            status = "PASS_EVIDENCE" if pass_reps == expected else "BLOCKED"
        elif raw.get("adapter_status") != "PASS":
            terminal = "ADAPTER_FAILURE" if raw.get("adapter_status") == "ADAPTER_FAILURE" else "ENGINE_EXECUTION_FAILURE"
            status = "BLOCKED"
        elif pass_reps != expected:
            terminal = "ENGINE_EXECUTION_FAILURE"
            status = "BLOCKED"
        else:
            terminal = "SCIENTIFIC_RESULT"
            status = "PASS_EVIDENCE"

        normalized = normalize_raw(j["engine"], raw, contract) if terminal == "SCIENTIFIC_RESULT" else {
            "stage": STAGE, "job_id": j["job_id"], "engine": j["engine"], "normalized_metrics": {},
            "discordance_class": None, "reason": terminal, "canonical_write": False,
        }
        write_json(job_dir / "NORMALIZED_EVIDENCE.json", normalized)
        audit = {
            "stage": STAGE,
            "job_id": j["job_id"],
            "engine": j["engine"],
            "status": status,
            "terminal_class": terminal,
            "requested_replicates": expected,
            "observed_replicates": len(reps),
            "successful_replicates": pass_reps,
            "job_engine_identity_match": identity_ok,
            "seed_ledger_match": seed_ledger_ok,
            "canonical_write_declared_false": no_write_declared,
            "raw_evidence_sha256": sha256_file(job_dir / "RAW_EVIDENCE.json"),
            "normalized_evidence_sha256": sha256_file(job_dir / "NORMALIZED_EVIDENCE.json"),
            "stdout_sha256": sha256_file(job_dir / "STDOUT.log"),
            "stderr_sha256": sha256_file(job_dir / "STDERR.log"),
            "canonical_write": False,
            "scientific_discordance_adjudicated": False,
        }
        write_json(job_dir / "JOB_AUDIT.json", audit)
        rows.append(audit)

    classes = ["SCIENTIFIC_RESULT", "SEMANTIC_NONCOMPARABILITY", "ENGINE_EXECUTION_FAILURE", "ADAPTER_FAILURE", "MISSING_EVIDENCE"]
    terminal_counts = {k: sum(1 for r in rows if r.get("terminal_class") == k) for k in classes}
    blocked = terminal_counts["ENGINE_EXECUTION_FAILURE"] + terminal_counts["ADAPTER_FAILURE"] + terminal_counts["MISSING_EVIDENCE"]
    checks.extend([
        Check("all_23_jobs_have_terminal_audit", len(rows) == 23, len(rows)),
        Check("all_23_jobs_terminal_nonblocked", blocked == 0, terminal_counts),
        Check("all_evidence_bundle_identities_match", all(r.get("job_engine_identity_match") is True for r in rows), None),
        Check("all_evidence_seed_ledgers_match", all(r.get("seed_ledger_match") is True for r in rows), None),
        Check("all_raw_evidence_declares_no_canonical_write", all(r.get("canonical_write_declared_false") is True for r in rows), None),
        Check("no_scientific_adjudication_in_r43", all(r.get("scientific_discordance_adjudicated") is False for r in rows)),
    ])
    status = EXECUTION_COMPLETE if blocked == 0 and all(c.passed for c in checks) else BLOCKED
    summary = {
        "stage": STAGE,
        "status": status,
        "job_count": 23,
        "terminal_counts": terminal_counts,
        "jobs": rows,
        "canonical_state_changed": False,
        "scientific_agreement_claimed": False,
        "discordance_adjudication_performed": False,
        "next_action": "RUN_R43_FINAL_SEAL" if status == EXECUTION_COMPLETE else "REPAIR_FAILED_R43_ENGINE_OR_ADAPTER_JOBS",
    }
    write_json(root / OUT_REL / "R4_3_EXECUTION_SUMMARY.json", summary)
    audit = {
        "stage": STAGE,
        "status": status,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "terminal_counts": terminal_counts,
        "canonical_state_changed": False,
        "checks": [c.to_dict() for c in checks],
    }
    write_json(root / OUT_REL / "R4_3_COMPLETENESS_AUDIT.json", audit)
    return audit, checks

def final_seal(root: Path) -> dict[str, Any]:
    audit, _ = collect(root)
    cfg = load_json(root / CFG_REL)
    parent = load_json(root / R42_SEAL_REL) if (root / R42_SEAL_REL).exists() else {}
    summary_path = root / OUT_REL / "R4_3_EXECUTION_SUMMARY.json"
    summary = load_json(summary_path) if summary_path.exists() else {}
    tc = summary.get("terminal_counts", {})
    blocked = sum(int(tc.get(k, 0)) for k in ("ENGINE_EXECUTION_FAILURE", "ADAPTER_FAILURE", "MISSING_EVIDENCE"))
    terminal_total = sum(int(v) for v in tc.values()) if tc else 0
    checks = [
        Check("parent_r42_sealed", parent.get("status") == R42_SEALED, parent.get("status")),
        Check("r43_completeness_audit_pass", audit.get("status") == EXECUTION_COMPLETE, audit.get("status")),
        Check("r43_completeness_zero_failed_checks", audit.get("checks_failed") == 0, audit.get("checks_failed")),
        Check("exact_23_terminal_jobs", terminal_total == 23, terminal_total),
        Check("zero_blocked_terminal_jobs", blocked == 0, tc),
        Check("baseline_a_preserved", cfg.get("baseline_a") == "ARCANA_REDUCED_ORDER_R3_19_TO_R3_39", cfg.get("baseline_a")),
        Check("canonical_state_unchanged", cfg.get("canonical_state_changed") is False),
        Check("deep_biological_coupling_off", cfg.get("deep_biological_coupling") is False),
        Check("scientific_agreement_not_claimed", summary.get("scientific_agreement_claimed") is False),
        Check("discordance_adjudication_not_performed", summary.get("discordance_adjudication_performed") is False),
    ]
    ok = all(c.passed for c in checks)
    seal = {
        "stage": STAGE,
        "audit": "FINAL_FROZEN_23_ENGINE_WINDOW_HISTORICAL_REVALIDATION_EXECUTION_AND_NORMALIZATION",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks],
        "summary": {
            "parent_r42_sealed": parent.get("status") == R42_SEALED,
            "frozen_job_count": 23,
            "terminal_counts": tc,
            "historical_execution_performed": bool(ok),
            "all_jobs_terminal_nonblocked": blocked == 0 and terminal_total == 23,
            "canonical_state_changed": False,
            "baseline_a_preserved": True,
            "deep_biological_coupling": False,
            "scientific_agreement_claimed": False,
            "discordance_adjudication_performed": False,
            "next_action": "BUILD_R44_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX_AND_ADJUDICATION" if ok else "REPAIR_R43_EXECUTION_OR_MAPPING_FAILURES",
        },
    }
    write_json(root / SEAL_REL, seal)
    return seal

