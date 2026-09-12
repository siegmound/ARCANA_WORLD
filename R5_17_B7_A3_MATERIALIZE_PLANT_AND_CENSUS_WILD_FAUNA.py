from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


HEAD_EXPECTED = "43463b57209927a1d6e8aedb8cb178105ad15e2b"
A1_SHA256 = "9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f"
R334_SHA256 = "31f5954b846be3cb4a6bb14afb2ae19e7cccafd47c90719a1434e9058bc35d86"
A1_AGES = [210.0, 180.0, 150.0, 140.0, 130.0, 120.0, 90.0, 66.0, 60.0, 30.0, 0.0]
RECENT_AGES = [20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0, 0.0]
A1_CHANNELS = ["browse_forage", "low_forage", "wetland_forage", "total_edible_forage"]
R334_FIELDS = ["suitability", "resource_abundance", "harvest_return", "propagation_opportunity"]

A2_PATH = Path("R5_17_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION.json")
OUT_JSON = Path("R5_17_B7_A3_PLANT_MATERIALIZATION_AND_WILD_FAUNA_AUTHORITY_CENSUS.json")
OUT_MD = Path("R5_17_B7_A3_PLANT_MATERIALIZATION_AND_WILD_FAUNA_AUTHORITY_CENSUS.md")


class GateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_file():
        return candidate.resolve()
    candidate = root / value
    if candidate.is_file():
        return candidate.resolve()
    raise GateError(f"Governed source is missing: {value}")


def record(path: Path, root: Path) -> dict[str, Any]:
    try:
        display = path.relative_to(root).as_posix()
    except ValueError:
        display = str(path)
    return {
        "path": display,
        "tracked": display in set(git("ls-files").splitlines()),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def finite_summary(array: np.ndarray) -> dict[str, Any]:
    finite = np.isfinite(array) if array.dtype.kind in "biufc" else None
    result: dict[str, Any] = {"shape": list(array.shape), "dtype": str(array.dtype), "size": int(array.size)}
    if finite is not None:
        result["finite"] = bool(finite.all())
        result["valid_count"] = int(finite.sum())
    return result


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise GateError(f"{label} mismatch: expected {expected!r}, got {actual!r}")


def deep_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for child in value.values():
            keys.update(deep_keys(child))
    elif isinstance(value, list):
        for child in value[:20]:
            keys.update(deep_keys(child))
    return keys


def fauna_candidate(path: Path, root: Path, *, role: str, temporal: str, spatial: str, semantics: str, suitable: bool) -> dict[str, Any]:
    if not path.is_file():
        raise GateError(f"Governed fauna candidate is missing: {path}")
    keys: list[str] = []
    if path.suffix == ".json":
        loaded = load_json(path)
        keys = sorted(deep_keys(loaded))
    return {
        **record(path, root),
        "producing_stage": role,
        "authority_status": "GOVERNED_PROVENANCE_CANDIDATE",
        "temporal_coverage": temporal,
        "spatial_coverage": spatial,
        "quantity_semantics": semantics,
        "observed_key_names": keys,
        "suitable_for_wild_animal_resource_support": suitable,
    }


def main() -> int:
    root = Path(__file__).resolve().parent
    head = git("rev-parse", "HEAD")
    require_equal(head, HEAD_EXPECTED, "repository HEAD")
    a2 = load_json(root / A2_PATH)
    require_equal(a2["status"], "PASS_R517_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATED", "A2 status")
    require_equal(a2["decision"], "AUTHORIZE_B7_A3_NATURAL_RESOURCE_COMPONENT_MATERIALIZATION_WITH_EXPLICIT_AQUATIC_MARINE_GAP", "A2 decision")

    a1_info = a2["semantic_bindings"]["plant_trophic_resource_support"]["authority"]
    a1_path = resolve_path(root, a1_info["path"])
    require_equal(sha256_file(a1_path), A1_SHA256, "A1 SHA256")
    with np.load(a1_path, allow_pickle=False) as a1:
        require_equal(a1["age_ma"].tolist(), A1_AGES, "A1 age anchors")
        require_equal(list(a1["lat"].shape), [90], "A1 latitude shape")
        require_equal(list(a1["lon"].shape), [180], "A1 longitude shape")
        channel_summary: dict[str, Any] = {}
        for channel in A1_CHANNELS:
            if channel not in a1.files or list(a1[channel].shape) != [11, 90, 180]:
                raise GateError(f"A1 channel schema mismatch: {channel}")
            channel_summary[channel] = finite_summary(np.asarray(a1[channel]))
            if not channel_summary[channel]["finite"]:
                raise GateError(f"A1 channel is non-finite: {channel}")
        land_mask = np.asarray(a1["land_mask"])
        if list(land_mask.shape) != [11, 90, 180] or not np.isfinite(land_mask).all():
            raise GateError("A1 land-mask coverage schema/integrity mismatch")
        a1_coverage = {
            "land_mask": finite_summary(land_mask),
            "valid_cells_by_anchor": [
                int(np.isfinite(a1["total_edible_forage"][anchor]).sum())
                for anchor in range(11)
            ],
        }

    r334_info = a2["semantic_bindings"]["recent_plant_resource_refinement"]["payload"]
    r334_path = resolve_path(root, r334_info["path"])
    require_equal(sha256_file(r334_path), R334_SHA256, "R3.34 SHA256")
    with np.load(r334_path, allow_pickle=False) as r334:
        require_equal(r334["anchor_age_ka"].tolist(), RECENT_AGES, "R3.34 age anchors")
        producer_ids = [str(x) for x in r334["producer_taxon_ids"].tolist()]
        require_equal(len(producer_ids), 36, "R3.34 producer count")
        require_equal([str(x) for x in r334["landscape_variable_names"].tolist()], R334_FIELDS, "R3.34 landscape fields")
        landscape = np.asarray(r334["producer_landscape"])
        require_equal(list(landscape.shape), [36, 9, 90, 180, 4], "R3.34 landscape shape")
        if not np.isfinite(landscape).all():
            raise GateError("R3.34 landscape contains non-finite values")
        recent_summary = {
            field: finite_summary(landscape[:, :, :, :, index])
            for index, field in enumerate(R334_FIELDS)
        }

    fauna_root = root / "SIMULATION_RESULTS"
    fauna_paths = [
        (fauna_root / "02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json", "R3.21", "present 0 ka", "present component occupancy summaries", "present lineage records; population_total is present state, not historical abundance", False),
        (fauna_root / "02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_PRESENT_COMPONENT_REGISTRY.json", "R3.21", "present 0 ka", "present component/range summaries", "present component geometry and population_total, not historical range or biomass", False),
        (fauna_root / "02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_HISTORICAL_LINEAGE_CLOSURE.json", "R3.21", "historical lineage events", "lineage/event references; no spatial grid abundance", "historical lineage existence/closure, not spatial abundance or density", False),
        (fauna_root / "91_SUPPORT_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_SUMMARY.json", "R3.23", "present 0 ka", "present functional components/species", "functional phenotype and present population summaries, not food availability", False),
        (root / "outputs/v0_6D1_R3_21/R3_21_REDUCED_GENETIC_STATE_SUMMARY.json", "R3.21", "historical/present genetic summary", "genetic state summary", "genetic/reduced state evidence; no governed historical spatial abundance", False),
        (root / "outputs/v0_6D1_R3_21/R3_21_FUNCTIONAL_PHENOTYPE_FORK_INTERFACE.json", "R3.21", "historical interface", "functional phenotype interface", "interface/provenance surface; no historical spatial abundance", False),
        (root / "outputs/v0_6D1_R3_21/R3_21_OUTPUT_MANIFEST.json", "R3.21", "stage output metadata", "manifest", "provenance metadata only", False),
        (root / "outputs/v0_6D1_R3_21/R3_21_AUDIT_SUMMARY.json", "R3.21", "audit metadata", "audit", "audit/provenance metadata only", False),
    ]
    candidates = [
        fauna_candidate(path, root, role=stage, temporal=temporal, spatial=spatial, semantics=semantics, suitable=suitable)
        for path, stage, temporal, spatial, semantics, suitable in fauna_paths
    ]
    lineage = load_json(fauna_paths[0][0])
    components = load_json(fauna_paths[1][0])
    closure = load_json(fauna_paths[2][0])
    functional = load_json(fauna_paths[3][0])
    require_equal(len(lineage["lineages"]), 134, "present species count")
    require_equal(len(components["components"]), 295, "present component count")
    if not closure.get("historical_species_registry") or not closure.get("historical_events"):
        raise GateError("historical lineage closure is not populated")
    require_equal(len(functional["species"]), 134, "functional present species count")
    historical_by_species = {
        item["species_id"]: item
        for item in closure["historical_species_registry"]
        if "species_id" in item
    }

    species_bindings = [
        {
            "species_id": item["species_id"],
            "historical_existence_interval_ma": {
                "birth_age_ma": historical_by_species.get(item["species_id"], {}).get("birth_age_ma"),
                "extinct_age_ma": historical_by_species.get(item["species_id"], {}).get("extinct_age_ma"),
                "silent_interpolation": False,
            },
            "component_identity_continuity": {
                "present_component_ids": item.get("component_ids", []),
                "historical_event_links_present": bool(item.get("historical_event_ids_ancestry_scoped")),
                "status": "LINEAGE_LINKED_BUT_SPATIAL_HISTORY_NOT_MATERIALIZED",
            },
            "present_spatial_endpoint": {
                "occupied_component_grid_cells": item.get("occupied_component_grid_cells"),
                "endpoint_domain": "PRESENT_0KA_ONLY",
            },
            "usable_ecological_functional_traits": bool(item.get("functional_phenotype")) or item["species_id"] in {x.get("species_id") for x in functional["species"]},
            "historical_environmental_support_available": False,
            "historical_spatial_support_materialized": False,
            "uncertainty": "historical range/occupancy absent; absence is not interpreted as zero range",
        }
        for item in lineage["lineages"]
    ]
    component_bindings = [
        {
            "component_id": item["component_id"],
            "species_id": item["species_id"],
            "component_identity_continuity": {
                "historical_event_links_present": bool(item.get("historical_event_ids")),
                "status": "PRESENT_COMPONENT_IDENTITY_ONLY",
            },
            "present_spatial_endpoint": {
                "range_grid_summary_keys": sorted(item.get("range_grid_summary", {})),
                "endpoint_domain": "PRESENT_0KA_ONLY",
            },
            "historical_environmental_support_available": False,
            "historical_spatial_support_materialized": False,
            "uncertainty": "present component range summary is not a historical range/occupancy series",
        }
        for item in components["components"]
    ]

    diagnostic = a2["semantic_bindings"]["aquatic_marine_resource_support"]
    governance = {
        "human_management_used": False,
        "population_target_used": False,
        "k_x_t_materialized": False,
        "canonical_mutation": False,
        "new_scientific_engine_introduced": False,
    }
    payload = {
        "schema": "ARCANA_R517_B7_A3_PLANT_MATERIALIZATION_AND_WILD_FAUNA_CENSUS_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B7-A3_INTERMEDIATE",
        "repository_head": head,
        "plant_trophic_resource_support": {
            "materialized": True,
            "materialization_kind": "LOSSLESS_IDENTITY_VIEW_OF_GOVERNED_A1_NATIVE_CHANNELS",
            "source_authority": record(a1_path, root),
            "age_anchors_ma": A1_AGES,
            "spatial_domain": {"grid_shape": [90, 180], "anchor_count": 11},
            "channel_names": A1_CHANNELS,
            "channel_summary": channel_summary,
            "coverage_mask": a1_coverage,
            "source_age_provenance": "A1 governed sparse anchors 210 Ma -> 0 Ma; no interpolation performed",
            "semantic_meaning": "native trophic-resource proxy only; not biomass, human calories, food production, carrying capacity or K(x,t)",
            "scalar_integration": "UNRESOLVED_NATIVE_CHANNELS_PRESERVED_NO_WEIGHTING",
            "uncertainty_gaps": ["sparse anchors", "no intermediate-age interpolation", "no scalar combination authorized"],
        },
        "recent_plant_resource_refinement": {
            "materialized": True,
            "materialization_kind": "LOSSLESS_SOURCE_REFERENCED_COMPONENT",
            "source_authority": record(r334_path, root),
            "age_anchors_ka": RECENT_AGES,
            "spatial_domain": {"grid_shape": [90, 180], "producer_count": 36},
            "producer_identity_semantics": "anonymous functional operational producers, not literal H0 flora phylogeny",
            "authorized_fields": {"resource_abundance": recent_summary["resource_abundance"], "harvest_return": recent_summary["harvest_return"]},
            "context_only_field": {"suitability": recent_summary["suitability"], "meaning": "ecological support covariate, not direct food quantity"},
            "excluded_field": {"propagation_opportunity": recent_summary["propagation_opportunity"], "excluded": True, "meaning": "management affordance"},
            "temporal_mask": "20 Ka -> 0 Ka only; backprojection earlier than 20 Ka is false",
            "semantic_meaning": "separate recent pre-management plant-resource refinement; no cross-component weighting",
            "uncertainty_gaps": ["recent-only domain", "no merge with A1 authorized in this pass"],
        },
        "wild_animal_authority_census": {
            "present_species_count": 134,
            "present_component_count": 295,
            "historical_lineage_closure_present": True,
            "candidates": candidates,
            "historical_spatial_support_materialized": False,
            "historical_abundance_materialized": False,
            "historical_reconstruction_required": True,
            "species_bindings": species_bindings,
            "component_bindings": component_bindings,
            "decision_gate": "B",
            "decision": "Historical lineage/event closure exists, but a governed historical spatial range/occupancy/abundance quantity is not materialized.",
            "unresolved_gap": "No governed historical spatial abundance, density, occupancy or range time series suitable for wild-animal resource support was recovered; present 0 ka geometry and lineage existence through time are insufficient.",
            "recommended_a3f2": "Construct the minimum governed historical spatial range/occupancy or abundance reconstruction with explicit temporal and grid semantics; do not infer biomass or K(x,t), and evaluate specialist engines only after this gate.",
        },
        "aquatic_marine_resource_support": {
            "materialized": False,
            "status": "NOT_MATERIALIZED",
            "explicit_gap": True,
            "a2_diagnostic_filename_hits": diagnostic["a1_marine_filename_hits"],
            "a2_diagnostic_content_hits": diagnostic["a1_marine_content_hits"],
            "diagnostic_is_biological_authority": False,
        },
        "governance": governance,
        "next_decision": {
            "a3_status": "INTERMEDIATE_A3_1_A3_2_A3F1_COMPLETE",
            "b7_globally_complete": False,
            "recommended_exact_next_operation": "R5.17-B7-A3F2_GOVERNED_HISTORICAL_WILD_FAUNA_SPATIAL_RECONSTRUCTION",
            "derived_binary_artifacts": [],
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# R5.17-B7-A3 — Plant Materialization & Wild-Fauna Authority Census\n\n"
        "STATUS: INTERMEDIATE_A3_1_A3_2_A3F1_COMPLETE (B7 NOT COMPLETE)\n\n"
        f"HEAD: `{head}`\n\n"
        "## Plant components\n\n"
        f"A1 native channels materialized as a lossless identity view from `{a1_path.relative_to(root).as_posix()}` with SHA256 `{A1_SHA256}`. The 11 governed anchors and 90 x 180 grid were verified; no interpolation or arbitrary channel weighting was performed.\n\n"
        f"R3.34 recent refinement materialized separately from `{r334_path.relative_to(root).as_posix()}` with SHA256 `{R334_SHA256}`. Nine anchors, 36 anonymous producers and 90 x 180 dimensions were verified. `resource_abundance` and `harvest_return` are retained; `suitability` is context-only and `propagation_opportunity` is excluded. Backprojection is false.\n\n"
        "## Wild fauna\n\n"
        "The governed family verifies 134 present species, 295 present components and populated historical lineage closure. No governed historical spatial range/occupancy/abundance quantity suitable for wild-animal resource support was recovered. Historical spatial support and historical abundance therefore remain unmaterialized; A3F2 reconstruction is required.\n\n"
        "## Marine and governance\n\n"
        "Aquatic/marine support remains `NOT_MATERIALIZED`; the two documentary A1 content hits are not biological authority. Human management, population target use, K(x,t) materialization and canonical mutation are all false. No new scientific engine was introduced.\n\n"
        "## Next\n\n"
        "`R5.17-B7-A3F2_GOVERNED_HISTORICAL_WILD_FAUNA_SPATIAL_RECONSTRUCTION`\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": payload["next_decision"]["a3_status"],
        "repository_head": head,
        "a1_source": payload["plant_trophic_resource_support"]["source_authority"],
        "a1_anchors": len(A1_AGES),
        "a1_grid": [90, 180],
        "r334_source": payload["recent_plant_resource_refinement"]["source_authority"],
        "r334_anchors": len(RECENT_AGES),
        "r334_producers": 36,
        "r334_backprojection": False,
        "propagation_opportunity_excluded": True,
        "wild_species": 134,
        "wild_components": 295,
        "historical_lineage_closure": True,
        "historical_spatial_support_materialized": False,
        "historical_abundance_materialized": False,
        "historical_reconstruction_required": True,
        "marine_materialized": False,
        **governance,
        "recommended_next_operation": payload["next_decision"]["recommended_exact_next_operation"],
        "output_json": str(root / OUT_JSON),
        "output_md": str(root / OUT_MD),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
