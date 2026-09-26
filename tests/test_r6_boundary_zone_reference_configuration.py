"""Reference-configuration contract tests; no spherical t0 zone is fabricated."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6_bind_boundary_zone_reference_configuration.py"
SPEC = importlib.util.spec_from_file_location("r6_boundary_reference", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def outputs():
    return MODULE.build_artifacts(MODULE.validate_inputs())


def test_width_envelope_is_authorial_context_not_empirical_universal_bound():
    result = outputs()["R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT.json"]
    prior = result["candidate_prior"]
    assert prior["full_width_range_m"] == [100_000.0, 1_000_000.0]
    assert prior["distribution"] == "NONE_ASSIGNED; bounded interval only"
    assert prior["status"] == "PROPOSED_BOUNDED_SCALE_PRIOR_NOT_CANONICALIZED"
    assert prior["canonical_realization"] is None
    assert prior["outcome_blind"] is True


def test_three_width_concepts_and_support_are_not_conflated():
    contract = outputs()["R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT.json"]
    concepts = contract["width_concepts"]
    assert concepts["W_model"]["units"] == "m"
    assert concepts["W_numerical"]["value"] is None
    assert concepts["W_support"]["upgraded_by_mesh"] is False


def test_reference_strain_semantics_preserve_unknown_pre_t0_history():
    contract = outputs()["R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT.json"]
    state = contract["reference_state_semantics"]
    assert state["model_relative_F_at_t0"].startswith("IDENTITY_BY_DEFINITION")
    assert state["accumulated_R6_post_t0_strain_at_initialization"] == 0.0
    assert state["pre_t0_total_geological_strain"] == "UNKNOWN"
    assert state["canonical_zone_state_materialized"] is False


def test_no_map_or_interval_is_claimed_without_geometry_validation():
    all_outputs = outputs()
    reference = all_outputs["R6_T0_BOUNDARY_ZONE_REFERENCE_MAP_MANIFEST.json"]
    validation = all_outputs["R6_T0_CONTINUUM_REFERENCE_VALIDATION.json"]
    readiness = all_outputs["R6_FIRST_PHYSICAL_INTERVAL_READINESS_V8.json"]
    assert reference["status"] == "NOT_MATERIALIZED"
    assert reference["zone_footprints"] is None
    assert validation["tests"]["footprint_coverage"] == "NOT_RUN_NO_FOOTPRINT"
    assert validation["tests"]["jacobian_invertibility"] == "NOT_RUN_NO_REFERENCE_MAP"
    assert readiness["positive_interval"] is False
    assert readiness["dt_first_years"] is None
    assert readiness["boundary_segments_blocked"] == 1983
    assert readiness["junctions_blocked"] == 20


def test_json_outputs_are_deterministically_serializable():
    for name, value in outputs().items():
        if name.endswith(".json"):
            parsed = json.loads(MODULE.encode_json(value))
            assert parsed["artifact"]

