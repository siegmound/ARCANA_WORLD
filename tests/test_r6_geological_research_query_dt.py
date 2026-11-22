"""No synthetic geological survey is permitted to become canonical T0/T1."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from arcana_worldsim.r6 import geological_research_query as g
from arcana_worldsim.r6.geological_coarse_state import GeologicalContractError

ROOT = Path(__file__).resolve().parents[1]
OCEAN = "R6G1D-R089-C359"
OTHER = "R6G1D-R089-C358"


def query(*, cells=None, factor=None, sample=None, candidates=None, age=210.):
    return {
       "schema": g.QUERY_SCHEMA,
       "at_ma": age,
       "research_question": "sparse_native_t0_research",
       "parent_cell_ids": [OCEAN] if cells is None else cells,
       "sample": sample,
       "candidate_materials": [] if candidates is None else candidates,
       "subdivision_factor": factor,
    }


def sample(low=2800., high=2950., authority="SYNTHETIC_RESEARCH_SAMPLE"):
    return {
       "authority": authority, "source_ref": "synthetic_measurement_001",
       "density_interval": {"unit": "kg/m3", "low": low, "high": high}
    }


def candidate(cid="mafic_001",low=2700.,high=3000.):
    return {
       "candidate_id": cid,
       "material_family": "MAFIC_CRUST_CANDIDATE",
       "hypothetical_density_range":
          {"unit":"kg/m3","low":low,"high":high},
       "authority": "DECLARED_UNCALIBRATED_REFERENCE_INTERVAL",
    }


def fake_native_extract(root, ids, *, field_package=None,
                        plate_partition=None, refinement_query=None):
    # Authentication belongs exclusively to the genuine source adapter,
    # which has its own FAIR-tested SHA256 and plate mapping tests.
    from arcana_worldsim.r6.geological_coarse_state import (
        empty_catalog, validate_catalog, make_refinement_plan)
    source = {
       "original_grid_id": "R6_GLOBAL_GEOGRAPHY_1DEG_V1",
       "source_field_package_sha256": "39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e",
       "source_vector_partition_sha256": "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
       "source_document_git_blobs": {"fixture": "NOT_AN_ACTUAL_HASH"},
       "selected_cell_count": len(ids),
       "native_cell_source_records": [
           {"parent_cell_id": name, "source_plate_id": 8,
            "source_model_crust_domain_id": 1,
            "source_authored_crustal_thickness_m": 6500.,
            "reference_crust_density_nominal_kg_m3": 2890.,
            "density_authority": "AUTHORED_REFERENCE_MODEL_NOT_LOCAL_ROCK_MEASUREMENT",
            "actual_local_bulk_density_kg_m3": None,
            "actual_mineral_phase_field": None,
            "actual_ore_resource_field": None,
            "actual_Deep_accessibility": None}
           for name in ids
       ],
    }
    if refinement_query is not None:
        status=validate_catalog(empty_catalog(ROOT),ROOT)
        source["read_only_geometric_refinement"]=make_refinement_plan(
            status,refinement_query)
    return source


def test_real_pinned_dt_matrix_reports_no_go_for_100_and_1000_years():
    report=g.dt_feasibility(ROOT)
    assert report["decision"]=="NO_GO_PHYSICAL_T0_TO_T1_FOR_100_OR_1000_YEARS"
    assert report["source_authority_matrix_git_blob"]==g.DT_SOURCE_BLOB
    assert report["physical_T1"] is None
    assert not report["world_history_production_authorized"]
    assert not report["mechanical_solve_authorized"]
    assert report["history_store_writes"]==0
    assert len(report["blocking_gates"])>=4
    assert {x["gate"] for x in report["blocking_gates"]}>={
        "T0_THERMAL_STATE","T0_TO_T1_EVOLUTION","T1_THERMAL_STATE"}
    horizons=report["horizons"]
    assert [x["requested_delta_t_years"] for x in horizons]==[100,1000]
    assert [x["elapsed_seconds_if_julian_year"] for x in horizons]==[
        3155760000,31557600000]
    assert horizons[0]["arithmetic_target_ma_only_not_a_physical_state"]==209.9999
    assert horizons[1]["arithmetic_target_ma_only_not_a_physical_state"]==209.999
    assert all(x["physical_T1"] is None and
               x["physical_simulation_executed"] is False and
               x["go"] is False for x in horizons)


def test_dt_gate_can_select_one_horizon_but_not_authorize():
    report=g.dt_feasibility(ROOT,(100,))
    assert len(report["horizons"])==1
    assert report["horizons"][0]["requested_delta_t_years"]==100
    assert report["decision"].startswith("NO_GO")


@pytest.mark.parametrize("bad",[
    (1,), (100,100), (True,), (1000,100,100), [100], (),
])
def test_dt_gate_rejects_unsupported_horizon_lists(bad):
    with pytest.raises(g.ResearchQueryError,match="DT_ONLY_DECLARED"):
        g.dt_feasibility(ROOT,bad)


def test_dt_gate_source_byte_drift_cannot_be_hidden(tmp_path):
    source=tmp_path/g.DT_SOURCE_PATH
    source.parent.mkdir(parents=True)
    source.write_bytes((ROOT/g.DT_SOURCE_PATH).read_bytes()+b" ")
    with pytest.raises(g.ResearchQueryError,match="DT_AUTHORITY_SOURCE_DRIFT"):
        g.dt_feasibility(tmp_path)


def test_empty_t0_sample_query_is_not_a_density_observation(monkeypatch):
    monkeypatch.setattr(g,"extract",fake_native_extract)
    out=g.research(ROOT,query())
    assert out["density_screening"]["status"]=="NOT_REQUESTED"
    assert out["sample"] is None
    assert out["selected_cell_count"]==1
    assert out["source_cells"][0]["source_plate_id"]==8
    assert out["source_cells"][0]["reference_crust_density_nominal_kg_m3"]==2890
    assert out["source_cells"][0]["actual_local_bulk_density_kg_m3"] is None
    assert out["actual_natural_material_identification"] is None
    assert out["actual_ore_presence"] is None
    assert out["actual_Deep_accessibility"] is None
    assert out["history_store_writes"]==0 and out["physical_T1"] is None


def test_hypothetical_sample_density_overlap_is_not_an_observation(monkeypatch):
    monkeypatch.setattr(g,"extract",fake_native_extract)
    out=g.research(ROOT,query(sample=sample(),
        candidates=[candidate(),candidate("nonoverlap_001",900.,1300.)]))
    screen=out["density_screening"]
    assert screen["status"]=="INTERVAL_OVERLAP_ONLY_NOT_IDENTIFICATION"
    assert [x["overlap_under_declared_intervals"]
            for x in screen["conditional_candidates"]]==[True,False]
    assert all(x["posterior_probability"] is None
               for x in screen["conditional_candidates"])
    assert out["sample"]["verified_natural_observation"] is False
    assert out["sample_is_not_a_model_source_fact"]
    assert out["model_reference_density_is_not_local_measurement"]
    assert not out["density_screening_produces_posteriors"]


def test_user_reported_sample_is_unverified_not_adopted_into_t0(monkeypatch):
    monkeypatch.setattr(g,"extract",fake_native_extract)
    out=g.research(ROOT,query(
      sample=sample(authority="USER_REPORTED_UNVERIFIED_SAMPLE")))
    assert out["sample"]["authority"]=="USER_REPORTED_UNVERIFIED_SAMPLE"
    assert out["sample"]["verified_natural_observation"] is False
    assert out["density_screening"]["status"]=="INSUFFICIENT_CALIBRATED_PRIORS"
    assert out["source_cells"][0]["actual_local_bulk_density_kg_m3"] is None


def test_deterministic_parent_cell_selection_reuses_source_refinement(monkeypatch):
    monkeypatch.setattr(g,"extract",fake_native_extract)
    first=g.research(ROOT,query(cells=[OCEAN,OTHER],factor=2))
    second=g.research(ROOT,query(cells=[OTHER,OCEAN],factor=2))
    assert first==second
    assert first["selected_cell_count"]==2
    assert first["refinement"]["child_geometry_count"]==8
    assert first["refinement"]["research_epoch_ma"]==210
    assert first["source_query_identity_sha256"]==second["source_query_identity_sha256"]
    assert all(x["scientific_values_created"] is False
               and x["material_family"] is None
               and x["bulk_density_kg_m3"] is None
               for x in first["refinement"]["children"])
    assert first["refinement"]["physical_T1"] is None


@pytest.mark.parametrize("modification,err",[
 ("non_t0","NON_T0_EPOCH_UNAVAILABLE"),
 ("future_time","NON_T0_EPOCH_UNAVAILABLE"),
 ("wrong_epoch_type","NON_T0_EPOCH_UNAVAILABLE"),
 ("zero_parents","QUERY_INVALID_PARENT_SELECTION"),
 ("duplicate_parent","QUERY_INVALID_PARENT_SELECTION"),
 ("too_many","EXCEEDS_SPARSE_NATIVE_CELL_BUDGET"),
 ("bad_question","QUESTION_ID_INVALID"),
 ("bad_schema","SCHEMA_NOT_SUPPORTED"),
 ("bad_factor","REFINEMENT_BUDGET_INVALID"),
 ("bool_factor","REFINEMENT_BUDGET_INVALID"),
 ("large_geometry","REFINEMENT_BUDGET_INVALID"),
 ("sample_auth_claim","SAMPLE_CANNOT_CLAIM_AUTHENTICATED_OBSERVATION"),
 ("sample_dens_missing","RESEARCH_SAMPLE_DENSITY_REQUIRED"),
 ("sample_bad_units","MEASUREMENT_INTERVAL_UNIT_OR_FIELDS_INVALID"),
 ("candidate_no_sample","DENSITY_CANDIDATES_WITHOUT_SAMPLE"),
])
def test_bad_or_unqualified_query_rejected(modification,err):
    q=query()
    if modification=="non_t0":q["at_ma"]=209.9999
    if modification=="future_time":q["at_ma"]=210.001
    if modification=="wrong_epoch_type":q["at_ma"]="210"
    if modification=="zero_parents":q["parent_cell_ids"]=[]
    if modification=="duplicate_parent":q["parent_cell_ids"]=[OCEAN,OCEAN]
    if modification=="too_many":
        q["parent_cell_ids"]=[f"R6G1D-R089-C{i:03d}" for i in range(9)]
    if modification=="bad_question":q["research_question"]=""
    if modification=="bad_schema":q["schema"]="WRONG"
    if modification=="bad_factor":q["subdivision_factor"]=1
    if modification=="bool_factor":q["subdivision_factor"]=True
    if modification=="large_geometry":
        q["subdivision_factor"]=8
        q["parent_cell_ids"]=[f"R6G1D-R089-C{i:03d}" for i in range(5)]
    if modification=="sample_auth_claim":
        q["sample"]=sample(authority="PROVEN_PHYSICAL_T0_DENSITY")
    if modification=="sample_dens_missing":
        q["sample"]=sample()
        q["sample"]["density_interval"]=None
    if modification=="sample_bad_units":
        q["sample"]=sample()
        q["sample"]["density_interval"]["unit"]="g/cm3"
    if modification=="candidate_no_sample":
        q["candidate_materials"]=[candidate()]
    with pytest.raises((g.ResearchQueryError,GeologicalContractError),match=err):
        g.validate_query(q)


def test_write_once_receipt_sha_and_no_history(tmp_path):
    result=g.dt_feasibility(ROOT)
    out=tmp_path/"new_dt_gate"
    g.write_new(out,result,inputs={"mode":"dt_gate","horizons":[100,1000]})
    m=json.loads((out/"MANIFEST.json").read_text())
    assert m["report_sha256"]==hashlib.sha256(
        (out/"REPORT.json").read_bytes()).hexdigest()
    assert m["no_history_store_mutations"]
    assert m["no_physical_T1"]
    with pytest.raises(g.ResearchQueryError,match="EVIDENCE_ALREADY_EXISTS"):
        g.write_new(out,result,inputs={"mode":"dt_gate"})
