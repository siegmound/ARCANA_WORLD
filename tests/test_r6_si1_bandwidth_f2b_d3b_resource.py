import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from scripts.r6_si1_bandwidth_f2b_d3b_resource import (
    ARITHMETIC_VERIFIED,
    D3A_REPORT_SHA256,
    F2AV_RECOVERY_MANIFEST_SHA256,
    INSUFFICIENT_RESOURCE_AUTHORITY,
    INVALID_INPUT,
    OFFLINE_VALIDATOR_PASS,
    SOURCE_IDENTITY_VERIFIED,
    IDENTITY_DECLARED_ONLY,
    load_case_json,
    validate_resource_budget,
)


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "configs/r6_shells_si1/engineering_case.json"
ABI = {"real64_bytes": 8, "integer_bytes": 4, "logical_bytes": 4, "character_bytes": 1}
FAMILIES = [
    "matrix_stiff", "element_real", "node_real", "node_integer_logical", "dof_real_integer",
    "boundary", "element_integer_logical", "plates", "list", "runtime_nodes", "region_lr",
]


def inputs():
    case, case_sha = load_case_json(CASE_PATH)
    case["derived_n_rank"] = 128_884
    case["band_dimensions"] = {"kl": 727, "ku": 727, "LDAB": 2182}
    identity = {
        "case_id": case["case_id"],
        "source_commit": "9adb986f510d81d220ab39b69a2df71704aac606",
        "configuration_sha256": case_sha,
        "allocation_inventory_sha256": D3A_REPORT_SHA256,
        "band_dimension_evidence_sha256": F2AV_RECOVERY_MANIFEST_SHA256,
    }
    return case, identity


def run(case=None, identity=None, **kwargs):
    base_case, base_identity = inputs()
    return validate_resource_budget(
        copy.deepcopy(case if case is not None else base_case),
        lr_n=kwargs.pop("lr_n", 0), abi=kwargs.pop("abi", ABI),
        identity=copy.deepcopy(identity if identity is not None else base_identity),
        allocation_families=kwargs.pop("allocation_families", FAMILIES), **kwargs,
    )


def evidence_paths(case_path=CASE_PATH):
    return {
        "engineering_case": case_path,
        "d3a_report": ROOT / "docs/arcana/SI1_BW1_F2B_D3A_ATTESTABILITY_AUDIT.md",
        "f2av_recovery_manifest": ROOT / "outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/F2AV_RECOVERY_ARTIFACT_MANIFEST.json",
    }


def test_si1_integer_formula_and_lr_term_match_independent_reference():
    result = run(lr_n=0)
    assert result["status"] == OFFLINE_VALIDATOR_PASS
    assert result["matrix_bytes"] == 2_249_799_104
    assert result["named_array_subtotal_bytes"] == 2_932_975_900 + 112
    assert result["calculated_named_array_bytes"] == 2_932_976_012
    assert result["array_family_bytes"]["region_lr"] == 112
    assert result["is_upper_bound_on_rss"] is False
    assert result["real_process_or_job_memory"] == "UNKNOWN"


def test_copy_a0_b0_delta_and_known_corrected_total():
    result = run(lr_n=0, scenario="COPY_A0_B0")
    assert result["status"] == OFFLINE_VALIDATOR_PASS
    assert result["preservation_increment_bytes"] == 2_250_830_176
    assert result["calculated_named_array_bytes"] == 5_183_806_188
    # Removing the LR=0 term gives the D3A corrected fixed subtotal.
    assert result["calculated_named_array_bytes"] - 112 == 5_183_806_076


def test_total_budget_request_fails_closed_but_reports_static_arithmetic():
    result = run(require_complete_budget=True)
    assert result["status"] == INSUFFICIENT_RESOURCE_AUTHORITY
    assert result["fair_enforced_limits"] == "PENDING_HPC_MEASUREMENT"


def test_integer_abi_rejects_lr_increment_overflow_and_accepts_last_safe_value():
    signed_max = 2**31 - 1
    assert run(lr_n=signed_max)["status"] == INVALID_INPUT
    assert run(lr_n=signed_max - 1)["status"] == OFFLINE_VALIDATOR_PASS
    assert run(lr_n=2**31)["status"] == INVALID_INPUT


def test_asymmetric_si1_band_or_dimension_disagreement_is_rejected():
    case, _ = inputs()
    case["band_dimensions"] = {"kl": 726, "ku": 727, "LDAB": 2181}
    assert run(case=case)["status"] == INVALID_INPUT
    case, _ = inputs()
    case["derived_n_rank"] = 128_885
    assert run(case=case)["status"] == INVALID_INPUT


def test_artifact_hashes_membership_and_dimensions_can_be_verified_from_bytes():
    result = run(evidence_paths=evidence_paths())
    assert result["status"] == OFFLINE_VALIDATOR_PASS
    assert result["arithmetic_status"] == ARITHMETIC_VERIFIED
    assert result["provenance"]["evidence_artifact_identity"] == SOURCE_IDENTITY_VERIFIED
    assert result["provenance"]["source_commit_identity"].startswith("DECLARED_ONLY")
    assert result["provenance"]["manifest_member_count"] == 3


def test_unverified_mapping_stays_declared_only_and_tampering_fails_closed():
    ordinary = run()
    assert ordinary["provenance"]["evidence_artifact_identity"] == IDENTITY_DECLARED_ONLY
    assert ordinary["arithmetic_status"] == ARITHMETIC_VERIFIED
    assert ordinary["source_identity_status"] == IDENTITY_DECLARED_ONLY
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
        temp = Path(temp_name)
        changed_case = temp / "engineering_case.json"
        changed = json.loads(CASE_PATH.read_text(encoding="utf-8"))
        changed["feg"]["nodes"] += 1
        changed_case.write_text(json.dumps(changed), encoding="utf-8")
        result = run(evidence_paths=evidence_paths(changed_case))
        assert result["status"] == INVALID_INPUT
    missing = evidence_paths()
    missing["d3a_report"] = ROOT / "docs/does-not-exist.md"
    assert run(evidence_paths=missing)["status"] == INVALID_INPUT
    case, _ = inputs()
    case["band_dimensions"] = {"kl": 726, "ku": 726, "LDAB": 2179}
    assert run(case=case, evidence_paths=evidence_paths())["status"] == INVALID_INPUT
    escaped = evidence_paths()
    escaped["d3a_report"] = ROOT.parent
    assert run(evidence_paths=escaped)["status"] == INVALID_INPUT


def test_manifest_member_corruption_is_rejected_without_touching_source_evidence():
    original = evidence_paths()["f2av_recovery_manifest"].parent
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
        copy_root = Path(temp_name) / "recovery"
        copy_root.mkdir()
        for source in original.iterdir():
            if source.is_file():
                shutil.copy2(source, copy_root / source.name)
        member = copy_root / "BW1_F2AV_ASYMMETRY_CENSUS_NORMALIZED.csv"
        member.write_bytes(member.read_bytes() + b"\n")
        paths = evidence_paths()
        paths["f2av_recovery_manifest"] = copy_root / "F2AV_RECOVERY_ARTIFACT_MANIFEST.json"
        assert run(evidence_paths=paths)["status"] == INVALID_INPUT


def _copy_recovery_evidence(destination):
    source = evidence_paths()["f2av_recovery_manifest"].parent
    destination.mkdir()
    for item in source.iterdir():
        if item.is_file():
            shutil.copy2(item, destination / item.name)
    return destination / "F2AV_RECOVERY_ARTIFACT_MANIFEST.json"


def test_result_replacement_after_authenticated_snapshot_is_not_parsed_or_certified():
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
        copied = Path(temp_name) / "recovery"
        manifest_path = _copy_recovery_evidence(copied)
        result_path = copied / "F2AV_RECOVERY_RESULT.json"
        original_result = result_path.read_bytes()
        changed = json.loads(original_result)
        changed["diagnostics"]["stage"]["kl"] = 726
        changed["diagnostics"]["stage"]["ku"] = 726
        changed["diagnostics"]["stage"]["nKRows"] = 2179
        changed_bytes = json.dumps(changed, separators=(",", ":")).encode("utf-8")
        if len(changed_bytes) != len(original_result):
            # Preserve exact size to reproduce the prior equal-length race.
            changed_bytes = original_result.replace(b"727", b"726", 1)
        assert len(changed_bytes) == len(original_result)
        paths = evidence_paths()
        paths["f2av_recovery_manifest"] = manifest_path

        import scripts.r6_si1_bandwidth_f2b_d3b_resource as resource
        original_reader = resource._read_snapshot
        replaced = False

        def replace_after_snapshot(path, **kwargs):
            nonlocal replaced
            snapshot = original_reader(path, **kwargs)
            if Path(path) == result_path and not replaced:
                result_path.write_bytes(changed_bytes)
                replaced = True
            return snapshot

        resource._read_snapshot = replace_after_snapshot
        try:
            result = run(evidence_paths=paths)
        finally:
            resource._read_snapshot = original_reader

        assert replaced
        assert result["status"] == OFFLINE_VALIDATOR_PASS
        assert result["provenance"]["evidence_artifact_identity"] == SOURCE_IDENTITY_VERIFIED
        assert result["dimensions"]["kl"] == 727
        assert result["dimensions"]["LDAB"] == 2182
        assert hashlib.sha256(original_result).hexdigest() != hashlib.sha256(result_path.read_bytes()).hexdigest()
        assert result["provenance"]["snapshot_sha256"]["manifest_members"]["F2AV_RECOVERY_RESULT.json"] == hashlib.sha256(original_result).hexdigest()


def test_json_evidence_documents_are_each_opened_once_for_snapshot_and_parse():
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
        manifest_path = _copy_recovery_evidence(Path(temp_name) / "recovery")
        paths = evidence_paths()
        paths["f2av_recovery_manifest"] = manifest_path
        original_open = os.open
        opened = {}

        def counting_open(path, flags, *args, **kwargs):
            key = str(Path(path).resolve())
            opened[key] = opened.get(key, 0) + 1
            return original_open(path, flags, *args, **kwargs)

        os.open = counting_open
        try:
            result = run(evidence_paths=paths)
        finally:
            os.open = original_open
        assert result["status"] == OFFLINE_VALIDATOR_PASS
        for document in (CASE_PATH, paths["d3a_report"], manifest_path,
                         manifest_path.parent / "F2AV_RECOVERY_RESULT.json"):
            assert opened[str(document.resolve())] == 1


def test_modified_result_with_pinned_digest_and_modified_manifest_fail_closed():
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
        manifest_path = _copy_recovery_evidence(Path(temp_name) / "result-case")
        result_path = manifest_path.parent / "F2AV_RECOVERY_RESULT.json"
        original = result_path.read_bytes()
        result_document = json.loads(original)
        result_document["diagnostics"]["stage"]["kl"] = "726"
        altered = (json.dumps(result_document, indent=2) + "\n").encode("utf-8")
        assert altered != original and len(altered) == len(original)
        result_path.write_bytes(altered)
        paths = evidence_paths()
        paths["f2av_recovery_manifest"] = manifest_path
        assert run(evidence_paths=paths)["status"] == INVALID_INPUT


def test_manifest_member_size_hash_and_membership_alterations_fail_closed():
    for mutation in ("member_size", "member_hash", "membership"):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
            manifest_path = _copy_recovery_evidence(Path(temp_name) / mutation)
            manifest = json.loads(manifest_path.read_bytes())
            if mutation == "member_size":
                manifest["artifacts"][0]["bytes"] += 1
            elif mutation == "member_hash":
                manifest["artifacts"][0]["sha256"] = "0" * 64
            else:
                manifest["artifacts"].pop()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            paths = evidence_paths()
            paths["f2av_recovery_manifest"] = manifest_path
            assert run(evidence_paths=paths)["status"] == INVALID_INPUT


def test_directory_symlink_inside_evidence_root_is_rejected():
    with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
        root = Path(temp_name)
        copied = root / "recovery"
        manifest_path = _copy_recovery_evidence(copied)
        outside_dir = root / "outside-dir"
        outside_dir.mkdir()
        (outside_dir / "extra.txt").write_text("outside", encoding="utf-8")
        link_dir = copied / "linked-directory"
        try:
            os.symlink(outside_dir, link_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            import pytest
            pytest.skip("directory symlink creation is not available under this Windows account")
        paths = evidence_paths()
        paths["f2av_recovery_manifest"] = manifest_path
        assert run(evidence_paths=paths)["status"] == INVALID_INPUT


def test_manifest_member_traversal_and_symlink_escape_are_rejected():
    paths = evidence_paths()
    paths["f2av_recovery_manifest"] = paths["f2av_recovery_manifest"].parent / ".." / "F2AV_WITH_F2A_REFERENCE_V1" / "F2AV_RECOVERY_ARTIFACT_MANIFEST.json"
    assert run(evidence_paths=paths)["status"] == INVALID_INPUT

    with tempfile.TemporaryDirectory(dir=ROOT) as temp_name:
        root = Path(temp_name)
        outside = root / "outside.json"
        outside.write_bytes(CASE_PATH.read_bytes())
        link = root / "linked-case.json"
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            import pytest
            pytest.skip("symlink creation is not available under this Windows account")
        assert run(evidence_paths=evidence_paths(link))["status"] == INVALID_INPUT


def test_invalid_dimensions_abi_identity_and_inventory_are_rejected():
    case, identity = inputs()
    case["derived_n_rank"] = 128_883
    assert run(case=case)["status"] == INVALID_INPUT

    case, _ = inputs()
    case["band_dimensions"]["LDAB"] = 2181
    assert run(case=case)["status"] == INVALID_INPUT
    case, _ = inputs()
    del case["derived_n_rank"]
    assert run(case=case)["status"] == INVALID_INPUT

    bad_abi = dict(ABI, integer_bytes=8)
    assert run(abi=bad_abi)["status"] == INVALID_INPUT
    assert run(allocation_families=FAMILIES[:-1])["status"] == INVALID_INPUT
    assert run(allocation_families=FAMILIES + [FAMILIES[0]])["status"] == INVALID_INPUT

    identity["band_dimension_evidence_sha256"] = "0" * 64
    assert run(identity=identity)["status"] == INVALID_INPUT


def test_target_byte_count_overflow_is_rejected():
    result = run(byte_count_bits=32, scenario="COPY_A0_B0")
    assert result["status"] == INVALID_INPUT
    assert "overflows" in result["reason"]


def test_result_is_deterministic_and_configuration_identity_is_pinned():
    first = run(lr_n=14, scenario="COPY_A0_B0")
    second = run(lr_n=14, scenario="COPY_A0_B0")
    assert first == second
    _, identity = inputs()
    identity["configuration_sha256"] = "0" * 64
    assert run(identity=identity)["status"] == INVALID_INPUT


def test_missing_band_identity_and_unsupported_preservation_are_rejected():
    case, _ = inputs()
    del case["band_dimensions"]
    assert run(case=case)["status"] == INVALID_INPUT
    assert run(scenario="REPLAYABLE_MATVEC")["status"] == INVALID_INPUT
