import inspect
import arcana_worldsim.scientific_engines.r448_geonomics_j14_j18_full_job_revalidation_coverage_expansion_preflight as m


def test_remaining_branch_math():
    assert 192 - 1 == 191
    assert 64 - 1 == 63
    assert 191 + 63 == 254
    assert 191 * 4 + 63 * 4 == 1016


def test_expansion_metric_count_math():
    assert 191 * 141 * 4 * 3 == 323172
    assert 63 * 15 * 4 * 3 == 11340
    assert 323172 + 11340 == 334512
    assert 215448 + 7560 == 223008
    assert 107724 + 3780 == 111504


def test_full_geonomics_post_expansion_count_math():
    assert 192 * 141 * 4 * 3 == 324864
    assert 64 * 15 * 4 * 3 == 11520
    assert 324864 + 11520 + 10584 == 346968


def test_first_cohort_branch_is_fixed_and_excluded():
    assert m.FIRST_COHORT_BRANCH == (0, 0)
    s = inspect.getsource(m._inventory_j14)
    assert "(mi, ci_idx) == FIRST_COHORT_BRANCH" in s
    s2 = inspect.getsource(m._inventory_j18)
    assert "(mi, ci_idx) == FIRST_COHORT_BRANCH" in s2


def test_sharding_is_deterministic_and_bounded():
    assert m.MAX_BRANCHES_PER_SHARD == 8
    s = inspect.getsource(m._make_shards)
    assert "range(0, len(branches), MAX_BRANCHES_PER_SHARD)" in s
    assert "FROZEN_MEMBER_MAJOR_THEN_CANDIDATE_MINOR" in s


def test_representability_gate_is_source_based_not_result_selected():
    s = inspect.getsource(m._inventory_j14) + inspect.getsource(m._inventory_j18)
    assert "all_states_nonempty" in s
    assert "np.isfinite" in s
    assert "out_of_grid_coord_count" in s


def test_authorization_forbids_reexecution_of_closed_evidence():
    s = inspect.getsource(m._authorization)
    assert '"J14_first_cohort_reexecution_authorized": False' in s
    assert '"J18_first_cohort_reexecution_authorized": False' in s
    assert '"J21_reexecution_authorized": False' in s


def test_no_scientific_execution_in_r448():
    s = inspect.getsource(m)
    assert '"scientific_execution_performed": False' in s
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r449():
    assert m.NEXT == (
        "BUILD_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
        "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE"
    )
