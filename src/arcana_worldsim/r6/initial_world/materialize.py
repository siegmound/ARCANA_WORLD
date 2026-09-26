"""Validate, serialize and register the single 210 Ma R6 initial state."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile
import zipfile
from typing import Any

import numpy as np

from ..identity import (BranchId, HistoryId, R6RunId, canonical_bytes,
                        content_hash)
from ..provenance import ProvenanceRecord
from ..state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                     SupportClass, TimeSupport)
from ..store import HistoryStore
from ..temporal import RefinementAnchor
from ..repository_context import (canonical_text_sha256, external_root, require_repository_context,
                                  verify_protected_staged_blobs)
from .generator import generate_initial_world
from .grid import GlobalGrid1Degree
from .model import InitialWorldFields
from .seeds import GENERATOR_VERSION, SEED_ROOT_MATERIAL, lineage_manifest
from .validation import validate_initial_world


EXPECTED_HEAD = "592b1651b405363373590092e133bd25569d99a5"
SPEC_FILES = (
    "R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json",
    "R6_INITIAL_SUPERCONTINENT_GENERATOR_CONTRACT.json",
    "R6_INITIAL_WORLD_VALIDATION_CONTRACT.json",
)
DOC_FILES = (
    "R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.md",
    "R6_INITIAL_SUPERCONTINENT_GENERATOR_CONTRACT.md",
    "R6_INITIAL_WORLD_VALIDATION_CONTRACT.md",
    "R6_INITIAL_WORLD_IMPLEMENTATION_PLAN.md",
    "R6_INITIAL_WORLD_RECANONICALIZATION_BASIS.json",
    "R6_INITIAL_WORLD_RECANONICALIZATION_BASIS.md",
    "docs/strategy/R6_WORLD_HISTORY_ARCHITECTURE_FREEZE.md",
    "docs/strategy/R6_EXISTING_CAPABILITY_RECONCILIATION_AND_CORE_INTERFACE_SPEC.md",
    "R6_WAVE3B_PREIMPORT_RECOVERY_ADJUDICATION.json",
    "R6_SIMULATION1_BOOTSTRAP_AUTHORITY_RECOVERY.json",
    "R6_SIMULATION1_PHYSICAL_GEOGRAPHY_T0_BINDING.json",
    "R6_SIMULATION1_INITIAL_COMPONENT_MATRIX_WAVE3A.json",
)
PROTECTED_INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}


def _sha256(data: bytes) -> str:
    return sha256(data).hexdigest()


def _hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _hash_dependency(path: Path) -> str:
    """Hash source/spec dependencies portably while retaining binary hashes."""
    if path.suffix.lower() in {".json", ".md", ".py", ".toml", ".yml", ".yaml"}:
        return canonical_text_sha256(path)
    return _hash_file(path)


def _deterministic_npz(arrays: dict[str, np.ndarray]) -> bytes:
    """Create a stable, uncompressed ZIP/NPY bundle with fixed metadata."""
    out = BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as zf:
        for key in sorted(arrays):
            array = np.ascontiguousarray(arrays[key])
            buffer = BytesIO()
            np.lib.format.write_array(buffer, array, version=(2, 0), allow_pickle=False)
            info = zipfile.ZipInfo(f"{key}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o600 << 16
            zf.writestr(info, buffer.getvalue())
    return out.getvalue()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == data:
            return
        raise FileExistsError(f"refusing to overwrite differing immutable artifact: {path}")
    fd, tmp_name = tempfile.mkstemp(prefix=".r6-atomic-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _read_contracts(repo: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    documents = []
    for name in SPEC_FILES:
        documents.append(json.loads((repo / name).read_text(encoding="utf-8")))
    spec, generator, validation = documents
    if spec["provenance_decisions"]["r6_global_t0_ma"] != 210:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: t0 must be 210 Ma")
    if spec["spatial_contract"]["grid_id"] != generator["generation_method"]["spatial_support"]:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: grid IDs differ")
    if spec["spatial_contract"]["shape_lat_lon"] != validation["grid_invariants"]["shape_lat_lon"]:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: grid shape differs")
    if generator["specification_ref"] != SPEC_FILES[0]:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: generator references a different physical spec")
    if validation["specification_ref"] != SPEC_FILES[0] or validation["generator_contract_ref"] != SPEC_FILES[1]:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: validation references do not match")
    if generator["seed_and_determinism"]["root_material"] != "UTF8('ARCANA:R6:INITIAL_WORLD:v1')":
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: seed root differs")
    if spec["seed_lineage"]["strategy_id"] != "ARCANA_R6_INITIAL_WORLD_SEED_LINEAGE_V1":
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: seed strategy differs")
    if spec["terrain_and_crust"]["ocean_bathymetry"]["numeric_depths_materialized_by_initial_generator"]:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: numeric bathymetry is not authorized")
    if not generator["execution_boundary"]["authorized_by_this_contract"] is False:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: design contract unexpectedly authorizes execution")
    if validation["grid_invariants"]["cell_count"] != 64800:
        raise ValueError("R6_INITIAL_WORLD_CONTRACT_CONFLICT: expected 64,800 cells")
    return spec, generator, validation


def _git_value(repo: Path, *args: str) -> str:
    import subprocess
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def _preflight(repo: Path) -> None:
    require_repository_context(
        repo, required_ancestor=EXPECTED_HEAD,
    )
    verify_protected_staged_blobs(repo, PROTECTED_INDEX_BLOBS)


def _runtime_identity() -> dict[str, str]:
    return {
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "bit_generator": "NumPy PCG64",
        "array_order": "C",
        "serialization": "NPY v2 inside ZIP_STORED with fixed 1980 timestamp",
    }


def _reference_diagnostics(repo: Path, r6_validation: dict[str, Any]) -> dict[str, Any]:
    """Read-only scalar/context comparison; no reference raster enters generation."""
    a1_path = repo / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
    a1_expected = "9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f"
    a1_sha = _hash_file(a1_path)
    if a1_sha != a1_expected:
        raise RuntimeError("A1 reference hash differs from the governed reference-only source")
    with np.load(a1_path, allow_pickle=False) as archive:
        ages = archive["age_ma"]
        lat = archive["lat"].astype(np.float64)
        lon = archive["lon"].astype(np.float64)
        land = archive["land_mask"][0].astype(bool)
    if ages[0] != 210.0 or land.shape != (90, 180) or lat.size != 90 or lon.size != 180:
        raise RuntimeError("A1 reference-only comparison inputs violate their inventoried shape/time")
    lat_bounds = np.r_[lat[0] - 1.0, (lat[:-1] + lat[1:]) / 2.0, lat[-1] + 1.0]
    row_area = np.sin(np.deg2rad(lat_bounds[1:])) - np.sin(np.deg2rad(lat_bounds[:-1]))
    weights = np.broadcast_to(row_area[:, None], land.shape)
    a1_land_fraction = float(weights[land].sum() / weights.sum())
    occupied_rows, occupied_cols = np.nonzero(land)
    a1_lat_span = float(lat[occupied_rows].max() - lat[occupied_rows].min() + 2.0)
    sorted_lon = np.sort(np.unique(np.mod(lon[occupied_cols], 360.0)))
    gaps = np.diff(np.r_[sorted_lon, sorted_lon[0] + 360.0])
    a1_lon_span = float(360.0 - gaps.max() + 2.0)

    adjudication = json.loads((repo / "R6_WAVE3B_PREIMPORT_RECOVERY_ADJUDICATION.json").read_text(encoding="utf-8"))
    hybrid = adjudication["evidence"]["related_preimport_worldsim_prototype"]["210ma_execution_output"]
    hybrid_path = Path(hybrid["path"])
    hybrid_sha = _hash_file(hybrid_path)
    if hybrid_sha != hybrid["sha256"]:
        raise RuntimeError("HYBRID-1 reference output hash differs from recovery adjudication")
    geojson = json.loads(hybrid_path.read_text(encoding="utf-8"))
    features = geojson.get("features", [])
    major = [f for f in features if f.get("properties", {}).get("kind") == "major_continent"]
    positions: list[tuple[float, float]] = []
    for feature in major:
        stack = [feature.get("geometry", {}).get("coordinates", [])]
        while stack:
            item = stack.pop()
            if isinstance(item, list) and item and isinstance(item[0], (int, float)):
                positions.append((float(item[0]), float(item[1])))
            elif isinstance(item, list):
                stack.extend(item)
    if not major or not positions:
        raise RuntimeError("HYBRID-1 reference lacks major-continent polygon coordinates")
    return {
        "status": "DIAGNOSTIC_ONLY_NOT_USED_AS_INITIALIZER_OR_FIT_TARGET",
        "spatial_resampling_or_raster_fitting": False,
        "r6_metrics": {
            "land_fraction": r6_validation["land_fraction_area_weighted"],
            "dominant_component_share_of_land": r6_validation["dominant_component_share_of_land"],
            "latitudinal_span_deg": r6_validation["dominant_component_latitudinal_span_deg"],
            "longitudinal_span_deg": r6_validation["dominant_component_longitudinal_span_deg"],
            "coastline_edge_transition_count": r6_validation["coastline_edge_transition_count"],
        },
        "a1_210ma_reference": {
            "logical_path": "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz",
            "sha256": a1_sha, "grid": "90x180 / 2-degree cell centers",
            "land_fraction_area_weighted": a1_land_fraction,
            "land_latitudinal_span_deg": a1_lat_span,
            "land_longitudinal_span_deg": a1_lon_span,
            "used_by_generator": False, "runtime_dependency": False,
        },
        "hybrid1_210ma_prototype": {
            "source_id": "ARCANA_WorldSim_v0_1_Tectonics/outputs/hybrid1/210Ma/plates.geojson",
            "sha256": hybrid_sha, "feature_count": len(features),
            "major_continent_feature_count": len(major),
            "major_continent_names": [str(f.get("properties", {}).get("name", "UNKNOWN")) for f in major],
            "major_continent_longitude_bounds_deg": [min(p[0] for p in positions), max(p[0] for p in positions)],
            "major_continent_latitude_bounds_deg": [min(p[1] for p in positions), max(p[1] for p in positions)],
            "used_by_generator": False, "identity_as_original_simulation1": "UNPROVEN",
        },
        "comparison_policy": "Independent gross metrics only; no equality target, regridding, or adjustment.",
    }


def _field_inventory(payload_sha: str) -> list[dict[str, Any]]:
    fields = [
        ("land_ocean_mask", "PHYSICAL_GEOGRAPHY", "uint8", "1=LAND,0=OCEAN", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("coastline_mask", "PHYSICAL_GEOGRAPHY", "uint8", "boolean coastline cell", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("plate_id", "PROVINCE_STATE", "int16", "stable plate identity; not motion", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("crust_class", "PROVINCE_STATE", "int8", "0=OCEANIC,1=CONTINENTAL,2=TRANSITIONAL", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("boundary_class", "PROVINCE_STATE", "int8", "0=UNKNOWN,1=INTERIOR", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("province_class", "PROVINCE_STATE", "int8", "-2=NOT_APPLICABLE,0=OTHER_DESIGN,1=CRATON,2=SUTURE,3=OROGENIC_DESIGN", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("land_surface_elevation_m", "TOPOGRAPHY", "float32", "m relative to authorial R6 z=0 datum; ocean NaN masked unsupported", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("elevation_support_mask", "TOPOGRAPHY", "bool", "true only for land elevation support", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("synthetic_uncertainty_mask", "TOPOGRAPHY", "bool", "true for authorial synthetic land elevations", "DERIVED_SUPPORTED", "DERIVED_AUTHORITY"),
        ("bathymetry_unknown_mask", "BATHYMETRY", "bool", "true over ocean; no depth values", "UNKNOWN", "NONE"),
        ("plate_motion_unknown_mask", "TECTONIC_KINEMATICS", "bool", "all cells UNKNOWN", "UNKNOWN", "NONE"),
        ("deep_unknown_mask", "DEEP", "bool", "all cells UNKNOWN", "UNKNOWN", "NONE"),
        ("climate_unknown_mask", "CLIMATE", "bool", "all cells UNKNOWN", "UNKNOWN", "NONE"),
        ("hydrology_unknown_mask", "HYDROLOGY", "bool", "all cells UNKNOWN", "UNKNOWN", "NONE"),
    ]
    return [{"field": name, "domain": domain, "dtype": dtype, "semantics": semantics,
             "support_class": support, "authority_class": authority,
             "payload_ref": f"payload://sha256/{payload_sha}#{name}"}
            for name, domain, dtype, semantics, support, authority in fields]


def _validate_canonical_package(package: dict[str, Any]) -> None:
    if package.get("schema") != "ARCANA_R6_CANONICAL_INITIAL_STATE_PACKAGE_V1":
        raise ValueError("canonical package schema mismatch")
    if package.get("r6_global_t0_ma") != 210.0:
        raise ValueError("canonical package t0 mismatch")
    for key in ("r5_runtime_dependency", "a1_runtime_dependency",
                "simulation1_trajectory_dependency", "scientific_forward_simulation_executed",
                "provider_acquisition_executed", "p7q_reopened", "physical_soil_created",
                "scientific_authority_register_mutated", "execution_indexes_mutated",
                "current_state_updated"):
        if package.get(key) is not False:
            raise ValueError(f"canonical package governance flag must remain false: {key}")
    payload = package.get("materialized_payload", {})
    if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("sha256", ""))) or int(payload.get("bytes", 0)) <= 0:
        raise ValueError("canonical package payload identity is invalid")
    required_unknown = {"bathymetry", "tectonic_kinematics", "deep", "climate", "hydrology"}
    if not required_unknown.issubset(set(package.get("unknown_domains", ()))):
        raise ValueError("canonical package omits required UNKNOWN domains")
    for state in package.get("states", ()):
        if state.get("support_class") == "UNKNOWN" and state.get("payload_ref") is not None:
            raise ValueError(f"UNKNOWN domain must not bind a numeric payload: {state.get('domain')}")
    domains = {state.get("domain") for state in package.get("states", ())}
    if not {"physical_geography", "land_ocean", "province_state", "topography"}.issubset(domains):
        raise ValueError("canonical package lacks a supported physical t0 state")


def _make_states(fields: InitialWorldFields, payload_sha: str,
                 identity: dict[str, Any]) -> tuple[list[DomainStateEnvelope], RefinementAnchor, ProvenanceRecord,
                                                    str, str, str]:
    run_id = str(R6RunId.from_payload(identity))
    history_id = str(HistoryId.from_payload({"run_identity_sha256": content_hash(identity)}))
    branch_id = str(BranchId.from_payload({"run_identity_sha256": content_hash(identity),
                                           "branch_role": "GLOBAL_BASE"}))
    provenance = ProvenanceRecord.create(
        activity="R6_INITIAL_WORLD_AUTHORIAL_T0_GENERATION",
        source_refs=tuple(f"sha256:{digest}" for digest in sorted(identity["dependencies"].values())),
        attributes={"generator_id": GENERATOR_VERSION,
                    "time_ma": 210.0,
                    "authority_semantics": "AUTHORIAL_SYNTHETIC_INITIALIZATION",
                    "a1_used_as_input": False,
                    "simulation1_trajectory_reused": False,
                    "forward_evolution": False},
    )
    time = TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER")
    spatial = SpatialSupport(fields.grid.grid_id, (), "1 degree; 180x360", "GRID")
    p_ref = str(provenance.record_id)

    def supported(domain: str, field_refs: dict[str, str], extra: dict[str, Any] | None = None):
        value = {"schema": "R6_INITIAL_DOMAIN_FIELD_REFERENCE_V1",
                 "grid_id": fields.grid.grid_id, "time_ma": 210.0,
                 "payload_sha256": payload_sha, "field_refs": field_refs}
        if extra:
            value.update(extra)
        return DomainStateEnvelope.create(
            history_id=history_id, branch_id=branch_id, domain=domain,
            time_support=time, spatial_support=spatial,
            support_class=SupportClass.DERIVED_SUPPORTED,
            authority_class=AuthorityClass.DERIVED_AUTHORITY,
            value=value,
            uncertainty={"classification": "AUTHORIAL_SYNTHETIC_INITIALIZATION",
                         "no_empirical_210Ma_reconstruction_claim": True},
            provenance_ids=(p_ref,), payload_ref=f"sha256:{payload_sha}")

    states = [
        supported("physical_geography", {
            "land_ocean": f"payload://sha256/{payload_sha}#land_ocean_mask",
            "coastline": f"payload://sha256/{payload_sha}#coastline_mask",
            "plate_id": f"payload://sha256/{payload_sha}#plate_id",
            "crust_class": f"payload://sha256/{payload_sha}#crust_class",
            "province_class": f"payload://sha256/{payload_sha}#province_class",
            "land_surface_elevation": f"payload://sha256/{payload_sha}#land_surface_elevation_m",
        }, {"planet_specification_id": "R6_EARTH_SCALE_ANALOGUE_V1",
            "generator_id": GENERATOR_VERSION}),
        supported("land_ocean", {"land_ocean_mask": f"payload://sha256/{payload_sha}#land_ocean_mask",
                                  "coastline_mask": f"payload://sha256/{payload_sha}#coastline_mask"}),
        supported("province_state", {"plate_id": f"payload://sha256/{payload_sha}#plate_id",
                                      "crust_class": f"payload://sha256/{payload_sha}#crust_class",
                                      "boundary_class": f"payload://sha256/{payload_sha}#boundary_class",
                                      "province_class": f"payload://sha256/{payload_sha}#province_class"}),
        supported("topography", {"land_surface_elevation_m": f"payload://sha256/{payload_sha}#land_surface_elevation_m",
                                  "elevation_support_mask": f"payload://sha256/{payload_sha}#elevation_support_mask",
                                  "synthetic_uncertainty_mask": f"payload://sha256/{payload_sha}#synthetic_uncertainty_mask"}),
    ]
    unknowns = {
        "bathymetry": "Numeric ocean depth is not authorized by the physical specification.",
        "tectonic_kinematics": "Plate identity is materialized; plate motion is not authorized or inferred.",
        "deep": "No governed R6 Deep initializer/law package is bound.",
        "climate": "No t0 age-specific forcing or climate authority is bound.",
        "hydrology": "No hydrology is run; compatible climate/water inputs and R6 adapter are prerequisites.",
    }
    for domain, reason in unknowns.items():
        states.append(DomainStateEnvelope.create(
            history_id=history_id, branch_id=branch_id, domain=domain,
            time_support=time, spatial_support=spatial,
            support_class=SupportClass.UNKNOWN, authority_class=AuthorityClass.NONE,
            value=None, uncertainty={"status": "UNKNOWN", "reason": reason},
            provenance_ids=(p_ref,)))
    physical_domain_ids = tuple(s.domain for s in states if s.domain in {
        "physical_geography", "land_ocean", "province_state", "topography"})
    anchor = RefinementAnchor.create(
        history_id=history_id, branch_id=branch_id, time_key="210Ma",
        domain_ids=physical_domain_ids,
        state_ids=tuple(str(s.state_id) for s in states if s.domain in physical_domain_ids),
        provenance_refs=(p_ref,), validation_status="PASS_WITH_UNKNOWN",
        details={"role": "INITIAL_PHYSICAL_REFINEMENT_ANCHOR",
                 "included_domains": list(physical_domain_ids),
                 "excluded_unknown_domains": list(unknowns),
                 "authority": "AUTHORIAL_SYNTHETIC_INITIALIZATION"})
    return states, anchor, provenance, history_id, branch_id, run_id


def materialize_initial_world(repo_root: str | Path, output_root: str | Path,
                              *, perform_sensitivity: bool = True) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    output = Path(output_root).resolve()
    _preflight(repo)
    spec, generator_contract, validation_contract = _read_contracts(repo)
    for name in DOC_FILES:
        if not (repo / name).is_file():
            raise FileNotFoundError(f"required design authority missing: {name}")
    dependencies = {name: _hash_dependency(repo / name) for name in (*SPEC_FILES, *DOC_FILES)}
    code_names = (
        "src/arcana_worldsim/r6/initial_world/grid.py",
        "src/arcana_worldsim/r6/initial_world/seeds.py",
        "src/arcana_worldsim/r6/initial_world/model.py",
        "src/arcana_worldsim/r6/initial_world/generator.py",
        "src/arcana_worldsim/r6/initial_world/topography.py",
        "src/arcana_worldsim/r6/initial_world/validation.py",
        "src/arcana_worldsim/r6/initial_world/materialize.py",
    )
    dependencies.update({name: _hash_dependency(repo / name) for name in code_names})
    if dependencies[SPEC_FILES[0]] != dependencies["R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json"]:
        raise AssertionError("physical specification hash mismatch")

    first = generate_initial_world()
    first_validation = validate_initial_world(first)
    if first_validation["result"] == "FAIL":
        raise RuntimeError(f"canonical seed fails frozen contract: {first_validation['failures']}")
    second = generate_initial_world()
    second_validation = validate_initial_world(second)
    first_arrays, second_arrays = first.arrays(), second.arrays()
    if first_validation != second_validation or first.metadata != second.metadata:
        raise RuntimeError("deterministic replay validation/metadata mismatch")
    for key in first_arrays:
        if not np.array_equal(first_arrays[key], second_arrays[key], equal_nan=True):
            raise RuntimeError(f"deterministic replay array mismatch: {key}")
    payload_bytes = _deterministic_npz(first_arrays)
    replay_payload_bytes = _deterministic_npz(second_arrays)
    if _sha256(payload_bytes) != _sha256(replay_payload_bytes):
        raise RuntimeError("deterministic replay payload hash mismatch")
    payload_sha = _sha256(payload_bytes)

    sensitivity = None
    if perform_sensitivity:
        alternate = generate_initial_world(seed_root_material=b"ARCANA:R6:INITIAL_WORLD:SENSITIVITY:1")
        alternate_validation = validate_initial_world(alternate)
        if alternate_validation["result"] == "FAIL":
            raise RuntimeError(f"bounded alternate seed fails structural invariants: {alternate_validation['failures']}")
        if alternate.metadata["seed_root_sha256"] == first.metadata["seed_root_sha256"]:
            raise RuntimeError("alternate seed is not independent")
        sensitivity = {
            "classification": "NON_CANONICAL_SENSITIVITY_ONLY_NOT_PROMOTED",
            "alternate_seed_root_sha256": alternate.metadata["seed_root_sha256"],
            "validation_result": alternate_validation["result"],
            "land_fraction_area_weighted": alternate_validation["land_fraction_area_weighted"],
            "dominant_component_share_of_land": alternate_validation["dominant_component_share_of_land"],
            "array_hashes": {key: _sha256(np.ascontiguousarray(value).tobytes())
                             for key, value in alternate.arrays().items()},
        }

    runtime = _runtime_identity()
    identity = {
        "schema": "ARCANA_R6_INITIAL_WORLD_RUN_IDENTITY_V1",
        "t0_ma": 210.0,
        "generator_id": GENERATOR_VERSION,
        "grid": GlobalGrid1Degree().metadata(),
        "dependencies": dependencies,
        "payload_sha256": payload_sha,
        "runtime_identity": runtime,
        "seed_lineage": lineage_manifest(),
        "configuration": {
            "main_land_fraction_target": 0.27,
            "secondary_terrane_count": 4,
            "each_terrane_fraction_target": 0.0075,
            "plate_count_range": [12, 18],
            "craton_count_range": [4, 8],
            "elevation_range_m": [0, 8000],
        },
    }
    states, anchor, provenance, history_id, branch_id, run_id = _make_states(first, payload_sha, identity)
    package_dir_name = run_id
    output.mkdir(parents=True, exist_ok=True)
    target_dir = output / package_dir_name
    if target_dir.exists():
        existing = target_dir / "R6_INITIAL_PHYSICAL_GEOGRAPHY.npz"
        if not existing.is_file() or _hash_file(existing) != payload_sha:
            raise FileExistsError("existing immutable R6 run directory differs; refusing overwrite")
        payload_path = existing
        store_root = target_dir / "world_history"
        store = HistoryStore(store_root)
    else:
        temp_dir = Path(tempfile.mkdtemp(prefix=f".{run_id}.tmp-", dir=output))
        try:
            payload_path = temp_dir / "R6_INITIAL_PHYSICAL_GEOGRAPHY.npz"
            payload_path.write_bytes(payload_bytes)
            if _hash_file(payload_path) != payload_sha:
                raise RuntimeError("payload hash changed after write")
            store_root = temp_dir / "world_history"
            store = HistoryStore(store_root)
            store.append_provenance(provenance)
            for state in states:
                store.append_state(state)
            store.append_temporal(anchor)
            reread_states = store.states()
            if {str(s.state_id) for s in reread_states} != {str(s.state_id) for s in states}:
                raise RuntimeError("R6 history-store state round trip failed")
            reread_anchor = store.read_temporal(anchor.record_id)
            if reread_anchor.get("role") != "REFINEMENT_ANCHOR" or set(reread_anchor["state_ids"]) != set(anchor.state_ids):
                raise RuntimeError("R6 210 Ma refinement anchor round trip failed")
            os.replace(temp_dir, target_dir)
            payload_path = target_dir / "R6_INITIAL_PHYSICAL_GEOGRAPHY.npz"
            store_root = target_dir / "world_history"
        except Exception:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

    # Reopen from the immutable promoted location and re-verify the registered records.
    store = HistoryStore(store_root)
    if _hash_file(payload_path) != payload_sha:
        raise RuntimeError("promoted payload failed SHA-256 validation")
    if {str(s.state_id) for s in store.states()} != {str(s.state_id) for s in states}:
        raise RuntimeError("promoted history state registry mismatch")
    with np.load(payload_path, allow_pickle=False) as archive:
        if sorted(archive.files) != sorted(first_arrays):
            raise RuntimeError("materialized payload field inventory mismatch")
        for key, expected in first_arrays.items():
            if not np.array_equal(archive[key], expected, equal_nan=True):
                raise RuntimeError(f"materialized payload round trip differs: {key}")

    reference_comparison = _reference_diagnostics(repo, first_validation)
    validation = dict(first_validation)
    validation.update({
        "canonical_payload_sha256": payload_sha,
        "canonical_payload_bytes": len(payload_bytes),
        "deterministic_replay": "PASS_IDENTICAL_ARRAYS_METADATA_VALIDATION_AND_PAYLOAD_HASH",
        "sensitivity_test": sensitivity,
        "reference_comparison": reference_comparison,
        "world_history_registration": "PASS",
        "refinement_anchor": {"status": "PASS", "record_id": anchor.record_id,
                              "state_ids": list(anchor.state_ids),
                              "domain_ids": list(anchor.domain_ids)},
        "canonical_package_created": True,
        "forward_evolution_executed": False,
    })
    validation_bytes = canonical_bytes(validation) + b"\n"
    validation_sha = _sha256(validation_bytes)
    external_relpath = os.path.relpath(target_dir, repo).replace("\\", "/")

    package = {
        "schema": "ARCANA_R6_CANONICAL_INITIAL_STATE_PACKAGE_V1",
        "canonical_status": "CANONICAL_R6_INITIAL_PHYSICAL_STATE__UNKNOWN_DOMAINS_PRESERVED",
        "repository_baseline_head": EXPECTED_HEAD,
        "r6_global_t0_ma": 210.0,
        "historical_simulation1_t0_proven": False,
        "planet_specification_id": "R6_EARTH_SCALE_ANALOGUE_V1",
        "grid": GlobalGrid1Degree().metadata(),
        "generator": {"id": GENERATOR_VERSION, "identity_sha256": content_hash(identity)},
        "run_id": run_id,
        "history_id": history_id,
        "global_base_branch_id": branch_id,
        "seed_lineage": lineage_manifest(),
        "materialized_payload": {
            "relative_path": f"{external_relpath}/R6_INITIAL_PHYSICAL_GEOGRAPHY.npz",
            "bytes": len(payload_bytes), "sha256": payload_sha,
            "format": "deterministic NPZ/NPY v2 ZIP_STORED",
        },
        "world_history_store": f"{external_relpath}/world_history",
        "states": [{"domain": s.domain, "state_id": str(s.state_id),
                    "support_class": s.support_class.value,
                    "authority_class": s.authority_class.value,
                    "payload_ref": s.payload_ref}
                   for s in states],
        "unknown_domains": ["bathymetry", "tectonic_kinematics", "deep", "climate", "hydrology"],
        "refinement_anchor": {"record_id": anchor.record_id, "time_ma": 210.0,
                              "domains": list(anchor.domain_ids), "state_ids": list(anchor.state_ids)},
        "validation": {"relative_path": "R6_INITIAL_WORLD_VALIDATION.json",
                       "sha256": validation_sha, "result": validation["result"]},
        "first_post_t0_consumer_adjudication": {
            "selected_domain": "PHYSICAL_WORLD_EVOLUTION",
            "status": "BLOCKED_NOT_EXECUTED",
            "inputs_available": ["land_ocean", "plate_identity", "designed_province", "supported_land_elevation"],
            "missing": ["governed_plate_motion_or_geodynamic_law", "dated_physical_forcings_and_event_schedule",
                        "R6_Deep_initializer_and_laws_if_required_by_coupling", "bound_runtime_and_coupling_solver"],
            "existing_reusable_implementation": "No canonical R6 physical-world evolution engine is registered; A1/R1-R3 frames are references, and v0.1 HYBRID-1 is a prototype rather than process authority.",
            "provider_required": "Not yet decided; run suitability gate after a specific variable/consumer need and ARCANA evidence review.",
            "scientific_law_bound": False,
        },
        "reference_comparison": reference_comparison,
        "provenance_root_id": str(provenance.record_id),
        "authority_semantics": "AUTHORIAL_SYNTHETIC_INITIALIZATION; DERIVED_SUPPORTED under this newly governed R6 design",
        "r5_runtime_dependency": False,
        "a1_runtime_dependency": False,
        "simulation1_trajectory_dependency": False,
        "scientific_forward_simulation_executed": False,
        "provider_acquisition_executed": False,
        "p7q_reopened": False,
        "physical_soil_created": False,
        "scientific_authority_register_mutated": False,
        "execution_indexes_mutated": False,
        "current_state_updated": False,
    }
    _validate_canonical_package(package)
    package_bytes = canonical_bytes(package) + b"\n"
    package_sha = _sha256(package_bytes)
    manifest = {
        "schema": "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST_V1",
        "status": "MATERIALIZED_AND_VALIDATED",
        "canonical_initial_state_package_sha256": package_sha,
        "run_identity": identity,
        "run_id": run_id,
        "history_id": history_id,
        "branch_id": branch_id,
        "time_ma": 210.0,
        "grid": GlobalGrid1Degree().metadata(),
        "planetary_constants": spec["planetary_baseline"],
        "seed_lineage": lineage_manifest(),
        "payload": {"relative_path": f"{external_relpath}/R6_INITIAL_PHYSICAL_GEOGRAPHY.npz",
                    "bytes": len(payload_bytes), "sha256": payload_sha,
                    "fields": _field_inventory(payload_sha)},
        "field_authorities": {"land_ocean_province_topography": "DERIVED_SUPPORTED__AUTHORIAL_SYNTHETIC_INITIALIZATION",
                              "plate_motion_bathymetry_deep_climate_hydrology": "UNKNOWN"},
        "history_store": {"relative_path": f"{external_relpath}/world_history",
                          "state_count": len(states), "refinement_anchor_id": anchor.record_id},
        "validation": {"result": validation["result"], "sha256": validation_sha,
                       "report": validation},
        "reference_comparison": {**reference_comparison,
                                 "a1_numeric_initialization": False,
                                 "hybrid1_numeric_initialization": False},
        "first_post_t0_consumer_adjudication": package["first_post_t0_consumer_adjudication"],
        "governance": {},
    }
    manifest["governance"] = {key: package[key] for key in (
        "r5_runtime_dependency", "a1_runtime_dependency", "simulation1_trajectory_dependency",
        "scientific_forward_simulation_executed", "provider_acquisition_executed", "p7q_reopened",
        "physical_soil_created", "scientific_authority_register_mutated",
        "execution_indexes_mutated", "current_state_updated")}

    # Read-only source references are recorded by hash; no inputs are copied into the output.
    output_names = {
        "R6_INITIAL_WORLD_VALIDATION.json": validation_bytes,
        "R6_CANONICAL_INITIAL_STATE_PACKAGE.json": package_bytes,
        "R6_CANONICAL_INITIAL_STATE_PACKAGE.md": _package_markdown(package, package_sha).encode("utf-8"),
        "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json": canonical_bytes(manifest) + b"\n",
    }
    for name, data in output_names.items():
        _atomic_write(repo / name, data)
    return {
        "run_id": run_id, "history_id": history_id, "branch_id": branch_id,
        "payload_path": payload_path.resolve().relative_to(external_root(repo).resolve()).as_posix(),
        "payload_root_environment_variable": "ARCANA_EXTERNAL_ROOT",
        "payload_sha256": payload_sha,
        "payload_bytes": len(payload_bytes), "validation": validation,
        "canonical_package_sha256": package_sha,
        "output_files": list(output_names), "external_relative_path": external_relpath,
    }


def _package_markdown(package: dict[str, Any], package_sha: str) -> str:
    domains = "\n".join(
        f"- `{row['domain']}` — `{row['support_class']}` / `{row['authority_class']}`; state `{row['state_id']}`"
        for row in package["states"])
    missing = "\n".join(f"- `{item}`" for item in package["first_post_t0_consumer_adjudication"]["missing"])
    return f"""# R6 Canonical Initial State Package — 210 Ma

**Status:** `{package['canonical_status']}`

**Package content SHA-256:** `{package_sha}`
**Historical Simulation1 t0 recovered:** `false`

## Identity

- Run: `{package['run_id']}`
- History: `{package['history_id']}`
- GLOBAL_BASE branch: `{package['global_base_branch_id']}`
- Grid: `{package['grid']['grid_id']}` — 180×360, 1° nominal support
- Payload: `{package['materialized_payload']['relative_path']}`
- Payload SHA-256: `{package['materialized_payload']['sha256']}` ({package['materialized_payload']['bytes']} bytes)

## Registered domains

{domains}

UNKNOWN is preserved for bathymetry, plate motion, Deep, climate and hydrology. No numeric placeholders are materialized for those domains.

## First post-t0 consumer

Selected earliest causal domain: `{package['first_post_t0_consumer_adjudication']['selected_domain']}`. It is **blocked and not executed** pending:

{missing}

## Dependency/governance flags

- R5 runtime dependency: `{str(package['r5_runtime_dependency']).lower()}`
- A1 runtime dependency: `{str(package['a1_runtime_dependency']).lower()}`
- Simulation1 trajectory dependency: `{str(package['simulation1_trajectory_dependency']).lower()}`
- Forward scientific simulation executed: `{str(package['scientific_forward_simulation_executed']).lower()}`
- Provider acquisition executed: `{str(package['provider_acquisition_executed']).lower()}`
- P7Q reopened / physical soil created: `{str(package['p7q_reopened']).lower()}` / `{str(package['physical_soil_created']).lower()}`
"""
