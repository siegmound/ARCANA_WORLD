"""Filesystem-independent contract tests. All runner calls use a mock kernel."""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import platform

import pytest

import r6_int2c_replay_adapter as adapter
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.functional_development import initial_reduced_state
from arcana_worldsim.r6.identity import (
    CheckpointId, DomainStateId, ForcingId, ReplayRecipeId, content_hash, thaw_json,
)
from arcana_worldsim.r6.int0a_pipeline import build_fixture_pair_plan, trajectory_document
from arcana_worldsim.r6.replay import (
    ReplayInputError, ReplayRecipe, execute_replay, validate_replay_inputs,
)
from arcana_worldsim.r6.state import AuthorityClass, DomainStateEnvelope
from test_r6_int0a_pipeline import _assessment

ROOT = Path(__file__).resolve().parents[1]
R4 = ROOT / "outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04"


def changed(record, id_field, identity_type, parser, **changes):
    row = record.to_dict()
    row.update(changes)
    row.pop(id_field)
    row[id_field] = str(identity_type.from_payload(row))
    return parser(row)


@pytest.fixture
def synthetic():
    plan = build_fixture_pair_plan(_assessment())
    initial = tuple(initial_reduced_state(p, initial_width_m=plan.initial_width_m) for p in plan.profiles)
    # Hand-declared synthetic output; not a physical model or numerical replay.
    expected = tuple(replace(state, time_s=2.0) for state in initial)
    numerical = {"duration_years": 2.0 / adapter.kernel.SECONDS_PER_YEAR,
                 "maximum_kinematic_fraction_per_substep": 0.01,
                 "kernel": "functional_development.pure_shear_thermal_step"}
    doc = trajectory_document(plan, expected, duration_s=2.0, numerical_configuration=numerical)
    source = {"execution_commit": "a" * 40, "scope": "SYNTHETIC_FIXTURE_ONLY",
              "kernel_canonical_text_sha256": adapter.KERNEL_SHA256,
              "adapter_canonical_text_sha256": adapter._text_hash(Path(adapter.__file__).read_bytes()),
              "python": platform.python_version(), "numpy": adapter.np.__version__}
    config = {"configuration_sha256": doc["configuration_sha256"],
              "numerical_configuration": numerical, "duration_seconds": 2.0,
              "signed_Ux_m_per_year": plan.signed_extension_m_per_year}
    return adapter._bind_candidate(
        DomainStateEnvelope.from_dict(doc["b0_domain_states"]["initial"]),
        DomainStateEnvelope.from_dict(doc["b0_domain_states"]["candidate"]),
        ForcingRecord.from_dict(doc["b0_forcing_record"]),
        CheckpointEnvelope.from_dict(doc["b0_checkpoints"]["initial"]),
        ReplayRecipe.from_dict(doc["b0_replay_recipe"]), config, source,
        {"SYNTHETIC_FIXTURE_ONLY": "1" * 64})


def validated_fixture(p):
    # This transition is ONLY for fixtures; no real R4 checkpoint is promoted.
    assert p.initial.authority_class == AuthorityClass.FIXTURE_ONLY
    assert p.source_identity["scope"] == "SYNTHETIC_FIXTURE_ONLY"
    checkpoint = changed(p.checkpoint, "checkpoint_id", CheckpointId,
                         CheckpointEnvelope.from_dict, validation_status="VALIDATED")
    recipe = changed(p.recipe, "recipe_id", ReplayRecipeId, ReplayRecipe.from_dict,
                     base_checkpoint_id=str(checkpoint.checkpoint_id))
    return checkpoint, recipe


class MemoryReadFixture:
    """Test-only reader double for B0 contracts; no persistence or query implementation."""
    def __init__(self, p, checkpoint):
        self.states = {str(x.state_id): x for x in (p.initial, p.expected)}
        self.checkpoints = {str(checkpoint.checkpoint_id): checkpoint.to_dict()}
        self.forcings = {str(p.forcing.forcing_id): p.forcing.to_dict()}
        self.provenance = {str(p.provenance.record_id): p.provenance.to_dict()}

    @contextmanager
    def read_view(self):
        yield self

    def read_state(self, key):
        return self.states[key]

    def read_checkpoint(self, key):
        return self.checkpoints[key]

    def read_forcing(self, key):
        return self.forcings[key]

    def read_provenance(self, key):
        return self.provenance[key]


def test_verified_r4_preparation_preserves_originals_and_never_executes_kernel(monkeypatch):
    monkeypatch.setattr(adapter.kernel, "pure_shear_thermal_step",
                        lambda *a, **k: pytest.fail("real R4 kernel must not execute"))
    one, two = adapter.prepare_r4(ROOT, R4), adapter.prepare_r4(ROOT, R4)
    assert [x.to_dict() for x in one.records] == [x.to_dict() for x in two.records]
    assert one.checkpoint.validation_status == one.original_checkpoint.validation_status == "CANDIDATE_NONCANONICAL"
    assert one.checkpoint.checkpoint_id != one.original_checkpoint.checkpoint_id
    assert one.recipe.recipe_id != one.original_recipe.recipe_id
    assert one.checkpoint.upstream_dependency_ids == one.recipe.upstream_dependency_ids
    assert one.source_identity["execution_commit"] == "91fc83d50ec15d8bb9b826926ac2f2dc859281e8"
    assert one.configuration["historical_configuration"]["duration_seconds"] == 31_557_600_000.0
    assert one.forcing.value["signed_Ux_m_per_year"] == 0.11467052868814648
    assert one.initial.state_id.value == "r6state_a4c9f8dc71cc77d52b6e5d54cd82c921e57e9de9f3c4ce740f7de91a98aac127"
    assert one.expected.state_id.value == "r6state_d36b8094e89671d0d25894bcd4d798efdb426c65fcd6eb5d6652531f92c51d6a"


def test_candidate_checkpoint_remains_rejected_by_existing_b0(synthetic):
    p = synthetic
    with pytest.raises(ReplayInputError, match="not validated"):
        validate_replay_inputs(MemoryReadFixture(p, p.checkpoint), p.recipe)


def test_complete_typed_synthetic_closure_and_mock_dispatch(synthetic, monkeypatch):
    p = synthetic
    checkpoint, recipe = validated_fixture(p)
    store = MemoryReadFixture(p, checkpoint)
    calls = []

    def mock_step(state, **kwargs):
        calls.append((state, kwargs))
        return replace(state, time_s=state.time_s + kwargs["duration_s"]), None

    monkeypatch.setattr(adapter.kernel, "pure_shear_thermal_step", mock_step)
    result = execute_replay(store, recipe, adapter.DeterministicKernelAdapter(p))
    assert result.status == "VERIFIED"  # mock/fixture contract only
    assert len(calls) == 2
    assert calls[0][0].payload() == thaw_json(p.initial.value)["side_states"][0]
    assert calls[0][1] == {"duration_s": 2.0,
                          "extension_velocity_m_s": p.forcing.value["signed_Ux_m_per_year"] / 31_557_600.0,
                          "maximum_kinematic_fraction_per_substep": 0.01}


def test_expected_values_are_not_read_or_returned(synthetic, monkeypatch):
    p = synthetic
    checkpoint, recipe = validated_fixture(p)
    inputs = validate_replay_inputs(MemoryReadFixture(p, checkpoint), recipe)
    class PoisonOracle:
        def __getattribute__(self, name):
            raise AssertionError("expected output entered computation")
    monkeypatch.setattr(adapter.kernel, "pure_shear_thermal_step",
                        lambda state, **kw: (replace(state, time_s=7.0), None))
    output = adapter.DeterministicKernelAdapter(replace(p, expected=PoisonOracle()))(
        recipe, replace(inputs, expected_state=PoisonOracle()))
    assert output.state != p.expected
    assert output.state.value["side_states"][0]["time_s"] == 7.0
    # B0 reports a mismatch when the independent mock output differs from oracle.
    result = execute_replay(MemoryReadFixture(p, checkpoint), recipe, adapter.DeterministicKernelAdapter(p))
    assert result.status == "MISMATCH"


@pytest.mark.parametrize("defect", ["forcing_missing", "forcing_altered", "support", "material", "source", "configuration", "recipe_scope"])
def test_invalid_bindings_fail_before_kernel(synthetic, monkeypatch, defect):
    p = synthetic
    checkpoint, recipe = validated_fixture(p)
    inputs = validate_replay_inputs(MemoryReadFixture(p, checkpoint), recipe)
    monkeypatch.setattr(adapter.kernel, "pure_shear_thermal_step",
                        lambda *a, **k: pytest.fail("invalid binding reached kernel"))
    if defect == "forcing_missing":
        inputs = replace(inputs, forcings=())
    elif defect == "forcing_altered":
        value = thaw_json(p.forcing.value); value["signed_Ux_m_per_year"] *= 2
        forcing = changed(p.forcing, "forcing_id", ForcingId, ForcingRecord.from_dict, value=value)
        inputs = replace(inputs, forcings=(forcing,))
    elif defect in {"support", "material"}:
        value = thaw_json(p.initial.value)
        if defect == "support": value["support_ids"][0] = "WRONG-SUPPORT"
        else: value["side_states"][0]["materials"][0]["cp_j_kg_k"] *= 2
        state = changed(p.initial, "state_id", DomainStateId, DomainStateEnvelope.from_dict, value=value)
        inputs = replace(inputs, base_states=(state,))
    elif defect == "source":
        p = replace(p, source_identity={**thaw_json(p.source_identity), "execution_commit": "b" * 40})
    elif defect == "configuration":
        config = thaw_json(p.configuration); config["historical_configuration"]["duration_seconds"] = 3.0
        p = replace(p, configuration=config)
    else:
        recipe = changed(recipe, "recipe_id", ReplayRecipeId, ReplayRecipe.from_dict,
                         branch_id=str(p.initial.history_id).replace("r6hist_", "r6branch_"))
    with pytest.raises(adapter.ReplayBindingError):
        adapter.DeterministicKernelAdapter(p)(recipe, inputs)


@pytest.mark.parametrize("value", [True, 0.0, -1.0, float("nan"), float("inf")])
def test_invalid_duration_is_rejected(synthetic, value):
    p = synthetic
    config = thaw_json(p.configuration)["historical_configuration"]
    config["duration_seconds"] = value
    with pytest.raises(adapter.ReplayBindingError):
        adapter._bind_candidate(p.initial, p.expected, p.forcing, p.original_checkpoint,
                                p.original_recipe, config, p.source_identity, {})


def test_incomplete_initial_payload_and_missing_provenance_fail_closed(synthetic):
    payload = thaw_json(synthetic.initial.value)["side_states"][0]
    del payload["materials"]
    with pytest.raises(adapter.ReplayBindingError, match="INITIAL_STATE_INVALID"):
        adapter._restore(payload)
    checkpoint, recipe = validated_fixture(synthetic)
    store = MemoryReadFixture(synthetic, checkpoint)
    store.provenance.clear()
    with pytest.raises(ReplayInputError, match="closure failed"):
        validate_replay_inputs(store, recipe)


@pytest.mark.parametrize("defect", ["coordinate_nan", "material_boolean", "time_boolean"])
def test_malformed_initial_numeric_properties_are_rejected(synthetic, defect):
    payload = thaw_json(synthetic.initial.value)["side_states"][0]
    if defect == "coordinate_nan": payload["material_coordinate"][1] = float("nan")
    elif defect == "material_boolean": payload["materials"][0]["radiogenic_w_m3"] = False
    else: payload["time_s"] = False
    with pytest.raises(adapter.ReplayBindingError):
        adapter._restore(payload)


def test_historical_source_and_runtime_identity_are_required(synthetic, monkeypatch):
    monkeypatch.setattr(adapter.subprocess, "run", lambda *a, **k: type("Failed", (), {"returncode": 1})())
    with pytest.raises(adapter.ReplayBindingError, match="HISTORICAL_KERNEL"):
        adapter.verify_kernel_source(ROOT)
    monkeypatch.setattr(adapter.platform, "python_version", lambda: "WRONG_RUNTIME")
    with pytest.raises(adapter.ReplayBindingError, match="RUNTIME_IDENTITY"):
        adapter.DeterministicKernelAdapter(synthetic)._verify_runtime()


def test_preparation_configuration_is_immutable_and_typed_roundtrips(synthetic):
    p = synthetic
    with pytest.raises(TypeError):
        p.configuration["support_ids"] = ["WRONG"]
    for record in p.records:
        assert type(record).from_dict(record.to_dict()) == record
    assert p.checkpoint.configuration_sha256 == content_hash(thaw_json(p.configuration))


def test_canonical_path_is_rejected_before_any_bundle_read(monkeypatch):
    monkeypatch.setattr(adapter, "load_verified_bundle",
                        lambda *a, **k: pytest.fail("canonical path reached file reader"))
    with pytest.raises(adapter.ReplayBindingError, match="CANONICAL_PATH_FORBIDDEN"):
        adapter.prepare_r4(ROOT, ROOT / "WORLD_HISTORY" / R4.name)


def test_missing_typed_dependency_is_rejected_by_b0(synthetic):
    checkpoint, recipe = validated_fixture(synthetic)
    deps = (*recipe.upstream_dependency_ids, "missing-record")
    checkpoint = changed(checkpoint, "checkpoint_id", CheckpointId,
                         CheckpointEnvelope.from_dict, upstream_dependency_ids=list(deps))
    recipe = changed(recipe, "recipe_id", ReplayRecipeId, ReplayRecipe.from_dict,
                     base_checkpoint_id=str(checkpoint.checkpoint_id), upstream_dependency_ids=list(deps))
    with pytest.raises(ReplayInputError, match="unresolved dependency"):
        validate_replay_inputs(MemoryReadFixture(synthetic, checkpoint), recipe)
