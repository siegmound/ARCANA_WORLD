from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import sys
from typing import Any

import numpy as np

from arcana_worldsim.state_query.r50_query import (
    EXPECTED_PARENT_HASHES,
    EXPECTED_R456_VERDICT,
    STAGE,
    _semantic_array_hash,
    discover_r456_authority,
    sha256_file,
    write_json,
)

FINAL_STATUS = "PASS_R50_SELECTIVE_HIGH_RESOLUTION_NESTED_REPLAY_AND_ARBITRARY_AGE_STATE_QUERY_SEALED"
CANDIDATE_STATUS = "PASS_R50_QUERY_CONTRACT_AUTHORITY_RESOLVER_AND_20KA_17P5KA_END_TO_END_CANDIDATE"
EXPECTED_CANDIDATE_FILES = {
    "R5_0_20KA_QUERY.json",
    "R5_0_20KA_DERIVED_STATE.npz",
    "R5_0_20KA_PROVENANCE.json",
    "R5_0_20KA_UNCERTAINTY.json",
    "R5_0_20KA_REPLAY_RECIPE.json",
    "R5_0_20KA_QUERY_SUMMARY.json",
    "R5_0_17P5KA_QUERY.json",
    "R5_0_17P5KA_DERIVED_STATE.npz",
    "R5_0_17P5KA_PROVENANCE.json",
    "R5_0_17P5KA_UNCERTAINTY.json",
    "R5_0_17P5KA_REPLAY_RECIPE.json",
    "R5_0_17P5KA_QUERY_SUMMARY.json",
    "R5_0_INTEGRATED_AUDIT.json",
    "R5_0_AUTHORITY_RESOLUTION_SUMMARY.json",
    "R5_0_DETERMINISTIC_REPLAY_RECIPES.json",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def semantic_npz_hash(path: Path) -> str:
    with np.load(path, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    return _semantic_array_hash(arrays)


def recipe_hash_valid(obj: dict[str, Any]) -> bool:
    expected = obj.get("recipe_sha256")
    if not isinstance(expected, str):
        return False
    base = dict(obj)
    base.pop("recipe_sha256", None)
    return hashlib.sha256(canonical_json_bytes(base)).hexdigest() == expected


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out).resolve() if args.out else root / "outputs" / "v0_6D1_R5_0"
    authority_path = root / "R5_0_FINAL_SEAL_AUTHORITY.json"
    source_manifest_path = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_0.json"
    checks: list[dict[str, Any]] = []

    def ck(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    try:
        authority = load_json(authority_path)
        output_manifest_path = out / "R5_0_OUTPUT_MANIFEST.json"
        audit_path = out / "R5_0_INTEGRATED_AUDIT.json"
        resolution_path = out / "R5_0_AUTHORITY_RESOLUTION_SUMMARY.json"
        recipes_path = out / "R5_0_DETERMINISTIC_REPLAY_RECIPES.json"
        required_top = [authority_path, source_manifest_path, output_manifest_path, audit_path, resolution_path, recipes_path]
        ck("required_seal_inputs_present", all(p.is_file() for p in required_top), [str(p) for p in required_top if not p.is_file()])
        if not all(p.is_file() for p in required_top):
            raise RuntimeError("Missing R5.0 final-seal inputs")

        ck("seal_authority_stage_exact", authority.get("stage") == STAGE)
        ck("seal_authority_final_verdict_exact", authority.get("final_verdict") == FINAL_STATUS)
        ck("seal_authority_candidate_status_exact", authority.get("candidate_status_required") == CANDIDATE_STATUS)

        # Re-verify R4.56 independently at sealing time.
        r456 = discover_r456_authority(root)
        ck("r456_runtime_authority_verified_now", r456.get("status") == "R456_RUNTIME_AUTHORITY_VERIFIED", r456.get("status"))
        ck("r456_expected_verdict_bound", r456.get("expected_verdict") == EXPECTED_R456_VERDICT)
        ck("r456_all_semantic_checks_pass", bool(r456.get("checks")) and all(r456["checks"].values()), r456.get("checks"))

        # Re-verify immutable scientific parents, not only the earlier audit's statement.
        live_parent_hashes: dict[str, str] = {}
        for rel, expected in EXPECTED_PARENT_HASHES.items():
            p = root / rel
            live_parent_hashes[rel] = sha256_file(p) if p.is_file() else "MISSING"
        ck("exact_parent_count_is_9", len(EXPECTED_PARENT_HASHES) == int(authority["exact_parent_hash_count_required"]))
        ck("all_immutable_parent_hashes_match_now", live_parent_hashes == EXPECTED_PARENT_HASHES)

        manifest = load_json(output_manifest_path)
        files = manifest.get("files", {})
        ck("candidate_manifest_status_exact", manifest.get("status") == CANDIDATE_STATUS, manifest.get("status"))
        ck("candidate_manifest_scientific_eligible", manifest.get("scientific_candidate_eligible") is True)
        ck("candidate_manifest_allowlist_policy", manifest.get("manifest_policy") == "EXACT_ALLOWLIST_NO_DIRECTORY_SWEEP")
        ck("candidate_manifest_artifact_count_exact", manifest.get("candidate_artifact_count") == 15 == authority["candidate_artifact_count_required"])
        ck("candidate_manifest_filename_set_exact", set(files) == EXPECTED_CANDIDATE_FILES, sorted(set(files) ^ EXPECTED_CANDIDATE_FILES))
        ck("candidate_manifest_excludes_seal_outputs", not any("FINAL_SEAL" in name for name in files))

        candidate_hashes: dict[str, dict[str, Any]] = {}
        candidate_files_ok = True
        for name in sorted(EXPECTED_CANDIDATE_FILES):
            p = out / name
            meta = files.get(name, {})
            if not p.is_file():
                candidate_files_ok = False
                candidate_hashes[name] = {"error": "missing"}
                continue
            live = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
            candidate_hashes[name] = live
            if live != {"bytes": meta.get("bytes"), "sha256": meta.get("sha256")}:
                candidate_files_ok = False
        ck("all_15_candidate_artifacts_match_manifest_bytes_and_hashes", candidate_files_ok)

        audit = load_json(audit_path)
        ck("integrated_audit_candidate_status_exact", audit.get("status") == CANDIDATE_STATUS, audit.get("status"))
        ck("integrated_audit_scientific_eligible", audit.get("scientific_candidate_eligible") is True)
        ck("integrated_audit_23_of_23", audit.get("checks_passed") == 23 and audit.get("checks_total") == 23 and audit.get("checks_failed") == 0)
        ck("integrated_audit_all_individual_checks_pass", len(audit.get("checks", [])) == 23 and all(x.get("pass") is True for x in audit.get("checks", [])))
        summary = audit.get("summary", {})
        ck("integrated_audit_r456_verified", summary.get("r456_runtime_verified") is True)
        ck("integrated_audit_parent_count_9", summary.get("exact_parent_hash_count") == 9)

        expected_sem = authority["semantic_state_sha256"]
        ck("audit_20ka_semantic_hash_authorially_pinned", summary.get("20ka_semantic_state_sha256") == expected_sem["20ka"])
        ck("audit_17p5ka_semantic_hash_authorially_pinned", summary.get("17p5ka_semantic_state_sha256") == expected_sem["17p5ka"])
        for key in ("full_history_rerun_performed", "external_engine_execution_performed", "canonical_state_changed", "deep_biological_coupling"):
            ck(f"audit_governance_{key}_false", summary.get(key) is False)

        resolution = load_json(resolution_path)
        ck("authority_resolution_complete", resolution.get("status") == "R50_AUTHORITY_RESOLUTION_COMPLETE")
        ck("authority_resolution_parent_hashes_exact", resolution.get("exact_parent_hashes") == EXPECTED_PARENT_HASHES)
        rr = resolution.get("r456_authority", {})
        ck("authority_resolution_r456_verified", rr.get("status") == "R456_RUNTIME_AUTHORITY_VERIFIED")
        ck("authority_resolution_r456_semantic_checks_pass", bool(rr.get("checks")) and all(rr["checks"].values()))

        # Bind package semantics directly to the NPZ payloads; summaries alone are insufficient.
        package_records: dict[str, Any] = {}
        for tag, age, slug in (("20ka", 20.0, "20KA"), ("17p5ka", 17.5, "17P5KA")):
            q = load_json(out / f"R5_0_{slug}_QUERY.json")
            prov = load_json(out / f"R5_0_{slug}_PROVENANCE.json")
            unc = load_json(out / f"R5_0_{slug}_UNCERTAINTY.json")
            recipe = load_json(out / f"R5_0_{slug}_REPLAY_RECIPE.json")
            qs = load_json(out / f"R5_0_{slug}_QUERY_SUMMARY.json")
            npz_path = out / f"R5_0_{slug}_DERIVED_STATE.npz"
            live_sem = semantic_npz_hash(npz_path)

            ck(f"{tag}_query_target_age_exact", q.get("target_age_ka") == age)
            ck(f"{tag}_query_no_canonical_write", q.get("canonical_write") is False and q.get("authority_semantics") == "DERIVED_QUERY_ONLY_NO_CANONICAL_WRITE")
            ck(f"{tag}_query_no_extrapolation_authorized", q.get("allow_temporal_extrapolation") is False)
            ck(f"{tag}_summary_target_age_exact", qs.get("target_age_ka") == age and qs.get("status") == "R50_DERIVED_STATE_QUERY_COMPLETE")
            ck(f"{tag}_npz_semantic_hash_matches_authority", live_sem == expected_sem[tag], live_sem)
            ck(f"{tag}_summary_semantic_hash_matches_npz", qs.get("semantic_state_sha256") == live_sem)
            ck(f"{tag}_provenance_parent_hashes_exact", prov.get("parent_hashes") == EXPECTED_PARENT_HASHES)
            ck(f"{tag}_provenance_no_canonical_write", prov.get("canonical_write") is False)
            ck(f"{tag}_provenance_modes_exact", qs.get("provenance_modes") == authority["required_provenance_modes"][tag], qs.get("provenance_modes"))
            governance = qs.get("governance", {})
            ck(f"{tag}_all_forbidden_governance_flags_false", all(governance.get(k) is False for k in authority["required_governance_false"]), governance)
            global_rules = unc.get("global_rules", {})
            ck(f"{tag}_uncertainty_rules_fail_closed", global_rules == {
                "derived_state_is_not_canonical": True,
                "no_extrapolation": True,
                "no_hidden_interpolation": True,
                "no_invented_numeric_uncertainty": True,
            })
            ck(f"{tag}_recipe_hash_self_consistent", recipe_hash_valid(recipe))
            ck(f"{tag}_recipe_governance_clean", recipe.get("randomness_used") is False and recipe.get("external_engine_execution") is False and recipe.get("full_history_rerun") is False and recipe.get("canonical_write") is False)
            package_records[tag] = {
                "target_age_ka": age,
                "semantic_state_sha256": live_sem,
                "derived_state_file_sha256": sha256_file(npz_path),
                "recipe_sha256": recipe.get("recipe_sha256"),
                "provenance_modes": qs.get("provenance_modes"),
            }

        all_recipes = load_json(recipes_path)
        recipes = all_recipes.get("recipes", [])
        ck("combined_recipe_registry_exactly_two", all_recipes.get("status") == "R50_DETERMINISTIC_REPLAY_RECIPES" and len(recipes) == 2)
        ck("combined_recipe_registry_hashes_valid", len(recipes) == 2 and all(recipe_hash_valid(r) for r in recipes))
        individual_recipe_hashes = {
            load_json(out / "R5_0_20KA_REPLAY_RECIPE.json").get("recipe_sha256"),
            load_json(out / "R5_0_17P5KA_REPLAY_RECIPE.json").get("recipe_sha256"),
        }
        ck("combined_recipe_registry_matches_individual_recipes", {r.get("recipe_sha256") for r in recipes} == individual_recipe_hashes)

        failed = [x for x in checks if not x["pass"]]
        if failed:
            result = {
                "stage": STAGE,
                "status": "FAIL_R50_FINAL_SEAL",
                "sealed": False,
                "scientific_candidate_eligible": False,
                "checks_passed": len(checks) - len(failed),
                "checks_total": len(checks),
                "checks_failed": len(failed),
                "failed": failed,
            }
            print(json.dumps(result, indent=2))
            return 1

        output_manifest_sha = sha256_file(output_manifest_path)
        source_manifest_sha = sha256_file(source_manifest_path)
        final = {
            "stage": STAGE,
            "stage_name": authority["stage_name"],
            "status": FINAL_STATUS,
            "sealed": True,
            "scientific_candidate_eligible": True,
            "scientific_meaning": authority["scientific_meaning"],
            "checks_passed": len(checks),
            "checks_total": len(checks),
            "checks_failed": 0,
            "checks": checks,
            "source_authority_manifest_sha256": source_manifest_sha,
            "candidate_output_manifest_sha256": output_manifest_sha,
            "candidate_artifact_hashes": candidate_hashes,
            "immutable_parent_hashes": live_parent_hashes,
            "r456_runtime_authority": r456,
            "packages": package_records,
            "summary": {
                "r456_runtime_verified": True,
                "exact_parent_hash_count": len(live_parent_hashes),
                "candidate_artifact_count": len(candidate_hashes),
                "20ka_semantic_state_sha256": package_records["20ka"]["semantic_state_sha256"],
                "17p5ka_semantic_state_sha256": package_records["17p5ka"]["semantic_state_sha256"],
                "full_history_rerun_performed": False,
                "external_engine_execution_performed": False,
                "canonical_state_changed": False,
                "deep_biological_coupling": False,
                "derived_refinement_promoted_to_canon": False,
            },
        }
        seal_path = out / "R5_0_FINAL_SEAL.json"
        write_json(seal_path, final)
        seal_manifest = {
            "stage": STAGE,
            "status": "PASS_R50_FINAL_SEAL_MANIFEST",
            "final_seal_file": {
                "path": seal_path.name,
                "bytes": seal_path.stat().st_size,
                "sha256": sha256_file(seal_path),
            },
            "candidate_output_manifest": {
                "path": output_manifest_path.name,
                "sha256": output_manifest_sha,
            },
            "source_authority_manifest": {
                "path": source_manifest_path.name,
                "sha256": source_manifest_sha,
            },
        }
        write_json(out / "R5_0_FINAL_SEAL_MANIFEST.json", seal_manifest)
        print(json.dumps({
            "stage": STAGE,
            "status": FINAL_STATUS,
            "sealed": True,
            "checks_passed": len(checks),
            "checks_total": len(checks),
            "summary": final["summary"],
            "candidate_output_manifest_sha256": output_manifest_sha,
            "final_seal_sha256": seal_manifest["final_seal_file"]["sha256"],
        }, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"stage": STAGE, "status": "FAIL_R50_FINAL_SEAL", "error": repr(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
