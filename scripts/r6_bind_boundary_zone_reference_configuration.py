"""Bind an authorial width-scale prior and fail closed before t0 map creation."""
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
T0_SHA = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
KIN_SHA = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
WIDTH_RANGE_M = [100_000.0, 1_000_000.0]


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def encode_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_json(name: str, value: dict) -> None:
    path = ROOT / name
    payload = encode_json(value)
    if path.exists() and path.read_bytes() != payload:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("artifact") != value.get("artifact") or existing.get("schema") != value.get("schema"):
            raise FileExistsError(f"refusing to overwrite artifact outside this schema/lineage: {name}")
        if existing.get("repository_baseline", {}).get("head", HEAD) != HEAD:
            raise FileExistsError(f"refusing to overwrite artifact with a different repository baseline: {name}")
        path.write_bytes(payload)
    elif not path.exists():
        path.write_bytes(payload)


def write_md(name: str, value: str) -> None:
    path = ROOT / name
    payload = value.encode("utf-8")
    if path.exists() and path.read_bytes() != payload:
        old_title = path.read_text(encoding="utf-8").splitlines()[:1]
        new_title = value.splitlines()[:1]
        if old_title != new_title:
            raise FileExistsError(f"refusing to overwrite Markdown outside this artifact title: {name}")
        path.write_bytes(payload)
    elif not path.exists():
        path.write_bytes(payload)


def validate_inputs() -> dict:
    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    for ref in ("origin/main",):
        if subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip() != HEAD:
            raise RuntimeError(f"unexpected {ref}")
    verify_protected_staged_blobs(ROOT, INDEX_BLOBS)

    partition = read_json("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    kinematics = read_json("R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    boundary = read_json("R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")
    census = read_json("R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json")
    prior_continuum = read_json("R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT.json")
    previous_guard = read_json("R6_T0_CONTINUUM_DEFORMATION_GUARD.json")
    readiness = read_json("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7.json")
    rift = read_json("R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json")
    latent = read_json("R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY_MANIFEST.json")

    if partition["payload"]["sha256"] != VECTOR_SHA or partition["canonical_parent_sha256"] != T0_SHA:
        raise RuntimeError("canonical vector-partition identity mismatch")
    if kinematics["payload_identity_sha256"] != KIN_SHA or kinematics["parent_vector_partition_sha256"] != VECTOR_SHA:
        raise RuntimeError("canonical kinematics identity mismatch")
    if boundary["parent_vector_partition_sha256"] != VECTOR_SHA or boundary["canonical_kinematics_sha256"] != KIN_SHA:
        raise RuntimeError("shared-boundary parent identity mismatch")
    if len(boundary["segments"]) != 1983 or len(boundary["junctions"]) != 20 or len(census["segments"]) != 1983:
        raise RuntimeError("unexpected source graph cardinality")
    if prior_continuum["decision"] != "CONTINUUM_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_UNBOUND":
        raise RuntimeError("unexpected parent continuum decision")
    if previous_guard["positive_horizon_bound"] or readiness["positive_interval"] or readiness["forward_evolution_executed"]:
        raise RuntimeError("parent unexpectedly authorizes a positive interval/evolution")
    if rift["initial_state"]["state"] != "RIFT_QUIESCENT_AT_EXACT_T0" or rift["initial_state"]["progress_m"] != 0.0:
        raise RuntimeError("rift parent authority changed")
    if latent["parent_payload_sha256"] != T0_SHA:
        raise RuntimeError("latent geometry is not bound to canonical t0")
    return {"partition": partition, "kinematics": kinematics, "boundary": boundary, "census": census,
            "prior_continuum": prior_continuum, "previous_guard": previous_guard, "readiness": readiness,
            "rift": rift, "latent": latent}


def build_artifacts(source: dict) -> dict[str, dict | str]:
    class_counts = Counter(item["local_kinematic_diagnostic"] for item in source["census"]["segments"])
    parent_hashes = {name: sha_file(ROOT / name) for name in (
        "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json", "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
        "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json", "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json",
        "R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT.json", "R6_T0_CONTINUUM_DEFORMATION_GUARD.json",
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7.json", "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json",
    )}
    citations = [
        {"source": "Chen & Grimison (1989), Earthquakes associated with diffuse zones of deformation in the oceanic lithosphere: some examples",
         "doi": "10.1016/0040-1951(89)90209-6", "url": "https://doi.org/10.1016/0040-1951(89)90209-6",
         "setting": "Several modern oceanic diffuse-deformation examples", "reported_scale": "up to several hundred kilometres wide",
         "definition_and_limit": "seismic/deformation-zone extent, not a universal mechanical corridor width; not transferable as a measured ARCANA parameter"},
        {"source": "Gordon (1998), The plate tectonic approximation: Plate nonrigidity, diffuse plate boundaries, and global plate reconstructions",
         "doi": "10.1146/annurev.earth.26.1.615", "url": "https://doi.org/10.1146/annurev.earth.26.1.615",
         "setting": "Global review, continental and oceanic diffuse boundaries", "reported_scale": "some zones exceed 1000 km on a side",
         "definition_and_limit": "reported dimensions are not necessarily cross-boundary width; supports context dependence, not a numeric width bound"},
        {"source": "Gurnis et al. (2018), Global tectonic reconstructions with continuously deforming and evolving rigid plates",
         "doi": "10.1016/j.cageo.2018.04.007", "url": "https://doi.org/10.1016/j.cageo.2018.04.007",
         "setting": "Global reconstruction method", "reported_scale": "finite deforming network domains tessellated by triangular mesh",
         "definition_and_limit": "supports finite-domain/strain representation; does not prescribe universal width, partition, or ARCANA constitutive law"},
        {"source": "Official pyGPlates Primer: Deformation and topological networks", "url": "https://www.gplates.org/docs/pygplates/pygplates_primer",
         "setting": "Software representation", "reported_scale": "network polygon, rigid blocks, deforming points, triangulation and strain", "definition_and_limit": "technical capabilities only; no ARCANA physical or width authority"},
        {"source": "Babuška & Melenk (1997), The partition of unity method", "doi": "10.1002/(SICI)1097-0207(19970228)40:4<727::AID-NME86>3.0.CO;2-N",
         "url": "https://doi.org/10.1002/%28SICI%291097-0207%2819970228%2940%3A4%3C727%3A%3AAID-NME86%3E3.0.CO%3B2-N",
         "setting": "Numerical finite-element approximation", "reported_scale": "basis/regularity method, not a geological width", "definition_and_limit": "supports partition-of-unity as a numerical basis concept only; does not provide ARCANA zone geometry or tectonic law"},
        {"source": "McKenzie & Morgan (1969), Evolution of triple junctions", "doi": "10.1038/224125a0", "url": "https://doi.org/10.1038/224125a0",
         "setting": "Plate triple-junction kinematics", "reported_scale": "not a width study", "definition_and_limit": "junction stability depends on boundary configuration/motion, not incidence alone"},
        {"source": "Cronin (1992), Types and kinematic stability of triple junctions", "doi": "10.1016/0040-1951(92)90391-I", "url": "https://doi.org/10.1016/0040-1951(92)90391-I",
         "setting": "Plate triple-junction kinematics", "reported_scale": "not a width study", "definition_and_limit": "requires boundary classes and evolving kinematic constraints"},
    ]
    contract = {
        "artifact": "R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT",
        "schema": "R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT_V1",
        "repository_baseline": repository_provenance(ROOT),
        "parents_sha256": parent_hashes,
        "t0_identity": {"age_ma": 210.0, "canonical_payload_sha256": T0_SHA, "vector_partition_sha256": VECTOR_SHA,
                        "kinematics_identity_sha256": KIN_SHA, "plate_count": 12, "boundary_segments": 1983, "degree3_junctions": 20},
        "width_concepts": {
            "W_model": {"meaning": "full cross-zone width of the reduced model's distributed-deformation domain", "units": "m", "separate_from_numerical": True},
            "W_numerical": {"meaning": "mesh/node/discretization spacing", "units": "m", "value": None, "separate_from_physical": True},
            "W_support": {"meaning": "epistemic support inherited from synthetic 1-degree t0 geometry", "value": "COARSE_SUPPORT_ON_FINE_GRID", "upgraded_by_mesh": False},
        },
        "candidate_prior": {"authority": "AUTHORIAL_REDUCED_MODEL_SPATIAL_PRIOR_CONSTRAINED_BY_LITERATURE_SCALE_CONTEXT",
            "status": "PROPOSED_BOUNDED_SCALE_PRIOR_NOT_CANONICALIZED",
            "full_width_range_m": WIDTH_RANGE_M, "range_semantics": "ARCANA design envelope approximately 10^2–10^3 km for a deliberately diffuse global reduced-interface model; endpoints are authorial bounds, not empirical limits or a universal geological width",
            "distribution": "NONE_ASSIGNED; bounded interval only",
            "conditioning": "GLOBAL_SCALE_CANDIDATE_ONLY; no crust-pair or geological boundary-type conditioning because those types are not bound",
            "canonical_realization": None, "seed_stream": None,
            "selection_rule": "Do not draw a width until the spherical footprint/overlap/narrow-feature acceptance algorithm and criteria are frozen. Then use a predeclared deterministic seed rule and exactly one candidate; no outcome inspection or resampling.",
            "outcome_blind": True},
        "footprint_architecture": {"status": "BLOCKED_NOT_MATERIALIZED", "construction": "NOT_SELECTED",
            "candidate": "Spherical geodesic offset corridor with shared junction patches and one global ownership/partition construction; must be computed from vector edges, never painted raster cells.",
            "bilateral_policy": "UNBOUND; a 50/50 split is not presumed physical; may be an explicit numerical convention only after authorization",
            "core_zone_partition": "UNBOUND", "overlap_resolution": "UNBOUND; no clipping or nearest-plate repair", "narrow_feature_policy": "BLOCK_OR_EXPLICIT_PATCH; no silent width shrink"},
        "interpolation_candidate": {"status": "NOT_BOUND", "candidate": "nonnegative local barycentric/finite-element basis on a single spherical simplicial complex; C0 velocity continuity is a candidate minimum, with partition of unity and tangent-vector interpolation as numerical conventions, not geology",
            "reason": "No footprint, triangulation, boundary constraints, or junction patches exist to verify continuity/derivatives"},
        "reference_state_semantics": {"model_relative_F_at_t0": "IDENTITY_BY_DEFINITION_IF_AND_WHEN_A_REFERENCE_MESH_IS_CREATED",
            "accumulated_R6_post_t0_strain_at_initialization": 0.0,
            "pre_t0_total_geological_strain": "UNKNOWN",
            "canonical_zone_state_materialized": False,
            "interpretation": "The identity/zero are operator-relative initialization semantics only; they assert nothing about geological strain before 210 Ma. No state is instantiated without zone material coordinates."},
        "governance": {"forward_evolution": False, "canonical_t0_changed": False, "vector_partition_changed": False,
            "kinematics_changed": False, "rift_progress_advanced": False, "zone_payload_created": False,
            "scientific_authority_register_mutated": False, "execution_indexes_mutated": False},
        "scientific_sources": citations,
        "decision": "BOUNDARY_FOOTPRINT_CONSTRUCTION_BLOCKED",
        "verdict": "PASS_WIDTH_SCALE_PRIOR_ADJUDICATION__REFERENCE_MAP_NOT_CANONICALIZED",
        "next_action": "R6_SPHERICAL_BOUNDARY_ZONE_FOOTPRINT_AND_JUNCTION_PATCH_CONSTRUCTION",
    }
    matrix = {"artifact": "R6_BOUNDARY_ZONE_WIDTH_EVIDENCE_MATRIX", "schema": "R6_BOUNDARY_ZONE_WIDTH_EVIDENCE_MATRIX_V1",
        "literature_evidence": citations,
        "model_comparison": [
            {"model": "A_SINGLE_GLOBAL_BOUNDED_MODEL_SCALE", "status": "PREFERRED_MINIMUM_PRIOR_CANDIDATE", "reason": "Avoids unsupported type-specific distinctions; a bounded authorial envelope is explicit, but not yet a physical canonical field."},
            {"model": "B_CRUST_PAIR_CONDITIONED", "status": "NOT_AVAILABLE", "reason": "The current boundary records do not govern a crust-pair classification for each segment."},
            {"model": "C_KINEMATIC_MODE_CONDITIONED", "status": "NOT_SELECTED", "reason": "Opening/closing/shear are diagnostics, not geological boundary-type evidence; no source validates mapping mode to width."},
            {"model": "D_SEEDED_SPATIALLY_CORRELATED_FIELD", "status": "UNNECESSARY_COMPLEXITY_AT_THIS_STAGE", "reason": "No support exists for correlation length or covariance; adding them would invent parameters."},
            {"model": "E_ADAPTIVE_NUMERICAL_WIDTH", "status": "NUMERICAL_ONLY_NOT_PHYSICAL", "reason": "Cannot stand in for W_model or produce physical strain authority."},
        ],
        "proposed_authorial_envelope_m": WIDTH_RANGE_M,
        "envelope_status": "DESIGN_HYPOTHESIS_ONLY; literature context does not empirically bound these endpoints",
        "fault_damage_widths_excluded": True,
        "no_distribution_assigned": True,
        "canonical_width_realization": "NOT_MATERIALIZED_PENDING_GEOMETRIC_ACCEPTANCE_RULE",
        "decision": contract["decision"], "verdict": contract["verdict"],
    }
    map_manifest = {"artifact": "R6_T0_BOUNDARY_ZONE_REFERENCE_MAP_MANIFEST", "schema": "R6_T0_BOUNDARY_ZONE_REFERENCE_MAP_MANIFEST_V1",
        "status": "NOT_MATERIALIZED", "time_ma": 210.0, "parent_canonical_payload_sha256": T0_SHA,
        "parent_vector_partition_sha256": VECTOR_SHA, "parent_kinematics_sha256": KIN_SHA,
        "source_boundary_count": 1983, "source_junction_count": 20,
        "model_width_prior_range_m": WIDTH_RANGE_M, "canonical_width": None,
        "zone_footprints": None, "junction_patches": None, "rigid_core_ownership": None,
        "material_coordinates": None, "weights": None, "external_payload": None,
        "reason": "No spherical polygon offset/union, narrow-feature, ownership, or degree-3 patch acceptance implementation has been validated. No raster painting, clipping, or width capping was performed.",
        "canonical_t0_changed": False, "forward_evolution": False}
    validation = {"artifact": "R6_T0_CONTINUUM_REFERENCE_VALIDATION", "schema": "R6_T0_CONTINUUM_REFERENCE_VALIDATION_V1",
        "decision": contract["decision"], "parent_identities_verified": True,
        "tests": {"width_units_and_order": "PASS", "physical_numerical_support_separation": "PASS",
            "t0_F_identity_semantics_vs_unknown_pre_t0_strain": "PASS_DEFINITION_ONLY_NOT_MATERIALIZED",
            "footprint_coverage": "NOT_RUN_NO_FOOTPRINT", "rigid_core_zone_ownership": "NOT_RUN_NO_FOOTPRINT",
            "overlap_gap": "NOT_RUN_NO_FOOTPRINT", "junction_patches": "NOT_RUN_NO_PATCH_GEOMETRY",
            "partition_of_unity": "NOT_RUN_NO_MESH", "spherical_tangent_velocity": "NOT_RUN_NO_BASIS",
            "relative_motion_conservation": "NOT_RUN_NO_FIELD", "jacobian_invertibility": "NOT_RUN_NO_REFERENCE_MAP",
            "pure_opening_closing_shear_and_mixed_fixtures": "NOT_RUN_NO_SELECTED_MAP_OPERATOR",
            "dateline_polar_and_narrow_feature_fixtures": "NOT_RUN_NO_FOOTPRINT_OPERATOR",
            "high_deformation_guard": "NOT_RUN_NO_JACOBIAN_OR_VALIDITY_THRESHOLD",
            "deterministic_generation": "PASS_CONTRACT_SERIALIZATION_ONLY", "canonical_parent_mutation": "NONE"},
        "blocker": "SPHERICAL_FOOTPRINT_AND_JUNCTION_PATCH_CONSTRUCTION_NOT_IMPLEMENTED_OR_VALIDATED",
        "forward_evolution": False}
    readiness = {"artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V8", "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V8",
        "repository": repository_provenance(ROOT),
        "decision": contract["decision"], "verdict": contract["verdict"], "t0_ma": 210.0,
        "positive_interval": False, "dt_first_years": None, "execution_contract_created": False,
        "width_prior": "BOUNDED_AUTHORIAL_SCALE_ENVELOPE_PROPOSED; canonical realization pending geometry gate",
        "zone_map": "NOT_MATERIALIZED", "reference_F_t0": "IDENTITY_BY_DEFINITION_IF_MESH_CREATED; not instantiated",
        "pre_t0_geological_strain": "UNKNOWN", "post_t0_operator_strain_initialization": "ZERO_BY_DEFINITION_IF_STATE_CREATED",
        "continuous_velocity_basis": "NOT_BOUND", "jacobian_guard": "NOT_EVALUABLE", "boundary_segments_blocked": 1983,
        "junctions_blocked": 20, "rift_guard_years": source["previous_guard"]["existing_rift_guard_years"],
        "rift_guard_is_legal_dt": False, "canonical_t0_changed": False, "vector_partition_changed": False,
        "kinematics_changed": False, "forward_evolution": False,
        "remaining_blocker": "SPHERICAL_FOOTPRINT_AND_DEGREE3_JUNCTION_PATCH_CONSTRUCTION_WITH_VALIDATED_OWNERSHIP_AND_COVERAGE",
        "next_action": contract["next_action"]}
    return {
        "R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT.json": contract,
        "R6_BOUNDARY_ZONE_WIDTH_EVIDENCE_MATRIX.json": matrix,
        "R6_T0_BOUNDARY_ZONE_REFERENCE_MAP_MANIFEST.json": map_manifest,
        "R6_T0_CONTINUUM_REFERENCE_VALIDATION.json": validation,
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V8.json": readiness,
        "R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT.md": contract_md(contract),
        "R6_BOUNDARY_ZONE_WIDTH_EVIDENCE_MATRIX.md": matrix_md(matrix),
        "R6_T0_CONTINUUM_REFERENCE_VALIDATION.md": validation_md(validation),
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V8.md": readiness_md(readiness),
    }


def contract_md(x: dict) -> str:
    return ("# R6 boundary-zone footprint and width-prior contract\n\n"
        f"Decision: **{x['decision']}**\n\n{ x['verdict'] }. The bounded scale is an ARCANA design hypothesis, not an empirical universal width.\n\n"
        "## Width concepts\n\n"
        "`W_model` (physical-model domain scale), `W_numerical` (mesh spacing), and `W_support` (coarse inherited support) are separate. Proposed `W_model` envelope: 100–1,000 km, with no probability distribution. Both endpoints are authorial assumptions, informed only by broad literature scale context; they are not measured bounds. Fault-damage-zone widths are excluded.\n\n"
        "No canonical realization is drawn until footprint and acceptance rules are frozen. The t0 geometry requires spherical vector corridors, non-overlapping core/zone ownership, shared degree-3 junction patches, and no silent clipping/capping. Those are not yet implemented or validated, so no map or t0 zone state exists.\n\n"
        "If a reference mesh is later created, `F_R6(t0)=I` and accumulated post-t0 operator strain zero are definitions relative to that operator's start. Pre-t0 geological strain remains `UNKNOWN`; no claim of a geologically undeformed Earth is made.\n\n"
        "Opening continues to use existing rift progress as its sole source of truth. Shortening is not subduction/orogeny; shear is not fault mechanics. No strain rates or Jacobian guard are computed without an instantiated field and mesh.\n\n"
        "## Sources\n\n"+"\n".join(f"- [{s['source']}]({s['url']}): {s['reported_scale']}; {s['definition_and_limit']}." for s in x['scientific_sources'])+"\n")


def matrix_md(x: dict) -> str:
    rows="\n".join(f"| {e['model']} | {e['status']} | {e['reason']} |" for e in x['model_comparison'])
    return ("# R6 boundary-zone width evidence matrix\n\n| Candidate | Status | Finding |\n|---|---|---|\n"+rows+
        "\n\nThe proposed authorial envelope is 100,000–1,000,000 m, with no distribution. Its endpoints are not empirical limits. Chen & Grimison report several-hundred-kilometre extents in oceanic diffuse deformation examples; Gordon reports some diffuse zones exceeding 1,000 km on a side (not necessarily cross-boundary width). These contextual observations do not calibrate a universal ARCANA parameter.\n")


def validation_md(x: dict) -> str:
    return ("# R6 t0 continuum reference validation\n\nParent identity and contract semantics validate. The reference map itself is not materialized.\n\n"
        "Footprint, ownership, overlap/gap, junction patches, partition of unity, spherical velocity, Jacobian, and deformation fixtures are **not run** because no footprint or mesh operator is selected. This is a fail-closed result, not a validation pass for continuum geometry.\n\n"
        f"Blocker: `{x['blocker']}`. No future geometry or physical evolution was produced.\n")


def readiness_md(x: dict) -> str:
    return ("# R6 first physical interval readiness V8\n\n"
        f"**{x['decision']}** — {x['verdict']}.\n\nThe authorial scale envelope is proposed but not realized. The t0 zone map, junction patches, continuous velocity field, and Jacobian guard are absent. The existing rift horizon is not a timestep. `dt_first_years = null`; no execution contract or forward state was created.\n\n"
        f"Remaining blocker: {x['remaining_blocker']}.\n\nNext action: `{x['next_action']}`.\n")


def main() -> None:
    outputs = build_artifacts(validate_inputs())
    for name, value in outputs.items():
        if name.endswith(".json"):
            write_json(name, value)  # type: ignore[arg-type]
        else:
            write_md(name, value)  # type: ignore[arg-type]
    print(json.dumps({"decision": outputs["R6_FIRST_PHYSICAL_INTERVAL_READINESS_V8.json"]["decision"],
                      "width_prior_m": WIDTH_RANGE_M, "map_materialized": False, "dt_first_years": None}, sort_keys=True))


if __name__ == "__main__":
    main()
