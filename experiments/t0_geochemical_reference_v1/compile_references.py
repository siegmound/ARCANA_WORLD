"""R6 T0 geological composition research: pinned Earth analogue tables.

Actual continental/basalt/mantle chemistry is not identifiable from R6
thermal/density reference role codes. Compile unassigned reference Earth bulk
major-oxide and element budgets; preserve FeO* as FeO-equivalent, not redox.
No mineral phase, hydration/pressure, tectonic mechanics, ore or Deep mapping.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

DECISION = "REAL_EARTH_BULK_GEOCHEMISTRY_LIBRARY__R6_T0_COMPOSITION_UNASSIGNED"
SCHEMA = "ARCANA_R6_T0_EARTH_GEOCHEMICAL_REFERENCE_LIBRARY_V1"
ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent / "data"
SOURCES = {
    "CC__Rudnick_Gao__2014.csv":
        "4127120d7499e3d9b62a22384465c39b8806aaf0",
    "DM__Salters_Stracke__2004.csv":
        "262447b687f5cae36fde836ffd12c7d439a9f16b",
}
R6_SOURCES = {
    "docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json":
        "e06770577ebaf549aa113a4e72ec9f6095a29c2d",
    "docs/arcana/research/B6N8L_SUPPORT_MATERIAL_BINDING_MATRIX.json":
        "2c6ff8f755afb91445fe229b2edef416b835bcec",
    "docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json":
        "6e51db00a5df691f8021097af4ff4929fabe8691",
}
CANON_SOURCE_SHAS = {
    "CANON/12_DEEP_ENERGY_GEOGRAPHY_EXTRACTION_AND_TRANSPORT.md":
        "d82eba8b048cbb54eb80c9b54c34a35e8ce1dcc40abc6822ba31ae62f645d983",
    "CANON/53_MATERIAL_COUPLING_AND_CONSTITUTIVE_RESPONSE_CANDIDATE.md":
        "d8e2ec657e03a54c0b845e38a71a3286c5a3725df45b0662508d07b4c22b32ad",
    "CANON/57_MATERIAL_PROPERTY_LIBRARY_AND_MODE_ACCESS_NUMERICAL_CALIBRATION_CANDIDATE.md":
        "c43c782db49d0b9e0c9785cb5fd39707a2090efce6eb5f889727ec68bb0d655c",
}
CONTINENTAL_CATEGORIES = ("Upper continental crust","Middle continental crust",
                           "Lower continental crust","Bulk continental crust")
MAJOR_OXIDES = ("SiO2","TiO2","Al2O3","FeO*","MnO","MgO","CaO","Na2O",
                "K2O","P2O5")
MANTLE_OXIDES = ("SiO2","Al2O3","FeO","MgO","CaO","Na2O")
ATOMIC_WEIGHTS = {"O":15.999,"Si":28.085,"Ti":47.867,"Al":26.9815385,
                  "Fe":55.845,"Mn":54.938044,"Mg":24.305,"Ca":40.078,
                  "Na":22.98976928,"K":39.0983,"P":30.973761998}
OXIDE_FORMULAS = {
    "SiO2":{"Si":1,"O":2},"TiO2":{"Ti":1,"O":2},
    "Al2O3":{"Al":2,"O":3},"FeO*":{"Fe":1,"O":1},
    "FeO":{"Fe":1,"O":1},"MnO":{"Mn":1,"O":1},
    "MgO":{"Mg":1,"O":1},"CaO":{"Ca":1,"O":1},
    "Na2O":{"Na":2,"O":1},"K2O":{"K":2,"O":1},
    "P2O5":{"P":2,"O":5},
}

class GeochemistrySourceError(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise GeochemistrySourceError(code)


def git_blob_sha(raw:bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()


def source_bytes(path:Path, expected_git_blob:str) -> tuple[bytes,str]:
    raw=path.read_bytes()
    need(git_blob_sha(raw)==expected_git_blob,
         "GEOCHEM_SOURCE_GIT_BLOB_SHA_MISMATCH:"+path.name)
    return raw,hashlib.sha256(raw).hexdigest()


def positive_number(raw:str, code:str, *, allow_zero=True) -> float:
    try: x=float(raw)
    except (TypeError,ValueError) as exc:
        raise GeochemistrySourceError("GEOCHEM_INVALID_"+code) from exc
    need(math.isfinite(x) and (x>=0 if allow_zero else x>0),
         "GEOCHEM_INVALID_"+code)
    return x


def elemental_oxide_budget(oxides:dict[str,float]) -> dict:
    """Analytic oxide-equivalent element budget, NOT normative mineral phases."""
    elements={}
    total=sum(oxides.values())
    need(0<total<110,"GEOCHEM_MAJOR_OXIDE_SUM_INVALID")
    for oxide,wt in oxides.items():
        need(oxide in OXIDE_FORMULAS,
             "GEOCHEM_UNKNOWN_OXIDE_STOICHIOMETRY")
        fraction=positive_number(wt,oxide)
        stoich=OXIDE_FORMULAS[oxide]
        mw=sum(ATOMIC_WEIGHTS[e]*count for e,count in stoich.items())
        for element,count in stoich.items():
            elements[element]=elements.get(element,0.)+fraction*(
                count*ATOMIC_WEIGHTS[element]/mw)
    need(abs(sum(elements.values())-total)<1e-9,
         "GEOCHEM_ELEMENT_OXIDE_MASS_BALANCE_FAILED")
    return {
        "source_major_oxide_subset_total_wt_percent":total,
        "oxide_equivalent_element_mass_wt_percent":dict(sorted(elements.items())),
        "oxide_to_element_budget_conserved":True,
        "not_normalized_to_100":True,
        "oxygen_from_FeO_equivalent_is_not_Fe_redox":True,
        "normative_mineral_modal_percent":None,
        "unaccounted_components_and_volatiles_wt_percent":None,
    }


def continental_reference(raw:bytes) -> list[dict]:
    text=raw.decode("utf-8-sig")
    need("Rudnick and Gao, 2014" in text,
         "GEOCHEM_CONTINENTAL_SOURCE_HEADER_INVALID")
    lines=[s for s in text.splitlines() if s.strip() and
           not s.lstrip().startswith("#")]
    rows=list(csv.DictReader(io.StringIO("\n".join(lines))))
    need(rows and set(rows[0])==set(("Element","Unit",*CONTINENTAL_CATEGORIES)),
         "GEOCHEM_CONTINENTAL_CSV_SCHEMA_INVALID")
    index={}
    for row in rows:
        elem=row["Element"].strip()
        need(elem and elem not in index,
             "GEOCHEM_CONTINENTAL_DUPLICATE_ELEMENT")
        index[elem]=row
    need(all(k in index and index[k]["Unit"]=="wt.%" for k in MAJOR_OXIDES),
         "GEOCHEM_CONTINENTAL_MAJOR_OXIDE_UNITS_INCOMPLETE")
    reports=[]
    for name in CONTINENTAL_CATEGORIES:
        ox={k:positive_number(index[k][name],"OXIDE_"+k) for k in MAJOR_OXIDES}
        traces={}
        for key in ("Li","Cr","Ni","Cu","Th","U"):
            if key in index:
                v=index[key][name].strip()
                if v:
                    need(index[key]["Unit"] in ("ug/g","ng/g"),
                         "GEOCHEM_TRACE_UNITS_UNKNOWN")
                    traces[key]={"value":positive_number(v,"TRACE_"+key),
                                 "unit":"ppm" if index[key]["Unit"]=="ug/g"
                                        else "ppb"}
        reports.append({"reference_id":"EARTH_RG2014_"+name.upper().replace(" ","_"),
            "reference_scope":name,
            "authority":"PUBLISHED_EARTH_RESERVOIR_ESTIMATE_ANALOGUE",
            "doi":"10.1016/B978-0-08-095975-7.00301-6",
            "source_major_oxides_wt_percent":ox,
            "selected_source_trace_elements":traces,
            "estimated_bulk_chemistry_not_measured_local_rock":True,
            "physical_rock_phase_assemblage":None,
            "arcana_cell_assignments":0,
            "arcana_fault_assignments":0,
            "mass_budget":elemental_oxide_budget(ox)})
    return reports


def depleted_mantle_reference(raw:bytes) -> dict:
    text=raw.decode("utf-8-sig")
    need("Salters" in text and "2004" in text
         and "10.1029/2003GC000597" in text,
         "GEOCHEM_MANTLE_SOURCE_HEADER_INVALID")
    lines=[s for s in text.splitlines() if s.strip() and
           not s.lstrip().startswith("#")]
    rows=list(csv.DictReader(io.StringIO("\n".join(lines))))
    need(rows and set(rows[0])==set((
         "Element","Model","Unit","Constraint","Uncertainty in %")),
         "GEOCHEM_MANTLE_CSV_SCHEMA_INVALID")
    records={}
    for row in rows:
        element=row["Element"].strip()
        need(element and element not in records,"GEOCHEM_MANTLE_DUPLICATE_ELEMENT")
        records[element]=row
    need(all(k in records and records[k]["Unit"]=="wt%"
         for k in MANTLE_OXIDES),
         "GEOCHEM_MANTLE_MAJOR_OXIDE_UNITS_INCOMPLETE")
    ox={k:positive_number(records[k]["Model"],"MANTLE_"+k)
        for k in MANTLE_OXIDES}
    need("H2O" in records and records["H2O"]["Unit"]=="ppm",
         "GEOCHEM_MANTLE_H2O_MODEL_SOURCE_MISSING_OR_WRONG_UNITS")
    h2o=positive_number(records["H2O"]["Model"],"MANTLE_H2O")
    return {
        "reference_id":"EARTH_SALTERS_STRACKE_2004_DEPLETED_MORB_MANTLE",
        "authority":"PUBLISHED_MODELED_EARTH_MANTLE_RESERVOIR_ANALOGUE",
        "doi":"10.1029/2003GC000597",
        "source_major_oxides_wt_percent":ox,
        "water_model":{"H2O_mass_concentration_ppm":h2o,
             "source_constraint":records["H2O"]["Constraint"],
             "source_uncertainty_percent":
                 positive_number(records["H2O"]["Uncertainty in %"],"H2O_UNCERTAINTY"),
             "IS_NOT_ARCANA_PORE_PRESSURE_OR_MANTLE_HYDRATION":True},
        "physical_rock_phase_assemblage":None,
        "arcana_cell_assignments":0,"arcana_fault_assignments":0,
        "mass_budget":elemental_oxide_budget(ox),
    }


def read_r6_support(repo_root:Path) -> dict:
    docs={}
    for filename,git_sha in R6_SOURCES.items():
        raw,_=source_bytes(repo_root/filename,git_sha)
        docs[Path(filename).stem]=json.loads(raw)
    index=docs["B6N8N_ADMITTED_SUPPORT_BINDING_INDEX"]
    matrix=docs["B6N8L_SUPPORT_MATERIAL_BINDING_MATRIX"]
    roles=docs["B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY"]
    part=index["partition_counts"]
    inventory=matrix["spatial_inventory"]
    need(part["native"]==inventory["native_cell_count"]==64800
         and part["admitted"]==63620
         and part["continental"]==inventory["continental_thermal_support_cells"]==14258
         and part["positive_age_ocean_admitted"]==
             inventory["ocean_positive_age_hwr_eligible_cells"]==49362
         and part["unresolved_positive_age_ocean_excluded"]==
             inventory["ocean_positive_age_excluded_or_unresolved_cells"]==1072
         and part["zero_age_ridge_excluded"]==
             inventory["age_zero_selected_ridge_cells"]==108
         and 14258+49362+1072+108==64800
         and 14258+49362==63620,
         "GEOCHEM_NATIVE_T0_THERMAL_SUPPORT_PARTITION_MISMATCH")
    need(set(roles["roles"])=={
         "CONTINENTAL_CRUST_REFERENCE","OCEANIC_CRUST_REFERENCE",
         "LITHOSPHERIC_MANTLE_REFERENCE"},
         "GEOCHEM_R6_MATERIAL_ROLE_REGISTRY_CHANGED")
    need(matrix["domain_id_semantics"]["continental_thermal_domain_id"][
             "composition_inference"] is False,
         "GEOCHEM_R6_THERMAL_CLASS_COMPOSITION_PROMOTION")
    need(all(row.get("material_role") is not None
         for row in matrix["support_rows"] if
         row.get("mapping")!="UNKNOWN"),
         "GEOCHEM_R6_SOURCE_ROLE_MISSING")
    return {"native_cells":64800,"thermal_support_admitted":63620,
            "continental_thermal_support":14258,
            "positive_age_ocean_thermal_support":49362,
            "geologically_unresolved_ocean_support":1072,
            "age_zero_ridge_excluded":108,
            "geochemical_composition_assigned_cells":0,
            "geochemical_composition_assigned_faults":0,
            "role_registry":sorted(roles["roles"]),
            "native_thermal_support_is_not_mineral_chemistry":True,
            "no_global_or_regional_mineral_facies_are_inferred":True}


def build(repo_root:Path,out:Path):
    need(not out.exists(),"GEOCHEM_OUTPUT_ALREADY_EXISTS")
    files={}
    for name,blob in SOURCES.items():
        raw,digest=source_bytes(repo_root/"experiments"/
                               "t0_geochemical_reference_v1"/"data"/name,blob)
        files[name]={"sha256":digest,"git_blob_sha":blob,"bytes":len(raw),
                     "source_upstream_commit":
                         "e82b70de1b65d8e9cde52166b93ebc88a50934b2"}
    cont=continental_reference((repo_root/"experiments"/
        "t0_geochemical_reference_v1"/"data"/
        "CC__Rudnick_Gao__2014.csv").read_bytes())
    mantle=depleted_mantle_reference((repo_root/"experiments"/
        "t0_geochemical_reference_v1"/"data"/
        "DM__Salters_Stracke__2004.csv").read_bytes())
    support=read_r6_support(repo_root)
    report={"schema":SCHEMA,"decision":DECISION,
       "Earth_reference_analogues":[*cont,mantle],
       "reference_records":5,
       "source_artifact_manifest":files,
       "R6_T0_spatial_material_support":support,
       "canon_read_only_source_sha256":CANON_SOURCE_SHAS,
       "canonical_role_not_sufficient_for_natural_lithology":True,
       "earth_references_are_not_210Ma_ARCANA_measurements":True,
       "bulk_oxide_chemistry_does_not_define_mineral_modal_fraction":True,
       "mantle_model_H2O_does_not_define_ARCANA_gouge_water":True,
       "no_oxide_to_friction_or_rheology_implicit_lookup":True,
       "no_ore_mineral_vein_or_deep_accessibility_inference":True,
       "requested_authority_to_assign_geology":"NONE",
       "planetary_composition_field_T0":None,
       "fault_mineralogy_hydration_porosity_pore_pressure":None,
       "geochemistry_to_thermo_phase_equilibrium_mapping":None,
       "ore_deposit_resource_field":None,
       "Deep_X_accessibility_field":None,
       "physical_T1":None,
       "D_024":"ACTIVE",
       "mechanical_solve_authorized":False,
       "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False}
    out.mkdir(parents=True,exist_ok=False)
    rp=out/"REPORT.json"
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2,
                             allow_nan=False)+"\n")
    digest=hashlib.sha256(rp.read_bytes()).hexdigest()
    (out/"MANIFEST.json").write_text(json.dumps({
       "schema":"ARCANA_R6_T0_GEOCH_REFERENCE_MANIFEST_V1",
       "decision":DECISION,"files":{"REPORT.json":digest},
       "pinned_earth_data_files":files,
       "no_canonical_promotion":True,"no_solver_run":True,"no_T1":True
    },indent=2)+"\n")
    return {"decision":DECISION,"earth_reference_records":len(cont)+1,
       "native_T0_cells":support["native_cells"],
       "thermal_support_cells":support["thermal_support_admitted"],
       "T0_composition_assignments":0,"T0_mineral_phase_assignments":0,
       "T0_fault_gouge_assignments":0,
       "D_024":"ACTIVE","physical_T1":None}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,default=ROOT)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(build(args.repo_root,args.output),indent=2))


if __name__=="__main__":
    main()
