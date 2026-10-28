from __future__ import annotations

import hashlib
import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from arcana_worldsim.r6.experimental_trajectory_archive import (  # noqa: E402
    ArchiveError,
    ExperimentalTrajectoryArchive,
    NativeTime,
    RunIdentityClaim,
    SourceDigest,
    _archive_identity_payload,
    _id,
    canonical_bytes,
    index_existing_aspect_series,
)


def _write_series(root: Path, *, variable_mesh: bool = False) -> None:
    root.mkdir(parents=True)
    for ordinal, time_value in enumerate((0.0, 1.0, 2.0)):
        dx = float(ordinal) if variable_mesh else 0.0
        pressure = 10.0 + ordinal
        xml = f'''<VTKFile type="UnstructuredGrid" version="1.0" byte_order="LittleEndian">
<UnstructuredGrid><Piece NumberOfPoints="4" NumberOfCells="1">
<PointData><DataArray Name="p" type="Float32" NumberOfComponents="1" format="ascii">{pressure} {pressure} {pressure} {pressure}</DataArray></PointData>
<CellData><DataArray Name="material_id" type="Int32" NumberOfComponents="1" format="ascii">7</DataArray></CellData>
<Points><DataArray Name="Points" type="Float32" NumberOfComponents="3" format="ascii">{dx} 0 0 {2 + dx} 0 0 {2 + dx} 1 0 {dx} 1 0</DataArray></Points>
<Cells><DataArray Name="connectivity" type="Int32" NumberOfComponents="1" format="ascii">0 1 2 3</DataArray>
<DataArray Name="offsets" type="Int32" NumberOfComponents="1" format="ascii">4</DataArray>
<DataArray Name="types" type="UInt8" NumberOfComponents="1" format="ascii">9</DataArray></Cells>
</Piece></UnstructuredGrid></VTKFile>'''
        (root / f"state_{ordinal}.vtu").write_text(xml, encoding="utf-8", newline="\n")
    datasets = "".join(
        f'<DataSet timestep="{time_value}" group="" part="0" file="state_{ordinal}.vtu"/>'
        for ordinal, time_value in enumerate((0.0, 1.0, 2.0))
    )
    (root / "series.pvd").write_text(
        f'<VTKFile type="Collection" version="1.0"><Collection>{datasets}</Collection></VTKFile>',
        encoding="utf-8", newline="\n",
    )


def _inventory(root: Path) -> dict[str, SourceDigest]:
    result = {}
    for path in sorted(root.iterdir()):
        if path.is_file():
            raw = path.read_bytes()
            ref = path.name
            result[ref] = SourceDigest(ref, len(raw), hashlib.sha256(raw).hexdigest())
    return result


def _claim() -> RunIdentityClaim:
    return RunIdentityClaim(
        attempt_id="fixture-attempt-01", solver_name="ASPECT", solver_version="fixture",
        solver_source_commit="30eb77ee5da186137d436dbad35c6cb3cab64b69",
        repository_commit="1fd5e8d8f21e28876da9ef89423755615efc6162",
        adapter_commit="e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa",
        configuration_sha256="e" * 64, input_identities=("f" * 64,), time_basis_id="native-seconds-v1",
        time_unit="s", time_unit_source="synthetic test declaration", solver_completed_time=2.5,
        availability_checked_at_utc="2026-01-01T00:00:00Z",
        declared_provenance={"fixture": "TEST_ONLY", "solver_source_commit_algorithm": "sha1",
                             "repository_commit_algorithm": "sha1", "adapter_commit_algorithm": "sha1"},
        build_identity="TEST_ONLY",
    )


def test_run_identity_accepts_real_sha1_ids_and_preserves_algorithm_provenance():
    claim = _claim()
    assert claim.solver_source_commit == "30eb77ee5da186137d436dbad35c6cb3cab64b69"
    assert claim.repository_commit == "1fd5e8d8f21e28876da9ef89423755615efc6162"
    assert claim.adapter_commit == "e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa"
    assert {key: claim.declared_provenance[key] for key in (
        "solver_source_commit_algorithm", "repository_commit_algorithm", "adapter_commit_algorithm"
    )} == {"solver_source_commit_algorithm": "sha1", "repository_commit_algorithm": "sha1",
          "adapter_commit_algorithm": "sha1"}
    # The exact strings survive in the deterministic identity payload/manifest.
    assert claim.solver_source_commit in json.dumps(claim.__dict__, sort_keys=True)


def test_run_identity_accepts_sha256_git_object_ids_without_rewriting_them():
    claim = replace(_claim(), solver_source_commit="a" * 64,
                    repository_commit="b" * 64, adapter_commit="c" * 64,
                    declared_provenance={"fixture": "TEST_ONLY", "solver_source_commit_algorithm": "sha256",
                                         "repository_commit_algorithm": "sha256",
                                         "adapter_commit_algorithm": "sha256"})
    assert (claim.solver_source_commit, claim.repository_commit, claim.adapter_commit) == (
        "a" * 64, "b" * 64, "c" * 64)


@pytest.mark.parametrize("length", (39, 41, 63, 65))
@pytest.mark.parametrize("field", ("solver_source_commit", "repository_commit", "adapter_commit"))
def test_run_identity_rejects_unsupported_git_object_id_lengths(field, length):
    with pytest.raises(ValueError, match="40- or 64-hex"):
        replace(_claim(), **{field: "a" * length})


@pytest.mark.parametrize("bad_id", ("g" * 40, "A" * 40, "G" * 64, "A" * 64))
@pytest.mark.parametrize("field", ("solver_source_commit", "repository_commit", "adapter_commit"))
def test_run_identity_rejects_nonhex_or_uppercase_git_object_ids(field, bad_id):
    with pytest.raises(ValueError, match="40- or 64-hex"):
        replace(_claim(), **{field: bad_id})


def test_run_identity_keeps_configuration_and_inputs_strictly_sha256():
    with pytest.raises(ValueError, match="configuration_sha256 must be exactly 64"):
        replace(_claim(), configuration_sha256="a" * 40)
    with pytest.raises(ValueError, match="input_identities"):
        replace(_claim(), input_identities=("a" * 40,))


def _build(source: Path, output: Path, *, inventory=None, variable_mesh=False):
    if not source.exists():
        _write_series(source, variable_mesh=variable_mesh)
    return index_existing_aspect_series(
        trusted_source_root=source, pvd_relative_ref="series.pvd", run_identity=_claim(),
        expected_source_inventory=inventory or _inventory(source), output_index_root=output,
    )


def _open(output: Path, source: Path | None = None):
    roots = {} if source is None else {"source": source}
    return ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=output,
                                              trusted_source_roots=roots)


def test_manifest_and_ids_are_deterministic_across_relocated_source_roots(tmp_path):
    source_a, source_b = tmp_path / "mount_a", tmp_path / "mount_b"
    _write_series(source_a)
    shutil.copytree(source_a, source_b)
    out_a, out_b = tmp_path / "idx_a", tmp_path / "idx_b"
    first = _build(source_a, out_a)
    second = _build(source_b, out_b)
    assert first.status == second.status == "COMPLETE"
    manifest_a = (out_a / "manifest.json").read_bytes()
    manifest_b = (out_b / "manifest.json").read_bytes()
    assert manifest_a == manifest_b
    manifest_doc = json.loads(manifest_a)
    assert manifest_doc["archive_id"] == first.archive_id
    assert manifest_doc["run"]["identity_payload"]["solver"]["source_commit"] == _claim().solver_source_commit
    assert manifest_doc["run"]["identity_payload"]["source"] == {
        "repository_commit": _claim().repository_commit, "adapter_commit": _claim().adapter_commit}
    assert manifest_doc["run"]["source"]["provenance_claims"]["solver_source_commit_algorithm"] == "sha1"
    assert not any(path.suffix == ".vtu" for path in out_a.iterdir())
    assert sorted(path.name for path in out_a.iterdir()) == ["manifest.json", "manifest.sha256"]


def test_queries_are_exact_inclusive_native_time_and_have_no_nearest_fallback(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    result = _build(source, output)
    archive = _open(output, source)
    run_id = archive.manifest["run"]["run_id"]
    assert result.status == "COMPLETE"
    assert len(archive.query_snapshots(run_id).value) == 3
    assert len(archive.query_snapshots(run_id, start=NativeTime(1.0, "s", "native-seconds-v1"),
                                       end=NativeTime(2.0, "s", "native-seconds-v1")).value) == 2
    assert archive.get_snapshot_at(run_id, NativeTime(1.5, "s", "native-seconds-v1")).status == "MISSING_SNAPSHOT"
    assert archive.get_snapshot_at(run_id, NativeTime(1.0, "yr", "native-seconds-v1")).status == "INCOMPATIBLE_TIME_BASIS"
    assert archive.get_snapshot_at(run_id, NativeTime(1.0, "s", "other-basis")).status == "INCOMPATIBLE_TIME_BASIS"


def test_exact_lookup_reports_ambiguous_duplicate_native_times(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    _build(source, output)
    archive = _open(output)
    rows = archive.manifest["snapshots"]
    rows[1]["time"]["value"] = rows[0]["time"]["value"]
    duplicate_time = NativeTime(0.0, "s", "native-seconds-v1")
    result = archive.get_snapshot_at(archive.manifest["run"]["run_id"], duplicate_time)
    assert result.status == "AMBIGUOUS"
    assert len(result.candidates) == 2


def test_on_demand_field_and_snapshot_readback_verify_source_and_typed_values(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    _build(source, output)
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source.iterdir()}
    archive = _open(output, source)
    row = archive.manifest["snapshots"][1]
    p_field = next(item for item in archive.manifest["field_catalog"] if item["source_key"] == "point:p")
    field = archive.get_field(row["snapshot_id"], p_field["field_id"])
    snap = archive.get_snapshot(row["snapshot_id"])
    assert field.status == "FOUND" and field.value["values"] == (11.0, 11.0, 11.0, 11.0)
    assert snap.status == "FOUND"
    assert archive.verify_integrity().status == "PASS"
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source.iterdir()}
    assert before == after


def test_mesh_catalog_supports_changing_mesh_identity(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    _build(source, output, variable_mesh=True)
    archive = _open(output)
    assert len(archive.list_meshes().value) == 3
    assert len({row["mesh_id"] for row in archive.manifest["snapshots"]}) == 3
    assert archive.get_mesh(archive.manifest["snapshots"][0]["mesh_id"]).status == "FOUND"


def test_metadata_stays_readable_when_original_payload_root_is_not_provided(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    _build(source, output)
    archive = _open(output)
    run_id = archive.manifest["run"]["run_id"]
    assert archive.query_snapshots(run_id).status == "FOUND"
    assert archive.verify_integrity().status == "MISSING_PAYLOAD"
    field = archive.manifest["field_catalog"][0]
    row = archive.manifest["snapshots"][0]
    assert archive.get_field(row["snapshot_id"], field["field_id"]).status == "MISSING_PAYLOAD"
    assert archive.get_snapshot(row["snapshot_id"]).status == "MISSING_PAYLOAD"

    empty_root = tmp_path / "empty_source"
    empty_root.mkdir()
    missing_roots = [empty_root]
    pvd_missing_root = tmp_path / "pvd_missing_source"
    shutil.copytree(source, pvd_missing_root)
    (pvd_missing_root / "series.pvd").unlink()
    missing_roots.append(pvd_missing_root)
    vtu_missing_root = tmp_path / "vtu_missing_source"
    shutil.copytree(source, vtu_missing_root)
    (vtu_missing_root / "state_0.vtu").unlink()
    missing_roots.append(vtu_missing_root)
    for root in missing_roots:
        configured = _open(output, root)
        assert configured.verify_integrity().status == "MISSING_PAYLOAD"
        assert configured.get_snapshot(row["snapshot_id"]).status == "MISSING_PAYLOAD"
        assert configured.get_field(row["snapshot_id"], field["field_id"]).status == "MISSING_PAYLOAD"


def test_modified_payload_and_wrong_inventory_fail_closed(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    _write_series(source)
    bad = _inventory(source)
    bad["state_0.vtu"] = SourceDigest("state_0.vtu", 1, "0" * 64)
    built = _build(source, output, inventory=bad)
    assert built.status == "FAILED"
    assert (output / "INCOMPLETE.json").exists()
    incomplete = ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=output)
    assert incomplete.verify_integrity().status == "ARCHIVE_INCOMPLETE"
    assert incomplete.query_snapshots("anything").status == "ARCHIVE_INCOMPLETE"

    good_output = tmp_path / "good_index"
    _build(source, good_output)
    (source / "state_0.vtu").write_text("tampered", encoding="utf-8")
    archive = _open(good_output, source)
    assert archive.verify_integrity().status == "CORRUPT_PAYLOAD"
    row = archive.manifest["snapshots"][0]
    assert archive.get_snapshot(row["snapshot_id"]).status == "CORRUPT_PAYLOAD"


def test_pvd_disappearance_or_replacement_during_semantic_read_keeps_payload_status(tmp_path, monkeypatch):
    import arcana_worldsim.r6.experimental_trajectory_archive as archive_module

    source, output = tmp_path / "vanishing_source", tmp_path / "vanishing_index"
    _build(source, output)
    archive = _open(output, source)
    pvd = source / "series.pvd"
    original_reader = archive_module._pvd_time_tokens

    def remove_pvd_before_read(path):
        path.unlink()
        return original_reader(path)

    monkeypatch.setattr(archive_module, "_pvd_time_tokens", remove_pvd_before_read)
    missing = archive.verify_integrity()
    assert missing.status == "MISSING_PAYLOAD"
    assert missing.missing_files == ("source:series.pvd",)

    monkeypatch.setattr(archive_module, "_pvd_time_tokens", original_reader)
    changed_source, changed_output = tmp_path / "changed_source", tmp_path / "changed_index"
    _build(changed_source, changed_output)
    changed_archive = _open(changed_output, changed_source)
    changed_pvd = changed_source / "series.pvd"

    def replace_pvd_before_read(path):
        path.write_text(path.read_text(encoding="utf-8").replace('timestep="0.0"', 'timestep="0.25"', 1),
                        encoding="utf-8", newline="\n")
        return original_reader(path)

    monkeypatch.setattr(archive_module, "_pvd_time_tokens", replace_pvd_before_read)
    corrupt = changed_archive.verify_integrity()
    assert corrupt.status == "CORRUPT_PAYLOAD"
    assert corrupt.corrupt_files == ("source:series.pvd",)

    # A source can also disappear after verification but before the on-demand read.
    monkeypatch.setattr(archive_module, "_pvd_time_tokens", original_reader)
    on_demand_source, on_demand_output = tmp_path / "ondemand_source", tmp_path / "ondemand_index"
    _build(on_demand_source, on_demand_output)
    on_demand = _open(on_demand_output, on_demand_source)
    actual_series = on_demand._series

    def remove_pvd_after_integrity(root):
        (root / "series.pvd").unlink()
        return actual_series(root)

    monkeypatch.setattr(on_demand, "_series", remove_pvd_after_integrity)
    snapshot_id = on_demand.manifest["snapshots"][0]["snapshot_id"]
    assert on_demand.verify_integrity().status == "PASS"
    assert on_demand.get_snapshot(snapshot_id).status == "MISSING_PAYLOAD"


def test_interrupted_finalization_leaves_index_incomplete(tmp_path, monkeypatch):
    import arcana_worldsim.r6.experimental_trajectory_archive as archive_module

    source, output = tmp_path / "source", tmp_path / "index"
    _write_series(source)
    real_replace = archive_module.os.replace

    def fail_manifest_publish(source_path, target_path):
        if Path(target_path).name == "manifest.json":
            raise OSError("synthetic interruption before final manifest publication")
        return real_replace(source_path, target_path)

    monkeypatch.setattr(archive_module.os, "replace", fail_manifest_publish)
    result = _build(source, output)
    assert result.status == "FAILED"
    assert (output / "INCOMPLETE.json").exists()
    opened = ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=output)
    assert opened.verify_integrity().status == "ARCHIVE_INCOMPLETE"
    assert opened.list_meshes().status == "ARCHIVE_INCOMPLETE"


def test_manifest_seal_and_internal_reference_validation(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    _build(source, output)
    path = output / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["snapshots"][0]["vtu_relative_ref"] = "../outside.vtu"
    manifest["archive_id"] = _id("geodyn3archive", _archive_identity_payload(manifest))
    data = canonical_bytes(manifest)
    path.write_bytes(data)
    (output / "manifest.sha256").write_text(hashlib.sha256(data).hexdigest() + "\n", encoding="ascii")
    with pytest.raises(ArchiveError, match="manifest schema/reference"):
        _open(output)


def test_output_collision_is_not_overwritten_and_source_traversal_fails_closed(tmp_path):
    source, output = tmp_path / "source", tmp_path / "already_there"
    _write_series(source)
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    result = index_existing_aspect_series(
        trusted_source_root=source, pvd_relative_ref="series.pvd", run_identity=_claim(),
        expected_source_inventory=_inventory(source), output_index_root=output,
    )
    assert result.status == "FAILED" and sentinel.read_text(encoding="utf-8") == "preserve"
    failed = index_existing_aspect_series(
        trusted_source_root=source, pvd_relative_ref="../series.pvd", run_identity=_claim(),
        expected_source_inventory=_inventory(source), output_index_root=tmp_path / "bad_index",
    )
    assert failed.status == "FAILED"
    assert (tmp_path / "bad_index" / "INCOMPLETE.json").exists()


def test_external_symlink_source_is_rejected(tmp_path):
    source, external = tmp_path / "source", tmp_path / "external"
    _write_series(source)
    _write_series(external)
    link = source / "linked.pvd"
    try:
        link.symlink_to(external / "series.pvd")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Windows policy does not permit creating symlinks: {exc}")
    result = index_existing_aspect_series(
        trusted_source_root=source, pvd_relative_ref="linked.pvd", run_identity=_claim(),
        expected_source_inventory=_inventory(source), output_index_root=tmp_path / "symlink_index",
    )
    assert result.status == "FAILED"
    assert "symlink" in (result.message or "").lower() or "reparse" in (result.message or "").lower()


def test_duplicate_expected_inventory_refs_are_not_silently_accepted(tmp_path):
    source, output = tmp_path / "source", tmp_path / "index"
    _write_series(source)
    inventory = _inventory(source)
    inventory["extra.vtu"] = SourceDigest("extra.vtu", 0, "0" * 64)
    result = _build(source, output, inventory=inventory)
    assert result.status == "FAILED"
    assert (output / "INCOMPLETE.json").exists()
