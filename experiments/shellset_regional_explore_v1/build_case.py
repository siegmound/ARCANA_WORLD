"""Extract a bounded, fault-free ARCANA T0 case and its experimental PRE reader."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from arcana_worldsim.r6.shellset_mesh.coordinates import rotation_matrices, _unit_vectors
from arcana_worldsim.r6.shellset_mesh.feg import parse_feg, write_feg

ROOT = Path(__file__).resolve().parents[2]
PRE = "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1"
FEG = "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
EULER = "R6_T0_CANONICAL_PLATE_KINEMATICS.json"
LAW = "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"
LOADER = "external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90"
MARKER = "ARCANA_R6_REGIONAL_PRE_EXPERIMENT_V1"
SCHEMA = "arcana_worldsim.r6.regional_owner_bound_experiment.v1"
RADIUS = 6_371_000.0
YEAR_SECONDS = 31_557_600.0
VERDICT = "BLOCKED_EXACT_G2_G3_INPUTS"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def specialize_loader(source, count):
    """Generate one build-local reader, retaining ValidateRecord and evaluator."""
    replacements = {
        "ARCANA_NODE_COUNT = 64442": f"ARCANA_NODE_COUNT = {count}",
        "TRIM(tokens(3)) /= '64442'": f"TRIM(tokens(3)) /= '{count}'",
        "(/14258,108,50076/)": f"(/{count},0,0/)",
        "mixed_count /= 2697": "mixed_count /= 0",
        "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1": MARKER,
        "arcana_worldsim.r6.shellset_owner_bound_runtime.v1": SCHEMA,
    }
    for old, new in replacements.items():
        expected = 2 if old == "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1" else 1
        if source.count(old) != expected:
            raise ValueError(f"Unexpected loader source at {old}")
        source = source.replace(old, new)
    return source


def perimeter(elements):
    """Trace the oriented external cycle, checking the interior face joins."""
    edges = {}
    for element in elements:
        a, b, c = element.node_ids
        for start, end in [(a, b), (b, c), (c, a)]:
            edges.setdefault(tuple(sorted((start, end))), []).append((start, end))
    if any(len(v) > 2 or (len(v) == 2 and v[0] != v[1][::-1]) for v in edges.values()):
        raise ValueError("Inconsistent triangle incidence")
    outer = [v[0] for v in edges.values() if len(v) == 1]
    following = dict(outer)
    if len(following) != len(outer) or set(following) != set(following.values()):
        raise ValueError("Perimeter is not a simple directed cycle")
    cycle = [min(following)]
    while following[cycle[-1]] != cycle[0]:
        next_node = following[cycle[-1]]
        if next_node in cycle:
            raise ValueError("Invalid perimeter traversal")
        cycle.append(next_node)
    if len(cycle) != len(outer):
        raise ValueError("Multiple perimeter cycles")
    return cycle


def prepare(output):
    pre_path = ROOT / (PRE + ".dat")
    feg_path = ROOT / FEG
    metadata = json.loads((ROOT / (PRE + ".json")).read_text())
    closure = json.loads((ROOT / "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json").read_text())
    euler = json.loads((ROOT / EULER).read_text())
    law = json.loads((ROOT / LAW).read_text())
    if (sha(pre_path) != metadata["runtime_data_sha256"]
            or sha(feg_path) != closure["evidence"]["raw_feg_sha256"]
            or euler["payload_identity_sha256"] != metadata["projection_source_lineage"]["kinematics_sha256"]):
        raise ValueError("Parent input identity mismatch")
    mesh = load_canonical_mesh(ROOT)
    if mesh.normalized_sha256 != closure["evidence"]["canonical_mesh_sha256"]:
        raise ValueError("Parent mesh identity mismatch")
    parent = parse_feg(feg_path.read_text(), mode="SHELLS_READY")
    if parent.faults or len(parent.elements) != len(mesh.triangles):
        raise ValueError("Unexpected parent topology")
    manifest = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
    with np.load(resolve_external_payload_path(ROOT, manifest["payload"]["path"]), allow_pickle=False) as data:
        face_index = {pair: i for i, pair in enumerate(zip(data["face_row"], data["face_col"]))}
    with pre_path.open() as stream:
        header = next(stream).split()
        # Preserve every selected PRE field token verbatim apart from node ID.
        pre_rows = [line.split() for line in stream]
    if int(header[-1]) != len(parent.nodes) or len(pre_rows) != len(parent.nodes):
        raise ValueError("PRE and FEG node inventories differ")
    border_nodes = {n for edge in mesh.boundary_edge_nodes for n in edge}
    # A 2x2 patch has one interior node. Choose the nearest admissible patch
    # to R091/C028 in a small, explicitly bounded continental search.
    candidates = sorted((abs(r-91)+abs(c-28), r, c)
                        for r in range(87, 96) for c in range(24, 33))
    for _, row, col in candidates:
        cells = [(row+i, col+j) for i in (0, 1) for j in (0, 1)]
        faces = [face_index[cell] for cell in cells]
        triangles = sorted(t for face in faces for t in mesh.parent_face_triangles[face])
        plates = {int(mesh.triangle_plate_id[t-1]) for t in triangles}
        nodes = sorted({int(n) for t in triangles for n in mesh.triangles[t-1]})
        if (len(plates) == 1 and len(nodes) == 9 and not border_nodes.intersection(nodes)
                and all(float(pre_rows[n-1][8]) == 1 and float(pre_rows[n-1][5]) == 0 for n in nodes)):
            break
    else:
        raise ValueError("No admissible single-plate continental patch in search window")

    local = {n: i for i, n in enumerate(nodes, 1)}
    elements = []
    element_map = []
    cell_lookup = dict(zip(faces, cells))
    for i, t in enumerate(triangles, 1):
        element = parent.elements[t-1]
        if element.node_ids != tuple(mesh.triangles[t-1]):
            raise ValueError("Parent triangle binding mismatch")
        elements.append(replace(element, element_id=i, node_ids=tuple(local[n] for n in element.node_ids)))
        element_map.append(dict(local_id=i, parent_id=t,
                                parent_cell=cell_lookup[int(mesh.triangle_parent_face[t-1])]))
    model = replace(parent, title=MARKER, nodes=tuple(replace(parent.nodes[n-1], node_id=local[n]) for n in nodes),
                    elements=tuple(elements))
    feg = write_feg(model)
    if parse_feg(feg, mode="SHELLS_READY") != model:
        raise ValueError("Regional FEG round trip failed")
    cycle = perimeter(elements)
    interior = sorted(set(local.values()) - set(cycle))
    if len(cycle) != 8 or len(interior) != 1:
        raise ValueError("Unexpected regional topology")

    plate, = plates
    vectors = {p["plate_id"]: p["euler_vector_rad_per_year"] for p in euler["plates"]}
    if set(vectors) != set(range(12)) or euler["time_ma"] != 210:
        raise ValueError("Unexpected Euler inventory")
    rotation, _ = rotation_matrices()
    xyz = _unit_vectors(mesh.vertices_lat_lon[np.array(nodes)-1])
    rotated = xyz @ rotation.T
    runtime_coordinates = np.array([(n.latitude_deg, n.longitude_deg) for n in model.nodes])
    frame_error = float(np.max(abs(rotated - _unit_vectors(runtime_coordinates))))
    if frame_error > 2e-14:
        raise ValueError("FEG frame is incompatible with the canonical nodes")
    velocity = np.cross(vectors[plate], xyz) @ rotation.T * RADIUS / YEAR_SECONDS
    np.testing.assert_allclose(velocity, np.cross(rotation @ vectors[plate], rotated) * RADIUS / YEAR_SECONDS,
                               rtol=1e-13, atol=1e-24)
    node_map = []
    for i, n in enumerate(nodes, 1):
        node = model.nodes[i-1]
        values = pre_rows[n-1]
        if len(values) != 51 or int(values[0]) != n:
            raise ValueError("Unexpected PRE record")
        fields = dict(zip(metadata["field_order"], map(float, values)))
        if (fields["crust_thickness_m"], fields["mantle_lithosphere_thickness_m"],
                fields["surface_heat_flow_w_m2"]) != (node.crustal_thickness_m,
                    node.mantle_lithosphere_thickness_m, node.heat_flow_w_m2):
            raise ValueError("PRE physical binding mismatch")
        phi, lam = np.deg2rad(runtime_coordinates[i-1])
        south = [np.sin(phi)*np.cos(lam), np.sin(phi)*np.sin(lam), -np.cos(phi)]
        east = [-np.sin(lam), np.cos(lam), 0.]
        v_south, v_east = float(velocity[i-1] @ south), float(velocity[i-1] @ east)
        node_map.append(dict(local_id=i, parent_id=n, canonical_lat_lon_deg=mesh.vertices_lat_lon[n-1].tolist(),
                             runtime_lat_lon_deg=runtime_coordinates[i-1].tolist(), PRE=fields,
                             boundary_tag="REGIONAL_CUT" if i in cycle else None,
                             candidate_euler_south_east_m_s=[v_south, v_east],
                             candidate_euler_north_clockwise_deg=float(np.degrees(np.arctan2(v_east, -v_south)) % 360),
                             prescribed_components=None, prescribed_traction_pa=None))
    areas = []
    for row_record, element in zip(element_map, elements):
        a, b, c = rotated[np.array(element.node_ids)-1]
        det = float(a @ np.cross(b,c))
        area = 2 * RADIUS**2 * np.arctan2(det, 1+a@b+b@c+c@a)
        if area <= 0:
            raise ValueError("Nonpositive spherical triangle")
        row_record["area_m2"] = float(area)
        areas.append(area)

    paths = [FEG, PRE + ".dat", PRE + ".json", EULER, LAW, LOADER,
             "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json",
             "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"]
    case = dict(verdict=VERDICT, source_sha256={p: sha(ROOT/p) for p in paths},
                plate_id=plate, cells=cells, nodes=node_map, elements=element_map,
                perimeter_local_ids=cycle, interior_local_ids=interior,
                total_area_m2=float(sum(areas)), frame_roundtrip_max_component_error=frame_error,
                first_segment_rule=law["first_segment_policy"], time_age_ma=210,
                numerical_frame="ARCANA_SHELLSET_RUNTIME_RX_PLUS_0P5_DEG_V1",
                mechanical_reference=None, basal_condition=None, regional_validity_end=None,
                traction_policy=None, rigid_mode_constraints=None, t1=None)
    output.mkdir()
    (output / "regional.feg").write_text(feg)
    lines = [f"{MARKER} {SCHEMA} {len(nodes)}"]
    lines += [" ".join([str(local[n]), *pre_rows[n-1][1:]]) for n in nodes]
    (output / "regional_PRE.dat").write_text("\n".join(lines) + "\n")
    (output / "MOD_ArcanaRuntime.regional.f90").write_text(specialize_loader((ROOT/LOADER).read_text(), len(nodes)))
    (output / "CASE.json").write_text(json.dumps(case, indent=2, allow_nan=False) + "\n")
    print(VERDICT, cells, plate, nodes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    prepare(parser.parse_args().output)
