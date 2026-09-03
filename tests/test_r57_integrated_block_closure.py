from __future__ import annotations
from pathlib import Path
import json
import pytest

from arcana_worldsim.state_query import r57_block_closure as r57


def wj(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_manifest(out: Path, stage: str, status: str):
    files = {}
    for name in sorted(r57.EXPECTED_MANIFEST_FILES[stage]):
        p = out / name
        assert p.is_file(), name
        files[name] = {"bytes": p.stat().st_size, "sha256": r57.sha256_file(p)}
    wj(out / r57.OUTPUT_MANIFEST_NAME[stage], {"stage": "x", "status": status, "files": files})


def audit(stage: str, summary: dict):
    n = r57.EXPECTED_CHECK_COUNTS[stage]
    return {
        "stage": stage,
        "status": r57.CANDIDATE_STATUS[stage],
        "scientific_candidate_eligible": True,
        "checks_passed": n,
        "checks_total": n,
        "failed": [],
        "checks": {f"c{i}": True for i in range(n)},
        "summary": summary,
    }


def common_summary():
    return {"canonical_state_changed": False, "derived_refinement_promoted_to_canon": False, "deep_biological_coupling": False, "majority_vote": False}


def build_fake_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path
    # Source referenced by R5.6 parent binding.
    j14 = root / r57.J14_REL; j14.parent.mkdir(parents=True, exist_ok=True); j14.write_bytes(b"j14")
    src55 = root / "src/arcana_worldsim/state_query/r55_contact_history.py"
    src55.parent.mkdir(parents=True, exist_ok=True)
    src55.write_text("# r55 source\n", encoding="utf-8")

    # Sealed R5.2 parent. Patch test constants to the synthetic live hashes.
    o52 = root / r57.R52_OUT; o52.mkdir(parents=True)
    wj(root / r57.R52_PLAN, {"plan": "r52"})
    wj(root / r57.R52_RAW, {"raw": "r52"})
    wj(root / r57.R52_OUTPUT_MANIFEST, {"manifest": "r52"})
    psha = r57.sha256_file(root / r57.R52_PLAN)
    rsha = r57.sha256_file(root / r57.R52_RAW)
    msha = r57.sha256_file(root / r57.R52_OUTPUT_MANIFEST)
    seal = {
        "sealed": True,
        "status": "PASS_R52_TARGETED_EXPANSION_CORRIDOR_VALIDATION_SEALED",
        "summary": {"robust_family_count": 12, "scientific_stream_count": 80, "numeric_corridor_truth_claimed": False, "canonical_state_changed": False, "derived_refinement_promoted_to_canon": False, "deep_biological_coupling": False},
        "authority": {"r52_execution_plan_sha256": psha, "r52_raw_evidence_manifest_sha256": rsha, "r52_candidate_output_manifest_sha256": msha},
    }
    wj(root / r57.R52_FINAL_SEAL, seal)
    monkeypatch.setattr(r57, "EXPECTED_R52_PLAN_SHA256", psha)
    monkeypatch.setattr(r57, "EXPECTED_R52_RAW_SHA256", rsha)
    monkeypatch.setattr(r57, "EXPECTED_R52_OUTPUT_MANIFEST_SHA256", msha)
    monkeypatch.setattr(r57, "EXPECTED_R52_FINAL_SEAL_SHA256", r57.sha256_file(root / r57.R52_FINAL_SEAL))

    # R5.3
    o53 = root / r57.R53_OUT; o53.mkdir(parents=True)
    wj(o53 / "R5_3_CDMETAPOP_RUNTIME_IDENTITY.json", {"status":"PASS_R53_CDMETAPOP_3_08_PINNED_RUNTIME_IDENTITY","cdmetapop_version":"3.08","cdmetapop_commit":"3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118"})
    wj(o53 / "R5_3_CDMETAPOP_EXECUTION_PLAN.json", {"standardized_diagnostic_semantics":{"r52_range_geometry_used_as_cdmetapop_input":False}})
    wj(o53 / "R5_3_CDMETAPOP_EXECUTION_BRIDGE.json", {"records":[]})
    raw53 = root / "outputs/v0_6D1_R5_3/raw/a.txt"; raw53.parent.mkdir(parents=True); raw53.write_text("r53", encoding="utf-8")
    wj(o53 / "R5_3_RAW_EVIDENCE_MANIFEST.json", {"file_count":1,"files":{"outputs/v0_6D1_R5_3/raw/a.txt":{"bytes":raw53.stat().st_size,"sha256":r57.sha256_file(raw53)}}})
    wj(o53 / "R5_3_CDMETAPOP_STREAM_EVIDENCE.json", {"records":[]})
    wj(o53 / "R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json", {"records":[]})
    s53 = common_summary() | {"robust_family_count":12,"group_count":36,"scientific_stream_count":72,"sensitivity_record_count":36,"external_engine":"CDMetaPOP","external_engine_version":"3.08","external_engine_commit":"3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118","new_external_engine_execution_performed":True,"numeric_demographic_truth_claimed":False,"r52_corridor_geometry_promoted_to_input_authority":False,"external_engine_defines_arcana_target":False}
    wj(o53 / "R5_3_INTEGRATED_AUDIT.json", audit("R5.3", s53))
    make_manifest(o53,"R5.3",r57.CANDIDATE_STATUS["R5.3"])

    # R5.4
    o54 = root / r57.R54_OUT; o54.mkdir(parents=True)
    b54={"status":"R54_PARENT_CANDIDATE_BINDING","r53_plan_sha256":r57.sha256_file(o53/"R5_3_CDMETAPOP_EXECUTION_PLAN.json"),"r53_audit_sha256":r57.sha256_file(o53/"R5_3_INTEGRATED_AUDIT.json"),"r53_sensitivity_sha256":r57.sha256_file(o53/"R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json"),"r53_output_manifest_sha256":r57.sha256_file(o53/"R5_3_OUTPUT_MANIFEST.json")}
    wj(o54/"R5_4_PARENT_CANDIDATE_BINDING.json",b54)
    wj(o54/"R5_4_NEMO_RUNTIME_IDENTITY.json",{"status":"PASS_R54_NEMO_2_4_2_PINNED_RUNTIME_IDENTITY","nemo_version":"2.4.2","conda_package_version":"2.4.2","nemo_executable_sha256":"a"*64})
    wj(o54/"R5_4_NEMO_EXECUTION_PLAN.json",{"semantics":{"r53_cdmetapop_values_used_to_fit_nemo":False,"r53_used_only_for_side_by_side_reporting":True}})
    wj(o54/"R5_4_NEMO_EXECUTION_BRIDGE.json",{})
    raw54=root/"outputs/v0_6D1_R5_4/raw/b.txt"; raw54.parent.mkdir(parents=True); raw54.write_text("r54",encoding="utf-8")
    wj(o54/"R5_4_RAW_EVIDENCE_MANIFEST.json",{"file_count":1,"files":{"outputs/v0_6D1_R5_4/raw/b.txt":{"bytes":raw54.stat().st_size,"sha256":r57.sha256_file(raw54)}}})
    wj(o54/"R5_4_NEMO_STREAM_EVIDENCE.json",{})
    wj(o54/"R5_4_NEMO_MATCHED_FLOW_CONTROL_PAIRS.json",{})
    wj(o54/"R5_4_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY.json",{})
    s54=common_summary()|{"family_count":12,"group_count":36,"scientific_stream_count":144,"matched_pair_count":72,"sensitivity_record_count":36,"external_engine":"NEMO","external_engine_version":"2.4.2","new_external_engine_execution_performed":True,"r53_cdmetapop_values_used_to_fit_nemo":False,"cross_engine_numeric_truth_claimed":False,"cross_engine_metrics_forced_to_equality":False}
    wj(o54/"R5_4_INTEGRATED_AUDIT.json",audit("R5.4",s54))
    make_manifest(o54,"R5.4",r57.CANDIDATE_STATUS["R5.4"])

    # R5.5
    o55=root/r57.R55_OUT; o55.mkdir(parents=True)
    atlas=o55/"R5_5_CONTACT_OPPORTUNITY_ATLAS.npz"; atlas.write_bytes(b"fake npz")
    wj(o55/"R5_5_CONTACT_ZONE_HISTORY.json",{"semantics":"MATCHED_CONTACT_NOT_REALIZED_ADMIXTURE"})
    wj(o55/"R5_5_CROSS_ENGINE_CONTACT_CONTEXT.json",{})
    b55={"status":"R55_PARENT_CANDIDATE_BINDING","r54_plan_sha256":r57.sha256_file(o54/"R5_4_NEMO_EXECUTION_PLAN.json"),"r54_audit_sha256":r57.sha256_file(o54/"R5_4_INTEGRATED_AUDIT.json"),"r54_sensitivity_sha256":r57.sha256_file(o54/"R5_4_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY.json"),"r54_output_manifest_sha256":r57.sha256_file(o54/"R5_4_OUTPUT_MANIFEST.json"),"r53_sensitivity_sha256":r57.sha256_file(o53/"R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json"),"r53_output_manifest_sha256":r57.sha256_file(o53/"R5_3_OUTPUT_MANIFEST.json"),"j14_sha256":r57.sha256_file(j14)}
    wj(o55/"R5_5_PARENT_CANDIDATE_BINDING.json",b55)
    s55=common_summary()|{"family_count":12,"cross_lineage_pair_count":35,"pair_with_one_cell_contact_opportunity_count":35,"pair_with_exact_overlap_count":35,"age_state_count":141,"cross_engine_context_record_count":105,"new_external_engine_execution_performed":False,"r53_cdmetapop_used_as_contact_geometry":False,"r54_nemo_used_as_contact_geometry":False,"realized_admixture_claimed":False,"numeric_gene_flow_truth_claimed":False,"single_contact_history_winner_selected":False}
    wj(o55/"R5_5_INTEGRATED_AUDIT.json",audit("R5.5",s55))
    make_manifest(o55,"R5.5",r57.CANDIDATE_STATUS["R5.5"])

    # R5.6
    o56=root/r57.R56_OUT; o56.mkdir(parents=True)
    b56={"status":"R56_PARENT_CANDIDATE_BINDING","r55_audit_sha256":r57.sha256_file(o55/"R5_5_INTEGRATED_AUDIT.json"),"r55_history_sha256":r57.sha256_file(o55/"R5_5_CONTACT_ZONE_HISTORY.json"),"r55_atlas_sha256":r57.sha256_file(atlas),"r55_context_sha256":r57.sha256_file(o55/"R5_5_CROSS_ENGINE_CONTACT_CONTEXT.json"),"r55_output_manifest_sha256":r57.sha256_file(o55/"R5_5_OUTPUT_MANIFEST.json"),"r55_source_sha256":r57.sha256_file(src55)}
    wj(o56/"R5_6_PARENT_CANDIDATE_BINDING.json",b56)
    wj(o56/"R5_6_SLIM_RUNTIME_IDENTITY.json",{"status":"PASS_R56_SLIM_5_2_PINNED_RUNTIME_IDENTITY","slim_version":"5.2","slim_package_version":"5.2","tskit_version":"1.0.3","slim_executable_sha256":"b"*64})
    wj(o56/"R5_6_SLIM_EXECUTION_PLAN.json",{"schedule_class_count":1,"planned_stream_count":6,"semantics":{"r55_binary_contact_schedule_is_input_authority":True,"r55_contact_support_fraction_used_as_migration_magnitude":False,"simulated_ancestry_is_not_promoted_to_realized_historical_admixture":True}})
    wj(o56/"R5_6_EXECUTION_BRIDGE.json",{})
    raw56=o56/"slim_work/x/result.txt"; raw56.parent.mkdir(parents=True); raw56.write_text("r56",encoding="utf-8")
    wj(o56/"R5_6_RAW_EVIDENCE_MANIFEST.json",{"file_count":1,"files":{"slim_work/x/result.txt":{"bytes":raw56.stat().st_size,"sha256":r57.sha256_file(raw56)}}})
    wj(o56/"R5_6_ANCESTRY_ADMIXTURE_SENSITIVITY.json",{})
    s56=common_summary()|{"pair_count":35,"schedule_class_count":1,"scientific_stream_count":6,"variant_count":3,"seed_count":2,"external_engine":"SLiM","external_engine_version":"5.2","new_external_engine_execution_performed":True,"tree_sequence_ancestry_analysis_performed":True,"numeric_admixture_truth_claimed":False,"realized_historical_admixture_claimed":False,"r55_contact_support_fraction_used_as_migration_magnitude":False,"result_selected_tuning":False,"single_history_winner_selected":False}
    wj(o56/"R5_6_INTEGRATED_AUDIT.json",audit("R5.6",s56))
    make_manifest(o56,"R5.6",r57.CANDIDATE_STATUS["R5.6"])
    return root


def test_integrated_block_audit_and_seal_pass(tmp_path, monkeypatch):
    root=build_fake_tree(tmp_path,monkeypatch)
    a=r57.run_integrated_audit(root)
    assert a["scientific_block_seal_eligible"] is True
    wj(root/"R5_7_FINAL_BLOCK_SEAL_AUTHORITY.json",{"stage":r57.STAGE,"stage_name":"test","final_verdict":r57.FINAL_STATUS,"scientific_meaning":"test"})
    wj(root/"SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_7.json",{"test":True})
    s=r57.seal_block(root)
    assert s["sealed"] is True
    assert s["status"] == r57.FINAL_STATUS
    assert (root/r57.OUT_REL/"R5_7_FINAL_BLOCK_SEAL.json").is_file()


def test_raw_evidence_drift_fails_closed(tmp_path, monkeypatch):
    root=build_fake_tree(tmp_path,monkeypatch)
    (root/"outputs/v0_6D1_R5_4/raw/b.txt").write_text("tampered",encoding="utf-8")
    a=r57.run_integrated_audit(root)
    assert a["scientific_block_seal_eligible"] is False
    assert any(x["name"]=="R5.4_raw_evidence_manifest_rehash_complete" for x in a["failed"])


def test_parent_binding_drift_fails_closed(tmp_path, monkeypatch):
    root=build_fake_tree(tmp_path,monkeypatch)
    p=root/r57.R53_OUT/"R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json"
    wj(p,{"tampered":True})
    a=r57.run_integrated_audit(root)
    assert a["scientific_block_seal_eligible"] is False
    assert any(x["name"]=="candidate_to_candidate_hash_bindings_revalidated_live" for x in a["failed"])


def test_schedule_class_observation_is_bound(tmp_path, monkeypatch):
    root=build_fake_tree(tmp_path,monkeypatch)
    p=root/r57.R56_OUT/"R5_6_SLIM_EXECUTION_PLAN.json"
    d=json.loads(p.read_text()); d["schedule_class_count"]=2; d["planned_stream_count"]=12; wj(p,d)
    a=r57.run_integrated_audit(root)
    assert a["scientific_block_seal_eligible"] is False
    assert any(x["name"]=="r56_schedule_class_count_exactly_one_observed" for x in a["failed"])
