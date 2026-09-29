"""Cell-to-FEG numerical support projection with categorical fail-closed edges."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

import numpy as np


@dataclass(frozen=True)
class FEGHeatFlowProjection:
    node_count: int
    node_heat_flow_w_m2: tuple[float | None, ...]
    node_domain_id: tuple[int | None, ...]
    lineage: tuple[dict[str, Any], ...]
    source_classification: str = "NUMERICAL_DERIVED_SUPPORT"
    serialized_authority: str = "NUMERICAL_RUNTIME_INPUT_ONLY"

    @property
    def replay_sha256(self) -> str:
        body = {"node_count": self.node_count,
                "node_heat_flow_w_m2": self.node_heat_flow_w_m2,
                "node_domain_id": self.node_domain_id,
                "lineage": self.lineage,
                "source_classification": self.source_classification,
                "serialized_authority": self.serialized_authority,
                "physical_resolution_promotion": False,
                "smoothing": "NONE"}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

    def serialized_payload(self) -> dict[str, Any]:
        if self.node_count != 64_442:
            raise ValueError("FEG_NODE_COUNT_NOT_GOVERNED")
        if any(v == 0.0 for v in self.node_heat_flow_w_m2 if v is not None):
            raise ValueError("FEG_ZERO_SENTINEL_FOR_PHYSICAL_NODE_FORBIDDEN")
        return {"schema":"R6_PRE_ORBDATA_FEG_HEAT_FLOW_NUMERICAL_INPUT_V1",
                "authority":"NUMERICAL_RUNTIME_INPUT_ONLY",
                "classification":"NUMERICAL_DERIVED_SUPPORT",
                "node_count":self.node_count,
                "heat_flow_w_m2":list(self.node_heat_flow_w_m2),
                "physical_domain_id":list(self.node_domain_id),
                "lineage":list(self.lineage),
                "validity_mask_separate":True,
                "smoothing":"NONE",
                "physical_resolution_promotion":False,
                "replay_sha256":self.replay_sha256}


def project_heat_flow_to_feg(mesh, face_rows: np.ndarray, face_cols: np.ndarray,
                             heat_flow_w_m2: np.ndarray, physical_domain_id: np.ndarray,
                             *, source_lineage: dict[str,str], expected_nodes: int=64_442
                             ) -> FEGHeatFlowProjection:
    q=np.asarray(heat_flow_w_m2,dtype=np.float64)
    domain=np.asarray(physical_domain_id)
    rows=np.asarray(face_rows,dtype=np.int64); cols=np.asarray(face_cols,dtype=np.int64)
    if q.shape != domain.shape or rows.shape != cols.shape:
        raise ValueError("FEG_PROJECTION_PARENT_SHAPE_MISMATCH")
    if not source_lineage or any(not k or not v for k,v in source_lineage.items()):
        raise ValueError("FEG_PROJECTION_LINEAGE_MISSING")
    if rows.size and (np.any(rows<0) or np.any(cols<0) or
                      np.any(rows>=q.shape[0]) or np.any(cols>=q.shape[1])):
        raise ValueError("FEG_PARENT_CELL_INDEX_OUT_OF_RANGE")
    if len(mesh.vertices_lat_lon) != expected_nodes:
        raise ValueError("FEG_NODE_COUNT_MISMATCH")
    if len(mesh.triangle_parent_face) != len(mesh.triangles) or np.any(mesh.triangle_parent_face<0) or np.any(mesh.triangle_parent_face>=len(rows)):
        raise ValueError("FEG_PARENT_CELL_LINEAGE_INCOMPLETE")
    incident=[set() for _ in range(expected_nodes)]
    for triangle, face in zip(mesh.triangles,mesh.triangle_parent_face):
        for node in triangle: incident[int(node)-1].add(int(face))
    if any(not faces for faces in incident): raise ValueError("FEG_NODE_WITHOUT_PARENT_CELL")
    values=[]; domains=[]; lineage=[]
    for node_id,faces in enumerate(incident,1):
        cells=sorted({(int(rows[f]),int(cols[f])) for f in faces})
        cats={int(domain[r,c]) for r,c in cells}
        all_known=all(np.isfinite(q[r,c]) and q[r,c]>0 and int(domain[r,c]) in {1,2,3,4,5,6} for r,c in cells)
        homogeneous=len(cats)==1 and all_known
        # Exact unanimity is a categorical node rule. Mixed support is UNKNOWN;
        # no continent/ocean average or arbitrary class selection is made.
        selected=cells[0] if homogeneous else None
        values.append(float(q[selected]) if selected else None)
        domains.append(int(domain[selected]) if selected else None)
        lineage.append({"node_id":node_id,"incident_parent_cells_row_col":[list(x) for x in cells],
                        "selected_parent_cell_row_col":list(selected) if selected else None,
                        "rule":"LEXICOGRAPHIC_FIRST_CELL_WITH_HOMOGENEOUS_DOMAIN_SUPPORT",
                        "incident_domain_ids":sorted(cats),"status":"NUMERICAL_DERIVED_SUPPORT" if homogeneous else "UNKNOWN_MIXED_OR_INVALID_SUPPORT",
                        "parent_lineage":dict(sorted(source_lineage.items())),
                        "physical_resolution_promotion":False,"smoothing":"NONE"})
    return FEGHeatFlowProjection(expected_nodes,tuple(values),tuple(domains),tuple(lineage))
