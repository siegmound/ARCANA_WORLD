"""Prepared finite-volume cover diffusion, MANUFACTURED_METHOD_TEST_ONLY.

No global T0 input is read. No geological parameter is inferred. Arrays here
represent native numerical cells, independently of history or display cadence.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

SCHEMA = "ARCANA_HR2_P1_MANUFACTURED_FV_V1"
MATERIAL_ID = "HR2_P1_MANUFACTURED_UNIFORM_COVER_V1"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=False).encode("utf8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def source_identity():
    folder = Path(__file__).resolve().parent
    return {"schema": SCHEMA, "python": sys.version.split()[0],
            "numpy": np.__version__, "sources": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(folder.glob("*.py"))}}


@dataclass(frozen=True)
class Parameters:
    kappa_m2_year: float
    planned_end_year: float
    density_kg_m3: float | None
    cfl_fraction: float = 0.5
    scope: str = "MANUFACTURED_METHOD_TEST_ONLY"

    def validate(self):
        require(self.scope == "MANUFACTURED_METHOD_TEST_ONLY", "P1_AUTHORITY_INVALID")
        require(finite_number(self.kappa_m2_year) and self.kappa_m2_year >= 0,
                "KAPPA_INVALID")
        require(finite_number(self.planned_end_year) and self.planned_end_year > 0,
                "PLANNED_CLOCK_INVALID")
        require(self.cfl_fraction == 0.5, "P1_CFL_CONTRACT_MISMATCH")
        require(self.density_kg_m3 is None or (
            finite_number(self.density_kg_m3) and self.density_kg_m3 > 0),
            "DECLARED_DENSITY_INVALID")


class Mesh:
    """Immutable numerical face graph; every stored face is integrated once."""

    def __init__(self, areas, first, second, lengths, distances, metadata):
        require(np.asarray(first).dtype.kind in "iu" and np.asarray(second).dtype.kind in "iu",
                "FACE_INDICES_MUST_BE_EXACT_INTEGERS")
        self.areas = np.array(areas, dtype="<f8", copy=True).reshape(-1)
        self.first = np.array(first, dtype="<i8", copy=True).reshape(-1)
        self.second = np.array(second, dtype="<i8", copy=True).reshape(-1)
        self.lengths = np.array(lengths, dtype="<f8", copy=True).reshape(-1)
        self.distances = np.array(distances, dtype="<f8", copy=True).reshape(-1)
        self.metadata = json.loads(canonical(metadata))
        n = len(self.areas)
        require(n > 1 and np.isfinite(self.areas).all() and (self.areas > 0).all(),
                "AREA_INVALID")
        require(len({len(self.first), len(self.second), len(self.lengths),
                     len(self.distances)}) == 1, "FACE_SHAPE_INVALID")
        require(len(self.first) > 0, "NO_INTERNAL_FACES")
        require((self.first >= 0).all() and (self.second >= 0).all()
                and (self.first < n).all() and (self.second < n).all()
                and (self.first != self.second).all(), "FACE_ENDPOINT_INVALID")
        keys = np.minimum(self.first, self.second) * n + np.maximum(self.first, self.second)
        require(len(np.unique(keys)) == len(keys), "DUPLICATE_INTERNAL_FACE")
        require(np.isfinite(self.lengths).all() and (self.lengths > 0).all()
                and np.isfinite(self.distances).all() and (self.distances > 0).all(),
                "FACE_METRIC_INVALID")
        self.degrees = (np.bincount(self.first, minlength=n)
                        + np.bincount(self.second, minlength=n))
        for a in [self.areas, self.first, self.second, self.lengths,
                  self.distances, self.degrees]:
            a.flags.writeable = False

    def payload(self):
        return {"areas_m2": self.areas.tolist(), "first": self.first.tolist(),
                "second": self.second.tolist(), "face_length_m": self.lengths.tolist(),
                "center_distance_m": self.distances.tolist(), "metadata": self.metadata}

    @property
    def sha256(self):
        return digest(self.payload())

    def conductance(self, kappa):
        require(finite_number(kappa) and kappa >= 0, "KAPPA_INVALID")
        values = kappa * self.lengths / self.distances
        require(np.isfinite(values).all(), "CONDUCTANCE_NONFINITE")
        return values

    def step_limit(self, kappa):
        c = self.conductance(kappa)
        sums = (np.bincount(self.first, weights=c, minlength=len(self.areas))
                + np.bincount(self.second, weights=c, minlength=len(self.areas)))
        positive = sums > 0
        return (0.5 * float(np.min(self.areas[positive] / sums[positive]))
                if positive.any() else math.inf)


def spherical_mesh(width, height, radius_m):
    require(type(width) is int and type(height) is int and height >= 2
            and width == 2 * height, "SPHERE_REQUIRES_2_TO_1_GRID")
    require(finite_number(radius_m) and radius_m > 0, "RADIUS_INVALID")
    dphi, dlam = math.pi / height, 2 * math.pi / width
    bounds = np.linspace(-math.pi / 2, math.pi / 2, height + 1)
    centers = (bounds[:-1] + bounds[1:]) / 2
    areas = np.repeat(radius_m**2 * dlam * np.diff(np.sin(bounds)), width)
    ids = np.arange(width * height, dtype=np.int64).reshape(height, width)
    # East faces include exactly one seam face per row. W>=4 avoids duplicate
    # two-column faces. Point-only polar contacts are deliberately not faces.
    east_i, east_j = ids.ravel(), np.roll(ids, -1, axis=1).ravel()
    east_length = np.full(width * height, radius_m * dphi)
    east_distance = np.repeat(2 * radius_m * np.arcsin(
        np.cos(centers) * math.sin(dlam / 2)), width)
    north_i, north_j = ids[:-1].ravel(), ids[1:].ravel()
    north_length = np.repeat(radius_m * dlam * np.cos(bounds[1:-1]), width)
    north_distance = np.full(width * (height - 1), radius_m * dphi)
    mesh = Mesh(areas, np.concatenate([east_i, north_i]),
                np.concatenate([east_j, north_j]),
                np.concatenate([east_length, north_length]),
                np.concatenate([east_distance, north_distance]),
                {"kind": "SPHERICAL_LATLON_FV", "width": width, "height": height,
                 "radius_m": radius_m, "row_order": "SOUTH_TO_NORTH",
                 "longitude": "PERIODIC_FACE_ONCE", "external_polar_face_length_m": 0.0,
                 "polar_point_contacts": "NOT_FLUX_FACES",
                 "distance": "great_circle_between_cell_centers",
                 "material_id": MATERIAL_ID, "authority": "MANUFACTURED_METHOD_TEST_ONLY"})
    require(math.isclose(math.fsum(map(float, mesh.areas)), 4 * math.pi * radius_m**2,
                         rel_tol=64 * np.finfo(float).eps), "SPHERE_AREA_CLOSURE")
    return mesh


def finite_volume_step(mesh, volumes_m3, kappa_m2_year, dt_year):
    """Simultaneous old-state face fluxes, with no stock clipping/renormalization."""
    values = np.array(volumes_m3, dtype="<f8", copy=True).reshape(-1)
    require(values.shape == mesh.areas.shape and np.isfinite(values).all()
            and (values >= 0).all(), "VOLUME_STATE_INVALID")
    require(finite_number(dt_year) and dt_year > 0, "STEP_CLOCK_INVALID")
    limit = mesh.step_limit(kappa_m2_year)
    require(dt_year <= limit, "STEP_EXCEEDS_POSITIVITY_GUARD")
    h = values / mesh.areas
    transfer = mesh.conductance(kappa_m2_year) * (h[mesh.first] - h[mesh.second]) * dt_year
    n = len(values)
    delta = (np.bincount(mesh.second, weights=transfer, minlength=n)
             - np.bincount(mesh.first, weights=transfer, minlength=n))
    updated = values + delta
    require(np.isfinite(transfer).all() and np.isfinite(updated).all(), "UPDATE_NONFINITE")
    require((updated >= 0).all(), "NEGATIVE_STOCK_NO_CLIP_PERMITTED")
    total_before, total_after = math.fsum(map(float, values)), math.fsum(map(float, updated))
    # Each vertex gathers at most degree signed terms. Same represented transfer
    # is used at both ends; error is bounded by gathering and stock additions.
    count = 2 * int(mesh.degrees.max()) + 6
    eps = np.finfo(float).eps
    gamma = count * eps / (1 - count * eps)
    magnitude = (math.fsum(map(abs, values)) + math.fsum(map(abs, updated))
                 + 2 * math.fsum(map(abs, transfer)))
    bound = 8 * gamma * magnitude  # Predeclared conservative roundoff allowance.
    require(abs(total_after - total_before) <= bound, "STEP_VOLUME_NOT_CONSERVED")
    return updated, {"dt_year": dt_year, "step_limit_year": limit if math.isfinite(limit) else None,
                     "guard_ratio": dt_year / limit if math.isfinite(limit) else 0.0,
                     "volume_before_m3": total_before, "volume_after_m3": total_after,
                     "volume_residual_m3": total_after - total_before,
                     "roundoff_bound_m3": bound, "minimum_volume_m3": float(updated.min()),
                     "face_count": len(transfer), "external_polar_flux_m3": 0.0,
                     "transfer_sha256": hashlib.sha256(transfer.astype("<f8").tobytes()).hexdigest()}, transfer


class Integrator:
    """Full native state includes a resumable window schedule and all counters."""

    def __init__(self, mesh, parameters, initial_heights_m, initial_identity):
        parameters.validate()
        values = np.array(initial_heights_m, dtype="<f8", copy=True).reshape(-1)
        require(values.shape == mesh.areas.shape and np.isfinite(values).all()
                and (values >= 0).all(), "INITIAL_HEIGHT_INVALID")
        self.mesh, self.parameters = mesh, parameters
        self.volumes = values * mesh.areas
        require(np.isfinite(self.volumes).all(), "INITIAL_VOLUME_OVERFLOW")
        self.initial_identity = json.loads(canonical(initial_identity))
        self.initial_volume = math.fsum(map(float, self.volumes))
        self.year = 0.0
        self.accepted_steps = 0
        self.completed_windows = 0
        self.window = None
        self.cumulative_roundoff_bound = 0.0
        self.dt_histogram = {}

    def start_window(self, end_year, substeps=None):
        require(self.window is None, "WINDOW_ALREADY_ACTIVE")
        require(finite_number(end_year) and self.year < end_year <= self.parameters.planned_end_year,
                "WINDOW_OUTSIDE_PLANNED_CLOCK")
        duration = end_year - self.year
        limit = self.mesh.step_limit(self.parameters.kappa_m2_year)
        count = max(1, math.ceil(duration / limit)) if math.isfinite(limit) else 1
        if substeps is not None:
            require(type(substeps) is int and substeps > 0, "SUBSTEP_COUNT_INVALID")
            count = substeps
        # Division can round up a fraction of an ulp. Increase the actual count;
        # never relax the guard to fit an intended annual timestep.
        if substeps is None:
            while duration / count > limit:
                count += 1
        require(duration / count <= limit, "SUBSTEP_SCHEDULE_UNSTABLE")
        self.window = {"start_year": self.year, "end_year": float(end_year),
                       "substeps": count, "completed": 0}

    def step(self):
        require(self.window is not None, "NO_ACTIVE_WINDOW")
        win = self.window
        dt = (win["end_year"] - win["start_year"]) / win["substeps"]
        updated, diagnostic, _ = finite_volume_step(
            self.mesh, self.volumes, self.parameters.kappa_m2_year, dt)
        new_bound = self.cumulative_roundoff_bound + diagnostic["roundoff_bound_m3"]
        require(abs(math.fsum(map(float, updated)) - self.initial_volume) <= new_bound,
                "CUMULATIVE_VOLUME_NOT_CONSERVED")
        # All failure checks precede mutation of the accepted state.
        self.volumes = updated
        self.cumulative_roundoff_bound = new_bound
        win["completed"] += 1
        self.accepted_steps += 1
        key = float(dt).hex()
        self.dt_histogram[key] = self.dt_histogram.get(key, 0) + 1
        self.year = (win["end_year"] if win["completed"] == win["substeps"]
                     else win["start_year"] + win["completed"] * dt)
        if win["completed"] == win["substeps"]:
            self.window = None
            self.completed_windows += 1
        return {**diagnostic, "end_year": self.year, "accepted_step": self.accepted_steps,
                "cumulative_roundoff_bound_m3": self.cumulative_roundoff_bound}

    def finish_window(self):
        rows = []
        while self.window is not None:
            rows.append(self.step())
        return rows

    def heights(self):
        return self.volumes / self.mesh.areas

    def native_body(self):
        return {"schema": SCHEMA, "source_identity": source_identity(),
                "parameters": asdict(self.parameters), "mesh": self.mesh.payload(),
                "mesh_sha256": self.mesh.sha256, "volumes_m3": self.volumes.tolist(),
                "initial_identity": self.initial_identity, "initial_volume_m3": self.initial_volume,
                "year": self.year, "accepted_steps": self.accepted_steps,
                "completed_windows": self.completed_windows, "window": self.window,
                "cumulative_roundoff_bound_m3": self.cumulative_roundoff_bound,
                "dt_histogram": self.dt_histogram, "material_id": MATERIAL_ID,
                "arithmetic": "binary64; fixed face order; bincount simultaneous old-state flux",
                "history_resolution": "separate contract; native checkpoint stores complete current state",
                "scientific_authority": False, "production_authority": False}

    def checkpoint(self):
        # A returned checkpoint owns its containers even when the live schedule
        # or histogram changes after this call.
        body = json.loads(canonical(self.native_body()))
        return {"body": body, "sha256": digest(body)}


def restore_native(checkpoint, expected_parameters=None, expected_mesh_sha256=None):
    require(set(checkpoint) == {"body", "sha256"} and digest(checkpoint["body"]) == checkpoint["sha256"],
            "NATIVE_CHECKPOINT_CORRUPT")
    body = checkpoint["body"]
    require(body["schema"] == SCHEMA and body["source_identity"] == source_identity(),
            "NATIVE_SOURCE_OR_SCHEMA_MISMATCH")
    params = Parameters(**body["parameters"])
    params.validate()
    if expected_parameters is not None:
        require(asdict(params) == asdict(expected_parameters), "NATIVE_CONFIG_MISMATCH")
    data = body["mesh"]
    mesh = Mesh(data["areas_m2"], data["first"], data["second"], data["face_length_m"],
                data["center_distance_m"], data["metadata"])
    require(mesh.sha256 == body["mesh_sha256"] and
            (expected_mesh_sha256 is None or mesh.sha256 == expected_mesh_sha256), "NATIVE_MESH_MISMATCH")
    require(body["material_id"] == MATERIAL_ID and body["scientific_authority"] is False
            and body["production_authority"] is False, "NATIVE_AUTHORITY_MISMATCH")
    obj = Integrator.__new__(Integrator)
    obj.mesh, obj.parameters = mesh, params
    obj.volumes = np.array(body["volumes_m3"], dtype="<f8", copy=True)
    require(obj.volumes.shape == mesh.areas.shape and np.isfinite(obj.volumes).all()
            and (obj.volumes >= 0).all(), "NATIVE_VOLUME_INVALID")
    obj.initial_identity = json.loads(canonical(body["initial_identity"]))
    for attr, key in [("initial_volume", "initial_volume_m3"), ("year", "year"),
                      ("accepted_steps", "accepted_steps"), ("completed_windows", "completed_windows"),
                      ("cumulative_roundoff_bound", "cumulative_roundoff_bound_m3")]:
        setattr(obj, attr, body[key])
    require(math.isfinite(obj.year) and 0 <= obj.year <= params.planned_end_year,
            "NATIVE_CLOCK_INVALID")
    require(math.isfinite(obj.initial_volume) and obj.initial_volume >= 0
            and math.isfinite(obj.cumulative_roundoff_bound) and obj.cumulative_roundoff_bound >= 0,
            "NATIVE_BALANCE_COUNTER_INVALID")
    require(type(obj.accepted_steps) is int and obj.accepted_steps >= 0
            and type(obj.completed_windows) is int and obj.completed_windows >= 0,
            "NATIVE_STEP_COUNTER_INVALID")
    obj.dt_histogram = dict(body["dt_histogram"])
    require(all(type(v) is int and v > 0 and math.isfinite(float.fromhex(k)) and float.fromhex(k) > 0
                for k, v in obj.dt_histogram.items())
            and sum(obj.dt_histogram.values()) == obj.accepted_steps, "NATIVE_DT_HISTOGRAM_INVALID")
    elapsed = math.fsum(float.fromhex(k) * n for k, n in obj.dt_histogram.items())
    clock_allowance = 16 * np.finfo(float).eps * max(abs(obj.year), abs(elapsed))
    require(math.isfinite(elapsed) and abs(elapsed - obj.year) <= clock_allowance,
            "NATIVE_DT_CLOCK_LEDGER_INVALID")
    obj.window = json.loads(canonical(body["window"]))
    if obj.window is not None:
        win = obj.window
        require(set(win) == {"start_year", "end_year", "substeps", "completed"}
                and type(win["substeps"]) is int and type(win["completed"]) is int
                and 0 <= win["completed"] < win["substeps"]
                and 0 <= win["start_year"] < win["end_year"] <= params.planned_end_year,
                "NATIVE_WINDOW_INVALID")
        dt = (win["end_year"] - win["start_year"]) / win["substeps"]
        require(obj.year == win["start_year"] + win["completed"] * dt
                and dt <= mesh.step_limit(params.kappa_m2_year), "NATIVE_WINDOW_CLOCK_OR_CFL_INVALID")
    require(abs(math.fsum(map(float, obj.volumes)) - obj.initial_volume)
            <= obj.cumulative_roundoff_bound, "NATIVE_VOLUME_LEDGER_INVALID")
    require(obj.checkpoint() == checkpoint, "NATIVE_STATE_NOT_EXACTLY_REPRESENTABLE")
    return obj
