"""Scientific R6 authorial bulk-oxide hypotheses, never canonical T0 chemistry.

An explicit recipe can be mixed with full mass-conservation accounting,
but its native-grid placement requires independent original source proofs.
Original R6 thermophysical material roles do not imply mineralogy.
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
from experiments.t0_geochemical_reference_v1.compile_references import (
    elemental_oxide_budget, git_blob_sha,
)

SCHEMA="ARCANA_R6_T0_AUTHORIAL_BULK_COMPOSITION_HYPOTHESIS_V1"
RESULT_SCHEMA="ARCANA_R6_T0_BULK_COMPOSITION_CANDIDATE_REPORT_V1"
AUTHORITY="EXPLICIT_AUTHORIAL_EXPERIMENT_ONLY_NOT_CANONICAL"
INDEX="docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json"
INDEX_BLOB="e06770577ebaf549aa113a4e72ec9f6095a29c2d"
FIELD_SHA="39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e"
PLATE_SHA="a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
OXIDES={"SiO2","TiO2","Al2O3","FeO*","FeO","MnO","MgO","CaO","Na2O","K2O","P2O5"}
ROLES={"CONTINENTAL_CRUST_BULK","OCEANIC_CRUST_BULK",
       "LITHOSPHERIC_MANTLE_BULK","FAULT_GOUGE_BULK"}
CELL_ID=re.compile(r"^R6G1D-R(\d{3})-C(\d{3})$")
LABEL=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,99}$")


class SourceAuthorityError(ValueError):
    pass


def require(ok,code):
    if not ok: raise SourceAuthorityError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def number(v,label,low=0.,high=100.):
    require(type(v) in (float,int) and
            math.isfinite(v) and low<=v<=high,
            "COMPOSITION_INVALID_NUMBER:"+label)
    return float(v)


def identity(v,label):
    require(type(v) is str and bool(LABEL.fullmatch(v)),
            "COMPOSITION_INVALID_ID:"+label)
    return v


def source_index(root):
    raw=(root/INDEX).read_bytes()
    require(git_blob_sha(raw)==INDEX_BLOB,"COMPOSITION_B6N8N_SOURCE_HASH_DRIFT")
    index=json.loads(raw)
    require(index["schema"]=="ARCANA_R6_B6N8N_ADMITTED_SUPPORT_BINDING_INDEX_V1"
            and index["grid"]["shape"]==[180,360]
            and index["partition_counts"]["admitted"]==63620
            and index["partition_counts"]["native"]==64800,
            "COMPOSITION_ORIGINAL_NATIVE_SUPPORT_CHANGED")
    return index


def make_template(root):
    index=source_index(root)
    return {"schema":SCHEMA,"scenario_id":None,"authority":AUTHORITY,
            "parent_grid":index["grid"]["grid_id"],
            "field_package_sha256":FIELD_SHA,
            "plate_partition_sha256":PLATE_SHA,
            "authorial_selection_confirmed":False,
            "authorial_selection_id":None,
            "recipes":[],"mixtures":[],"placements":[],
            "canonical_T0_materialization_authorized":False,
            "mechanical_solve_authorized":False,"physical_T1":None}


def oxide_recipe(row):
    require(type(row) is dict,"COMPOSITION_RECIPE_NOT_OBJECT")
    rid=identity(row.get("id"),"RECIPE")
    role=row.get("role")
    require(role in ROLES,"COMPOSITION_MATERIAL_ROLE_NOT_SUPPORTED")
    require(row.get("authority")==AUTHORITY and
            type(row.get("rationale")) is str and
            len(row["rationale"].strip())>=15,
            "COMPOSITION_AUTHORIAL_RATIONALE_REQUIRED")
    require(row.get("basis")=="AS_REPORTED_WT_PERCENT_NO_NORMALIZATION",
            "COMPOSITION_OXIDE_BASIS_MISSING")
    source=row.get("source")
    require(type(source) is dict and
            source.get("kind")=="AUTHORIAL_EXPLICIT_HYPOTHESIS"
            and type(source.get("reference")) is str and
            len(source["reference"].strip())>=5,
            "COMPOSITION_RECIPE_PROVENANCE_MISSING")
    vals=row.get("oxides")
    require(type(vals) is dict and vals and
            set(vals)<=OXIDES and "SiO2" in vals,
            "COMPOSITION_OXIDES_MISSING_OR_UNSUPPORTED")
    require(not ("FeO" in vals and "FeO*" in vals),
            "COMPOSITION_IRON_CONVENTION_AMBIGUOUS")
    oxide,bounds={},{}
    for k,entry in sorted(vals.items()):
        require(type(entry) is dict and
                set(entry)=={"unit","value","low","high"} and
                entry["unit"]=="wt.%",
                "COMPOSITION_OXIDE_UNIT_OR_INTERVAL_REQUIRED:"+k)
        x=number(entry["value"],k)
        lo=number(entry["low"],"LOW_"+k)
        hi=number(entry["high"],"HIGH_"+k)
        require(lo<=x<=hi,"COMPOSITION_NOMINAL_OUTSIDE_INTERVAL:"+k)
        oxide[k]=x
        bounds[k]=[lo,hi]
    require(0<sum(oxide.values())<110.,
            "COMPOSITION_TOTAL_OXIDE_SUBSET_INVALID")
    require(row.get("full_chemistry_known") is False and
            row.get("Fe_redox_speciation") is None and
            row.get("water_wt_pct") is None and
            row.get("pore_pressure_pa") is None and
            row.get("oxygen_fugacity") is None,
            "COMPOSITION_UNQUALIFIED_PHASE_FLUID_OR_FULL_CHEMISTRY")
    return {"id":rid,"role":role,"source":source,
        "authorial_rationale":row["rationale"],
        "oxide_mass_wt_percent":oxide,
        "oxide_authorial_intervals_wt_percent":bounds,
        "oxide_subset_total_wt_percent":sum(oxide.values()),
        "elemental_oxide_equivalent_budget":elemental_oxide_budget(oxide),
        "no_silent_normalization":True,
        "natural_mineral_assemblage":None,
        "iron_redox_fluid_thermodynamic_state":None,
        "physical_fault_law":None}


def mix(row,recipes):
    require(type(row) is dict,"COMPOSITION_MIXTURE_NOT_OBJECT")
    mid=identity(row.get("id"),"MIXTURE")
    comps=row.get("components")
    require(type(comps) is list and len(comps)>=2,
            "COMPOSITION_MIXTURE_TWO_ENDMEMBERS_REQUIRED")
    parts=[]
    for part in comps:
        require(type(part) is dict and
                set(part)=={"recipe_id","mass_fraction"},
                "COMPOSITION_MIXTURE_COMPONENT_SCHEMA_INVALID")
        rid=identity(part["recipe_id"],"RECIPE_ID")
        require(rid in recipes and rid not in [x for x,_ in parts],
                "COMPOSITION_MIXTURE_RECIPE_INVALID_OR_DUPLICATED")
        parts.append((rid,number(part["mass_fraction"],"FRACTION",0.,1.)))
    require(all(f>0 for _,f in parts) and
            math.isclose(sum(f for _,f in parts),1.,rel_tol=0,abs_tol=1e-12),
            "COMPOSITION_MASS_FRACTIONS_NOT_CONSERVED")
    roles={recipes[k]["role"] for k,_ in parts}
    keys={tuple(sorted(recipes[k]["oxide_mass_wt_percent"])) for k,_ in parts}
    require(len(roles)==len(keys)==1,
            "COMPOSITION_INCOMPATIBLE_ROLES_OR_OXIDE_BASIS")
    ox={name:sum(f*recipes[r]["oxide_mass_wt_percent"][name]
                 for r,f in parts) for name in next(iter(keys))}
    intervals={name:[sum(f*recipes[r]["oxide_authorial_intervals_wt_percent"][name][j]
                         for r,f in parts) for j in (0,1)] for name in ox}
    return {"id":mid,"role":next(iter(roles)),
            "components":[{"recipe_id":r,"mass_fraction":f} for r,f in parts],
            "oxide_mass_wt_percent":ox,
            "oxide_authorial_intervals_wt_percent":intervals,
            "oxide_subset_total_wt_percent":sum(ox.values()),
            "elemental_oxide_equivalent_budget":elemental_oxide_budget(ox),
            "candidate_only":True,"natural_mineral_assemblage":None}


def exact_member_ids(path,expected_hash):
    b=path.read_bytes()
    require(sha(b)==expected_hash,"COMPOSITION_ADMITTED_MEMBERSHIP_HASH_MISMATCH")
    lines=b.decode("utf8").splitlines(keepends=True)
    ids=[x[:-1] for x in lines]
    require(len(ids)==63620 and
            all(x.endswith("\n") and CELL_ID.fullmatch(x[:-1])
                for x in lines) and
            ids==sorted(set(ids)),
            "COMPOSITION_ADMITTED_MEMBERSHIP_FORMAT_OR_COUNT_INVALID")
    return set(ids)


def pinned_npz(path,expected_sha):
    b=path.read_bytes()
    require(sha(b)==expected_sha,
            "COMPOSITION_ORIGINAL_BINARY_SOURCE_SHA_MISMATCH")
    with np.load(io.BytesIO(b),allow_pickle=False) as archive:
        return {k:archive[k] for k in archive.files}


def source_placements(placements,sc,idx,recipes,mixtures,
                      *,field_package=None,plate_partition=None,
                      admitted_membership=None,plate_array_key=None):
    if not placements:return []
    require(all(x is not None for x in
                (field_package,plate_partition,admitted_membership,
                 plate_array_key)),
            "COMPOSITION_SPATIAL_SOURCE_PROVIDERS_REQUIRED")
    require(sc.get("authorial_selection_confirmed") is True and
            type(sc.get("authorial_selection_id")) is str and
            len(sc["authorial_selection_id"].strip())>=8,
            "COMPOSITION_AUTHORIAL_SELECTION_UNCONFIRMED")
    ids=exact_member_ids(admitted_membership,
         idx["membership_sha256"]["ADMITTED_INITIALIZER_SUPPORT"])
    f=pinned_npz(field_package,FIELD_SHA)
    p=pinned_npz(plate_partition,PLATE_SHA)
    require("physical_crust_domain_id" in f and
            f["physical_crust_domain_id"].shape==(180,360) and
            plate_array_key in p and p[plate_array_key].shape==(180,360),
            "COMPOSITION_ORIGINAL_SOURCE_GRID_FIELD_MISSING")
    domain=f["physical_crust_domain_id"]
    grid=p[plate_array_key]
    require(np.issubdtype(domain.dtype,np.integer) and
            np.issubdtype(grid.dtype,np.integer) and
            np.all((grid>=1)&(grid<=12)),
            "COMPOSITION_PLATE_GRID_NOT_INTEGER_1_TO_12")
    out=[];seen=set()
    for item in placements:
        require(type(item) is dict and
                set(item)=={"cell_id","plate_id","crust_domain_id","recipe_or_mixture_id"},
                "COMPOSITION_PLACEMENT_FIELDS_INVALID")
        name=item["cell_id"]
        m=CELL_ID.fullmatch(name) if type(name) is str else None
        require(m is not None and name not in seen,
                "COMPOSITION_CELL_ID_INVALID_OR_DUPLICATED")
        seen.add(name)
        r,c=map(int,m.groups())
        require(r<180 and c<360 and name in ids,
                "COMPOSITION_CELL_NOT_PROVEN_ADMITTED")
        plate=item["plate_id"];crust=item["crust_domain_id"]
        require(type(plate) is int and type(crust) is int and
                plate==int(grid[r,c]) and crust==int(domain[r,c]),
                "COMPOSITION_PLATE_OR_CRUST_SOURCE_BINDING_MISMATCH")
        key=item["recipe_or_mixture_id"]
        candidate=recipes.get(key) or mixtures.get(key)
        require(candidate is not None,
                "COMPOSITION_PLACEMENT_RECIPE_NOT_IDENTIFIED")
        role=candidate["role"]
        require((crust==1 and role=="OCEANIC_CRUST_BULK") or
                (crust in (2,3,4,5,6) and role=="CONTINENTAL_CRUST_BULK"),
                "COMPOSITION_CRUST_ROLE_MISMATCH_OR_NONCRUST_DISALLOWED")
        out.append({"cell_id":name,"plate_id":plate,"crust_domain_id":crust,
            "bulk_composition_hypothesis_id":key,
            "candidate_only_not_observed_rock":True,
            "physical_mineralogy":None,"actual_fluid_state":None})
    return out


def compile_scenario(sc,root,*,field_package=None,plate_partition=None,
                     admitted_membership=None,plate_array_key=None):
    idx=source_index(root)
    require(type(sc) is dict and sc.get("schema")==SCHEMA and
            sc.get("authority")==AUTHORITY and
            sc.get("parent_grid")==idx["grid"]["grid_id"] and
            sc.get("field_package_sha256")==FIELD_SHA and
            sc.get("plate_partition_sha256")==PLATE_SHA and
            sc.get("canonical_T0_materialization_authorized") is False and
            sc.get("mechanical_solve_authorized") is False and
            sc.get("physical_T1") is None,
            "COMPOSITION_SCENARIO_AUTHORITY_OR_PARENT_INVALID")
    require(all(type(sc.get(k)) is list for k in
                ("recipes","mixtures","placements")),
            "COMPOSITION_SCENARIO_COLLECTIONS_MISSING")
    rec={}
    for row in sc["recipes"]:
        x=oxide_recipe(row)
        require(x["id"] not in rec,"COMPOSITION_RECIPE_DUPLICATED")
        rec[x["id"]]=x
    mixtures={}
    for row in sc["mixtures"]:
        x=mix(row,rec)
        require(x["id"] not in mixtures and x["id"] not in rec,
                "COMPOSITION_MIXTURE_DUPLICATED")
        mixtures[x["id"]]=x
    sites=source_placements(sc["placements"],sc,idx,rec,mixtures,
         field_package=field_package,plate_partition=plate_partition,
         admitted_membership=admitted_membership,plate_array_key=plate_array_key)
    return {"schema":RESULT_SCHEMA,
        "decision":"AUTHORIAL_BULK_OXIDE_HYPOTHESES_ONLY_NO_CANONICAL_GEOLOGY",
        "scenario_id":sc.get("scenario_id"),
        "authorial_selection_id":sc.get("authorial_selection_id"),
        "source_B6N8N_index_sha256":sha((root/INDEX).read_bytes()),
        "source_exact_membership_sha256":
             idx["membership_sha256"]["ADMITTED_INITIALIZER_SUPPORT"],
        "source_original_field_package_sha256":FIELD_SHA,
        "source_original_plate_partition_sha256":PLATE_SHA,
        "native_cell_count":64800,
        "thermal_eligible_support_not_geochemical_support":63620,
        "experimental_recipe_records":list(rec.values()),
        "experimental_mass_mixture_records":list(mixtures.values()),
        "hypothetical_native_cell_assignments":sites,
        "hypothetical_native_cell_assignment_count":len(sites),
        "physically_ratified_T0_composition_cell_count":0,
        "physical_T0_bulk_chemistry":None,
        "physical_T0_mineral_phases":None,
        "fault_gouge_mineralogy_hydration":None,
        "crust_mantle_phase_equilibrium":None,
        "ore_deposits_and_resources":None,
        "Deep_mode_accessibility":None,
        "geological_mass_transport_history":None,
        "mechanical_solve_authorized":False,
        "world_history_production_authorized":False,
        "D_024":"ACTIVE","physical_T1":None}


def write_once(path,bytes_):
    require(not path.exists(),"COMPOSITION_OUTPUT_EXISTS_NO_OVERWRITE")
    path.write_bytes(bytes_)


def write_report(out,report,scenario_bytes):
    require(not out.exists(),"COMPOSITION_OUTPUT_EXISTS_NO_OVERWRITE")
    out.mkdir(parents=True,exist_ok=False)
    rp=out/"REPORT.json"
    rp.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_T0_BULK_COMPOSITION_HYPOTHESIS_MANIFEST_V1",
        "source_scenario_sha256":sha(scenario_bytes),
        "files":{"REPORT.json":sha(rp.read_bytes())},
        "no_canonical_promotion":True,
        "no_physical_materialization":True,
        "no_mechanical_solve":True,"no_T1":True,
        "no_world_history":True},indent=2)+"\n")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[2])
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--template-out",type=Path)
    g.add_argument("--scenario",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--field-package",type=Path)
    ap.add_argument("--plate-partition",type=Path)
    ap.add_argument("--admitted-membership",type=Path)
    ap.add_argument("--plate-array-key")
    a=ap.parse_args()
    if a.template_out is not None:
        require(a.output is None,"COMPOSITION_TEMPLATE_REPORT_CONFLICT")
        write_once(a.template_out,(json.dumps(make_template(a.repo_root),indent=2)+"\n").encode())
        print(json.dumps({"status":"EMPTY_AUTHORIAL_SCENARIO_TEMPLATE","T0_compositions":0,"physical_T1":None}))
    else:
        require(a.output is not None,"COMPOSITION_OUTPUT_REQUIRED")
        raw=a.scenario.read_bytes()
        result=compile_scenario(json.loads(raw),a.repo_root,
            field_package=a.field_package,plate_partition=a.plate_partition,
            admitted_membership=a.admitted_membership,
            plate_array_key=a.plate_array_key)
        write_report(a.output,result,raw)
        print(json.dumps({"decision":result["decision"],
              "candidate_recipes":len(result["experimental_recipe_records"]),
              "candidate_mixtures":len(result["experimental_mass_mixture_records"]),
              "hypothetical_native_assignments":result["hypothetical_native_cell_assignment_count"],
              "physical_T0_assignments":0,"physical_T1":None}))


if __name__=="__main__":main()
