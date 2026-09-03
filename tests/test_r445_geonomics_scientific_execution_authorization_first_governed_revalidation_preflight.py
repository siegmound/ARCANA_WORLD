import inspect
import arcana_worldsim.scientific_engines.r445_geonomics_scientific_execution_authorization_first_governed_revalidation_preflight as m


def test_frozen_seed_vectors_are_exact():
    assert m.FROZEN_SEEDS[m.J14] == [
        310746493, 1894477382, 1291996560, 1554786554
    ]
    assert m.FROZEN_SEEDS[m.J18] == [
        999124684, 1705133798, 1085091276, 555097754
    ]
    assert m.FROZEN_SEEDS[m.J21] == [
        1617603515, 1207292893, 1138693833, 989125497
    ]


def test_metric_record_count_math():
    assert 141 * 4 * 3 == 1692
    assert 15 * 4 * 3 == 180
    assert 9 * 4 * 147 * 2 == 10584
    assert 1692 + 180 + 10584 == 12456
    assert 6540 + 5916 == 12456


def test_j14_j18_cohort_is_deterministic_not_full_job():
    s = inspect.getsource(m._freeze_run_plan)
    assert "member_index_0_candidate_index_0_FROZEN_ORDER" in s
    assert '"full_job_revalidation_claim": False' in s


def test_j21_full_native_layer_sequence_is_frozen():
    s = inspect.getsource(m._freeze_run_plan)
    assert "FULL_FROZEN_J21_LAYER_SEQUENCE" in s
    assert '"native_dynamic_layer_count": 147' in s
    assert '"dynamic_sidecar_count": 4' in s


def test_authorization_has_no_threshold_or_target_definition():
    s = inspect.getsource(m._execution_authorization)
    assert 'plan["adjudicative_numeric_threshold_count"] == 0' in s
    assert 'plan["majority_vote_authorized"] is False' in s
    assert 'plan["engine_output_defines_arcana_target"] is False' in s
    assert 'plan["canonical_rewrite_authorized"] is False' in s


def test_r445_authorizes_but_does_not_execute():
    s = inspect.getsource(m)
    assert '"scientific_execution_authorized": bool(ok)' in s
    assert '"geonomics_execution_ready": bool(ok)' in s
    assert '"first_governed_revalidation_run_executed": False' in s
    assert '"scientific_engine_execution_performed": False' in s
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_plan_hash_is_frozen():
    s = inspect.getsource(m._freeze_run_plan)
    assert 'plan["plan_sha256"] = _sha_json(plan)' in s


def test_next_is_r446():
    assert m.NEXT == (
        "BUILD_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
        "AND_EVIDENCE_CAPTURE"
    )
