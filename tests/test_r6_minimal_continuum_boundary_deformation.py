"""Contract checks for the fail-closed continuum-boundary adjudication."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6_bind_minimal_continuum_boundary_deformation.py"
SPEC = importlib.util.spec_from_file_location("r6_minimal_continuum", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_model_families_do_not_confuse_representation_with_physics():
    outputs = MODULE.build_artifacts(MODULE.validate_inputs())
    contract = outputs["R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT.json"]
    families = {x["family"]: x["status"] for x in contract["model_family_adjudication"]}
    assert families["A_FINITE_WIDTH_CONTINUOUS_DEFORMATION_ZONE"] == "NOT_BOUND"
    assert families["B_TRIANGULATED_DEFORMING_NETWORK"] == "REPRESENTATION_CANDIDATE_NOT_CAUSAL_AUTHORITY"
    assert families["C_ZERO_WIDTH_INTERFACE_LEDGER"] == "INSUFFICIENT_FOR_CONTINUOUS_MATERIAL_MAP"
    assert families["D_FAIL_CLOSED"] == "CURRENT_POLICY_RETAINED"


def test_width_initial_strain_and_jacobian_remain_unknown_not_fabricated():
    outputs = MODULE.build_artifacts(MODULE.validate_inputs())
    contract = outputs["R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT.json"]
    guard = outputs["R6_T0_CONTINUUM_DEFORMATION_GUARD.json"]
    readiness = outputs["R6_FIRST_PHYSICAL_INTERVAL_READINESS_V7.json"]
    assert contract["width_adjudication"]["value"] is None
    assert contract["t0_process_state"]["materialized"] is False
    assert contract["t0_process_state"]["strain_initialization"] == "NOT_ASSIGNED; not assumed zero"
    assert guard["t0_diagnostics"]["minimum_jacobian"] is None
    assert guard["t0_diagnostics"]["maximum_extensional_strain_rate_per_year"] is None
    assert readiness["positive_interval"] is False
    assert readiness["dt_first_years"] is None


def test_no_forward_state_or_canonical_parent_is_changed_by_contract_generation():
    outputs = MODULE.build_artifacts(MODULE.validate_inputs())
    contract = outputs["R6_MINIMAL_CONTINUUM_BOUNDARY_DEFORMATION_CONTRACT.json"]
    assert all(value is False for key, value in contract["governance"].items()
               if key.endswith("changed") or key.endswith("executed") or key.endswith("advanced") or key.endswith("created"))
    assert "R6_T0_BOUNDARY_PROCESS_STATE_MANIFEST.json" not in outputs
    assert "R6_FIRST_PHYSICAL_INTERVAL_EXECUTION_CONTRACT.json" not in outputs


def test_artifacts_are_json_serializable_without_nonfinite_values():
    outputs = MODULE.build_artifacts(MODULE.validate_inputs())
    for name, value in outputs.items():
        if name.endswith(".json"):
            encoded = MODULE.canonical_bytes(value)
            parsed = json.loads(encoded)
            assert parsed["artifact"]

