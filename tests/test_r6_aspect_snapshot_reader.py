from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
import sys
import zlib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from arcana_worldsim.r6.adapters.aspect_snapshot_reader import (  # noqa: E402
    CLASSIFICATION,
    AspectSnapshotSeries,
    ReaderLimits,
    SnapshotFormatError,
    main,
)


POINTS = (0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 1.0, 0.0, 0.0, 1.0, 0.0)
CONNECTIVITY = (0, 1, 2, 3)
OFFSETS = (4,)
CELL_TYPES = (9,)


def _raw(kind: str, values: tuple[int | float, ...], endian: str = "<") -> bytes:
    fmt = {"Float32": "f", "Float64": "d", "Int32": "i", "UInt8": "B"}[kind]
    return struct.pack(endian + str(len(values)) + fmt, *values)


def _binary_text(kind: str, values: tuple[int | float, ...], compressed: bool,
                 endian: str = "<", header_type: str = "UInt32", segmented: bool = False,
                 multi_block: bool = False,
                 header_override: tuple[int, ...] | None = None,
                 data_override: bytes | None = None) -> str:
    raw = _raw(kind, values, endian)
    if compressed:
        if multi_block and len(raw) > 1 and data_override is None:
            split = len(raw) // 2
            raw_blocks = (raw[:split], raw[split:])
            packed_blocks = tuple(zlib.compress(block) for block in raw_blocks)
            header_values = (2, split, len(raw_blocks[-1]), *(len(block) for block in packed_blocks))
            data = b"".join(packed_blocks)
        else:
            packed = zlib.compress(raw) if data_override is None else data_override
            header_values = (1, len(raw), len(raw), len(packed))
            data = packed
    else:
        header_values = (len(raw),)
        data = raw
    if header_override is not None:
        header_values = header_override
    header_code = "I" if header_type == "UInt32" else "Q"
    header = struct.pack(endian + str(len(header_values)) + header_code, *header_values)
    if segmented:
        return (base64.b64encode(header) + base64.b64encode(data)).decode("ascii")
    return base64.b64encode(header + data).decode("ascii")


def _da(name: str | None, kind: str, values: tuple[int | float, ...], components: int = 1,
        mode: str = "ascii", compressed: bool = False, units: str | None = None,
        endian: str = "<", header_type: str = "UInt32", segmented: bool = False,
        multi_block: bool = False,
        header_override: tuple[int, ...] | None = None, data_override: bytes | None = None) -> str:
    attrs = f'type="{kind}" NumberOfComponents="{components}" format="{mode}"'
    if name is not None:
        attrs = f'Name="{name}" ' + attrs
    if units is not None:
        attrs += f' Units="{units}"'
    if mode == "ascii":
        body = " ".join(str(v) for v in values)
    else:
        body = _binary_text(kind, values, compressed, endian, header_type, segmented,
                            multi_block, header_override, data_override)
    return f"<DataArray {attrs}>{body}</DataArray>"


def _write_vtu(path: Path, *, mode: str = "ascii", compressed: bool = False,
               segmented: bool = False, header_type: str = "UInt32",
               multi_block_connectivity: bool = False,
               time_state: int = 0, corrupt: str | None = None,
               byte_order: str = "LittleEndian") -> None:
    endian = "<" if byte_order == "LittleEndian" else ">"
    points = _da("Points", "Float32", POINTS, 3, mode, compressed, endian=endian,
                 header_type=header_type, segmented=segmented)
    connectivity = _da("connectivity", "Int32", CONNECTIVITY, 1, mode, compressed, endian=endian,
                       header_type=header_type, segmented=segmented,
                       multi_block=multi_block_connectivity)
    offsets = _da("offsets", "Int32", OFFSETS, 1, mode, compressed, endian=endian,
                  header_type=header_type, segmented=segmented)
    cell_types = _da("types", "UInt8", CELL_TYPES, 1, mode, compressed, endian=endian,
                     header_type=header_type, segmented=segmented)
    velocity = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) if time_state == 0 else (1, 0, 0) * 4
    temperature = (0, 0, 0, 0)
    if corrupt == "nan":
        temperature = (0, float("nan"), 0, 0)
    if corrupt == "bad_connection":
        connectivity = _da("connectivity", "Int32", (0, 1, 2, 99), 1, mode, compressed,
                           endian=endian, header_type=header_type, segmented=segmented)
    point_fields = "".join((
        _da("velocity", "Float32", velocity, 3, mode, compressed, "m/s", endian,
            header_type, segmented),
        _da("p", "Float32", (2, 2, 2, 2) if time_state == 0 else (3, 3, 3, 3), 1, mode, compressed,
            "Pa", endian, header_type, segmented),
        _da("density", "Float32", (3300, 3300, 3300, 3300), 1, mode, compressed,
            "kg/m^3", endian, header_type, segmented),
        _da("density_comp", "Float32", (3300, 3300, 3300, 3300), 1, mode, compressed,
            "kg/m^3", endian, header_type, segmented),
        _da("T", "Float32", temperature, 1, mode, compressed, "K", endian, header_type, segmented),
        _da("viscosity", "Float32", (1, 1, 1, 1), 1, mode, compressed,
            "Pa s", endian, header_type, segmented),
        _da("stress", "Float64", (1, 2, 3, 4) if time_state else (0, 0, 0, 0), 1, mode, compressed,
            "Pa", endian, header_type, segmented),
    ))
    if corrupt == "appended":
        points = _da("Points", "Float32", POINTS, 3, "appended")
    if corrupt in {"bad_zlib", "bad_header", "bad_block_size", "bad_block_count", "bad_padding",
                    "truncated", "zlib_truncated", "zlib_trailing"}:
        raw = _raw("Float32", POINTS, endian)
        packed = zlib.compress(raw)
        header = (1, len(raw), len(raw), len(packed))
        if corrupt == "bad_zlib":
            packed = packed[:-1] + bytes((packed[-1] ^ 0xFF,))
        elif corrupt == "zlib_truncated":
            packed = packed[:-1]
        elif corrupt == "zlib_trailing":
            packed += b"unexpected trailing byte"
        elif corrupt == "bad_header":
            header = (1, len(raw), len(raw) + 1, len(packed))
        elif corrupt == "bad_block_size":
            header = (1, len(raw), len(raw), len(packed) + 1)
        elif corrupt == "bad_block_count":
            header = (2**32 - 1, len(raw), len(raw), len(packed))
        binary = _binary_text("Float32", POINTS, True, endian, header_type, segmented,
                              header_override=header, data_override=packed)
        if corrupt == "bad_padding":
            if "=" not in binary[:-2]:
                raise AssertionError("fixture requires separately padded header")
            binary = binary.replace("=", "A", 1)
        elif corrupt == "truncated":
            binary = binary[:-2]
        points = f'<DataArray Name="Points" type="Float32" NumberOfComponents="3" format="binary">{binary}</DataArray>'
    if corrupt == "unnamed_points":
        points = points.replace('Name="Points" ', "", 1)
    if corrupt == "unnamed_field":
        point_fields = point_fields.replace('Name="p" ', "", 1)
    header_attr = f' header_type="{header_type}"'
    xml = (f'<VTKFile type="UnstructuredGrid" version="1.0" byte_order="{byte_order}"{header_attr}'
           f'{" compressor=\"vtkZLibDataCompressor\"" if compressed or corrupt in {"bad_zlib", "bad_header", "bad_block_size", "bad_padding", "truncated"} else ""}>'
           f'<UnstructuredGrid><Piece NumberOfPoints="4" NumberOfCells="1">'
           f'<PointData>{point_fields}</PointData><CellData>{_da("material_id", "Int32", (1,), 1, mode, compressed, endian=endian, header_type=header_type, segmented=segmented)}</CellData>'
           f'<Points>{points}</Points><Cells>{connectivity}{offsets}{cell_types}</Cells>'
           f'</Piece></UnstructuredGrid></VTKFile>')
    if corrupt == "appended_root":
        xml = xml.replace("version=\"1.0\"", "version=\"1.0\" AppendedData=\"raw\"")
    path.write_text(xml, encoding="utf-8")

def _write_pvd(path: Path, entries: list[tuple[float, str]]) -> None:
    datasets = "".join(f'<DataSet timestep="{time}" group="" part="0" file="{name}"/>'
                       for time, name in entries)
    path.write_text(f'<VTKFile type="Collection" version="1.0"><Collection>{datasets}</Collection></VTKFile>', encoding="utf-8")


def _series(tmp_path: Path, modes: tuple[tuple[str, bool], ...] = (("ascii", False), ("binary", False), ("binary", True))):
    entries = []
    for index, (mode, compressed) in enumerate(modes):
        name = f"state_{index}.vtu"
        _write_vtu(tmp_path / name, mode=mode, compressed=compressed, time_state=index)
        entries.append((float(index), name))
    pvd = tmp_path / "series.pvd"
    _write_pvd(pvd, entries)
    return AspectSnapshotSeries(pvd, run_id="rigid_shear_test", time_unit="s",
                                time_unit_source="fixture declaration", mpi_rank_count=1,
                                solver_completed_time=3.0)


@pytest.mark.parametrize("mode,compressed", [("ascii", False), ("binary", False), ("binary", True)])
def test_ascii_binary_and_zlib_decode_geometry_fields_and_precision(tmp_path, mode, compressed):
    _write_vtu(tmp_path / "state.vtu", mode=mode, compressed=compressed, time_state=1)
    _write_pvd(tmp_path / "series.pvd", [(0.25, "state.vtu")])
    series = AspectSnapshotSeries(tmp_path / "series.pvd", run_id="fixture_run", time_unit="s",
                                  time_unit_source="fixture input", mpi_rank_count=1)
    snapshot = series.read_snapshot(0)
    assert snapshot.record.classification == CLASSIFICATION
    assert snapshot.record.time_value == 0.25
    assert snapshot.record.time_unit == "s"
    assert snapshot.mesh.point_count == 4
    assert snapshot.mesh.cell_count == 1
    assert snapshot.mesh.coordinates == POINTS
    assert snapshot.mesh.connectivity == CONNECTIVITY
    assert snapshot.mesh.offsets == OFFSETS
    assert snapshot.mesh.cell_types == CELL_TYPES
    assert snapshot.fields["point:velocity"].metadata.components == 3
    assert snapshot.fields["point:velocity"].metadata.units == "m/s"
    assert snapshot.fields["point:velocity"].values[:3] == (1.0, 0.0, 0.0)
    assert snapshot.fields["point:stress"].metadata.vtk_type == "Float64"
    assert snapshot.fields["point:stress"].values == (1.0, 2.0, 3.0, 4.0)
    assert snapshot.fields["cell:material_id"].values == (1,)
    assert "coordinates:Float32" in snapshot.record.precision_types
    assert len(snapshot.record.mesh_fingerprint) == 64
    other = tmp_path / "other_encoding"
    other.mkdir()
    _write_vtu(other / "state.vtu", mode="ascii", time_state=1)
    _write_pvd(other / "series.pvd", [(0.25, "state.vtu")])
    other_snapshot = AspectSnapshotSeries(other / "series.pvd", run_id="other", time_unit="s",
                                          time_unit_source="fixture input", mpi_rank_count=1).read_snapshot(0)
    assert snapshot.record.mesh_fingerprint == other_snapshot.record.mesh_fingerprint


def test_big_endian_inline_binary_decodes_numeric_values(tmp_path):
    _write_vtu(tmp_path / "big.vtu", mode="binary", time_state=1, byte_order="BigEndian")
    _write_pvd(tmp_path / "series.pvd", [(0.0, "big.vtu")])
    snapshot = AspectSnapshotSeries(tmp_path / "series.pvd", run_id="big_endian", time_unit="s",
                                    time_unit_source="fixture input", mpi_rank_count=1).read_snapshot(0)
    assert snapshot.mesh.connectivity == CONNECTIVITY
    assert snapshot.fields["point:p"].values == (3.0, 3.0, 3.0, 3.0)


@pytest.mark.parametrize(
    "header_type,byte_order,compressed",
    [("UInt32", "LittleEndian", False), ("UInt64", "BigEndian", True)],
)
def test_segmented_base64_and_unnamed_points_decode_without_fabricating_metadata(
    tmp_path, header_type, byte_order, compressed
):
    _write_vtu(tmp_path / "segmented.vtu", mode="binary", compressed=compressed,
               segmented=True, header_type=header_type, byte_order=byte_order,
               multi_block_connectivity=compressed,
               corrupt="unnamed_points", time_state=1)
    _write_pvd(tmp_path / "series.pvd", [(0.0, "segmented.vtu")])
    series = AspectSnapshotSeries(tmp_path / "series.pvd", run_id="segmented", time_unit="s",
                                  time_unit_source="fixture", mpi_rank_count=1)
    snapshot = series.read_snapshot(0)
    assert snapshot.mesh.coordinates == POINTS
    assert snapshot.mesh.coordinate_source_name is None
    assert snapshot.mesh.connectivity == CONNECTIVITY
    assert snapshot.fields["point:velocity"].values[:3] == (1.0, 0.0, 0.0)
    endian = "<" if byte_order == "LittleEndian" else ">"
    assert snapshot.mesh.coordinate_sha256_bytes == hashlib.sha256(
        _raw("Float32", POINTS, endian)
    ).hexdigest()
    assert snapshot.fields["point:velocity"].metadata.sha256_bytes == hashlib.sha256(
        _raw("Float32", (1, 0, 0) * 4, endian)
    ).hexdigest()
    audit_row = series.audit().snapshots[0]
    assert audit_row.coordinate_source_name is None
    assert audit_row.coordinate_vtk_type == "Float32"
    assert audit_row.coordinate_sha256_bytes == snapshot.mesh.coordinate_sha256_bytes
    velocity_metadata = next(item for item in audit_row.field_metadata if item.name == "velocity")
    assert velocity_metadata.sha256_bytes == snapshot.fields["point:velocity"].metadata.sha256_bytes


@pytest.mark.parametrize("corrupt", ["bad_header", "bad_block_size", "bad_block_count", "bad_padding",
                                     "truncated", "zlib_truncated", "zlib_trailing"])
def test_segmented_base64_rejects_corrupt_header_padding_and_payload(tmp_path, corrupt):
    _write_vtu(tmp_path / "bad.vtu", mode="binary", compressed=True, segmented=True,
               header_type="UInt64", byte_order="BigEndian", corrupt=corrupt)
    _write_pvd(tmp_path / "bad.pvd", [(0.0, "bad.vtu")])
    series = AspectSnapshotSeries(tmp_path / "bad.pvd", run_id="bad", time_unit="s",
                                  time_unit_source="fixture", mpi_rank_count=1)
    with pytest.raises(SnapshotFormatError):
        series.read_snapshot(0)


def test_physical_array_without_name_remains_rejected(tmp_path):
    _write_vtu(tmp_path / "bad.vtu", corrupt="unnamed_field")
    _write_pvd(tmp_path / "bad.pvd", [(0.0, "bad.vtu")])
    series = AspectSnapshotSeries(tmp_path / "bad.pvd", run_id="bad", time_unit="s",
                                  time_unit_source="fixture", mpi_rank_count=1)
    with pytest.raises(SnapshotFormatError, match="Name"):
        series.read_snapshot(0)


def test_series_reports_stable_mesh_schema_invariants_duplicates_and_no_completion_snapshot(tmp_path):
    series = _series(tmp_path)
    audit = series.audit()
    assert audit.classification == "SYNTHETIC_ENGINEERING_ONLY"
    assert audit.snapshot_count == 3
    assert tuple(row.time_value for row in audit.snapshots) == (0.0, 1.0, 2.0)
    assert audit.mesh_stable and audit.schema_stable
    assert audit.snapshots[0].point_count == 4
    assert audit.snapshots[0].cell_count == 1
    assert audit.snapshots[0].cell_type_counts == {"9": 1}
    assert audit.snapshots[0].coordinate_bounds == ((0.0, 2.0), (0.0, 1.0), (0.0, 0.0))
    assert "point:T" in audit.invariant_fields
    assert "point:T" in audit.zero_valued_invariant_fields
    assert audit.field_annotations["point:T"] == "Observed constant zero; discrepancy from the initial expression remains unexplained."
    assert "point:viscosity" in audit.invariant_fields
    assert "point:p" in audit.dynamic_fields
    assert "point:velocity" in audit.dynamic_fields
    assert ("point:density", "point:density_comp") in audit.numerically_duplicate_fields
    assert audit.time_gaps == (1.0, 1.0)
    assert audit.final_snapshot_at_solver_completion is False
    assert audit.solver_completed_time == 3.0


def test_solver_completion_time_does_not_create_a_final_snapshot(tmp_path):
    series = _series(tmp_path, (("ascii", False), ("ascii", False)))
    # Rebuild the collection with the observed nonterminal snapshot time. The
    # later solver completion is metadata only, never a fabricated field set.
    _write_pvd(tmp_path / "series.pvd", [(0.0, "state_0.vtu"), (1.0142299266, "state_1.vtu")])
    series = AspectSnapshotSeries(tmp_path / "series.pvd", run_id="reported_rigid_shear", time_unit="s",
                                 time_unit_source="FAIR operator-reported audit",
                                 mpi_rank_count=1,
                                 solver_completed_time=1.098612289)
    audit = series.audit()
    assert series.times() == (0.0, 1.0142299266)
    assert audit.final_snapshot_at_solver_completion is False
    assert audit.snapshots[-1].time_value == 1.0142299266


def test_file_hashes_and_mesh_fingerprint_are_deterministic_and_no_input_is_mutated(tmp_path):
    series = _series(tmp_path, (("binary", True),))
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir()}
    first = series.read_snapshot(0)
    second = series.read_snapshot(0)
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in tmp_path.iterdir()}
    assert before == after
    assert first.record.snapshot_id == second.record.snapshot_id
    assert first.record.mesh_fingerprint == second.record.mesh_fingerprint
    assert first.record.provenance["file_sha256"]["state_0.vtu"] == before["state_0.vtu"]


def test_rejects_non_monotonic_and_duplicate_timestamps(tmp_path):
    _write_vtu(tmp_path / "a.vtu")
    _write_pvd(tmp_path / "bad.pvd", [(1, "a.vtu"), (1, "a.vtu")])
    with pytest.raises(SnapshotFormatError, match="strictly increasing"):
        AspectSnapshotSeries(tmp_path / "bad.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1)


@pytest.mark.parametrize("corrupt,match,mode,compressed", [
    ("nan", "NaN or infinity", "ascii", False),
    ("bad_connection", "out-of-range", "ascii", False),
    ("appended", "format", "ascii", False),
    ("appended_root", "appended data", "ascii", False),
    ("bad_zlib", "zlib block|zlib-compressed", "binary", True),
])
def test_rejects_corrupt_or_unsupported_vtu(tmp_path, corrupt, match, mode, compressed):
    _write_vtu(tmp_path / "bad.vtu", corrupt=corrupt, mode=mode, compressed=compressed)
    _write_pvd(tmp_path / "bad.pvd", [(0, "bad.vtu")])
    series = AspectSnapshotSeries(tmp_path / "bad.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1)
    with pytest.raises(SnapshotFormatError, match=match):
        series.read_snapshot(0)


def test_rejects_pvd_path_traversal(tmp_path):
    root = tmp_path / "series"
    root.mkdir()
    _write_vtu(root / "local.vtu")
    _write_vtu(tmp_path / "outside.vtu")
    _write_pvd(root / "series.pvd", [(0, "../outside.vtu")])
    with pytest.raises(SnapshotFormatError, match="traversal"):
        AspectSnapshotSeries(root / "series.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1)


def test_rejects_external_symlink_reference(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.vtu"
    _write_vtu(outside)
    link = root / "linked.vtu"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        if os.name == "nt":
            pytest.skip(f"Windows symlink creation is unavailable: {exc}")
        raise
    _write_pvd(root / "series.pvd", [(0, "linked.vtu")])
    with pytest.raises(SnapshotFormatError, match="escapes"):
        AspectSnapshotSeries(root / "series.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1)


def test_pvtu_single_piece_reads_matching_vtu_schema(tmp_path):
    _write_vtu(tmp_path / "piece.vtu", mode="binary", time_state=1)
    declarations = ''.join(
        f'<PDataArray type="{vtk_type}" Name="{name}" NumberOfComponents="{components}"/>'
        for name, components, vtk_type in (("velocity", 3, "Float32"), ("p", 1, "Float32"),
                                           ("density", 1, "Float32"), ("density_comp", 1, "Float32"),
                                           ("T", 1, "Float32"), ("viscosity", 1, "Float32"),
                                           ("stress", 1, "Float64"))
    )
    pvtu = tmp_path / "state.pvtu"
    pvtu.write_text(f'<VTKFile type="PUnstructuredGrid" version="1.0"><PUnstructuredGrid GhostLevel="0"><PPointData>{declarations}</PPointData><PCellData><PDataArray type="Int32" Name="material_id"/></PCellData><PPoints><PDataArray type="Float32" NumberOfComponents="3"/></PPoints><Piece Source="piece.vtu"/></PUnstructuredGrid></VTKFile>', encoding="utf-8")
    _write_pvd(tmp_path / "series.pvd", [(0.0, "state.pvtu")])
    assert AspectSnapshotSeries(tmp_path / "series.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1).read_snapshot(0).mesh.cell_count == 1
    pvtu.write_text(pvtu.read_text(encoding="utf-8").replace('Source="piece.vtu"', 'Source="../piece.vtu"'), encoding="utf-8")
    with pytest.raises(SnapshotFormatError, match="traversal"):
        AspectSnapshotSeries(tmp_path / "series.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1).read_snapshot(0)


def test_rejects_pvtu_multipiece_and_memory_over_limit(tmp_path):
    _write_vtu(tmp_path / "piece.vtu")
    (tmp_path / "state.pvtu").write_text('<VTKFile type="PUnstructuredGrid"><PUnstructuredGrid><Piece Source="piece.vtu"/><Piece Source="piece.vtu"/></PUnstructuredGrid></VTKFile>', encoding="utf-8")
    _write_pvd(tmp_path / "multi.pvd", [(0, "state.pvtu")])
    with pytest.raises(SnapshotFormatError, match="one PVTU Piece"):
        AspectSnapshotSeries(tmp_path / "multi.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1)
    _write_pvd(tmp_path / "single.pvd", [(0, "piece.vtu")])
    series = AspectSnapshotSeries(tmp_path / "single.pvd", run_id="x", time_unit="s", time_unit_source="test",
                                  mpi_rank_count=1, limits=ReaderLimits(max_array_bytes=16))
    with pytest.raises(SnapshotFormatError, match="decoded-size limit"):
        series.read_snapshot(0)


def test_rejects_wrong_field_cardinality_and_missing_file(tmp_path):
    _write_vtu(tmp_path / "state.vtu")
    path = tmp_path / "state.vtu"
    path.write_text(path.read_text(encoding="utf-8").replace(
        '0 0 0 0</DataArray><DataArray Name="viscosity"',
        '0 0</DataArray><DataArray Name="viscosity"',
    ), encoding="utf-8")
    _write_pvd(tmp_path / "series.pvd", [(0, "state.vtu")])
    with pytest.raises(SnapshotFormatError, match="expected 4"):
        AspectSnapshotSeries(tmp_path / "series.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1).read_snapshot(0)
    _write_pvd(tmp_path / "missing.pvd", [(0, "absent.vtu")])
    with pytest.raises(SnapshotFormatError, match="missing"):
        AspectSnapshotSeries(tmp_path / "missing.pvd", run_id="x", time_unit="s", time_unit_source="test", mpi_rank_count=1)


def test_audit_reports_mesh_and_schema_changes_instead_of_assuming_stability(tmp_path):
    _write_vtu(tmp_path / "a.vtu", time_state=0)
    _write_vtu(tmp_path / "b.vtu", time_state=1)
    second = tmp_path / "b.vtu"
    second.write_text(second.read_text(encoding="utf-8").replace("2.0 0.0 0.0", "2.25 0.0 0.0", 1)
                      .replace('<DataArray Name="stress" type="Float64" NumberOfComponents="1" format="ascii" Units="Pa">1 2 3 4</DataArray>', ""),
                      encoding="utf-8")
    _write_pvd(tmp_path / "series.pvd", [(0, "a.vtu"), (1, "b.vtu")])
    audit = AspectSnapshotSeries(tmp_path / "series.pvd", run_id="varying", time_unit="s",
                                 time_unit_source="fixture", mpi_rank_count=1).audit()
    assert audit.mesh_stable is False
    assert audit.schema_stable is False


def test_cli_emits_metadata_without_materializing_arrays_in_json(tmp_path, capsys):
    series = _series(tmp_path, (("ascii", False),))
    assert main([str(series.pvd_path), "--run-id", "cli_fixture", "--mpi-rank-count", "1", "--time-unit", "s",
                 "--time-unit-source", "fixture contract"]) == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["classification"] == CLASSIFICATION
    assert payload["snapshot_count"] == 1
    assert '"values"' not in output


def test_external_provenance_is_recorded_as_a_caller_claim(tmp_path):
    _write_vtu(tmp_path / "state.vtu")
    _write_pvd(tmp_path / "series.pvd", [(0, "state.vtu")])
    series = AspectSnapshotSeries(
        tmp_path / "series.pvd", run_id="external_claim", time_unit="s",
        time_unit_source="PVD operator declaration",
        mpi_rank_count=1,
        experiment_provenance={"aspect_commit": "30eb77ee5da186137d436dbad35c6cb3cab64b69",
                               "authority": "operator-reported"},
    )
    record = series.read_snapshot(0).record
    assert record.provenance["declared"]["authority"] == "operator-reported"
    assert series.audit().declared_provenance["aspect_commit"] == "30eb77ee5da186137d436dbad35c6cb3cab64b69"


def test_rejects_unqualified_multi_rank_output(tmp_path):
    _write_vtu(tmp_path / "state.vtu")
    _write_pvd(tmp_path / "series.pvd", [(0.0, "state.vtu")])
    with pytest.raises(SnapshotFormatError, match="one-rank"):
        AspectSnapshotSeries(tmp_path / "series.pvd", run_id="multi_rank", time_unit="s",
                             time_unit_source="fixture declaration", mpi_rank_count=4)
