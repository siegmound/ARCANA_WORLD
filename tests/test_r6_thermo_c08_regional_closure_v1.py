"""Focused offline checks. Develop against reads and in-memory reconstruction."""
from pathlib import Path
import shutil

import numpy as np
import pytest

from experiments.r6_thermo_provider_pilot_v1 import c08_constitutive as g2
from experiments.r6_thermo_provider_pilot_v1 import run_c08_regional_closure as c08

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def reports():
    return c08.build(ROOT)


def test_c07_receipt_and_all_payloads_replayed(reports):
    record = reports["C07_REPLAY.json"]
    assert len(record["inventory"]) == len(record["reconstructed_all_members"]) == 9
    assert record["operator_exit"] is None
    assert record["reported"]["regression_total"] == 719
    assert record["retained_library_state_count"] == 35
    assert record["retained_comparative_queries"] == 951


def test_c07_member_mutation_refused(tmp_path):
    folder = tmp_path/c08.c07.OUT.name
    shutil.copytree(c08.c07.OUT,folder)
    with (folder/"AUTHORIAL_DECISION_SHEET.json").open("a") as handle:
        handle.write(" ")
    with pytest.raises(ValueError, match="C08_C07_INVENTORY_SCOPE"):
        c08.verify_c07(folder)


def test_axial_to_invariant_and_native_factor():
    # Directly compare one SI stress/strain pair in each convention.
    n = 4.
    A = 1.1e-4
    delta_sigma_mpa = 50.
    axial = A*delta_sigma_mpa**n
    eps2 = np.sqrt(3)/2*axial
    s2 = delta_sigma_mpa*1e6/np.sqrt(3)
    assert g2.invariant_prefactor(A,n)*s2**n == pytest.approx(eps2)
    lr = {"aCreep_candidate_pa_s_to_e":2.,"bCreep_candidate_kelvin":0.,
          "cCreep_candidate_kelvin_per_m":0.,"eCreep_candidate":.25}
    assert g2.raw_native_stress(lr,.25,1.,3.,1200.,0.) == pytest.approx(2*3**.25)


def test_brittle_branches_are_continuous_and_pore_pressure_reduces_strength():
    p = np.array([0.,2e8,4e8])
    dry = g2.column.brittle_shear_pa(p,g2.friction_policy(0.))
    water = g2.column.brittle_shear_pa(p,g2.friction_policy(.5))
    assert dry == pytest.approx([0,170e6,290e6])
    assert water == pytest.approx([0,85e6,170e6])
    assert 50e6+.6*2e8 == .85*2e8


def test_unsupported_ductile_domain_refused():
    law = g2.law_mantle([1e-14,1e-12],14e-6)
    for t,p,rate in [(1300,2e9,1e-13),(1400,1e9,1e-13),(1400,2e9,1e-5)]:
        with pytest.raises(ValueError,match="G2_CREEP_SOURCE_VALIDITY_OUTSIDE_CALIBRATED_DOMAIN"):
            g2.column.flow_stress_pa(law,np.array([t]),np.array([p]),rate)


def test_integral_and_support_partition(reports):
    assert g2.integrate(np.array([1,2,4]),np.array([3,6,12])) == 22.5
    with pytest.raises(ValueError,match="C08_INTEGRAL_INPUT"):
        g2.integrate(np.array([1,1]),np.array([3,6]))
    d = reports["REGIONAL_PT_RATE_SUPPORT.json"]
    assert len(d["nodes"]) == 81 and d["BHQ_eligible_depth_interval_count"] == 0
    assert d["native_Moho_PT_projection"]["projected_moho_points"] == 896
    row = d["nodes"]["34581"]
    z0 = row["layers"]["mantle"]["depth_m"][0]
    intervals = row["dry_olivine_analogue_TP_intervals"]
    assert intervals[0][0] == z0 and all(a[1]==b[0] for a,b in zip(intervals,intervals[1:]))
    assert intervals[-1][1] == row["layers"]["mantle"]["depth_m"][-1]


def test_common_exponent_error_is_only_a_partial_analogue(reports):
    c = reports["NATIVE_COMMON_EXPONENT_COMPARISON.json"]
    errors = c["rates"]["300"]["max_abs_depth_fractional_error"]
    assert c["common_e_candidates"]["joint_slope_minimax"] == pytest.approx(15/56)
    assert errors["joint_slope_minimax"] == pytest.approx(.0308336396439)
    assert errors["mantle_slope"] < 2e-13
    assert c["empirical_fit"] is None and c["accepted_error_threshold"] is None
    s = reports["WHOLE_COLUMN_STRENGTH_CANDIDATES.json"]["nodes"]["34581"]
    assert s["crust_ductile_integral_N_m"] is None and s["total_lithosphere_integral_N_m"] is None
    a = s["mantle_partial"][0]["rate_cases"]["300"]
    assert a["native_form_comparison"]["joint_slope_minimax"]["relative_integrated_error"] == pytest.approx(
        errors["joint_slope_minimax"])


def test_shared_dof_conflict_and_gauge(reports):
    b = reports["REGIONAL_BOUNDARY_CONDITION_CANDIDATES.json"]
    ranks = reports["CONSTRAINT_RANK_AND_GAUGE_ANALYSIS.json"]
    assert [x["parent"] for x in b["north_south_shared_plate_junctions"]["north"]] == [37463]
    assert [x["parent"] for x in b["north_south_shared_plate_junctions"]["south"]] == [34587]
    assert len(b["distal_node_candidates"]) == 18
    assert len(b["contact_kinematic_priors"]) == 12
    for name,rank in [("full_distal_S_and_E",36),("normal_only_distal_hypothesis",18)]:
        d = ranks[name]
        assert d["rank"] == rank and d["unconstrained_dof"] == 162-rank
        assert d["remaining_rigid_rotation_modes"] == 0 and d["stiffness_rank"] is None
    bad = ranks["prohibited_dual_Euler_N_S_counterexample"]
    assert bad["constraint_rows"] == 44 and bad["rank"] == 40
    assert bad["max_rhs_consistency_residual_m_s"] > 2e-9
    for row in b["distal_node_candidates"].values():
        mag = row["magnitude_m_s"]
        angle = np.deg2rad(row["azimuth_clockwise_from_north_deg"])
        assert row["south_east_m_s"] == pytest.approx([-mag*np.cos(angle),mag*np.sin(angle)], abs=2e-22)


def test_missing_physical_support_and_publication_stays_false(reports,tmp_path):
    b = reports["REGIONAL_BOUNDARY_CONDITION_CANDIDATES.json"]
    assert all(r["external_traction_N_per_m"] is None for r in b["edges"])
    closure = reports["BASAL_SUPPORT_AND_FORCE_OWNERSHIP.json"]
    assert all(closure[k] is None for k in ("normal_support_Pa","mechanical_LAB_m","mantle_motion_m_s","basal_traction_Pa"))
    for report in reports.values():
        assert all(report[k]==v for k,v in c08.SCOPE.items())
    out = tmp_path/"scope"
    with pytest.raises(ValueError,match="C08_OUTPUT_SCOPE"):
        c08.write_once(out,{"bad.json":dict(c08.SCOPE,mechanical_solve_authorized=True)},c08.ENTRY)
    assert not out.exists()
    c08.write_once(out,{"test.json":c08.SCOPE},c08.ENTRY)
    with pytest.raises(ValueError,match="C08_OUTPUT_EXISTS"):
        c08.write_once(out,{"test.json":c08.SCOPE},c08.ENTRY)
