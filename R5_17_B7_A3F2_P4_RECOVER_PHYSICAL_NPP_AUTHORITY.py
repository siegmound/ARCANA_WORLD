from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HEAD = "cfc5f26bb0965e87f8a43ea29ad6e27b4d43d021"
OUT_JSON = Path("R5_17_B7_A3F2_P4_PHYSICAL_NPP_AUTHORITY_RECOVERY.json")
OUT_MD = Path("R5_17_B7_A3F2_P4_PHYSICAL_NPP_AUTHORITY_RECOVERY.md")
AUTH = {
    "current_state": Path("ARCANA_WORLD_CURRENT_STATE.md"),
    "p3": Path("R5_17_B7_A3F2_P3_MADINGLEY_RUNTIME_AND_INPUT_BINDING_AUDIT.json"),
    "p2": Path("R5_17_B7_A3F2_P2_MACROECOLOGICAL_RESOURCE_PROVIDER_ADJUDICATION.json"),
    "index": Path("ARCANA_EXECUTION_REFERENCE_INDEX.json"),
    "manifest": Path("SIMULATION_RESULTS/MANIFEST.json"),
    "catalog": Path("SIMULATION_RESULTS/SEMANTIC_CATALOG.md"),
    "a1": Path("references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"),
    "r333": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz"),
    "r334": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"),
    "madingley_runner": Path("benchmarks/r43/madingley_r43.R"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source(root: Path, path: Path, role: str) -> dict:
    p = root / path
    if not p.is_file():
        return {"path": path.as_posix(), "role": role, "available": False}
    return {"path": path.as_posix(), "role": role, "available": True, "tracked": path.as_posix() in set(git("ls-files").splitlines()), "size_bytes": p.stat().st_size, "sha256": sha(p), "git_blob_oid": git("hash-object", "--", path.as_posix())}


def main() -> int:
    root = Path(__file__).resolve().parent
    if git("rev-parse", "HEAD") != HEAD:
        raise RuntimeError("repository HEAD changed during P4 audit")
    p3 = load(root / AUTH["p3"])
    p2 = load(root / AUTH["p2"])
    if p3["pilot_decision"] != "BLOCKED_MISSING_PHYSICAL_NPP_AUTHORITY":
        raise RuntimeError("P3 parent decision mismatch")
    result = {
        "stage": "R5.17-B7-A3F2-P4",
        "status": "P4_RECOVERY_COMPLETE_BLOCKED_ONLY_NORMALIZED_PROXY_EXISTS",
        "repository": {"head": HEAD, "branch": git("branch", "--show-current")},
        "parent_p3_decision": p3["pilot_decision"],
        "exact_required_npp_semantics": {"quantity": "physical terrestrial net primary productivity", "provider": "MadingleyR-1.0.6__CPP-2.02", "dimensions": "12 monthly layers on provider spatial grid", "not_equivalent_to": ["normalized NPP factor", "A1 total_edible_forage", "R3.33 npp_factor", "R3.34 resource_abundance", "R3.34 harvest_return", "vegetation suitability"]},
        "search_surfaces": {"order": ["tracked governed authority", "SIMULATION_RESULTS catalogue", "provenance-linked local payloads", "referenced reconstruction/census surfaces", "historical Git objects where provenance-linked"], "terms": ["npp", "net primary productivity", "primary production", "gpp", "carbon flux", "kgC", "gC", "photosynthesis", "autotroph production", "PAR", "APAR", "fPAR", "LAI", "vegetation productivity", "biomass production"]},
        "source_artifacts": {k: source(root, path, k) for k, path in AUTH.items()},
        "candidate_artifacts": [
            {"artifact": "R3.33 npp_factor / related recent environmental fields", "path": AUTH["r333"].as_posix(), "tracked": source(root, AUTH["r333"], "r333").get("tracked", False), "sha256": source(root, AUTH["r333"], "r333").get("sha256"), "classification": "DIMENSIONLESS_NPP_FACTOR", "authority_status": "governed recent covariate, not physical NPP", "temporal_domain": "recent Holocene authority; not deep-time backprojectable"},
            {"artifact": "A1 total_edible_forage", "path": AUTH["a1"].as_posix(), "tracked": source(root, AUTH["a1"], "a1").get("tracked", False), "sha256": source(root, AUTH["a1"], "a1").get("sha256"), "classification": "TROPHIC/FORAGE_PROXY", "authority_status": "governed trophic proxy, not NPP", "temporal_domain": "canonical A1 anchors 210 Ma to 0 Ma"},
            {"artifact": "R3.34 producer resource landscape", "path": AUTH["r334"].as_posix(), "tracked": source(root, AUTH["r334"], "r334").get("tracked", False), "sha256": source(root, AUTH["r334"], "r334").get("sha256"), "classification": "TROPHIC/FORAGE_PROXY", "authority_status": "producer resource/abundance proxy; not NPP", "temporal_domain": "20 ka to 0 ka"},
            {"artifact": "Madingley prior terrestrial_net_primary_productivity inputs", "path": AUTH["madingley_runner"].as_posix(), "tracked": source(root, AUTH["madingley_runner"], "madingley_runner").get("tracked", False), "sha256": source(root, AUTH["madingley_runner"], "madingley_runner").get("sha256"), "classification": "UNKNOWN", "authority_status": "provider input files exist in prior runtime payloads, but are not ARCANA physical-NPP authority; prior runner applies normalized boundary factor", "temporal_domain": "prior representative runs only"},
            {"artifact": "physical NPP/GPP/carbon-flux generator-backed ARCANA authority", "path": None, "tracked": False, "sha256": None, "classification": "UNKNOWN", "authority_status": "not recovered", "temporal_domain": "none established"},
        ],
        "candidate_classification": {"physical_npp": 0, "physical_gpp": 0, "physical_carbon_flux": 0, "dimensionless_npp_factor": 1, "normalized_productivity_proxy": 1, "trophic_forage_proxy": 2, "unknown": 2},
        "generator_provenance": {"physical_candidate_found": False, "known_generator": "benchmarks/r43/madingley_r43.R changes provider NPP by a bounded normalized environment factor; it does not establish ARCANA physical units", "inputs_formula_units_scaling": "no ARCANA physical NPP generator with verified carbon/time/area units recovered", "fail_closed_reason": "units cannot be inferred from magnitude or filename"},
        "physical_units_verified": False,
        "temporal_coverage": {"strategy": "INDEPENDENT_ECOLOGICAL_OPPORTUNITY_SNAPSHOTS", "all_required_anchors": False, "coverage": "no usable physical-NPP anchors; A1 forage covers anchors only as proxy", "subset_only": False, "present_day_only": False, "extrapolation": False},
        "spatial_compatibility": {"arcana_grid": "90x180 lat/lon with changing paleogeography and latitude-dependent cell area", "candidate_grid": "prior Madingley 1-degree provider grid", "classification": "SEMANTICALLY_UNSAFE", "production_remapping": False, "required_future_transform": "area-aware, units-preserving, time-slice regrid retaining land mask, latitude, cell area, shoreline and provenance"},
        "decision": "BLOCKED_ONLY_NORMALIZED_PROXY_EXISTS",
        "missing_quantity_contract": {"quantity": "physical terrestrial NPP", "units": "provider-compatible carbon mass per area per time, explicitly documented", "spatial_support": "ARCANA-compatible 90x180 or losslessly area-aware regrid", "temporal_anchors": "each authorized terrestrial snapshot anchor; no silent interpolation", "environmental_inputs": ["land/sea and shoreline state", "temperature", "precipitation", "seasonality", "radiation/PAR or equivalent if required", "vegetation/productivity model inputs"], "uncertainty": "source and transformation uncertainty masks retained", "madingley_compatibility": "12 monthly provider layers with verified units and terrestrial semantics"},
        "recommended_next_operation": "R5.17-B7-A3F2-P5 PHYSICAL PRIMARY PRODUCTIVITY PROVIDER SUITABILITY GATE",
        "governance": {"Madingley_invoked": False, "physical_npp_synthesized": False, "normalized_proxy_rescaled": False, "animal_resource_support_materialized": False, "historical_abundance_materialized": False, "k_x_t_materialized": False, "human_management_used": False, "population_target_used": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("""# R5.17-B7-A3F2-P4\n\n## Decision\n\n**BLOCKED_ONLY_NORMALIZED_PROXY_EXISTS**. The exact Madingley requirement is physical terrestrial NPP supplied as 12 monthly provider-grid layers with documented carbon mass/area/time units. The recovered ARCANA surfaces contain normalized NPP factors, A1 forage proxies, and R3.34 producer-resource proxies, but no generator-backed physical NPP authority.\n\nPrior Madingley input files are provider payloads, not ARCANA authority; the prior runner applies a normalized environment factor and explicitly does not establish physical units. No magnitude-based or 0..1 rescaling is permitted. Existing grid differences also require an area-aware, units-preserving adapter.\n\nThe exact next operation is **R5.17-B7-A3F2-P5 PHYSICAL PRIMARY PRODUCTIVITY PROVIDER SUITABILITY GATE**. No Madingley run, NPP synthesis, remapping, resource materialization, current-state/index update, staging, commit, or push occurred.\n\n`AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n""", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
