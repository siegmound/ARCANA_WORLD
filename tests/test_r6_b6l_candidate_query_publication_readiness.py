from __future__ import annotations

import pytest

from arcana_worldsim.r6.b6l_readiness import (CandidateSupportIndex,
    canonical_publication_plan, continuation_guard)
from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import BranchId, HistoryId, PayloadIdentity, canonical_bytes, content_hash
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.replay import ReplayExecutionOutput, ReplayRecipe, execute_replay
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
    SupportClass, TimeSupport)
from arcana_worldsim.r6.store import HistoryStore


def _index():
    # Pair row indexes are the same stable row references used by B6K boundary evidence.
    pairs = ((1, 10), (1, 20), (2, 10), (2, 20), (3, 10), (3, 20), (3, 30))
    interfaces = [{"boundary_id": "b12", "incident_plate_ids": [10, 20],
        "sides": [{"plate_id": 10, "coordinate_rows": [0, 2]},
                  {"plate_id": 20, "coordinate_rows": [1, 3]}]}]
    junctions = [{"junction_id": "j3", "canonical_node_id": 3,
        "incident_plate_ids": [10, 20, 30]}]
    return CandidateSupportIndex(candidate_id="candidate-fixture", pairs=pairs,
        interfaces=interfaces, junctions=junctions)


def test_canonical_node_resolves_every_plate_local_representation_without_owner():
    index = _index()
    rows = index.representations_for_source(3)
    assert [row["plate_support"] for row in rows] == [10, 20, 30]
    assert all(row["unique_owner"] is None and row["support_is_set_valued"] for row in rows)
    assert index.summary()["candidate_representation_count"] == 7


def test_candidate_representation_resolves_source_and_boundary_membership():
    index = _index()
    row = index.representations_for_source(1)[0]
    resolved = index.source_for_representation(row["representation_id"])
    assert resolved["source_canonical_node_id"] == 1
    assert resolved["plate_support"] == 10
    assert resolved["boundary_interface_ids"] == ["b12"]
    assert resolved["representation_lineage"]["source_canonical_node_id"] == 1
    assert resolved["representation_lineage"]["candidate_id"] == "candidate-fixture"


def test_junction_query_keeps_all_incident_plate_sides():
    index = _index()
    rows = index.representations_for_source(3)
    assert {row["junction_ids"][0] for row in rows} == {"j3"}
    assert {row["plate_support"] for row in rows} == {10, 20, 30}


def test_duplicate_representation_pair_fails_closed():
    with pytest.raises(ValueError, match="unique support pairs"):
        CandidateSupportIndex(candidate_id="candidate", pairs=((1, 2), (1, 2)),
            interfaces=(), junctions=())


def test_boundary_side_plate_mismatch_fails_closed():
    with pytest.raises(ValueError, match="mismatched plate"):
        CandidateSupportIndex(candidate_id="candidate", pairs=((1, 10),),
            interfaces=[{"boundary_id": "b", "incident_plate_ids": [10, 20],
                "sides": [{"plate_id": 20, "coordinate_rows": [0]},
                          {"plate_id": 10, "coordinate_rows": [0]}]}], junctions=())


def test_junction_requires_set_of_three_or_more_plates():
    with pytest.raises(ValueError, match=r"3\+ incident plates"):
        CandidateSupportIndex(candidate_id="candidate", pairs=((1, 10), (1, 20)),
            interfaces=(), junctions=[{"junction_id": "j", "canonical_node_id": 1,
                                       "incident_plate_ids": [10, 20]}])


def test_unknown_source_and_representation_queries_fail_closed():
    index = _index()
    with pytest.raises(KeyError, match="unknown canonical source"):
        index.representations_for_source(99)
    with pytest.raises(KeyError, match="unknown candidate representation"):
        index.source_for_representation("missing")


def test_continuation_is_blocked_at_untransitioned_event_boundary():
    assert continuation_guard(event_transition_status="NOT_EXECUTED",
        ordinary_step_requested=True) == "CONTINUATION_BLOCKED_PENDING_RIFT_TRANSITION"


def test_nonordinary_query_is_not_a_continuation_attempt():
    assert continuation_guard(event_transition_status="NOT_EXECUTED",
        ordinary_step_requested=False) == "CONTINUATION_ALLOWED"


def test_continuation_requires_transition_to_be_executed():
    assert continuation_guard(event_transition_status="EXECUTED",
        ordinary_step_requested=True) == "CONTINUATION_ALLOWED"


def test_publication_plan_is_deterministic_and_does_not_publish():
    kwargs = dict(candidate_id="c", candidate_state_id="s", payload_sha256="a" * 64,
        topology_identity="t", replay_recipe_id="r", dt_hex="0x1.0p+1", target_age_ma=1.0)
    left = canonical_publication_plan(**kwargs)
    right = canonical_publication_plan(**kwargs)
    assert left == right
    assert left["publication_executed"] is False
    assert left["payload_policy"] == "REFERENCE_OR_PROMOTE_EXISTING_CONTENT_ID; NO_COPY"
    assert {row["action"] for row in left["atomic_bundle_records"]} <= {
        "NEW_CANONICAL_RECORD", "REFERENCE_EXISTING_PAYLOAD",
        "PROMOTE_CANDIDATE_PAYLOAD_REFERENCE", "NO_ACTION_REQUIRED"}


def test_persisted_replay_recipe_reopens_and_reproduces_payload(tmp_path):
    history = str(HistoryId.from_payload({"b6l": "history"}))
    branch = str(BranchId.from_payload({"b6l": "branch"}))
    time = TimeSupport("fixture:t0", "B6L_FIXTURE")
    space = SpatialSupport("fixture-grid", ("node-1",), "fixture", "CELL_SET")
    provenance = ProvenanceRecord.create(activity="B6L_RECIPE_FIXTURE",
        source_refs=("fixture://input-closure",))
    base = DomainStateEnvelope.create(history_id=history, branch_id=branch,
        domain="fixture", time_support=time, spatial_support=space,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"n": 1}, provenance_ids=(str(provenance.record_id),))
    payload = canonical_bytes({"n": 2})
    payload_id = PayloadIdentity.from_bytes(payload)
    expected = DomainStateEnvelope.create(history_id=history, branch_id=branch,
        domain="fixture", time_support=TimeSupport("fixture:t1", "B6L_FIXTURE"),
        spatial_support=space, support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY, value={"n": 2},
        provenance_ids=(str(provenance.record_id),), parent_state_ids=(str(base.state_id),),
        payload_ref=f"sha256:{payload_id.digest}")
    runtime, config, seed = {"adapter": "fixture:b6l"}, {"dt_hex": "fixture"}, {"seed": 0}
    forcing = ForcingRecord.create(history_id=history, branch_id=branch,
        forcing_kind="B6L_FIXTURE_FORCING", domain="fixture", time_support=time,
        spatial_support=space, support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY, value={"increment": 1},
        provenance_ids=(str(provenance.record_id),))
    checkpoint = CheckpointEnvelope.create(history_id=history, branch_id=branch,
        time_key=time.time_key, restart_state_ids=(str(base.state_id),),
        retained_history_state_ids=(str(base.state_id),), runtime_identity=runtime,
        configuration=config, seed_lineage=seed,
        upstream_dependency_ids=(str(provenance.record_id),))
    recipe = ReplayRecipe.create(history_id=history, branch_id=branch,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=runtime,
        configuration_sha256=content_hash(config), seed_lineage=seed,
        forcing_ids=(str(forcing.forcing_id),), upstream_dependency_ids=(str(provenance.record_id),),
        provenance_ids=(str(provenance.record_id),), expected_output_state_id=str(expected.state_id),
        model_adapter_id="fixture:b6l-replay-v1", expected_payload_identity=payload_id)
    root = tmp_path / "b6l-replay-store"
    HistoryStore(root).append_transaction((provenance, base, expected, forcing, checkpoint, recipe))
    reopened = HistoryStore(root)
    loaded = reopened.read_replay_recipe(str(recipe.recipe_id))
    result = execute_replay(reopened, loaded,
        lambda _recipe, inputs: ReplayExecutionOutput(inputs.expected_state, payload))
    assert result.status == "VERIFIED"
    assert result.produced_state_id == str(expected.state_id)
    assert result.produced_payload_identity == payload_id


@pytest.mark.parametrize(("stage", "count"), [("before_publication", 0),
                                                ("after_publication", 1),
                                                ("before_commit", 2)])
def test_isolated_publication_transaction_rolls_back_then_retries(tmp_path, stage, count):
    history = str(HistoryId.from_payload({"b6l-tx": "history"}))
    branch = str(BranchId.from_payload({"b6l-tx": "branch"}))
    time = TimeSupport("fixture:t0", "B6L_FIXTURE")
    space = SpatialSupport("fixture-grid", ("cell",), "fixture", "CELL_SET")
    provenance = ProvenanceRecord.create(activity="B6L_TRANSACTION_FIXTURE",
        source_refs=("fixture://isolated-target",))
    state = DomainStateEnvelope.create(history_id=history, branch_id=branch,
        domain="fixture", time_support=time, spatial_support=space,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"candidate": True}, provenance_ids=(str(provenance.record_id),))
    root = tmp_path / "publication-target"
    def inject(found_stage, found_count):
        if (found_stage, found_count) == (stage, count):
            raise RuntimeError("B6L failure injection")
    with pytest.raises(RuntimeError, match="B6L failure injection"):
        HistoryStore(root, _fault_injector=inject).append_transaction((provenance, state))
    recovered = HistoryStore(root)
    assert recovered.states() == ()
    assert not (root / "provenance" / f"{provenance.record_id}.json").exists()
    HistoryStore(root).append_transaction((provenance, state))
    retried = HistoryStore(root)
    assert retried.states() == (state,)
    assert retried.read_provenance(str(provenance.record_id))["record_id"] == str(provenance.record_id)
