from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
from typing import Any

TARGET = Path("src/arcana_worldsim/scientific_engines/r432_target_authority_binding_geonomics_static.py")
MANIFEST = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_32.json")
R423 = Path("outputs/v0_6D1_R4_23/R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json")
OUT = Path("outputs/v0_6D1_R4_32_R2")
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

OLD = """    # J18 R423 translation
    r=by.get(J18,{}) ; src=r.get('canonical_spatial_source') or {}; sp=root/str(src.get('path','')); ok=bool(sp.exists() and src.get('sha256') and sha256(sp)==src.get('sha256'))
    records.append({'job_id':J18,'window_id':'SAPIENT_200KA_TO_0','source_authority_kind':'R3_28_CANONICAL_HIGH_RESOLUTION_SPATIAL_REPLAY',
        'sources':[{'path':src.get('path'),'sha256':src.get('sha256'),'hash_match':ok}],
        'required_mappings':{'time_mapping':'snapshot_age_ka','space_mapping':'snapshot_deme_state:grid_row,grid_col + snapshot_active','population_mapping':'population_proxy','domain_mapping':'sapient spatial population support','uncertainty_mapping':'preserve replay/candidate dimensions; no target-derived tuning'},
        'static_parameter_manifest_valid':ok and r.get('binding_translation_materialized') is True})
    # J21 R423 translation
    r=by.get(J21,{}) ; ss=r.get('canonical_spatial_sources') or []; chk=[]
    for s in ss:
        sp=root/str(s.get('path','')); chk.append({'path':s.get('path'),'sha256':s.get('sha256'),'role':s.get('role'),'hash_match':bool(sp.exists() and s.get('sha256') and sha256(sp)==s.get('sha256'))})
    ok=bool(len(chk)==2 and all(x['hash_match'] for x in chk))
    records.append({'job_id':J21,'window_id':'PRODUCER_20KA_TO_0','source_authority_kind':'R3_33_R3_34_CANONICAL_HOLOCENE_RESOURCE_LANDSCAPE_BINDING',
        'sources':chk,'required_mappings':{'time_mapping':'anchor_age_ka exact shared anchors','space_mapping':'shared raster grid index; no cross-layer interpolation','population_mapping':'producer_landscape resource_abundance/suitability as producer support only, not agent count synthesis','domain_mapping':'producer resource landscape','uncertainty_mapping':'environment and producer layers remain provenance-separate; cross-layer numeric mixing forbidden without later explicit authority'},
        'static_parameter_manifest_valid':ok and r.get('binding_translation_materialized') is True})
"""

NEW = """    # J18/J21 R423 translation.
    # R4.23 deliberately stores only summary/materialization state in its registry
    # records and freezes the detailed canonical spatial binding in profile_path.
    # R4.32 must dereference that frozen profile instead of assuming the detailed
    # source fields were duplicated into the summary registry.
    def _r423_profile(summary:dict[str,Any])->tuple[dict[str,Any],Path|None]:
        rel=summary.get('profile_path')
        if not rel:
            return {},None
        pp=root/str(rel)
        return (load(pp),pp) if pp.exists() else ({},pp)

    r=by.get(J18,{})
    pr,pp=_r423_profile(r)
    src=pr.get('canonical_spatial_source') or {}
    sp=root/str(src.get('path',''))
    ok=bool(
        pp is not None and pp.exists()
        and pr.get('job_id')==J18
        and r.get('binding_materialized') is True
        and sp.exists() and src.get('sha256') and sha256(sp)==src.get('sha256')
    )
    records.append({'job_id':J18,'window_id':'SAPIENT_200KA_TO_0','source_authority_kind':'R3_28_CANONICAL_HIGH_RESOLUTION_SPATIAL_REPLAY',
        'r423_profile_path':r.get('profile_path'),'r423_binding_materialized':r.get('binding_materialized'),
        'sources':[{'path':src.get('path'),'sha256':src.get('sha256'),'hash_match':ok}],
        'required_mappings':{'time_mapping':'snapshot_age_ka','space_mapping':'snapshot_deme_state:grid_row,grid_col + snapshot_active','population_mapping':'population_proxy','domain_mapping':'sapient spatial population support','uncertainty_mapping':'preserve replay/candidate dimensions; no target-derived tuning'},
        'static_parameter_manifest_valid':ok})

    r=by.get(J21,{})
    pr,pp=_r423_profile(r)
    ss=pr.get('canonical_spatial_sources') or []
    chk=[]
    for s in ss:
        sp=root/str(s.get('path',''))
        chk.append({'path':s.get('path'),'sha256':s.get('sha256'),'role':s.get('role'),
                    'hash_match':bool(sp.exists() and s.get('sha256') and sha256(sp)==s.get('sha256'))})
    ok=bool(
        pp is not None and pp.exists()
        and pr.get('job_id')==J21
        and r.get('binding_materialized') is True
        and len(chk)==2 and all(x['hash_match'] for x in chk)
    )
    records.append({'job_id':J21,'window_id':'PRODUCER_20KA_TO_0','source_authority_kind':'R3_33_R3_34_CANONICAL_HOLOCENE_RESOURCE_LANDSCAPE_BINDING',
        'r423_profile_path':r.get('profile_path'),'r423_binding_materialized':r.get('binding_materialized'),
        'sources':chk,'required_mappings':{'time_mapping':'anchor_age_ka exact shared anchors','space_mapping':'shared raster grid index; no cross-layer interpolation','population_mapping':'producer_landscape resource_abundance/suitability as producer support only, not agent count synthesis','domain_mapping':'producer resource landscape','uncertainty_mapping':'environment and producer layers remain provenance-separate; cross-layer numeric mixing forbidden without later explicit authority'},
        'static_parameter_manifest_valid':ok})
"""

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def loadj(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))

def writej(p: Path, x: Any):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def find_record(reg: dict, jid: str) -> dict:
    for r in reg.get("records") or []:
        if r.get("job_id") == jid:
            return r
    return {}

def update_manifest_hashes(obj: Any, target_norm: str, new_sha: str, new_bytes: int) -> int:
    n = 0
    if isinstance(obj, dict):
        p = obj.get("path") or obj.get("file")
        if isinstance(p, str) and p.replace("\\","/") == target_norm:
            if "sha256" in obj:
                obj["sha256"] = new_sha
                n += 1
            if "size" in obj:
                obj["size"] = new_bytes
            if "bytes" in obj:
                obj["bytes"] = new_bytes
        for v in obj.values():
            n += update_manifest_hashes(v, target_norm, new_sha, new_bytes)
    elif isinstance(obj, list):
        for v in obj:
            n += update_manifest_hashes(v, target_norm, new_sha, new_bytes)
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    target = root / TARGET
    manifest = root / MANIFEST
    r423p = root / R423
    out = root / OUT
    out.mkdir(parents=True, exist_ok=True)

    if not target.exists() or not manifest.exists() or not r423p.exists():
        raise SystemExit("R4.32-R2 PRECONDITION FAILURE: target/manifest/R4.23 registry missing")

    reg = loadj(r423p)
    proof = {}
    for jid, source_key, nsrc in (
        (J18, "canonical_spatial_source", 1),
        (J21, "canonical_spatial_sources", 2),
    ):
        s = find_record(reg, jid)
        pp_rel = s.get("profile_path")
        pp = root / str(pp_rel or "")
        pr = loadj(pp) if pp_rel and pp.exists() else {}
        src = pr.get(source_key)
        if source_key.endswith("sources"):
            srcs = src or []
        else:
            srcs = [src or {}]
        src_checks = []
        for row in srcs:
            fp = root / str(row.get("path") or "")
            expected = row.get("sha256")
            src_checks.append({
                "path": row.get("path"),
                "exists": fp.exists(),
                "expected_sha256": expected,
                "actual_sha256": sha(fp) if fp.exists() else None,
                "hash_match": bool(fp.exists() and expected and sha(fp) == expected),
            })
        proof[jid] = {
            "summary_binding_materialized": s.get("binding_materialized"),
            "profile_path": pp_rel,
            "profile_exists": pp.exists(),
            "profile_job_id": pr.get("job_id"),
            "profile_source_field": source_key,
            "source_count": len(srcs),
            "source_checks": src_checks,
        }
        good = (
            s.get("binding_materialized") is True
            and pp.exists()
            and pr.get("job_id") == jid
            and len(srcs) == nsrc
            and all(x["hash_match"] for x in src_checks)
        )
        if not good:
            writej(out/"R4_32_R2_PREPATCH_CAUSE_PROOF.json", {
                "stage":"v0.6D1-R4.32-R2","status":"BLOCKED_R432_R2_R423_PROFILE_AUTHORITY_PRECONDITION_FAILURE",
                "proof":proof
            })
            raise SystemExit(f"R4.32-R2 PRECONDITION FAILURE for {jid}")

    before = target.read_text(encoding="utf-8")
    pre_sha = sha(target)
    already = NEW in before
    if not already:
        if OLD not in before:
            raise SystemExit("R4.32-R2 FAIL-CLOSED: expected buggy R4.32 block not found exactly; no patch applied")
        backup = out / "PREPATCH_r432_target_authority_binding_geonomics_static.py"
        shutil.copy2(target, backup)
        target.write_text(before.replace(OLD, NEW, 1), encoding="utf-8")

    post_sha = sha(target)
    post_bytes = target.stat().st_size

    # Reseal the R4.32 source authority manifest to the authorized R2 producer hash.
    m = loadj(manifest)
    backup_manifest = out / "PREPATCH_SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_32.json"
    if not backup_manifest.exists():
        shutil.copy2(manifest, backup_manifest)
    updates = update_manifest_hashes(m, TARGET.as_posix(), post_sha, post_bytes)
    if updates < 1:
        raise SystemExit("R4.32-R2 FAIL-CLOSED: target producer entry not found in R4.32 source authority manifest")
    writej(manifest, m)

    audit = {
        "stage":"v0.6D1-R4.32-R2",
        "status":"PASS_R432_R2_R423_PROFILE_INDIRECTION_REPAIR_APPLIED",
        "root_cause":"R432_CONSUMER_READ_R423_SUMMARY_RECORD_AS_IF_IT_CONTAINED_DETAILED_PROFILE_SOURCE_FIELDS",
        "repair":"DEREFERENCE_FROZEN_R423_PROFILE_PATH_FOR_J18_J21_AND_USE_SUMMARY_BINDING_MATERIALIZED_AS_TERMINAL_MATERIALIZATION_AUTHORITY",
        "target_file":TARGET.as_posix(),
        "target_prepatch_sha256":pre_sha,
        "target_postpatch_sha256":post_sha,
        "target_postpatch_bytes":post_bytes,
        "manifest_hash_entry_updates":updates,
        "r423_authority_proof":proof,
        "governance":{
            "r423_modified":False,
            "canonical_state_changed":False,
            "external_engine_execution_performed":False,
            "target_numeric_execution_performed":False,
            "readjudication_performed":False,
            "gate_weakening_performed":False,
            "failed_r432_evidence_preserved":True
        }
    }
    writej(out/"R4_32_R2_REPAIR_AUDIT.json", audit)
    print(json.dumps(audit, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
