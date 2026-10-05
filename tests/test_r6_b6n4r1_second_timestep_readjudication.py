from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import r6_b6n4r1_second_timestep_readjudication as runner
from scripts.r6_b6n4r1_second_timestep_readjudication import (
    build_decision,
    evaluate_dependency_closure,
    require_external_output,
    select_nearest_positive_limiter,
    verify_source_gate,
)


DEVELOPMENT_HEAD = "d3128fca0f6bd812298544768dbac0ef74dcca75"


def _git_fixture(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    for key in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                "GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):
        env.pop(key, None)
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True,
        text=True, encoding="utf-8", env=env,
    )
    return result.stdout.strip()


def _clean_test_git_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                "GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE"):
        monkeypatch.delenv(key, raising=False)


def _source_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    _clean_test_git_environment(monkeypatch)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_fixture(repo, "init", "--initial-branch", runner.EXPECTED_BRANCH)
    _git_fixture(repo, "config", "user.name", "ARCANA test")
    _git_fixture(repo, "config", "user.email", "arcana-test@example.invalid")
    (repo / "tracked.txt").write_text("qualified source\n", encoding="utf-8")
    _git_fixture(repo, "add", "tracked.txt")
    _git_fixture(repo, "commit", "-m", "qualification fixture")
    return repo, _git_fixture(repo, "rev-parse", "HEAD")


def _dep(identifier: str, **changes):
    row = {
        "id": identifier,
        "scope_role": "REQUIRED_FOR_REQUESTED_OUTPUT",
        "authority_status": "AUTHORIZED",
        "impact_bound_status": "BOUNDED",
        "dependency_status": "CLOSED",
    }
    row.update(changes)
    return row


def test_dependency_closure_is_deterministic_and_unknown_impact_blocks() -> None:
    rows = [
        _dep("bounded", positive_validity_years=8214.0),
        _dep("unknown-event", impact_bound_status="UNKNOWN", dependency_status="NOT_PROVEN"),
    ]
    first = evaluate_dependency_closure(rows, 8214.0)
    second = evaluate_dependency_closure(list(reversed(rows)), 8214.0)
    assert first == second
    assert first["status"] == "BLOCKED_RELEVANT_AUTHORITY_UNRESOLVED"
    assert first["blocking_dependencies"] == [
        {"dependency": "unknown-event", "reason": "IMPACT_BOUND_UNRESOLVED"}
    ]
    assert first["SECOND_DT_SELECTED"] is False
    assert first["dt2_years"] is None


def test_not_applicable_mechanics_does_not_block_requested_scope() -> None:
    mechanics = _dep(
        "MECHANICS_REQUIREMENT",
        scope_role="NOT_APPLICABLE_TO_REQUESTED_OUTPUT",
        authority_status="NOT_REQUIRED",
        impact_bound_status="NOT_APPLICABLE",
    )
    limiter = [{"horizon_id": "model-cap", "delta_time_years": 10.0, "authorized": True}]
    result = evaluate_dependency_closure([mechanics], 10.0, limiter)
    assert result["status"] == "AUTHORIZED_POSITIVE_PROPAGATION"
    assert result["positive_propagation_established"] is True
    assert result["nearest_authorized_limiter"]["horizon_id"] == "model-cap"
    assert result["SECOND_DT_SELECTED"] is False
    assert result["T2_CREATED"] is False


def test_authority_block_cannot_be_waived_by_small_or_bounded_impact() -> None:
    rift = _dep("NEXT_RIFT_PROCESS_EVOLUTION", authority_status="NOT_AUTHORIZED")
    result = evaluate_dependency_closure([rift], 8214.0)
    assert result["blocking_dependencies"] == [
        {"dependency": "NEXT_RIFT_PROCESS_EVOLUTION", "reason": "AUTHORITY_NOT_AUTHORIZED"}
    ]


def test_source_provenance_is_distinct_from_successor_model_authority() -> None:
    source = _dep(
        "SOURCE_TEMPORAL_VALIDITY",
        scope_role="SOURCE_PROVENANCE_NOT_EXTENDED",
        authority_status="UNKNOWN",
        impact_bound_status="UNKNOWN",
    )
    successor = _dep("B6N2_SUCCESSOR_MODEL", positive_validity_years=8214.0)
    limiter = [{"horizon_id": "B6N3A_MODEL_SCOPE_CAP", "delta_time_years": 8214.0, "authorized": True}]
    result = evaluate_dependency_closure([source, successor], 8214.0, limiter)
    assert result["status"] == "AUTHORIZED_POSITIVE_PROPAGATION"
    assert result["SECOND_DT_SELECTED"] is False


def test_unknown_is_not_relabelled_absent_and_isolation_must_be_explicit() -> None:
    unknown = _dep(
        "PLATE_INTERFACE_EVENT_PREDICATES",
        impact_bound_status="UNKNOWN",
        dependency_status="NOT_PROVEN",
        event_occurrence="UNKNOWN",
    )
    result = evaluate_dependency_closure([unknown], 8214.0)
    assert unknown["event_occurrence"] == "UNKNOWN"
    assert result["status"] == "BLOCKED_RELEVANT_AUTHORITY_UNRESOLVED"
    assert not result["positive_propagation_established"]


def test_unproven_dependency_is_not_treated_as_isolated_scope() -> None:
    candidate = _dep("topology-event", impact_bound_status="BOUNDED",
                     dependency_status="NOT_PROVEN")
    result = evaluate_dependency_closure([candidate], 8214.0)
    assert result["blocking_dependencies"] == [
        {"dependency": "topology-event", "reason": "DEPENDENCY_CLOSURE_NOT_PROVEN"}
    ]


def test_nearest_limiter_selection_is_deterministic_and_requires_positive_authority() -> None:
    candidates = [
        {"horizon_id": "later", "delta_time_years": 12.0, "authorized": True},
        {"horizon_id": "ignored-unknown", "delta_time_years": 2.0, "authorized": False},
        {"horizon_id": "earlier", "delta_time_years": 4.0, "authorized": True},
        {"horizon_id": "zero", "delta_time_years": 0.0, "authorized": True},
    ]
    assert select_nearest_positive_limiter(candidates) == select_nearest_positive_limiter(list(reversed(candidates)))
    assert select_nearest_positive_limiter(candidates)["horizon_id"] == "earlier"
    assert select_nearest_positive_limiter([]) is None


def test_nonpositive_model_scope_limit_fails_closed() -> None:
    with pytest.raises(ValueError, match="positive duration"):
        evaluate_dependency_closure([], 0.0)


def test_current_closure_preserves_the_four_global_blockers() -> None:
    dependencies = [
        _dep("GENERIC_TOPOLOGY_EVENT_COVERAGE", impact_bound_status="UNKNOWN",
             dependency_status="NOT_PROVEN", event_occurrence="UNKNOWN"),
        _dep("JUNCTION_CONSISTENCY", scope_role="RELEVANT_NON_LIMITING_FOR_REQUESTED_OUTPUT",
             impact_bound_status="UNKNOWN", dependency_status="NOT_PROVEN", event_occurrence=None),
        _dep("MECHANICS_REQUIREMENT", scope_role="NOT_APPLICABLE_TO_REQUESTED_OUTPUT",
             authority_status="NOT_REQUIRED", impact_bound_status="NOT_APPLICABLE"),
        _dep("NEXT_RIFT_PROCESS_EVOLUTION", authority_status="NOT_AUTHORIZED",
             impact_bound_status="UNKNOWN", dependency_status="NOT_PROVEN", event_occurrence="UNKNOWN"),
        _dep("PLATE_INTERFACE_EVENT_PREDICATES", impact_bound_status="UNKNOWN",
             dependency_status="NOT_PROVEN", event_occurrence="UNKNOWN"),
        _dep("SOURCE_TEMPORAL_VALIDITY", scope_role="SOURCE_PROVENANCE_NOT_EXTENDED",
             authority_status="UNKNOWN", impact_bound_status="UNKNOWN", event_occurrence=None),
        _dep("SUPPORT_MEMBERSHIP_VALIDITY", impact_bound_status="UNKNOWN",
             dependency_status="NOT_PROVEN", event_occurrence=None),
        _dep("SUCCESSOR_MODEL_SCOPE_REVALIDATION",
             scope_role="AUTHORIZED_FINITE_UPPER_BOUND_CANDIDATE",
             positive_validity_years=8214.051909111062),
        _dep("ASYNC_DOMAIN_VALIDITY", scope_role="NOT_APPLICABLE_TO_TECTONIC_KINEMATIC_OUTPUT",
             authority_status="NOT_REQUIRED", impact_bound_status="NOT_APPLICABLE"),
        _dep("RIGID_ROTATION_NUMERICAL_STABILITY", scope_role="NOT_APPLICABLE_NO_GOVERNED_LIMIT",
             authority_status="NOT_REQUIRED", impact_bound_status="NOT_APPLICABLE"),
    ]
    result = evaluate_dependency_closure(dependencies, 8214.051909111062)
    assert result["status"] == "BLOCKED_RELEVANT_AUTHORITY_UNRESOLVED"
    assert result["blocking_dependencies"] == [
        {"dependency": "GENERIC_TOPOLOGY_EVENT_COVERAGE", "reason": "IMPACT_BOUND_UNRESOLVED"},
        {"dependency": "NEXT_RIFT_PROCESS_EVOLUTION", "reason": "AUTHORITY_NOT_AUTHORIZED"},
        {"dependency": "PLATE_INTERFACE_EVENT_PREDICATES", "reason": "IMPACT_BOUND_UNRESOLVED"},
        {"dependency": "SUPPORT_MEMBERSHIP_VALIDITY", "reason": "IMPACT_BOUND_UNRESOLVED"},
    ]
    assert dependencies[0]["event_occurrence"] == "UNKNOWN"
    assert result["positive_propagation_established"] is False
    assert result["nearest_authorized_limiter"] is None
    assert result["SECOND_DT_SELECTED"] is False
    assert result["dt2_years"] is None
    assert result["target_age_ma"] is None
    assert result["T2_CREATED"] is False


def test_source_gate_has_no_hard_coded_development_head() -> None:
    assert not hasattr(runner, "EXPECTED_HEAD")
    assert DEVELOPMENT_HEAD not in Path(runner.__file__).read_text(encoding="utf-8")


def test_source_gate_requires_and_records_matching_explicit_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, head = _source_repo(tmp_path, monkeypatch)
    result = verify_source_gate(repo, head)
    assert result == {
        "branch": runner.EXPECTED_BRANCH,
        "qualified_source_commit": head,
        "observed_head": head,
        "worktree_clean": True,
    }


def test_source_gate_fails_closed_when_explicit_commit_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, head = _source_repo(tmp_path, monkeypatch)
    wrong = "0" * 40 if head != "0" * 40 else "1" * 40
    with pytest.raises(ValueError, match="source commit mismatch"):
        verify_source_gate(repo, wrong)


@pytest.mark.parametrize("untracked", [False, True], ids=["tracked-dirty", "untracked-file"])
def test_source_gate_rejects_dirty_tracked_and_untracked_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, untracked: bool,
) -> None:
    repo, head = _source_repo(tmp_path, monkeypatch)
    target = repo / ("untracked.txt" if untracked else "tracked.txt")
    target.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="worktree is not clean"):
        verify_source_gate(repo, head)


def test_cli_requires_explicit_qualified_source_commit(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        runner.main([
            "--repo-root", str(tmp_path), "--evidence-root", str(tmp_path),
            "--canonical-root", str(tmp_path), "--output", str(tmp_path / "result.json"),
        ])
    assert exc_info.value.code == 2


def test_build_result_records_supplied_source_and_observed_head_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, head = _source_repo(tmp_path, monkeypatch)
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    sentinel = canonical / "sentinel.txt"
    sentinel.write_text("unchanged\n", encoding="utf-8")

    horizon_rows = {
        "GENERIC_TOPOLOGY_EVENT_COVERAGE": ("INSUFFICIENT_IMPACT_BOUND", "UNKNOWN"),
        "JUNCTION_CONSISTENCY": ("INSUFFICIENT_IMPACT_BOUND", None),
        "MECHANICS_REQUIREMENT": ("NOT_APPLICABLE", None),
        "NEXT_RIFT_PROCESS_EVOLUTION": ("AUTHORITY_BLOCKED", "UNKNOWN"),
        "PLATE_INTERFACE_EVENT_PREDICATES": ("INSUFFICIENT_IMPACT_BOUND", "UNKNOWN"),
        "SOURCE_TEMPORAL_VALIDITY": ("AUTHORITY_BLOCKED", None),
        "SUPPORT_MEMBERSHIP_VALIDITY": ("INSUFFICIENT_IMPACT_BOUND", None),
    }
    replay = {
        "case_count": 7, "repeatable": True,
        "semantic_results_match_development_prequalification": True,
        "adjudications": [
            {"assessment": {"subject_id": key, "event_occurrence": occurrence},
             "significance_class": classification}
            for key, (classification, occurrence) in horizon_rows.items()
        ],
    }
    invariance = {
        "physical_epoch_count_before": 2, "physical_epoch_count_after": 2,
        "pre_event_state_id": runner.EXPECTED_PRE_STATE,
        "post_event_state_id": runner.EXPECTED_POST_STATE,
        "physical_payload_sha256": runner.EXPECTED_PAYLOAD_SHA256,
    }
    documents = {
        "R6_RIFT_PROCESS_ACTIVATION_MODEL_V1.json": {},
        "R6_POST_EVENT_KINEMATIC_AUTHORITY_V1.json": {
            "temporal_scope": {"source_temporal_support": "INSTANT_ONLY"},
            "second_dt_gate": {"SECOND_DT_SELECTED": False},
        },
        "R6_POST_EVENT_KINEMATIC_REVALIDATION_HORIZON_V1.json": {
            "scope": {"physical_age_ma": runner.EXPECTED_AGE_MA,
                      "causal_origin_state_id": runner.EXPECTED_POST_STATE},
            "derivation": {"horizon_delta_years": 8214.051909111062},
            "b6n4_eligibility": {"limiting_eligible_for_dt_adjudication": True},
        },
        "R6_SECOND_DT_AUTHORIZATION_AFTER_RIFT_V1.json": {
            "second_dt_authorized_by_this_contract": False,
            "t2_creation_authorized": False, "failure_behavior": "unknown blocks",
        },
        "R6_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY_V1.json": {
            "current_policy_qualification": {"historical_B6N4_V1_authorization_changed": False},
        },
        "R6_B6N4A_ATTESTATION.json": {
            "qualified_source_commit": runner.EXPECTED_B6N4A_SOURCE,
            "evidence_manifest_sha256": runner.EXPECTED_B6N4A_MANIFEST_SHA256,
        },
        "B6N4A_QUALIFICATION_RESULT.json": {
            "verdict": "PASS_B6N4A_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY",
            "qualified_source_commit": runner.EXPECTED_B6N4A_SOURCE,
        },
        "B6N4A_SEVEN_UNKNOWN_ADJUDICATION.json": replay,
        "B6N4A_CANONICAL_INVARIANCE.json": invariance,
    }
    monkeypatch.setattr(runner, "_load_json", lambda path: documents[Path(path).name])
    monkeypatch.setattr(runner, "_verify_manifest", lambda bundle: None)
    monkeypatch.setattr(runner, "inspect_canonical_read_only", lambda root: {"read_only": True})

    result = build_decision(repo, tmp_path / "evidence", canonical, head)
    assert result["qualified_source_commit"] == head
    assert result["observed_head"] == head
    assert result["source_gate"]["worktree_clean"] is True
    assert result["verdict"] == "BLOCKED_B6N4R1_RELEVANT_AUTHORITY_UNRESOLVED"
    assert [row["dependency"] for row in result["decision"]["blocking_dependencies"]] == [
        "GENERIC_TOPOLOGY_EVENT_COVERAGE", "NEXT_RIFT_PROCESS_EVOLUTION",
        "PLATE_INTERFACE_EVENT_PREDICATES", "SUPPORT_MEMBERSHIP_VALIDITY",
    ]
    assert result["decision"]["SECOND_DT_SELECTED"] is False
    assert result["decision"]["T2_CREATED"] is False
    assert sentinel.read_text(encoding="utf-8") == "unchanged\n"


def test_qualification_output_must_be_outside_repository_and_canonical_store(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    canonical = tmp_path / "canonical"
    repo.mkdir()
    canonical.mkdir()
    require_external_output(tmp_path / "evidence" / "result.json", repo, canonical)
    with pytest.raises(ValueError, match="outside repository"):
        require_external_output(repo / "result.json", repo, canonical)
    with pytest.raises(ValueError, match="outside canonical WORLD_HISTORY"):
        require_external_output(canonical / "result.json", repo, canonical)

