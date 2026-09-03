from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math

import numpy as np

STAGE = "v0.6D1-R3.21"
EXPECTED_R319_JSON_SHA256 = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
EXPECTED_R319_NPZ_SHA256 = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_PRESENT_SPECIES = 134
EXPECTED_PRESENT_COMPONENTS = 295
EXPECTED_TOTAL_POPULATION = 1217.2506240828814
EXPECTED_Q_CEILING = 0.08


class R321GateError(RuntimeError):
    """Fail-closed R3.21 governance/closure error."""


@dataclass(frozen=True)
class R321Config:
    occupancy_floor: float = 1e-12
    population_abs_tolerance: float = 1e-9
    require_exact_r319_hashes: bool = True


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    raise TypeError(type(value).__name__)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )


def load_checkpoint_files(
    checkpoint_json: Path,
    checkpoint_npz: Path,
    cfg: R321Config = R321Config(),
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, str]]:
    checkpoint_json = Path(checkpoint_json)
    checkpoint_npz = Path(checkpoint_npz)
    if not checkpoint_json.is_file() or not checkpoint_npz.is_file():
        raise R321GateError("R3.19 checkpoint JSON/NPZ pair is missing")

    hashes = {
        "json_sha256": sha256_file(checkpoint_json),
        "npz_sha256": sha256_file(checkpoint_npz),
    }
    if cfg.require_exact_r319_hashes:
        if hashes["json_sha256"] != EXPECTED_R319_JSON_SHA256:
            raise R321GateError(
                f"R3.19 JSON hash mismatch: {hashes['json_sha256']} != {EXPECTED_R319_JSON_SHA256}"
            )
        if hashes["npz_sha256"] != EXPECTED_R319_NPZ_SHA256:
            raise R321GateError(
                f"R3.19 NPZ hash mismatch: {hashes['npz_sha256']} != {EXPECTED_R319_NPZ_SHA256}"
            )

    metadata = json.loads(checkpoint_json.read_text(encoding="utf-8"))
    with np.load(checkpoint_npz, allow_pickle=False) as z:
        arrays = {k: np.array(z[k], copy=True) for k in z.files}
    return metadata, arrays, hashes


def _walk(obj: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path, str(k), v
            yield from _walk(v, path + (str(k),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, path + (str(i),))


def _find_json_key(metadata: dict[str, Any], key: str, default: Any = None, required: bool = False) -> Any:
    found: list[tuple[tuple[str, ...], Any]] = []
    if key in metadata:
        found.append(((), metadata[key]))
    for path, k, v in _walk(metadata):
        if k == key and not (not path and key in metadata):
            found.append((path, v))
    if not found:
        if required:
            raise R321GateError(f"Required checkpoint JSON field not found: {key}")
        return default
    # Prefer the shallowest canonical occurrence. Multiple diagnostic echoes are allowed.
    found.sort(key=lambda x: len(x[0]))
    return found[0][1]


def _find_array(arrays: dict[str, np.ndarray], *aliases: str, required: bool = True) -> np.ndarray | None:
    for k in aliases:
        if k in arrays:
            return arrays[k]
    lowered = {k.lower(): k for k in arrays}
    for k in aliases:
        hit = lowered.get(k.lower())
        if hit is not None:
            return arrays[hit]
    if required:
        raise R321GateError(f"Required checkpoint NPZ array not found; aliases={aliases}; keys={sorted(arrays)}")
    return None


def _as_str_list(value: Any, field: str) -> list[str]:
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if not isinstance(value, list):
        raise R321GateError(f"{field} must be a list")
    return [str(x) for x in value]


def _normalize_registry(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, dict):
        rows = []
        for k, v in raw.items():
            if isinstance(v, dict):
                row = dict(v)
                row.setdefault("species_id", str(k))
                rows.append(row)
    elif isinstance(raw, list):
        rows = [dict(x) for x in raw if isinstance(x, dict)]
    else:
        raise R321GateError("checkpoint registry is neither dict nor list")

    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        sid = row.get("species_id") or row.get("lineage_id") or row.get("daughter_species_id")
        if sid is None:
            raise R321GateError("registry row lacks species_id")
        sid = str(sid)
        if sid in out and out[sid] != row:
            raise R321GateError(f"duplicate non-identical registry entry for {sid}")
        out[sid] = row
    if not out:
        raise R321GateError("empty historical species registry")
    return out


def _normalize_events(raw: Any) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if raw is None:
        return events
    if isinstance(raw, list):
        for i, e in enumerate(raw):
            if isinstance(e, dict):
                row = dict(e)
                row.setdefault("_event_index", i)
                row.setdefault("_event_type", str(row.get("event_type", row.get("event", row.get("type", "event")))))
                events.append(row)
        return events
    if isinstance(raw, dict):
        for category, seq in raw.items():
            if isinstance(seq, list):
                for i, e in enumerate(seq):
                    if isinstance(e, dict):
                        row = dict(e)
                        row.setdefault("_event_index", i)
                        row.setdefault("_event_type", str(row.get("event_type", row.get("event", row.get("type", category)))))
                        events.append(row)
            elif isinstance(seq, dict):
                row = dict(seq)
                row.setdefault("_event_type", str(row.get("event_type", row.get("event", row.get("type", category)))))
                events.append(row)
        return events
    raise R321GateError("checkpoint events field has unsupported type")


def _event_species_refs(event: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for k, v in event.items():
        lk = k.lower()
        if "species" not in lk and "lineage" not in lk:
            continue
        if isinstance(v, str):
            refs.add(v)
        elif isinstance(v, list):
            refs.update(str(x) for x in v if isinstance(x, (str, int)))
    return refs


def _event_component_refs(event: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for k, v in event.items():
        lk = k.lower()
        if not any(token in lk for token in ("deme", "component")):
            continue
        if isinstance(v, str):
            refs.add(v)
        elif isinstance(v, list):
            refs.update(str(x) for x in v if isinstance(x, (str, int)))
    return refs


def _is_extinction_event(event: dict[str, Any]) -> bool:
    text = " ".join(
        str(event.get(k, "")) for k in ("_event_type", "event_type", "event", "type", "semantic_status", "status")
    ).lower()
    return "extinct" in text or "extinction" in text


def _parent_of(row: dict[str, Any]) -> str | None:
    p = row.get("parent_species_id")
    if p in (None, "", "None"):
        return None
    return str(p)


def _ancestry_chain(sid: str, registry: dict[str, dict[str, Any]]) -> list[str]:
    chain = [sid]
    seen = {sid}
    cur = sid
    while True:
        parent = _parent_of(registry[cur])
        if parent is None:
            break
        if parent not in registry:
            raise R321GateError(f"lineage {sid} references missing parent {parent}")
        if parent in seen:
            raise R321GateError(f"cycle detected in ancestry of {sid}: {parent}")
        chain.append(parent)
        seen.add(parent)
        cur = parent
    chain.reverse()
    return chain


def _weighted_grid_summary(pop: np.ndarray, occupancy_floor: float) -> dict[str, Any]:
    positive = pop > occupancy_floor
    occupied = int(np.count_nonzero(positive))
    total = float(pop.sum())
    out: dict[str, Any] = {"occupied_grid_cells": occupied, "population_total": total}
    if pop.ndim == 2 and total > 0:
        ii, jj = np.indices(pop.shape)
        out.update(
            {
                "grid_shape": [int(pop.shape[0]), int(pop.shape[1])],
                "population_weighted_row": float((ii * pop).sum() / total),
                "population_weighted_col": float((jj * pop).sum() / total),
            }
        )
        where = np.argwhere(positive)
        if len(where):
            out["occupied_row_minmax"] = [int(where[:, 0].min()), int(where[:, 0].max())]
            out["occupied_col_minmax"] = [int(where[:, 1].min()), int(where[:, 1].max())]
    return out


def _array_row(arr: np.ndarray | None, idx: int) -> Any:
    if arr is None:
        return None
    return np.asarray(arr[idx]).tolist()


def _detect_deep_off(metadata: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    evidence: list[dict[str, Any]] = []
    forbidden_true_names = {
        "deep_adaptation_enabled",
        "deep_biological_coupling",
        "deep_coupling_enabled",
        "deep_enabled",
    }
    for path, k, v in _walk(metadata):
        lk = k.lower()
        if lk in forbidden_true_names and isinstance(v, (bool, int)):
            evidence.append({"path": ".".join(path + (k,)), "value": bool(v)})
    if not evidence:
        # R3.21 does not invent a state value if the checkpoint omits the duplicated diagnostic.
        return True, [{"path": "checkpoint_authority", "value": "R3.19 SEALED H0 / Deep OFF"}]
    return all(not bool(x["value"]) for x in evidence), evidence


def build_registry_from_loaded(
    metadata: dict[str, Any],
    arrays: dict[str, np.ndarray],
    *,
    source_hashes: dict[str, str] | None = None,
    cfg: R321Config = R321Config(),
    enforce_canonical_counts: bool = True,
) -> dict[str, Any]:
    component_ids = _as_str_list(_find_json_key(metadata, "component_ids", required=True), "component_ids")
    current_species = _as_str_list(_find_json_key(metadata, "current_species", required=True), "current_species")
    root_species = _as_str_list(_find_json_key(metadata, "root_species", required=True), "root_species")
    registry = _normalize_registry(_find_json_key(metadata, "registry", required=True))
    events = _normalize_events(_find_json_key(metadata, "events", default=[]))

    ncomp = len(component_ids)
    if len(current_species) != ncomp or len(root_species) != ncomp:
        raise R321GateError("component_ids/current_species/root_species length mismatch")
    if len(set(component_ids)) != ncomp:
        raise R321GateError("component IDs are not unique")

    pop = _find_array(arrays, "pop", "population", "endpoint_population")
    guild = _find_array(arrays, "guild", "deme_guild_id", "guild_id")
    trait = _find_array(arrays, "trait", "endpoint_trait")
    va = _find_array(arrays, "va", "endpoint_additive_variance")
    gen = _find_array(arrays, "gen", "generation_time", "generation_time_proxy_years")
    accessible = _find_array(arrays, "current_accessible", "accessible", required=False)
    va_within = _find_array(arrays, "reduced_va_within", "va_within", required=False)
    ancestry_cov = _find_array(arrays, "reduced_ancestry_covariance", "ancestry_covariance", required=False)
    segregation = _find_array(
        arrays,
        "reduced_neutral_segregation_potential",
        "neutral_segregation_potential",
        required=False,
    )
    adaptive_coordinate = _find_array(
        arrays,
        "reduced_adaptive_coordinate",
        "adaptive_coordinate",
        required=False,
    )

    for name, arr in (("pop", pop), ("guild", guild), ("trait", trait), ("va", va), ("gen", gen)):
        if arr is None or arr.shape[0] != ncomp:
            raise R321GateError(f"{name} first dimension must equal component count {ncomp}")
    if not np.isfinite(pop).all() or np.any(pop < 0):
        raise R321GateError("population array is non-finite or negative")
    if not np.isfinite(trait).all() or not np.isfinite(va).all() or not np.isfinite(gen).all():
        raise R321GateError("trait/VA/generation arrays must be finite")
    if np.any(va < 0) or np.any(gen <= 0):
        raise R321GateError("VA must be nonnegative and generation times positive")
    if accessible is not None:
        if accessible.shape != pop.shape[1:]:
            raise R321GateError("current_accessible shape does not match spatial population grid")
        inaccessible_mass = float(pop[:, ~accessible.astype(bool)].sum())
    else:
        inaccessible_mass = None

    present_species = sorted(set(current_species))
    missing_registry = sorted(set(present_species) - set(registry))
    if missing_registry:
        raise R321GateError(f"present species missing from registry: {missing_registry[:10]}")

    # Validate every historical parent edge, not just present leaves.
    ancestry_cache: dict[str, list[str]] = {}
    for sid in registry:
        ancestry_cache[sid] = _ancestry_chain(sid, registry)

    extinct_direct: set[str] = set()
    for event in events:
        if _is_extinction_event(event):
            extinct_direct |= _event_species_refs(event)
    resurrected = sorted(set(present_species) & extinct_direct)
    if resurrected:
        raise R321GateError(f"species marked extinct are present at 0 ka: {resurrected}")

    total_population = float(pop.sum())
    if enforce_canonical_counts:
        if len(present_species) != EXPECTED_PRESENT_SPECIES:
            raise R321GateError(f"present species {len(present_species)} != {EXPECTED_PRESENT_SPECIES}")
        if ncomp != EXPECTED_PRESENT_COMPONENTS:
            raise R321GateError(f"components {ncomp} != {EXPECTED_PRESENT_COMPONENTS}")
        if not math.isclose(total_population, EXPECTED_TOTAL_POPULATION, rel_tol=0.0, abs_tol=cfg.population_abs_tolerance):
            raise R321GateError(
                f"population {total_population:.17g} != {EXPECTED_TOTAL_POPULATION:.17g} within {cfg.population_abs_tolerance}"
            )
        if inaccessible_mass is not None and inaccessible_mass != 0.0:
            raise R321GateError(f"nonzero population on inaccessible exact-0ka support: {inaccessible_mass}")

    deep_off, deep_evidence = _detect_deep_off(metadata)
    if not deep_off:
        raise R321GateError("Deep biological coupling is enabled in an R3.21 input")

    component_event_map: dict[str, list[int]] = {cid: [] for cid in component_ids}
    species_event_map: dict[str, list[int]] = {sid: [] for sid in registry}
    event_rows: list[dict[str, Any]] = []
    for ei, event in enumerate(events):
        eref = {
            "event_id": f"E{ei:06d}",
            "event_type": str(event.get("_event_type", event.get("event_type", event.get("type", "event")))),
            "age_ma": event.get("age_ma"),
            "relative_year": event.get("relative_year"),
            "species_refs": sorted(_event_species_refs(event)),
            "component_refs": sorted(_event_component_refs(event)),
            "raw": {k: v for k, v in event.items() if not k.startswith("_")},
        }
        event_rows.append(eref)
        for sid in eref["species_refs"]:
            if sid in species_event_map:
                species_event_map[sid].append(ei)
        for cid in eref["component_refs"]:
            if cid in component_event_map:
                component_event_map[cid].append(ei)

    component_rows: list[dict[str, Any]] = []
    species_to_components: dict[str, list[int]] = {sid: [] for sid in present_species}
    for i, cid in enumerate(component_ids):
        sid = current_species[i]
        species_to_components[sid].append(i)
        component_rows.append(
            {
                "component_id": cid,
                "species_id": sid,
                "root_species_id": root_species[i],
                "guild_id": int(np.asarray(guild[i]).reshape(-1)[0]),
                "population_total": float(pop[i].sum()),
                "range_grid_summary": _weighted_grid_summary(pop[i], cfg.occupancy_floor),
                "legacy_ecological_trait_vector": _array_row(trait, i),
                "additive_variance_vector": _array_row(va, i),
                "generation_time_proxy_years": float(np.asarray(gen[i]).reshape(-1)[0]),
                "va_within": _array_row(va_within, i) if va_within is not None and va_within.shape[0] == ncomp else None,
                "adaptive_coordinate": _array_row(adaptive_coordinate, i)
                if adaptive_coordinate is not None and adaptive_coordinate.shape[0] == ncomp
                else None,
                "historical_event_ids": [f"E{x:06d}" for x in component_event_map.get(cid, [])],
            }
        )

    species_rows: list[dict[str, Any]] = []
    for sid in present_species:
        idx = species_to_components[sid]
        reg = registry[sid]
        chain = ancestry_cache[sid]
        sp_pop = float(sum(float(pop[i].sum()) for i in idx))
        weighted_gen = sum(float(pop[i].sum()) * float(np.asarray(gen[i]).reshape(-1)[0]) for i in idx)
        weighted_gen = weighted_gen / sp_pop if sp_pop > 0 else None
        occupied = int(sum(np.count_nonzero(pop[i] > cfg.occupancy_floor) for i in idx))
        species_event_ids: set[str] = set()
        for ancestor in chain:
            species_event_ids.update(f"E{x:06d}" for x in species_event_map.get(ancestor, []))
        species_rows.append(
            {
                "lineage_id": sid,
                "species_id": sid,
                "status": "PRESENT_0KA_H0",
                "parent_species_id": _parent_of(reg),
                "root_species_id": str(reg.get("root_species_id", chain[0])),
                "ancestry_chain_root_to_present": chain,
                "lineage_depth": len(chain) - 1,
                "birth_relative_year": reg.get("birth_relative_year"),
                "birth_age_ma": reg.get("birth_age_ma"),
                "semantic_status": reg.get("semantic_status"),
                "trait_provenance": reg.get("trait_provenance"),
                "guild_id": int(reg.get("guild_id", np.asarray(guild[idx[0]]).reshape(-1)[0])),
                "component_ids": [component_ids[i] for i in idx],
                "component_count": len(idx),
                "population_total": sp_pop,
                "occupied_component_grid_cells": occupied,
                "population_weighted_generation_time_proxy_years": weighted_gen,
                "historical_event_ids_ancestry_scoped": sorted(species_event_ids),
                "functional_phenotype": {
                    "status": "NOT_MATERIALIZED_R3_21",
                    "values": None,
                    "human_readiness_score": None,
                },
            }
        )

    # R3.19 SEALED carries the four governed reduced genetic-state arrays.
    # R3.21 preserves them read-only and fails closed if the canonical state is
    # absent, malformed, or numerically invalid.
    reduced_arrays = {
        "reduced_va_within": va_within,
        "reduced_ancestry_covariance": ancestry_cov,
        "reduced_neutral_segregation_potential": segregation,
        "reduced_adaptive_coordinate": adaptive_coordinate,
    }
    missing_reduced = [k for k, arr in reduced_arrays.items() if arr is None]
    if missing_reduced:
        raise R321GateError(f"canonical reduced genetic state missing: {missing_reduced}")

    # Canonical R3.7/R3.8 reduced-state geometry:
    #   VA_within[deme, trait]
    #   C_ancestry_LD[deme, trait]
    #   S_neutral[deme, deme, trait]
    #   h[deme, trait]
    # Only S is pairwise. REV3 incorrectly imposed S geometry on ancestry/LD.
    if trait.ndim != 2:
        raise R321GateError("trait state must be a 2D component-by-trait array")
    ntrait = int(trait.shape[1])
    if va.shape != (ncomp, ntrait):
        raise R321GateError(f"production VA must have canonical component-by-trait shape ({ncomp}, {ntrait})")

    component_trait_states = (
        ("reduced_va_within", va_within, True),
        ("reduced_ancestry_covariance", ancestry_cov, False),
        ("reduced_adaptive_coordinate", adaptive_coordinate, False),
    )
    for name, arr, require_nonnegative in component_trait_states:
        if arr.shape != (ncomp, ntrait):
            raise R321GateError(f"{name} must have canonical component-by-trait shape ({ncomp}, {ntrait})")
        if not np.isfinite(arr).all():
            raise R321GateError(f"{name} contains non-finite values")
        if require_nonnegative and np.any(arr < 0):
            raise R321GateError(f"{name} contains negative values")

    if segregation.shape != (ncomp, ncomp, ntrait):
        raise R321GateError(
            "reduced_neutral_segregation_potential must have canonical "
            f"pairwise component-by-component-by-trait shape ({ncomp}, {ncomp}, {ntrait})"
        )
    if not np.isfinite(segregation).all():
        raise R321GateError("reduced_neutral_segregation_potential contains non-finite values")
    if np.any(segregation < 0):
        raise R321GateError("reduced_neutral_segregation_potential contains negative values")

    reduced_state = {
        "va_within_present": True,
        "ancestry_covariance_present": True,
        "neutral_segregation_potential_present": True,
        "adaptive_coordinate_present": True,
        "canonical_npz_keys": {
            "va_within": "reduced_va_within",
            "ancestry_covariance": "reduced_ancestry_covariance",
            "neutral_segregation_potential": "reduced_neutral_segregation_potential",
            "adaptive_coordinate": "reduced_adaptive_coordinate",
        },
        "shapes": {k: list(arr.shape) for k, arr in reduced_arrays.items()},
    }

    closure = {
        "stage": STAGE,
        "status": "PASS_R321_PRESENT_LINEAGE_REGISTRY_CLOSURE_CANDIDATE",
        "source_checkpoint": source_hashes or {},
        "present_species": len(present_species),
        "present_components": ncomp,
        "historical_registry_species": len(registry),
        "historical_events": len(event_rows),
        "total_population": total_population,
        "inaccessible_population_0ka": inaccessible_mass,
        "deep_biological_coupling_off": deep_off,
        "deep_evidence": deep_evidence,
        "no_new_biology_executed": True,
        "no_human_target": True,
        "no_functional_phenotype_values_materialized": True,
        "no_h0_or_cha2_mutation": True,
        "all_present_species_have_registry_entry": not missing_registry,
        "ancestry_graph_acyclic_and_parent_complete": True,
        "no_extinct_species_present": not resurrected,
        "population_accounting_error": float(sum(x["population_total"] for x in species_rows) - total_population),
        "reduced_state_presence": reduced_state,
    }

    return {
        "closure": closure,
        "present_lineages": species_rows,
        "present_components": component_rows,
        "historical_species_registry": [registry[k] for k in sorted(registry)],
        "historical_events": event_rows,
        "reduced_state_arrays": reduced_arrays,
        "component_ids": component_ids,
    }


def functional_phenotype_fork_interface(source_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    domains = [
        "manipulative_capability",
        "locomotor_flexibility",
        "cognitive_capacity",
        "learning_plasticity",
        "sociality",
        "dietary_flexibility",
        "life_history",
        "ecological_generalism",
        "tool_use_potential",
        "environmental_problem_solving_capability",
    ]
    return {
        "stage": STAGE,
        "interface_status": "SCHEMA_ONLY_NOT_MATERIALIZED",
        "source_checkpoint": source_hashes or {},
        "scope": "GENERIC_ALL_LINEAGES_NO_HUMAN_TARGET",
        "domains_reserved_for_r3_22": [
            {
                "domain": d,
                "value": None,
                "heritability": None,
                "evolvability": None,
                "metabolic_ecological_cost": None,
                "correlations": None,
                "status": "UNDEFINED_UNTIL_R3_22",
            }
            for d in domains
        ],
        "composite_human_readiness_score": None,
        "deep_coupling": "OFF",
        "rule": "R3.21 may expose the fork schema but MUST NOT assign, rank, optimize, or select lineages by these domains.",
    }


def materialize_r321(
    checkpoint_json: Path,
    checkpoint_npz: Path,
    output_dir: Path,
    cfg: R321Config = R321Config(),
) -> dict[str, Any]:
    metadata, arrays, hashes = load_checkpoint_files(checkpoint_json, checkpoint_npz, cfg)
    built = build_registry_from_loaded(metadata, arrays, source_hashes=hashes, cfg=cfg, enforce_canonical_counts=True)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "R3_21_PRESENT_LINEAGE_REGISTRY.json", {
        "stage": STAGE,
        "source_checkpoint": hashes,
        "lineages": built["present_lineages"],
    })
    write_json(output_dir / "R3_21_PRESENT_COMPONENT_REGISTRY.json", {
        "stage": STAGE,
        "source_checkpoint": hashes,
        "components": built["present_components"],
    })
    write_json(output_dir / "R3_21_HISTORICAL_LINEAGE_CLOSURE.json", {
        "stage": STAGE,
        "source_checkpoint": hashes,
        "historical_species_registry": built["historical_species_registry"],
        "historical_events": built["historical_events"],
    })
    reduced = built["reduced_state_arrays"]
    np.savez_compressed(
        output_dir / "R3_21_REDUCED_GENETIC_STATE.npz",
        component_ids=np.asarray(built["component_ids"], dtype="U"),
        reduced_va_within=reduced["reduced_va_within"],
        reduced_ancestry_covariance=reduced["reduced_ancestry_covariance"],
        reduced_neutral_segregation_potential=reduced["reduced_neutral_segregation_potential"],
        reduced_adaptive_coordinate=reduced["reduced_adaptive_coordinate"],
    )
    write_json(output_dir / "R3_21_REDUCED_GENETIC_STATE_SUMMARY.json", {
        "stage": STAGE,
        "source_checkpoint": hashes,
        "status": "READ_ONLY_CANONICAL_REDUCED_STATE_PRESERVED",
        "component_ordering": "R3.19 component_ids exact order",
        "arrays": {
            k: {"shape": list(v.shape), "dtype": str(v.dtype)}
            for k, v in reduced.items()
        },
        "reinterpretation_as_functional_phenotype": False,
    })
    write_json(output_dir / "R3_21_FUNCTIONAL_PHENOTYPE_FORK_INTERFACE.json", functional_phenotype_fork_interface(hashes))
    write_json(output_dir / "R3_21_AUDIT_SUMMARY.json", built["closure"])

    audit_md = "# v0.6D1-R3.21 — Present Lineage Registry Audit\n\n"
    audit_md += f"- status: `{built['closure']['status']}`\n"
    audit_md += f"- present species: `{built['closure']['present_species']}`\n"
    audit_md += f"- present components: `{built['closure']['present_components']}`\n"
    audit_md += f"- total population: `{built['closure']['total_population']:.16g}`\n"
    audit_md += f"- historical registry rows: `{built['closure']['historical_registry_species']}`\n"
    audit_md += f"- historical events indexed: `{built['closure']['historical_events']}`\n"
    audit_md += "- ancestry graph: `ACYCLIC / PARENT-COMPLETE`\n"
    audit_md += "- Deep biological coupling: `OFF`\n"
    audit_md += "- human target: `NONE`\n"
    audit_md += "- new functional phenotype values: `NONE`\n"
    audit_md += "- H0 / CHA-2 scientific mutation: `NONE`\n\n"
    audit_md += "R3.21 is a read-only derived registry stage. It does not advance biological time or alter the SEALED natural-control state.\n"
    (output_dir / "R3_21_AUDIT.md").write_text(audit_md, encoding="utf-8")

    manifest = {
        "stage": STAGE,
        "source_checkpoint": hashes,
        "files": {},
    }
    for p in sorted(output_dir.iterdir()):
        if p.is_file() and p.name != "R3_21_OUTPUT_MANIFEST.json":
            manifest["files"][p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    write_json(output_dir / "R3_21_OUTPUT_MANIFEST.json", manifest)
    return built["closure"]
