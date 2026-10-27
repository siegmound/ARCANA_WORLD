"""Bounded, read-only reader for a single-piece ASPECT VTK snapshot series.

This adapter deliberately returns an experimental record, never a
``DomainStateEnvelope``. It supports only inline ASCII and inline base64
binary (uncompressed or VTK zlib-block compressed) XML VTK files.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import math
import re
import struct
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree as ET


CLASSIFICATION = "SYNTHETIC_ENGINEERING_ONLY"
_DTYPES: dict[str, tuple[str, int, bool]] = {
    "Float32": ("f", 4, True), "Float64": ("d", 8, True),
    "Int8": ("b", 1, False), "UInt8": ("B", 1, False),
    "Int16": ("h", 2, False), "UInt16": ("H", 2, False),
    "Int32": ("i", 4, False), "UInt32": ("I", 4, False),
    "Int64": ("q", 8, False), "UInt64": ("Q", 8, False),
}
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")


class SnapshotFormatError(ValueError):
    """The file is malformed or uses a VTK feature outside this contract."""


@dataclass(frozen=True)
class ReaderLimits:
    max_file_bytes: int = 64 * 1024 * 1024
    max_snapshots: int = 10_000
    max_points: int = 1_000_000
    max_cells: int = 1_000_000
    max_array_bytes: int = 32 * 1024 * 1024
    max_total_decoded_bytes: int = 96 * 1024 * 1024
    max_materialized_values: int = 1_500_000
    # Conservative estimate for Python numeric objects/references. This is a
    # guardrail, not an OS-enforced RSS quota.
    max_estimated_python_bytes: int = 96 * 1024 * 1024

    def __post_init__(self) -> None:
        if any(value <= 0 for value in asdict(self).values()):
            raise ValueError("all reader limits must be positive")


@dataclass(frozen=True)
class ArrayMetadata:
    name: str
    association: str
    vtk_type: str
    components: int
    tuples: int
    units: str | None


@dataclass(frozen=True)
class NumericArray:
    metadata: ArrayMetadata
    values: tuple[int | float, ...]


@dataclass(frozen=True)
class AspectSnapshotRecord:
    classification: str
    run_id: str
    mpi_rank_count: int
    snapshot_id: str
    ordinal: int
    time_value: float
    time_unit: str
    time_unit_source: str
    mesh_fingerprint: str
    field_metadata: tuple[ArrayMetadata, ...]
    precision_types: tuple[str, ...]
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class MeshValues:
    point_count: int
    cell_count: int
    coordinates: tuple[float, ...]
    connectivity: tuple[int, ...]
    offsets: tuple[int, ...]
    cell_types: tuple[int, ...]


@dataclass(frozen=True)
class AspectSnapshot:
    record: AspectSnapshotRecord
    mesh: MeshValues
    fields: Mapping[str, NumericArray]


@dataclass(frozen=True)
class SnapshotMetadata:
    ordinal: int
    time_value: float
    time_unit: str
    source_file: str
    snapshot_id: str
    mesh_fingerprint: str
    point_count: int
    cell_count: int
    cell_type_counts: Mapping[str, int]
    coordinate_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    file_sha256: Mapping[str, str]
    declared_provenance: Mapping[str, str]
    field_metadata: tuple[ArrayMetadata, ...]


@dataclass(frozen=True)
class SeriesAudit:
    classification: str
    run_id: str
    mpi_rank_count: int
    pvd_sha256: str
    declared_provenance: Mapping[str, str]
    snapshot_count: int
    snapshots: tuple[SnapshotMetadata, ...]
    mesh_stable: bool
    schema_stable: bool
    invariant_fields: tuple[str, ...]
    dynamic_fields: tuple[str, ...]
    zero_valued_invariant_fields: tuple[str, ...]
    field_annotations: Mapping[str, str]
    numerically_duplicate_fields: tuple[tuple[str, str], ...]
    time_gaps: tuple[float, ...]
    solver_completed_time: float | None
    final_snapshot_at_solver_completion: bool | None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_file(root: Path, parent: Path, relative: str, limits: ReaderLimits) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or not relative or "\\" in relative:
        raise SnapshotFormatError(f"invalid relative VTK path: {relative!r}")
    if any(part in (".", "..") for part in candidate.parts):
        raise SnapshotFormatError(f"path traversal is not allowed: {relative!r}")
    try:
        resolved = (parent / candidate).resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise SnapshotFormatError(f"VTK reference escapes the declared directory or is missing: {relative!r}") from exc
    if not resolved.is_file():
        raise SnapshotFormatError(f"VTK reference is not a file: {relative!r}")
    size = resolved.stat().st_size
    if size <= 0 or size > limits.max_file_bytes:
        raise SnapshotFormatError(f"file size outside configured limit: {relative!r} ({size} bytes)")
    return resolved


def _read_xml(path: Path) -> ET.Element:
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise SnapshotFormatError("DTD/entity declarations are not supported")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SnapshotFormatError(f"invalid XML in {path.name}: {exc}") from exc


def _required_int(element: ET.Element, key: str, *, minimum: int = 0) -> int:
    try:
        value = int(element.attrib[key])
    except (KeyError, ValueError) as exc:
        raise SnapshotFormatError(f"missing or invalid integer attribute {key}") from exc
    if value < minimum:
        raise SnapshotFormatError(f"attribute {key} must be >= {minimum}")
    return value


def _unpack_values(raw: bytes, vtk_type: str, byte_order: str) -> list[int | float]:
    code, size, is_float = _DTYPES[vtk_type]
    if len(raw) % size:
        raise SnapshotFormatError(f"byte length is not aligned for {vtk_type}")
    count = len(raw) // size
    prefix = "<" if byte_order == "LittleEndian" else ">"
    if count == 0:
        return []
    try:
        values = list(struct.unpack(f"{prefix}{count}{code}", raw))
    except struct.error as exc:
        raise SnapshotFormatError(f"could not decode {vtk_type} payload") from exc
    if is_float and not all(math.isfinite(value) for value in values):
        raise SnapshotFormatError("non-finite floating-point value in VTK array")
    return values


def _decode_binary(text: str, vtk_type: str, byte_order: str, header_type: str,
                   compressor: str | None, expected_bytes: int, limits: ReaderLimits) -> bytes:
    encoded = "".join(text.split())
    if len(encoded) > 2 * (limits.max_array_bytes + 1024 * 1024):
        raise SnapshotFormatError("base64 array text exceeds configured limit")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise SnapshotFormatError("invalid base64 VTK array") from exc
    code, header_size, _ = _DTYPES[header_type]
    prefix = "<" if byte_order == "LittleEndian" else ">"

    def read_header(offset: int) -> tuple[int, int]:
        if offset + header_size > len(payload):
            raise SnapshotFormatError("truncated VTK binary header")
        return struct.unpack_from(f"{prefix}{code}", payload, offset)[0], offset + header_size

    if compressor is None:
        length, data_offset = read_header(0)
        if length != expected_bytes or length > limits.max_array_bytes:
            raise SnapshotFormatError("VTK binary payload length disagrees with its declared shape")
        raw = payload[data_offset:]
        if len(raw) != length:
            raise SnapshotFormatError("truncated or trailing bytes in VTK binary array")
        return raw

    if compressor != "vtkZLibDataCompressor":
        raise SnapshotFormatError(f"unsupported VTK compressor {compressor!r}")
    blocks, offset = read_header(0)
    block_size, offset = read_header(offset)
    last_block_size, offset = read_header(offset)
    if blocks < 1 or blocks > limits.max_materialized_values or block_size < 1:
        raise SnapshotFormatError("invalid or excessive zlib block header")
    if last_block_size < 1 or last_block_size > block_size:
        raise SnapshotFormatError("invalid zlib last-block size")
    if (blocks - 1) * block_size + last_block_size != expected_bytes:
        raise SnapshotFormatError("zlib block sizes disagree with declared array shape")
    compressed_sizes: list[int] = []
    for _ in range(blocks):
        size, offset = read_header(offset)
        if size <= 0 or size > limits.max_file_bytes:
            raise SnapshotFormatError("invalid compressed block size")
        compressed_sizes.append(size)
    if sum(compressed_sizes) != len(payload) - offset:
        raise SnapshotFormatError("compressed block table disagrees with payload length")
    output = bytearray()
    for index, compressed_size in enumerate(compressed_sizes):
        expected_block = last_block_size if index == blocks - 1 else block_size
        compressed = payload[offset:offset + compressed_size]
        offset += compressed_size
        decoder = zlib.decompressobj()
        try:
            block = decoder.decompress(compressed, expected_block + 1)
            if len(block) > expected_block or decoder.unconsumed_tail:
                raise SnapshotFormatError("zlib block expands beyond its declared size")
        except zlib.error as exc:
            raise SnapshotFormatError("invalid zlib-compressed VTK block") from exc
        if len(block) != expected_block or not decoder.eof or decoder.unused_data:
            raise SnapshotFormatError("zlib block has an invalid decoded length or stream")
        if len(output) + len(block) > limits.max_array_bytes:
            raise SnapshotFormatError("decoded array exceeds configured limit")
        output.extend(block)
    if len(output) != expected_bytes:
        raise SnapshotFormatError("decoded zlib payload length mismatch")
    return bytes(output)


def _decode_array(element: ET.Element, *, association: str, tuple_count: int,
                  byte_order: str, header_type: str, compressor: str | None,
                  limits: ReaderLimits, budget: list[int]) -> NumericArray:
    name = element.attrib.get("Name")
    vtk_type = element.attrib.get("type")
    if not name or not _SAFE_ID.fullmatch(name):
        raise SnapshotFormatError("every numeric array needs a safe, non-empty Name")
    if vtk_type not in _DTYPES:
        raise SnapshotFormatError(f"unsupported VTK numeric type {vtk_type!r}")
    components = _required_int(element, "NumberOfComponents", minimum=1) if "NumberOfComponents" in element.attrib else 1
    if components > 64:
        raise SnapshotFormatError("component count exceeds configured safety bound")
    value_count = tuple_count * components
    code, type_size, is_float = _DTYPES[vtk_type]
    expected_bytes = value_count * type_size
    if expected_bytes <= 0 or expected_bytes > limits.max_array_bytes:
        raise SnapshotFormatError(f"array {name!r} exceeds configured decoded-size limit")
    budget[0] += expected_bytes
    budget[1] += value_count
    if budget[0] > limits.max_total_decoded_bytes:
        raise SnapshotFormatError("snapshot decoded bytes exceed configured limit")
    if budget[1] > limits.max_materialized_values or budget[1] * 40 > limits.max_estimated_python_bytes:
        raise SnapshotFormatError("snapshot Python materialization estimate exceeds configured limit")

    fmt = element.attrib.get("format", "ascii").lower()
    text = element.text or ""
    if fmt == "ascii":
        tokens = text.split()
        if len(tokens) != value_count:
            raise SnapshotFormatError(f"array {name!r} has {len(tokens)} values; expected {value_count}")
        try:
            values: list[int | float] = [float(token) for token in tokens] if is_float else [int(token, 10) for token in tokens]
        except ValueError as exc:
            raise SnapshotFormatError(f"invalid ASCII value in array {name!r}") from exc
        if is_float and not all(math.isfinite(value) for value in values):
            raise SnapshotFormatError(f"array {name!r} contains NaN or infinity")
        if is_float and vtk_type == "Float32":
            try:
                values = [struct.unpack("<f", struct.pack("<f", value))[0] for value in values]
            except (OverflowError, struct.error) as exc:
                raise SnapshotFormatError(f"array {name!r} contains a value outside Float32 range") from exc
        elif not is_float:
            bits = type_size * 8
            signed = vtk_type.startswith("Int")
            minimum = -(1 << (bits - 1)) if signed else 0
            maximum = (1 << (bits - (1 if signed else 0))) - 1
            if any(value < minimum or value > maximum for value in values):
                raise SnapshotFormatError(f"array {name!r} contains a value outside {vtk_type} range")
    elif fmt == "binary":
        raw = _decode_binary(text, vtk_type, byte_order, header_type, compressor,
                             expected_bytes, limits)
        values = _unpack_values(raw, vtk_type, byte_order)
    else:
        raise SnapshotFormatError(f"unsupported DataArray format {fmt!r}")
    metadata = ArrayMetadata(name, association, vtk_type, components, tuple_count,
                             element.attrib.get("Units") or element.attrib.get("units"))
    return NumericArray(metadata, tuple(values))


def _mesh_summary(mesh: MeshValues) -> tuple[Mapping[str, int], tuple[tuple[float, float], tuple[float, float], tuple[float, float]]]:
    counts: dict[str, int] = {}
    for cell_type in mesh.cell_types:
        key = str(cell_type)
        counts[key] = counts.get(key, 0) + 1
    axes = tuple(tuple(mesh.coordinates[index::3]) for index in range(3))
    bounds = tuple((min(axis), max(axis)) for axis in axes)
    return counts, bounds  # type: ignore[return-value]


def _canonical_mesh_fingerprint(mesh: MeshValues) -> str:
    digest = hashlib.sha256(b"ARCANA-ASPECT-MESH-NUMERIC-V1\0")
    digest.update(struct.pack("<QQQ", mesh.point_count, mesh.cell_count, len(mesh.connectivity)))
    for value in mesh.coordinates:
        digest.update(struct.pack("<d", value))
    for value in mesh.connectivity:
        digest.update(struct.pack("<q", value))
    for value in mesh.offsets:
        digest.update(struct.pack("<q", value))
    for value in mesh.cell_types:
        digest.update(struct.pack("<B", value))
    return digest.hexdigest()


def _parse_vtu(path: Path, limits: ReaderLimits) -> tuple[MeshValues, dict[str, NumericArray], str, str]:
    root = _read_xml(path)
    if root.tag != "VTKFile" or root.attrib.get("type") != "UnstructuredGrid":
        raise SnapshotFormatError("VTU root must declare type=UnstructuredGrid")
    if "AppendedData" in root.attrib or root.find("AppendedData") is not None:
        raise SnapshotFormatError("VTK appended data are not supported")
    byte_order = root.attrib.get("byte_order", "LittleEndian")
    if byte_order not in ("LittleEndian", "BigEndian"):
        raise SnapshotFormatError("unsupported VTK byte_order")
    header_type = root.attrib.get("header_type", "UInt32")
    if header_type not in ("UInt32", "UInt64"):
        raise SnapshotFormatError("header_type must be UInt32 or UInt64")
    compressor = root.attrib.get("compressor")
    if compressor not in (None, "", "vtkZLibDataCompressor"):
        raise SnapshotFormatError(f"unsupported VTK compressor {compressor!r}")
    if compressor == "":
        compressor = None
    grid = root.find("UnstructuredGrid")
    pieces = [] if grid is None else grid.findall("Piece")
    if grid is None or len(pieces) != 1:
        raise SnapshotFormatError("only one UnstructuredGrid Piece per VTU is supported")
    piece = pieces[0]
    point_count = _required_int(piece, "NumberOfPoints", minimum=1)
    cell_count = _required_int(piece, "NumberOfCells", minimum=1)
    if point_count > limits.max_points or cell_count > limits.max_cells:
        raise SnapshotFormatError("point/cell count exceeds configured limit")
    budget = [0, 0]

    points_node = piece.find("Points")
    point_arrays = [] if points_node is None else points_node.findall("DataArray")
    if len(point_arrays) != 1:
        raise SnapshotFormatError("Points must contain exactly one DataArray")
    point_array = _decode_array(point_arrays[0], association="points", tuple_count=point_count,
                                byte_order=byte_order, header_type=header_type,
                                compressor=compressor, limits=limits, budget=budget)
    if point_array.metadata.components != 3 or point_array.metadata.vtk_type not in ("Float32", "Float64"):
        raise SnapshotFormatError("point coordinates must be 3-component Float32/Float64")
    coordinates = tuple(float(value) for value in point_array.values)

    cells_node = piece.find("Cells")
    if cells_node is None:
        raise SnapshotFormatError("VTU Piece is missing Cells")
    cell_arrays = cells_node.findall("DataArray")
    by_name = {array.attrib.get("Name"): array for array in cell_arrays}
    if len(cell_arrays) != 3 or set(by_name) != {"connectivity", "offsets", "types"}:
        raise SnapshotFormatError("Cells must contain connectivity, offsets and types arrays")
    if any(by_name[name].attrib.get("NumberOfComponents", "1") != "1"
           for name in ("connectivity", "offsets", "types")):
        raise SnapshotFormatError("cell topology arrays must be scalar")
    conn_count = _array_tuple_count(by_name["connectivity"], limits, byte_order, header_type, compressor)
    conn = _decode_array(by_name["connectivity"], association="cells", tuple_count=conn_count,
                         byte_order=byte_order, header_type=header_type, compressor=compressor, limits=limits, budget=budget)
    offs = _decode_array(by_name["offsets"], association="cells", tuple_count=cell_count,
                         byte_order=byte_order, header_type=header_type, compressor=compressor, limits=limits, budget=budget)
    types = _decode_array(by_name["types"], association="cells", tuple_count=cell_count,
                          byte_order=byte_order, header_type=header_type, compressor=compressor, limits=limits, budget=budget)
    if any(array.metadata.components != 1 or array.metadata.vtk_type.startswith("Float") for array in (conn, offs, types)):
        raise SnapshotFormatError("cell topology arrays must use scalar integer types")
    connectivity = tuple(int(value) for value in conn.values)
    offsets = tuple(int(value) for value in offs.values)
    cell_types = tuple(int(value) for value in types.values)
    previous = 0
    for offset in offsets:
        if offset <= previous or offset > len(connectivity):
            raise SnapshotFormatError("cell offsets must be strictly increasing and within connectivity")
        previous = offset
    if offsets[-1] != len(connectivity):
        raise SnapshotFormatError("final cell offset must equal connectivity length")
    if any(index < 0 or index >= point_count for index in connectivity):
        raise SnapshotFormatError("connectivity contains an out-of-range point index")
    if any(cell_type <= 0 or cell_type > 255 for cell_type in cell_types):
        raise SnapshotFormatError("invalid VTK cell type")
    mesh = MeshValues(point_count, cell_count, coordinates, connectivity, offsets, cell_types)

    fields: dict[str, NumericArray] = {}
    for association, count in (("point", point_count), ("cell", cell_count)):
        container = piece.find("PointData" if association == "point" else "CellData")
        if container is None:
            continue
        for element in container.findall("DataArray"):
            array = _decode_array(element, association=association, tuple_count=count,
                                  byte_order=byte_order, header_type=header_type,
                                  compressor=compressor, limits=limits, budget=budget)
            key = f"{association}:{array.metadata.name}"
            if key in fields:
                raise SnapshotFormatError(f"duplicate field name {key!r}")
            fields[key] = array

    return mesh, fields, _canonical_mesh_fingerprint(mesh), point_array.metadata.vtk_type


def _array_tuple_count(element: ET.Element, limits: ReaderLimits, byte_order: str,
                       header_type: str, compressor: str | None) -> int:
    """Infer flat connectivity tuple count from its bounded payload shape."""
    vtk_type = element.attrib.get("type")
    if vtk_type not in _DTYPES:
        raise SnapshotFormatError("unsupported connectivity numeric type")
    _, size, _ = _DTYPES[vtk_type]
    fmt = element.attrib.get("format", "ascii").lower()
    if fmt == "ascii":
        count = len((element.text or "").split())
    elif fmt == "binary":
        # The expected decoded byte length is not stored separately for a flat
        # connectivity array; decode its single base64 header to obtain it.
        # Re-encoding/decoding is bounded by the source file-size limit.
        encoded = "".join((element.text or "").split())
        try:
            payload = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise SnapshotFormatError("invalid base64 connectivity array") from exc
        count = _binary_payload_length(payload, byte_order, header_type, compressor, limits) // size
    else:
        raise SnapshotFormatError(f"unsupported DataArray format {fmt!r}")
    if count <= 0 or count * size > limits.max_array_bytes:
        raise SnapshotFormatError("connectivity array exceeds configured limit")
    return count


def _binary_payload_length(payload: bytes, byte_order: str, header_type: str,
                           compressor: str | None, limits: ReaderLimits) -> int:
    # Cell arrays are decoded again by _decode_binary; this helper reads only
    # the binary header to derive the number of connectivity entries.
    code, size, _ = _DTYPES[header_type]
    endian = "<" if byte_order == "LittleEndian" else ">"
    if len(payload) < size:
        raise SnapshotFormatError("truncated connectivity header")
    first = struct.unpack_from(f"{endian}{code}", payload, 0)[0]
    if compressor is None:
        return first
    if compressor != "vtkZLibDataCompressor" or len(payload) < size * 3:
        raise SnapshotFormatError("unsupported or truncated compressed connectivity header")
    blocks = first
    block_size = struct.unpack_from(f"{endian}{code}", payload, size)[0]
    last_size = struct.unpack_from(f"{endian}{code}", payload, size * 2)[0]
    if blocks < 1 or blocks > limits.max_materialized_values or block_size < 1 or last_size < 1 or last_size > block_size:
        raise SnapshotFormatError("invalid compressed connectivity header")
    return (blocks - 1) * block_size + last_size


def _parse_pvtu(path: Path, root_dir: Path, limits: ReaderLimits) -> tuple[Path, tuple[tuple[str, str, int], ...], tuple[str, int]]:
    root = _read_xml(path)
    if root.tag != "VTKFile" or root.attrib.get("type") != "PUnstructuredGrid":
        raise SnapshotFormatError("PVTU root must declare type=PUnstructuredGrid")
    if "AppendedData" in root.attrib or root.find("AppendedData") is not None:
        raise SnapshotFormatError("PVTU appended data are not supported")
    grid = root.find("PUnstructuredGrid")
    pieces = [] if grid is None else grid.findall("Piece")
    if len(pieces) != 1 or not pieces[0].attrib.get("Source"):
        raise SnapshotFormatError("only one PVTU Piece Source is supported")
    source = pieces[0].attrib["Source"]
    if Path(source).suffix.lower() != ".vtu":
        raise SnapshotFormatError("PVTU Piece Source must reference a .vtu file")
    child = _safe_file(root_dir, path.parent, source, limits)
    declarations: list[tuple[str, str, int]] = []
    for container_name, association in (("PPointData", "point"), ("PCellData", "cell")):
        container = grid.find(container_name)
        if container is not None:
            for item in container.findall("PDataArray"):
                name, vtk_type = item.attrib.get("Name"), item.attrib.get("type")
                if not name or not vtk_type or vtk_type not in _DTYPES:
                    raise SnapshotFormatError("invalid PVTU PDataArray declaration")
                try:
                    components = int(item.attrib.get("NumberOfComponents", "1"))
                except ValueError as exc:
                    raise SnapshotFormatError("invalid PVTU component count") from exc
                if components < 1 or components > 64:
                    raise SnapshotFormatError("PVTU component count outside limit")
                declarations.append((f"{association}:{name}", vtk_type, components))
    points = grid.find("PPoints")
    point_arrays = [] if points is None else points.findall("PDataArray")
    if len(point_arrays) != 1:
        raise SnapshotFormatError("PVTU PPoints must declare exactly one coordinate array")
    point_type = point_arrays[0].attrib.get("type")
    try:
        point_components = int(point_arrays[0].attrib.get("NumberOfComponents", "1"))
    except ValueError as exc:
        raise SnapshotFormatError("invalid PVTU coordinate component count") from exc
    if point_type not in ("Float32", "Float64") or point_components != 3:
        raise SnapshotFormatError("PVTU coordinates must declare three Float32/Float64 components")
    return child, tuple(declarations), (point_type, point_components)


class AspectSnapshotSeries:
    """Read-only PVD series reader with a fixed synthetic-evidence class."""

    def __init__(self, pvd_path: str | Path, *, run_id: str, time_unit: str,
                 time_unit_source: str, mpi_rank_count: int,
                 limits: ReaderLimits | None = None,
                 solver_completed_time: float | None = None,
                 experiment_provenance: Mapping[str, str] | None = None):
        if not _SAFE_ID.fullmatch(run_id):
            raise ValueError("run_id must be a non-empty stable identifier")
        if mpi_rank_count != 1:
            raise SnapshotFormatError("only a caller-verified one-rank output is supported")
        if not time_unit.strip() or not time_unit_source.strip():
            raise ValueError("time_unit and its source must be declared explicitly")
        if solver_completed_time is not None and not math.isfinite(solver_completed_time):
            raise ValueError("solver_completed_time must be finite")
        self.limits = limits or ReaderLimits()
        supplied = Path(pvd_path)
        if supplied.is_symlink():
            # A PVD symlink obscures the declared directory boundary.
            raise SnapshotFormatError("PVD symlink is not accepted")
        try:
            self.pvd_path = supplied.resolve(strict=True)
        except OSError as exc:
            raise SnapshotFormatError("PVD file does not exist") from exc
        if not self.pvd_path.is_file():
            raise SnapshotFormatError("PVD path must be a file")
        self.root_dir = self.pvd_path.parent.resolve(strict=True)
        if self.pvd_path.stat().st_size > self.limits.max_file_bytes:
            raise SnapshotFormatError("PVD file exceeds configured size limit")
        self.run_id = run_id
        self.mpi_rank_count = mpi_rank_count
        self.time_unit = time_unit
        self.time_unit_source = time_unit_source
        self.solver_completed_time = solver_completed_time
        declared = dict(experiment_provenance or {})
        if any(not _SAFE_ID.fullmatch(key) or not isinstance(value, str) or not value.strip()
               for key, value in declared.items()):
            raise ValueError("experiment_provenance must contain safe keys and non-empty string values")
        self.experiment_provenance = declared
        self.pvd_sha256 = _sha256(self.pvd_path)
        self._entries = self._read_collection()
        if solver_completed_time is not None and solver_completed_time < self._entries[-1][0]:
            raise ValueError("solver_completed_time cannot precede the last PVD snapshot")

    def _read_collection(self) -> tuple[tuple[float, Path, Path | None, tuple[tuple[str, str, int], ...], tuple[str, int] | None], ...]:
        root = _read_xml(self.pvd_path)
        if root.tag != "VTKFile" or root.attrib.get("type") != "Collection":
            raise SnapshotFormatError("PVD root must declare type=Collection")
        collection = root.find("Collection")
        datasets = [] if collection is None else collection.findall("DataSet")
        if not datasets or len(datasets) > self.limits.max_snapshots:
            raise SnapshotFormatError("PVD has no datasets or exceeds snapshot count limit")
        entries = []
        previous_time = -math.inf
        for dataset in datasets:
            try:
                time_value = float(dataset.attrib["timestep"])
            except (KeyError, ValueError) as exc:
                raise SnapshotFormatError("PVD DataSet requires a numeric timestep") from exc
            if not math.isfinite(time_value) or time_value <= previous_time:
                raise SnapshotFormatError("PVD timesteps must be finite and strictly increasing")
            previous_time = time_value
            if dataset.attrib.get("group", "") not in ("", "__default__"):
                raise SnapshotFormatError("non-default PVD groups are not supported")
            if dataset.attrib.get("part", "0") != "0":
                raise SnapshotFormatError("only PVD part 0 is supported")
            source = dataset.attrib.get("file", "")
            suffix = Path(source).suffix.lower()
            if suffix not in (".vtu", ".pvtu"):
                raise SnapshotFormatError("PVD references must end in .vtu or .pvtu")
            resolved = _safe_file(self.root_dir, self.pvd_path.parent, source, self.limits)
            pvtu_path = resolved if suffix == ".pvtu" else None
            declarations: tuple[tuple[str, str, int], ...] = ()
            point_declaration: tuple[str, int] | None = None
            vtu_path = resolved
            if pvtu_path is not None:
                vtu_path, declarations, point_declaration = _parse_pvtu(pvtu_path, self.root_dir, self.limits)
            entries.append((time_value, vtu_path, pvtu_path, declarations, point_declaration))
        return tuple(entries)

    @property
    def snapshot_count(self) -> int:
        return len(self._entries)

    def times(self) -> tuple[float, ...]:
        return tuple(entry[0] for entry in self._entries)

    def read_snapshot(self, ordinal: int) -> AspectSnapshot:
        if not isinstance(ordinal, int) or ordinal < 0 or ordinal >= len(self._entries):
            raise IndexError("snapshot ordinal out of range")
        time_value, vtu_path, pvtu_path, declarations, point_declaration = self._entries[ordinal]
        mesh, fields, fingerprint, coordinate_dtype = _parse_vtu(vtu_path, self.limits)
        metadata = tuple(array.metadata for array in fields.values())
        if pvtu_path is not None:
            actual = tuple(sorted((key, array.metadata.vtk_type, array.metadata.components)
                                  for key, array in fields.items()))
            if tuple(sorted(declarations)) != actual:
                raise SnapshotFormatError("PVTU field declarations disagree with referenced VTU")
        if point_declaration is not None and point_declaration != (coordinate_dtype, 3):
            raise SnapshotFormatError("PVTU coordinate declaration disagrees with referenced VTU")
        file_hashes: dict[str, str] = {
            vtu_path.relative_to(self.root_dir).as_posix(): _sha256(vtu_path),
            self.pvd_path.relative_to(self.root_dir).as_posix(): self.pvd_sha256,
        }
        if pvtu_path is not None:
            file_hashes[pvtu_path.relative_to(self.root_dir).as_posix()] = _sha256(pvtu_path)
        snapshot_id = hashlib.sha256(json.dumps({
            "run_id": self.run_id, "mpi_rank_count": self.mpi_rank_count,
            "ordinal": ordinal, "time": time_value,
            "source": vtu_path.relative_to(self.root_dir).as_posix(), "mesh": fingerprint,
            "files": file_hashes, "declared_provenance": self.experiment_provenance,
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        record = AspectSnapshotRecord(
            classification=CLASSIFICATION, run_id=self.run_id, snapshot_id=snapshot_id,
            mpi_rank_count=self.mpi_rank_count, ordinal=ordinal,
            time_value=time_value, time_unit=self.time_unit,
            time_unit_source=self.time_unit_source, mesh_fingerprint=fingerprint,
            field_metadata=metadata,
            precision_types=tuple(sorted({item.vtk_type for item in metadata} | {"coordinates:" + coordinate_dtype})),
            provenance={"file_sha256": file_hashes, "declared": dict(self.experiment_provenance)},
        )
        return AspectSnapshot(record, mesh, fields)

    def metadata(self) -> tuple[SnapshotMetadata, ...]:
        rows = []
        for ordinal, (time_value, vtu_path, pvtu_path, _, _) in enumerate(self._entries):
            snapshot = self.read_snapshot(ordinal)
            hashes = dict(snapshot.record.provenance["file_sha256"])
            type_counts, bounds = _mesh_summary(snapshot.mesh)
            rows.append(SnapshotMetadata(
                ordinal, time_value, self.time_unit, vtu_path.relative_to(self.root_dir).as_posix(),
                snapshot.record.snapshot_id, snapshot.record.mesh_fingerprint,
                snapshot.mesh.point_count, snapshot.mesh.cell_count, type_counts, bounds,
                hashes, dict(self.experiment_provenance), snapshot.record.field_metadata,
            ))
        return tuple(rows)

    def audit(self) -> SeriesAudit:
        rows: list[SnapshotMetadata] = []
        fingerprints: set[str] = set()
        schemas: set[tuple[tuple[str, str, str, int, str | None], ...]] = set()
        first_values: dict[str, tuple[int | float, ...]] | None = None
        invariant_candidates: set[str] = set()
        dynamic: set[str] = set()
        zero_valued_invariants: set[str] = set()
        duplicate_candidates: set[tuple[str, str]] | None = None
        for ordinal in range(self.snapshot_count):
            snap = self.read_snapshot(ordinal)
            time_value, vtu_path, pvtu_path, _, _ = self._entries[ordinal]
            file_hashes = dict(snap.record.provenance["file_sha256"])
            type_counts, bounds = _mesh_summary(snap.mesh)
            rows.append(SnapshotMetadata(
                ordinal, time_value, self.time_unit, vtu_path.relative_to(self.root_dir).as_posix(),
                snap.record.snapshot_id, snap.record.mesh_fingerprint,
                snap.mesh.point_count, snap.mesh.cell_count, type_counts, bounds,
                file_hashes, dict(self.experiment_provenance), snap.record.field_metadata,
            ))
            fingerprints.add(snap.record.mesh_fingerprint)
            schemas.add(tuple(sorted((f.name, f.association, f.vtk_type, f.components, f.units)
                                     for f in snap.record.field_metadata)))
            current = {key: value.values for key, value in snap.fields.items()}
            if first_values is None:
                first_values = current
                invariant_candidates = set(current)
                zero_valued_invariants = {key for key, values in current.items()
                                           if values and all(value == 0 for value in values)}
            else:
                for key in invariant_candidates.copy():
                    if key not in current or current[key] != first_values[key]:
                        invariant_candidates.discard(key)
                        zero_valued_invariants.discard(key)
                        dynamic.add(key)
                dynamic.update(set(current) - set(first_values))
            current_pairs: set[tuple[str, str]] = set()
            keys = list(snap.fields)
            for i, first in enumerate(keys):
                for second in keys[i + 1:]:
                    if snap.fields[first].values == snap.fields[second].values:
                        current_pairs.add(tuple(sorted((first, second))))
            duplicate_candidates = current_pairs if duplicate_candidates is None else duplicate_candidates & current_pairs
        times = self.times()
        final_match = None if self.solver_completed_time is None else times[-1] == self.solver_completed_time
        return SeriesAudit(
            CLASSIFICATION, self.run_id, self.mpi_rank_count, self.pvd_sha256,
            dict(self.experiment_provenance),
            self.snapshot_count, tuple(rows),
            len(fingerprints) == 1, len(schemas) == 1,
            tuple(sorted(invariant_candidates)), tuple(sorted(dynamic)),
            tuple(sorted(zero_valued_invariants)),
            ({"point:T": "Observed constant zero; discrepancy from the initial expression remains unexplained."}
             if "point:T" in zero_valued_invariants else {}),
            tuple(sorted(duplicate_candidates or set())),
            tuple(times[i + 1] - times[i] for i in range(len(times) - 1)),
            self.solver_completed_time, final_match,
        )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of a single-piece ASPECT PVD/PVTU/VTU series")
    parser.add_argument("pvd", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mpi-rank-count", required=True, type=int, choices=(1,),
                        help="only rank-count 1 is accepted; this is caller-supplied provenance")
    parser.add_argument("--time-unit", required=True, help="unit as declared by the caller; no conversion is performed")
    parser.add_argument("--time-unit-source", required=True, help="provenance for the declared time unit")
    parser.add_argument("--solver-completed-time", type=float)
    parser.add_argument("--provenance", action="append", default=[], metavar="KEY=VALUE",
                        help="caller-declared run/build provenance; preserved as an unauthenticated claim")
    args = parser.parse_args(argv)
    declared: dict[str, str] = {}
    for item in args.provenance:
        key, separator, value = item.partition("=")
        if not separator or key in declared:
            parser.error("--provenance must be unique KEY=VALUE entries")
        declared[key] = value
    series = AspectSnapshotSeries(
        args.pvd, run_id=args.run_id, time_unit=args.time_unit,
        time_unit_source=args.time_unit_source, mpi_rank_count=args.mpi_rank_count,
        solver_completed_time=args.solver_completed_time,
        experiment_provenance=declared,
    )
    print(json.dumps(_jsonable(series.audit()), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI exercised by invocation
    raise SystemExit(main())
