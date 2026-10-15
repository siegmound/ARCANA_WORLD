from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState, pure_shear_thermal_step
from arcana_worldsim.r6 import int3_eng10k as eng
from r6_int3_eng10k import (
    CONFIG_SHA256, EXECUTION_DECISION, _diagnostic_summary,
    _validate_checkout_identity, _validate_execution_authorization, _write_bundle,
)
import r6_int3_eng10k_supervisor as supervisor
from r6_int3_eng10k_supervisor import _parse_stat, _proc_group_snapshot


SUPPORTS = ("R6G1D-R091-C029", "R6G1D-R091-C028")
SOURCE_COMPOSITE = "b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca"
PROVIDER_IDENTITIES = {
    "source_set": SOURCE_COMPOSITE,
    "kinematics_semantic": "5" * 64, "kinematics_artifact": "6" * 64,
    "mapping": "7" * 64, "vector_partition": "8" * 64,
    "thermal_field_package": "9" * 64, "support_binding_index": "a" * 64,
    "event_census": "b" * 64,
}


def _state(time_s: float = 0.0) -> ReducedState:
    n = 73
    material = NodeMaterial("CONTINENTAL_CRUST_REFERENCE", 3.0, 2800.0, 1000.0, 1e-6)
    mantle = NodeMaterial("LITHOSPHERIC_MANTLE_REFERENCE", 4.0, 3300.0, 1100.0, 0.0)
    materials = tuple(material if i < 26 else mantle for i in range(n))
    xi = tuple(i / (n - 1) for i in range(n))
    width, lithosphere, crust = 100_000.0, 80_000.0, 28_000.0
    return ReducedState(time_s=time_s, initial_width_m=width, width_m=width,
        initial_crust_m=crust, initial_lithosphere_m=lithosphere, crust_m=crust,
        lithosphere_m=lithosphere, beta=1.0, accumulated_strain=0.0,
        crust_fraction=crust / lithosphere, material_coordinate=xi,
        temperature_k=tuple(280.0 + i * 10.0 for i in range(n)), materials=materials,
        surface_temperature_k=280.0, base_temperature_k=1000.0)


def _synthetic_r4_bundle(path: Path) -> tuple[str, list[dict], list[dict]]:
    initial = [_state().payload(), _state().payload()]
    finals = []
    for row in initial:
        start = eng.state_from_payload(row)
        end, _ = pure_shear_thermal_step(start, duration_s=1000 * eng.SECONDS_PER_YEAR,
            extension_velocity_m_s=0.11467052868814648 / eng.SECONDS_PER_YEAR,
            maximum_kinematic_fraction_per_substep=0.0005)
        finals.append(end.payload())
    section = {"boundary_id": eng.R4_BOUNDARY_ID, "support_ids": list(SUPPORTS),
        "signed_candidate_Ux_m_per_year": 0.11467052868814648,
        "forcing_mode": "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER",
        "temperature_boundary_conditions": "EXISTING_TF1_COLUMN_CONTRACT_FIXED_SURFACE_AND_MODEL_BASE",
        "lateral_thermal_coupling": "NOT_MODELED_IN_REDUCED_1D_COLUMN_PAIR"}
    trajectory = {
        "source_code": {"commit": eng.R4_SOURCE_COMMIT,
                        "source_identity_sha256": SOURCE_COMPOSITE},
        "numerical_configuration": {"duration_years": 1000.0,
            "maximum_kinematic_fraction_per_substep": 0.0005,
            "kernel": "functional_development.pure_shear_thermal_step"},
        "b0_checkpoints": {"candidate": {"validation_status": "CANDIDATE_NONCANONICAL",
                                          "time_key": "209.999Ma"}},
        "b0_domain_states": {
            "initial": {"value": {"support_ids": list(SUPPORTS), "side_states": initial}},
            "candidate": {"value": {"support_ids": list(SUPPORTS), "side_states": finals}}},
        "b0_forcing_record": {"forcing_kind": "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER",
            "source_refs": [PROVIDER_IDENTITIES[key] for key in (
                "source_set", "kinematics_semantic", "kinematics_artifact", "mapping",
                "vector_partition", "thermal_field_package", "support_binding_index", "event_census")],
            "value": {"signed_Ux_m_per_year": 0.11467052868814648,
                      "frame": "T_F2B_SELECTED_SECTION_NORMAL_PLATE_5_TO_11",
                      "support_ids": list(SUPPORTS)}},
    }
    docs = {
        "CANDIDATE_CHECKPOINT.json": {"canonical_publication": False, "elapsed_years": 1000.0,
            "initial_states": initial, "candidate_states": finals},
        "CANDIDATE_TRAJECTORY.json": trajectory,
        "DIAGNOSTIC_NUMERICAL_SAMPLES.json": {}, "EDGE_AUDIT_MATRIX.json": {},
        "REPLAY_RESTART.json": {}, "SELECTED_SECTION_AND_PROFILES.json": section,
        "THERMAL_CONVERGENCE.json": {},
    }
    path.mkdir()
    files = {}
    for name, doc in docs.items():
        raw = eng.canonical_bytes(doc)
        (path / name).write_bytes(raw)
        files[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    result = {"selected_support_ids": list(SUPPORTS), "selected_boundary_id": eng.R4_BOUNDARY_ID,
        "checkpoint_commit": eng.R4_SOURCE_COMMIT, "duration_years": 1000.0,
        "resolution_factors": list(eng.RESOLUTION_FACTORS),
        "signed_Ux_m_per_year": 0.11467052868814648,
        "resolution_results": [{"maximum_kinematic_fraction_per_substep": 0.0005,
                                "final_states": finals}]}
    result_raw = eng.canonical_bytes(result)
    (path / "RUN_RESULT.json").write_bytes(result_raw)
    manifest = {"canonical_publication": False, "configuration_sha256": "1" * 64,
        "provider_identities": PROVIDER_IDENTITIES, "files": files,
        "RUN_RESULT.json": {"bytes": len(result_raw), "sha256": hashlib.sha256(result_raw).hexdigest()}}
    manifest_raw = eng.canonical_bytes(manifest)
    (path / "CANDIDATE_MANIFEST.json").write_bytes(manifest_raw)
    return hashlib.sha256(manifest_raw).hexdigest(), initial, finals


def test_r4_input_closure_authenticates_and_parses_identical_snapshots(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    digest, _, _ = _synthetic_r4_bundle(bundle)
    monkeypatch.setattr(eng, "R4_MANIFEST_SHA256", digest)
    result = eng.load_r4_continuation_bundle(bundle)
    assert result.manifest_sha256 == digest
    assert result.support_ids == SUPPORTS
    assert result.initial_states[0].time_s == 0.0
    assert result.checkpoint_states[0].time_s == 1000 * eng.SECONDS_PER_YEAR
    assert len(result.checkpoint_states[0].temperature_k) == 73


def test_r4_input_closure_rejects_tampered_member_even_when_json_parses(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    digest, _, _ = _synthetic_r4_bundle(bundle)
    monkeypatch.setattr(eng, "R4_MANIFEST_SHA256", digest)
    path = bundle / "CANDIDATE_CHECKPOINT.json"
    data = json.loads(path.read_text())
    data["elapsed_years"] = 1001.0
    path.write_text(json.dumps(data))
    with pytest.raises(eng.Eng10kContractError, match="MEMBER_IDENTITY_MISMATCH"):
        eng.load_r4_continuation_bundle(bundle)


def test_r4_input_closure_rejects_wrong_manifest_and_extra_file(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    digest, _, _ = _synthetic_r4_bundle(bundle)
    monkeypatch.setattr(eng, "R4_MANIFEST_SHA256", digest)
    (bundle / "unexpected.bin").write_bytes(b"extra")
    with pytest.raises(eng.Eng10kContractError, match="DIRECTORY_MEMBERSHIP"):
        eng.load_r4_continuation_bundle(bundle)


def test_r4_input_closure_rejects_source_ref_disagreement_with_manifest(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    _synthetic_r4_bundle(bundle)
    trajectory_path = bundle / "CANDIDATE_TRAJECTORY.json"
    trajectory = json.loads(trajectory_path.read_text())
    trajectory["b0_forcing_record"]["source_refs"][1] = "f" * 64
    trajectory_raw = eng.canonical_bytes(trajectory)
    trajectory_path.write_bytes(trajectory_raw)
    manifest_path = bundle / "CANDIDATE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][trajectory_path.name] = {
        "bytes": len(trajectory_raw), "sha256": hashlib.sha256(trajectory_raw).hexdigest()}
    manifest_raw = eng.canonical_bytes(manifest)
    manifest_path.write_bytes(manifest_raw)
    monkeypatch.setattr(eng, "R4_MANIFEST_SHA256", hashlib.sha256(manifest_raw).hexdigest())
    with pytest.raises(eng.Eng10kContractError, match="R4_SOURCE_IDENTITY_MISMATCH"):
        eng.load_r4_continuation_bundle(bundle)


def test_nonzero_time_continuation_preserves_accumulated_clock_and_reports_omissions():
    state = _state(1000 * eng.SECONDS_PER_YEAR)
    final, report = eng.advance_with_bounded_samples(state, support_id=SUPPORTS[0],
        duration_years=100.0, extension_velocity_m_per_year=0.11467052868814648,
        resolution_factor=0.0005, sample_interval_years=10.0)
    assert final.time_s > state.time_s
    assert abs(final.time_s - 1100 * eng.SECONDS_PER_YEAR) <= report["time_accumulation_roundoff_bound_s"]
    assert report["interpolation"] == "NONE"
    assert report["omitted_integration_observations"] >= 0
    assert report["samples"][0]["record_type"] == "INITIAL"
    assert report["samples"][-1]["record_type"] == "FINAL_COMPLETE_STATE"
    assert len(report["samples"]) <= eng.MAX_RETAINED_SAMPLES_PER_SUPPORT


def test_bounded_sampling_records_skipped_schedule_targets_without_fabricating_samples():
    final, report = eng.advance_with_bounded_samples(_state(), support_id=SUPPORTS[0],
        duration_years=25.0, extension_velocity_m_per_year=0.11467052868814648,
        resolution_factor=0.001, sample_interval_years=1.0)
    assert final.time_s > 0
    assert report["missed_schedule_targets"] >= 0
    assert report["retained_diagnostic_samples"] == len(report["samples"])
    assert report["integration_observations_including_initial"] == report["integration_substeps"] + 1


def test_run_result_diagnostic_summary_does_not_duplicate_sample_payload():
    diagnostic = {"samples": [{"time_s": 1.0}], "integration_substeps": 4,
                  "retained_diagnostic_samples": 1, "interpolation": "NONE"}
    summary = _diagnostic_summary(diagnostic)
    assert "samples" not in summary
    assert summary == {"integration_substeps": 4, "retained_diagnostic_samples": 1,
                       "interpolation": "NONE"}


def test_output_projection_fails_before_writing_artifact_members(tmp_path, monkeypatch):
    import r6_int3_eng10k as runner

    output = tmp_path / "candidate"
    output.mkdir()
    (output / "RUN_STARTED.json").write_bytes(b"{}\n")
    monkeypatch.setattr(runner, "MAX_PROJECTED_OUTPUT_BYTES", 1)
    with pytest.raises(eng.Eng10kContractError, match="OUTPUT_SIZE_EXCEEDS_PREFLIGHT_BOUNDS"):
        _write_bundle(output, {"payload.json": {"x": "y"}}, b"{}\n", {}, {})
    assert not (output / "payload.json").exists()
    assert not (output / "ARTIFACT_MANIFEST.json").exists()
    assert (output / "INCOMPLETE.json").exists()


def test_invalid_duration_and_resolution_fail_closed():
    for duration, factor in ((0.0, 0.0005), (-1.0, 0.0005), (1.0, 0.04)):
        with pytest.raises(eng.Eng10kContractError):
            eng.advance_with_bounded_samples(_state(), support_id=SUPPORTS[0],
                duration_years=duration, extension_velocity_m_per_year=0.1,
                resolution_factor=factor)


def test_direct_versus_restart_metrics_report_values_without_acceptance_tolerance():
    start = _state()
    direct, _ = eng.advance_with_bounded_samples(start, support_id=SUPPORTS[0],
        duration_years=100.0, extension_velocity_m_per_year=0.1,
        resolution_factor=0.0005)
    checkpoint, _ = eng.advance_with_bounded_samples(start, support_id=SUPPORTS[0],
        duration_years=40.0, extension_velocity_m_per_year=0.1,
        resolution_factor=0.0005)
    restarted, _ = eng.advance_with_bounded_samples(checkpoint, support_id=SUPPORTS[0],
        duration_years=60.0, extension_velocity_m_per_year=0.1,
        resolution_factor=0.0005)
    metrics = eng.compare_reduced_states(direct, restarted)
    assert metrics["scope"] == "ENGINEERING_PATH_COMPARISON_NO_SCIENTIFIC_THRESHOLD"
    assert metrics["temperature_k"]["node_count"] == 73
    assert "absolute_difference" in metrics["width_m"]
    assert "relative_difference" in metrics["width_m"]
    assert metrics["temperature_k"]["maximum_absolute_difference"] >= 0.0


def test_r4_manifest_identity_is_a_fixed_external_anchor():
    assert eng.R4_MANIFEST_SHA256 == "191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236"


def test_current_head_bound_source_set_can_differ_while_provider_payloads_match():
    current = dict(PROVIDER_IDENTITIES, source_set="c" * 64)
    assert current["source_set"] != PROVIDER_IDENTITIES["source_set"]
    assert eng.provider_component_bindings_match(current, PROVIDER_IDENTITIES)
    current["thermal_field_package"] = "d" * 64
    assert not eng.provider_component_bindings_match(current, PROVIDER_IDENTITIES)


def test_immutable_case_configuration_digest_and_output_projection():
    raw = Path("configs/r6_int3_eng10k/engineering_case.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CONFIG_SHA256
    assert eng.MAX_PROJECTED_OUTPUT_BYTES < 512 * 1024 * 1024
    assert eng.MAX_RETAINED_SAMPLES_PER_SUPPORT == 1002


def test_execution_authorization_is_bound_to_source_config_paths_and_budgets():
    from r6_int3_eng10k import _validate_execution_authorization
    args = {"decision": EXECUTION_DECISION, "source_head": "a" * 40,
        "configuration_sha256": CONFIG_SHA256,
        "output_relative": "R6/INT3_ENG10K/run/candidate",
        "evidence_root_absolute": "F:/ARCANA_WORLD_EVIDENCE",
        "output_absolute": "F:/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K/run/candidate",
        "supervision_relative": "R6/INT3_ENG10K/run/supervision",
        "supervision_absolute": "F:/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K/run/supervision",
        "one_attempt_only": True, "noncanonical": True,
        "limits": {"wall_seconds": 900, "process_group_rss_bytes": 2_147_483_648,
                   "cumulative_output_bytes": 536_870_912}}
    _validate_execution_authorization(args, source_head="a" * 40,
        configuration_sha256=CONFIG_SHA256, evidence_root_absolute=args["evidence_root_absolute"],
        output_relative=Path(args["output_relative"]),
        output_absolute=args["output_absolute"],
        supervision_relative=Path(args["supervision_relative"]),
        supervision_absolute=args["supervision_absolute"])
    args["limits"]["wall_seconds"] = 901
    with pytest.raises(eng.Eng10kContractError, match="AUTHORIZATION_MISMATCH"):
        _validate_execution_authorization(args, source_head="a" * 40,
            configuration_sha256=CONFIG_SHA256, evidence_root_absolute=args["evidence_root_absolute"],
            output_relative=Path(args["output_relative"]), output_absolute=args["output_absolute"],
            supervision_relative=Path(args["supervision_relative"]),
            supervision_absolute=args["supervision_absolute"])


def test_evidence_root_and_destinations_are_external_existing_and_read_only_preflight(tmp_path):
    from arcana_worldsim.r6.int3_eng10k import resolve_evidence_destinations

    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    output_rel = Path("R6/INT3_ENG10K/attempt-01/candidate")
    supervision_rel = Path("R6/INT3_ENG10K/attempt-01/supervision")
    resolved_root, output, supervision = resolve_evidence_destinations(
        root, output_rel, supervision_rel, repo_root=checkout)
    assert resolved_root == root.absolute()
    assert output == root / output_rel
    assert supervision == root / supervision_rel
    assert root.is_dir()
    assert not (root / "R6").exists()


def test_evidence_root_missing_or_inside_checkout_fails_closed(tmp_path):
    from arcana_worldsim.r6.int3_eng10k import resolve_evidence_destinations

    missing = tmp_path / "ARCANA_WORLD_EVIDENCE"
    with pytest.raises(eng.Eng10kContractError, match="EVIDENCE_ROOT_UNAVAILABLE"):
        resolve_evidence_destinations(missing, "R6/INT3_ENG10K/a/candidate",
            "R6/INT3_ENG10K/a/supervision", repo_root=eng.Path(__file__).resolve().parents[1])
    fake_checkout = tmp_path / "checkout"
    fake_checkout.mkdir()
    checkout_root = fake_checkout / "ARCANA_WORLD_EVIDENCE"
    checkout_root.mkdir()
    try:
        with pytest.raises(eng.Eng10kContractError):
            resolve_evidence_destinations(checkout_root, "R6/INT3_ENG10K/a/candidate",
                "R6/INT3_ENG10K/a/supervision", repo_root=fake_checkout)
    finally:
        checkout_root.rmdir()


@pytest.mark.parametrize("bad_path", [
    "R6/INT3_ENG10K/../escape/candidate",
    "R6/INT3_ENG10K/a/../candidate",
    "/tmp/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K/a/candidate",
    "C:/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K/a/candidate",
])
def test_evidence_destination_rejects_traversal_and_absolute_paths(tmp_path, bad_path):
    from arcana_worldsim.r6.int3_eng10k import resolve_evidence_destinations

    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    with pytest.raises(eng.Eng10kContractError):
        resolve_evidence_destinations(root, bad_path, "R6/INT3_ENG10K/a/supervision",
            repo_root=checkout)


def test_evidence_destination_rejects_symlink_and_attempt_collision(tmp_path):
    from arcana_worldsim.r6.int3_eng10k import resolve_evidence_destinations

    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    attempt = root / "R6" / "INT3_ENG10K" / "attempt-01"
    attempt.mkdir(parents=True)
    (attempt / "preexisting.txt").write_text("preserve")
    with pytest.raises(eng.Eng10kContractError, match="ATTEMPT_DIRECTORY_COLLISION"):
        resolve_evidence_destinations(root, "R6/INT3_ENG10K/attempt-01/candidate",
            "R6/INT3_ENG10K/attempt-01/supervision", repo_root=checkout)
    link = root / "R6" / "INT3_ENG10K" / "linked-attempt"
    try:
        link.symlink_to(attempt, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Windows policy does not permit creating symlinks in this test environment")
    with pytest.raises(eng.Eng10kContractError, match="SYMLINK|JUNCTION|LINK"):
        resolve_evidence_destinations(root, "R6/INT3_ENG10K/linked-attempt/candidate",
            "R6/INT3_ENG10K/linked-attempt/supervision", repo_root=checkout)


def test_evidence_targets_cannot_overlap_world_history_or_r4_bundle(tmp_path):
    from arcana_worldsim.r6.int3_eng10k import resolve_evidence_destinations

    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    history = root / "R6" / "INT3_ENG10K" / "attempt"
    with pytest.raises(eng.Eng10kContractError, match="WORLD_HISTORY"):
        resolve_evidence_destinations(root, "R6/INT3_ENG10K/attempt/candidate",
            "R6/INT3_ENG10K/attempt/supervision", repo_root=checkout,
            world_history_roots=(history,))
    r4 = root / "R6" / "INT3_ENG10K" / "attempt" / "input"
    r4.mkdir(parents=True)
    with pytest.raises(eng.Eng10kContractError, match="R4_INPUT"):
        resolve_evidence_destinations(root, "R6/INT3_ENG10K/attempt/candidate",
            "R6/INT3_ENG10K/attempt/supervision", repo_root=checkout,
            r4_bundle=r4)


def test_incomplete_output_marker_target_is_unsealed_and_same_attempt(tmp_path):
    from arcana_worldsim.r6.int3_eng10k import resolve_incomplete_evidence_output

    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    attempt = root / "R6" / "INT3_ENG10K" / "attempt"
    output = attempt / "candidate"
    supervision = attempt / "supervision"
    output.mkdir(parents=True)
    supervision.mkdir()
    (output / "RUN_STARTED.json").write_text("{}")
    (supervision / "child.stdout").write_bytes(b"")
    (supervision / "child.stderr").write_bytes(b"")
    assert resolve_incomplete_evidence_output(root, "R6/INT3_ENG10K/attempt/candidate",
        "R6/INT3_ENG10K/attempt/supervision", repo_root=checkout) == output.absolute()
    (output / "ARTIFACT_MANIFEST.json").write_text("{}")
    with pytest.raises(eng.Eng10kContractError, match="ALREADY_SEALED"):
        resolve_incomplete_evidence_output(root, "R6/INT3_ENG10K/attempt/candidate",
            "R6/INT3_ENG10K/attempt/supervision", repo_root=checkout)


def test_checkout_branch_and_exact_head_are_both_required():
    _validate_checkout_identity("r6/si1-bandwidth-f2av", "a" * 40, "a" * 40)
    with pytest.raises(eng.Eng10kContractError, match="BRANCH_MISMATCH"):
        _validate_checkout_identity("detached", "a" * 40, "a" * 40)
    with pytest.raises(eng.Eng10kContractError, match="HEAD_EXPECTATION"):
        _validate_checkout_identity("r6/si1-bandwidth-f2av", "a" * 40, "b" * 40)
    with pytest.raises(eng.Eng10kContractError, match="HEAD_EXPECTATION"):
        _validate_checkout_identity("r6/si1-bandwidth-f2av", "a" * 40, None)


def test_execution_contract_is_pinned_and_keeps_execution_disabled():
    from r6_int3_eng10k import _verify_execution_contract

    contract = _verify_execution_contract()
    assert contract["execution_authorized"] is False
    assert contract["canonical_publication_authorized"] is False
    assert contract["fair_evidence_root"] == "/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE"


def test_supervisor_command_is_bound_to_runtime_root_and_attempt_paths(tmp_path):
    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    bundle = tmp_path / "authenticated-r4"
    bundle.mkdir()
    authorization = tmp_path / "authorization.json"
    authorization.write_text("{}")
    out = Path("R6/INT3_ENG10K/attempt/candidate")
    sup = Path("R6/INT3_ENG10K/attempt/supervision")
    expected_head = "a" * 40
    cmd = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts/r6_int3_eng10k.py"),
        "--mode", "execute", "--evidence-root", str(root.absolute()),
        "--output-relative", out.as_posix(), "--supervision-relative", sup.as_posix(),
        "--r4-bundle", str(bundle.absolute()), "--expected-head", expected_head,
        "--authorization-json", str(authorization.absolute())]
    supervisor._expected_child_command(cmd, root=root.absolute(), output_relative=out,
        supervision_relative=sup, r4_bundle=bundle, expected_head=expected_head,
        authorization_json=authorization)
    cmd[5] = str(tmp_path / "other-root")
    with pytest.raises(supervisor.SupervisionError, match="EXACT_BOUND"):
        supervisor._expected_child_command(cmd, root=root.absolute(), output_relative=out,
            supervision_relative=sup, r4_bundle=bundle, expected_head=expected_head,
            authorization_json=authorization)


def test_linux_proc_stat_parser_handles_parentheses_in_process_name():
    fields = ["S", "1", "77", "77"] + ["0"] * 15 + ["1234"]
    assert _parse_stat(f"42 (python (worker)) {' '.join(fields)}") == ("S", 1, 77, 1234)


def test_linux_proc_group_snapshot_sums_only_requested_group(tmp_path):
    for pid, group, rss in (("10", "10", 100), ("11", "10", 200), ("12", "99", 900)):
        proc = tmp_path / pid
        proc.mkdir()
        fields = ["S", "1", group, group] + ["0"] * 15 + [pid]
        (proc / "stat").write_text(f"{pid} (python {pid}) {' '.join(fields)}")
        (proc / "status").write_text(f"Name:\tpython\nVmRSS:\t{rss} kB\n")
    assert _proc_group_snapshot(tmp_path, 10) == (300 * 1024, [10, 11])


@pytest.mark.parametrize("state", ["Z", "X", "x"])
def test_linux_proc_group_snapshot_ignores_terminal_process_without_vmrss(tmp_path, state):
    proc = tmp_path / "10"
    proc.mkdir()
    fields = [state, "1", "10", "10"] + ["0"] * 15 + ["101"]
    (proc / "stat").write_text(f"10 (python (zombie)) {' '.join(fields)}")
    (proc / "status").write_text("Name:\tpython\n")
    assert _proc_group_snapshot(tmp_path, 10) == (0, [])


def test_linux_proc_stat_parser_rejects_invalid_state():
    fields = ["?", "1", "77", "77"] + ["0"] * 15 + ["1234"]
    with pytest.raises(supervisor.SupervisionError, match="PROC_STAT_STATE_INVALID"):
        _parse_stat(f"42 (python) {' '.join(fields)}")


@pytest.mark.parametrize("status", ["Name:\tpython\n", "Name:\tpython\nVmRSS:\tbad kB\n"])
def test_linux_proc_group_snapshot_fails_closed_for_live_unverifiable_rss(tmp_path, status):
    proc = tmp_path / "10"
    proc.mkdir()
    fields = ["S", "1", "10", "10"] + ["0"] * 15 + ["101"]
    (proc / "stat").write_text(f"10 (python) {' '.join(fields)}")
    (proc / "status").write_text(status)
    with pytest.raises(supervisor.SupervisionError, match="PROC_RESOURCE_SNAPSHOT_UNVERIFIABLE:10"):
        _proc_group_snapshot(tmp_path, 10)


def test_linux_proc_group_snapshot_skips_pid_that_disappears_mid_read(tmp_path, monkeypatch):
    proc = tmp_path / "10"
    proc.mkdir()
    fields = ["S", "1", "10", "10"] + ["0"] * 15 + ["101"]
    (proc / "stat").write_text(f"10 (python) {' '.join(fields)}")
    (proc / "status").write_text("Name:\tpython\nVmRSS:\t100 kB\n")
    original = Path.read_text
    reads = 0

    def disappear_after_first_stat(path, *args, **kwargs):
        nonlocal reads
        if path == proc / "stat":
            reads += 1
            if reads == 2:
                raise FileNotFoundError(str(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", disappear_after_first_stat)
    assert _proc_group_snapshot(tmp_path, 10) == (0, [])


def test_linux_proc_group_snapshot_fails_closed_on_pid_reuse(tmp_path, monkeypatch):
    proc = tmp_path / "10"
    proc.mkdir()
    fields = ["S", "1", "10", "10"] + ["0"] * 15 + ["101"]
    changed = ["S", "1", "10", "10"] + ["0"] * 15 + ["999"]
    (proc / "stat").write_text(f"10 (python) {' '.join(fields)}")
    (proc / "status").write_text("Name:\tpython\nVmRSS:\t100 kB\n")
    original = Path.read_text
    reads = 0

    def reuse_after_status(path, *args, **kwargs):
        nonlocal reads
        if path == proc / "stat":
            reads += 1
            if reads == 2:
                return f"10 (reused) {' '.join(changed)}"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", reuse_after_status)
    with pytest.raises(supervisor.SupervisionError, match="PROC_PID_IDENTITY_CHANGED:10"):
        _proc_group_snapshot(tmp_path, 10)


def test_linux_proc_group_snapshot_keeps_live_descendant_after_zombie_leader(tmp_path):
    for pid, state, ppid, rss in ((10, "Z", 1, None), (11, "S", 1, 250)):
        proc = tmp_path / str(pid)
        proc.mkdir()
        fields = [state, str(ppid), "10", "10"] + ["0"] * 15 + [str(pid * 10)]
        (proc / "stat").write_text(f"{pid} (python) {' '.join(fields)}")
        status = "Name:\tpython\n" if rss is None else f"Name:\tpython\nVmRSS:\t{rss} kB\n"
        (proc / "status").write_text(status)
    assert _proc_group_snapshot(tmp_path, 10, expected_leader_start_ticks=100) == (250 * 1024, [11])


def test_natural_exit_requires_bounded_repeated_empty_group_confirmation():
    complete, since = supervisor._update_empty_group_confirmation(0, [], 10.0, None)
    assert not complete and since == 10.0
    complete, since = supervisor._update_empty_group_confirmation(0, [], 10.0 +
        supervisor.NATURAL_EXIT_CONFIRMATION_S - 0.001, since)
    assert not complete and since == 10.0
    complete, since = supervisor._update_empty_group_confirmation(0, [], 10.0 +
        supervisor.NATURAL_EXIT_CONFIRMATION_S, since)
    assert complete and since == 10.0

    # A live member restarts the interval; a still-running leader cannot confirm it.
    complete, since = supervisor._update_empty_group_confirmation(0, [123], 11.0, since)
    assert not complete and since is None
    complete, since = supervisor._update_empty_group_confirmation(None, [], 12.0, since)
    assert not complete and since is None


def test_supervisor_termination_uses_term_then_kill_when_group_disappears(monkeypatch):
    calls = []

    class Process:
        returncode = None
        def poll(self):
            return self.returncode
        def wait(self):
            self.returncode = -15
            return self.returncode

    def fake_killpg(pgid, signal_number):
        calls.append((pgid, signal_number))
        if signal_number == 0:
            raise ProcessLookupError

    monkeypatch.setattr(supervisor.os, "killpg", fake_killpg, raising=False)
    monkeypatch.setattr(supervisor.signal, "SIGKILL", 9, raising=False)
    process = Process()
    supervisor._terminate_group(44, process)
    assert calls == [(44, supervisor.signal.SIGTERM), (44, 0), (44, supervisor.signal.SIGKILL)]
    assert process.returncode == -15


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="requires Linux /proc and process groups")
def test_linux_supervise_runs_only_a_synthetic_child_and_records_natural_exit(tmp_path, monkeypatch):
    """Exercise the real supervisor loop without invoking the ENG10K runner."""
    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    r4 = tmp_path / "r4-input"
    r4.mkdir()
    authorization = tmp_path / "invalid-authorization.json"
    authorization.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(supervisor, "ROOT", checkout)
    command = [sys.executable, "-c", "import time; print('SYNTHETIC_ONLY', flush=True); time.sleep(0.25)"]

    def allow_only_this_fixture(actual, **_kwargs):
        assert actual == command
        assert "r6_int3_eng10k" not in " ".join(actual)
        return actual

    monkeypatch.setattr(supervisor, "_expected_child_command", allow_only_this_fixture)
    result = supervisor.supervise(
        command, evidence_root=root,
        output_relative=Path("R6/INT3_ENG10K/probe-natural/candidate"),
        supervision_relative=Path("R6/INT3_ENG10K/probe-natural/supervision"),
        r4_bundle=r4, expected_head="f072c46c77ee73e45b4ad5d7230451b19f35a692",
        authorization_json=authorization,
    )

    assert result["stop_reason"] == "NATURAL_EXIT"
    assert result["natural_exit_code"] == 0
    assert result["root_pid"] > 0
    assert result["sample_count"] >= 1
    assert result["peak_sampled_process_group_rss_bytes"] > 0
    streams = Path(result["supervision_absolute"])
    assert (streams / "child.stdout").read_text(encoding="utf-8").strip() == "SYNTHETIC_ONLY"
    assert json.loads((streams / "SUPERVISION.json").read_text(encoding="utf-8")) == result
    assert not Path(result["output_absolute"]).exists()


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="requires Linux /proc and process groups")
def test_linux_supervise_wall_timeout_terminates_synthetic_process_group(tmp_path, monkeypatch):
    """Exercise sampled timeout and group termination using a harmless child tree."""
    import time

    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    r4 = tmp_path / "r4-input"
    r4.mkdir()
    authorization = tmp_path / "invalid-authorization.json"
    authorization.write_text("{}", encoding="utf-8")
    marker = tmp_path / "descendant-survived.txt"
    monkeypatch.setattr(supervisor, "ROOT", checkout)
    monkeypatch.setattr(supervisor, "WALL_LIMIT_S", 0.35)
    monkeypatch.setattr(supervisor, "POLL_INTERVAL_S", 0.025)
    monkeypatch.setattr(supervisor, "TERM_GRACE_S", 0.2)
    monkeypatch.setattr(supervisor, "RSS_LIMIT_BYTES", 1_000_000_000)
    monkeypatch.setattr(supervisor, "OUTPUT_LIMIT_BYTES", 1_000_000)
    descendant = (
        "import pathlib,time; time.sleep(30); "
        f"pathlib.Path({str(marker)!r}).write_text('SURVIVED')"
    )
    command = [sys.executable, "-c",
        "import subprocess,sys,time; "
        f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}]); "
        "print('DESCENDANT_PID='+str(p.pid), flush=True); time.sleep(30)"]

    def allow_only_this_fixture(actual, **_kwargs):
        assert actual == command
        assert "r6_int3_eng10k" not in " ".join(actual)
        return actual

    monkeypatch.setattr(supervisor, "_expected_child_command", allow_only_this_fixture)
    result = supervisor.supervise(
        command, evidence_root=root,
        output_relative=Path("R6/INT3_ENG10K/probe-timeout/candidate"),
        supervision_relative=Path("R6/INT3_ENG10K/probe-timeout/supervision"),
        r4_bundle=r4, expected_head="f072c46c77ee73e45b4ad5d7230451b19f35a692",
        authorization_json=authorization,
    )

    assert result["stop_reason"] == "WALL_TIME_LIMIT"
    assert result["natural_exit_code"] not in (None, 0)
    assert result["sample_count"] >= 1
    assert result["peak_sampled_process_group_rss_bytes"] > 0
    stdout = (Path(result["supervision_absolute"]) / "child.stdout").read_text(encoding="utf-8")
    assert stdout.startswith("DESCENDANT_PID=")
    descendant_pid = int(stdout.partition("=")[2].strip())
    proc_entry = Path("/proc") / str(descendant_pid)
    deadline = time.monotonic() + 2.0
    while proc_entry.exists() and time.monotonic() < deadline:
        stat = (proc_entry / "stat").read_text(encoding="utf-8", errors="replace")
        close = stat.rfind(")")
        state = stat[close + 1:].strip().split()[0] if close >= 0 else "?"
        if state == "Z":
            break
        time.sleep(0.02)
    assert not proc_entry.exists() or state == "Z"
    time.sleep(0.1)
    assert not marker.exists()
    assert not Path(result["output_absolute"]).exists()


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="requires Linux /proc and process groups")
def test_linux_supervise_waits_for_live_descendant_after_leader_exits(tmp_path, monkeypatch):
    """A ready child in the same group prevents premature leader natural-exit."""
    root = tmp_path / "ARCANA_WORLD_EVIDENCE"
    root.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    r4 = tmp_path / "r4-input"
    r4.mkdir()
    authorization = tmp_path / "invalid-authorization.json"
    authorization.write_text("{}", encoding="utf-8")
    finished = tmp_path / "descendant-finished.txt"
    ready = tmp_path / "descendant-ready.txt"
    monkeypatch.setattr(supervisor, "ROOT", checkout)
    descendant = _live_descendant_fixture_source(ready, finished)
    command = [sys.executable, "-c",
        "import subprocess,sys; "
        f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}],stdout=subprocess.PIPE,text=True); "
        "line=p.stdout.readline(); "
        "print('CHILD_READY='+line.strip(),flush=True) if line.strip() == 'READY' else sys.exit(91)"]

    def allow_only_this_fixture(actual, **_kwargs):
        assert actual == command
        assert "r6_int3_eng10k" not in " ".join(actual)
        return actual

    monkeypatch.setattr(supervisor, "_expected_child_command", allow_only_this_fixture)
    result = supervisor.supervise(
        command, evidence_root=root,
        output_relative=Path("R6/INT3_ENG10K/probe-descendant/candidate"),
        supervision_relative=Path("R6/INT3_ENG10K/probe-descendant/supervision"),
        r4_bundle=r4, expected_head="f072c46c77ee73e45b4ad5d7230451b19f35a692",
        authorization_json=authorization,
    )
    assert result["stop_reason"] == "NATURAL_EXIT"
    assert result["natural_exit_code"] == 0
    assert result["elapsed_seconds"] >= 0.35
    child_pid, child_pgrp = map(int, ready.read_text(encoding="utf-8").split())
    assert child_pid > 0 and child_pgrp == result["process_group_id"]
    assert finished.read_text(encoding="utf-8").split() == [str(child_pid), str(child_pgrp)]
    assert f"CHILD_READY={child_pid} {child_pgrp}" in (
        Path(result["supervision_absolute"]) / "child.stdout").read_text(encoding="utf-8")
    assert not Path(result["output_absolute"]).exists()


def _live_descendant_fixture_source(ready: Path, finished: Path) -> str:
    """Build child-only Python source; PID and process-group calls run in child."""
    return (
        "import os,pathlib,time; "
        f"pathlib.Path({str(ready)!r}).write_text(f'{{os.getpid()}} {{os.getpgrp()}}'); "
        "print('READY',flush=True); time.sleep(0.45); "
        f"pathlib.Path({str(finished)!r}).write_text(f'{{os.getpid()}} {{os.getpgrp()}}')"
    )


def test_live_descendant_fixture_source_is_valid_without_running_supervisor(tmp_path):
    ready = tmp_path / "ready.txt"
    finished = tmp_path / "finished.txt"
    source = _live_descendant_fixture_source(ready, finished)

    assert source.count("os.getpid()") == 2
    assert source.count("os.getpgrp()") == 2
    assert "import os" in source
    compile(source, "<live-descendant-fixture>", "exec")
