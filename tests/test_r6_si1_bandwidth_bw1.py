from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from arcana_worldsim.r6.si1_bandwidth_bw1 import (
    _parse_runtime,
    _remap_feg,
    _roundtrip_check,
    _replace_tokens,
    build_permutation,
    validate_permutation,
    verify_output_manifest,
    _verify_authorities,
)


def test_rcm_maps_are_deterministic_bijection_and_inverse():
    triangles = np.asarray([[1, 2, 3], [2, 4, 3], [3, 4, 5]], dtype=np.int64)
    maps_a = build_permutation(triangles, 5)
    maps_b = build_permutation(triangles, 5)
    assert np.array_equal(maps_a[0], maps_b[0])
    assert np.array_equal(maps_a[1], maps_b[1])
    validate_permutation(*maps_a, 5)


def test_permutation_fails_closed_for_missing_duplicate_or_out_of_range_ids():
    with pytest.raises(ValueError, match="bijection"):
        validate_permutation(np.asarray([1, 1, 3]), np.asarray([1, 2, 3]), 3)
    with pytest.raises(ValueError, match="inverses"):
        validate_permutation(np.asarray([2, 1, 3]), np.asarray([1, 2, 3]), 3)
    with pytest.raises(ValueError, match="outside permutation domain"):
        build_permutation(np.asarray([[1, 2, 4]]), 3)
    with pytest.raises(ValueError, match="missing or extra IDs"):
        validate_permutation(np.asarray([1, 2]), np.asarray([1, 2]), 3)
    with pytest.raises(ValueError, match="positive"):
        validate_permutation(np.asarray([], dtype=np.int64), np.asarray([], dtype=np.int64), 0)


def test_feg_id_rewrite_preserves_non_id_text_orientation_and_inverse_bytes():
    nodes = ["1 10.000 20.00 -3.0 0.0\n", "2 -1 4 8 9\n", "3 7 8 9 10\n"]
    triangles = ["9 1 2 3 77\n"]
    old_to_new = np.asarray([2, 3, 1], dtype=np.int64)
    new_to_old = np.asarray([3, 1, 2], dtype=np.int64)
    mapped_nodes = [_replace_tokens(nodes[old - 1], {0: str(new)}) for new, old in enumerate(new_to_old, 1)]
    mapped_triangles = [_replace_tokens(triangles[0], {1: "2", 2: "3", 3: "1"})]
    _roundtrip_check(nodes, triangles, mapped_nodes, mapped_triangles, new_to_old, old_to_new)
    assert mapped_triangles[0].split()[1:4] == ["2", "3", "1"]
    assert mapped_triangles[0].split()[4] == "77"


def test_runtime_records_keep_all_50_values_and_support_metadata_on_mapping(tmp_path):
    path = tmp_path / "runtime.dat"
    fields_a = ["1"] + [str(index / 3) for index in range(1, 51)]
    fields_b = ["2"] + [str(index / 5) for index in range(1, 51)]
    path.write_bytes(("ARCANA_R6_PRE_ORBDATA_RUNTIME_V1 arcana_worldsim.r6.shellset_owner_bound_runtime.v1 2\n" + " ".join(fields_a) + "\n" + " ".join(fields_b) + "\n").encode("ascii"))
    header, records, _ = _parse_runtime(path, 2)
    new_to_old = np.asarray([2, 1], dtype=np.int64)
    derived = [_replace_tokens(records[old - 1], {0: str(new)}) for new, old in enumerate(new_to_old, 1)]
    assert [len(line.split()) for line in derived] == [51, 51]
    assert derived[0].split()[1:] == fields_b[1:]
    assert derived[1].split()[1:] == fields_a[1:]
    assert header[0].startswith("ARCANA_R6_PRE_ORBDATA_RUNTIME_V1")


def test_runtime_rejects_nan_inf_duplicate_or_wrong_field_count(tmp_path):
    path = tmp_path / "runtime.dat"
    good = ["1"] + ["0.0"] * 50
    bad = good.copy()
    bad[15] = "NaN"
    path.write_bytes(("schema package 1\n" + " ".join(bad) + "\n").encode("ascii"))
    with pytest.raises(ValueError, match="NaN or infinity"):
        _parse_runtime(path, 1)
    path.write_bytes(b"schema package 1\n1 2 3\n")
    with pytest.raises(ValueError, match="fields"):
        _parse_runtime(path, 1)


def test_runtime_rejects_duplicate_node_identity(tmp_path):
    path = tmp_path / "runtime.dat"
    record = " ".join(["1"] + ["0.0"] * 50)
    path.write_bytes(("schema package 2\n" + record + "\n" + record + "\n").encode("ascii"))
    with pytest.raises(ValueError, match="duplicate runtime node ID"):
        _parse_runtime(path, 2)


def test_governed_input_hash_mismatch_fails_closed(tmp_path):
    feg = tmp_path / "source.feg"
    package = tmp_path / "runtime.dat"
    feg_manifest = tmp_path / "feg.json"
    package_manifest = tmp_path / "runtime.json"
    feg.write_bytes(b"actual-feg")
    package.write_bytes(b"actual-runtime")
    feg_manifest.write_text(json.dumps({"production_feg": {"raw_sha256": "wrong"}}), encoding="utf-8")
    package_manifest.write_text(json.dumps({"runtime_data_sha256": hashlib.sha256(package.read_bytes()).hexdigest()}), encoding="utf-8")
    with pytest.raises(ValueError, match="FEG raw SHA256"):
        _verify_authorities(feg, package, feg_manifest, package_manifest)


def test_output_manifest_checks_all_input_hashes_and_fails_on_corruption(tmp_path):
    files = {
        "derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg": b"feg\n",
        "derived/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat": b"runtime\n",
        "fair_staging/INPUT/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg": b"feg\n",
        "fair_staging/INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat": b"runtime\n",
    }
    entries = []
    for relative, payload in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        entries.append({"path": relative, "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    permutation = tmp_path / "permutation/BW1_NODE_PERMUTATION_V1.json"
    permutation.parent.mkdir(parents=True, exist_ok=True)
    map_blob = np.asarray([2, 1, 2, 1], dtype="<i8").tobytes()
    permutation.write_text(json.dumps({"schema": "R6_SI1_BW1_NODE_PERMUTATION_V1", "node_count": 2, "old_to_new": [2, 1], "new_to_old": [2, 1], "serialized_maps_sha256_little_endian_int64": hashlib.sha256(map_blob).hexdigest()}), encoding="utf-8")
    permutation_payload = permutation.read_bytes()
    entries.append({"path": "permutation/BW1_NODE_PERMUTATION_V1.json", "size_bytes": len(permutation_payload), "sha256": hashlib.sha256(permutation_payload).hexdigest()})
    manifest_path = tmp_path / "manifests/BW1_INPUT_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"schema": "R6_SI1_BW1_ARTIFACT_MANIFEST_V1", "files": entries}), encoding="utf-8")
    assert verify_output_manifest(tmp_path)["valid"] is True
    (tmp_path / "derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg").write_bytes(b"corrupt\n")
    with pytest.raises(ValueError, match="integrity mismatch"):
        verify_output_manifest(tmp_path)
