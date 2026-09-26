from __future__ import annotations

import subprocess

import pytest

from arcana_worldsim.r6.repository_context import (
    require_repository_context, resolve_external_payload_path,
)


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def test_repository_context_accepts_feature_branch_and_detached_head(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "r6/ubuntu-workstation")
    _git(repo, "config", "user.name", "R6 test")
    _git(repo, "config", "user.email", "r6-test@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-m", "fixture")

    feature = require_repository_context(
        repo, required_ancestor=_git(repo, "rev-parse", "HEAD").stdout.strip()
    )
    missing_remote = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
        cwd=repo, check=False,
    )
    assert missing_remote.returncode != 0
    assert feature.branch == "r6/ubuntu-workstation"
    assert feature.detached is False
    assert len(feature.head) == 40
    assert feature.refs["origin/main"] is None
    assert feature.to_dict()["origin_main"] is None

    _git(repo, "checkout", "--detach", "HEAD")
    detached = require_repository_context(repo, required_ancestor=feature.head)
    assert detached.branch is None
    assert detached.detached is True
    assert detached.head == feature.head
    assert detached.refs["origin/main"] is None


def test_repository_context_rejects_head_not_descending_from_baseline(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "r6/ubuntu-workstation")
    _git(repo, "config", "user.name", "R6 test")
    _git(repo, "config", "user.email", "r6-test@example.invalid")
    (repo / "seed.txt").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-m", "baseline")
    baseline = _git(repo, "rev-parse", "HEAD").stdout.strip()

    _git(repo, "checkout", "--orphan", "unrelated")
    (repo / "independent.txt").write_text("unrelated history\n", encoding="utf-8")
    _git(repo, "add", "independent.txt")
    _git(repo, "commit", "-m", "unrelated root")
    _git(repo, "cat-file", "-e", f"{baseline}^{{commit}}")

    with pytest.raises(RuntimeError, match="required base is not an ancestor"):
        require_repository_context(repo, required_ancestor=baseline)


def test_canonical_text_digest_ignores_checkout_line_endings(tmp_path):
    from arcana_worldsim.r6.repository_context import canonical_text_sha256

    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    lf.write_bytes(b'{\n  "value": true\n}\n')
    crlf.write_bytes(b'{\r\n  "value": true\r\n}\r\n')
    assert canonical_text_sha256(lf) == canonical_text_sha256(crlf)


def test_legacy_windows_external_payload_path_maps_to_portable_root(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    external = tmp_path / "payload-root"
    monkeypatch.setenv("ARCANA_EXTERNAL_ROOT", str(external))
    legacy = r"F:\old\machine\_ARCANA_EXTERNAL_SOURCES\r6\tectonic_t0\mesh.npz"
    resolved = resolve_external_payload_path(repo, legacy)
    assert resolved == external / "r6" / "tectonic_t0" / "mesh.npz"
