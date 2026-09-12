from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


HEAD_EXPECTED = "43463b57209927a1d6e8aedb8cb178105ad15e2b"
A2_STATUS = "PASS_R517_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATED"
A3_STATUS = "INTERMEDIATE_A3_1_A3_2_A3F1_COMPLETE"
A2_PATH = Path("R5_17_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION.json")
A3_PATH = Path("R5_17_B7_A3_PLANT_MATERIALIZATION_AND_WILD_FAUNA_AUTHORITY_CENSUS.json")
OUT_JSON = Path("R5_17_B7_A3F2_HISTORICAL_WILD_FAUNA_SPATIAL_RECONSTRUCTION.json")
OUT_MD = Path("R5_17_B7_A3F2_HISTORICAL_WILD_FAUNA_SPATIAL_RECONSTRUCTION.md")

PRIMARY = {
    "present_lineage_registry": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json"),
    "present_component_registry": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_PRESENT_COMPONENT_REGISTRY.json"),
    "historical_lineage_closure": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_HISTORICAL_LINEAGE_CLOSURE.json"),
    "present_functional_summary": Path("SIMULATION_RESULTS/91_SUPPORT_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_SUMMARY.json"),
}


class GateError(RuntimeError):
    pass


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(value: Any, expected: Any, label: str) -> None:
    if value != expected:
        raise GateError(f"{label}: expected {expected!r}, got {value!r}")


def source_record(root: Path, path: Path, role: str) -> dict[str, Any]:
    if not path.is_file():
        raise GateError(f"Missing governed authority: {path}")
    relative = path.relative_to(root).as_posix()
    return {
        "path": relative,
        "role": role,
        "tracked": relative in set(git("ls-files").splitlines()),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def main() -> int:
    root = Path(__file__).resolve().parent
    head = git("rev-parse", "HEAD")
    require(head, HEAD_EXPECTED, "repository HEAD")
    a2 = load(root / A2_PATH)
    a3 = load(root / A3_PATH)
    require(a2["status"], A2_STATUS, "A2 status")
    require(a3["next_decision"]["a3_status"], A3_STATUS, "A3 parent status")

    authorities = {name: source_record(root, root / path, name) for name, path in PRIMARY.items()}
    lineage = load(root / PRIMARY["present_lineage_registry"])
    components = load(root / PRIMARY["present_component_registry"])
    closure = load(root / PRIMARY["historical_lineage_closure"])
    functional = load(root / PRIMARY["present_functional_summary"])
    require(len(lineage.get("lineages", [])), 134, "present species count")
    require(len(components.get("components", [])), 295, "present component count")
    require(len(functional.get("species", [])), 134, "functional species count")
    if not closure.get("historical_species_registry") or not closure.get("historical_events"):
        raise GateError("historical lineage closure is empty")

    historical_by_species = {
        item["species_id"]: item
        for item in closure["historical_species_registry"]
        if "species_id" in item
    }
    functional_ids = {item["species_id"] for item in functional["species"]}
    species_masks = []
    for item in lineage["lineages"]:
        species_id = item["species_id"]
        history = historical_by_species.get(species_id, {})
        species_masks.append(
            {
                "species_id": species_id,
                "birth_age_ma": history.get("birth_age_ma"),
                "extinct_age_ma": history.get("extinct_age_ma"),
                "component_ids": item.get("component_ids", []),
                "functional_authority_present": species_id in functional_ids,
                "lineage_time_mask_semantics": "eligible only within recorded lineage interval; no silent interpolation or extrapolation",
                "historical_spatial_support": "UNKNOWN_NOT_ZERO",
                "historical_environmental_support": "NOT_MATERIALIZED",
            }
        )

    component_endpoints = []
    for item in components["components"]:
        summary = item.get("range_grid_summary", {})
        component_endpoints.append(
            {
                "component_id": item["component_id"],
                "species_id": item["species_id"],
                "historical_event_links_present": bool(item.get("historical_event_ids")),
                "present_endpoint_only": {
                    key: summary[key]
                    for key in ("grid_shape", "occupied_col_minmax", "occupied_row_minmax", "occupied_grid_cells")
                    if key in summary
                },
                "historical_cell_assignment": "NOT_ASSIGNED",
                "validity_policy": "component cannot be assigned before lineage origination or after termination; historical cells remain unknown",
            }
        )

    governance = {
        "human_management_used": False,
        "population_target_used": False,
        "k_x_t_materialized": False,
        "canonical_mutation": False,
        "new_scientific_engine_introduced": False,
        "abundance_materialized": False,
        "density_materialized": False,
        "biomass_materialized": False,
        "edible_animal_resource_materialized": False,
    }
    payload = {
        "schema": "ARCANA_R517_B7_A3F2_HISTORICAL_WILD_FAUNA_SPATIAL_RECONSTRUCTION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B7-A3F2",
        "status": "A3F2_GATE_COMPLETE_HISTORICAL_SPATIAL_GAP_REMAINS",
        "repository_head": head,
        "parent_evidence": source_record(root, root / A3_PATH, "A3F1_PARENT_EVIDENCE"),
        "authority_chain": {
            "A2_binding": source_record(root, root / A2_PATH, "A2_SEMANTIC_BINDING_AUTHORITY"),
            **authorities,
            "provider_suitability_gate": source_record(root, root / "SCIENTIFIC_ENGINE_SUITABILITY_GATE.md", "PROVIDER_SELECTION_POLICY"),
        },
        "phase_1_reconstruction_contract": {
            "species_count": 134,
            "component_count": 295,
            "temporal_domain": "R3.21 historical lineage closure intervals only; no new temporal anchors",
            "spatial_domain": {"grid_shape": [90, 180], "endpoint": "present 0 ka component range summaries only"},
            "species_lineage_time_masks": species_masks,
            "component_identity_and_endpoint_records": component_endpoints,
            "historical_environmental_support_available": False,
            "absence_is_zero_range": False,
        },
        "phase_2_provider_suitability_gate": {
            "decision": "BLOCKED_INSUFFICIENT_SEMANTICS",
            "canonical_arcana": {"decision": "INSUFFICIENT_FOR_HISTORICAL_SPATIAL_RECONSTRUCTION", "available": ["lineage intervals", "present endpoint summaries", "present functional authority"]},
            "validated_specialist_provider": {"evaluated": False, "reason": "No provider invoked before a governed quantity/specification is available."},
            "RangeShiftR": {"evaluated": False, "invoked": False, "reason": "Not run merely because it is available; the required historical quantity and assumptions remain unspecified."},
            "minimum_custom_scope": "Control-plane census and explicit unknown masks only; no spatial propagation or scientific fauna reconstruction algorithm.",
        },
        "spatial_state": {
            "historical_spatial_support_materialized": False,
            "historical_abundance_materialized": False,
            "historical_range_series_materialized": False,
            "historical_occupancy_series_materialized": False,
            "present_endpoint_occupancy_summaries_materialized": True,
            "range_occupancy_semantics": "Present endpoint summaries are not promoted to historical range/occupancy; missing historical support is UNKNOWN_NOT_ZERO.",
            "uncertainty_mask": {"historical_cells": "UNKNOWN", "pre_origination_cells": "INVALID", "post_termination_cells": "INVALID", "present_endpoint_summary": "OBSERVED_GOVERNED_SUMMARY"},
            "reconstruction_method": "Lineage interval binding plus present endpoint census; no interpolation, extrapolation, dispersal or cell propagation.",
        },
        "aquatic_marine_resource_support": {"materialized": False, "status": "NOT_MATERIALIZED", "explicit_gap": True},
        "governance": governance,
        "derived_binary_artifacts": [],
        "next_decision": {
            "historical_spatial_reconstruction_ready": False,
            "minimum_required_quantity": "Governed historical spatial range/occupancy or explicit spatial-support state with temporal anchors and ecological support semantics.",
            "recommended_exact_next_operation": "R5.17-B7-A3F2_SPECIFY_AND_BIND_HISTORICAL_SPATIAL_SUPPORT_QUANTITY_BEFORE_PROVIDER_EXECUTION",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# R5.17-B7-A3F2 — Governed Historical Wild-Fauna Spatial Reconstruction\n\n"
        "STATUS: `A3F2_GATE_COMPLETE_HISTORICAL_SPATIAL_GAP_REMAINS`\n\n"
        f"HEAD: `{head}`\n\n"
        "## Result\n\n"
        "The R3.21 lineage registry, component registry and historical lineage closure, together with R3.23 present functional authority, were bound and verified for 134 species and 295 components. Lineage-time masks and present endpoint summaries are recorded. Historical spatial cells remain explicitly unknown, never zero.\n\n"
        "## Provider gate\n\n"
        "`BLOCKED_INSUFFICIENT_SEMANTICS`: canonical ARCANA evidence is insufficient for a historical spatial range/occupancy series. No validated specialist provider was invoked and RangeShiftR was not run. The custom scope is limited to control-plane census and uncertainty/eligibility masks; no spatial propagation was performed.\n\n"
        "## Guardrails\n\n"
        "Historical abundance, density, biomass, edible animal resource, human harvest, population targets and K(x,t) remain unmaterialized. Marine/aquatic support remains `NOT_MATERIALIZED`.\n\n"
        "## Next\n\n"
        "`R5.17-B7-A3F2_SPECIFY_AND_BIND_HISTORICAL_SPATIAL_SUPPORT_QUANTITY_BEFORE_PROVIDER_EXECUTION`\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": payload["status"],
        "repository_head": head,
        "species_count": 134,
        "component_count": 295,
        "historical_lineage_closure": True,
        "historical_spatial_support_materialized": False,
        "historical_abundance_materialized": False,
        "provider_decision": payload["phase_2_provider_suitability_gate"]["decision"],
        "rangeshiftr_invoked": False,
        "k_x_t_materialized": False,
        "marine_status": "NOT_MATERIALIZED",
        "output_json": str(root / OUT_JSON),
        "output_md": str(root / OUT_MD),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
