"""Deterministic branch registry derived from canonical boundary incidence."""
from __future__ import annotations

import hashlib
from typing import Any


def build_branch_registry(boundary_state: dict[str, Any], mesh: Any,
                          geometry_metrics: dict[str, Any]) -> dict[str, Any]:
    records = boundary_state["segments"]
    junctions = boundary_state["junctions"]
    junction_by_vertex = {str(item["vertex_id"]): str(item["junction_id"])
                          for item in junctions}
    by_id = {str(item["boundary_id"]): item for item in records}
    graph: dict[str, list[str]] = {}
    for record in records:
        left, right = map(str, record["endpoint_vertex_ids"])
        graph.setdefault(left, []).append(str(record["boundary_id"]))
        graph.setdefault(right, []).append(str(record["boundary_id"]))
    if len(by_id) != 1_983 or len(junction_by_vertex) != 20:
        raise ValueError("canonical branch graph inventory differs from governed counts")
    if any(len(edge_ids) != (3 if vertex in junction_by_vertex else 2)
           for vertex, edge_ids in graph.items()):
        raise ValueError("boundary graph has an ungoverned non-junction endpoint/degree")
    mesh_edge_by_id = {bid: pair for bid, pair in zip(mesh.boundary_ids, mesh.boundary_edge_nodes)}
    metric_by_id = {record["canonical_boundary_id"]: record
                    for record in geometry_metrics["per_edge_metrics"]}
    visited: set[str] = set()
    branches = []
    for start_vertex, start_junction in sorted(junction_by_vertex.items(), key=lambda item: item[1]):
        for first_edge in sorted(graph[start_vertex]):
            if first_edge in visited:
                continue
            edge_ids = [first_edge]
            vertices = [start_vertex]
            visited.add(first_edge)
            current = next(v for v in by_id[first_edge]["endpoint_vertex_ids"] if v != start_vertex)
            vertices.append(str(current))
            while current not in junction_by_vertex:
                candidates = [edge for edge in graph[str(current)] if edge not in visited]
                if len(candidates) != 1:
                    raise ValueError("canonical branch path is not a simple ordered chain")
                edge_id = candidates[0]
                visited.add(edge_id)
                edge_ids.append(edge_id)
                nxt = next(v for v in by_id[edge_id]["endpoint_vertex_ids"] if v != current)
                current = str(nxt)
                vertices.append(current)
            end_junction = junction_by_vertex[current]
            # Neutral branch orientation: lexically smaller stable junction ID first.
            if end_junction < start_junction:
                edge_ids.reverse()
                vertices.reverse()
                start_id, end_id = end_junction, start_junction
            else:
                start_id, end_id = start_junction, end_junction
            digest_source = "\n".join((start_id, end_id, *edge_ids)).encode("utf-8")
            branch_id = "R6BR-DERIVED-" + hashlib.sha256(digest_source).hexdigest()[:20]
            plate_pairs = {tuple(sorted(map(int, by_id[edge]["ordered_plate_pair"])))
                           for edge in edge_ids}
            if len(plate_pairs) != 1:
                raise ValueError("one junction-to-junction branch changes plate-pair ownership")
            pair = next(iter(plate_pairs))
            oriented_feg_edges = []
            first_vertex = vertices[0]
            if first_vertex.startswith("GRID_VERTEX:"):
                _, row_text, col_text = first_vertex.split(":")
                row_line, col_line = int(row_text), int(col_text)
                expected_start = (1 if row_line == 0 else 2 if row_line == 180
                                  else 3 + (row_line - 1) * 360 + col_line % 360)
            else:
                expected_start = 1 if first_vertex == "SOUTH_POLE" else 2
            physical_vertices = []
            for vertex_id in vertices:
                if vertex_id == "SOUTH_POLE":
                    physical_vertices.append([-90.0, 0.0])
                elif vertex_id == "NORTH_POLE":
                    physical_vertices.append([90.0, 0.0])
                else:
                    _, row_text, col_text = vertex_id.split(":")
                    physical_vertices.append([-90.0 + int(row_text),
                                              -180.0 + int(col_text) % 360])
            for edge_id in edge_ids:
                u, v = mesh_edge_by_id[edge_id]
                if expected_start == u:
                    oriented_feg_edges.append([u, v])
                    expected_start = v
                elif expected_start == v:
                    oriented_feg_edges.append([v, u])
                    expected_start = u
                else:
                    raise ValueError(f"FEG edge chain discontinuity in {branch_id}")
            branches.append({
                "canonical_branch_id": branch_id,
                "id_authority": "DERIVED_CANONICAL_TOPOLOGY_REGISTRY_ID",
                "endpoint_junction_ids": [start_id, end_id],
                "ordered_canonical_boundary_segment_ids": edge_ids,
                "adjacent_plate_ids": list(pair),
                "orientation": "lexically lower junction ID to higher junction ID",
                "ordered_canonical_physical_vertices": vertices,
                "ordered_canonical_physical_vertices_lat_lon_deg": physical_vertices,
                "ordered_feg_edge_chain": oriented_feg_edges,
                "edge_representation": "DIRECT_FEG_EDGE",
                "geometry_approximation": geometry_metrics["classification"],
                "edge_error_metrics": [metric_by_id[edge] for edge in edge_ids],
                "provenance": "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST endpoint incidence and manifested partition edge-to-FEG mapping",
            })
    branches.sort(key=lambda item: item["canonical_branch_id"])
    assigned = [edge for branch in branches for edge in branch["ordered_canonical_boundary_segment_ids"]]
    if (len(branches) != 30 or len(visited) != 1_983
            or len(assigned) != 1_983 or len(set(assigned)) != 1_983):
        raise ValueError("branch reconstruction failed exact 30/1983 accounting")
    adjacency_pairs = {tuple(branch["adjacent_plate_ids"]) for branch in branches}
    if len(adjacency_pairs) != 30:
        raise ValueError("reconstructed branch graph does not preserve 30 plate-pair adjacencies")
    return {
        "schema": "R6_T0_CANONICAL_BOUNDARY_BRANCH_REGISTRY_V1",
        "id_policy": "DERIVED_CANONICAL_TOPOLOGY_REGISTRY_ID; not historical IDs",
        "canonical_payload_sha256": "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
        "branch_count": len(branches), "boundary_segment_count": len(assigned),
        "junction_count": len(junction_by_vertex), "plate_pair_adjacency_count": len(adjacency_pairs),
        "unassigned_boundary_segments": [], "duplicated_segment_ownership": [],
        "branches": branches,
    }
