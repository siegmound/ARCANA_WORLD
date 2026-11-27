"""Focused checks for C09 offline physical hypotheses and source staging."""
from pathlib import Path
import math
import shutil

import numpy as np
import pytest

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.r6_thermo_provider_pilot_v1 import c09_column_scenarios as g2
from experiments.r6_thermo_provider_pilot_v1 import c09_mechanical_case as g3
from experiments.r6_thermo_provider_pilot_v1 import run_c09_physical_scenario as c09
from experiments.shellset_regional_explore_v1.solution_mapping import bind_solution

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def result():
    return c09.build(ROOT)


def test_c08_exact_replay_and_reported_scope(result):
    reports,_ = result
    replay = reports["C08_REPLAY.json"]
    assert set(replay["replayed_members"]) == set(replay["verified_members"]) == c09.MEMBERS
    assert replay["operator_report"]["reported_test_seconds"] == 6.88
    assert replay["operator_report"]["exit"] is None
    assert [replay[k] for k in ("retained_material_states","retained_source_chemistries",
                                "retained_query_identities")] == [35,14,951]


def test_c08_member_mutation_refused(tmp_path):
    archive = tmp_path/c09.c08.OUT.name
    shutil.copytree(c09.c08.OUT,archive)
    with (archive/"AUTHORIAL_PHYSICAL_DECISION_SHEET.json").open("a") as handle:
        handle.write(" ")
    with pytest.raises(ValueError,match="C09_C08_INVENTORY"):
        c09.verify_c08(archive)


def test_pressure_with_one_exact_thermal_correction():
    pre = {"crust_density_kg_m3":2.,"mantle_density_kg_m3":3.}
    for layer,a,b,t in ((1,0.,2.,100.),(2,2.,3.,200.)):
        k = f"layer{layer}_"
        pre |= {k+"z0_m":a,k+"z1_m":b,k+"c0_k":t,k+"c1_k_m":0.,
                k+"c2_k_m2":0.,k+"c3_k_m3":0.}
    z = np.asarray([0.,1.,2.,3.])
    assert g2.pressure(pre,z,10.,{"crust":.001,"mantle":.001}) == pytest.approx([0,18,36,60])


def test_exact_composite_and_creep_pivot():
    d = np.array([17.,40.])
    f = np.array([68.,2.])
    s = g2.composite_stress(d,f,3.5)
    assert np.all(s < np.minimum(d,f))
    assert (s/d)**3.5+s/f == pytest.approx([1.,1.],abs=3e-12)
    m = g2.model_catalog(ROOT,c09.sha)["native_diorite2"]
    pivot=1e-14
    inputs=(m,0,np.array([1000.]),np.array([980.]),np.array([1e8]),pivot)
    raw,brittle,cap = g2.native_components(*inputs,m["eCreep"],pivot)
    change,_,_ = g2.native_components(*inputs,g2.COMMON_E,pivot)
    assert change == pytest.approx(raw,rel=2e-15)
    assert brittle[0] == pytest.approx(math.sin(math.atan(.85))*1e8) and cap == 5e8


def test_strength_mechanisms_and_hydrostatic_sensitivity(result):
    reports,_ = result
    report = reports["WHOLE_COLUMN_SCENARIO_COMPARISON.json"]
    assert report["conditional_synthetic_columns"] == 81
    assert report["empirically_validated_ARCANA_columns"] == 0
    dry = report["by_parent"]["100km_dry"]
    wet = report["by_parent"]["100km_hydrostatic"]
    assert len(dry)==len(wet)==81
    for parent,v in dry.items():
        for name,case in v.items():
            assert 0 < wet[parent][name]["total_N_m"] <= case["total_N_m"]
            assert len(case["curves"]) == (3 if name=="layered_two_crust" else 2)
            for segment in case["curves"]:
                assert sum(segment["mechanism_samples"].values())==257
                assert np.all(np.isfinite(segment["effective_viscosity_Pa_s"]))
    scenario = report["results"]["100km_hydrostatic"]["native_diorite2"]
    assert scenario["total_N_m"]["min"] == pytest.approx(2.23067836458979e12)
    assert scenario["max_128_vs_256"] == pytest.approx(0.00012457736391949)


def test_regional_package_parent_mapping_and_no_implicit_bc(result):
    reports,files = result
    case = reports["CANDIDATE_NATIVE_INPUT_PACKAGE.json"]
    pre = files["regional_PRE.dat"].splitlines()
    assert len(pre)==82 and pre[-1].split()[0]=="81"
    assert "mixed_count /= 13" in files["MOD_ArcanaRuntime.regional.f90"]
    mesh = parse_feg(files["regional.feg"],mode="SHELLS_READY")
    assert len(mesh.nodes)==81 and len(mesh.elements)==128 and not mesh.faults
    bc = case["BC_records_in_perimeter_order"]
    assert len(bc)==32 and sum(row["native_bc_candidate"] is None for row in bc)==14
    assert all(row["external_traction_N_per_m"] is None for row in bc)
    mapping = case["G4_mapping"]
    # Existing G4 mapper under zero synthetic velocity and sentinel EDot.
    m = bind_solution(mapping,{i:[0.,0.] for i in range(1,82)},
                      {i:[[i,-1.,2.]]*7 for i in range(1,129)})
    assert len(m["canonical_xyz_m_s_by_parent_node"])==81
    assert all(trace["horizontal_trace_s_inv"]==[row["local_id"]-1.]*7
               for row in mapping["elements"]
               for trace in [m["strain_rate_by_parent_element"][row["parent_id"]]])


def test_global_closed_mesh_and_d12_distinction(result):
    reports,_ = result
    r = reports["REGIONAL_GLOBAL_ROUTE_COMPARISON.json"]["global"]
    assert r["node_count"]-r["undirected_edges"]+r["triangle_count"]==2
    assert r["outer_cut_edges"]==r["explicit_native_faults"]==0
    assert r["known_PRE_profiles"]==64442 and r["D12_unadmitted_cells"]==1180
    assert r["native_tangent_DOF"]==128884
    assert r["bandwidth_receipt"]["conditional_matrix_bytes"]==2249799104
    assert r["bandwidth_receipt"]["solver_measured_wall_s"] is None


def test_pending_time_and_no_authority_promotion(result, tmp_path):
    reports,files = result
    case = reports["CANDIDATE_NATIVE_INPUT_PACKAGE.json"]
    t = case["time"]
    assert t["candidate_trial_year"]==1. and t["same_start_halving_year"]==.5
    assert t["candidate_trial_year"]<t["opening_based_provisional_bound_year"]
    assert t["accepted_deformation_step_year"] is None
    assert all(value is None for value in case["required_input_values"].values())
    assert case["status"]=="NOT_EXECUTABLE"
    assert all(all(r[k]==v for k,v in c09.SCOPE.items()) for r in reports.values())
    assert g3.time_plan(100e3,1e-8,.1,.5)["candidate_trial_year"]==.25
    out=tmp_path/"test"
    with pytest.raises(ValueError,match="C09_OUTPUT_SCOPE"):
        c09.write_once(out,{"CANDIDATE_NATIVE_INPUT_PACKAGE.json":
                            dict(case,mechanical_solve_authorized=True)},files,c09.ENTRY)
    assert not out.exists()
    c09.write_once(out,{"CANDIDATE_NATIVE_INPUT_PACKAGE.json":case},files,c09.ENTRY,development=True)
    with pytest.raises(ValueError,match="C09_OUTPUT_EXISTS"):
        c09.write_once(out,{"CANDIDATE_NATIVE_INPUT_PACKAGE.json":case},files,c09.ENTRY)
