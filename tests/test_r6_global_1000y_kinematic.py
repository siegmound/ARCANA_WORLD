"""Phase 2 pure-kernel and Phase-1 evidence-reuse guards. No global run."""
import numpy as np
import pytest
from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    BenchmarkError, STATUS as STATUS100, SCHEMA as SCHEMA100,
    PLATES, NODES, TRIANGLES, IDENTITY_TOL, AREA_TOL_SR,
    unit_xyz, rotate_xyz, save_checkpoint,
)
from experiments.global_t0_kinematic_baseline_v1.phase2_1000y import (
    PHASE1_COMMIT, validate_phase1_report, load_prior_checkpoint, replay,
    YEARS, CHECKPOINT_YEARS,
)


def sample_report():
    return {
        "status":STATUS100,"schema":SCHEMA100,
        "code_source_commit":PHASE1_COMMIT,
        "source_sha256":{"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat":"abc"},
        "source_mesh_identity_sha256":"mesh",
        "model_years":100,"first_event_horizon_model_years":27123.,
        "grid":{"nodes":NODES,"triangles":TRIANGLES,"plates":12},
        "passive_PRE":{"mode":"T0_SOURCE_ONLY_NO_THERMAL_EVOLUTION",
                       "data_sha256":"abc"},
        "solver_runs":0,"physical_deforming_T1":None,
        "numerical_acceptance":{
            "max_xyz_drift_unit":5e-15,"max_radial_norm_error":5e-15,
            "max_triangle_area_change_sr":7e-17,
            "restart_50_plus_50_xyz_error":0.,
            "numerical_tolerance_unit":IDENTITY_TOL,
            "triangle_area_tolerance_sr":AREA_TOL_SR,
            "all_milestones_accepted":True},
        "milestones":{str(i):{"inverted_triangles":0} for i in (0,1,10,50,100)},
        "checkpoints":[{"file":f"KINEMATIC_{y:03d}.npz"} for y in (0,50,100)],
    }


def test_phase1_report_reference_accepts_only_proven_same_source():
    report=sample_report()
    validate_phase1_report(report,report["source_sha256"],"mesh",27123.)


@pytest.mark.parametrize("key,value",[
    ("source_mesh_identity_sha256","altered"),
    ("code_source_commit","other"),
    ("model_years",1000),
    ("physical_deforming_T1",{"unauthorized":True}),
])
def test_wrong_phase1_source_or_authority_fails_closed(key,value):
    report=sample_report()
    report[key]=value
    with pytest.raises(BenchmarkError,match="PHASE1_REPORT"):
        validate_phase1_report(report,
                               {"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat":"abc"},
                               "mesh",27123.)


def test_phase1_numeric_failure_not_promoted():
    report=sample_report()
    report["numerical_acceptance"]["max_xyz_drift_unit"]=1e-3
    with pytest.raises(BenchmarkError,match="PHASE1_NUMERICAL"):
        validate_phase1_report(report,report["source_sha256"],"mesh",27123.)


def test_year100_exact_prefix_and_restart500_preserve_state():
    x=unit_xyz([[10,-20],[30,60]])
    w={p:[(p+1)*1e-8,0,0] for p in PLATES}
    continuous={p:x.copy() for p in PLATES}
    for _ in range(100):
        replay(continuous,w,1)
    prefix={p:continuous[p].copy() for p in PLATES}
    for _ in range(400):
        replay(continuous,w,1)
    at500={p:continuous[p].copy() for p in PLATES}
    for _ in range(500):
        replay(continuous,w,1)
    resumed=replay(at500,w,500)
    assert all(np.array_equal(resumed[p],continuous[p]) for p in PLATES)
    assert all(np.max(np.abs(prefix[p]-rotate_xyz(x,w[p],100)))<1e-12 for p in PLATES)


def test_checkpoint_schema_and_ids_are_source_bound(tmp_path):
    x=unit_xyz([[5,6],[7,8]])
    views={p:{"ids":np.array([4,8]),"source_xyz":x} for p in PLATES}
    state={p:x.copy() for p in PLATES}
    save_checkpoint(tmp_path,100,views,state)
    got=load_prior_checkpoint(tmp_path/"KINEMATIC_100.npz",views,100)
    assert all(np.array_equal(got[p],state[p]) for p in PLATES)
    views[0]["ids"]=np.array([4,9])
    with pytest.raises(BenchmarkError,match="MATERIAL_IDS"):
        load_prior_checkpoint(tmp_path/"KINEMATIC_100.npz",views,100)


def test_phase2_scope_locked_to_1000_with_bounded_checkpoints():
    assert YEARS==1000
    assert CHECKPOINT_YEARS==(0,1,10,100,500,1000)
