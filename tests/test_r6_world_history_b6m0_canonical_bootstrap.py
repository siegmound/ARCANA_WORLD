"""Static/unit coverage for B6M0 gates and atomic genesis installation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from arcana_worldsim.r6 import canonical_bootstrap as b6m0


def _expected_env() -> dict[str, str]:
    return {
        "GIT_OBJECT_DIRECTORY": r"C:\Users\jose_\AppData\Local\ARCANA\git-objects\r6",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": (
            "F:\\corsiiiuu\\Magistrale\\Arcana\\ArcanaWorld\\"
            "ARCANA_WORLD1_v0_6D1_R3_11_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CANDIDATE\\.git\\objects"),
        "ARCANA_WORLD_HISTORY_ROOT": (
            r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\ARCANA_WORLD_HISTORY_R6_CANONICAL"),
    }


def test_environment_gate_requires_all_exact_supplied_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _expected_env().items():
        monkeypatch.setenv(key, value)
    assert b6m0._expected_environment() == _expected_env()
    monkeypatch.delenv("ARCANA_WORLD_HISTORY_ROOT")
    with pytest.raises(b6m0.CanonicalBootstrapError, match="environment differs"):
        b6m0._expected_environment()


def test_source_gate_checks_commit_object_and_tolerates_only_named_logs(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    responses = {
        ("branch", "--show-current"): b6m0.EXPECTED_BRANCH,
        ("rev-parse", "--verify", "HEAD"): b6m0.EXPECTED_HEAD,
        ("cat-file", "-t", "HEAD"): "commit",
        ("log", "-1", "--format=%H%n%s", "HEAD"): (
            f"{b6m0.EXPECTED_HEAD}\nfeat: qualify first candidate for canonical publication"),
        ("status", "--porcelain", "--untracked-files=all"):
            "?? B6J_CODEX_LUNA_RESULT.txt\n?? B6M_CODEX_LUNA_RESULT.txt",
        ("diff", "--cached", "--name-only"): "",
        ("diff", "--unified=0", "--", "src/arcana_worldsim/r6/t0_world_history_adapter.py"):
            "-def authority_inventory(root: str | Path) -> dict[str, Any]:\n"
            "+def authority_inventory(root: str | Path, *,\n"
            '+                       expected_branch: str = "r6/b3-governed-t0-read-only-ingest"\n'
            "+                       ) -> dict[str, Any]:\n"
            '-    if branch != "r6/b3-governed-t0-read-only-ingest":\n'
            "+    if branch != expected_branch:",
    }
    monkeypatch.setattr(b6m0, "_git", lambda _root, *args, **_kwargs: responses[args])
    result = b6m0.verify_source_gate(tmp_path)
    assert result["object_type"] == "commit"
    assert result["known_local_logs_tolerated"] is True


def test_source_gate_fails_closed_on_wrong_commit_object(monkeypatch: pytest.MonkeyPatch,
                                                         tmp_path: Path) -> None:
    responses = {
        ("branch", "--show-current"): b6m0.EXPECTED_BRANCH,
        ("rev-parse", "--verify", "HEAD"): b6m0.EXPECTED_HEAD,
        ("cat-file", "-t", "HEAD"): "tree",
        ("log", "-1", "--format=%H%n%s", "HEAD"): "wrong\nsubject",
    }
    monkeypatch.setattr(b6m0, "_git", lambda _root, *args, **_kwargs: responses[args])
    with pytest.raises(b6m0.CanonicalBootstrapError, match="source identity"):
        b6m0.verify_source_gate(tmp_path)


@pytest.mark.parametrize("status", [
    " M src/unrelated.py", "?? unrelated.txt",
])
def test_source_gate_rejects_unrelated_worktree_changes(monkeypatch: pytest.MonkeyPatch,
                                                        tmp_path: Path,
                                                        status: str) -> None:
    responses = {
        ("branch", "--show-current"): b6m0.EXPECTED_BRANCH,
        ("rev-parse", "--verify", "HEAD"): b6m0.EXPECTED_HEAD,
        ("cat-file", "-t", "HEAD"): "commit",
        ("log", "-1", "--format=%H%n%s", "HEAD"): f"{b6m0.EXPECTED_HEAD}\nsubject",
        ("status", "--porcelain", "--untracked-files=all"): status,
        ("diff", "--cached", "--name-only"): "",
        ("diff", "--unified=0", "--", "src/arcana_worldsim/r6/t0_world_history_adapter.py"):
            "-def authority_inventory(root: str | Path) -> dict[str, Any]:\n"
            "+def authority_inventory(root: str | Path, *,\n"
            '+                       expected_branch: str = "r6/b3-governed-t0-read-only-ingest"\n'
            "+                       ) -> dict[str, Any]:\n"
            '-    if branch != "r6/b3-governed-t0-read-only-ingest":\n'
            "+    if branch != expected_branch",
    }
    monkeypatch.setattr(b6m0, "_git", lambda _root, *args, **_kwargs: responses[args])
    with pytest.raises(b6m0.CanonicalBootstrapError, match="unrelated"):
        b6m0.verify_source_gate(tmp_path)


def test_root_classification_is_read_only_and_fail_closed(tmp_path: Path) -> None:
    target = tmp_path / "canonical"
    expected_id = "r6canonical_" + "a" * 64
    assert b6m0.classify_canonical_root(target, expected_id) == "ABSENT"
    target.mkdir()
    assert b6m0.classify_canonical_root(target, expected_id) == "EMPTY"
    (target / "unexpected.bin").write_bytes(b"keep")
    assert b6m0.classify_canonical_root(target, expected_id) == "NONEMPTY_UNRECOGNIZED_TARGET"
    (target / "unexpected.bin").unlink()
    (target / b6m0.STORE_DESCRIPTOR).write_text(
        json.dumps({"store_identity": "r6canonical_" + "b" * 64}), encoding="utf-8")
    assert b6m0.classify_canonical_root(target, expected_id) == "CONFLICTING_CANONICAL_STORE"
    assert set(p.name for p in target.iterdir()) == {b6m0.STORE_DESCRIPTOR}


def test_atomic_staged_install_is_no_overwrite_and_does_not_copy_payload(tmp_path: Path) -> None:
    staged = tmp_path / "private-stage"
    target = tmp_path / "canonical"
    staged.mkdir()
    (staged / b6m0.STORE_DESCRIPTOR).write_text("{}\n", encoding="utf-8")
    payload = staged / "payload.ref"
    payload.write_text("sha256:external-reference\n", encoding="utf-8")
    b6m0.publish_staged_store(staged, target)
    assert not staged.exists()
    assert (target / "payload.ref").read_text(encoding="utf-8").startswith("sha256:")
    second = tmp_path / "second-stage"
    second.mkdir()
    (second / b6m0.STORE_DESCRIPTOR).write_text("{}\n", encoding="utf-8")
    with pytest.raises(b6m0.CanonicalBootstrapError, match="changed before publication"):
        b6m0.publish_staged_store(second, target)
    assert (target / "payload.ref").exists()


def test_discovery_contract_is_path_independent_and_t1_stays_uncreated() -> None:
    store_id = "r6canonical_" + "c" * 64
    contract = b6m0.discovery_contract(store_id, ["r6state_" + "d" * 64])
    assert contract["runtime_root_source"] == "ARCANA_WORLD_HISTORY_ROOT"
    assert contract["absolute_path_in_semantic_identity"] is False
    assert contract["expected_canonical_temporal_state_count"] == 1
    assert "T1" not in json.dumps(contract)
