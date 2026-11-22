"""Read-only, source-bound sparse T0 coarse geology adapter for R6.

Original crustal thickness and plate identities are model-derived T0 inputs.
Authored material-reference density is NOT observed local rock density.
No 3D lithology, minerals, ore, Deep, T1 or HistoryStore production.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import re
from pathlib import Path

import numpy as np

from .geological_coarse_state import (
    empty_catalog, validate_catalog, make_refinement_plan,
    REQUEST_SCHEMA, _canonical_cells,
)
from .initial_world.grid import GlobalGrid1Degree
from .repository_context import resolve_external_payload_path
from .identity import content_hash

SCHEMA="ARCANA_R6_T0_SPARSE_NATIVE_GEOLOGICAL_SOURCE_ADAPTER_V1"
PINS={
  "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json":
    "695cc991c0c8008c03ff9b57f289c73a1e2b71c2",
  "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json":
    "2fffd9c49df777a0fb72f63acde31344731c1961",
  "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json":
    "e041e7dc91f617cf7f755b46ab36e7417d486fd0",
  "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json":
    "e06770577ebaf549aa113a4e72ec9f6095a29c2d",
}
FIELD_SHA="39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e"
PLATE_SHA="a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
FIELDS=(
  "physical_crust_domain_id","crustal_thickness_m",
  "continental_thermal_domain_id",
  "continental_reference_surface_heat_flow_w_m2",
  "continental_reference_lithosphere_thickness_m",
  "oceanic_lithosphere_age_ma",
)
DOMAINS={1:"NORMAL_OCEANIC",2:"TRANSITIONAL_MARGIN",
  3:"EXTENDED_CONTINENTAL",4:"NORMAL_CONTINENTAL",
  5:"STABLE_CONTINENTAL",6:"OROGENIC_THICKENED"}
CELL_RE=re.compile(r"^R6G1D-R(\d{3})-C(\d{3})$")


class GeologicalSourceError(ValueError):
    pass


def require(ok,code):
    if not ok:
        raise GeologicalSourceError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def gitblob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def verify_manifests(root):
    source={}
    for path,blob in PINS.items():
        raw=(root/path).read_bytes()
        require(gitblob(raw)==blob,"GEO_MANIFEST_HASH_CHANGED:"+path)
        source[path]=json.loads(raw)
    b=source["R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json"]
    p=source["R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"]
    m=source["R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json"]
    i=source["docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json"]
    require(b["field_package_sha256"]==FIELD_SHA
            and set(b["normalized_field_hashes"])>=set(FIELDS)
            and p["payload"]["sha256"]==PLATE_SHA
            and p["topology"]["face_count"]==64800
            and p["topology"]["plate_count"]==12
            and p["parent_grid"]["grid_id"]=="R6_GLOBAL_GEOGRAPHY_1DEG_V1"
            and p["parent_grid"]["shape"]==[180,360]
            and i["partition_counts"]["native"]==64800
            and i["partition_counts"]["admitted"]==63620
            and i["grid"]["grid_id"]=="R6_GLOBAL_GEOGRAPHY_1DEG_V1",
            "GEO_SOURCE_MANIFEST_CONTRACT_CHANGED")
    plate_ids=sorted({int(x[k]) for x in p["adjacency_groups"]
                      for k in ("plate_a","plate_b")})
    require(plate_ids==list(range(12)),
            "GEO_ORIGINAL_PLATE_IDS_NOT_0_TO_11")
    for role in ("continental_crust","oceanic_crust"):
        r=m["density"][role]
        require(r["authority_class"]=="ARCANA_AUTHORED_SPECIALIST_REFERENCE"
                and r["units"]=="kg m-3"
                and float(r["sensitivity_range"][0])<=float(r["nominal"])<=
                    float(r["sensitivity_range"][1]),
                "GEO_REFERENCE_DENSITY_AUTHORITY_CHANGED")
    return {"field":b,"vector":p,"material":m,"index":i,
            "plate_ids":plate_ids}


def verified_npz(path,expected,keys):
    require(path.is_file(),"GEO_ORIGINAL_NPZ_NOT_FOUND:"+path.name)
    raw=path.read_bytes()
    require(sha(raw)==expected,"GEO_ORIGINAL_NPZ_SHA_MISMATCH:"+path.name)
    with np.load(io.BytesIO(raw),allow_pickle=False) as src:
        require(set(src.files)>=set(keys),"GEO_ORIGINAL_NPZ_FIELDS_MISSING")
        return {name:src[name].copy() for name in keys}


def reconstruct_plates(parts,expected_plate_ids):
    rr,cc,pp=[parts[k] for k in ("face_row","face_col","face_plate_id")]
    require(all(a.shape==(64800,) and np.issubdtype(a.dtype,np.integer)
                for a in (rr,cc,pp)),
            "GEO_FACE_PARTITION_SHAPE_OR_TYPE_INVALID")
    require(np.all((rr>=0)&(rr<180))
            and np.all((cc>=0)&(cc<360))
            and sorted(map(int,np.unique(pp)))==expected_plate_ids,
            "GEO_FACE_PARTITION_RANGE_OR_PLATE_SET_CHANGED")
    flat=rr.astype(np.int64)*360+cc.astype(np.int64)
    require(np.unique(flat).size==64800,
            "GEO_FACE_PARTITION_DUPLICATE_OR_MISSING")
    grid=np.empty((180,360),dtype=np.int64)
    grid[rr,cc]=pp
    return grid


def numeric_at(array,row,col,*,positive=False):
    x=array[row,col]
    require(isinstance(x,(np.number,int,float))
            and not isinstance(x,(bool,np.bool_)),
            "GEO_SOURCE_FIELD_NOT_NUMERIC")
    val=float(x)
    if not math.isfinite(val):
        return None
    require(not positive or val>0,"GEO_SOURCE_INVALID_NONPOSITIVE_VALUE")
    return val


def selected_source_records(fields,parts,cell_ids,pins):
    """Pure join for verified source arrays; synthetic fixtures test logic only."""
    require(set(fields)>=set(FIELDS)
            and all(fields[k].shape==(180,360) for k in FIELDS),
            "GEO_SOURCE_FIELD_GRID_SHAPE_INVALID")
    dom=fields["physical_crust_domain_id"]
    therm=fields["continental_thermal_domain_id"]
    require(np.issubdtype(dom.dtype,np.integer)
            and np.issubdtype(therm.dtype,np.integer)
            and sorted(map(int,np.unique(dom)))==list(DOMAINS)
            and np.all(np.isin(therm,[0,1,2,3])),
            "GEO_SOURCE_DOMAIN_OR_THERMAL_CODES_INVALID")
    plates=reconstruct_plates(parts,pins["plate_ids"])
    rho=pins["material"]["density"]
    areas=GlobalGrid1Degree().cell_areas_m2()
    result=[]
    for name in cell_ids:
        match=CELL_RE.fullmatch(name)
        require(match is not None,"GEO_INVALID_NATIVE_CELL_ID")
        row,col=int(match[1]),int(match[2])
        require(row<180 and col<360,"GEO_NATIVE_CELL_OUT_OF_BOUNDS")
        domain=int(dom[row,col]);is_ocean=(domain==1)
        thick=numeric_at(fields["crustal_thickness_m"],row,col,positive=True)
        require(thick is not None,"GEO_CRUST_THICKNESS_NOT_SOURCE_KNOWN")
        thermal_id=int(therm[row,col])
        if is_ocean:
            require(thermal_id==0,"GEO_OCEAN_CONTINENTAL_THERMAL_LEAK")
            heat=None; lith=None;thermal_class=None
            age=numeric_at(fields["oceanic_lithosphere_age_ma"],row,col)
        else:
            require(thermal_id in (1,2,3),
                    "GEO_CONTINENTAL_THERMAL_CODE_INVALID")
            heat=numeric_at(fields[
              "continental_reference_surface_heat_flow_w_m2"],row,col,
              positive=True)
            lith=numeric_at(fields[
              "continental_reference_lithosphere_thickness_m"],row,col,
              positive=True)
            require(heat is not None and lith is not None and lith>thick,
                    "GEO_CONTINENTAL_REFERENCE_GEOMETRY_INVALID")
            thermal_class=thermal_id;age=None
        density=rho["oceanic_crust" if is_ocean else "continental_crust"]
        result.append({
          "parent_cell_id":name,"source_plate_id":int(plates[row,col]),
          "source_model_crust_domain_id":domain,
          "source_model_crust_domain_label":DOMAINS[domain],
          "source_authored_crustal_thickness_m":thick,
          "source_continental_thermal_class_id":thermal_class,
          "source_continental_reference_heat_flow_w_m2":heat,
          "source_continental_reference_lithosphere_thickness_m":lith,
          "source_oceanic_lithosphere_age_ma":age,
          "native_cell_area_m2_geometric":float(areas[row,col]),
          "reference_crust_density_nominal_kg_m3":
              float(density["nominal"]),
          "reference_crust_density_sensitivity_kg_m3":
              list(map(float,density["sensitivity_range"])),
          "density_authority":
              "AUTHORED_REFERENCE_MODEL_NOT_LOCAL_ROCK_MEASUREMENT",
          "actual_local_bulk_density_kg_m3":None,
          "actual_mineral_phase_field":None,
          "actual_rock_family":None,
          "actual_ore_resource_field":None,
          "actual_Deep_accessibility":None,
          "actual_pressure_temperature_fugacity":None,
          "B6N8N_thermal_membership_verified":False,
          "B6N8N_thermal_membership":
              "NOT_CHECKED_EXACT_MEMBERSHIP_REQUIRED",
          "physical_historical_checkpoint_id":None,
        })
    return result


def extract(root,cell_ids,*,field_package=None,plate_partition=None,
            refinement_query=None):
    root=Path(root).resolve()
    pins=verify_manifests(root)
    try:
        cells=_canonical_cells(cell_ids)
    except ValueError as exc:
        raise GeologicalSourceError("GEO_INVALID_CELL_SELECTION") from exc
    require(1<=len(cells)<=8,"GEO_MAX_EIGHT_SELECTED_CELLS")
    fpath=(Path(field_package) if field_package is not None
           else root/pins["field"]["field_package_path"])
    ppath=(Path(plate_partition) if plate_partition is not None
           else resolve_external_payload_path(root,pins["vector"]["payload"]["path"]))
    field=verified_npz(fpath,FIELD_SHA,FIELDS)
    parts=verified_npz(ppath,PLATE_SHA,
                       ("face_row","face_col","face_plate_id"))
    records=selected_source_records(field,parts,cells,pins)
    output={
      "schema":SCHEMA,
      "decision":"PINNED_SPARSE_NATIVE_T0_COARSE_SOURCE_EXTRACTED_NO_NATURAL_ROCK_MAP",
      "original_grid_id":"R6_GLOBAL_GEOGRAPHY_1DEG_V1",
      "time_ma":210.0,"original_cells":64800,
      "thermal_role_eligible_cells_not_chemistry":63620,
      "source_field_package_sha256":FIELD_SHA,
      "source_vector_partition_sha256":PLATE_SHA,
      "source_document_git_blobs":dict(PINS),
      "selected_cell_count":len(records),
      "native_cell_source_records":records,
      "actual_world_natural_density_cells":0,
      "actual_world_mineral_cells":0,
      "actual_world_ore_and_Deep_fields":None,
      "physical_geology_history_generated":False,
      "history_store_writes":0,
      "mechanical_solve_authorized":False,
      "world_history_production_authorized":False,
      "D_024":"ACTIVE","physical_T1":None,
    }
    if refinement_query is not None:
        require(type(refinement_query) is dict
                and refinement_query.get("schema")==REQUEST_SCHEMA
                and refinement_query.get("at_ma")==210
                and _canonical_cells(refinement_query.get("parent_cell_ids"))==cells,
                "GEO_REFINE_REQUEST_NOT_SAME_T0_SOURCE_CELLS")
        c=validate_catalog(empty_catalog(root),root)
        plan=make_refinement_plan(c,refinement_query)
        output["read_only_geometric_refinement"]=plan
        output["child_geological_fields_created"]=0
        output["checkpoint_reconstruction_executed"]=False
    return output


def write_new(output,report):
    require(not output.exists(),"GEO_EVIDENCE_EXISTS_NO_OVERWRITE")
    output.mkdir(parents=True,exist_ok=False)
    rp=output/"REPORT.json"
    rp.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (output/"MANIFEST.json").write_text(json.dumps({
       "schema":"ARCANA_R6_T0_SPARSE_SOURCE_EXTRACTION_MANIFEST_V1",
       "source_field_package_sha256":FIELD_SHA,
       "source_vector_partition_sha256":PLATE_SHA,
       "source_selected_cell_ids_sha256":content_hash(
           [x["parent_cell_id"] for x in report["native_cell_source_records"]]),
       "files":{"REPORT.json":sha(rp.read_bytes())},
       "original_sources_unchanged":True,"history_not_written":True,
       "no_physical_T1":True},indent=2)+"\n")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[3])
    ap.add_argument("--cell",action="append",required=True)
    ap.add_argument("--field-package",type=Path)
    ap.add_argument("--plate-partition",type=Path)
    ap.add_argument("--query",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    x=ap.parse_args()
    request=None if x.query is None else json.loads(x.query.read_text("utf8"))
    r=extract(x.repo_root,x.cell,field_package=x.field_package,
              plate_partition=x.plate_partition,refinement_query=request)
    write_new(x.output,r)
    print(json.dumps({
       "decision":r["decision"],"source_bound_cells":r["selected_cell_count"],
       "density_reference_not_natural_cell_density":True,
       "child_geometry_count":r.get("read_only_geometric_refinement",{}).get(
           "child_geometry_count",0),
       "natural_rock_mineralogy_created":0,"physical_T1":None}))


if __name__=="__main__":
    main()
