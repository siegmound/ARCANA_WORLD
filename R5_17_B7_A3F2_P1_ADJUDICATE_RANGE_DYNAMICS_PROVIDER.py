from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

HEAD_EXPECTED = "43463b57209927a1d6e8aedb8cb178105ad15e2b"
OUT_JSON = Path("R5_17_B7_A3F2_P1_RANGE_DYNAMICS_PROVIDER_ADJUDICATION.json")
OUT_MD = Path("R5_17_B7_A3F2_P1_RANGE_DYNAMICS_PROVIDER_ADJUDICATION.md")

AUTH = {
    "a3f2": Path("R5_17_B7_A3F2_HISTORICAL_WILD_FAUNA_SPATIAL_RECONSTRUCTION.json"),
    "lineage_registry": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json"),
    "component_registry": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_PRESENT_COMPONENT_REGISTRY.json"),
    "historical_closure": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_21/R3_21_HISTORICAL_LINEAGE_CLOSURE.json"),
    "functional_summary": Path("SIMULATION_RESULTS/91_SUPPORT_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_SUMMARY.json"),
    "r52_runtime": Path("SIMULATION_RESULTS/04_VALIDATION_AUXILIARY/outputs/v0_6D1_R5_2/R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json"),
    "r52_plan": Path("SIMULATION_RESULTS/93_SUPPORT_VALIDATION/outputs/v0_6D1_R5_2/R5_2_RANGE_EXECUTION_PLAN.json"),
    "r52_r1": Path("SIMULATION_RESULTS/93_SUPPORT_VALIDATION/outputs/v0_6D1_R5_2/R5_2_R1_SOURCE_BINDING_PREFLIGHT.json"),
    "r52_adjudication": Path("SIMULATION_RESULTS/04_VALIDATION_AUXILIARY/outputs/v0_6D1_R5_2/R5_2_EVIDENCE_STRUCTURE_AND_NEXT_ENGINE_ADJUDICATION.json"),
    "suitability_gate": Path("SCIENTIFIC_ENGINE_SUITABILITY_GATE.md"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def record(root: Path, path: Path, role: str, tracked: set[str]) -> dict[str, Any]:
    absolute = path if path.is_absolute() else root / path
    if not absolute.is_file():
        raise FileNotFoundError(absolute)
    rel = absolute.relative_to(root).as_posix()
    return {"path": rel, "role": role, "tracked": rel in tracked, "size_bytes": absolute.stat().st_size, "sha256": digest(absolute)}


def contains_any(value: Any, needles: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        return any(any(n in str(k).lower() for n in needles) or contains_any(v, needles) for k, v in value.items())
    if isinstance(value, list):
        return any(contains_any(v, needles) for v in value)
    return False


def main() -> int:
    root = Path(__file__).resolve().parent
    if git("rev-parse", "HEAD") != HEAD_EXPECTED:
        raise RuntimeError("repository HEAD differs from governed expected HEAD")
    tracked = set(git("ls-files").splitlines())
    data = {k: load(root / p) for k, p in AUTH.items() if p.suffix == ".json"}
    lineages = data["lineage_registry"]["lineages"]
    components = data["component_registry"]["components"]
    functional = data["functional_summary"]
    if (len(lineages), len(components), len(functional["species"]), len(functional["components"])) != (134, 295, 134, 295):
        raise RuntimeError("R3.21/R3.23 governed counts do not resolve to 134 species / 295 components")

    origin_needles = ("origin_cell", "cradle", "origination_location", "founder_cell", "initial_cell", "birth_location", "ancestral_location")
    species_origin = sum(contains_any(x, origin_needles) for x in lineages)
    component_origin = sum(contains_any(x, origin_needles) for x in components)
    runtime = data["r52_runtime"]
    plan = data["r52_plan"]
    r1 = data["r52_r1"]
    evidence = data["r52_adjudication"]
    sources = {k: record(root, p, k, tracked) for k, p in AUTH.items()}
    result: dict[str, Any] = {
        "stage": "R5.17-B7-A3F2-P1",
        "status": "P1_ADJUDICATION_COMPLETE_BLOCKED_MISSING_INITIALIZATION_AUTHORITY",
        "repository": {"head": HEAD_EXPECTED, "branch": git("branch", "--show-current"), "canonical_mutation": False},
        "authority_chain": ["R3.21 present lineage registry", "R3.21 present component registry", "R3.21 historical lineage closure", "R3.23 present functional/phenotype authority", "A3F2 spatial-gap decision", "SCIENTIFIC_ENGINE_SUITABILITY_GATE.md"],
        "sources": sources,
        "scope": {"species_count": 134, "component_count": 295, "quantity": "historical range / occupancy / spatial-support state", "excluded": ["abundance", "density", "biomass", "edible animal resource", "human harvest", "population targets", "K(x,t)"]},
        "initialization_authority_audit": {
            "species": {"FULL": 0, "PARTIAL": 0, "ABSENT": 134, "origin_location_fields_found": species_origin, "reason": "lineage intervals and present endpoints do not establish historical initial cells"},
            "components": {"FULL": 0, "PARTIAL": 0, "ABSENT": 295, "origin_location_fields_found": component_origin, "reason": "component identity/continuity is not a governed historical spatial initialization"},
            "available": ["lineage existence interval", "historical event/ancestry closure", "present component identity", "present spatial endpoint where recorded"],
            "not_available": ["cradle/origination cells", "ancestral component starting geography", "founder/split geography", "first occupied historical cells"],
            "policy": "absence of historical range is UNKNOWN, never zero; present endpoint is not historical initial distribution"
        },
        "parameter_authority_audit": {
            "EXACT_AUTHORITY": {"count": 0, "items": []},
            "DEFENSIBLE_DERIVATION": {"count": 0, "items": []},
            "FUNCTIONAL_GROUP_PROXY": {"count": 2, "items": ["present R3.23 functional/phenotype traits", "present generation-time proxy where available"]},
            "MISSING": {"count": 7, "items": ["dispersal kernel", "movement/connectivity", "survival", "fecundity", "density dependence", "barriers/permeability", "historical ecological tolerance/environment response"]},
            "rule": "no arbitrary constants may be promoted to historical species authority"
        },
        "prior_validated_provider": {
            "provider": "RangeShiftR",
            "version": runtime.get("package_version"),
            "runtime": {"r_version": runtime.get("r_version"), "library_path": runtime.get("library_path")},
            "prior_scope": "governed descriptive connectivity/corridor evidence, not canonical range truth",
            "prior_design": {"robust_cradle_families": plan.get("robust_family_count"), "groups": plan.get("group_count"), "executable_groups": plan.get("executable_group_count"), "seeds": plan.get("seeds"), "replicates_per_stream": plan.get("replicates_per_stream"), "initialization": plan.get("source_initialization_contract"), "movement_profiles": plan.get("movement_profiles"), "occupancy_readout": plan.get("occupancy_readout"), "parameter_reuse": plan.get("r41_parameter_reuse"), "r1_checks_passed": r1.get("checks_passed")},
            "prior_semantics": evidence.get("semantics"),
            "adapter_reuse": "not authorized; prior source cells were fixed R5.1/J14 corridor inputs and do not initialize the 134/295 historical fauna authority"
        },
        "dynamic_landscape_compatibility": {"arcana_grid": "90x180 latitude/longitude", "range_shiftr_prior_mapping": "one ARCANA grid cell to one normalized engine cell; 100 engine meters computational, not geodesic; longitude rolled per family", "time_mapping": "one engine year represented one ARCANA 20 kyr transition in R5.2 diagnostic work, not literal biological years", "compatible": False, "blockers": ["latitude-dependent cell area", "changing land/sea and shoreline", "barriers/disconnected land and permeability", "temporal anchor mismatch", "lineage-time masks not bound to provider initialization"], "minimum_adapter_semantics_before_run": ["equal-area or area-weighted cell semantics", "versioned time-indexed land/sea mask", "explicit shoreline/barrier rule", "lineage origination and termination masks", "governed initial occupancy cells", "units-preserving time and movement parameters"]},
        "validity": {"forward": "conditionally valid in principle only after initialization, parameter, and spatial adapter authorities are independently closed", "inverse_from_present": False, "inverse_reason": "backward inference from 0 ka/present endpoint is not historical truth", "endpoint_validation": {"calibration": "pre-register parameters on independent cradle/early-history evidence", "validation": "hold out later governed endpoints or intervals", "metrics": ["cell-wise Jaccard", "commission/omission", "range-size ratio", "probabilistic occupancy scoring only when probabilities are authorized"], "anti_circular_rule": "never tune and validate on the same endpoint"}},
        "provider_gate": {"decision": "BLOCKED_MISSING_INITIALIZATION_AUTHORITY", "decision_order_evaluated": ["REUSE_CANONICAL_ARCANA", "REUSE_ALREADY_VALIDATED_SPECIALIST_PROVIDER", "AUDIT_NEW_SPECIALIST_PROVIDER", "MINIMUM_CUSTOM_ARCANA"], "rationale": "canonical ARCANA replay lacks the required historical spatial series; RangeShiftR is validated only for a narrower prior descriptive scope and cannot be initialized for these lineages/components", "conditions_for_reopen": ["recover governed historical cradle/origination cells for all applicable species/components", "close parameter authority without arbitrary constants", "approve a lossless dynamic-landscape adapter and units", "pre-register forward validation and uncertainty propagation"]},
        "governance": {"human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "historical_spatial_support_materialized": False, "historical_abundance_materialized": False, "RangeShiftR_invoked": False, "new_engine_invoked": False, "heavy_arrays_created": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
        "next_operation": "Recover and adjudicate governed historical initialization authority; do not run RangeShiftR or materialize historical occupancy arrays until the provider gate is reopened."
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = "# R5.17-B7-A3F2-P1\n\n## Decision\n\n**BLOCKED_MISSING_INITIALIZATION_AUTHORITY**. RangeShiftR 3.0.1 is reusable only as prior descriptive corridor evidence; it is not ready to reconstruct the 134-species / 295-component historical fauna spatial state.\n\n## Authority and audit\n\n- Authority chain: R3.21 lineage/component registries, R3.21 historical closure, R3.23 functional authority, A3F2 gap decision, and the scientific-engine suitability gate.\n- Initialization: species FULL/PARTIAL/ABSENT = **0/0/134**; components = **0/0/295**. Present endpoints do not count as historical initial geography.\n- Parameters: exact authority **0**, defensible derivation **0**, functional-group proxy dimensions **2**, missing dimensions **7** (kernel, movement, survival, fecundity, density dependence, barriers, historical environmental response).\n- Spatial policy: 90x180 ARCANA geography, changing land/sea, cell-area variation, shoreline/barrier semantics, and lineage-time masks require an approved adapter.\n\n## Provider and validity\n\nThe recovered prior provider is RangeShiftR **3.0.1**, R **4.5.3**, with 12 robust cradle families, 24 groups (20 executable), fixed source-cell initialization, two seeds, and descriptive occupancy/connectivity readouts. Its prior evidence explicitly did not define canonical corridor truth. Forward use is conditional after authority closure; inverse inference from the present endpoint is invalid.\n\n## Governance\n\nNo engine was invoked, no arrays or abundance were materialized, no K(x,t) was materialized, no current-state/index files were changed, and no staging/commit/push occurred. Marine/aquatic resource support remains **NOT_MATERIALIZED**.\n\nSee the JSON artifact for hashes, source sizes, adapter conditions, and the pre-registered validation design.\n"
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
