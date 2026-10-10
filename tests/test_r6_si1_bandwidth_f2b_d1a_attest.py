from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import pytest

from scripts.r6_si1_bandwidth_f2b_d1a_attest import (
    AttestationError,
    dof_node_slot,
    sha256_file,
    validate_permutation,
    validate_output_location,
    validate_bw1_source_authority_links,
    verify_feg_pair,
    verify_manifest,
    verify_runtime_pair,
)


def _map_digest(old_to_new: list[int], new_to_old: list[int]) -> str:
    content = b"".join(struct.pack("<q", value) for value in old_to_new + new_to_old)
    return hashlib.sha256(content).hexdigest()


def _write_feg(path: Path, node_lines: list[str], triangles: list[str]) -> None:
    path.write_text(
        "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1\n"
        f"{len(node_lines)} {len(node_lines)} 0 100000 T\n"
        + "".join(line + "\n" for line in node_lines)
        + f"{len(triangles)}\n"
        + "".join(line + "\n" for line in triangles)
        + "0\n",
        encoding="ascii",
        newline="\n",
    )


def _remap_fixture_feg(source: Path, derived: Path, old_to_new: list[int], new_to_old: list[int]) -> None:
    lines = source.read_bytes().splitlines(keepends=True)
    n = len(new_to_old)
    nodes = {int(line.split()[0]): line for line in lines[2 : 2 + n]}
    mapped_nodes = []
    for new_id, old_id in enumerate(new_to_old, start=1):
        line = nodes[old_id]
        fields = line.split()
        mapped_nodes.append(b" ".join([str(new_id).encode(), *fields[1:]]) + b"\n")
    tri_begin = 3 + n
    tri_count = int(lines[2 + n].split()[0])
    mapped_triangles = []
    for line in lines[tri_begin : tri_begin + tri_count]:
        fields = line.split()
        fields[1:4] = [str(old_to_new[int(v) - 1]).encode() for v in fields[1:4]]
        mapped_triangles.append(b" ".join(fields) + b"\n")
    derived.write_bytes(b"".join(lines[:2] + mapped_nodes + [lines[2 + n]] + mapped_triangles + [lines[-1]]))


def test_permutation_bijection_inverse_digest_and_raw_slot_mapping() -> None:
    old_to_new = [2, 4, 1, 3]
    new_to_old = [3, 1, 4, 2]
    checked = validate_permutation(old_to_new, new_to_old, 4, _map_digest(old_to_new, new_to_old))
    assert checked["inverse_equations_checked"] == 8
    assert dof_node_slot(1, new_to_old) == (1, 1, 3)
    assert dof_node_slot(2, new_to_old) == (1, 2, 3)
    assert dof_node_slot(8, new_to_old) == (4, 2, 2)
    with pytest.raises(AttestationError, match="bijections"):
        validate_permutation([2, 2, 1, 3], new_to_old, 4, _map_digest([2, 2, 1, 3], new_to_old))
    with pytest.raises(AttestationError, match="inverse equation"):
        validate_permutation([2, 4, 3, 1], new_to_old, 4, _map_digest([2, 4, 3, 1], new_to_old))
    with pytest.raises(AttestationError, match="digest"):
        validate_permutation(old_to_new, new_to_old, 4, "0" * 64)
    with pytest.raises(AttestationError, match="outside"):
        dof_node_slot(0, new_to_old)


def test_permutation_rejects_out_of_range_and_non_integer_entries() -> None:
    valid_old_to_new = [2, 1, 3]
    valid_new_to_old = [2, 1, 3]
    digest = _map_digest(valid_old_to_new, valid_new_to_old)
    with pytest.raises(AttestationError, match="bijections"):
        validate_permutation([2, 1, 4], valid_new_to_old, 3, digest)
    with pytest.raises(AttestationError, match="JSON integers"):
        validate_permutation([2, 1, True], valid_new_to_old, 3, digest)


def test_feg_transform_and_exact_inverse_roundtrip(tmp_path: Path) -> None:
    original = tmp_path / "original.feg"
    derived = tmp_path / "derived.feg"
    _write_feg(
        original,
        ["1 10.0 20.0 1", "2 11.0 21.0 2", "3 12.0 22.0 3", "4 13.0 23.0 4"],
        ["1 1 2 3 99", "2 2 4 3 88"],
    )
    old_to_new = [2, 4, 1, 3]
    new_to_old = [3, 1, 4, 2]
    _remap_fixture_feg(original, derived, old_to_new, new_to_old)
    result = verify_feg_pair(original, derived, old_to_new, new_to_old, 4, 2)
    assert result["triangle_vertex_references_checked"] == 6
    assert result["exact_text_inverse_reconstruction"] is True


def test_feg_coordinate_or_connectivity_alteration_fails_closed(tmp_path: Path) -> None:
    original = tmp_path / "original.feg"
    derived = tmp_path / "derived.feg"
    _write_feg(original, ["1 10 20 1", "2 11 21 2", "3 12 22 3"], ["1 1 2 3"])
    old_to_new = [2, 3, 1]
    new_to_old = [3, 1, 2]
    _remap_fixture_feg(original, derived, old_to_new, new_to_old)
    lines = derived.read_text(encoding="ascii").splitlines()
    lines[2] = lines[2].replace("12", "99", 1)
    derived.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    with pytest.raises(AttestationError, match="FEG nodal row"):
        verify_feg_pair(original, derived, old_to_new, new_to_old, 3, 1)


def test_feg_triangle_connectivity_alteration_fails_closed(tmp_path: Path) -> None:
    original = tmp_path / "original.feg"
    derived = tmp_path / "derived.feg"
    _write_feg(original, ["1 10 20 1", "2 11 21 2", "3 12 22 3"], ["1 1 2 3"])
    old_to_new = [2, 3, 1]
    new_to_old = [3, 1, 2]
    _remap_fixture_feg(original, derived, old_to_new, new_to_old)
    lines = derived.read_text(encoding="ascii").splitlines()
    lines[6] = "1 1 3 2"
    derived.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    with pytest.raises(AttestationError, match="triangle connectivity/order/orientation"):
        verify_feg_pair(original, derived, old_to_new, new_to_old, 3, 1)


def _runtime_record(node_id: int, branch: int, mixed: int, tag: int) -> str:
    fields = [str(node_id), str(tag), "0", "1", "1", str(mixed), "0", "0", str(branch)]
    fields.extend(str(i + tag) for i in range(42))
    assert len(fields) == 51
    return " ".join(fields)


def test_runtime_rows_reordered_and_all_payload_fields_preserved(tmp_path: Path) -> None:
    original = tmp_path / "orig.dat"
    derived = tmp_path / "derived.dat"
    records = {
        1: _runtime_record(1, 1, 0, 10),
        2: _runtime_record(2, 2, 1, 20),
        3: _runtime_record(3, 1, 0, 30),
    }
    header = "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1 arcana_worldsim.r6.shellset_owner_bound_runtime.v1 3"
    original.write_text(header + "\n" + "\n".join(records.values()) + "\n", encoding="ascii", newline="\n")
    new_to_old = [3, 1, 2]
    derived_records = [_runtime_record(i, int(records[new_to_old[i - 1]].split()[8]), int(records[new_to_old[i - 1]].split()[5]), int(records[new_to_old[i - 1]].split()[1])) for i in range(1, 4)]
    derived.write_text(header + "\n" + "\n".join(derived_records) + "\n", encoding="ascii", newline="\n")
    result = verify_runtime_pair(
        original,
        derived,
        new_to_old,
        3,
        expected_branch_counts={"1": 2, "2": 1},
        expected_mixed_count=1,
    )
    assert result["runtime_payload_fields_checked"] == 150
    altered = derived.read_text(encoding="ascii").replace("30", "31", 1)
    derived.write_text(altered, encoding="ascii", newline="\n")
    with pytest.raises(AttestationError, match="exact field-preserving remap"):
        verify_runtime_pair(original, derived, new_to_old, 3, expected_branch_counts={"1": 2, "2": 1}, expected_mixed_count=1)


def test_runtime_duplicate_node_record_fails_closed(tmp_path: Path) -> None:
    original = tmp_path / "orig.dat"
    derived = tmp_path / "derived.dat"
    records = [_runtime_record(1, 1, 0, 10), _runtime_record(2, 2, 1, 20)]
    header = "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1 arcana_worldsim.r6.shellset_owner_bound_runtime.v1 2"
    original.write_text(header + "\n" + "\n".join(records) + "\n", encoding="ascii", newline="\n")
    derived.write_text(header + "\n" + records[0] + "\n" + records[0] + "\n", encoding="ascii", newline="\n")
    with pytest.raises(AttestationError, match="duplicate or out of range"):
        verify_runtime_pair(original, derived, [1, 2], 2, expected_branch_counts={"1": 1, "2": 1}, expected_mixed_count=0)


def test_manifest_membership_and_tampering_are_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "bundle"
    root.mkdir()
    member = root / "payload.dat"
    member.write_bytes(b"authoritative payload\n")
    manifest = root / "manifest.json"
    doc = {"items": [{"path": "payload.dat", "bytes": member.stat().st_size, "sha256": sha256_file(member)}]}
    manifest.write_text(json.dumps(doc), encoding="utf-8")
    digest = sha256_file(manifest)
    ok = verify_manifest(root, "manifest.json", expected_manifest_sha256=digest, entries_key="items", size_key="bytes", sha_key="sha256")
    assert ok["member_count"] == 1
    member.write_bytes(b"tampered payload\n")
    with pytest.raises(AttestationError, match="identity mismatch"):
        verify_manifest(root, "manifest.json", expected_manifest_sha256=digest, entries_key="items", size_key="bytes", sha_key="sha256")


def test_manifest_rejects_extra_files_and_unsafe_paths(tmp_path: Path) -> None:
    root = tmp_path / "bundle"
    root.mkdir()
    member = root / "payload.dat"
    member.write_bytes(b"one\n")
    manifest = root / "manifest.json"
    doc = {"items": [{"path": "payload.dat", "bytes": member.stat().st_size, "sha256": sha256_file(member)}]}
    manifest.write_text(json.dumps(doc), encoding="utf-8")
    digest = sha256_file(manifest)
    (root / "unexpected.txt").write_text("extra", encoding="utf-8")
    with pytest.raises(AttestationError, match="membership mismatch"):
        verify_manifest(root, "manifest.json", expected_manifest_sha256=digest, entries_key="items", size_key="bytes", sha_key="sha256")
    (root / "unexpected.txt").unlink()
    doc["items"][0]["path"] = "../payload.dat"
    manifest.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(AttestationError, match="unsafe"):
        verify_manifest(root, "manifest.json", expected_manifest_sha256=sha256_file(manifest), entries_key="items", size_key="bytes", sha_key="sha256")


def test_output_path_must_be_new_and_separate_from_protected_inputs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    outputs = repo / "outputs"
    bw1 = outputs / "r6_si1_bandwidth_bw1"
    recovery = outputs / "r6_si1_bandwidth_f2av_offline_recovery"
    shellset = repo / "external/ShellSet-v1.1.0"
    evidence = tmp_path / "sealed_f2av"
    for path in (bw1, recovery, shellset, evidence, outputs):
        path.mkdir(parents=True, exist_ok=True)
    allowed = validate_output_location(repo, evidence, outputs / "r6_si1_bandwidth_f2b_d1a_attestation")
    assert allowed == outputs / "r6_si1_bandwidth_f2b_d1a_attestation"
    blocked = (
        bw1 / "accidental-output",
        recovery / "accidental-output",
        shellset / "accidental-output",
        evidence / "accidental-output",
        repo / "outside-outputs",
    )
    for candidate in blocked:
        with pytest.raises(AttestationError, match="output"):
            validate_output_location(repo, evidence, candidate)
        assert not candidate.exists()


def test_original_authorities_must_match_independent_bw1_report_hashes() -> None:
    authorities = {
        "original_feg": {"sha256": "a" * 64, "manifest_sha256": "b" * 64},
        "original_runtime": {"sha256": "c" * 64, "manifest_sha256": "d" * 64},
    }
    report_hashes = {
        "feg_sha256": "a" * 64,
        "runtime_package_sha256": "c" * 64,
        "feg_manifest_sha256": "b" * 64,
        "runtime_manifest_sha256": "d" * 64,
    }
    validate_bw1_source_authority_links(authorities, report_hashes)
    mutated = dict(report_hashes, feg_manifest_sha256="e" * 64)
    with pytest.raises(AttestationError, match="independently sealed BW1 report"):
        validate_bw1_source_authority_links(authorities, mutated)
    with pytest.raises(AttestationError, match="independently sealed BW1 report"):
        validate_bw1_source_authority_links(authorities, None)
