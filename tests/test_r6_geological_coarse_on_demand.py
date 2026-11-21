"""Source-frozen grid, sparse declared geology and no invented child geology."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from arcana_worldsim.r6 import geological_coarse_state as g

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
C0 = "R6G1D-R089-C359"
C1 = "R6G1D-R090-C000"
C2 = "R6G1D-R000-C000"


def catalog():
    return g.empty_catalog(ROOT)


def interval(a=2700., b=3100., unit="kg/m3"):
    return {"unit":unit, "low":a, "high":b}


def snapshot(cell=C0,at_ma=200.,with_density=True,events=None):
    return {
        "parent_cell_id":cell, "at_ma":at_ma,
        "material_family":"MAFIC_CRUST_CANDIDATE",
        "uncertainty_class":"BOUNDED_AUTHORIAL_HYPOTHESIS",
        "observables":{
            "bulk_density_kg_m3":interval() if with_density else None,
            "crustal_thickness_m":None, "temperature_k":None},
        "event_refs":[] if events is None else events,
        "source_claim":"AUTHORIAL_HYPOTHESIS_NOT_VERIFIED_GEOLOGY",
    }


def event(at_ma=205.,cells=None):
    return {
        "event_id":"EVT_01","kind":"MAGMATISM","at_ma":at_ma,
        "parent_cell_ids":[C0] if cells is None else cells,
        "source_claim":"AUTHORIAL_HYPOTHESIS_NOT_PHYSICAL_EVENT",
    }


def query(ids=None,factor=2,time=200.,sample=None,candidates=None):
    return {"schema":g.REQUEST_SCHEMA,
       "parent_cell_ids":[C0] if ids is None else ids,
       "at_ma":time, "subdivision_factor":factor,
       "research_question":"density_investigation",
       "sample_density_interval":sample,
       "declared_density_candidates":[] if candidates is None else candidates}


def candidate(cid="MAFIC_01",family="MAFIC_CRUST_CANDIDATE",lo=2800.,hi=3200.):
    return {"candidate_id":cid,"material_family":family,
        "hypothetical_density_range":interval(lo,hi),
        "authority":"DECLARED_UNCALIBRATED_REFERENCE_INTERVAL"}


def test_empty_original_64800_grid_index_and_zero_physical_geology():
    c=catalog()
    assert c["snapshots"]==c["events"]==[]
    result=g.report(ROOT,c)
    assert result["native_parent_cell_count"]==64800
    assert result["thermal_support_cells_NOT_geochemical_mapping"]==63620
    assert result["physical_geological_cell_assignments"]==0
    assert result["history_store_mutations"]==0
    assert result["physical_T1"] is None


def test_valid_source_anchored_sparse_candidate_is_not_physical_t0():
    c=catalog()
    c["events"]=[event()]
    c["snapshots"]=[snapshot(events=["EVT_01"])]
    result=g.validate_catalog(c,ROOT)
    assert result["noncanonical_sparse_snapshot_count"]==1
    assert result["noncanonical_event_reference_count"]==1
    assert result["physical_geological_cell_assignments"]==0
    assert result["catalog"]["snapshots"][0]["event_refs"]==["EVT_01"]


def test_canonical_catalog_digest_independent_of_event_snapshot_insertion_order():
    c=catalog()
    c["events"]=[event(cells=[C0,C1]),
                 {**event(cells=[C1]),"event_id":"EVT_02","at_ma":200.}]
    c["snapshots"]=[snapshot(C1,200.,events=["EVT_02"]),
                    snapshot(C0,200.,events=["EVT_01"])]
    left=g.validate_catalog(c,ROOT)["catalog_digest_sha256"]
    c["events"].reverse()
    c["snapshots"].reverse()
    assert g.validate_catalog(c,ROOT)["catalog_digest_sha256"]==left


def test_request_scoped_children_are_geometry_only_and_do_not_repeat_density():
    c=catalog();c["snapshots"]=[snapshot()]
    v=g.validate_catalog(c,ROOT)
    output=g.make_refinement_plan(v,query(factor=3))
    assert output["parent_count"]==1
    assert output["child_geometry_count"]==9
    assert output["parents"][0]["parent_density_kg_m3_interval"]==interval()
    assert output["parents"][0]["parent_mass_kg"] is None
    assert output["conservation_checked"] is False
    assert output["physical_parent_mass_available"] is False
    assert all(x["bulk_density_kg_m3"] is None and
               x["material_family"] is None and
               x["child_mass_kg"] is None and
               x["scientific_values_created"] is False
               for x in output["children"])
    assert not output["mechanical_solve_authorized"]
    assert not output["world_history_production_authorized"]


def test_request_replay_deterministic_even_if_catalog_rows_reordered():
    c=catalog();c["snapshots"]=[snapshot(C1),snapshot(C0)]
    v=g.validate_catalog(c,ROOT)
    first=g.make_refinement_plan(v,query(ids=[C1,C0],factor=2))
    second=g.make_refinement_plan(v,query(ids=[C0,C1],factor=2))
    assert first==second
    assert first["child_geometry_count"]==8
    assert first["refinement_request_id"].startswith("r6refinementrequest_")


def test_request_without_parent_snapshot_retains_unknown_no_invented_values():
    result=g.make_refinement_plan(g.validate_catalog(catalog(),ROOT),query(ids=[C2]))
    assert result["parents"][0]["coarse_snapshot"] is None
    assert result["parents"][0]["parent_density_kg_m3_interval"] is None
    assert result["children"][0]["mineral_phase_fractions"] is None
    assert result["children"][0]["ore_deposit_probability"] is None
    assert result["children"][0]["Deep_X_accessibility"] is None


def test_declared_density_overlap_is_screening_not_probability():
    candidates=[candidate(),candidate("FELSIC_01","FELSIC_CRUST_CANDIDATE",2200.,2500.)]
    out=g.make_refinement_plan(g.validate_catalog(catalog(),ROOT),
         query(sample=interval(2900.,3000.),candidates=candidates))
    screening=out["density_screening"]
    assert screening["status"]=="INTERVAL_OVERLAP_ONLY_NOT_IDENTIFICATION"
    assert [x["overlap_under_declared_intervals"]
            for x in screening["conditional_candidates"]]==[True,False]
    assert all(x["posterior_probability"] is None for x in screening["conditional_candidates"])
    assert screening["actual_material_identification"] is None


def test_no_density_prior_is_insufficient_not_absence():
    out=g.make_refinement_plan(g.validate_catalog(catalog(),ROOT),
        query(sample=interval()))
    assert out["density_screening"]["status"]=="INSUFFICIENT_CALIBRATED_PRIORS"


@pytest.mark.parametrize("mutate,code",[
    ("wrong_grid","CATALOG_CLAIMS_UNAUTHORIZED_HISTORY"),
    ("physical_T1","CATALOG_CLAIMS_UNAUTHORIZED_HISTORY"),
    ("history_enabled","CATALOG_CLAIMS_UNAUTHORIZED_HISTORY"),
    ("checkpoint_forgery","CATALOG_CLAIMS_UNAUTHORIZED_HISTORY"),
    ("duplicate","DUPLICATED_SNAPSHOT_AT_TIME"),
    ("invalid_family","FAMILY_NOT_IN_GENERIC_VOCABULARY"),
    ("fake_measurement","UNVERIFIED_SNAPSHOT_SOURCE_PROMOTION"),
    ("invalid_density_unit","MEASUREMENT_INTERVAL_UNIT_OR_FIELDS_INVALID"),
    ("nonfinite_density","MEASUREMENT_INTERVAL_INVALID"),
    ("unbounded_family","COARSE_UNCERTAINTY_MISMATCH"),
    ("missing_event","EVENT_OUTSIDE_CELL_OR_PRIOR_TIME"),
    ("future_event","EVENT_OUTSIDE_CELL_OR_PRIOR_TIME"),
])
def test_fail_closed_unqualified_or_inconsistent_sparse_catalog(mutate,code):
    c=catalog(); c["snapshots"]=[snapshot()]
    if mutate=="wrong_grid":c["original_grid_id"]="OTHER"
    if mutate=="physical_T1":c["physical_T1"]=False
    if mutate=="history_enabled":c["world_history_production_authorized"]=True
    if mutate=="checkpoint_forgery":c["source_checkpoint_sha256"]="0"*64
    if mutate=="duplicate":c["snapshots"].append(snapshot())
    if mutate=="invalid_family":c["snapshots"][0]["material_family"]="DIAMOND_ORE"
    if mutate=="fake_measurement":c["snapshots"][0]["source_claim"]="DIRECT_AUTHORITY"
    if mutate=="invalid_density_unit":
        c["snapshots"][0]["observables"]["bulk_density_kg_m3"]["unit"]="g/cm3"
    if mutate=="nonfinite_density":
        c["snapshots"][0]["observables"]["bulk_density_kg_m3"]["low"]=float("nan")
    if mutate=="unbounded_family":
        c["snapshots"][0]["uncertainty_class"]="UNRESOLVED_UNKNOWN"
    if mutate=="missing_event":c["snapshots"][0]["event_refs"]=["NOT_THERE"]
    if mutate=="future_event":
        c["events"]=[event(at_ma=190.)]
        c["snapshots"][0]["event_refs"]=["EVT_01"]
    with pytest.raises(g.GeologicalContractError,match=code):
        g.validate_catalog(c,ROOT)


@pytest.mark.parametrize("bad,code",[
    ("no_parent","PARENT_CELL_COLLECTION_INVALID"),
    ("out_of_bounds","PARENT_CELL_OUTSIDE_ORIGINAL_GRID"),
    ("too_many_parents","REFINEMENT_BUDGET_EXCEEDED"),
    ("too_many_children","REFINEMENT_BUDGET_EXCEEDED"),
    ("bool_factor","REFINEMENT_BUDGET_EXCEEDED"),
    ("density_bad_units","MEASUREMENT_INTERVAL_UNIT_OR_FIELDS_INVALID"),
    ("missing_question","RESEARCH_QUESTION_ID_INVALID"),
    ("duplicate","DUPLICATE_OR_INVALID_PARENT_CELLS"),
])
def test_refinement_request_fail_closed_and_limited_budget(bad,code):
    q=query()
    if bad=="no_parent":q["parent_cell_ids"]=[]
    if bad=="out_of_bounds":q["parent_cell_ids"]=["R6G1D-R180-C000"]
    if bad=="too_many_parents":
        q["parent_cell_ids"]=[f"R6G1D-R001-C{j:03d}" for j in range(9)]
    if bad=="too_many_children":
        q["parent_cell_ids"]=[f"R6G1D-R001-C{j:03d}" for j in range(8)]
        q["subdivision_factor"]=8
    if bad=="bool_factor":q["subdivision_factor"]=True
    if bad=="density_bad_units":
        q["sample_density_interval"]=interval(unit="unknown")
    if bad=="missing_question":q["research_question"]=""
    if bad=="duplicate":q["parent_cell_ids"]=[C0,C0]
    with pytest.raises(g.GeologicalContractError,match=code):
        g.make_refinement_plan(g.validate_catalog(catalog(),ROOT),q)


def test_catalog_source_git_object_digest_rejects_tampering(tmp_path):
    target=tmp_path/g.INDEX
    target.parent.mkdir(parents=True)
    target.write_bytes((ROOT/g.INDEX).read_bytes()+b" ")
    with pytest.raises(g.GeologicalContractError,match="SOURCE_INDEX_SHA_DRIFT"):
        g.empty_catalog(tmp_path)


def test_write_once_report_manifest_binds_input_and_no_world_history(tmp_path):
    raw=json.dumps(catalog()).encode()
    result=g.report(ROOT,json.loads(raw))
    out=tmp_path/"NEW_GEOLOGICAL_COARSE_REPORT"
    g.write_evidence(out,result,raw,None)
    report=json.loads((out/"REPORT.json").read_text())
    manifest=json.loads((out/"MANIFEST.json").read_text())
    assert report["physical_T1"] is None
    assert manifest["input_catalog_sha256"]==hashlib.sha256(raw).hexdigest()
    assert manifest["files"]["REPORT.json"]==hashlib.sha256(
        (out/"REPORT.json").read_bytes()).hexdigest()
    assert manifest["no_world_history"]
    assert manifest["geometry_only"]
    with pytest.raises(g.GeologicalContractError,match="OUTPUT_EXISTS_NO_OVERWRITE"):
        g.write_evidence(out,result,raw,None)
