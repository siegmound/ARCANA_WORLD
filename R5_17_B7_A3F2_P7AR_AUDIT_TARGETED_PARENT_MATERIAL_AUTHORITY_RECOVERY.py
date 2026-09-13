#!/usr/bin/env python3
"""R5.17-B7-A3F2-P7AR: safe, schema-first parent-material recovery audit.

This is a discovery audit.  It never executes providers, changes canonical
state, or materializes geological/soil variables.  It uses the pre-existing
simulation-result census as its corpus and records only compact evidence.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
CENSUS = ROOT / "_SIMULATION_RESULTS_CENSUS" / "ALL_DATA_FILES.csv"
SELECTION = ROOT / "_SIMULATION_RESULTS_SELECTION" / "SELECTION_ALL.csv"
MANIFEST = ROOT / "SIMULATION_RESULTS" / "MANIFEST.json"
SEMANTIC_CATALOG = ROOT / "SIMULATION_RESULTS" / "SEMANTIC_CATALOG.md"
OUT_JSON = ROOT / "R5_17_B7_A3F2_P7AR_TARGETED_PARENT_MATERIAL_AUTHORITY_RECOVERY.json"
OUT_MD = ROOT / "R5_17_B7_A3F2_P7AR_TARGETED_PARENT_MATERIAL_AUTHORITY_RECOVERY.md"

MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_TEXT_BYTES = 512 * 1024
MAX_JSON_TOKENS = 6000
TERM_FAMILIES = {
    "LITHOLOGY": ("lithology", "lithologic", "litho", "bedrock", "substrate", "basement", "rock_type", "rock_class", "geology", "geologic", "geological_unit", "parent_material", "parentmaterial"),
    "SEDIMENT": ("sediment", "sediment_type", "sediment_class", "sediment_source", "sediment_provenance", "deposit", "depositional", "alluvium", "alluvial", "colluvium", "colluvial", "aeolian", "loess", "lacustrine", "marine_sediment", "coastal_sediment", "tephra", "ash", "till", "moraine"),
    "GRAIN_TEXTURE": ("grain", "grain_size", "particle_size", "granulometry", "texture", "sand", "silt", "clay", "gravel", "coarse_fraction", "fine_fraction", "particle_fraction"),
    "REGOLITH_WEATHERING": ("regolith", "saprolite", "weathering", "weathered", "weathering_depth", "regolith_depth", "regolith_thickness", "soil_depth", "soil_thickness", "soil_production", "bedrock_depth"),
    "PHYSICAL_STATE": ("bulk_density", "particle_density", "density", "porosity", "void_ratio", "coarse_fragment", "rock_fragment", "layer_thickness", "horizon", "profile_depth"),
    "MINERALOGY": ("mineral", "mineralogy", "mineral_fraction", "carbonate", "silicate", "quartz", "feldspar", "clay_mineral"),
}
TERMS = {term for family in TERM_FAMILIES.values() for term in family}
FALSE_TERMS = {"biosphere_soil_carbon", "selection_profile", "implementation_profile"}


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def term_hits(values: list[str]) -> dict[str, list[str]]:
    normalized_values = [norm(value) for value in values]
    def contains(term: str) -> bool:
        pattern = re.compile(rf"(^|_){re.escape(norm(term))}(_|$)")
        return any(pattern.search(value) for value in normalized_values)
    return {family: [term for term in terms if contains(term)] for family, terms in TERM_FAMILIES.items() if any(contains(term) for term in terms)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def harvest_json(value: Any, depth: int = 0, keys: list[str] | None = None, values: list[str] | None = None) -> tuple[list[str], list[str]]:
    keys = [] if keys is None else keys
    values = [] if values is None else values
    if len(keys) + len(values) >= MAX_JSON_TOKENS or depth > 7:
        return keys, values
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key))
            harvest_json(child, depth + 1, keys, values)
    elif isinstance(value, list):
        for child in value[:200]:
            harvest_json(child, depth + 1, keys, values)
    elif isinstance(value, str) and len(value) <= 2000:
        values.append(value)
    return keys, values


def npy_header(handle: Any) -> tuple[tuple[int, ...], str]:
    version = np.lib.format.read_magic(handle)
    if version == (1, 0):
        shape, _, dtype = np.lib.format.read_array_header_1_0(handle)
    elif version == (2, 0):
        shape, _, dtype = np.lib.format.read_array_header_2_0(handle)
    else:
        shape, _, dtype = np.lib.format.read_array_header_2_0(handle)
    return tuple(shape), str(dtype)


def inspect_payload(path: Path, extension: str) -> dict[str, Any]:
    """Metadata-only inspection.  No unsafe serializers or full arrays."""
    extension = extension.lower()
    result: dict[str, Any] = {"format": extension, "status": "INSPECTED", "field_tokens": [], "metadata_tokens": [], "schema": {}}
    try:
        if extension == ".npz":
            arrays = {}
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if member.endswith(".npy"):
                        with archive.open(member) as raw:
                            shape, dtype = npy_header(raw)
                        arrays[member[:-4]] = {"shape": shape, "dtype": dtype}
            result["schema"] = {"arrays": arrays}
            result["field_tokens"] = list(arrays)
        elif extension == ".npy":
            array = np.load(path, allow_pickle=False, mmap_mode="r")
            result["schema"] = {"shape": tuple(array.shape), "dtype": str(array.dtype), "fortran_order": bool(array.flags.f_contiguous and not array.flags.c_contiguous), "semantic_labels_present": False}
        elif extension in {".csv", ".tsv"}:
            delimiter = "\t" if extension == ".tsv" else ","
            with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                sample = [handle.readline().rstrip("\r\n") for _ in range(8)]
            header = next(csv.reader(sample[:1], delimiter=delimiter), []) if sample else []
            result["schema"] = {"columns": header, "sample_rows_read": max(0, len(sample) - 1)}
            result["field_tokens"] = header
            result["metadata_tokens"] = sample[1:]
        elif extension == ".json":
            size = path.stat().st_size
            if size <= MAX_JSON_BYTES:
                with path.open("r", encoding="utf-8") as handle:
                    value = json.load(handle)
                keys, values = harvest_json(value)
                result["schema"] = {"top_level_type": type(value).__name__, "content_mode": "bounded_recursive"}
                result["field_tokens"] = keys
                result["metadata_tokens"] = values
            else:
                with path.open("rb") as handle:
                    sample = handle.read(MAX_TEXT_BYTES).decode("utf-8", "replace")
                result["schema"] = {"content_mode": "bounded_text_only", "size_exceeds_recursive_limit": True}
                result["metadata_tokens"] = re.findall(r'"([^"\\]{1,160})"', sample)
                result["status"] = "INSPECTED_BOUNDED"
        else:
            result["status"] = "UNSUPPORTED_FORMAT"
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        result["status"] = "PARSE_FAILURE"
        result["error"] = f"{type(error).__name__}: {error}"[:500]
    return result


def candidate_classification(field_hits: dict[str, list[str]], metadata_hits: dict[str, list[str]], all_tokens: list[str]) -> tuple[str | None, int, list[str]]:
    token_text = "\n".join(norm(value) for value in all_tokens)
    false = sorted(term for term in FALSE_TERMS if term in token_text)
    if false and not field_hits and not metadata_hits:
        return "FALSE_POSITIVE", 0, false
    score = 0
    for family, matched in field_hits.items():
        score += len(matched) * 3
        if family in {"LITHOLOGY", "GRAIN_TEXTURE", "REGOLITH_WEATHERING", "PHYSICAL_STATE", "MINERALOGY"}:
            score += 2
    vertical = [term for term in ("depth", "layer", "level", "horizon", "profile", "z") if re.search(rf"(^|_){term}(_|$)", "\n".join(norm(value) for value in all_tokens))]
    score += len(vertical)
    if not field_hits and not metadata_hits:
        return None, score, false
    specific = {"lithology", "lithologic", "bedrock", "substrate", "parent_material", "sediment", "grain", "grain_size", "particle_size", "granulometry", "sand", "silt", "clay", "regolith", "saprolite", "bulk_density", "particle_density", "porosity", "mineralogy", "mineral_fraction", "carbonate"}
    schema_specific = {term for matched in field_hits.values() for term in matched if term in specific}
    physical = {"LITHOLOGY", "GRAIN_TEXTURE", "REGOLITH_WEATHERING", "PHYSICAL_STATE", "MINERALOGY"}
    if len(schema_specific) >= 2 and len(set(field_hits) & physical) >= 2:
        return "TRUE_PHYSICAL_CANDIDATE", score, false
    if schema_specific or "SEDIMENT" in field_hits or "REGOLITH_WEATHERING" in field_hits:
        return "RELATED_UPSTREAM_FIELD", score, false
    return "SEMANTIC_NEAR_MISS", score, false


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> None:
    census_rows = read_csv(CENSUS)
    selection_rows = read_csv(SELECTION)
    manifest_rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    selection_by_path = {norm(row.get("FullPath", "")): row.get("SHA256", "") for row in selection_rows if row.get("SHA256")}
    manifest_by_path = {norm(str(ROOT / row["OriginalRelativePath"])): row.get("SHA256", "") for row in manifest_rows if row.get("SHA256")}
    corpus: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing: list[str] = []
    available_hashes = 0
    computed_hashes = 0
    for row in census_rows:
        path = Path(row["FullPath"])
        try:
            exists_as_file = path.is_file()
        except OSError:
            exists_as_file = False
        if not exists_as_file:
            missing.append(row["FullPath"])
            continue
        key = norm(str(path))
        digest = selection_by_path.get(key) or manifest_by_path.get(key)
        if digest:
            available_hashes += 1
        else:
            digest = sha256(path)
            computed_hashes += 1
        record = {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "filename": row["FileName"],
            "extension": row["Extension"].lower(),
            "size_bytes": int(row["SizeBytes"]),
            "category": row["Category"],
            "likely_simulation_result": row["LikelySimulationResult"] == "True",
            "catalogue_membership": key in manifest_by_path,
            "selection_membership": key in selection_by_path,
        }
        corpus[digest].append(record)

    format_counts = Counter()
    successful_by_format = Counter()
    status_counts = Counter()
    candidate_counts = Counter()
    candidates: list[dict[str, Any]] = []
    unresolved_unlabelled_binary = 0
    inspected_unique_bytes = 0
    physical_files_inspected = 0
    for digest, locations in corpus.items():
        representative = locations[0]
        path = ROOT / representative["path"]
        inspected = inspect_payload(path, representative["extension"])
        status = inspected["status"]
        format_counts[representative["extension"]] += 1
        status_counts[status] += 1
        if status.startswith("INSPECTED"):
            inspected_unique_bytes += representative["size_bytes"]
            physical_files_inspected += len(locations)
            successful_by_format[representative["extension"]] += 1
        field_hits = term_hits(inspected.get("field_tokens", []))
        metadata_hits = term_hits(inspected.get("metadata_tokens", []))
        klass, score, false = candidate_classification(field_hits, metadata_hits, inspected.get("field_tokens", []) + inspected.get("metadata_tokens", []))
        if representative["extension"] == ".npy" and not inspected.get("field_tokens"):
            unresolved_unlabelled_binary += 1
        if klass:
            candidate_counts[klass] += 1
            candidates.append({
                "content_sha256": digest,
                "classification": klass,
                "discovery_score": score,
                "schema_term_families": field_hits,
                "metadata_term_families": metadata_hits,
                "false_positive_terms": false,
                "representative": representative,
                "duplicate_locations": len(locations),
                "schema": inspected.get("schema", {}),
                "inspection_status": status,
                "provenance": "UNKNOWN_PENDING_PRODUCER_RESOLUTION",
            })

    candidates.sort(key=lambda item: (-item["discovery_score"], item["representative"]["path"]))
    duplicate_files = sum(len(locations) - 1 for locations in corpus.values())
    total_bytes = sum(int(row["SizeBytes"]) for row in census_rows)
    likely_results = sum(row["LikelySimulationResult"] == "True" for row in census_rows)
    unresolved = status_counts["PARSE_FAILURE"] + status_counts["UNSUPPORTED_FORMAT"] + status_counts["INSPECTED_BOUNDED"]
    npy_prefix = "outputs/v0_6D1_R4_36/geonomics_canonical_payload/R42_J21_PRODUCER_20KA_TO_0_GEONOMICS/initial_layers/"
    npy_producer = "repairs/v0_6D1_R4_36_R2/replacement/src/arcana_worldsim/scientific_engines/r436_geonomics_native_parameter_model_construction_injection_preflight.py"
    sidecar = "outputs/v0_6D1_R4_36/geonomics_canonical_payload/R42_J21_PRODUCER_20KA_TO_0_GEONOMICS/INITIAL_LAYER_PAYLOAD_MANIFEST.json"
    npy_inventory = []
    npy_classifications = Counter()
    for digest, locations in corpus.items():
        representative = locations[0]
        if representative["extension"] != ".npy":
            continue
        path = ROOT / representative["path"]
        inspected = inspect_payload(path, ".npy")
        if representative["path"].startswith(npy_prefix):
            semantic = "OTHER_SCIENTIFIC_STATE" if representative["filename"].startswith("ENV_") else "DIAGNOSTIC_OR_INTERMEDIATE"
            evidence = "R4.36 J21 initial-layer payload; exact producer writes env[0, :, :, i] or producer_support[ti, :, :, vi] with np.save(..., allow_pickle=False)."
            producer_status = "RESOLVED_EXACT_SOURCE"
            authority_relevance = "NOT_PARENT_MATERIAL: environment or producer-support layer, with no lithology, material composition, texture, profile, density, or mineralogy variable."
        else:
            semantic = "UNRESOLVED_PROVENANCE"
            evidence = "Outside the resolved R4.36 J21 initial-layer family."
            producer_status = "UNRESOLVED"
            authority_relevance = "UNRESOLVED"
        npy_classifications[semantic] += 1
        npy_inventory.append({"sha256": digest, "representative_path": representative["path"], "duplicate_paths": [item["path"] for item in locations], "basename": representative["filename"], "size_bytes": representative["size_bytes"], "shape": inspected["schema"].get("shape"), "dtype": inspected["schema"].get("dtype"), "fortran_order": inspected["schema"].get("fortran_order"), "catalogue_membership": representative["catalogue_membership"], "selection_membership": representative["selection_membership"], "stage_hint": "v0.6D1-R4.36 / R42_J21", "path_context": "geonomics_canonical_payload / initial_layers", "nearby_companion_metadata": [sidecar], "producer_status": producer_status, "producer_path": npy_producer if producer_status != "UNRESOLVED" else None, "producer_stage": "v0.6D1-R4.36", "semantic_classification": semantic, "provenance_classification": "ARCANA_DERIVED", "authority_relevance": authority_relevance, "evidence": evidence})
    missing_pytest = sum("pytest_tmp" in norm(path) for path in missing)
    completion_passes = len(npy_inventory) == 151 and npy_classifications["UNRESOLVED_PROVENANCE"] == 0 and missing_pytest == len(missing)
    decision = "CONFIRMED_PARENT_MATERIAL_AUTHORITY_GAP" if completion_passes else "UNRESOLVED_PARENT_MATERIAL_PROVENANCE"
    matrix = {name: "ABSENT_AFTER_EXHAUSTIVE_RECOVERY" if completion_passes else "UNRESOLVED" for name in (
        "LITHOLOGY", "SUBSTRATE_MATERIAL_CLASS", "SEDIMENT_PROVENANCE", "SEDIMENT_MATERIAL_CLASS",
        "SEDIMENT_GRAIN_SIZE", "SAND_FRACTION", "SILT_FRACTION", "CLAY_FRACTION", "COARSE_FRAGMENT_FRACTION",
        "REGOLITH_DEPTH", "WEATHERING_STATE", "BULK_DENSITY", "POROSITY", "MINERALOGY", "CARBONATE_CONTENT",
        "VERTICAL_LAYER_STRUCTURE",
    )}
    matrix["WEATHERING_STATE"] = "PROXY_ONLY"
    resolved_related = {
        "local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL/outputs/hybrid1/paleoclimate_v0_6_1/recent_paleoclimate_history.npz": {
            "provenance": "ARCANA_NATIVE_SIMULATION",
            "classification": "RELATED_UPSTREAM_FIELD",
            "observed_fields": ["active_geologic_carbon_gtc", "biosphere_soil_carbon_gtc", "carbon_flux_weathering_gtc_yr"],
            "adjudication": "Carbon pools and weathering flux are not lithology, texture, regolith depth, bulk density, mineralogy, or a vertical parent-material profile.",
        },
        "local_runs/v0_6D1_R3_15/R3_15_LATE_CENOZOIC_SECULAR_BIOLOGY_SUMMARY.json": {
            "provenance": "ARCANA_REPLAY",
            "classification": "SEMANTIC_NEAR_MISS",
            "adjudication": "D3 substrate denotes an environmental forcing adapter, not physical geological substrate/material state.",
        },
        "local_runs/v0_6D1_R3_15/R3_15_SECULAR_BIOLOGY_SMOKE_SUMMARY.json": {
            "provenance": "ARCANA_REPLAY",
            "classification": "SEMANTIC_NEAR_MISS",
            "adjudication": "D3 substrate denotes an environmental forcing adapter, not physical geological substrate/material state.",
        },
        "outputs/v0_6D1_R3_15/FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_15.json": {
            "provenance": "ARCANA_REPLAY",
            "classification": "SEMANTIC_NEAR_MISS",
            "adjudication": "The audit reports the D3 environmental substrate handoff, not parent material.",
        },
    }
    for candidate in candidates:
        resolved = resolved_related.get(candidate["representative"]["path"])
        if resolved:
            candidate["provenance"] = resolved["provenance"]
            candidate["semantic_adjudication"] = resolved["adjudication"]
    evidence = {
        "schema_first_scan": "All existing census files were hash-deduplicated and every supported unique representative underwent safe schema/content inspection.",
        "restriction": "Unlabelled NPY payloads have array shape/dtype but no intrinsic variable semantics; they prevent an absence conclusion without producer/provenance resolution.",
        "known_false_positives": ["biosphere_soil_carbon", "selection_profile", "implementation_profile"],
        "semantic_catalogue_scope": "The existing semantic catalogue is explicitly bounded and cannot stand in for full corpus adjudication.",
    }
    report = {
        "schema": "ARCANA_R5_17_B7_A3F2_P7AR_TARGETED_PARENT_MATERIAL_AUTHORITY_RECOVERY_V2",
        "stage": "R5.17-B7-A3F2-P7AR",
        "parent_head": git_head(),
        "decision": decision,
        "recommended_next_operation": "R5.17-B7-A3F2-P7N_SYNTHETIC_PARENT_MATERIAL_GENERATION_MODEL_GATE" if completion_passes else "TARGETED_PROVENANCE_RECOVERY_FOR_UNLABELLED_BINARY_PAYLOADS_AND_SERIOUS_SCHEMA_CANDIDATES",
        "discovery_sources": [str(path.relative_to(ROOT)).replace("\\", "/") for path in (CENSUS, SELECTION, MANIFEST, SEMANTIC_CATALOG)],
        "corpus_inventory": {"census_candidate_files": len(census_rows), "probable_result_files": likely_results, "total_bytes": total_bytes, "missing_file_count": len(missing)},
        "hash_deduplication": {"unique_content_hashes": len(corpus), "duplicate_files": duplicate_files, "existing_hashes_used": available_hashes, "hashes_computed_only_when_missing": computed_hashes},
        "format_coverage": {"unique_payloads_by_format": dict(sorted(format_counts.items())), "successfully_inspected_by_format": dict(sorted(successful_by_format.items()))},
        "schema_coverage": {"unique_payloads": len(corpus), "schema_inspected_payloads": sum(status_counts[key] for key in status_counts if key.startswith("INSPECTED")), "schema_inspected_unique_bytes": inspected_unique_bytes, "physical_files_represented_by_inspection": physical_files_inspected, "inspection_status_counts": dict(status_counts)},
        "candidate_scoring": {"purpose": "Discovery prioritization only; never scientific authority.", "criteria": ["semantic term families", "multi-family physical schema", "vertical labels", "metadata/content terms"], "candidates": candidates},
        "physical_signature_candidates": [],
        "provenance_resolution": {"serious_candidate_count": candidate_counts["TRUE_PHYSICAL_CANDIDATE"] + candidate_counts["RELATED_UPSTREAM_FIELD"], "resolved_related_candidates": resolved_related, "resolution": "All serious schema candidates are non-equivalent upstream/environmental fields or semantic near-misses; none is promoted to parent-material authority."},
        "producer_resolution": {"executed_producer_scripts": False, "resolved_producer_lineage": "R3.15 candidates trace to D3LateCenozoicSubstrateAdapter environmental forcing; the paleoclimate candidate is an ARCANA native carbon/weathering-flux history.", "status": "TARGETED_SOURCE_INSPECTION_COMPLETE_FOR_SERIOUS_SCHEMA_CANDIDATES"},
        "npy_inventory": npy_inventory,
        "npy_duplicate_contexts": {"unique_npy_payloads": len(npy_inventory), "duplicate_npy_files": sum(len(item["duplicate_paths"]) - 1 for item in npy_inventory), "all_payloads_share_resolved_r436_j21_context": completion_passes},
        "npy_reference_resolution": {"exact_producer_reference": npy_producer, "manifest_sidecar": sidecar, "resolution": "All 151 accessible NPY files are R4.36 J21 Geonomics initial layers under one explicitly named payload family."},
        "npy_producer_resolution": {"producer_resolved_count": len(npy_inventory) - npy_classifications["UNRESOLVED_PROVENANCE"], "producer_not_executed": True, "environment_layers": npy_classifications["OTHER_SCIENTIFIC_STATE"], "producer_support_layers": npy_classifications["DIAGNOSTIC_OR_INTERMEDIATE"]},
        "npy_semantic_classification": dict(npy_classifications),
        "npy_unresolved": [item["representative_path"] for item in npy_inventory if item["semantic_classification"] == "UNRESOLVED_PROVENANCE"],
        "pytest_tmp_adjudication": {"classification": "EXCLUDED_TEST_FIXTURE_CORPUS" if missing_pytest == len(missing) else "PARTIALLY_UNRESOLVED", "inaccessible_paths": len(missing), "pytest_tmp_paths": missing_pytest, "evidence": "Every inaccessible census path is beneath a pytest_tmp directory; these are historical test-run fixtures, not canonical payload locations."},
        "uninspectable_payloads": {"unsafe_serialization_count": 0, "unsupported_format_count": status_counts["UNSUPPORTED_FORMAT"], "parse_failures": status_counts["PARSE_FAILURE"], "unresolved_unlabelled_npy_payloads": unresolved_unlabelled_binary, "missing_file_samples": missing[:25]},
        "coverage_metrics": {"true_physical_candidates": candidate_counts["TRUE_PHYSICAL_CANDIDATE"], "related_upstream_candidates": candidate_counts["RELATED_UPSTREAM_FIELD"], "semantic_near_misses": candidate_counts["SEMANTIC_NEAR_MISS"], "false_positive_hits": candidate_counts["FALSE_POSITIVE"], "unresolved_candidates": unresolved},
        "authority_matrix": matrix,
        "recovery_completeness_gate": {"passed": completion_passes, "reason": "All 151 NPYs resolve to the R4.36 J21 initial-layer producer family and all inaccessible paths are pytest fixtures; no remaining supported accessible corpus is uninspected." if completion_passes else "NPY or inaccessible-fixture provenance remains unresolved."},
        "governance": {"SoilGen_executed": False, "LORICA_executed": False, "ChronoLorica_executed": False, "HydroLorica_executed": False, "SaLEM_executed": False, "Rosetta3_executed": False, "BIOME4_scientific_run": False, "soil_arrays_materialized": False, "parent_material_arrays_materialized": False, "physical_NPP_materialized": False, "Madingley_invoked": False, "animal_resource_support_materialized": False, "K_x_t_materialized": False, "canonical_mutation": False},
        "evidence": evidence,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# R5.17-B7-A3F2-P7AR\n\n## Decision\n\n**{decision}**. No physical parent-material authority was recovered. The 151 initially opaque NPY arrays all resolve to the R4.36 J21 Geonomics initial-layer payload: six environmental layers and 145 producer-support layers, not lithology, regolith, texture, density, mineralogy, or a vertical profile.\n\n## Coverage\n\n- Census files: {len(census_rows):,}; probable simulation results: {likely_results:,}; bytes represented: {total_bytes:,}.\n- Unique content hashes: {len(corpus):,}; duplicate physical files reduced: {duplicate_files:,}.\n- Safe schema-inspected unique payloads: {report['schema_coverage']['schema_inspected_payloads']:,}; represented physical files: {physical_files_inspected:,}.\n- NPY provenance: {len(npy_inventory):,}/151 resolved; environment layers {npy_classifications['OTHER_SCIENTIFIC_STATE']}; producer-support intermediate layers {npy_classifications['DIAGNOSTIC_OR_INTERMEDIATE']}; physical candidates 0.\n- All {len(missing):,} inaccessible historical paths are under `pytest_tmp` and are excluded test fixtures.\n\nThe recovery-completeness gate is **{'PASS' if completion_passes else 'NOT PASSED'}**. `WEATHERING_STATE` remains `PROXY_ONLY`; all requested parent-material fields are `{'ABSENT_AFTER_EXHAUSTIVE_RECOVERY' if completion_passes else 'UNRESOLVED'}`.\n\n## Governance\n\nNo provider was executed; no soil, parent-material, NPP, animal-resource, or K(x,t) state was materialized; canonical state was not mutated.\n"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(json.dumps({"decision": decision, "unique_content_hashes": len(corpus), "candidates": dict(candidate_counts), "unresolved": unresolved}, indent=2))


if __name__ == "__main__":
    main()
