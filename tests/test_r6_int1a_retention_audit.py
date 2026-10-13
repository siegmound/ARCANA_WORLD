from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile

import pytest

from scripts.r6_int1a_retention_audit import (
    AuditError,
    _difference_metrics,
    analyze_samples,
    load_verified_bundle,
    run_audit,
)


@pytest.fixture
def scratch_path():
    # Use one fresh, uniquely named repo-local directory because the managed
    # Windows temp mount rejects pytest's chmod/symlink setup.
    repo_root = Path(__file__).absolute().parents[1]
    with tempfile.TemporaryDirectory(prefix="int1a-test-", dir=repo_root) as folder:
        yield Path(folder)


def _document(times: list[float] | None = None) -> dict:
    times = times or [0.0, 1.0, 2.0, 3.0]
    width_values = [10.0, 11.0, 14.0, 16.0]
    temp_values = [[280.0, 1000.0, 1200.0], [280.0, 1001.0, 1203.0],
                   [280.0, 1004.0, 1205.0], [280.0, 1006.0, 1208.0]]
    coordinates = [0.0, 0.5, 1.0]
    rows = []
    for index, time in enumerate(times):
        width = width_values[index]
        lithosphere = 8.0 - index * 0.25
        row = {
            "record_type": "DIAGNOSTIC_SAMPLE" if index < len(times)-1 else "ENDPOINT_STATE",
            "support_id": "support-a", "elapsed_years": time,
            "time_s": time * 31_557_600.0, "width_m": width,
            "crust_m": 4.0-index*0.1, "lithosphere_m": lithosphere,
            "beta": width/10.0, "accumulated_strain": math.log(width/10.0),
            "material_coordinate": list(coordinates),
            "z_m": [x*lithosphere for x in coordinates],
            "temperature_k": temp_values[index],
        }
        rows.append(row)
    rows[-1].update({"materials": [], "initial_width_m": 10.0})
    rows[0]["record_type"] = "DIAGNOSTIC_SAMPLE"
    doc = {
        "schema": "ARCANA_R6_TF2B_NUMERICAL_STEP_SAMPLES_V2",
        "scope": "NONCANONICAL_ENGINEERING_REFERENCE_TRAJECTORY",
        "support_ids": ["support-a"],
        "sampling": "SYNTHETIC_TEST_ONLY",
        "resolution_fraction": 0.0005,
        "interpolation": "NONE",
        "maximum_samples_per_support_including_initial": 10001,
        "maximum_profile_nodes": 73,
        "units": {"elapsed_years": "year", "time_s": "s"},
        "all_numerical_substeps_captured": True,
        "sample_count_by_support": {"support-a": len(rows)},
        "samples_by_support": {"support-a": rows},
        "canonical_publication": False,
    }
    return doc


def test_endpoints_only_reconstruction_has_independent_expected_errors():
    metrics = analyze_samples(_document())
    endpoints = next(row for row in metrics["strategies"]
                     if row["strategy"] == "FIXED_ACTUAL_TIMESTAMP_SUBSET"
                     and row["retained_indices_0based"] == [0, 3])
    width = endpoints["support_errors"]["support-a"]["recorded_fields"]["width_m"]["combined_omitted_state_metrics"]
    assert width["max_abs_error"] == 1.0
    assert width["rmse"] == pytest.approx(math.sqrt(0.5))
    assert width["max_component_relative_error"] == pytest.approx(1.0 / 11.0)
    assert endpoints["retained_state_count_per_support"] == 2
    assert endpoints["omitted_state_count_per_support"] == 2
    temp = endpoints["support_errors"]["support-a"]["recorded_fields"]["temperature_k"]["per_omitted_sample"]
    assert [row["max_abs_error_node_index_0based"] for row in temp] == [1, 2]
    assert [row["max_abs_error_material_coordinate"] for row in temp] == [0.5, 1.0]
    derived = endpoints["support_errors"]["support-a"]["derived_quantities"]
    assert derived["area_m2_from_width_times_lithosphere"]["max_abs_error"] == pytest.approx(7.75)
    assert derived["beta_from_width_over_initial_width"]["max_abs_error"] == pytest.approx(0.1)
    assert derived["accumulated_strain_from_log_beta"]["max_abs_error"] == pytest.approx(
        math.log(1.2) - math.log(1.1))


def test_fixed_subsets_enumerate_each_internal_timestamp_and_full_retention():
    metrics = analyze_samples(_document())
    fixed = [row for row in metrics["strategies"] if not row["adaptive"]]
    assert [row["retained_indices_0based"] for row in fixed] == [
        [0, 3], [0, 1, 3], [0, 2, 3], [0, 1, 2, 3]
    ]
    full = fixed[-1]
    assert full["retention_ratio"] == 1.0
    assert full["support_errors"]["support-a"]["recorded_fields"]["temperature_k"][
        "combined_omitted_state_metrics"]["value_count"] == 0


def test_adaptive_selection_is_marked_retrospective_not_online():
    metrics = analyze_samples(_document())
    adaptive = metrics["strategies"][-1]
    assert adaptive["adaptive"] is True
    assert adaptive["uses_complete_trajectory_and_future_endpoint"] is True
    assert adaptive["causal_online_policy_validated"] is False
    assert adaptive["selected_interior_index_0based"] in (1, 2)
    assert metrics["online_adaptive_policy"].startswith("UNKNOWN")
    assert metrics["event_retention"].startswith("UNKNOWN")


@pytest.mark.parametrize("times", ([0.0, 1.0, 1.0, 3.0], [0.0, 2.0, 1.0, 3.0], [0.0, float("nan"), 2.0, 3.0]))
def test_invalid_times_fail_closed(times):
    with pytest.raises(AuditError):
        analyze_samples(_document(list(times)))


def test_empty_or_malformed_sample_sequence_fails_closed():
    doc = _document()
    doc["samples_by_support"]["support-a"] = []
    doc["sample_count_by_support"]["support-a"] = 0
    with pytest.raises(AuditError, match="SAMPLE_COUNT_OUT_OF_SCOPE"):
        analyze_samples(doc)


def test_material_node_correspondence_and_derived_depth_are_checked():
    changed = _document()
    changed["samples_by_support"]["support-a"][2]["material_coordinate"][1] += 0.01
    with pytest.raises(AuditError, match="MATERIAL_COORDINATE_ALIGNMENT_CHANGED"):
        analyze_samples(changed)
    changed = _document()
    changed["samples_by_support"]["support-a"][1]["z_m"][1] += 1.0
    with pytest.raises(AuditError, match="DEPTH_COORDINATE_RECONCILIATION_MISMATCH"):
        analyze_samples(changed)


def test_zero_reference_relative_error_is_explicit():
    result = _difference_metrics([0.0, 2.0], [1.0, 2.0])
    assert result["max_abs_error"] == 1.0
    assert result["zero_reference_nonzero_error_count"] == 1
    assert result["relative_error_status"] == "ZERO_REFERENCE_NONZERO_ERROR"


def _write_bundle(root: Path, payload: bytes = b'{"v":1}\n') -> tuple[str, dict[str, tuple[int, str]]]:
    root.mkdir()
    run = b'{"decision":"fixture"}\n'
    (root / "payload.json").write_bytes(payload)
    (root / "RUN_RESULT.json").write_bytes(run)
    members = {"payload.json": (len(payload), hashlib.sha256(payload).hexdigest()),
               "RUN_RESULT.json": (len(run), hashlib.sha256(run).hexdigest())}
    manifest = {"schema": "ARCANA_R6_TF2B_INT0_OUTPUT_MANIFEST_V1",
                "canonical_publication": False,
                "configuration_sha256": "fixture",
                "provider_identities": {},
                "files": {"payload.json": {"bytes": len(payload), "sha256": members["payload.json"][1]}},
                "RUN_RESULT.json": {"bytes": len(run), "sha256": members["RUN_RESULT.json"][1]}}
    manifest_bytes = (json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
    (root / "CANDIDATE_MANIFEST.json").write_bytes(manifest_bytes)
    return hashlib.sha256(manifest_bytes).hexdigest(), members


def test_snapshot_manifest_verifies_bytes_and_returns_the_authenticated_snapshot(scratch_path):
    root = scratch_path / "INT0B_TF2B_5_11_R4_20261013_04"
    digest, members = _write_bundle(root)
    docs, sizes, hashes, snapshots = load_verified_bundle(
        root, expected_manifest_sha256=digest, expected_members=members)
    assert docs["payload.json"] == {"v": 1}
    assert snapshots["payload.json"] == (root / "payload.json").read_bytes()
    assert sizes["payload.json"] == members["payload.json"][0]
    assert hashes["payload.json"] == members["payload.json"][1]


def test_altered_member_unlisted_file_and_manifest_digest_are_rejected(scratch_path):
    root = scratch_path / "INT0B_TF2B_5_11_R4_20261013_04"
    digest, members = _write_bundle(root)
    (root / "payload.json").write_bytes(b'{"v":2}\n')
    with pytest.raises(AuditError, match="MEMBER_INTEGRITY_MISMATCH"):
        load_verified_bundle(root, expected_manifest_sha256=digest, expected_members=members)
    (root / "payload.json").write_bytes(b'{"v":1}\n')
    (root / "extra.bin").write_bytes(b"extra")
    with pytest.raises(AuditError, match="CANDIDATE_DIRECTORY_MEMBERSHIP_MISMATCH"):
        load_verified_bundle(root, expected_manifest_sha256=digest, expected_members=members)
    (root / "extra.bin").unlink()
    with pytest.raises(AuditError, match="CANDIDATE_MANIFEST_SHA256_MISMATCH"):
        load_verified_bundle(root, expected_manifest_sha256="0"*64, expected_members=members)


def test_analysis_refuses_existing_or_overlapping_output(scratch_path):
    source = scratch_path / "source"
    source.mkdir()
    with pytest.raises(AuditError, match="OUTPUT_DIRECTORY_ALREADY_EXISTS"):
        run_audit(source, source)
    child = source / "child"
    with pytest.raises(AuditError, match="INPUT_OUTPUT_PATH_OVERLAP"):
        run_audit(source, child)
