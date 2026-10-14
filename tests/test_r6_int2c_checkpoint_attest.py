"""Technical issuance tests: no real kernel or filesystem publication."""
from dataclasses import replace

import pytest

import r6_int2c_checkpoint_attest as attest
import r6_int2c_replay_adapter as adapter
from arcana_worldsim.r6.replay import validate_replay_inputs
from test_r6_int2c_replay_adapter import ROOT, R4, MemoryReadFixture


def test_authenticated_r4_issuance_and_b0_input_contract(monkeypatch):
    monkeypatch.setattr(adapter.kernel, "pure_shear_thermal_step",
                        lambda *a, **k: pytest.fail("numerical execution prohibited"))
    one, two = attest.attest_r4(ROOT, R4), attest.attest_r4(ROOT, R4)
    assert one == two
    assert len(one.records) == 11 and len(one.inventory) == 9
    assert one.original.original_checkpoint.validation_status == "CANDIDATE_NONCANONICAL"
    assert one.original.checkpoint.validation_status == "CANDIDATE_NONCANONICAL"
    p = one.prepared
    assert p.checkpoint.validation_status == "VALIDATED"
    assert p.checkpoint.checkpoint_id != one.original.checkpoint.checkpoint_id
    assert p.recipe.recipe_id != one.original.recipe.recipe_id
    assert p.checkpoint.parent_checkpoint_id == str(one.original.checkpoint.checkpoint_id)
    scope = p.checkpoint.output_manifest["technical_attestation"]
    assert scope["scope"] == attest.SCOPE
    assert scope["numerical_replay_executed"] is False
    inputs = validate_replay_inputs(MemoryReadFixture(p, p.checkpoint), p.recipe)
    assert inputs.base_states == (p.initial,)
    assert inputs.forcings == (p.forcing,)
    assert inputs.expected_state == p.expected
    assert inputs.checkpoint.configuration_sha256 == p.recipe.configuration_sha256


@pytest.mark.parametrize("component", ["python", "numpy"])
def test_actual_runtime_mismatch_prevents_issuance(monkeypatch, component):
    if component == "python":
        monkeypatch.setattr(adapter.platform, "python_version", lambda: "3.12.14")
    else:
        monkeypatch.setattr(adapter.np, "__version__", "2.5.3")
    with pytest.raises(adapter.ReplayBindingError, match="RUNTIME_IDENTITY_MISMATCH"):
        attest.attest_r4(ROOT, R4)


def test_missing_dependency_fails_closed(monkeypatch):
    p = adapter.prepare_r4(ROOT, R4)
    # A malformed prepared closure cannot silently receive a technical status.
    monkeypatch.setattr(attest, "prepare_r4", lambda *a: replace(p, recipe=replace(
        p.recipe, upstream_dependency_ids=())))
    # Typed identities themselves reject alteration before issuance.
    with pytest.raises(ValueError):
        attest.attest_r4(ROOT, R4)


def test_missing_bundle_and_canonical_root_rejected(tmp_path):
    with pytest.raises((ValueError, OSError)):
        attest.attest_r4(ROOT, tmp_path / "missing")
    with pytest.raises(ValueError):
        attest.attest_r4(ROOT, tmp_path / "WORLD_HISTORY")
