"""Adjudicate minimum continuum-boundary authority without advancing R6 time."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import require_repository_context, repository_provenance, verify_protected_staged_blobs
HEAD = "592b1651b405363373590092e133bd25569d99a5"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
KIN_SHA = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
T0_SHA = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def write_json(name: str, value: dict) -> None:
    path = ROOT / name
    data = canonical_bytes(value)
    if path.exists() and path.read_bytes() != data:
        raise FileExistsError(f"refusing to overwrite pre-existing task output: {name}")
    if not path.exists():
        path.write_bytes(data)


def write_md(name: str, text: str) -> None:
    path = ROOT / name
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() != data:
        raise FileExistsError(f"refusing to overwrite pre-existing task output: {name}")
    if not path.exists():
        path.write_bytes(data)


def validate_inputs() -> dict:
    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    for ref in ("origin/main",):
        if subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip() != HEAD:
            raise RuntimeError(f"unexpected {ref}")
    verify_protected_staged_blobs(ROOT, INDEX_BLOBS)

    partition = read_json("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    kinematics = read_json("R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    state = read_json("R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")
    census = read_json("R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json")
    previous_law = read_json("R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json")
    finite = read_json("R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json")
    junction = read_json("R6_JUNCTION_COMPATIBILITY_CONTRACT.json")
    rift = read_json("R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json")
    readiness = read_json("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V6.json")
    guard = read_json("R6_BOUNDARY_AND_JUNCTION_GUARD.json")

    if partition["payload"]["sha256"] != VECTOR_SHA or partition["canonical_parent_sha256"] != T0_SHA:
        raise RuntimeError("t0 vector partition identity mismatch")
    if kinematics["payload_identity_sha256"] != KIN_SHA or kinematics["parent_vector_partition_sha256"] != VECTOR_SHA:
        raise RuntimeError("canonical kinematics identity mismatch")
    if state["parent_vector_partition_sha256"] != VECTOR_SHA or state["canonical_kinematics_sha256"] != KIN_SHA:
        raise RuntimeError("shared-boundary state parent mismatch")
    if len(census["segments"]) != 1983 or len(state["junctions"]) != 20:
        raise RuntimeError("unexpected t0 segment or junction cardinality")
    if finite["finite_step_status_counts"] != {"BLOCKED": 1983} or finite["junction_status_counts"] != {"BLOCKED": 20}:
        raise RuntimeError("the parent fail-closed census no longer matches expected state")
    if previous_law["decision"] != "NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND":
        raise RuntimeError("unexpected previous boundary-law decision")
    if rift["initial_state"]["progress_m"] != 0.0 or rift["initial_state"]["state"] != "RIFT_QUIESCENT_AT_EXACT_T0":
        raise RuntimeError("rift t0 authority mismatch")
    if readiness["positive_interval"] or readiness["forward_evolution_executed"]:
        raise RuntimeError("unexpected prior first-interval readiness/evolution state")
    return {"partition": partition, "kinematics": kinematics, "state": state, "census": census,
            "finite": finite, "junction": junction, "rift": rift, "previous_law": previous_law,
            "previous_guard": guard}


def build_artifacts(inputs: dict) -> dict[str, dict | str]:
    segments = inputs["census"]["segments"]
    modes = Counter(s["local_kinematic_diagnostic"] for s in segments)
    max_normal = max(abs(float(s["relative_normal_velocity_m_per_year"])) for s in segments)
    max_tangent = max(abs(float(s["relative_tangential_velocity_m_per_year"])) for s in segments)
    sources = [
        {"citation": "Gordon (1998), The plate tectonic approximation: Plate nonrigidity, diffuse plate boundaries, and global plate reconstructions",
         "doi": "10.1146/annurev.earth.26.1.615", "url": "https://doi.org/10.1146/annurev.earth.26.1.615",
         "finding": "Diffuse zones vary strongly in scale; some exceed 1000 km across and reported relative rates/strain vary. This demonstrates non-universality, not an ARCANA width prior."},
        {"citation": "Gurnis et al. (2018), Global tectonic reconstructions with continuously deforming and evolving rigid plates",
         "doi": "10.1016/j.cageo.2018.04.007", "url": "https://doi.org/10.1016/j.cageo.2018.04.007",
         "finding": "A deforming network uses finite network geometry and triangular tessellation with strain tracking; it is an implementation representation requiring specified domain and constraints, not a universal constitutive law."},
        {"citation": "Bird (2003), An updated digital model of plate boundaries",
         "doi": "10.1029/2001GC000252", "url": "https://doi.org/10.1029/2001GC000252",
         "finding": "Boundary classes combine kinematics with geological evidence; relative motion alone does not determine process type."},
        {"citation": "McKenzie & Morgan (1969), Evolution of triple junctions",
         "doi": "10.1038/224125a0", "url": "https://doi.org/10.1038/224125a0",
         "finding": "Junction stability depends on boundary configuration and motion; incidence degree alone is insufficient."},
        {"citation": "Cronin (1992), Types and kinematic stability of triple junctions",
         "doi": "10.1016/0040-1951(92)90391-I", "url": "https://doi.org/10.1016/0040-1951(92)90391-I",
         "finding": "Kinematic compatibility/stability depends on boundary types and evolving motions, unavailable for the synthetic t0 graph."},
        {"citation": "pyGPlates Primer, Deformation and topological networks", "url": "https://www.gplates.org/docs/pygplates/pygplates_primer",
         "finding": "The technical model represents finite network polygons, optional rigid blocks, deforming points, triangulation, and strain; it does not select ARCANA physics or parameters."},
    ]
    parents = {
        name: digest(ROOT / name) for name in (
            "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json", "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
            "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json", "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json",
            "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json", "R6_JUNCTION_COMPATIBILITY_CONTRACT.json",
            "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json", "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V6.json",
        )
    }
    shared = {
        "schema": "R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT_V1",
        "artifact": "R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT",
        "repository_baseline": repository_provenance(ROOT),
        "t0": {"age_ma": 210.0, "plate_count": 12, "boundary_segment_count": 1983, "degree3_junction_count": 20,
               "vector_partition_sha256": VECTOR_SHA, "canonical_kinematics_identity_sha256": KIN_SHA,
               "canonical_initial_world_sha256": T0_SHA},
        "parent_artifact_sha256": parents,
        "model_family_adjudication": [
            {"family": "A_FINITE_WIDTH_CONTINUOUS_DEFORMATION_ZONE", "status": "NOT_BOUND",
             "reason": "No zone footprint, width, core ownership, material-coordinate mapping, deformation law, or event capacity is defined for the untyped synthetic interfaces."},
            {"family": "B_TRIANGULATED_DEFORMING_NETWORK", "status": "REPRESENTATION_CANDIDATE_NOT_CAUSAL_AUTHORITY",
             "reason": "A mesh can represent strain only after network domains, boundary/core constraints, initial material state, and a constitutive/kinematic map are specified."},
            {"family": "C_ZERO_WIDTH_INTERFACE_LEDGER", "status": "INSUFFICIENT_FOR_CONTINUOUS_MATERIAL_MAP",
             "reason": "Bookkeeping does not locate material or define a one-to-one spherical map and cannot prove coverage/invertibility."},
            {"family": "D_FAIL_CLOSED", "status": "CURRENT_POLICY_RETAINED",
             "reason": "No positive finite-time transition is authorized until zone footprint/width and response/junction semantics are governed."},
        ],
        "width_adjudication": {"value": None, "units": "m", "status": "UNBOUND_NO_UNIVERSAL_TRANSFERABLE_WIDTH",
            "literature_transfer": "Published diffuse-boundary dimensions vary by tectonic setting and reach hundreds to >1000 km in some examples; those observations do not establish a universal width for ARCANA's untyped synthetic interfaces.",
            "forbidden_substitutes": ["1-degree grid spacing", "boundary edge length", "arbitrary fixed width", "unseeded width assignment"]},
        "t0_process_state": {"materialized": False, "strain_initialization": "NOT_ASSIGNED; not assumed zero",
            "reason": "No zone footprint/material domain exists to which a strain tensor or deformation gradient could attach. This task does not canonicalize an empty or undeformed zone."},
        "candidate_future_model_semantics": {"velocity_field": "UNBOUND; no interpolation selected", "opening": "existing cumulative local boundary normal opening/rift progress remains sole source of truth and is not advanced",
            "shortening": "NOT_MATERIALIZED; not subduction, crustal thickening, orogeny, or elevation", "shear": "NOT_MATERIALIZED; not fault slip",
            "finite_strain_state": "UNBOUND; no deformation gradient/Jacobian state can be evaluated without a material mesh", "junction_velocity": "UNBOUND; no boundary types/constraints; no averaging",
            "remeshing": "NOT_BOUND", "history_policy": "CHECKPOINT_ONLY if future unresolved model-valid strain is explicitly supported; no World History snapshot until complete partition and process semantics validate"},
        "governance": {"forward_evolution_executed": False, "future_geometry_created": False, "rift_progress_advanced": False,
            "shortening_advanced": False, "shear_advanced": False, "canonical_t0_changed": False,
            "canonical_kinematics_changed": False, "canonical_partition_changed": False,
            "scientific_authority_register_mutated": False, "execution_indexes_mutated": False},
        "sources": sources,
        "decision": "CONTINUUM_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_UNBOUND",
        "verdict": "PASS_TARGETED_CONTINUUM_MODEL_ADJUDICATION__FIRST_INTERVAL_BLOCKED",
        "next_action": "R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_BINDING",
    }
    evidence = {
        "schema": "R6_BOUNDARY_DEFORMATION_PARAMETER_EVIDENCE_MATRIX_V1",
        "artifact": "R6_BOUNDARY_DEFORMATION_PARAMETER_EVIDENCE_MATRIX",
        "parameters": [
            {"parameter": "boundary_zone_footprint_and_core_ownership", "units": "spatial geometry", "authority": "MISSING_MODEL_DEFINITION", "effect": "required to define material domain and continuous core/interface joins"},
            {"parameter": "zone_width", "units": "m", "authority": "NO_UNIVERSAL_TRANSFERABLE_WIDTH; literature reports setting-dependent diffuse zones", "effect": "sets strain from relative displacement and affects map regularity; no value assigned"},
            {"parameter": "interpolation_or_shape_functions", "units": "dimensionless / basis definition", "authority": "NOT_SELECTED", "effect": "must satisfy shared-core boundary conditions and junction continuity"},
            {"parameter": "compressive_model_validity_or_handoff", "units": "strain or displacement", "authority": "MISSING_FOR_UNTYPED_SYNTHETIC_BOUNDARIES", "effect": "needed before shortening response is physically unresolved beyond tolerance"},
            {"parameter": "shear_model_validity_or_handoff", "units": "strain or displacement", "authority": "MISSING", "effect": "no fault/slip law or numerical validity limit bound"},
            {"parameter": "jacobian_quality_floor_and_mesh_tolerance", "units": "dimensionless / geometry tolerance", "authority": "NOT_PRECOMMITTED", "effect": "cannot compute a positive invertibility horizon absent a mesh/material map"},
        ],
        "numeric_literature_bounds_transferred": [],
        "reason_no_numeric_zone_width_bound": "Observed diffuse-boundary scales vary strongly by tectonic setting; current synthetic boundary segments are not geologically typed, and coarse cell support/edge length is not a physical deforming-zone width.",
        "sources": sources,
        "decision": shared["decision"], "verdict": shared["verdict"],
    }
    guard = {
        "schema": "R6_T0_CONTINUUM_DEFORMATION_GUARD_V1", "artifact": "R6_T0_CONTINUUM_DEFORMATION_GUARD",
        "t0_ma": 210.0, "parent_vector_partition_sha256": VECTOR_SHA, "canonical_kinematics_sha256": KIN_SHA,
        "t0_diagnostics": {"segments": len(segments), "junctions": 20, "kinematic_classes": dict(sorted(modes.items())),
            "maximum_absolute_normal_relative_velocity_m_per_year": max_normal,
            "maximum_absolute_tangential_relative_velocity_m_per_year": max_tangent,
            "maximum_extensional_strain_rate_per_year": None, "maximum_compressive_strain_rate_per_year": None,
            "maximum_shear_strain_rate_per_year": None, "width_min_m": None, "width_median_m": None, "width_max_m": None,
            "minimum_jacobian": None, "limiting_segment": None, "limiting_junction": None},
        "boundary_deformation_guard_years": None, "junction_compatibility_guard_years": None, "combined_topology_guard_years": None,
        "reason": "No material-zone geometry/width, velocity map, finite-strain field, junction constraints, or precommitted Jacobian criterion exists; a numeric guard would be fabricated.",
        "existing_rift_guard_years": inputs["previous_guard"]["rift_event_guard_years"],
        "existing_rift_guard_is_legal_dt": False, "first_dt_years": None, "positive_horizon_bound": False,
        "segment_disposition_counts": {"BLOCKED": 1983}, "junction_disposition_counts": {"BLOCKED": 20},
        "t0_state_materialized": False, "predictive_geometry_computed": False, "forward_evolution_executed": False,
    }
    readiness = {
        "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7", "artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7",
        "repository": repository_provenance(ROOT),
        "decision": shared["decision"], "verdict": shared["verdict"], "t0_ma": 210.0,
        "positive_interval": False, "dt_first_years": None, "execution_contract_created": False,
        "boundary_segments": {"total": 1983, "advance_allowed": 0, "blocked": 1983},
        "junctions": {"total": 20, "compatible": 0, "blocked": 20},
        "t0_boundary_zone_state": "NOT_MATERIALIZED", "initial_strain": "NOT_ASSIGNED_NOT_ASSUMED_ZERO",
        "coverage": "T0 PARTITION ONLY; NO FUTURE CONTINUOUS-COVERAGE CLAIM",
        "jacobian_invertibility": "NOT_EVALUABLE_WITHOUT_MATERIAL_MESH_AND_PRECOMMITTED_GUARD",
        "historical_snapshot_with_unresolved_strain": "CHECKPOINT_ONLY_IF_LATER_EXPLICITLY_AUTHORIZED; current interval blocked",
        "canonical_t0_changed": False, "canonical_kinematics_changed": False, "canonical_partition_changed": False,
        "rift_progress_advanced": False, "forward_evolution_executed": False,
        "remaining_blocker": "NO_GOVERNED_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR; no continuous material map/strain or junction constraint can be evaluated",
        "next_action": shared["next_action"],
    }
    return {
        "R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT.json": shared,
        "R6_BOUNDARY_DEFORMATION_PARAMETER_EVIDENCE_MATRIX.json": evidence,
        "R6_T0_CONTINUUM_DEFORMATION_GUARD.json": guard,
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7.json": readiness,
        "R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT.md": contract_md(shared),
        "R6_BOUNDARY_DEFORMATION_PARAMETER_EVIDENCE_MATRIX.md": evidence_md(evidence),
        "R6_T0_CONTINUUM_DEFORMATION_GUARD.md": guard_md(guard),
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7.md": readiness_md(readiness),
    }


def contract_md(x: dict) -> str:
    return ("# R6 minimal continuum boundary-deformation contract\n\n"
            f"Decision: **{x['decision']}**\n\n{ x['verdict'] }. No forward evolution is authorized.\n\n"
            "## Adjudication\n\n"
            "Finite-width zones and triangulated deforming networks are scientifically useful representation families, but ARCANA has not defined the zone footprint, width, core ownership, material-coordinate map, strain law, or junction constraints. The zero-width ledger does not establish where material resides. The current fail-closed policy therefore remains.\n\n"
            "Diffuse-boundary dimensions vary by tectonic setting; reported Earth examples cannot be promoted to a universal width for untyped synthetic boundaries. The 1-degree cell scale and edge length are not substitutes. No t0 zone state is created and initial strain is not assumed zero.\n\n"
            "Opening continues to use the existing rift-progress state as its sole source of truth (not advanced). Shortening and shear remain unmaterialized and are not interpreted as subduction, orogeny, or fault slip. No continuous velocity field, finite strain, Jacobian guard, or junction velocity is selected.\n\n"
            "## Sources\n\n" + "\n".join(f"- [{s['citation']}]({s['url']}): {s['finding']}" for s in x['sources']) + "\n")


def evidence_md(x: dict) -> str:
    rows = "\n".join(f"| {p['parameter']} | {p['units']} | {p['authority']} |" for p in x["parameters"])
    return "# R6 boundary-deformation parameter evidence matrix\n\n| Parameter | Units | Authority status |\n|---|---|---|\n" + rows + "\n\n" + x["reason_no_numeric_zone_width_bound"] + "\n"


def guard_md(x: dict) -> str:
    d = x["t0_diagnostics"]
    return ("# R6 t0 continuum-deformation guard\n\n"
            f"At 210 Ma: {d['segments']} boundary segments and {d['junctions']} junctions. Available maximum absolute relative velocities are {d['maximum_absolute_normal_relative_velocity_m_per_year']:.9g} m/year normal and {d['maximum_absolute_tangential_relative_velocity_m_per_year']:.9g} m/year tangential. Strain rates and Jacobian are not computable without a governed zone width/material mesh.\n\n"
            "Boundary and junction horizons are unbound; first dt is null. The existing 27,123.405-year rift guard is conditional and is not a legal dt. No predictive geometry or future state was computed.\n")


def readiness_md(x: dict) -> str:
    return ("# R6 first physical interval readiness V7\n\n"
            f"**{x['decision']}** — {x['verdict']}.\n\n"
            f"All {x['boundary_segments']['blocked']} boundary segments and {x['junctions']['blocked']} junctions remain blocked. No t0 zone state or initial strain is assigned; no positive interval, Jacobian guard, or execution contract exists.\n\n"
            f"Remaining blocker: {x['remaining_blocker']}.\n\nNext action: `{x['next_action']}`.\n")


def main() -> None:
    outputs = build_artifacts(validate_inputs())
    for name, value in outputs.items():
        if name.endswith(".json"):
            write_json(name, value)  # type: ignore[arg-type]
        else:
            write_md(name, value)  # type: ignore[arg-type]
    print(json.dumps({"decision": outputs["R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7.json"]["decision"],
                      "positive_interval": False, "dt_first_years": None, "forward_evolution_executed": False}, sort_keys=True))


if __name__ == "__main__":
    main()
