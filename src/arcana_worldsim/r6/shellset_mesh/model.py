"""ARCANA's normalized in-memory subset of the ShellSet FEG model."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class NodeRecord:
    node_id: int
    longitude_deg: float
    latitude_deg: float
    elevation_m: float
    heat_flow_w_m2: float
    crustal_thickness_m: float | None = None
    mantle_lithosphere_thickness_m: float | None = None
    chemical_density_anomaly_kg_m3: float | None = None
    cooling_curvature_k_m2: float | None = None


@dataclass(frozen=True)
class ElementRecord:
    element_id: int
    node_ids: tuple[int, int, int]
    lr_id: int | None = None


@dataclass(frozen=True)
class FaultRecord:
    fault_id: int
    node_ids: tuple[int, int, int, int]
    dip1_deg: float
    dip2_deg: float
    past_offset_m: float
    lr_id: int | None = None


@dataclass(frozen=True)
class PhysicalFieldBinding:
    """Explicit per-node physical values; never synthesized by the writer."""

    values_by_node_id: Mapping[int, tuple[float, ...]]
    authority: str


@dataclass(frozen=True)
class FEGModel:
    title: str
    mode: str
    nodes: tuple[NodeRecord, ...]
    elements: tuple[ElementRecord, ...]
    faults: tuple[FaultRecord, ...]
    n_fake_nodes: int = 0
    n1000: int = 0
    brief: int = 0
    fixture_status: tuple[str, ...] = ()


def model_from_mesh(mesh, field_binding: PhysicalFieldBinding, *,
                    title: str, mode: str = "SHELLS_READY",
                    fixture_status: tuple[str, ...] = ()) -> FEGModel:
    """Bind numerical geometry to explicit caller-supplied nodal state."""
    if mode not in {"PRE_ORBDATA", "SHELLS_READY"}:
        raise ValueError(f"unsupported FEG mode {mode}")
    if field_binding.authority == "TEST_FIXTURE_ONLY":
        required = {"TEST_FIXTURE_ONLY", "NOT_CANONICAL", "NOT_WORLD_HISTORY", "NOT_PRODUCTION_INPUT"}
        if not required.issubset(set(fixture_status)):
            raise ValueError("test fixture FEG must carry all noncanonical status flags")
    field_count = 2 if mode == "PRE_ORBDATA" else 6
    if set(field_binding.values_by_node_id) != set(range(1, len(mesh.vertices_lat_lon) + 1)):
        raise ValueError("physical field binding must cover every mesh node exactly")
    nodes = []
    for node_id, (lat, lon) in enumerate(mesh.vertices_lat_lon, 1):
        values = tuple(float(v) for v in field_binding.values_by_node_id[node_id])
        if len(values) != field_count:
            raise ValueError(f"{mode} binding requires {field_count} explicit physical values per node")
        if mode == "PRE_ORBDATA":
            nodes.append(NodeRecord(node_id, float(lon), float(lat), values[0], values[1]))
        else:
            nodes.append(NodeRecord(node_id, float(lon), float(lat), *values))
    elements = tuple(ElementRecord(i, tuple(map(int, tri)))
                     for i, tri in enumerate(mesh.triangles, 1))
    fixture = tuple(sorted(set(fixture_status)))
    return FEGModel(title, mode, tuple(nodes), elements, (), fixture_status=fixture)
