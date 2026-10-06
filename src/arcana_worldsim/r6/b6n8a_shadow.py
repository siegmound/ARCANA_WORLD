"""Noncanonical B6N8-A numerical shadow for restricted post-event kinematics.

This module evaluates only conditional plate-local rigid rotations over a
diagnostic window. It never writes to WORLD_HISTORY or treats results as
physical rift state, interface accommodation, or transition authority.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
from typing import Any, Iterable, Mapping, Sequence

from .finite_rotation import rotate_vector_constant_euler
from .query import HistoryQueryService
from .store import HistoryStore

POST_EVENT_ID = "r6state_86b55139388fd6d01cb0ff640f9580e1e1331f2469fb5c4f296c6cf2578fc630"
POST_EVENT_PAYLOAD_SHA256 = "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a"
KINEMATICS_SOURCE_SHA256 = "0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2"
REVALIDATION_HORIZON_YEARS = 8214.051909111062
EARTH_RADIUS_M = 6_371_000.0
LABELS = ["DIAGNOSTIC_SHADOW_TRAJECTORY", "NONCANONICAL", "CONDITIONAL",
          "NOT_PHYSICAL_HISTORY_AUTHORITY", "WORLD_HISTORY_PUBLICATION_PROHIBITED"]
STEPS_PER_WINDOW = (4, 8, 16, 32)
OBSERVABLE_REGISTRY = [
    {"name":"plate_local_position","semantic_meaning":"coordinate under conditional rigid rotation","units":"unit sphere XYZ","derivation":"RK4 integration from the exact POST_EVENT plate-side coordinate using its governed constant Euler vector","authority":"B6N2 restricted successor kinematics and B6K POST_EVENT coordinate payload","scope":"72 identified nodes on plate sides 1 and 3; fixed structural regime is diagnostic-only","class":"DERIVED_DIAGNOSTIC","adaptive_signal":"displacement/error can inform numerical step-size diagnostics; no action threshold","state_extraction":"only if a future authorized model marks a supported state significant"},
    {"name":"rigid_point_displacement","semantic_meaning":"great-circle displacement from POST_EVENT origin under B6N2 Euler vector","units":"m","derivation":"great-circle distance from the initial plate-local coordinate at common sample times","authority":"B6N2 restricted successor kinematics; not physical rift authority","scope":"72 identified nodes on plate sides 1 and 3 over the quarter model-scope window","class":"DERIVED_DIAGNOSTIC","adaptive_signal":"local displacement and numerical error are candidate signals; no production threshold","state_extraction":"not physical state; retain only under a later significant-state contract"},
    {"name":"pair_side_geometric_mismatch","semantic_meaning":"great-circle separation of the two independently rotated representations for the same shared interface node; not opening/accommodation","units":"m","derivation":"great-circle separation between plate-side 1 and 3 coordinate representations at common sample times","authority":"derived from B6K coordinates and B6N2 rotations; no interface response authority","scope":"71 governed pair segments represented by 72 shared node identities","class":"DERIVED_DIAGNOSTIC","adaptive_signal":"change/rate may flag numerical or scope sensitivity","state_extraction":"not a physical interface response"},
    {"name":"topology_and_support_identity","semantic_meaning":"frozen input identity; no transition or reassignment computed","units":"discrete identity","derivation":"identity carried unchanged from the governed B6K input support","authority":"B6K input binding; no transition or remapping authority","scope":"plate pair 1:3 support only","class":"INVARIANT","adaptive_signal":"no transition predicate signal","state_extraction":"initial support reference only"},
    {"name":"rift_process_state_and_physical_transition","semantic_meaning":"not supplied by B6N2 restricted kinematics","units":"n/a","derivation":"not derivable from the diagnostic coordinates","authority":"UNAVAILABLE; requires a governed physical model and event authority","scope":"outside this geometric shadow","class":"UNAVAILABLE / UNKNOWN","adaptive_signal":"requires model/authority; refinement cannot supply","state_extraction":"no candidate physical event/state"}]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_snapshot(root: Path) -> dict[str, Any]:
    """Return a deterministic read-only inventory of canonical store bytes."""
    root = root.resolve(strict=True)
    entries = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()),
                       key=lambda p: p.relative_to(root).as_posix()):
        entries.append({"path": path.relative_to(root).as_posix(),
                        "bytes": path.stat().st_size, "sha256": _sha256(path)})
    encoded = json.dumps(entries, separators=(",", ":"), sort_keys=True,
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return {"file_count": len(entries),
            "logical_bytes": sum(row["bytes"] for row in entries),
            "tree_sha256": sha256(encoded).hexdigest(), "files": entries}


def _assert_output_isolated(output_dir: Path, repository_root: Path,
                             canonical_root: Path) -> Path:
    output = output_dir.resolve()
    repo = repository_root.resolve()
    canonical = canonical_root.resolve()
    if output == repo or repo in output.parents:
        raise ValueError("diagnostic output must be outside the repository")
    if output == canonical or canonical in output.parents:
        raise ValueError("diagnostic output must be outside canonical WORLD_HISTORY")
    if output.exists() and any(output.iterdir()):
        raise ValueError("diagnostic output directory must be absent or empty")
    return output


def _preflight_live_canonical_store(canonical_root: Path) -> dict[str, Any]:
    """Validate the configured store's committed view through the typed APIs.

    HistoryStore opening can initialize/recover writer metadata, so it is
    opened only on a byte-identical temporary copy. The configured canonical
    tree is snapshotted before and after to prove this preflight was read-only.
    """
    root = canonical_root.resolve(strict=True)
    configured = os.environ.get("ARCANA_WORLD_HISTORY_ROOT")
    if not configured or Path(configured).resolve() != root:
        raise ValueError("canonical root does not match ARCANA_WORLD_HISTORY_ROOT")

    before = canonical_snapshot(root)
    current_pointer_path = root / ".history_visibility" / "CURRENT.json"
    pointer = _read_json(current_pointer_path)
    if pointer.get("schema") != "ARCANA_R6_COMMITTED_READ_VIEW_V1":
        raise ValueError("canonical CURRENT pointer schema is invalid")
    expected_view_id = pointer.get("view_id")
    if not isinstance(expected_view_id, str) or not expected_view_id.startswith("view_"):
        raise ValueError("canonical CURRENT pointer has no valid view identity")

    transaction_root = root / ".history_transactions"
    pending = []
    if transaction_root.exists():
        pending = sorted(p.name for p in transaction_root.iterdir()
                         if p.name != ".retired")
    if pending:
        raise ValueError("canonical store has unresolved transaction entries")

    # This descriptor describes B6M0 genesis. It is reported for provenance,
    # never treated as the live epoch count or latest state.
    descriptor = _read_json(root / "arcana_canonical_store.json")
    descriptor_epoch_count = descriptor.get("canonical_temporal_state_count")

    try:
        with tempfile.TemporaryDirectory(prefix="r6-b6n8a-live-view-") as temporary:
            reader_root = Path(temporary) / "canonical_snapshot"
            shutil.copytree(root, reader_root)
            store = HistoryStore(reader_root)
            query = HistoryQueryService(store)
            with store.read_view() as view:
                if view.view_id != expected_view_id:
                    raise ValueError("copied store reader view differs from canonical CURRENT")
                states = store.states()
                temporal_records = store.temporal_records()
                post = store.read_state(POST_EVENT_ID)
                pre = store.read_state(
                    "r6state_3e484d59d985ba93ec8c58d5a9a82ca4369f7aaa2d6725339479e68a7559810c")
                if post.domain != "tectonic_geometry" or pre.domain != post.domain:
                    raise ValueError("PRE_EVENT/POST_EVENT are not tectonic geometry states")
                if post.payload_ref != f"sha256:{POST_EVENT_PAYLOAD_SHA256}" or \
                        pre.payload_ref != post.payload_ref:
                    raise ValueError("visible PRE_EVENT/POST_EVENT payload identity mismatch")
                if (pre.history_id, pre.branch_id, pre.time_support.time_key) != \
                        (post.history_id, post.branch_id, post.time_support.time_key):
                    raise ValueError("PRE_EVENT and POST_EVENT do not share one causal time")

                geometry = [state for state in states
                            if state.domain == "tectonic_geometry"]
                ages = set()
                for state in geometry:
                    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)Ma",
                                         state.time_support.time_key)
                    if match is None:
                        raise ValueError("live tectonic geometry has an unrecognized age key")
                    ages.add(float(match.group(1)))
                if ages != {210.0, 209.97287659484368}:
                    raise ValueError("live committed view does not contain exactly the T0/T1 ages")
                if sum(state.time_support.time_key == "210.0Ma" for state in geometry) != 1:
                    raise ValueError("live committed view lacks its unique T0 geometry state")

                causal = post.applicability.get("causal_order_key", {})
                event_id = causal.get("causal_event_id")
                if (causal.get("causal_phase") != "POST_EVENT" or
                        causal.get("physical_time_key") != post.time_support.time_key or
                        not isinstance(event_id, str)):
                    raise ValueError("POST_EVENT causal binding is absent or inconsistent")
                selected_pre = query.state_at(history_id=post.history_id,
                    branch_id=post.branch_id, domain=post.domain,
                    time_key=post.time_support.time_key,
                    causal_phase="PRE_EVENT", causal_event_id=event_id)
                selected_post = query.state_at(history_id=post.history_id,
                    branch_id=post.branch_id, domain=post.domain,
                    time_key=post.time_support.time_key,
                    causal_phase="POST_EVENT", causal_event_id=event_id)
                ambiguous = query.state_at(history_id=post.history_id,
                    branch_id=post.branch_id, domain=post.domain,
                    time_key=post.time_support.time_key)
                same_time_history = query.history_result(history_id=post.history_id,
                    branch_id=post.branch_id, domain=post.domain,
                    time_key=post.time_support.time_key).states
                if (selected_pre.status != "FOUND" or selected_pre.state is None or
                        str(selected_pre.state.state_id) != str(pre.state_id)):
                    raise ValueError("PRE_EVENT causal selector did not resolve predecessor")
                if (selected_post.status != "FOUND" or selected_post.state is None or
                        str(selected_post.state.state_id) != POST_EVENT_ID):
                    raise ValueError("POST_EVENT causal selector did not resolve successor")
                if ambiguous.status != "CONFLICT" or \
                        ambiguous.provenance.get("reason") != "AMBIGUOUS_CAUSAL_STATE":
                    raise ValueError("unselected same-time state query is not fail-closed")
                if [str(state.state_id) for state in same_time_history] != [
                        str(pre.state_id), POST_EVENT_ID]:
                    raise ValueError("same-time history is not causally ordered PRE then POST")

                live_epoch_count = len(ages)
                live_state_count = len(states)
                temporal_record_count = len(temporal_records)
                selected_view_id = view.view_id
    except Exception as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("canonical"):
            raise
        raise ValueError(f"canonical live-view preflight failed closed: {exc}") from exc

    after = canonical_snapshot(root)
    if before != after:
        raise ValueError("canonical WORLD_HISTORY changed during read-only preflight")
    return {
        "status": "PASS_CANONICAL_LIVE_VIEW_PREflight".upper(),
        "reader": "HistoryStore + HistoryQueryService on byte-identical temporary snapshot",
        "canonical_root_matches_environment": True,
        "canonical_current_view_id": selected_view_id,
        "canonical_descriptor_role": "IMMUTABLE_B6M0_GENESIS_DESCRIPTOR_NOT_LIVE_VIEW",
        "descriptor_temporal_state_count_informational_only": descriptor_epoch_count,
        "live_visible_state_count": live_state_count,
        "live_temporal_record_count": temporal_record_count,
        "live_physical_geometry_epoch_count": live_epoch_count,
        "live_physical_ages_ma": [210.0, 209.97287659484368],
        "pre_event_visible_and_queryable": True,
        "post_event_visible_and_queryable": True,
        "unselected_same_time_query_conflicts": True,
        "same_time_history_order": ["PRE_EVENT", "POST_EVENT"],
        "post_event_state_id": POST_EVENT_ID,
        "post_event_payload_sha256": POST_EVENT_PAYLOAD_SHA256,
        "pending_transactions": 0,
        "canonical_tree_unchanged": True,
        "canonical_tree_sha256": before["tree_sha256"],
    }


def _decode_coordinate_payload(path: Path) -> tuple[list[tuple[int, int]], list[tuple[float, float, float]]]:
    raw = path.read_bytes()
    if not raw.startswith(b"R6B6K\0") or len(raw) < 14:
        raise ValueError("POST_EVENT coordinate payload has an unknown binary header")
    header_size = int.from_bytes(raw[6:14], "little")
    header_end = 14 + header_size
    if header_end > len(raw):
        raise ValueError("coordinate payload header is truncated")
    header = json.loads(raw[14:header_end].decode("utf-8"))
    if (header.get("schema") != "R6_B6K_PLATE_LOCAL_COORDINATES_V1"
            or header.get("units") != "unit_sphere"
            or header.get("identity_columns") != ["node_id_1based", "plate_id"]
            or header.get("coordinate_columns") != ["x", "y", "z"]):
        raise ValueError("coordinate payload schema is not the governed B6K representation")
    count = int(header["row_count"])
    if len(raw) - header_end != count * (2 * 8 + 3 * 8):
        raise ValueError("coordinate payload arrays have inconsistent lengths")
    identities = [struct.unpack_from("<qq", raw, header_end + i * 16) for i in range(count)]
    coord_start = header_end + count * 16
    coordinates = [struct.unpack_from("<ddd", raw, coord_start + i * 24)
                    for i in range(count)]
    if len(set(identities)) != count:
        raise ValueError("coordinate payload repeats a node/plate representation")
    if not all(all(math.isfinite(x) for x in xyz) for xyz in coordinates):
        raise ValueError("coordinate payload contains non-finite values")
    return [(int(n), int(p)) for n, p in identities], coordinates


def _verified_b6k_inputs(repository_root: Path, canonical_root: Path) -> tuple[
        list[tuple[int, tuple[float, float, float], tuple[float, float, float]]],
        dict[int, tuple[float, float, float]], dict[str, Any]]:
    root = repository_root.resolve(strict=True)
    out = root / "outputs/r6_b6k_isolated_first_candidate_state"
    manifest = _read_json(out / "B6K_ARTIFACT_MANIFEST.json")
    entries: dict[str, dict[str, Any]] = {}
    for row in manifest.get("artifacts", []):
        name = Path(row.get("relative_path", "")).name
        if name in entries:
            raise ValueError(f"B6K manifest has an ambiguous basename: {name}")
        entries[name] = row
    names = ("B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin", "B6K_PLATE_ROTATIONS.json",
             "B6K_BOUNDARY_CANDIDATE.json", "B6K_REPLAY.json",
             "B6K_SOURCE_FREEZE.json", "B6K_CANDIDATE_IDENTITY.json")
    for name in names:
        row = entries.get(name)
        path = out / name
        if row is None or not path.is_file() or _sha256(path) != row.get("sha256"):
            raise ValueError(f"B6K input is absent or differs from its artifact manifest: {name}")
        if path.stat().st_size != row.get("byte_size"):
            raise ValueError(f"B6K input size differs from its artifact manifest: {name}")

    n2 = _read_json(root / "contracts/R6_POST_EVENT_KINEMATIC_AUTHORITY_V1.json")
    n3a = _read_json(root / "contracts/R6_POST_EVENT_KINEMATIC_REVALIDATION_HORIZON_V1.json")
    n4r1 = _read_json(root / "docs/arcana/qualifications/R6_B6N4R1_ATTESTATION.json")
    n7 = _read_json(root / "docs/arcana/qualifications/R6_B6N7_ATTESTATION.json")
    require = lambda ok, msg: None if ok else (_ for _ in ()).throw(ValueError(msg))
    require(n2.get("status") == "POST_EVENT_KINEMATIC_AUTHORITY_CONTINUES_WITH_RESTRICTED_SCOPE",
            "B6N2 successor kinematic authority is not active")
    require(n2.get("provenance", {}).get("post_event_state_id") == POST_EVENT_ID,
            "B6N2 authority is not bound to the exact POST_EVENT state")
    require(n2.get("provenance", {}).get("post_event_payload_sha256") == POST_EVENT_PAYLOAD_SHA256,
            "B6N2 authority payload identity changed")
    require(n2.get("predecessor_authority", {}).get("source_file_sha256") == KINEMATICS_SOURCE_SHA256,
            "B6N2 predecessor kinematic source identity changed")
    horizon = n3a.get("derivation", {}).get("horizon_delta_years")
    require(horizon == REVALIDATION_HORIZON_YEARS, "B6N3-A revalidation horizon changed")
    require(n3a.get("horizon_class") == "MODEL_SCOPE_REVALIDATION"
            and n3a.get("termination_semantics", {}).get("physical_event_predicted") is False,
            "B6N3-A horizon semantics changed")
    require(n4r1.get("positive_propagation_interval") == "NOT_ESTABLISHED",
            "B6N4-R1 positive propagation blocker changed")
    require(n7.get("verdict") == "PASS_B6N7_MINIMUM_EVOLVABLE_RIFT_MODEL_REQUIREMENTS_DEFINED"
            and n7.get("qualified_source_commit") == "cb1546f3c7aeb9703c4317aecadc21cf38d6cb2f",
            "B6N7 attestation identity/status changed")

    canonical_preflight = _preflight_live_canonical_store(canonical_root)

    payload_path = out / "B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin"
    if _sha256(payload_path) != POST_EVENT_PAYLOAD_SHA256:
        raise ValueError("B6K materialization does not match canonical POST_EVENT payload SHA256")
    identities, coordinates = _decode_coordinate_payload(payload_path)
    coordinate_by_pair = dict(zip(identities, coordinates))

    rotations = _read_json(out / "B6K_PLATE_ROTATIONS.json")
    if len(rotations.get("plates", [])) != 12:
        raise ValueError("expected all 12 governed plate Euler vectors")
    omega = {int(row["plate_id"]): tuple(float(x) for x in row["omega_rad_per_year"])
             for row in rotations["plates"]}
    if set(omega) != set(range(12)) or not all(math.isfinite(x) for v in omega.values() for x in v):
        raise ValueError("governed Euler vectors are incomplete or non-finite")
    source_freeze = _read_json(out / "B6K_SOURCE_FREEZE.json")
    frozen_kinematics = source_freeze.get("source_snapshot_after", {}).get(
        "R6_T0_CANONICAL_PLATE_KINEMATICS.json", {}).get("sha256")
    if frozen_kinematics != KINEMATICS_SOURCE_SHA256:
        raise ValueError("B6K source freeze is not bound to the B6N2-renewed kinematic vector source")
    replay = _read_json(out / "B6K_REPLAY.json")
    if replay.get("status") != "PASS_DETERMINISTIC_RECONSTRUCTION_BYTES":
        raise ValueError("B6K deterministic reconstruction evidence is not passing")
    identity = _read_json(out / "B6K_CANDIDATE_IDENTITY.json")
    if identity.get("payload_sha256") != POST_EVENT_PAYLOAD_SHA256:
        raise ValueError("B6K candidate identity does not match canonical POST_EVENT payload")

    boundary = _read_json(out / "B6K_BOUNDARY_CANDIDATE.json")
    rows = [row for row in boundary.get("interfaces", [])
            if sorted(int(x) for x in row.get("incident_plate_ids", [])) == [1, 3]]
    if boundary.get("interface_count") != 1983 or len(rows) != 71:
        raise ValueError("B6K governed 1:3 interface cardinality changed")
    graph: dict[int, set[int]] = defaultdict(set)
    degrees: Counter[int] = Counter()
    for row in rows:
        sides = {int(side["plate_id"]): [int(x) for x in side["coordinate_rows"]]
                 for side in row.get("sides", [])}
        if set(sides) != {1, 3} or len(sides[1]) != 2 or len(sides[3]) != 2:
            raise ValueError("pair interface lacks two endpoint representations per plate")
        node_sides = []
        for plate in (1, 3):
            node_sides.append([identities[index][0] for index in sides[plate]])
            if any(identities[index][1] != plate for index in sides[plate]):
                raise ValueError("boundary endpoint representation has the wrong plate identity")
        if node_sides[0] != node_sides[1]:
            raise ValueError("pair boundary endpoint node identities do not match across sides")
        a, b = node_sides[0]
        if a == b:
            raise ValueError("pair boundary segment has identical endpoints")
        graph[a].add(b); graph[b].add(a)
        degrees[a] += 1; degrees[b] += 1
    if len(graph) != 72 or sum(len(v) for v in graph.values()) // 2 != 71:
        raise ValueError("pair interface no longer has 72 vertices and 71 segments")
    if sorted(degrees.values()).count(1) != 2 or any(v not in (1, 2) for v in degrees.values()):
        raise ValueError("pair interface endpoint/degree structure differs from the governed chain")
    seen = set(); stack = [min(graph)]
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node); stack.extend(graph[node] - seen)
    if len(seen) != 72:
        raise ValueError("pair interface support is disconnected")

    pair_nodes = []
    for node in sorted(graph):
        if (node, 1) not in coordinate_by_pair or (node, 3) not in coordinate_by_pair:
            raise ValueError(f"pair interface node {node} lacks both plate-side coordinates")
        pair_nodes.append((node, coordinate_by_pair[(node, 1)], coordinate_by_pair[(node, 3)]))
    input_identity = {"post_event_state_id": POST_EVENT_ID,
        "post_event_payload_sha256": POST_EVENT_PAYLOAD_SHA256,
        "canonical_live_view_preflight": canonical_preflight,
        "kinematics_source_sha256": KINEMATICS_SOURCE_SHA256,
        "plate_rotation_support_identity_sha256": rotations["support_identity_sha256"],
        "pair_interface_count": len(rows), "pair_interface_node_count": len(pair_nodes),
        "coordinate_payload_rows": len(identities)}
    return pair_nodes, {1: omega[1], 3: omega[3]}, input_identity


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _rk4_step(x: Sequence[float], omega: Sequence[float], dt: float) -> tuple[float, float, float]:
    def f(y: Sequence[float]) -> tuple[float, float, float]:
        return _cross(omega, y)
    k1 = f(x)
    k2 = f(tuple(x[i] + 0.5*dt*k1[i] for i in range(3)))
    k3 = f(tuple(x[i] + 0.5*dt*k2[i] for i in range(3)))
    k4 = f(tuple(x[i] + dt*k3[i] for i in range(3)))
    return tuple(x[i] + dt*(k1[i] + 2*k2[i] + 2*k3[i] + k4[i])/6.0
                 for i in range(3))  # type: ignore[return-value]


def _norm(x: Sequence[float]) -> float:
    return math.sqrt(sum(v*v for v in x))


def _arc_m(a: Sequence[float], b: Sequence[float]) -> float:
    na, nb = _norm(a), _norm(b)
    if na == 0.0 or nb == 0.0:
        raise ValueError("zero vector cannot represent a spherical position")
    aa = tuple(v/na for v in a); bb = tuple(v/nb for v in b)
    cross = _cross(aa, bb)
    sine = _norm(cross)
    cosine = max(-1.0, min(1.0, sum(aa[i]*bb[i] for i in range(3))))
    return EARTH_RADIUS_M * math.atan2(sine, cosine)


def _trajectory_digest(samples: Sequence[Sequence[tuple[float, ...]]]) -> str:
    data = json.dumps(samples, separators=(",", ":"), allow_nan=False).encode("ascii")
    return sha256(data).hexdigest()


def compute_multiresolution(pair_nodes: Sequence[tuple[int, Sequence[float], Sequence[float]]],
                            omega_by_plate: Mapping[int, Sequence[float]],
                            horizon_years: float = REVALIDATION_HORIZON_YEARS,
                            window_fraction: float = 0.25) -> dict[str, Any]:
    """Integrate only pair-local rigid coordinates; no state is published."""
    if not math.isfinite(horizon_years) or horizon_years <= 0:
        raise ValueError("finite positive model-scope horizon is required")
    if not math.isfinite(window_fraction) or not 0 < window_fraction < 1:
        raise ValueError("diagnostic window fraction must be inside (0,1)")
    duration = horizon_years * window_fraction
    if not 0 < duration < horizon_years:
        raise ValueError("diagnostic window must remain strictly inside model-scope horizon")
    if set(omega_by_plate) != {1, 3}:
        raise ValueError("only the governed plate-pair 1:3 Euler vectors are accepted")
    if not pair_nodes or len({int(row[0]) for row in pair_nodes}) != len(pair_nodes):
        raise ValueError("pair support must contain unique node identities")

    initial = {int(node): {1: tuple(map(float, xyz1)), 3: tuple(map(float, xyz3))}
               for node, xyz1, xyz3 in pair_nodes}
    if any(not math.isfinite(x) for sides in initial.values() for xyz in sides.values() for x in xyz):
        raise ValueError("initial geometry must be finite")
    if any(abs(_norm(xyz) - 1.0) > 2e-12 for sides in initial.values() for xyz in sides.values()):
        raise ValueError("initial B6K coordinates must be unit-sphere positions")

    resolution_rows = []
    trajectories: dict[int, list[dict[int, dict[int, tuple[float, float, float]]]]] = {}
    sample_count = 4
    for total_steps in STEPS_PER_WINDOW:
        if total_steps % sample_count:
            raise ValueError("step levels must land exactly on all common sample times")
        dt = duration / total_steps
        quarter_steps = total_steps // sample_count
        state = {node: dict(sides) for node, sides in initial.items()}
        samples = [{node: dict(sides) for node, sides in state.items()}]
        for step in range(1, total_steps + 1):
            state = {node: {plate: _rk4_step(xyz, omega_by_plate[plate], dt)
                            for plate, xyz in sides.items()}
                     for node, sides in state.items()}
            if step % quarter_steps == 0:
                samples.append({node: dict(sides) for node, sides in state.items()})
        trajectories[total_steps] = samples

        rows = []
        for sample_index, sample in enumerate(samples):
            elapsed = duration * sample_index / sample_count
            point_displacements = [_arc_m(initial[node][plate], sample[node][plate])
                                   for node in sorted(sample) for plate in (1, 3)]
            side_separations = [_arc_m(sample[node][1], sample[node][3]) for node in sorted(sample)]
            exact_errors = []
            radius_drift = []
            for node in sorted(sample):
                for plate in (1, 3):
                    exact = rotate_vector_constant_euler(initial[node][plate],
                        omega_by_plate[plate], elapsed)
                    exact_errors.append(EARTH_RADIUS_M * math.sqrt(sum(
                        (sample[node][plate][i] - exact[i])**2 for i in range(3))))
                    radius_drift.append(abs(_norm(sample[node][plate]) - 1.0))
            rows.append({"elapsed_years": elapsed,
                "median_rigid_point_displacement_m": _median(point_displacements),
                "max_rigid_point_displacement_m": max(point_displacements, default=0.0),
                "median_pair_side_mismatch_m": _median(side_separations),
                "max_pair_side_mismatch_m": max(side_separations, default=0.0),
                "max_exact_rotation_error_m": max(exact_errors, default=0.0),
                "max_unit_radius_drift": max(radius_drift, default=0.0)})
        digest_rows = [[sample[node][plate][axis] for node in sorted(sample)
                        for plate in (1, 3) for axis in range(3)] for sample in samples]
        initial_digest = _trajectory_digest([[initial[node][plate][axis]
            for node in sorted(initial) for plate in (1, 3) for axis in range(3)]])
        resolution_rows.append({"step_count": total_steps, "internal_dt_years": dt,
            "initial_state_coordinate_sha256": initial_digest,
            "internal_dt_is_persistent_interval": False,
            "sample_count": len(samples), "samples": rows,
            "trajectory_sample_coordinates_sha256": _trajectory_digest(digest_rows)})

    finest = trajectories[STEPS_PER_WINDOW[-1]]
    comparisons = []
    for steps in STEPS_PER_WINDOW[:-1]:
        sample_rows = []
        for index, (coarse, fine) in enumerate(zip(trajectories[steps], finest)):
            differences = [EARTH_RADIUS_M * math.sqrt(sum(
                (coarse[node][plate][axis]-fine[node][plate][axis])**2 for axis in range(3)))
                for node in sorted(coarse) for plate in (1, 3)]
            reference_displacements = [EARTH_RADIUS_M * math.sqrt(sum(
                (rotate_vector_constant_euler(initial[node][plate], omega_by_plate[plate],
                    duration*index/sample_count)[axis]-initial[node][plate][axis])**2
                for axis in range(3))) for node in sorted(coarse) for plate in (1, 3)]
            reference_scale = max(reference_displacements, default=0.0)
            maximum = max(differences, default=0.0)
            sample_rows.append({"elapsed_years": duration*index/sample_count,
                "max_position_difference_to_finest_m": maximum,
                "max_difference_relative_to_max_exact_displacement": (
                    maximum/reference_scale if reference_scale > 0 else None),
                "rms_position_difference_to_finest_m": math.sqrt(
                    sum(x*x for x in differences)/len(differences)) if differences else 0.0})
        rates = []
        for left, right in zip(sample_rows, sample_rows[1:]):
            rates.append((right["max_position_difference_to_finest_m"] -
                          left["max_position_difference_to_finest_m"]) /
                         (duration/sample_count))
        comparisons.append({"step_count": steps, "reference_step_count": STEPS_PER_WINDOW[-1],
                            "samples": sample_rows,
                            "endpoint_max_position_difference_m": sample_rows[-1][
                                "max_position_difference_to_finest_m"],
                            "max_abs_change_in_cross_resolution_error_rate_m_per_year": max(
                                (abs(value) for value in rates), default=0.0),
                            "max_trajectory_difference_m": max(
                                row["max_position_difference_to_finest_m"] for row in sample_rows)})

    mismatch_series = [row["samples"] for row in resolution_rows]
    for level, samples in zip(resolution_rows, mismatch_series):
        values = [row["max_pair_side_mismatch_m"] for row in samples]
        rates = [(right-left)/(duration/sample_count) for left, right in zip(values, values[1:])]
        level["pair_mismatch_diagnostic_shape"] = {
            "sampled_max_mismatch_m": values,
            "monotonic_non_decreasing": all(right >= left for left, right in zip(values, values[1:])),
            "max_abs_sampled_mismatch_rate_m_per_year": max((abs(x) for x in rates), default=0.0),
            "rate_semantics": "GEOMETRIC_DIAGNOSTIC_ONLY; NOT PHYSICAL INTERFACE RESPONSE"}

    # Deterministic temporal-refinement probe on the quarter with the largest
    # coarse-vs-finest discrepancy. This is a numerical probe, not an event.
    coarse = trajectories[STEPS_PER_WINDOW[0]]
    fine = trajectories[STEPS_PER_WINDOW[-1]]
    interval_errors = []
    interval_maxima = []
    for interval in range(sample_count):
        errors = [(EARTH_RADIUS_M * math.sqrt(sum(
            (coarse[interval + 1][node][plate][axis]-fine[interval + 1][node][plate][axis])**2
            for axis in range(3))), node, plate)
            for node in sorted(initial) for plate in (1, 3)]
        maximum = max(errors, default=(0.0, None, None))
        interval_errors.append(maximum[0])
        interval_maxima.append(maximum)
    selected_interval = max(range(sample_count), key=lambda i: (interval_errors[i], -i))
    interval_duration = duration / sample_count
    coarse_local_error = []
    refined_local_error = []
    for node in sorted(initial):
        for plate in (1, 3):
            start = coarse[selected_interval][node][plate]
            omega = omega_by_plate[plate]
            exact_end = rotate_vector_constant_euler(start, omega, interval_duration)
            coarse_end = _rk4_step(start, omega, interval_duration)
            refined_steps = 32
            refined_end = start
            for _ in range(refined_steps):
                refined_end = _rk4_step(refined_end, omega, interval_duration/refined_steps)
            coarse_local_error.append(EARTH_RADIUS_M*math.sqrt(sum((coarse_end[i]-exact_end[i])**2 for i in range(3))))
            refined_local_error.append(EARTH_RADIUS_M*math.sqrt(sum((refined_end[i]-exact_end[i])**2 for i in range(3))))
    refinement = {"selected_quarter_index": selected_interval,
        "interval_start_years": interval_duration*selected_interval,
        "interval_end_years": interval_duration*(selected_interval+1),
        "selection_max_coarse_vs_finest_position_difference_m": interval_errors[selected_interval],
        "max_discrepancy_node_id": interval_maxima[selected_interval][1],
        "max_discrepancy_plate_id": interval_maxima[selected_interval][2],
        "spatial_scope_semantics": "IDENTIFIED_INPUT_NODE_ONLY; NO_SPATIAL_REFINEMENT_EXECUTED",
        "local_coarse_step_count": 1, "local_refined_step_count": 32,
        "local_coarse_exact_error_max_m": max(coarse_local_error, default=0.0),
        "local_refined_exact_error_max_m": max(refined_local_error, default=0.0),
        "numerical_error_decreased": max(refined_local_error, default=0.0) < max(coarse_local_error, default=0.0),
        "event_or_transition_created": False, "temporary_trajectory_only": True}

    compression = []
    for level in resolution_rows:
        series = trajectories[level["step_count"]]
        errors = []
        for index, sample in enumerate(series):
            elapsed = duration*index/sample_count
            for node in sorted(initial):
                for plate in (1, 3):
                    replayed = rotate_vector_constant_euler(initial[node][plate],
                        omega_by_plate[plate], elapsed)
                    errors.append(EARTH_RADIUS_M*math.sqrt(sum(
                        (sample[node][plate][axis]-replayed[axis])**2 for axis in range(3))))
        compression.append({"step_count": level["step_count"],
            "sparse_replay_checkpoint_count": 1,
            "reconstruction_max_error_m": max(errors, default=0.0),
            "reconstruction_rms_error_m": math.sqrt(sum(x*x for x in errors)/len(errors)) if errors else 0.0,
            "tolerance_authority": "ABSENT", "compression_acceptance_claim": False})

    exact_error_by_level = [{"step_count": row["step_count"],
        "max_exact_rotation_error_m": max(sample["max_exact_rotation_error_m"]
            for sample in row["samples"])} for row in resolution_rows]
    error_decreased_each_refinement = all(
        right["max_exact_rotation_error_m"] < left["max_exact_rotation_error_m"]
        for left, right in zip(exact_error_by_level, exact_error_by_level[1:]))
    max_cross_resolution = max((row["max_trajectory_difference_m"]
        for row in comparisons), default=0.0)

    return {"semantic_labels": list(LABELS), "physical_state_semantics": "NONE; plate-local geometric shadow only",
        "plate_pair": [1, 3], "interface_node_count": len(initial),
        "diagnostic_window_years": duration, "maximum_model_scope_revalidation_years": horizon_years,
        "window_fraction_of_model_scope_bound": window_fraction,
        "physical_event_free_horizon_claimed": False,
        "physical_positive_duration_authorized": False,
        "resolution_ladder": resolution_rows, "cross_resolution_comparison": comparisons,
        "temporal_refinement": refinement, "sparse_checkpoint_reconstruction": compression,
        "numerical_pattern_analysis": {
            "exact_rotation_error_by_resolution": exact_error_by_level,
            "error_decreased_at_each_refinement": error_decreased_each_refinement,
            "maximum_coarse_vs_finest_difference_m": max_cross_resolution,
            "cross_resolution_difference_observed": max_cross_resolution > 0.0,
            "numerical_acceptance_tolerance": "ABSENT; no stable/unstable physical acceptance classification",
        "numerical_vs_model_authority_classification":
            "NUMERICAL_DIFFERENCES_MEASURED_WITHOUT_ACCEPTANCE_TOLERANCE; "
            "MODEL_AUTHORITY_REMAINS_UNRESOLVED",
        "physical_model_gap_status":
            "RIFT_TRANSITION_STATE_AND_PREDICATE_UNAVAILABLE; NUMERICAL_REFINEMENT_CANNOT_CLOSE",
            "classification": ("RESOLUTION_CONTROL_PATTERN_CANDIDATE"
                if max_cross_resolution > 0.0 else "LIMITED_INFORMATION_EXACTLY_NO_RESOLUTION_DIFFERENCE")},
        "temporary_trajectory_accounting": {
            "resolution_count": len(STEPS_PER_WINDOW),
            "sample_times_per_resolution": sample_count + 1,
            "identified_interface_nodes": len(initial),
            "plate_side_coordinate_representations_per_node": 2,
            "temporary_sample_coordinate_triples": len(STEPS_PER_WINDOW) *
                (sample_count + 1) * len(initial) * 2,
            "temporary_sample_scalar_coordinates": len(STEPS_PER_WINDOW) *
                (sample_count + 1) * len(initial) * 2 * 3,
            "full_coordinate_trajectory_files_written": 0,
            "coordinate_arrays_retained_in_result": False,
            "per_resolution_coordinate_sha256_retained": True},
        "adaptive_control_signal_candidates": [
            {"signal": "cross-resolution discrepancy", "candidate_action": "DECREASE_INTERNAL_DT_OR_REFINE_INTERVAL",
             "authority": "DIAGNOSTIC_SIGNAL_ONLY; no production threshold or action authorized"},
            {"signal": "numerical error reduction under refinement", "candidate_action": "REFINE_INTERVAL",
             "observed_in_this_run": error_decreased_each_refinement,
             "authority": "CASE_SPECIFIC; no production threshold or action authorized"},
            {"signal": "physical transition predicate", "candidate_action": "REQUEST_MODEL_AUTHORITY",
             "observed_in_this_run": False,
             "authority": "NO_SIGNAL; missing model/authority cannot be repaired by temporal refinement"}],
        "candidate_sample_significance": {
            "initial_POST_EVENT": "MANDATORY_CAUSAL_BOUNDARY_ALREADY_EXISTS",
            "intermediate_samples": "INSIGNIFICANT_NUMERICAL_SAMPLE_FOR_THIS_DIAGNOSTIC_ONLY",
            "largest_coarse_fine_discrepancy": "RECONSTRUCTION_CHECKPOINT_CANDIDATE_ONLY; no tolerance authority",
            "event_candidate": "NONE_GOVERNED; physical event predicates unavailable",
            "uncertainty_boundary_candidate": "UNKNOWN; no physical uncertainty bound",
            "model_authority_boundary": "NOT_REACHED_BY_DIAGNOSTIC_WINDOW"},
        "pattern_generalization": [
            {"pattern": "RK4 cross-resolution discrepancy", "classification": "CASE_SPECIFIC_DIAGNOSTIC",
             "generalization_requirement": "repeat across governed model states/forcing and establish numerical acceptance criteria"},
            {"pattern": "refinement decreases exact-rotation error", "classification": "NUMERICAL_CONTROL_PATTERN",
             "generalization_requirement": "qualify across supported integrators, states, and forcing scales before a runtime rule"},
            {"pattern": "convergence cannot define physical rift transition", "classification": "MODEL_GAP_PATTERN",
             "generalization_requirement": "requires a governed transition model and event-coverage qualification"},
            {"pattern": "no physical uncertainty bounds", "classification": "AUTHORITY_GAP_PATTERN",
             "generalization_requirement": "requires explicit authority for uncertainty and acceptance bounds"}],
        "convergence_closes_model_or_authority_gap": False,
        "unavailable_or_unknown_physical_outputs": ["rift process state", "physical extension/opening",
            "rift width", "crustal thinning", "interface accommodation/regime", "junction response",
            "event/topology predicate status", "support-membership validity"],
        "publication_performed": False}


def _median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered)//2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle-1]+ordered[middle])/2.0


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                               ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def run_diagnostic(repository_root: Path, canonical_root: Path, output_dir: Path,
                   window_fraction: float = 0.25) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    canonical = canonical_root.resolve(strict=True)
    output = _assert_output_isolated(output_dir, root, canonical)
    before = canonical_snapshot(canonical)
    input_nodes, omega, input_identity = _verified_b6k_inputs(root, canonical)
    computed = compute_multiresolution(input_nodes, omega,
        REVALIDATION_HORIZON_YEARS, window_fraction)
    replayed = compute_multiresolution(input_nodes, omega,
        REVALIDATION_HORIZON_YEARS, window_fraction)
    if computed != replayed:
        raise ValueError("repeated deterministic shadow computation differs")
    after = canonical_snapshot(canonical)
    if before != after:
        raise ValueError("canonical WORLD_HISTORY changed during read-only shadow run")

    # No numerical tolerance is authorized. Informative means a deterministic
    # numerical comparison exists, not that any physical model is qualified.
    has_motion = any(row["samples"][-1]["max_rigid_point_displacement_m"] > 0
                     for row in computed["resolution_ladder"])
    has_resolution_signal = any(row["max_trajectory_difference_m"] > 0
                                for row in computed["cross_resolution_comparison"])
    decision = ("PASS_B6N8A_DIAGNOSTIC_SHADOW_PROPAGATION_INFORMATIVE"
                if has_motion and has_resolution_signal else
                "PASS_B6N8A_DIAGNOSTIC_SHADOW_PROPAGATION_LIMITED_INFORMATION")
    result = {"schema": "ARCANA_R6_B6N8A_SHADOW_RESULT_V1",
        "decision": decision,
        "source_branch": "r6/b6n8a-multiresolution-diagnostic-shadow-propagation",
        "source_baseline_commit": "54ea550ecc623760ee5115a9033b38cb963a4584",
        "input_identity": input_identity, "experiment": computed,
        "deterministic_replay": {"passed": True,
            "trajectory_hashes_by_step_count": {str(row["step_count"]): row["trajectory_sample_coordinates_sha256"]
                for row in computed["resolution_ladder"]}},
        "observable_registry": OBSERVABLE_REGISTRY,
        "b6n7_gap_mapping": [
            {"requirement":"evolvable process-state vector/evolution law","coverage":"NO_SIGNAL; MODEL_REQUIRED"},
            {"requirement":"forcing","coverage":"DIRECT_EXISTING_SIGNAL: restricted pair plate Euler vectors"},
            {"requirement":"interface response","coverage":"PARTIAL_DIAGNOSTIC_ONLY: relative geometry proxy; physical response remains unknown"},
            {"requirement":"transition predicates and topology coverage","coverage":"NO_SIGNAL; AUTHORITY_REQUIRED"},
            {"requirement":"support-membership validity","coverage":"INVARIANT_INPUT_IDENTITY_ONLY; validity/remapping authority absent"},
            {"requirement":"uncertainty and physical bounds","coverage":"MODEL/AUTHORITY UNCERTAINTY UNKNOWN; no physical acceptance thresholds"}],
        "sample_retention_analysis": {"WORLD_HISTORY_publication_prohibited": True,
            "initial_POST_EVENT_sample":"MANDATORY_CAUSAL_BOUNDARY_ALREADY_EXISTS; no new record",
            "intermediate_samples":"INSIGNIFICANT_NUMERICAL_SAMPLE_FOR_THIS_DIAGNOSTIC_ONLY; not production significance adjudication",
            "event_candidate":"NONE_DETECTED_OR_GOVERNED; UNKNOWN predicates remain unresolved",
            "model_authority_boundary":"NOT_REACHED; run stops at one quarter of the model-scope bound",
            "uncertainty_boundary":"NOT_RESOLVED; no threshold authority",
            "sparse_reconstruction_tolerance":"ABSENT; no compression acceptance claim"},
        "canonical_invariance": {"before": before, "after": after, "identical": True,
            "live_view_preflight": input_identity["canonical_live_view_preflight"],
            "physical_epochs": 2,"post_event_state_id": POST_EVENT_ID,
            "post_event_payload_sha256": POST_EVENT_PAYLOAD_SHA256,"T2_present": False},
        "authorization_gates": {"SECOND_DT_SELECTED":False,"dt2_years":None,"T2_CREATED":False,
            "B6O_authorized":False,"physical_rift_model_selected":False,"mechanics_executed":False,
            "canonical_forward_propagation_executed":False,"topology_transition_executed":False,
            "WORLD_HISTORY_unchanged":True},
        "conditional_scope": {"fixed_structural_regime_assumed_for_diagnostic_only": True,
            "structural_regime_physical_validity_established": False,
            "positive_physical_propagation_interval_established": False}}
    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "B6N8A_SHADOW_RESULT.json", result)
    return result
