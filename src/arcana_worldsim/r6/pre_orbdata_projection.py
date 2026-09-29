"""Cell-to-FEG numerical support projection with deterministic cell ownership."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

import numpy as np


@dataclass(frozen=True)
class FEGHeatFlowProjection:
    node_count: int
    node_heat_flow_w_m2: tuple[float | None, ...]
    numerical_owner_domain_id: tuple[int | None, ...]
    lineage: tuple[dict[str, Any], ...]
    source_lineage: dict[str, str]
    source_classification: str = "NUMERICAL_DERIVED_SUPPORT"
    serialized_authority: str = "NUMERICAL_RUNTIME_INPUT_ONLY"

    @property
    def replay_sha256(self) -> str:
        body = {"node_count": self.node_count,
                "node_heat_flow_w_m2": self.node_heat_flow_w_m2,
                "numerical_owner_domain_id": self.numerical_owner_domain_id,
                "lineage": self.lineage,
                "source_lineage": self.source_lineage,
                "source_classification": self.source_classification,
                "serialized_authority": self.serialized_authority,
                "projection_rule": "LEXICOGRAPHIC_FIRST_INCIDENT_CELL",
                "physical_resolution_promotion": False,
                "smoothing": "NONE"}
        return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                       allow_nan=False).encode()).hexdigest()

    def serialized_payload(self) -> dict[str, Any]:
        if self.node_count != 64_442:
            raise ValueError("FEG_NODE_COUNT_NOT_GOVERNED")
        if any(v is None for v in self.node_heat_flow_w_m2):
            raise ValueError("FEG_UNKNOWN_HEAT_FLOW_CANNOT_ENTER_ORBDATA")
        if any(v == 0.0 for v in self.node_heat_flow_w_m2):
            raise ValueError("FEG_ZERO_SENTINEL_FOR_PHYSICAL_NODE_FORBIDDEN")
        return {"schema": "R6_PRE_ORBDATA_FEG_HEAT_FLOW_NUMERICAL_INPUT_V1",
                "authority": "NUMERICAL_RUNTIME_INPUT_ONLY",
                "classification": "NUMERICAL_DERIVED_SUPPORT",
                "node_count": self.node_count,
                "node_unknown_count": 0,
                "heat_flow_w_m2": list(self.node_heat_flow_w_m2),
                "lineage": list(self.lineage),
                "source_lineage": dict(sorted(self.source_lineage.items())),
                "projection_rule": "LEXICOGRAPHIC_FIRST_INCIDENT_CELL",
                "smoothing": "NONE", "averaging": "NONE", "interpolation": "NONE",
                "physical_resolution_promotion": False,
                "replay_sha256": self.replay_sha256}


def project_heat_flow_to_feg(mesh, face_rows: np.ndarray, face_cols: np.ndarray,
                             heat_flow_w_m2: np.ndarray, physical_domain_id: np.ndarray,
                             *, source_lineage: dict[str, str],
                             cell_validity: np.ndarray | None = None,
                             owner_cell_fields: Mapping[str, np.ndarray] | None = None,
                             expected_nodes: int = 64_442) -> FEGHeatFlowProjection:
    q = np.asarray(heat_flow_w_m2, dtype=np.float64)
    domain = np.asarray(physical_domain_id)
    rows = np.asarray(face_rows, dtype=np.int64)
    cols = np.asarray(face_cols, dtype=np.int64)
    if q.shape != domain.shape or rows.shape != cols.shape:
        raise ValueError("FEG_PROJECTION_PARENT_SHAPE_MISMATCH")
    validity = (np.ones(q.shape, dtype=bool) if cell_validity is None
                else np.asarray(cell_validity, dtype=bool))
    if validity.shape != q.shape:
        raise ValueError("FEG_PROJECTION_VALIDITY_SHAPE_MISMATCH")
    owner_arrays = {str(name): np.asarray(values)
                    for name, values in (owner_cell_fields or {}).items()}
    if any(values.shape != q.shape for values in owner_arrays.values()):
        raise ValueError("FEG_OWNER_FIELD_SHAPE_MISMATCH")
    if any(not name for name in owner_arrays):
        raise ValueError("FEG_OWNER_FIELD_NAME_MISSING")
    if not source_lineage or any(not k or not v for k, v in source_lineage.items()):
        raise ValueError("FEG_PROJECTION_LINEAGE_MISSING")
    if rows.size and (np.any(rows < 0) or np.any(cols < 0) or
                      np.any(rows >= q.shape[0]) or np.any(cols >= q.shape[1])):
        raise ValueError("FEG_PARENT_CELL_INDEX_OUT_OF_RANGE")
    if len(mesh.vertices_lat_lon) != expected_nodes:
        raise ValueError("FEG_NODE_COUNT_MISMATCH")
    if (len(mesh.triangle_parent_face) != len(mesh.triangles) or
            np.any(mesh.triangle_parent_face < 0) or
            np.any(mesh.triangle_parent_face >= len(rows))):
        raise ValueError("FEG_PARENT_CELL_LINEAGE_INCOMPLETE")

    incident = [set() for _ in range(expected_nodes)]
    for triangle, face in zip(mesh.triangles, mesh.triangle_parent_face):
        for node in triangle:
            incident[int(node) - 1].add(int(face))
    if any(not faces for faces in incident):
        raise ValueError("FEG_NODE_WITHOUT_PARENT_CELL")

    def json_scalar(value: Any) -> Any:
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, float) and not np.isfinite(value):
            return None
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        raise ValueError("FEG_OWNER_FIELD_VALUE_NOT_JSON_SCALAR")

    values: list[float | None] = []
    owner_domains: list[int | None] = []
    lineage: list[dict[str, Any]] = []
    for node_id, faces in enumerate(incident, 1):
        cells = sorted({(int(rows[f]), int(cols[f])) for f in faces})
        categories = {int(domain[r, c]) for r, c in cells}
        all_valid = all(validity[r, c] and np.isfinite(q[r, c]) and q[r, c] > 0 and
                        int(domain[r, c]) in {1, 2, 3, 4, 5, 6} for r, c in cells)
        # Numerical ownership does not create a canonical physical node domain.
        owner = cells[0] if all_valid else None
        owner_domain = int(domain[owner]) if owner is not None else None
        values.append(float(q[owner]) if owner is not None else None)
        owner_domains.append(owner_domain)
        owner_runtime_branch = (json_scalar(owner_arrays["runtime_branch"][owner])
                                if owner is not None and "runtime_branch" in owner_arrays else None)
        owner_material_binding = (json_scalar(owner_arrays["material_configuration_binding"][owner])
                                  if owner is not None and "material_configuration_binding" in owner_arrays else None)
        owner_thermal_class = (json_scalar(owner_arrays["continental_thermal_domain_id"][owner])
                               if owner is not None and "continental_thermal_domain_id" in owner_arrays else None)
        lineage.append({
            "node_id": node_id,
            "incident_parent_cells_row_col": [list(cell) for cell in cells],
            "incident_physical_domain_ids": sorted(categories),
            "mixed_physical_support": len(categories) > 1,
            "numerical_owner_cell_row_col": list(owner) if owner is not None else None,
            "numerical_owner_domain_id": owner_domain,
            "numerical_owner_runtime_branch": owner_runtime_branch,
            "numerical_owner_thermal_class_id": owner_thermal_class,
            "numerical_owner_material_configuration_binding": owner_material_binding,
            "rule": "LEXICOGRAPHIC_FIRST_INCIDENT_CELL",
            "status": "NUMERICAL_DERIVED_SUPPORT" if all_valid else "UNKNOWN_INVALID_INCIDENT_SUPPORT",
            "physical_resolution_promotion": False,
            "smoothing": "NONE", "averaging": "NONE", "interpolation": "NONE"})

    return FEGHeatFlowProjection(expected_nodes, tuple(values), tuple(owner_domains),
                                 tuple(lineage), dict(sorted(source_lineage.items())))


def merge_projection_with_cell_state(projection: FEGHeatFlowProjection,
                                     cell_state: Mapping[str, Any]) -> dict[str, Any]:
    """Merge cell metadata without allowing it to overwrite node/source lineage."""
    protected = {"lineage", "source_lineage", "node_count", "node_unknown_count",
                 "numerical_owner_domain_id", "incident_physical_domain_ids",
                 "mixed_physical_support", "heat_flow_w_m2", "replay_sha256"}
    collision = protected.intersection(cell_state)
    if collision:
        raise ValueError(f"FEG_PROJECTION_METADATA_COLLISION:{','.join(sorted(collision))}")
    payload = projection.serialized_payload()
    payload.update(dict(cell_state))
    return payload
