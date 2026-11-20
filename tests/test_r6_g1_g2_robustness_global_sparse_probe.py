"""Source-free unit tests; do not mislabel sparse graph as G2 physics."""
import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.g1_g2_robustness_global_sparse_probe import (
    BASE, SCENARIOS, compare_regional, scenario_parameters,
    sparse_graph_operator, subyear_exact_check, execute,
)


def test_manifested_parameter_scenarios_and_positive_ranges():
    assert len(SCENARIOS)==8
    for item in SCENARIOS.values():
        p=scenario_parameters(item)
        assert set(p)==set(BASE)
        assert all(v>0 for v in p.values())


def test_invalid_parameter_name_and_sign_rejected():
    with pytest.raises(ValueError,match="UNKNOWN_PARAMETER"):
        scenario_parameters({"NUCLEAR_BASAL_FIELD":42})
    with pytest.raises(ValueError,match="INVALID_PARAMETER"):
        scenario_parameters({"TAU_YEARS":-1})


def test_uniform_viscosity_scale_is_not_independently_identifiable():
    uniform=scenario_parameters(SCENARIOS["uniform_viscosity_x10"])
    assert uniform["ETA_CRUST_PA_S"]/BASE["ETA_CRUST_PA_S"]==10
    assert uniform["ETA_MANTLE_PA_S"]/BASE["ETA_MANTLE_PA_S"]==10
    assert uniform["TAU_YEARS"]==BASE["TAU_YEARS"]


def test_exact_subyear_backward_euler_first_order():
    result=subyear_exact_check()
    assert result["independent_constant_drive_analytical_reference"]
    assert .9<result["estimated_order_1_to_half"]<1.1
    assert .9<result["estimated_order_half_to_quarter"]<1.1
    errors=result["errors_m_by_dt_years"]
    assert errors["0.25"]<errors["0.5"]<errors["1.0"]


def small_summary(v):
    return {
        "scales":[{"extent":width,"source_nodes":(width+1)**2,
                   "source_triangles":2*width*width,
                   "results":{h:{
                     "max_displacement_m":v,
                     "coupled_minus_g1_velocity_rms_m_per_year":.01,
                     "manufactured_internal_force_balance_relative":1e-13,
                     "area_and_mass":{"max_absolute_area_ratio_minus_one":.001}
                   } for h in ("100","1000")}}
                  for width in (8,16)]
    }


def test_compare_regional_nontrivial_sweep_and_uniform_constraint():
    outcomes={
        "baseline":small_summary(100.),
        "uniform_viscosity_x10":small_summary(100.+1e-10),
        "relaxation_half":small_summary(110.),
    }
    result=compare_regional(outcomes["baseline"],outcomes)
    assert result["uniform_scale_nonidentifiability_confirmed"]
    assert result["experiments"]["relaxation_half"]["8"]["1000"]["delta_max_displacement_vs_baseline_m"]==10.


def test_compare_rejects_uniform_scale_numerical_inconsistency():
    outcomes={
        "baseline":small_summary(100.),
        "uniform_viscosity_x10":small_summary(102.),
    }
    with pytest.raises(ValueError,match="UNIFORM_VISCOSITY_SCALE_NONINVARIANCE"):
        compare_regional(outcomes["baseline"],outcomes)


def fake_views():
    # Different plate-local node copies may have the same original parent IDs.
    return {
        5:{"ids":np.array([0,1,2]),"triangles":np.array([[0,1,2]])},
        8:{"ids":np.array([0,1,3]),"triangles":np.array([[0,1,2]])},
    }


def test_plate_local_global_graph_preserves_contacts():
    lap,count=sparse_graph_operator(fake_views(),2)
    assert lap.shape==(6,6)
    assert count==2
    assert lap[:3,3:].nnz==0 and lap[3:,:3].nnz==0
    assert np.max(np.abs(lap@np.ones(6)))<1e-12


def test_global_graph_rejects_missing_triangle():
    with pytest.raises(ValueError,match="TRIANGLE_COVERAGE_FAILED"):
        sparse_graph_operator(fake_views(),3)


def test_execution_rejects_missing_evidence_before_any_write(tmp_path):
    target=tmp_path/"new"
    with pytest.raises(ValueError,match="SOURCE_EVIDENCE_DIR_MISSING"):
        execute(tmp_path/"missing1",tmp_path/"missing2",
                tmp_path/"missing3",target,tmp_path)
    assert not target.exists()
