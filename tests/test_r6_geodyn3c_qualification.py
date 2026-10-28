import hashlib
import struct
import subprocess
from pathlib import Path

import pytest

import arcana_worldsim.r6.geodyn3c_qualification as qualification
from arcana_worldsim.r6.geodyn3c_qualification import (
    QualificationInputError,
    compare_numeric_audit,
    mesh_sha256_numeric,
    parse_geodyn2c_audit,
    validate_pytest_junit,
    validate_geodyn3c_run_claim,
    validate_source_inventory,
    verify_git_candidate,
)


def _mesh_arrays(index):
    np = pytest.importorskip("numpy", reason="numeric mesh digest requires NumPy")
    return (
        np.array([[index, 0, 0], [1, 0, 0], [0, 1, 0]], dtype="<f4"),
        np.array([0, 1, 2], dtype="<i4"),
        np.array([3], dtype="<i4"),
        np.array([5], dtype="|u1"),
    )


def _audit_pair():
    snapshots = []
    observed = []
    for snapshot_index in range(11):
        fields = []
        actual_fields = []
        for field_index in range(9):
            name = f"field_{field_index}"
            digest = hashlib.sha256(f"{snapshot_index}:{field_index}".encode()).hexdigest()
            numpy_dtype = "float32" if field_index % 2 == 0 else "float64"
            field_type = "Float32" if numpy_dtype == "float32" else "Float64"
            components = 2 if field_index == 0 else 1
            tuples = 3
            minimum = -1.25 if field_index == 0 else float(field_index)
            maximum = 2.5 if field_index == 0 else float(field_index + 2)
            stats = {"min": minimum, "max": maximum}
            name = "velocity" if field_index == 0 else name
            if field_index == 0:
                stats["norm_max"] = 2.75
            fields.append({"name": name, "type": numpy_dtype, "components": components,
                           "tuples": tuples, **stats, "sha256_bytes": digest})
            actual_fields.append({"name": name, "type": field_type, "components": components,
                                  "tuples": tuples, **stats, "sha256_bytes": digest})
        mesh_hash = _original_mesh_digest(snapshot_index)
        time_s = snapshot_index / 10
        snapshots.append({"time_s": time_s, "mesh_sha256_numeric": mesh_hash, "point_fields": fields})
        observed.append({"time_s": time_s, "mesh_sha256_numeric": mesh_hash, "point_fields": actual_fields})
    return {"snapshots": snapshots}, observed


def _original_mesh_digest(index):
    digest = hashlib.sha256()
    arrays = (
        ("float32", struct.pack("<9f", index, 0, 0, 1, 0, 0, 0, 1, 0)),
        ("int32", struct.pack("<3i", 0, 1, 2)),
        ("int32", struct.pack("<i", 3)),
        ("uint8", struct.pack("<B", 5)),
    )
    for dtype_name, payload in arrays:
        digest.update(dtype_name.encode())
        digest.update(payload)
    return digest.hexdigest()


def test_exact_geodyn2c_point_fields_schema_matches_99_fields_and_11_meshes():
    document, observed = _audit_pair()
    parsed = parse_geodyn2c_audit(document)
    result = compare_numeric_audit(parsed, observed)
    assert result["status"] == "PASS"
    assert result["mesh_comparisons"] == 11
    assert result["field_comparisons"] == 99
    first_velocity = parsed[0].point_fields[0]
    assert first_velocity.numpy_dtype == "float32"
    assert first_velocity.vtk_type == "Float32"
    assert (first_velocity.minimum, first_velocity.maximum, first_velocity.norm_max) == (-1.25, 2.5, 2.75)


def test_numeric_comparison_rejects_reordered_snapshot_times():
    document, observed = _audit_pair()
    with pytest.raises(QualificationInputError, match="native snapshot times differ"):
        compare_numeric_audit(parse_geodyn2c_audit(document), list(reversed(observed)))


def test_numeric_mesh_serialization_uses_declared_dtype_and_source_order():
    np = pytest.importorskip("numpy", reason="numeric mesh digest requires NumPy")
    expected = hashlib.sha256()
    for array in _mesh_arrays(0):
        value = np.ascontiguousarray(array)
        expected.update(str(value.dtype).encode("ascii"))
        expected.update(value.tobytes(order="C"))
    assert mesh_sha256_numeric(*_mesh_arrays(0)) == expected.hexdigest()
    assert mesh_sha256_numeric(*_mesh_arrays(0)) == _original_mesh_digest(0)


def test_geodyn2c_parser_rejects_unknown_or_incomplete_schema(tmp_path):
    with pytest.raises(QualificationInputError, match="top-level snapshots list"):
        parse_geodyn2c_audit({"snapshot_audits": []})
    document, _ = _audit_pair()
    del document["snapshots"][0]["point_fields"][0]["max"]
    with pytest.raises(QualificationInputError, match="missing point_fields"):
        parse_geodyn2c_audit(document)
    document, _ = _audit_pair()
    document["snapshots"][0]["point_fields"][0]["unexpected"] = "unknown schema extension"
    with pytest.raises(QualificationInputError, match="unsupported point_fields"):
        parse_geodyn2c_audit(document)
    document, _ = _audit_pair()
    document["snapshots"][0]["point_fields"][1]["type"] = "Float32"
    with pytest.raises(QualificationInputError, match="unsupported NumPy dtype"):
        parse_geodyn2c_audit(document)
    document, _ = _audit_pair()
    document["snapshots"][0]["point_fields"][1]["norm_max"] = 1.0
    with pytest.raises(QualificationInputError, match="invalid norm_max"):
        parse_geodyn2c_audit(document)
    report = tmp_path / "pytest.xml"
    _write_junit(report)
    assert validate_pytest_junit(report) == {
        "tests": 86, "passed": 86, "failed": 0, "errors": 0, "skipped": 0,
    }
    for count, outcome, bad_root_count, message in (
        (86, "skipped", False, "86 total/pass"),
        (86, "failure", False, "86 total/pass"),
        (86, "error", False, "86 total/pass"),
        (85, None, False, "86 total/pass"),
        (86, None, True, "suite tests counter"),
    ):
        _write_junit(report, count=count, outcome=outcome, bad_root_count=bad_root_count)
        with pytest.raises(QualificationInputError, match=message):
            validate_pytest_junit(report)


def _write_junit(path, *, count=86, outcome=None, bad_root_count=False):
    import xml.etree.ElementTree as ET

    failures = int(outcome == "failure")
    errors = int(outcome == "error")
    skipped = int(outcome == "skipped")
    root = ET.Element("testsuites", tests=str(count), failures=str(failures),
                      errors=str(errors), skipped=str(skipped))
    suite = ET.SubElement(root, "testsuite", tests=str(count),
                          failures=str(failures), errors=str(errors), skipped=str(skipped))
    for index in range(count):
        case = ET.SubElement(suite, "testcase", classname="fixture", name=f"test_{index}")
        if index == 0 and outcome:
            ET.SubElement(case, outcome).text = "fixture outcome"
    if bad_root_count:
        root.set("tests", str(count + 1))
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def test_geodyn3c_historical_run_claim_preserves_real_commit_identities():
    values = {
        "attempt_id": "R1-FAIR-20261027",
        "solver_name": "ASPECT",
        "solver_version": "3.2.0-pre",
        "solver_source_commit": "30eb77ee5da186137d436dbad35c6cb3cab64b69",
        "repository_commit": "1fd5e8d8f21e28876da9ef89423755615efc6162",
        "adapter_commit": "1fd5e8d8f21e28876da9ef89423755615efc6162",
        "configuration_sha256": "a" * 64,
        "input_identities": ("b" * 64,),
        "time_basis_id": "ASPECT_NATIVE_SECONDS",
        "time_unit": "s",
        "time_unit_source": "operator-reported R1 run record",
        "solver_completed_time": 1.098612289,
        "availability_checked_at_utc": "2026-10-27T10:50:33Z",
        "declared_provenance": {
            "solver_source_commit_algorithm": "sha1",
            "repository_commit_algorithm": "sha1",
            "adapter_commit_algorithm": "sha1",
        },
    }
    claim = validate_geodyn3c_run_claim(values)
    assert claim.solver_source_commit == "30eb77ee5da186137d436dbad35c6cb3cab64b69"
    assert claim.repository_commit == claim.adapter_commit == "1fd5e8d8f21e28876da9ef89423755615efc6162"


def test_geodyn3c_run_claim_rejects_incomplete_or_conflicting_provenance():
    values = {
        "attempt_id": "R1-FAIR-20261027",
        "solver_name": "ASPECT",
        "solver_version": "3.2.0-pre",
        "solver_source_commit": "30eb77ee5da186137d436dbad35c6cb3cab64b69",
        "repository_commit": "1fd5e8d8f21e28876da9ef89423755615efc6162",
        "adapter_commit": "1fd5e8d8f21e28876da9ef89423755615efc6162",
        "configuration_sha256": "a" * 64,
        "input_identities": ("b" * 64,),
        "time_basis_id": "ASPECT_NATIVE_SECONDS",
        "time_unit": "s",
        "time_unit_source": "operator-reported R1 run record",
        "solver_completed_time": 1.098612289,
        "availability_checked_at_utc": "2026-10-27T10:50:33Z",
        "declared_provenance": {
            "solver_source_commit_algorithm": "sha1",
            "repository_commit_algorithm": "sha1",
            "adapter_commit_algorithm": "sha1",
        },
    }
    for key in ("attempt_id", "input_identities", "configuration_sha256"):
        damaged = dict(values)
        damaged.pop(key)
        with pytest.raises((QualificationInputError, TypeError, ValueError)):
            validate_geodyn3c_run_claim(damaged)
    damaged = {**values, "declared_provenance": {}}
    with pytest.raises(QualificationInputError, match="algorithm"):
        validate_geodyn3c_run_claim(damaged)
    damaged = {**values, "adapter_commit": "e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa"}
    with pytest.raises(QualificationInputError, match="adapter commit"):
        validate_geodyn3c_run_claim(damaged)


def test_source_inventory_requires_nonempty_unique_valid_records():
    with pytest.raises(QualificationInputError, match="empty inventory"):
        validate_source_inventory({"files": []})
    row = {"relative_ref": "series/example.vtu", "byte_length": 3, "sha256": "a" * 64}
    assert validate_source_inventory({"files": [row]})[row["relative_ref"]].byte_length == 3
    with pytest.raises(QualificationInputError, match="duplicate ref"):
        validate_source_inventory({"files": [row, row]})
    with pytest.raises((QualificationInputError, ValueError)):
        validate_source_inventory({"files": [{**row, "sha256": "A" * 64}]})


@pytest.mark.parametrize("damage", (
    "mesh", "field_type", "field_components", "field_tuples", "field_hash",
))
def test_geodyn2c_comparison_rejects_mesh_and_typed_field_mismatches(damage):
    document, observed = _audit_pair()
    if damage == "mesh":
        observed[0]["mesh_sha256_numeric"] = "0" * 64
    else:
        key = {"field_type": "type", "field_components": "components",
               "field_tuples": "tuples", "field_hash": "sha256_bytes",
               "field_min": "min", "field_max": "max", "field_norm": "norm_max"}[damage]
        replacements = {"type": "Float64", "components": 7, "tuples": 4,
                        "sha256_bytes": "0" * 64, "min": 99.0, "max": 99.0, "norm_max": 99.0}
        observed[0]["point_fields"][0][key] = replacements[key]
    with pytest.raises(QualificationInputError, match="mismatch"):
        compare_numeric_audit(parse_geodyn2c_audit(document), observed)

    # Exercise the three additional auditor statistics without changing the
    # fixed 85-test FAIR acceptance count (one test covers the related cases).
    for key in ("min", "max", "norm_max"):
        document, observed = _audit_pair()
        observed[0]["point_fields"][0][key] = 99.0
        with pytest.raises(QualificationInputError, match="mismatch"):
            compare_numeric_audit(parse_geodyn2c_audit(document), observed)


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def test_git_candidate_checks_exact_remote_commit_and_parent_without_checkout_switch(tmp_path, monkeypatch):
    work = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    work.mkdir()
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "init", str(work))
    _git(work, "config", "user.email", "test@example.invalid")
    _git(work, "config", "user.name", "Test")
    (work / "base.txt").write_text("base\n", encoding="utf-8")
    _git(work, "add", "base.txt")
    _git(work, "commit", "-m", "parent")
    parent = _git(work, "rev-parse", "HEAD")
    _git(work, "switch", "-c", "maintenance")
    _git(work, "switch", "-c", "candidate")
    (work / "candidate.txt").write_text("qualified\n", encoding="utf-8")
    _git(work, "add", "candidate.txt")
    _git(work, "commit", "-m", "qualified candidate")
    candidate = _git(work, "rev-parse", "HEAD")
    real_git = qualification._git
    def fake_git(repo, *args):
        if args[:3] == ("ls-remote", "--exit-code", "origin"):
            return f"{candidate}\trefs/heads/r6/multiphysics-integration-20261026"
        return real_git(repo, *args)
    monkeypatch.setattr(qualification, "_git", fake_git)
    _git(work, "switch", "maintenance")
    before_head = _git(work, "rev-parse", "HEAD")
    result = verify_git_candidate(
        work, branch_ref="refs/heads/r6/multiphysics-integration-20261026",
        expected_commit=candidate, expected_parent=parent,
    )
    assert result["qualified_commit"] == candidate
    assert result["qualified_parent"] == parent
    assert result["remote_commit"] == candidate
    assert result["checkout_branch"] == "maintenance"
    assert result["checkout_head"] == before_head == parent
    assert _git(work, "rev-parse", "HEAD") == before_head

    # A linked worktree has a .git file rather than a .git directory. The gate
    # must inspect it through Git without changing the worktree/index identity.
    linked = tmp_path / "linked-worktree"
    _git(work, "worktree", "add", "--detach", str(linked), candidate)
    git_dir = _git(linked, "rev-parse", "--git-dir")
    assert (linked / ".git").is_file()
    assert Path(git_dir).exists() or (linked / git_dir).exists()
    linked_head = _git(linked, "rev-parse", "HEAD")
    linked_branch = _git(linked, "branch", "--show-current")
    index_path_text = _git(linked, "rev-parse", "--git-path", "index")
    index_path = Path(index_path_text)
    if not index_path.is_absolute():
        index_path = linked / index_path
    index_before = hashlib.sha256(index_path.read_bytes()).hexdigest()
    linked_result = verify_git_candidate(
        linked, branch_ref="refs/heads/r6/multiphysics-integration-20261026",
        expected_commit=candidate, expected_parent=parent,
    )
    assert linked_result["qualified_commit"] == candidate
    assert linked_result["qualified_parent"] == parent
    assert linked_result["checkout_head"] == linked_head == candidate
    assert linked_result["checkout_branch"] == linked_branch
    assert _git(linked, "rev-parse", "HEAD") == linked_head
    assert _git(linked, "branch", "--show-current") == linked_branch
    assert hashlib.sha256(index_path.read_bytes()).hexdigest() == index_before


def test_git_candidate_fails_closed_on_parent_or_remote_mismatch(tmp_path, monkeypatch):
    work = tmp_path / "repo"
    remote = tmp_path / "origin.git"
    work.mkdir()
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "init", str(work))
    _git(work, "config", "user.email", "test@example.invalid")
    _git(work, "config", "user.name", "Test")
    (work / "source.txt").write_text("one\n", encoding="utf-8")
    _git(work, "add", "source.txt")
    _git(work, "commit", "-m", "first")
    parent = _git(work, "rev-parse", "HEAD")
    (work / "source.txt").write_text("two\n", encoding="utf-8")
    _git(work, "commit", "-am", "second")
    candidate = _git(work, "rev-parse", "HEAD")
    remote_ref = "refs/heads/r6/multiphysics-integration-20261026"
    real_git = qualification._git
    def fake_git(repo, *args):
        if args[:3] == ("ls-remote", "--exit-code", "origin"):
            ref = args[3]
            return f"{parent}\t{ref}" if ref == remote_ref else f"{parent}\t{ref}"
        return real_git(repo, *args)
    monkeypatch.setattr(qualification, "_git", fake_git)
    with pytest.raises(QualificationInputError, match="parent mismatch"):
        verify_git_candidate(work, branch_ref="refs/heads/r6/multiphysics-integration-20261026",
                             expected_commit=candidate, expected_parent="0" * 40)
    with pytest.raises(QualificationInputError, match="commit and parent"):
        verify_git_candidate(work, branch_ref="refs/heads/r6/multiphysics-integration-20261026",
                             expected_commit=candidate, expected_parent="")
    with pytest.raises(QualificationInputError, match="remote ref points"):
        verify_git_candidate(work, branch_ref="refs/heads/other-branch",
                             expected_commit=candidate, expected_parent=parent)
