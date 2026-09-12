from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

HEAD_EXPECTED = "43463b57209927a1d6e8aedb8cb178105ad15e2b"
OUT_JSON = Path("R5_17_B7_A3F2_P2_MACROECOLOGICAL_RESOURCE_PROVIDER_ADJUDICATION.json")
OUT_MD = Path("R5_17_B7_A3F2_P2_MACROECOLOGICAL_RESOURCE_PROVIDER_ADJUDICATION.md")

AUTH = {
    "food_contract": Path("R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md"),
    "a2": Path("R5_17_B7_A2_SEMANTIC_BINDING_AND_TEMPORAL_COVERAGE_ADJUDICATION.json"),
    "a3": Path("R5_17_B7_A3_PLANT_MATERIALIZATION_AND_WILD_FAUNA_AUTHORITY_CENSUS.json"),
    "a3f2": Path("R5_17_B7_A3F2_HISTORICAL_WILD_FAUNA_SPATIAL_RECONSTRUCTION.json"),
    "p1": Path("R5_17_B7_A3F2_P1_RANGE_DYNAMICS_PROVIDER_ADJUDICATION.json"),
    "suitability_gate": Path("SCIENTIFIC_ENGINE_SUITABILITY_GATE.md"),
    "madingley_runtime": Path("outputs/v0_6D1_R4_3/R4_3_RUNTIME_IDENTITY_EVIDENCE.json"),
    "madingley_job_audit": Path("outputs/v0_6D1_R4_3/jobs/R42_J07_H0_POST_CHA1_RECOVERY_MADINGLEY/JOB_AUDIT.json"),
    "madingley_normalized": Path("outputs/v0_6D1_R4_3/jobs/R42_J07_H0_POST_CHA1_RECOVERY_MADINGLEY/NORMALIZED_EVIDENCE.json"),
    "madingley_driver": Path("benchmarks/r43/madingley_r43.R"),
    "r323_functional": Path("outputs/v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_SUMMARY.json"),
    "r321_lineage": Path("outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json"),
    "r334_resource": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"),
    "a1_reference": Path("references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source(root: Path, path: Path, role: str, tracked: set[str]) -> dict[str, Any]:
    absolute = path if path.is_absolute() else root / path
    if not absolute.is_file():
        return {"path": path.as_posix(), "role": role, "available": False}
    rel = absolute.relative_to(root).as_posix()
    return {"path": rel, "role": role, "available": True, "tracked": rel in tracked, "size_bytes": absolute.stat().st_size, "sha256": sha256(absolute)}


def main() -> int:
    root = Path(__file__).resolve().parent
    if git("rev-parse", "HEAD") != HEAD_EXPECTED:
        raise RuntimeError("repository HEAD differs from governed expected HEAD")
    tracked = set(git("ls-files").splitlines())
    a2 = load(root / AUTH["a2"])
    a3 = load(root / AUTH["a3"])
    a3f2 = load(root / AUTH["a3f2"])
    p1 = load(root / AUTH["p1"])
    lineage = load(root / AUTH["r321_lineage"])
    functional = load(root / AUTH["r323_functional"])
    if len(lineage.get("lineages", [])) != 134 or len(functional.get("species", [])) != 134 or len(functional.get("components", [])) != 295:
        raise RuntimeError("governed ARCANA fauna counts are not 134 species / 295 components")
    runtime = load(root / AUTH["madingley_runtime"])
    audit = load(root / AUTH["madingley_job_audit"])
    normalized = load(root / AUTH["madingley_normalized"])
    result: dict[str, Any] = {
        "stage": "R5.17-B7-A3F2-P2",
        "status": "P2_ADJUDICATION_COMPLETE_CONDITIONAL_SPECIALIST_PROVIDER_INTRODUCTION",
        "repository": {"head": HEAD_EXPECTED, "branch": git("branch", "--show-current"), "canonical_mutation": False},
        "sources": {k: source(root, p, k, tracked) for k, p in AUTH.items()},
        "scientific_target_reframe": {
            "b7_contract_target": "natural/pre-management biological food-resource opportunity; H0 fauna inspection includes spatial population/range state and trophic relationships",
            "adjudication": "B7 does not require literal reconstruction of the 134 ARCANA species as the only route to its wild-animal support quantity; a bounded macroecological functional opportunity layer is scientifically relevant, provided it is kept separate from ARCANA species authority",
            "selected_target": "NATURAL_WILD_ANIMAL_RESOURCE_SUPPORT",
            "provider_output_role": "PROVIDER_EVIDENCE_FOR_NATURAL_ANIMAL_RESOURCE_OPPORTUNITY",
            "not_claimed": ["historical truth about individual ARCANA species ranges", "human-edible fraction", "calories", "hunting return", "human carrying capacity", "K(x,t)"],
            "species_identity_requirement": "not required for a functional opportunity layer in principle; R3.21/R3.23 remain authoritative for ARCANA identity and are not replaced",
        },
        "rangeshiftr_disposition": {"current_p1_decision": p1["provider_gate"]["decision"], "disposition": "RETAIN_AS_BLOCKED_SPECIES_LEVEL_ALTERNATIVE", "reason": "historical cradle/initialization authority is absent for 134/295; species-range reconstruction is unnecessarily strong for the reframed B7 opportunity quantity"},
        "madingley_runtime_authority": {
            "available_in_repository": True,
            "implementation": "MadingleyR with Madingley C++ backend",
            "version": runtime.get("runtime", {}).get("confirmed_version", "MadingleyR-1.0.6__CPP-2.02"),
            "language_runtime": "R package plus compiled C++ backend; prior ARCANA evidence used the arcana-r40-r conda/R environment",
            "license_status": "not independently adjudicated in this tranche",
            "previous_arcana_validation": {"runtime_identity": runtime.get("status"), "job_status": audit.get("status"), "successful_replicates": audit.get("successful_replicates"), "canonical_write": audit.get("canonical_write"), "normalization_semantics": normalized.get("normalization_semantics")},
            "previous_scientific_role": "microbenchmark and bounded ecosystem response evidence; prior adapter used normalized NPP boundary-response factor and explicitly non-ARCANA Earth-reference-window geography",
            "production_ready_for_B7": False,
            "runtime_disposition": "MADINGLEY_STAGE_LOCAL_RUNTIME_AUDIT_REQUIRED",
        },
        "madingley_semantic_suitability": {
            "functional_heterotroph_groups_cohorts": "MATCH",
            "trophic_level": "PARTIAL_PROVIDER_STATE; must be exposed and mapped without species claims",
            "body_mass": "MATCH_AS_FUNCTIONAL_COHORT_PARAMETER",
            "abundance": "PROVIDER_OUTPUT_POSSIBLE_BUT_NOT_B7_AUTHORITY_BY_ITSELF",
            "biomass": "PROVIDER_OUTPUT_POSSIBLE_AS_OPPORTUNITY_STATE; not human food mass",
            "terrestrial_ecosystem_state": "MATCH",
            "environmental_dependence": "MATCH_IN_MODEL_FORM",
            "dispersal_mortality_reproduction": "MATCH_IN_MODEL_FORM; parameter authority still required",
            "trophic_interactions": "PARTIAL_OR_MODEL-DEFINED; must be audited against requested semantics",
            "overall": "scientifically stronger candidate than a custom trophic-efficiency scalar for natural animal opportunity, but not yet an ARCANA-authorized output",
        },
        "initialization_and_spinup_options": {
            "standard_functional_cohort_initialization": {"species_origin_required": False, "assumptions": ["generic cohort priors are defensible", "environmental inputs are physically/unit compatible"], "meaning": "model initial condition, not historical realized ecosystem"},
            "ecological_spinup_equilibrium": {"species_origin_required": False, "assumptions": ["stationary environment or declared equilibration interpretation", "equilibrium is relevant to opportunity"], "meaning": "equilibrium ecological opportunity, not literal history"},
            "independent_time_slice_equilibration": {"species_origin_required": False, "assumptions": ["each governed environment is interpreted independently", "cross-time path dependence is intentionally discarded"], "meaning": "snapshot opportunity"},
            "continuous_transient": {"species_origin_required": False, "assumptions": ["time-continuous environmental drivers", "cohort and trophic state carry-over", "validated temporal units"], "meaning": "transient functional ecosystem opportunity; still not ARCANA species history"},
            "warm_start": {"species_origin_required": False, "assumptions": ["preceding anchor state is governed and compatible", "state carry-over is scientifically justified"], "meaning": "path-dependent opportunity"},
            "preferred_future_pilot": "independent governed time-slice opportunity snapshots unless a transient environmental/state authority is first recovered; no option is authorized to run now",
        },
        "environment_input_crosswalk": {
            "land_ocean_mask": "PROXY_ONLY_OR_MISSING: available paleogeographic inputs require semantic/unit adapter; prior Madingley run was not ARCANA geography",
            "temperature": "PROXY_ONLY: Madingley requires monthly near-surface temperature; exact ARCANA historical field/domain binding not established",
            "precipitation": "PROXY_ONLY: name similarity is insufficient and relative precipitation must not be treated as water availability",
            "npp_primary_productivity": "PROXY_ONLY: A1 forage/NPP-like support is not automatically physical NPP in the Madingley input contract",
            "seasonality": "MISSING_FOR_GOVERNED_CROSSWALK: monthly/seasonal semantics and units not closed",
            "terrestrial_environment": "PROXY_ONLY: R3.33/R3.34 recent resource states cannot be backprojected into deep time",
            "plant_autotroph_base": "PROXY_ONLY: A3 plant materialization is a governed resource component, not automatically Madingley stock initialization",
            "spatial_grid_latitude_cell_area": "PROXY_ONLY: 90x180 lat/lon requires area-aware adapter",
            "changing_shoreline_paleogeography": "MISSING_AS_PROVIDER_INPUT_AUTHORITY",
            "forbidden_mappings": ["forage proxy as physical plant biomass", "relative precipitation as water availability", "coastal edge as marine productivity", "human-conditioned or domestication fields"],
            "overall": "no exact complete crosswalk; MADINGLEY_INPUT_CROSSWALK_REQUIRED",
        },
        "temporal_compatibility": {
            "downstream_domain": "B7 natural support follows governed A1 deep-time anchors and separately bounded recent authorities; exact source masks remain attached",
            "available_anchors": ["A1 210 Ma to 0 Ma canonical anchors", "R3.33/R3.34 recent 20 ka to 0 ka domain"],
            "transient": "not currently defensible: continuous environmental/state semantics and units are not closed",
            "independent_snapshots": "conditionally defensible for ecological opportunity at governed environmental anchors, with explicit no-interpolation policy",
            "neither": False,
            "temporal_mismatch": "do not silently backproject recent producer/resource fields or interpret equilibrium snapshots as historical realized states",
        },
        "spatial_compatibility": {
            "arcana_grid": "90x180 latitude/longitude with latitude-dependent cell area",
            "provider_assumption": "prior Madingley evidence used 1-degree Earth-reference input and non-ARCANA geography",
            "compatible_now": False,
            "minimum_adapter": ["area-aware remapping with explicit conservation/units", "time-indexed land/sea mask and shoreline rule", "land-only terrestrial domain mask", "latitude and cell-area fields retained", "uncertainty and coverage masks propagated", "no equal-area assumption"],
            "production_remap": "not implemented or authorized",
        },
        "terrestrial_scope": {"decision": "CONDITIONAL_SPECIALIST_CANDIDATE", "semantic_role": "natural terrestrial wild-animal trophic/resource opportunity", "pilot_authorized": False, "conditions": ["runtime audit", "complete input crosswalk", "spatial/temporal adapter", "output bounds below human exploitation and K(x,t)"]},
        "marine_scope": {"decision": "NOT_MATERIALIZED", "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED", "reason": "terrestrial macroecological suitability does not promote marine authority"},
        "alternative_provider_comparison": {
            "RangeShiftR_species_reconstruction": "blocked by missing historical initialization; unnecessarily strong for reframed B7 target",
            "Madingley_functional_macroecology": "best scientific candidate for bounded opportunity; requires new stage-local runtime/input/spatial audit",
            "minimum_custom_arcana": "not selected merely for ease; a custom trophic-efficiency approximation is less semantically defensible than functional ecosystem evidence",
            "explicitly_bounded_unmaterialized": "remains the current safe output until Madingley conditions close",
            "mandatory_order": ["REUSE_CANONICAL_ARCANA", "REUSE_ALREADY_VALIDATED_SPECIALIST_PROVIDER", "AUDIT_NEW_SPECIALIST_PROVIDER", "MINIMUM_CUSTOM_ARCANA"],
        },
        "provider_decision": "INTRODUCE_SPECIALIST_PROVIDER",
        "implementation_disposition": "MADINGLEY_STAGE_LOCAL_RUNTIME_AUDIT_REQUIRED",
        "remaining_conditions": ["confirm exact runtime/package on current host without production run", "complete semantic/unit crosswalk for each required environmental input", "approve area-aware 90x180 adapter", "select snapshot versus transient interpretation", "define uncertainty propagation and bounded output schema", "keep ARCANA species authority separate", "separate marine adjudication"],
        "governance": {"human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False, "historical_species_range_materialized": False, "historical_abundance_materialized": False, "RangeShiftR_invoked": False, "Madingley_invoked": False, "animal_biomass_materialized": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
        "next_operation": "Run a non-production stage-local Madingley runtime and license audit plus a source-bound environmental input crosswalk; do not run a scientific pilot until all remaining conditions are adjudicated."
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("""# R5.17-B7-A3F2-P2\n\n## Decision\n\n**INTRODUCE_SPECIALIST_PROVIDER**, conditionally. The B7 quantity is best reframed as `NATURAL_WILD_ANIMAL_RESOURCE_SUPPORT`: a bounded macroecological trophic/resource-opportunity layer independent of human exploitation. Literal historical identity for all 134 ARCANA species is not required for that layer, but R3.21/R3.23 remain the identity and phenotype authorities.\n\n## Provider adjudication\n\nMadingley is the strongest scientific candidate found for functional heterotroph/cohort, body-mass, trophic, environmental, mortality/reproduction and biomass-opportunity evidence. Prior ARCANA evidence recovers **MadingleyR-1.0.6__CPP-2.02**, with successful non-canonical R4.1/R4.3 runs. Those runs used a normalized NPP response adapter and explicitly non-ARCANA geography; they do not authorize production B7 evidence.\n\nRangeShiftR remains blocked for species-level historical reconstruction because cradle/initialization authority is absent, and that intermediate is unnecessarily strong for the reframed target. A custom trophic scalar is not selected merely for convenience.\n\n## Conditions\n\nNo pilot is authorized. A future pilot requires a complete source-bound environmental/unit crosswalk, area-aware 90x180 spatial adapter, explicit temporal interpretation, uncertainty propagation, output bounds below human exploitation and K(x,t), and strict separation from ARCANA species authority. Terrestrial scope is conditional; `AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n\nNo provider was run, no species ranges or animal biomass were materialized, and no current-state/index/staging/commit/push operation occurred.\n""", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
