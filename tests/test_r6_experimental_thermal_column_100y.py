"""All pilot outputs remain noncanonical, even if a numeric benchmark passes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from arcana_worldsim.r6 import experimental_thermal_column as m

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"experiments/thermal_column_100y_v1/SYNTHETIC_OCEANIC_REFERENCE_COLUMN.json"


def config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def source_record():
    return {
        "parent_cell_id": "R6G1D-R089-C359",
        "source_plate_id": 8,
        "source_model_crust_domain_label": "NORMAL_OCEANIC",
        "source_authored_crustal_thickness_m": 6500.0,
        "reference_crust_density_nominal_kg_m3": 2890.0,
        "actual_local_bulk_density_kg_m3": None,
        "actual_mineral_phase_field": None,
        "actual_ore_resource_field": None,
        "actual_Deep_accessibility": None,
    }


def fake_original(root, cell_ids, *, field_package=None, plate_partition=None):
    assert cell_ids == ["R6G1D-R089-C359"]
    return {
        "selected_cell_count": 1,
        "native_cell_source_records": [source_record()],
        "source_field_package_sha256":
            "39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e",
        "source_vector_partition_sha256":
            "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
        "physical_T1": None,
        "history_store_writes": 0,
    }


def params():
    return {"rho_kg_m3": 2890.,
            "cp_j_kg_k": 1000.,
            "conductivity_w_m_k": 2.2,
            "volumetric_heat_production_w_m3": 3e-7}


def test_policy_sha_and_permanent_noncanonical_prohibition():
    p=m.governance(ROOT)
    assert p["rule"]=="EXPERIMENTAL_RUNS_ARE_ALWAYS_NONCANONICAL_AND_NEVER_AUTO_PROMOTE"
    assert p["canonical_world_history_write_authorized"] is False
    assert p["automatic_promotion_after_simulator_completion"] is False
    assert p["new_production_runs_required_after_ratification"] is True
    assert p["history_store_mutations_authorized"] is False
    assert p["physical_T1"] is None


def test_policy_rejects_modified_bytes_even_if_semantics_similar(tmp_path):
    dest=tmp_path/m.POLICY
    dest.parent.mkdir(parents=True)
    dest.write_bytes((ROOT/m.POLICY).read_bytes()+b"\n")
    with pytest.raises(m.ExperimentalColumnError,match="PINNED_SOURCE_DRIFT"):
        m.governance(tmp_path)


def test_source_thermal_reference_is_read_only_hypothetical_not_geology():
    p=m.reference_parameters(ROOT,source_record())
    assert p["rho_kg_m3"]==2890
    assert p["cp_j_kg_k"]==1000
    assert p["conductivity_w_m_k"]==2.2
    assert p["volumetric_heat_production_w_m3"]==3e-7
    assert p["provenance"]=="AUTHORIAL_SPECIALIST_REFERENCE_NOT_NATURAL_T0_MEASUREMENT"
    assert p["material_reference_source_blob"]==m.REF_BLOB


@pytest.mark.parametrize("field,value",[
    ("source_plate_id",1),
    ("source_model_crust_domain_label","NORMAL_CONTINENTAL"),
    ("source_authored_crustal_thickness_m", 5200.),
    ("reference_crust_density_nominal_kg_m3",2600.),
    ("actual_local_bulk_density_kg_m3",2890.),
    ("actual_mineral_phase_field",{"quartz":0.1}),
    ("actual_ore_resource_field",{"gold":0.01}),
    ("actual_Deep_accessibility",True),
])
def test_fake_source_geology_violates_pilot_authenticity(field,value):
    fake=source_record()
    fake[field]=value
    with pytest.raises(m.ExperimentalColumnError,match="T0_MODEL_ANCHOR_NOT_AS_EXPECTED|REFERENCE_DENSITY_NOT_SOURCE_BOUND"):
        m.reference_parameters(ROOT,fake)


def test_exact_synthetic_config_and_100y_only():
    c=m.validate_config(config())
    assert c["requested_duration_years"]==100
    assert c["authority"]==m.AUTHORITY
    assert c["source_parent_cell_id"]=="R6G1D-R089-C359"


@pytest.mark.parametrize("change,code",[
    ("make_canonical","EXPERIMENTAL_ONLY_AUTHORITY_REQUIRED"),
    ("add_canonical_flag","EXPERIMENTAL_CONFIG_FIELDS_INVALID"),
    ("1000_years","EXPERIMENTAL_100Y_ONLY_1000Y_NOT_YET_QUALIFIED"),
    ("float_100","EXPERIMENTAL_100Y_ONLY_1000Y_NOT_YET_QUALIFIED"),
    ("fake_other_cell","EXPERIMENTAL_SELECTED_SOURCE_CELL_NOT_QUALIFIED"),
    ("large_depth","EXPERIMENTAL_DEPTH_EXACT_SYNTHETIC_BENCHMARK_REQUIRED"),
    ("unqualified_temperature","EXPERIMENTAL_SYNTHETIC_INITIAL_PROFILE_REQUIRED"),
    ("negative_temp","EXPERIMENTAL_SYNTHETIC_INITIAL_PROFILE_REQUIRED"),
    ("fixed_surface_temperature","EXPERIMENTAL_BOUNDARY_CONDITIONS_NOT_QUALIFIED"),
    ("pretend_natural_properties","EXPERIMENTAL_REFERENCE_NOT_NATURAL_PROPERTIES_REQUIRED"),
    ("pretend_natural_heat","EXPERIMENTAL_REFERENCE_NOT_NATURAL_PROPERTIES_REQUIRED"),
    ("unknown_run","EXPERIMENTAL_RUN_ID_NOT_DECLARED"),
])
def test_illegal_canonical_historical_or_undeclared_configuration_rejected(change,code):
    c=config()
    if change=="make_canonical":c["authority"]="PHYSICAL_CANONICAL"
    if change=="add_canonical_flag":c["canonical_T1"]=True
    if change=="1000_years":c["requested_duration_years"]=1000
    if change=="float_100":c["requested_duration_years"]=100.0
    if change=="fake_other_cell":c["source_parent_cell_id"]="R6G1D-R089-C358"
    if change=="large_depth":c["synthetic_column_depth_m"]=7000
    if change=="unqualified_temperature":
        c["initial_temperature_k"]["authority"]="T0_NATURAL_PROFILE"
    if change=="negative_temp":c["initial_temperature_k"]["base_k"]=-20.0
    if change=="fixed_surface_temperature":
        c["adiabatic_boundary_conditions"]["top"]="FIXED_300K"
    if change=="pretend_natural_properties":
        c["material_property_mode"]="CELLWISE_MEASURED"
    if change=="pretend_natural_heat":
        c["heat_production_mode"]="NATURAL_210_MA_HEAT"
    if change=="unknown_run":
        c["experimental_run_label"]="fake_run"
    with pytest.raises(m.ExperimentalColumnError,match=code):
        m.validate_config(c)


@pytest.mark.parametrize("nx,step",m.LEVELS)
def test_conservative_fv_with_exact_synthetic_analytic_solution(nx,step):
    s=m.evolve_neumann_cosine(
        n_cells=nx, step_years=step,
        duration_years=100, depth_m=1000.,
        reference=params(),base_k=300.,amplitude_k=15.)
    assert s["diffusive_cfl"]>0
    assert s["diffusive_cfl"]<0.5
    assert s["energy_balance_pass"]
    assert abs(s["energy_balance_residual_j_m2"])<=s["energy_balance_tolerance_j_m2"]
    assert s["max_abs_error_against_synthetic_exact_k"]<0.001
    assert s["physical_historical_T1"] is None
    assert len(s["temperature_k_sampled_cell_centres"])==5


def test_three_levels_strict_error_decrease_and_determinism():
    kwargs={"duration_years":100,"depth_m":1000.,
            "reference":params(),"base_k":300.,
            "amplitude_k":15.}
    results=[m.evolve_neumann_cosine(n_cells=n,step_years=dt,**kwargs)
             for n,dt in m.LEVELS]
    errors=[x["max_abs_error_against_synthetic_exact_k"] for x in results]
    assert errors[2]<errors[1]<errors[0]
    assert errors[2]<0.001
    assert results==[m.evolve_neumann_cosine(
        n_cells=n,step_years=dt,**kwargs) for n,dt in m.LEVELS]


def test_cfl_fail_closed_without_unbounded_numeric_run():
    with pytest.raises(m.ExperimentalColumnError,match="EXPLICIT_DIFFUSION_UNSTABLE_CFL"):
        m.evolve_neumann_cosine(n_cells=200,step_years=3.,
                               duration_years=300,depth_m=1000.,
                               reference=params(),base_k=300.,amplitude_k=15.)


def test_non_divisible_time_grid_rejected():
    with pytest.raises(m.ExperimentalColumnError,match="DURATION_MUST_DIVIDE_TIME_STEP"):
        m.evolve_neumann_cosine(n_cells=50,step_years=3.,
                               duration_years=100,depth_m=1000.,
                               reference=params(),base_k=300.,amplitude_k=15.)


def test_source_anchored_run_is_always_synthetic(monkeypatch):
    monkeypatch.setattr(m,"extract_original_t0",fake_original)
    result=m.run(ROOT,config())
    assert result["decision"]==(
        "EXPERIMENTAL_NONCANONICAL_100Y_CONSERVATIVE_THERMAL_BENCHMARK_PASS")
    assert result["authority"]=="EXPERIMENTAL_NONCANONICAL_ONLY"
    assert result["source_plate_id"]==8
    assert result["source_model_crust_thickness_m"]==6500.
    assert result["source_field_sha256"]==fake_original(
        ROOT,["R6G1D-R089-C359"])["source_field_package_sha256"]
    assert result["synthetic_numerical_run_executed"]
    assert result["natural_ARCANA_T0_temperature_profile_qualified"] is False
    assert result["natural_ARCANA_T1_temperature_profile_created"] is False
    assert result["automatically_canonicalizable"] is False
    assert result["all_energy_balances_pass"]
    assert result["convergence_error_strictly_decreases"]
    assert result["history_store_mutations"]==0
    assert result["actual_mineral_or_ore_or_Deep_assignments"]==0
    assert result["physical_T1"] is None
    assert result["world_history_production_authorized"] is False


def test_mutated_source_adapter_to_fake_physical_T1_is_rejected(monkeypatch):
    fake=fake_original(ROOT,["R6G1D-R089-C359"])
    fake["physical_T1"]={"temperature_k":1000}
    monkeypatch.setattr(m,"extract_original_t0",lambda *a,**kw:fake)
    with pytest.raises(m.ExperimentalColumnError,match="SOURCE_ADAPTER_NOT_READ_ONLY"):
        m.run(ROOT,config())


def test_write_once_no_fake_canon_and_hash_manifest(tmp_path,monkeypatch):
    monkeypatch.setattr(m,"extract_original_t0",fake_original)
    result=m.run(ROOT,config())
    target=tmp_path/"experiment"
    m.write_once(target,result,repository_root=ROOT)
    manifest=json.loads((target/"MANIFEST.json").read_text())
    assert manifest["report_sha256"]==hashlib.sha256(
        (target/"REPORT.json").read_bytes()).hexdigest()
    assert manifest["authority"]==m.AUTHORITY
    assert manifest["physical_T1"] is None
    assert manifest["no_history_store_writes"] is True
    with pytest.raises(m.ExperimentalColumnError,match="EVIDENCE_ALREADY_EXISTS"):
        m.write_once(target,result,repository_root=ROOT)

def test_evidence_cannot_write_inside_canonical_or_source_repository():
    with pytest.raises(m.ExperimentalColumnError,match="EVIDENCE_MUST_BE_OUTSIDE_REPOSITORY"):
        m.write_once(
            ROOT/"PROJECT_LEDGER"/"R6_EXPERIMENTAL_NOT_ALLOWED",
            {"physical_T1":None},repository_root=ROOT)
