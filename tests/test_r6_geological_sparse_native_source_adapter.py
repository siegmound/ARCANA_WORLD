"""Verify provenance and interpretation of sparse original T0 material sources.

Synthetic in-memory NPZ arrays test indexing only; real source authentication
is separately required by the public extractor.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from arcana_worldsim.r6 import geological_source_t0_adapter as g
from arcana_worldsim.r6.geological_coarse_state import GeologicalContractError

ROOT=Path(__file__).resolve().parents[1]
C0="R6G1D-R000-C000"
C1="R6G1D-R000-C001"


def synthetic_arrays():
    domain=np.full((180,360),4,dtype=np.int16)
    for code in range(1,7):
        domain[0,code-1]=code
    therm=np.full((180,360),2,dtype=np.int16)
    therm[domain==1]=0
    thick=np.full((180,360),35000.,dtype=np.float64)
    thick[domain==1]=6500.
    age=np.full((180,360),np.nan,dtype=np.float64)
    age[domain==1]=12.5
    heat=np.full((180,360),0.06,dtype=np.float64)
    heat[domain==1]=np.nan
    lith=np.full((180,360),135000.,dtype=np.float64)
    lith[domain==1]=np.nan
    fields={
        "physical_crust_domain_id":domain,
        "crustal_thickness_m":thick,
        "continental_thermal_domain_id":therm,
        "continental_reference_surface_heat_flow_w_m2":heat,
        "continental_reference_lithosphere_thickness_m":lith,
        "oceanic_lithosphere_age_ma":age,
    }
    rr,cc=np.indices((180,360))
    parts={"face_row":rr.ravel().astype(np.int16),
        "face_col":cc.ravel().astype(np.int16),
        "face_plate_id":(np.arange(64800)%12).astype(np.int16)}
    return fields,parts


def synthetic_pins():
    original=g.verify_manifests(ROOT)
    assert original["plate_ids"]==list(range(12))
    return original


def test_exact_pinned_manifest_identity_and_semantics():
    pins=g.verify_manifests(ROOT)
    assert pins["plate_ids"]==list(range(12))
    assert pins["field"]["field_package_sha256"]==g.FIELD_SHA
    assert pins["vector"]["payload"]["sha256"]==g.PLATE_SHA
    assert pins["index"]["partition_counts"]["admitted"]==63620
    assert pins["material"]["density"]["continental_crust"]["nominal"]==2800
    assert pins["material"]["density"]["oceanic_crust"]["nominal"]==2890


def test_original_zero_based_12_plate_face_partition_not_one_to_twelve():
    _,parts=synthetic_arrays()
    plate=g.reconstruct_plates(parts,list(range(12)))
    assert plate.shape==(180,360)
    assert plate[0,0]==0
    assert plate[0,1]==1
    assert plate[0,11]==11
    assert plate[0,12]==0


def test_synthetic_selected_native_cells_recover_model_not_observational_properties():
    f,p=synthetic_arrays()
    out=g.selected_source_records(f,p,[C0,C1],synthetic_pins())
    assert len(out)==2
    a,b=out
    assert a["source_plate_id"]==0
    assert a["source_model_crust_domain_id"]==1
    assert a["source_authored_crustal_thickness_m"]==6500.
    assert a["source_oceanic_lithosphere_age_ma"]==12.5
    assert a["reference_crust_density_nominal_kg_m3"]==2890
    assert a["source_continental_thermal_class_id"] is None
    assert b["source_plate_id"]==1
    assert b["source_model_crust_domain_id"]==2
    assert b["source_authored_crustal_thickness_m"]==35000.
    assert b["reference_crust_density_nominal_kg_m3"]==2800
    assert b["source_continental_reference_heat_flow_w_m2"]==0.06
    assert b["source_oceanic_lithosphere_age_ma"] is None
    assert a["native_cell_area_m2_geometric"]>0
    assert all(x["actual_local_bulk_density_kg_m3"] is None
               and x["actual_mineral_phase_field"] is None
               and x["actual_ore_resource_field"] is None
               and x["actual_Deep_accessibility"] is None
               and x["B6N8N_thermal_membership_verified"] is False
               for x in out)


def test_verified_npz_requires_real_digest_even_if_fields_match(tmp_path):
    f,_=synthetic_arrays()
    path=tmp_path/"synthetic.npz"
    np.savez(path,**f)
    with pytest.raises(g.GeologicalSourceError,match="ORIGINAL_NPZ_SHA_MISMATCH"):
        g.verified_npz(path,g.FIELD_SHA,g.FIELDS)


def test_verified_npz_synthetic_checksum_proves_array_integrity_only(tmp_path):
    f,_=synthetic_arrays()
    path=tmp_path/"synthetic.npz"
    np.savez(path,**f)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    arrays=g.verified_npz(path,digest,g.FIELDS)
    assert arrays["crustal_thickness_m"][0,0]==6500.
    # The synthetic hash is intentionally not a canonical R6 pin.
    assert digest!=g.FIELD_SHA


@pytest.mark.parametrize("fault,code",[
 ("face_duplicate","FACE_PARTITION_DUPLICATE_OR_MISSING"),
 ("face_missing","FACE_PARTITION_SHAPE_OR_TYPE_INVALID"),
 ("one_based","FACE_PARTITION_RANGE_OR_PLATE_SET_CHANGED"),
 ("out_of_bounds","FACE_PARTITION_RANGE_OR_PLATE_SET_CHANGED"),
 ("nonint","FACE_PARTITION_SHAPE_OR_TYPE_INVALID"),
])
def test_bad_plate_partition_cannot_join_source(fault,code):
    _,p=synthetic_arrays()
    if fault=="face_duplicate":p["face_row"][1]=0;p["face_col"][1]=0
    if fault=="face_missing":p["face_row"]=p["face_row"][:-1]
    if fault=="one_based":p["face_plate_id"]=p["face_plate_id"]+1
    if fault=="out_of_bounds":p["face_row"][0]=180
    if fault=="nonint":p["face_col"]=p["face_col"].astype(float)
    with pytest.raises(g.GeologicalSourceError,match=code):
        g.reconstruct_plates(p,list(range(12)))


@pytest.mark.parametrize("fault,code",[
 ("unknown_domain","SOURCE_DOMAIN_OR_THERMAL_CODES_INVALID"),
 ("missing_field","SOURCE_FIELD_GRID_SHAPE_INVALID"),
 ("ocean_thermal","OCEAN_CONTINENTAL_THERMAL_LEAK"),
 ("invalid_mantle_residual","CONTINENTAL_REFERENCE_GEOMETRY_INVALID"),
 ("no_thickness","CRUST_THICKNESS_NOT_SOURCE_KNOWN"),
 ("invalid_cell","INVALID_NATIVE_CELL_ID"),
 ("cell_out_of_grid","NATIVE_CELL_OUT_OF_BOUNDS"),
])
def test_bad_native_field_semantics_rejected(fault,code):
    f,p=synthetic_arrays()
    cell=[C0] if fault in ("ocean_thermal","no_thickness") else [C1]
    if fault=="unknown_domain":f["physical_crust_domain_id"][0,1]=7
    if fault=="missing_field":f.pop("crustal_thickness_m")
    if fault=="ocean_thermal":f["continental_thermal_domain_id"][0,0]=1
    if fault=="invalid_mantle_residual":
        f["continental_reference_lithosphere_thickness_m"][0,1]=35000.
    if fault=="no_thickness":f["crustal_thickness_m"][0,0]=np.nan
    if fault=="invalid_cell":cell=["bad_id"]
    if fault=="cell_out_of_grid":cell=["R6G1D-R180-C001"]
    with pytest.raises(g.GeologicalSourceError,match=code):
        g.selected_source_records(f,p,cell,synthetic_pins())


def test_public_extractor_rejects_missing_genuine_binary_not_faux_original(tmp_path):
    with pytest.raises(g.GeologicalSourceError,match="ORIGINAL_NPZ_NOT_FOUND"):
        g.extract(ROOT,[C0],field_package=tmp_path/"missing_original.npz",
                  plate_partition=tmp_path/"missing_plate.npz")


def test_public_extractor_requires_selected_cells_even_before_original_npz(tmp_path):
    with pytest.raises((g.GeologicalSourceError,GeologicalContractError),
                       match="MAX_EIGHT_SELECTED_CELLS|PARENT_CELL_COLLECTION_INVALID"):
        g.extract(ROOT,[],field_package=tmp_path/"irrelevant.npz")
    with pytest.raises(g.GeologicalSourceError,match="MAX_EIGHT_SELECTED_CELLS"):
        g.extract(ROOT,[f"R6G1D-R001-C{i:03d}" for i in range(9)],
                  field_package=tmp_path/"irrelevant.npz")


def test_public_source_and_geometry_query_remain_unqualified_when_mocking_only_binary_reader(monkeypatch):
    f,p=synthetic_arrays()
    def synthetic_reader(path,expected,keys):
        return f if expected==g.FIELD_SHA else p
    monkeypatch.setattr(g,"verified_npz",synthetic_reader)
    req={
      "schema":"ARCANA_R6_GEOLOGICAL_ON_DEMAND_REQUEST_V1",
      "parent_cell_ids":[C0],"at_ma":210,
      "subdivision_factor":2,
      "research_question":"synthetic_native_join_only",
      "sample_density_interval":None,
      "declared_density_candidates":[],
    }
    out=g.extract(ROOT,[C0],
                  field_package=Path("synthetic-field"),
                  plate_partition=Path("synthetic-vector"),
                  refinement_query=req)
    assert out["selected_cell_count"]==1
    assert out["native_cell_source_records"][0]["source_plate_id"]==0
    assert out["read_only_geometric_refinement"]["child_geometry_count"]==4
    assert all(c["scientific_values_created"] is False
               and c["bulk_density_kg_m3"] is None
               and c["child_mass_kg"] is None
               for c in out["read_only_geometric_refinement"]["children"])
    assert out["world_history_production_authorized"] is False
    assert out["history_store_writes"]==0
    assert out["physical_T1"] is None
    req["at_ma"]=209
    with pytest.raises(g.GeologicalSourceError,match="REFINE_REQUEST_NOT_SAME_T0_SOURCE_CELLS"):
        g.extract(ROOT,[C0],
                  field_package=Path("synthetic-field"),
                  plate_partition=Path("synthetic-vector"),
                  refinement_query=req)


def test_write_once_source_receipt_no_history(tmp_path):
    report={
       "native_cell_source_records":[{"parent_cell_id":C0}],
       "physical_T1":None}
    out=tmp_path/"SOURCE_READ_ONLY_REPORT"
    g.write_new(out,report)
    m=json.loads((out/"MANIFEST.json").read_text())
    assert m["files"]["REPORT.json"]==hashlib.sha256(
        (out/"REPORT.json").read_bytes()).hexdigest()
    assert m["original_sources_unchanged"] and m["history_not_written"]
    with pytest.raises(g.GeologicalSourceError,match="EVIDENCE_EXISTS_NO_OVERWRITE"):
        g.write_new(out,report)
