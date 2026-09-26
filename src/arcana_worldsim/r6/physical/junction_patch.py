"""Deterministic local overlap-derived junction patches for R6 reference fields.

Membership is evaluated on the sphere from the three canonical incident
corridors. The tangent chart is used only to extract/refine a numerical mesh;
it does not add geological support. Any unresolved topology or port condition
fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable

import numpy as np

from .boundary_geometry import BoundaryFeature, SphericalSegment, two_plate_corridor_weights, unit_xyz


PATCH_ALGORITHM = "R6_SPHERICAL_TWO_OF_THREE_CORRIDOR_MEMBERSHIP_TOPOLOGY_V3"


@dataclass(frozen=True, slots=True)
class JunctionPatch:
    junction_id: str
    width_m: float
    plate_ids: tuple[int, int, int]
    boundary_ids: tuple[str, str, str]
    boundary_xy_m: tuple[tuple[float, float], ...]
    ports: tuple[str, ...]
    nodal_weights: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]
    status: str
    reason: str | None
    metrics: dict
    provenance: dict


def _exp_map(center: np.ndarray, east: np.ndarray, north: np.ndarray,
             x: float, y: float, radius: float) -> np.ndarray:
    distance = math.hypot(x, y)
    if distance == 0:
        return center
    theta = distance / radius
    tangent = (x * east + y * north) / distance
    q = math.cos(theta) * center + math.sin(theta) * tangent
    return q / np.linalg.norm(q)


def _latlon(point: np.ndarray) -> tuple[float, float]:
    return math.degrees(math.asin(float(np.clip(point[2], -1, 1)))), math.degrees(math.atan2(point[1], point[0]))


def _smoothstep(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _ear_clip(points: list[tuple[float, float]]) -> tuple[tuple[int, int, int], ...]:
    """Stable ear clipping of one simple CCW polygon; raises if no valid ear."""
    if len(points) < 3:
        raise ValueError("patch boundary has fewer than three vertices")
    idx = list(range(len(points)))
    area2 = math.fsum(points[i][0] * points[(i + 1) % len(points)][1]
                      - points[(i + 1) % len(points)][0] * points[i][1] for i in idx)
    if abs(area2) <= 1e-12:
        raise ValueError("patch boundary is degenerate")
    if area2 < 0:
        idx.reverse()
    out = []
    eps = 1e-10
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    def inside(p, a, b, c):
        return (cross(a,b,p) >= -eps and cross(b,c,p) >= -eps and cross(c,a,p) >= -eps)
    while len(idx) > 3:
        found = False
        for k in range(len(idx)):
            ia, ib, ic = idx[k-1], idx[k], idx[(k+1) % len(idx)]
            a,b,c = points[ia],points[ib],points[ic]
            if cross(a,b,c) <= eps:
                continue
            if any(inside(points[j],a,b,c) for j in idx if j not in (ia,ib,ic)):
                continue
            out.append((ia,ib,ic)); del idx[k]; found = True; break
        if not found:
            raise ValueError("deterministic ear clipping found no valid ear (self-intersection or degeneracy)")
    out.append(tuple(idx))
    return tuple(out)


def _component_from_grid(mask: np.ndarray, seed: tuple[int,int]) -> np.ndarray:
    rows, cols = mask.shape
    if not mask[seed]:
        raise ValueError("canonical junction is not in the sampled two-corridor overlap")
    seen = np.zeros_like(mask, dtype=bool)
    stack = [seed]; seen[seed] = True
    while stack:
        r,c = stack.pop()
        for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if 0 <= rr < rows and 0 <= cc < cols and mask[rr,cc] and not seen[rr,cc]:
                seen[rr,cc] = True; stack.append((rr,cc))
    return seen


def analyze_membership_topology(membership: np.ndarray, seed: tuple[int, int]) -> dict:
    """Extract the central >=2-corridor component and its singleton interfaces.

    ``membership`` is a 3-bit mask at each local arrangement node.  Port
    identity is derived exclusively from 4-neighbour patch/exclusive-region
    adjacency; no boundary-normal probes participate in this authority.
    The returned interface segments are numerical mesh edges in grid-index
    coordinates and must be associated with any refined contour separately.
    """
    masks = np.asarray(membership, dtype=np.uint8)
    if masks.ndim != 2 or np.any(masks > 7):
        raise ValueError("membership must be a 2-D three-bit mask array")
    multi = np.fromiter((int(v).bit_count() >= 2 for v in masks.flat),
                        dtype=bool, count=masks.size).reshape(masks.shape)
    component = _component_from_grid(multi, seed)
    active_masks = {int(v): int(np.count_nonzero(component & (masks == v)))
                    for v in range(8)}
    # Interfaces are unit grid edges between the central patch and exactly
    # one exclusive corridor node (mask 001, 010, or 100).
    edges: dict[int, list[tuple[tuple[int, int], tuple[int, int]]]] = {1: [], 2: [], 4: []}
    nr, nc = masks.shape
    for r, c in zip(*np.nonzero(component)):
        for rr, cc, a, b in (
            (r - 1, c, (r, c), (r, c + 1)),
            (r + 1, c, (r + 1, c), (r + 1, c + 1)),
            (r, c - 1, (r, c), (r + 1, c)),
            (r, c + 1, (r, c + 1), (r + 1, c + 1)),
        ):
            if 0 <= rr < nr and 0 <= cc < nc and not component[rr, cc]:
                label = int(masks[rr, cc])
                if label in edges:
                    edges[label].append((a, b))
    port_components = {}
    for label, label_edges in edges.items():
        # Edge connectivity uses shared mesh vertices. It deliberately keeps
        # disconnected interfaces separate instead of merging by corridor ID.
        by_vertex: dict[tuple[int, int], list[int]] = {}
        for i, (a, b) in enumerate(label_edges):
            by_vertex.setdefault(a, []).append(i)
            by_vertex.setdefault(b, []).append(i)
        unseen = set(range(len(label_edges)))
        comps = []
        while unseen:
            root = min(unseen)
            unseen.remove(root)
            stack = [root]
            members = []
            while stack:
                i = stack.pop()
                members.append(i)
                for v in label_edges[i]:
                    for j in by_vertex[v]:
                        if j in unseen:
                            unseen.remove(j)
                            stack.append(j)
            comps.append(members)
        port_components[str(label)] = [
            {"edge_count": len(comp),
             "edges_grid_ij": [[[int(v) for v in label_edges[i][0]],
                                [int(v) for v in label_edges[i][1]]] for i in comp]}
            for comp in comps
        ]
    exclusive_counts = {str(label): int(np.count_nonzero(masks == label))
                        for label in (1, 2, 4)}
    def count_components(label_mask):
        unseen = np.asarray(label_mask, dtype=bool).copy()
        count = 0
        while unseen.any():
            seed_cell = tuple(int(v) for v in np.argwhere(unseen)[0])
            component = _component_from_grid(unseen, seed_cell)
            unseen[component] = False
            count += 1
        return count
    exclusive_component_counts = {str(label): count_components(masks == label)
                                  for label in (1, 2, 4)}
    return {"membership_mask_counts_in_central_domain": {f"{i:03b}": int(np.count_nonzero(masks == i))
                                                          for i in range(8)},
            "membership_mask_counts_in_patch": {f"{i:03b}": active_masks[i] for i in range(8)},
            "exclusive_region_node_counts": exclusive_counts,
            "patch_node_count": int(component.sum()),
            "patch_component_count": 1,
            "domain_boundary_touched_by_patch": bool(component[0, :].any() or component[-1, :].any()
                                                      or component[:, 0].any() or component[:, -1].any()),
            "interface_edges_by_singleton_mask": port_components,
            "port_component_counts": {str(k): len(v) for k, v in port_components.items()},
            "exclusive_region_component_counts": exclusive_component_counts,
            "patch_component": component}


def evaluate_junction_membership(junction: dict, incident_corridors: Iterable[dict],
                                 width_m: float, cells_per_width: int = 32,
                                 sphere_radius_m: float = 6_371_000.0,
                                 corridor_query: Callable[[float, float, float], dict[str, float]] | None = None,
                                 domain_radius_m: float | None = None,
                                 distance_cache: dict | None = None):
    """Build one local three-bit membership grid without contour/P1 work."""
    records = tuple(sorted(incident_corridors, key=lambda x: x["boundary_id"]))
    if len(records) != 3 or cells_per_width < 8 or cells_per_width % 2:
        raise ValueError("membership audit requires three corridors and even resolution >=8")
    extent = float(width_m if domain_radius_m is None else domain_radius_m)
    if not math.isfinite(extent) or extent <= 0:
        raise ValueError("domain_radius_m must be positive and finite")
    n = int(cells_per_width)
    axis = np.linspace(-extent, extent, 2 * n + 1)
    center = unit_xyz(float(junction["lat_deg"]), float(junction["lon_deg"]))
    lat0, lon0 = math.radians(junction["lat_deg"]), math.radians(junction["lon_deg"])
    east = np.array((-math.sin(lon0), math.cos(lon0), 0.0))
    north = np.array((-math.sin(lat0)*math.cos(lon0), -math.sin(lat0)*math.sin(lon0), math.cos(lat0)))
    def distances(x, y):
        key=(round(float(x),6),round(float(y),6))
        if distance_cache is not None and key in distance_cache:
            return distance_cache[key]
        p = _exp_map(center, east, north, x, y, sphere_radius_m)
        lat, lon = _latlon(p)
        if corridor_query is not None:
            hits = corridor_query(lat, lon, width_m / 2)
            values=tuple(hits.get(str(r.get("component_id", r["boundary_id"])), math.inf) for r in records)
        else:
            values=tuple(min(s.distance_m(lat, lon, sphere_radius_m) for s in r["segments"]) for r in records)
        if distance_cache is not None:
            distance_cache[key]=values
        return values
    membership = np.zeros((len(axis), len(axis)), dtype=np.uint8)
    for ir, y in enumerate(axis):
        for ic, x in enumerate(axis):
            membership[ir, ic] = sum((1 << k) for k, d in enumerate(distances(x, y))
                                     if d <= width_m / 2)
    summary = analyze_membership_topology(membership, (n, n))
    summary.pop("patch_component")
    summary.update({"grid_spacing_m": float(axis[1]-axis[0]),
                    "domain_radius_m": extent,
                    "domain_radius_to_width_ratio": extent / float(width_m)})
    return membership, axis, summary


def branch_exclusive_run(masks: Iterable[int], singleton_bit: int,
                         initial_sample_count: int, topological_limit_sample: int,
                         minimum_persistent_samples: int = 2) -> dict:
    """Find a persistent exclusive-corridor run without crossing a topology limit.

    Samples are ordered outward along one already-resolved canonical branch.
    This helper is geometry-agnostic; callers must supply the branch-following
    spherical samples and their three-bit membership masks.
    """
    values = tuple(int(v) for v in masks)
    if singleton_bit not in (1, 2, 4) or any(v < 0 or v > 7 for v in values):
        raise ValueError("branch masks require a three-bit mask and singleton bit 1, 2, or 4")
    if minimum_persistent_samples < 1 or initial_sample_count < 0:
        raise ValueError("positive persistence and nonnegative initial domain required")
    limit = min(len(values), max(0, int(topological_limit_sample)))
    initial = min(limit, int(initial_sample_count))
    def find_run(end):
        run = 0
        for i, value in enumerate(values[:end]):
            run = run + 1 if value == singleton_bit else 0
            if run >= minimum_persistent_samples:
                return i - run + 1
        return None
    found = find_run(initial)
    if found is not None:
        status = "EXCLUSIVE_CORRIDOR_FOUND"
    else:
        found = find_run(limit)
        if found is not None:
            status = "LOCAL_DOMAIN_EXPANSION_REQUIRED"
        elif limit < len(values):
            status = "NO_EXCLUSIVE_CORRIDOR_BEFORE_TOPOLOGICAL_LIMIT"
        else:
            status = "LOCAL_DOMAIN_EXHAUSTED_BEFORE_TOPOLOGICAL_LIMIT"
    return {"status": status, "first_persistent_sample_index": found,
            "singleton_bit": singleton_bit, "initial_sample_count": initial,
            "topological_limit_sample": limit,
            "minimum_persistent_samples": minimum_persistent_samples}


def deterministic_domain_radii(initial_radius_m: float, topology_limit_m: float,
                               max_level: int = 4) -> tuple[float, ...]:
    """Dyadic numerical search radii strictly inside the next-junction limit."""
    if (not math.isfinite(initial_radius_m) or initial_radius_m <= 0
            or not math.isfinite(topology_limit_m) or topology_limit_m <= 0
            or max_level < 0):
        raise ValueError("positive finite radii and nonnegative max_level required")
    safe_limit = math.nextafter(float(topology_limit_m), 0.0)
    radii = []
    for level in range(max_level + 1):
        candidate = min(float(initial_radius_m) * (2 ** level), safe_limit)
        if not radii or candidate > radii[-1]:
            radii.append(candidate)
        if candidate >= safe_limit:
            break
    return tuple(radii)


def classify_trace_reach(patch_status: str, reason: str | None,
                         validation_passed: bool | None = None) -> tuple[str, str]:
    """Distinguish a trace failure from construction blockers before tracing."""
    if validation_passed is not None:
        return ("TRACE_PASS" if validation_passed else "TRACE_FAIL",
                "TRACE_CONVERGED" if validation_passed else "TRACE_NONCONVERGENT")
    text = (reason or "").lower()
    if patch_status == "BOUND":
        return "TRACE_NOT_REACHED", "TRACE_VALIDATION_NOT_INVOKED"
    if "corridor trace tolerance unmet" in text or "trace subdivision exceeded" in text:
        return "TRACE_FAIL", "TRACE_REFINEMENT_LIMIT_REACHED"
    if "corner port trace disagreement" in text:
        return "TRACE_NOT_REACHED", "PORT_CORNER_DIRICHLET_CONFLICT"
    if "port_extraction_implementation_failure" in text:
        return "TRACE_NOT_REACHED", "PORT_GEOMETRY_INVALID"
    return "TRACE_NOT_REACHED", "PATCH_CONSTRUCTION_BLOCKED"


def dirichlet_corner_errors(left_weights, right_weights, expected_weights,
                            left_point_xyz, right_point_xyz, tolerance=1e-4):
    """Compare two port traces at one identical spherical point, without averaging."""
    left=tuple(float(v) for v in left_weights); right=tuple(float(v) for v in right_weights)
    expected=tuple(float(v) for v in expected_weights)
    lp=tuple(float(v) for v in left_point_xyz); rp=tuple(float(v) for v in right_point_xyz)
    if not (len(left)==len(right)==len(expected)) or len(lp)!=3 or len(rp)!=3:
        raise ValueError("corner traces and expected vector must share dimensions")
    if any(not math.isfinite(v) for v in (*left,*right,*expected,*lp,*rp)):
        raise ValueError("corner comparison requires finite vectors")
    if max(abs(a-b) for a,b in zip(lp,rp))>1e-12:
        raise ValueError("corner port evaluators must use the same spherical point")
    corner=max(abs(a-b) for a,b in zip(left,right))
    pure=max(max(abs(a-b) for a,b in zip(left,expected)),
             max(abs(a-b) for a,b in zip(right,expected)))
    return {"E_corner":corner,"E_expected_pure_plate":pure,
            "same_spherical_point_used_for_both_port_evaluators":True,
            "status":"CORNER_COMPATIBLE" if corner<=tolerance and pure<=tolerance
                     else "CORNER_DIRICHLET_CONFLICT"}


def classify_corner_refinement(errors, tolerance=1e-4, relative_plateau_tolerance=0.01,
                               expected_errors=None):
    """Classify compatibility at the finest shared-point evaluation.

    Coarser levels document convergence; they are not themselves the final
    Dirichlet condition. Both the two-port mismatch and pure-plate reference
    mismatch must meet tolerance at the finest level when the latter is given.
    """
    values=tuple(float(v) for v in errors)
    if not values or any(not math.isfinite(v) or v<0 for v in values):
        raise ValueError("corner refinement errors must be finite nonnegative values")
    expected=(tuple(float(v) for v in expected_errors)
              if expected_errors is not None else ())
    if expected and (len(expected)!=len(values) or
                     any(not math.isfinite(v) or v<0 for v in expected)):
        raise ValueError("expected corner errors must match finite nonnegative refinement values")
    if values[-1]<=tolerance and (not expected or expected[-1]<=tolerance):
        return "CORNER_COMPATIBLE"
    if len(values)>=2 and values[-1]>tolerance and abs(values[-1]-values[-2])<=max(
            1e-8,relative_plateau_tolerance*values[-2]):
        return "CORNER_DIRICHLET_CONFLICT"
    if len(expected)>=2 and expected[-1]>tolerance and abs(expected[-1]-expected[-2])<=max(
            1e-8,relative_plateau_tolerance*expected[-2]):
        return "CORNER_DIRICHLET_CONFLICT"
    return "CORNER_NUMERICALLY_UNRESOLVED"


def _extract_ring(component: np.ndarray) -> list[tuple[int,int]]:
    """Boundary of unioned grid cells; reject holes/multiple boundary rings."""
    edges = set()
    nr,nc = component.shape
    for r,c in zip(*np.nonzero(component)):
        # CCW directed cell edges in (column,row) coordinates.
        for dr,dc,a,b in ((-1,0,(c,r),(c+1,r)),(0,1,(c+1,r),(c+1,r+1)),
                          (1,0,(c+1,r+1),(c,r+1)),(0,-1,(c,r+1),(c,r))):
            rr,cc=r+dr,c+dc
            if rr<0 or rr>=nr or cc<0 or cc>=nc or not component[rr,cc]:
                edges.add((a,b))
    outgoing={}
    for a,b in edges: outgoing.setdefault(a,[]).append(b)
    if any(len(v)!=1 for v in outgoing.values()):
        raise ValueError("overlap boundary is not one simple degree-2 ring")
    start=min(outgoing)
    ring=[start]; cur=start
    for _ in range(len(edges)+1):
        cur=outgoing[cur][0]
        if cur==start: break
        ring.append(cur)
    if cur!=start or len(ring)!=len(edges):
        raise ValueError("overlap boundary is disconnected or contains a hole")
    # Remove exactly collinear grid vertices; trace refinement reintroduces
    # points wherever inherited corridor data require them.
    changed=True
    while changed and len(ring)>3:
        changed=False; clean=[]
        for i,p in enumerate(ring):
            a,b=ring[i-1],ring[(i+1)%len(ring)]
            if (p[0]-a[0])*(b[1]-p[1])==(p[1]-a[1])*(b[0]-p[0]): changed=True
            else: clean.append(p)
        ring=clean
    return ring


def _extract_contour(component: np.ndarray, axis: np.ndarray, inside_at,
                     seed_xy=(0.0,0.0), root_tolerance_m: float=1.0):
    """Marching-squares contour with spherical-membership edge bisection.

    The input mask identifies the central sampled component. Contour points
    are then located on the actual corridor-membership transition rather than
    on the half-cell-shifted boundary of a union of raster pixels.
    """
    nr,nc=component.shape
    if len(axis)!=nr or nr!=nc: raise ValueError("contour grid must be square and axis-aligned")
    if not math.isfinite(root_tolerance_m) or root_tolerance_m<=0:
        raise ValueError("positive finite contour root tolerance required")
    h=float(axis[1]-axis[0]); crossings={}; segments=[]
    def edge_point(kind,r,c,ia,ib):
        key=(kind,r,c)
        if key in crossings: return key
        pa=(float(axis[c]),float(axis[r])) if kind=="H" else (float(axis[c]),float(axis[r]))
        pb=(float(axis[c+1]),float(axis[r])) if kind=="H" else (float(axis[c]),float(axis[r+1]))
        va=bool(component[ia]); vb=bool(component[ib])
        if va==vb: raise ValueError("marching contour requested on a non-crossing edge")
        lo=0.0; hi=1.0; vlo=va
        edge_length=math.hypot(pb[0]-pa[0],pb[1]-pa[1])
        for _ in range(48):
            if edge_length*(hi-lo)<=root_tolerance_m:
                break
            mid=(lo+hi)*0.5; point=(pa[0]*(1-mid)+pb[0]*mid,pa[1]*(1-mid)+pb[1]*mid)
            vm=bool(inside_at(*point))
            if vm==vlo: lo=mid
            else: hi=mid
        t=(lo+hi)*0.5; crossings[key]=(pa[0]*(1-t)+pb[0]*t,pa[1]*(1-t)+pb[1]*t)
        return key
    for r in range(nr-1):
        for c in range(nc-1):
            corners=((r,c),(r,c+1),(r+1,c+1),(r+1,c))
            vals=tuple(bool(component[q]) for q in corners)
            if all(vals) or not any(vals): continue
            edge_defs=(("H",r,c,0,1),("V",r,c+1,1,2),
                       ("H",r+1,c,3,2),("V",r,c,0,3))
            found=[]
            for edge in range(4):
                kind,er,ec,a,b=edge_defs[edge]
                if vals[a]!=vals[b]: found.append(edge_point(kind,er,ec,corners[a],corners[b]))
            if len(found)==2:
                segments.append((found[0],found[1])); continue
            if len(found)==4:
                center_inside=bool(inside_at((axis[c]+axis[c+1])/2,(axis[r]+axis[r+1])/2))
                # Resolve the checkerboard case by the actual spherical
                # predicate at the cell centre (the asymptotic-decider rule).
                if vals[0] and vals[2]:
                    pairs=((0,1),(2,3)) if center_inside else ((3,0),(1,2))
                else:
                    pairs=((3,0),(1,2)) if center_inside else ((0,1),(2,3))
                crossing_edges=[e for e in range(4)
                                if vals[edge_defs[e][3]]!=vals[edge_defs[e][4]]]
                by_edge={edge:found[k] for k,edge in enumerate(crossing_edges)}
                segments.extend((by_edge[a],by_edge[b]) for a,b in pairs)
                continue
            raise ValueError(f"marching contour has {len(found)} crossings in cell {(r,c)}")
    adjacency={}
    for a,b in segments:
        adjacency.setdefault(a,[]).append(b); adjacency.setdefault(b,[]).append(a)
    if not adjacency or any(len(v)!=2 for v in adjacency.values()):
        raise ValueError("spherical-membership contour is open or non-manifold")
    unseen=set(adjacency); rings=[]
    while unseen:
        start=min(unseen,key=lambda k:crossings[k]); ring=[]; prev=None; cur=start
        for _ in range(len(adjacency)+1):
            ring.append(crossings[cur]); unseen.discard(cur)
            nxt=next(q for q in sorted(adjacency[cur],key=lambda k:crossings[k]) if q!=prev)
            prev,cur=cur,nxt
            if cur==start: break
        if cur!=start: raise ValueError("spherical-membership contour loop did not close")
        rings.append(ring)
    def contains(poly,p):
        x,y=p; inside=False
        for i,(ax,ay) in enumerate(poly):
            bx,by=poly[(i+1)%len(poly)]
            if (ay>y)!=(by>y) and x < (bx-ax)*(y-ay)/(by-ay)+ax: inside=not inside
        return inside
    selected=[ring for ring in rings if contains(ring,seed_xy)]
    if len(selected)!=1: raise ValueError(f"central spherical-membership contour is not unique ({len(selected)} enclosing rings)")
    ring=selected[0]
    area=math.fsum(ring[i][0]*ring[(i+1)%len(ring)][1]-ring[(i+1)%len(ring)][0]*ring[i][1] for i in range(len(ring)))
    if area<0: ring.reverse()
    # Guard any numerically degenerate consecutive contour vertices.
    if any(math.hypot(ring[(i+1)%len(ring)][0]-p[0],ring[(i+1)%len(ring)][1]-p[1]) < h*1e-10 for i,p in enumerate(ring)):
        raise ValueError("spherical-membership contour contains a degenerate edge")
    return ring


def _refine_trace_edge(a, b, wa, wb, port, weight_at, tolerance, max_depth, edge_id):
    """Dyadically refine one port edge using exact corridor nodal values.

    ``weight_at(port, xy)`` returns the three plate weights from the governed
    two-plate corridor operator.  Quarter/midpoint/three-quarter probes are
    deterministic; no endpoint fitting or averaging occurs.
    """
    worst=0.0; refinements=0; worst_scale=math.hypot(b[0]-a[0],b[1]-a[1])
    def visit(p0,p1,w0,w1,depth):
        nonlocal worst,refinements,worst_scale
        samples=[]; error=0.0
        for t in (0.25,0.5,0.75):
            point=(p0[0]*(1-t)+p1[0]*t,p0[1]*(1-t)+p1[1]*t)
            exact=weight_at(port,point)
            linear=tuple((1-t)*w0[k]+t*w1[k] for k in range(3))
            error=max(error,max(abs(linear[k]-exact[k]) for k in range(3)))
            samples.append((point,exact))
        worst=max(worst,error)
        if error<=tolerance:
            return [(p0,w0)]
        if depth>=max_depth:
            worst_scale=min(worst_scale,math.hypot(p1[0]-p0[0],p1[1]-p0[1]))
            raise ValueError(f"corridor trace tolerance unmet at depth {depth}: branch={port}, edge={edge_id}, residual={error:.9g}, smallest edge scale={worst_scale:.9g} m")
        mid,wm=samples[1]
        refinements+=1
        return visit(p0,mid,w0,wm,depth+1)+visit(mid,p1,wm,w1,depth+1)
    nodes=visit(a,b,wa,wb,0)
    return nodes,{"max_residual_seen":worst,"subdivision_count":refinements,
                  "final_edge_count":len(nodes),"smallest_edge_scale_m":worst_scale}


def build_junction_patch(junction: dict, incident_corridors: Iterable[dict], width_m: float,
                         geometry_policy: dict, parent_plate_grid: np.ndarray,
                         sphere_radius_m: float = 6_371_000.0,
                         corridor_query: Callable[[float,float,float],dict[str,float]] | None = None,
                         membership_grid: np.ndarray | None = None) -> JunctionPatch:
    """Extract the central component covered by at least two incident corridors.

    Corridor record fields: boundary_id, plate_pair, segments (SphericalSegment
    sequence). Geometry policy fields are numerical: cells_per_width (even),
    trace_tolerance, trace_max_depth and max_boundary_nodes.
    """
    records=tuple(sorted(incident_corridors,key=lambda x:x["boundary_id"]))
    jid=str(junction["junction_id"]); ids=tuple(str(r["boundary_id"]) for r in records)
    plates=tuple(sorted({int(p) for r in records for p in r["plate_pair"]}))
    corner_metrics=[]
    def fail(reason, metrics=None):
        details=dict(metrics or {})
        if corner_metrics:
            details["corner_compatibility"]=list(corner_metrics)
        return JunctionPatch(jid,float(width_m),plates[:3],ids,(),(),(),(),"INVALID",reason,details,
                             {"algorithm":PATCH_ALGORITHM,"numerical_refinement_only":True})
    if len(records)!=3 or len(plates)!=3 or len(set(ids))!=3:
        return fail("junction must bind exactly three distinct canonical corridors and plates")
    if not math.isfinite(width_m) or width_m<=0: return fail("width must be positive and finite")
    n=int(geometry_policy.get("cells_per_width",32))
    if n<8 or n%2: return fail("cells_per_width must be even and >=8")
    h=float(width_m)/n
    # Numerical search window only; any central component reaching this
    # boundary is rejected, never clipped into a purported physical patch.
    extent=float(geometry_policy.get("domain_radius_m", width_m))
    if not math.isfinite(extent) or extent <= 0:
        return fail("domain_radius_m must be positive and finite")
    count=int(round(2*extent/h))+1
    # Membership samples are uniformly spaced cell centres including the
    # junction; extracted integer ring vertices are the intervening corners.
    axis=np.linspace(-extent,extent,count)
    center=unit_xyz(float(junction["lat_deg"]),float(junction["lon_deg"]))
    lat0,lon0=math.radians(junction["lat_deg"]),math.radians(junction["lon_deg"])
    east=np.array((-math.sin(lon0),math.cos(lon0),0.0)); north=np.array((-math.sin(lat0)*math.cos(lon0),-math.sin(lat0)*math.sin(lon0),math.cos(lat0)))
    membership=np.empty((count,count),dtype=np.uint8)
    ownership=np.asarray(parent_plate_grid)
    if ownership.shape!=(180,360): return fail("parent plate grid must be 180x360")
    def distances(x,y):
        p=_exp_map(center,east,north,x,y,sphere_radius_m); lat,lon=_latlon(p)
        if corridor_query is not None:
            hits=corridor_query(lat,lon,width_m/2)
            return [hits.get(str(r.get("component_id",r["boundary_id"])),math.inf) for r in records]
        return [min(seg.distance_m(lat,lon,sphere_radius_m) for seg in r["segments"]) for r in records]
    if membership_grid is not None:
        candidate=np.asarray(membership_grid,dtype=np.uint8)
        if candidate.shape != membership.shape or np.any(candidate>7):
            return fail("precomputed membership grid shape/mask invalid")
        membership=candidate.copy()
    else:
        for ir,y in enumerate(axis):
            for ic,x in enumerate(axis):
                ds=distances(x,y)
                membership[ir,ic]=sum((1 << k) for k,d in enumerate(ds) if d<=width_m/2)
    grid=np.fromiter((int(v).bit_count()>=2 for v in membership.flat),
                     dtype=bool,count=membership.size).reshape(membership.shape)
    seed=(count//2,count//2)
    topology = None
    try:
        topology=analyze_membership_topology(membership,seed)
        component=topology["patch_component"]
        if component[0,:].any() or component[-1,:].any() or component[:,0].any() or component[:,-1].any():
            raise ValueError("central overlap reaches local extraction boundary; expand chart/domain")
        def spherical_overlap(x,y):
            return sum(d<=width_m/2 for d in distances(x,y))>=2
        root_tolerance=float(geometry_policy.get("contour_root_tolerance_m",1.0))
        xy=_extract_contour(component,axis,spherical_overlap,root_tolerance_m=root_tolerance)
        # Port identities come from the categorical grid's patch/exclusive
        # region interfaces. Refined contour edges are associated with those
        # already-authoritative mesh interfaces by deterministic nearest-edge
        # matching, bounded to two source cells. No normal sampling labels a
        # port.
        interface_edges=[]
        for mask_value, components in topology["interface_edges_by_singleton_mask"].items():
            for component_index, port_component in enumerate(components):
                for edge in port_component["edges_grid_ij"]:
                    (r0,c0),(r1,c1)=edge
                    p0=(float(axis[c0]),float(axis[r0])); p1=(float(axis[c1]),float(axis[r1]))
                    interface_edges.append((int(mask_value),component_index,p0,p1))
        if not interface_edges:
            raise ValueError("SINGLETON_CORRIDOR_REGION_MISSING: patch has no exclusive-region adjacency")
        ports=[]; edge_start=[]; edge_end=[]; port_match_distances=[]
        for i,(x,y) in enumerate(xy):
            a=xy[i]; b=xy[(i+1)%len(xy)]
            mx=(a[0]+b[0])/2; my=(a[1]+b[1])/2
            candidates=[]
            for mask_value,component_index,p0,p1 in interface_edges:
                qx=(p0[0]+p1[0])/2; qy=(p0[1]+p1[1])/2
                distance=math.hypot(mx-qx,my-qy)
                candidates.append((distance,mask_value,component_index))
            distance,mask_value,component_index=min(candidates)
            if distance>4.0*h:
                raise ValueError(f"PORT_EXTRACTION_IMPLEMENTATION_FAILURE: refined contour edge lacks adjacent singleton mesh interface (distance={distance:.6g} m)")
            port_index=mask_value.bit_length()-1
            port=ids[port_index]; ports.append(port); port_match_distances.append(distance)
            record=records[port_index]
            pair=tuple(sorted(map(int,record["plate_pair"])))
            feature=BoundaryFeature(port,pair[0],pair[1],tuple(record["segments"]))
            def weights_at(px,py):
                plat,plon=_latlon(_exp_map(center,east,north,px,py,sphere_radius_m))
                row=min(179,max(0,int(math.floor(plat+90)))); col=int(math.floor((plon+180)%360))%360
                owner=int(ownership[row,col])
                if owner not in pair: raise ValueError("boundary port sample has no incident parent-plate side")
                w={p:0.0 for p in plates}
                w.update(two_plate_corridor_weights(feature,plat,plon,width_m,owner,sphere_radius_m))
                return tuple(w[p] for p in plates)
            edge_start.append(weights_at(*xy[i])); edge_end.append(weights_at(*xy[(i+1)%len(xy)]))
        nodal=[]
        record_by_id={r["boundary_id"]:r for r in records}
        corner_tolerance=float(geometry_policy.get("corner_tolerance",1e-4))
        for i in range(len(xy)):
            left=edge_end[i-1]; right=edge_start[i]
            if ports[i-1] != ports[i]:
                left_pair=set(map(int,record_by_id[ports[i-1]]["plate_pair"]))
                right_pair=set(map(int,record_by_id[ports[i]]["plate_pair"]))
                shared=left_pair & right_pair
                expected=tuple(1.0 if p in shared else 0.0 for p in plates) if len(shared)==1 else None
                lat,lon=_latlon(_exp_map(center,east,north,*xy[i],sphere_radius_m))
                point=_exp_map(center,east,north,*xy[i],sphere_radius_m)
                comparison=(dirichlet_corner_errors(left,right,expected,point,point,corner_tolerance)
                            if expected is not None else {"E_corner":max(abs(a-b) for a,b in zip(left,right)),
                                "E_expected_pure_plate":None,
                                "same_spherical_point_used_for_both_port_evaluators":True,
                                "status":"CORNER_DIRICHLET_CONFLICT"})
                corner_metrics.append({"point_xy_m":list(xy[i]),"point_lat_lon_deg":[lat,lon],
                    "point_unit_xyz":point.tolist(),"left_port_id":ports[i-1],"right_port_id":ports[i],
                    "left_plate_pair":sorted(left_pair),"right_plate_pair":sorted(right_pair),
                    "expected_shared_plate_id":next(iter(shared)) if len(shared)==1 else None,
                    "left_weights":list(left),"right_weights":list(right),
                    "expected_pure_plate_weights":list(expected) if expected is not None else None,
                    **comparison})
            nodal.append(right)
        if any(c["status"] != "CORNER_COMPATIBLE" for c in corner_metrics):
            worst=max(c["E_corner"] for c in corner_metrics if c["status"]!="CORNER_COMPATIBLE")
            raise ValueError(f"corner port trace disagreement {worst:.9g} exceeds tolerance")
        if geometry_policy.get("corner_check_only", False):
            return JunctionPatch(jid,float(width_m),plates,ids,tuple(xy),tuple(ports),tuple(nodal),(),
                "CORNER_CHECKED",None,{"corner_compatibility":list(corner_metrics),
                "port_count":len(set(ports)),"port_topology_source":"PATCH_TO_EXCLUSIVE_REGION_MESH_ADJACENCY"},
                {"algorithm":PATCH_ALGORITHM,"corner_check_only":True,
                 "domain_radius_m":extent,"cells_per_width":n})
        # Subdivide each port edge until its piecewise-linear P1 trace follows
        # the existing corridor operator.  Subdivision is numerical only: new
        # node weights are evaluated from that operator, never interpolated or
        # fitted.  The ring remains a shared, conforming sequence of nodes.
        trace_tolerance=float(geometry_policy.get("trace_tolerance",1e-4))
        trace_max_depth=int(geometry_policy.get("trace_max_depth",12))
        max_nodes=int(geometry_policy.get("max_boundary_nodes",8192))
        cache={}
        def exact_weights(port, point):
            key=(port, float(point[0]), float(point[1]))
            if key not in cache:
                cache[key]=weights_at(*point)
            return cache[key]
        refined_xy=[]; refined_weights=[]; refined_ports=[]
        worst_trace=0.0; worst_trace_edge=None; refinements=0; trace_edges=[]
        for i,a in enumerate(xy):
            b=xy[(i+1)%len(xy)]
            wa=nodal[i]; wb=nodal[(i+1)%len(xy)]; port=ports[i]
            points,trace_metric=_refine_trace_edge(a,b,wa,wb,port,exact_weights,
                                                   trace_tolerance,trace_max_depth,i)
            trace_edges.append(trace_metric)
            refinements+=trace_metric["subdivision_count"]
            if trace_metric["max_residual_seen"]>worst_trace:
                worst_trace=trace_metric["max_residual_seen"]
                worst_trace_edge={"edge":i,"port":port,**trace_metric}
            for point,weight in points:
                if refined_xy and point==refined_xy[-1]:
                    continue
                refined_xy.append(point); refined_weights.append(weight); refined_ports.append(port)
            if len(refined_xy)>max_nodes:
                raise ValueError(f"adaptive trace subdivision exceeded max_boundary_nodes={max_nodes}; W={width_m}, junction={jid}, branch={port}, residual={worst_trace:.9g}")
        xy=refined_xy; nodal=refined_weights; ports=refined_ports
        triangles=_ear_clip(xy)
        ang=max(math.hypot(x,y)/sphere_radius_m for x,y in xy)
        metric_distortion=ang/max(math.sin(ang),1e-15)-1.0
        max_distortion=float(geometry_policy.get("max_tangent_metric_relative_distortion",0.01))
        if metric_distortion>max_distortion: raise ValueError("local tangent chart exceeds metric-distortion bound")
        return JunctionPatch(jid,float(width_m),plates,ids,tuple(xy),tuple(ports),tuple(nodal),triangles,
                             "BOUND",None,{"node_count":len(xy),"triangle_count":len(triangles),
                             "max_angular_extent_rad":ang,"tangent_metric_relative_distortion":metric_distortion,"grid_spacing_m":h,
                             "connected_component_cells":int(component.sum()),"port_count":len(set(ports)),
                             "membership_mask_counts_in_central_domain":topology["membership_mask_counts_in_central_domain"],
                             "membership_mask_counts_in_patch":topology["membership_mask_counts_in_patch"],
                             "exclusive_region_node_counts":topology["exclusive_region_node_counts"],
                             "port_component_counts":topology["port_component_counts"],
                             "port_topology_source":"PATCH_TO_EXCLUSIVE_REGION_MESH_ADJACENCY",
                             "corner_compatibility":list(corner_metrics),
                             "port_contour_association_max_distance_m":max(port_match_distances),
                             "contour_root_tolerance_m":root_tolerance,
                             "trace_max_error_at_refinement_samples":worst_trace,
                             "trace_worst_edge":worst_trace_edge,"trace_subdivision_count":refinements,
                             "trace_edge_metrics":trace_edges,
                             "boundary_node_count_after_refinement":len(xy)},
                             {"algorithm":PATCH_ALGORITHM,"numerical_refinement_only":True,
                              "boundary_definition":"connected component of spherical points covered by >=2/3 incident corridors",
                              "port_definition":"mesh-adjacency interface between central multi-corridor patch and exact singleton membership masks",
                              "width_m":width_m,"cells_per_width":n})
    except (ValueError, IndexError, ZeroDivisionError) as exc:
        error_metrics={"grid_spacing_m":h,"grid_nodes_per_axis":count}
        if topology is not None:
            error_metrics.update({k:v for k,v in topology.items() if k!="patch_component"})
            error_metrics["port_topology_source"]="PATCH_TO_EXCLUSIVE_REGION_MESH_ADJACENCY"
        if corner_metrics:
            error_metrics["corner_compatibility"]=list(corner_metrics)
        return fail(str(exc),error_metrics)


def validate_junction_patch(patch: JunctionPatch, corridor_weight: Callable[[str,float,float],dict[int,float]],
                            tolerance: float=1e-4, trace_max_depth: int=12,
                            sphere_radius_m: float=6_371_000.0) -> dict:
    """Validate inherited traces at midpoint/quarter points; never repairs weights."""
    if patch.status!="BOUND": return {"pass":False,"reason":patch.reason,"max_trace_error":None}
    maxerr=0.0; worst=None; negative=0; sumerr=0.0
    for i,(a,b) in enumerate(zip(patch.boundary_xy_m,patch.boundary_xy_m[1:]+patch.boundary_xy_m[:1])):
        wa=np.asarray(patch.nodal_weights[i]); wb=np.asarray(patch.nodal_weights[(i+1)%len(patch.nodal_weights)])
        for t in (0.25,0.5,0.75):
            x=a[0]*(1-t)+b[0]*t; y=a[1]*(1-t)+b[1]*t
            port=patch.ports[i]
            expected=corridor_weight(port,x,y)
            actual=(1-t)*wa+t*wb
            err=max(abs(float(actual[k])-float(expected.get(p,0.0))) for k,p in enumerate(patch.plate_ids))
            if err>maxerr: maxerr=err; worst={"edge":i,"t":t,"port":port,"error":err,"xy_m":[x,y]}
            sumerr=max(sumerr,abs(float(actual.sum())-1.0)); negative+=int(bool(np.any(actual < -1e-12) or np.any(actual>1+1e-12)))
    return {"pass":maxerr<=tolerance and not negative and sumerr<=1e-12,
            "max_trace_error":maxerr,"trace_tolerance":tolerance,"worst_sample":worst,
            "partition_unity_residual":sumerr,"weight_violations":negative,
            "adaptive_trace_subdivision":"BUILT_IN_PATCH_CONSTRUCTION",
            "trace_max_depth":trace_max_depth}
