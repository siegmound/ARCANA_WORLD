"""C08 offline constitution and constraint study. No solver or evolution."""
import argparse
import json
import math
from pathlib import Path

from experiments.plate58_deforming_explore_v1 import prepare as plate
from experiments.r6_thermo_provider_pilot_v1 import c08_constitutive as g2
from experiments.r6_thermo_provider_pilot_v1 import c08_mechanics as g3
from experiments.r6_thermo_provider_pilot_v1 import run_c07_native_physical_configuration as c07

ENTRY = "1bad34e117e41da27fe0d1890358ceb324220850"
PIN = "7503dd802bea400749d8543fc3f39cc74a945f9eb23b9bca9838f62a78212149"
PARENT_SCHEMA = "R6_C07_NATIVE_PHYSICAL_CONFIGURATION_MANIFEST_V1"
STATUS = "C08_REGIONAL_CONSTITUTIVE_AND_MECHANICAL_CANDIDATES_EVALUATED__AUTHORIAL_SELECTION_REQUIRED"
OUT = c07.BASE/"R6_THERMO_C08_REGIONAL_CONSTITUTIVE_MECHANICAL_CLOSURE_NEW01"
HERE = Path(__file__).resolve().parent
RECEIPT = HERE/"c07_fair_receipt_v1.json"
need, read, sha = c07.need, c07.read, c07.sha
SCOPE = c07.SCOPE
C07_MEMBERS = {
    "C06_REPLAY.json","ORTHOGONAL_GEOLOGICAL_SUPPORT.json",
    "EXISTING_PHYSICAL_AUTHORITY_MATRIX.json","NATIVE_SHELLSET_CONFIGURATION_CANDIDATE.json",
    "NODAL_STATE_CROSSWALK.json","CONSTITUTIVE_AND_FAULT_CLOSURE.json",
    "REGIONAL_MECHANICAL_CLOSURE.json","TARGETED_HIGH_FIDELITY_REFINEMENT_REQUIREMENTS.json",
    "AUTHORIAL_DECISION_SHEET.json",
}


def verify_c07(folder):
    receipt = read(RECEIPT)
    need(receipt["source_sha"] == ENTRY and receipt["manifest_sha256"] == PIN
         and receipt["archive"] == folder.name and receipt["status"] == c07.STATUS
         and receipt["regression_passed"] == receipt["regression_total"] == 719
         and receipt["explicit_C07_EXIT_marker_supplied"] is False and receipt["exit"] is None,
         "C08_C07_RECEIPT")
    path = folder/"MANIFEST.json"
    need(folder.is_dir() and not folder.is_symlink() and path.is_file()
         and not path.is_symlink() and sha(path) == PIN, "C08_C07_MANIFEST_PIN")
    manifest = read(path)
    files = c07.c06.inventory(folder)
    files.pop("MANIFEST.json")
    need(set(manifest) == {"schema","source_sha","C06_manifest_sha256","status","candidate_sha256","files",*SCOPE}
         and files == manifest["files"] and set(files)==C07_MEMBERS
         and manifest["schema"]==PARENT_SCHEMA and manifest["source_sha"]==ENTRY
         and manifest["status"]==c07.STATUS and manifest["C06_manifest_sha256"]==c07.PIN
         and manifest["candidate_sha256"]==sha(c07.CANDIDATE)
         and all(manifest[k]==v for k,v in SCOPE.items()), "C08_C07_INVENTORY_SCOPE")
    return receipt, manifest, {name: read(folder/name) for name in sorted(files)}


def replay(root):
    receipt, manifest, prior = verify_c07(c07.OUT)
    rebuilt = json.loads(json.dumps(c07.build(root), allow_nan=False))
    need(rebuilt == prior, "C08_C07_REPLAY_DRIFT")
    targeted = prior["TARGETED_HIGH_FIDELITY_REFINEMENT_REQUIREMENTS.json"]
    need(targeted["comparative_identities"]==951 and targeted["executable_new_queries"]==0,
         "C08_COMPARATIVE_IDENTITY_DRIFT")
    return prior, {"reported":receipt,"inventory":manifest["files"],
                   "reconstructed_all_members":sorted(rebuilt),
                   "parent_C06_manifest_sha256":manifest["C06_manifest_sha256"],
                   "retained_library_state_count":35,"retained_comparative_queries":951,
                   "operator_exit":None, **SCOPE}


def pinned(path, pin):
    need(path.is_file() and not path.is_symlink() and sha(path)==pin,
         "C08_SOURCE_PIN:"+path.name)
    return path


def primary_inputs(root):
    packet = c07.BASE/"R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02"
    pin = "168549374cdcb17fc3fe88651b89da55a49ffb5a75f660ef4b711fda4136713e"
    pinned(packet/"MANIFEST.json", pin)
    index, _, _ = c07.c06.handoff.load_packet(packet, 8)
    hashes = index["source_hashes"]
    outer = c07.PACKET
    m = read(pinned(outer/"MANIFEST.json",hashes["multiscale_manifest_sha256"]))
    layout = read(pinned(outer/"CONTINUATION_A.json",m["files"]["CONTINUATION_A.json"]))
    extent, = (r for r in layout["topological_comparative_extents"] if r["cell_extent_per_side"]==8)
    feg = pinned(outer/"OUTER_A_08x08.feg", hashes["original_FEG_sha256"])
    pre = pinned(outer/"OUTER_A_08x08_PRE_T0_PASSIVE.dat", hashes["original_PRE_sha256"])
    lines = pre.read_text().splitlines()
    fields = extent["PRE_source_field_order"]
    source_profiles = index["source_original_PRE_model_T0_thermal_profiles_by_parent_node"]
    need(len(lines)==82 and len(fields)==51 and extent["parent_node_ids"]==index["original_parent_node_order"],
         "C08_PRE_INVENTORY")
    for row, parent in zip(lines[1:],index["original_parent_node_order"],strict=True):
        key, *values = row.split()
        record = dict(zip(fields[1:],map(float,values),strict=True))
        need(key==str(parent) and all(record[k]==v for k,v in source_profiles[key].items()),
             "C08_PRE_PROFILE_DRIFT")
    euler_pin = "0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2"
    euler = read(pinned(root/plate.EULER,euler_pin))
    need(euler["parent_vector_partition_sha256"]==layout["source_vector_partition_sha256"],
         "C08_EULER_PARTITION")
    dt_pin = "2a0a2919c293a4e1367dfbd3a9c5da65d25ccd2cf1a2f28fbf3c7d3e8e311cd6"
    dt = read(pinned(root/"outputs/r6_b6j_first_dt_adjudication/B6J_DT_SELECTION.json",dt_pin))
    need(dt["unit"]=="year" and dt["limiting_event"]=="RIFT_PROCESS_ACTIVATION",
         "C08_KINEMATIC_AUTHORITY")
    return index, extent, source_profiles, feg, euler, {
        "source_packet_manifest":pin, "original_regions":hashes,
        "Euler_sha256":euler_pin,"T0_first_segment_sha256":dt_pin,
        "exclusive_kinematic_upper_bound_model_year":dt["value"],
        "actual_selected_dt_year":None, "first_event":dt["limiting_event"],
    }


def source_evidence(quartz):
    bhq = quartz["BHQ"]
    hk = quartz["dry_olivine"]
    return {
        "BHQ":{"as_published":bhq, "doi":"10.1016/0040-1951(95)00011-B",
               "equation":"eps_axial=A_MPa * Delta_sigma_MPa^n * exp(-Q/RT) at published confining condition",
               "nominal_ASPECT_prefactor_Pa_minus_n_s_inv":g2.invariant_prefactor(g2.sources.GT_A_MPA,g2.sources.GT_N),
               "activation_volume_m3_mol":None,"absolute_P_at_T0":None},
        "wet_quartz":{"as_published":quartz["wet_quartz"],"doi":"10.1007/s005310000152",
                      "law":"eps_axial=A*f_H2O_MPa^m*Delta_sigma_MPa^n*exp(-Q/RT)",
                      "experimental_T_screen_doi":"10.1016/j.epsl.2018.10.017",
                      "mechanism_dependence":"fabric and pressure can change regime; T overlap alone is triage",
                      "bulk_water_to_fugacity_model":None,"pore_pressure_relation":None,
                      "sensitivity_at_fixed_other_inputs":"A tenfold fugacity change alters predicted stress by a factor 10^(-1/4)=0.56234; no absolute fugacity assigned."},
        "low_temperature_quartz":{"doi":"10.1029/2025JB032753","dataset_doi":"10.5061/dryad.rbnzs7hqv",
                                  "experiment_confining_pressure_Pa":[1.39e9,3.1e9],
                                  "dataset_runs":13,"dataset_T_K":[298.15,1472.15],
                                  "dataset_rate_s_inv":[1e-6,1e-5],
                                  "license":"Consult the version of record; metadata only used in C08",
                                  "observed_mechanism":"Low-T lattice resistance, Guyot-Dorn comparison below 800 C",
                                  "application":"Reference only. Pressure floor exceeds all primary crust overburden proxies. Field composition, pressure and mechanism transition unbound."},
        "mantle":{"as_published_benchmark":hk,"doi":"10.1029/138gm06",
                  "law":"eps_II=A_Pa sigma_II^n exp(-(E+P V)/(RT))",
                  "pressure_series":{"doi":"10.1029/2018JB015853","T_K":1373,"rate_s_inv":1e-5,
                                     "P_Pa":[1.8e9,8.8e9],"V_m3_mol_nominal_spread":[15e-6,5e-6]},
                  "warm_T_screen_K":g2.WARM_T,"conditional_V_choices_m3_mol":g2.V_CASES,
                  "high_T_reference":"https://doi.org/10.1007/s00269-016-0805-x",
                  "mantle_LTP_reference":"https://doi.org/10.1029/2018JB016736",
                  "mechanism":"Dry dislocation only. Diffusion branch requires material/water/grain size, and shallower plasticity requires independent support.",
                  "geological_rate_extrapolation":"Mandatory even inside analogue T and overburden limits; no experimental joint validity asserted"},
        "friction":{"doi":"10.1007/BF00876528","catalog":"https://pubs.usgs.gov/publication/70012542",
                    "branches":"Engineering analogue tau=0.85 sigma_eff to 200 MPa, 50 MPa + 0.6 sigma_eff above",
                    "variables":"sigma_eff=sigma_n-Biot*p_f. Wetting, sliding gouge and fault geometry unbound.",
                    "results_scope":"Dry/hydrostatic sliding sensitivities with unit normal/lithostatic ratio. No conversion to native cFric or fFric."},
        "raw_transient_curves":{"doi":"10.5281/zenodo.8304793","license":"See original repository rights; no redistribution",
                                "sha256":quartz["raw_curve_archive_sha256"],"rows":555,
                                "independent_new_steady_rate_pairs":0},
        "external_data_policy":"Public article/dataset metadata only. No third-party files mirrored. 19-run published supplement overlaps pre-existing laboratories; no independent fitted holdout established.",
        "wet_quartz_compilation":"https://d197for5662m48.cloudfront.net/documents/publicationstatus/109772/preprint_pdf/a66302abdaad1a8bc3ae4ea7b794b3bd.pdf",
        **SCOPE,
    }


def build(root):
    old, evidence = replay(root)
    index, extent, profiles, feg, euler, forcing = primary_inputs(root)
    xwalk = old["ORTHOGONAL_GEOLOGICAL_SUPPORT.json"]["regions"]["8"]["nodes"]
    initial = old["NATIVE_SHELLSET_CONFIGURATION_CANDIDATE.json"]
    c07.validate_thermal_mode(initial["proposed_policy"])
    params = source_evidence(old["CONSTITUTIVE_AND_FAULT_CLOSURE.json"]["research_candidates"] | {
        "raw_curve_archive_sha256":old["CONSTITUTIVE_AND_FAULT_CLOSURE.json"]["raw_curve_archive_sha256"]})
    assessment = read(root/c07.PLATE/"R6_G2_G3_CALIBRATION_ASSESSMENT_20261120.json")
    rates = assessment["source_records"]["kinematic_rate_proxies_s_inv"]
    gravity = initial["parameters"]["gMean"]["value"]
    rho_water = initial["parameters"]["reference_densities"]["seawater"]["nominal"]
    depth, strength, comparison = g2.assess_columns(profiles,rates,gravity,rho_water,SCOPE)
    depth["native_Moho_PT_projection"] = g2.integration_point_thermal(root,index,profiles,sha)
    depth["crust_overburden_range_at_Moho_Pa"] = g2.summary([
        x["layers"]["crust"]["overburden_proxy_Pa"][-1] for x in depth["nodes"].values()])
    depth["native_geological_counts"] = old["ORTHOGONAL_GEOLOGICAL_SUPPORT.json"]["regions"]["8"]["counts"]
    depth["BHQ_reference_pressure_Pa"] = params["BHQ"]["as_published"]["P_reference_GPa"]*1e9
    comparison["existing_separate_exponent_implementation"] = str(c07.PLATE/"nonlinear_layered_g3.py")
    comparison["mantle_rate_log10_ratio_to_Dixon_lab"] = {
        k: math.log10(v/1e-5) for k,v in rates.items()}
    params["local_evidence_sha256"] = {str(path):sha(root/path) for path in (
        c07.PLATE/"shells_lr_bridge.py", c07.PLATE/"full_column.py",
        c07.PLATE/"nonlinear_layered_g3.py", c07.PLATE/"g2_g3_empirical_calibration.py",
        c07.PLATE/"R6_G2_G3_CALIBRATION_ASSESSMENT_20261120.json",
        c07.PLATE/"PHYSICAL_EXPERIMENT_DECISION_PROPOSAL.json",
        Path("src/arcana_worldsim/r6/material_rheology_provider.py"),
        Path("external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90"),
    )}
    boundaries, ranks = g3.boundary(index,xwalk,euler,feg,extent,SCOPE)
    depth["kinematic_rate_provenance"] = {
        "prior_assessment_sha256":sha(root/c07.PLATE/"R6_G2_G3_CALIBRATION_ASSESSMENT_20261120.json"),
        "matched_contact_ids":list(plate.SOURCE_CONTACT_IDS),
        "regional_contact_component_ranges_m_year": {
            key:g2.summary([x[key] for x in boundaries["contact_kinematic_priors"]])
            for key in ("opening_m_year","along_contact_m_year")},
        "rates_choose_no_width":True,
    }
    basal = g3.basal_and_density(root,SCOPE)
    decisions = {
        "native_initialization":initial, "forcing_provenance":forcing,
        "recommended_next_configuration":{
            "support":"8x8 original shared FEG continuum, 16x16 domain sensitivity only",
            "distal":"Full distal Euler components, review numerical frame and authorize far-field use.",
            "north_south":"Physically closed exterior continuation A or a justified outer load. Internal contact reaches both cuts with changing orientation; current forcing does not support periodic or uniform along-contact continuation.",
            "basal":"Approve distinct mechanical support, mantle frame and tangential law or a declared decoupled limiting case with normal support.",
            "continuum_assumptions":"Approve strain accommodation width and stress closure. No sided contact; reconsider sided geometry if required by the scientific question.",
            "configuration_executable":False},
        "candidate_rheology":{"mantle":params["mantle"],"crust":params["BHQ"],
                              "wet_alternative":params["wet_quartz"], "friction":params["friction"],
                              "eCreep_screen":comparison["common_e_candidates"],
                              "chosen_a_b_c_d_e":None,"cold_crust_law":None,"cFric":None,"fFric":None,
                              "Biot":None,"Byerly":None,"visMax":None},
        "selection_requires":[
            "Agree separately on lithology, water, effective-pressure model and constitutive mechanisms. A mantle benchmark choice changes the eligible resistance envelope; it does not fill the crust gap.",
            "Confirm the N/S continuation and basal model jointly. Admissible distal velocities suppress rigid rotations, but cannot determine work and reactions at unsupported cuts.",
            "Tie a constitutive reduction tolerance to reaction/work/strain budgets, then qualify full native tensor or existing separate-exponent route. Neither numerical comparison ratifies a material.",
            "Keep the coupled route independent and conditional on stronger data needs. Preserve all 35 states and 951 comparisons."],
        "route_decision":{
            "native_SHELLS":"Smallest eventual solve if full-column engineering error and physical laws are accepted. Exact nominal two-exponent fit is impossible across rates.",
            "separate_exponents":"Existing research machinery preserves individual rate laws but requires a physical cold crust branch, matching invariants, exterior loads and separate operator qualification.",
            "coupled":"Deferred selective thermodynamics where phase or EOS properties matter; requires pressure/fluid and all existing groups."},
        **SCOPE,
    }
    return {"C07_REPLAY.json":evidence,"CONSTITUTIVE_SOURCE_EVIDENCE.json":params,
            "REGIONAL_PT_RATE_SUPPORT.json":depth,"WHOLE_COLUMN_STRENGTH_CANDIDATES.json":strength,
            "NATIVE_COMMON_EXPONENT_COMPARISON.json":comparison,
            "REGIONAL_BOUNDARY_CONDITION_CANDIDATES.json":boundaries|{"source_pins":forcing},
            "CONSTRAINT_RANK_AND_GAUGE_ANALYSIS.json":ranks,"BASAL_SUPPORT_AND_FORCE_OWNERSHIP.json":basal,
            "AUTHORIAL_PHYSICAL_DECISION_SHEET.json":decisions}


def write_once(output, reports, head):
    need(not output.exists() and not output.is_symlink(), "C08_OUTPUT_EXISTS")
    need(all(Path(name).name==name and name!="MANIFEST.json"
             and all(value.get(k)==v for k,v in SCOPE.items())
             for name,value in reports.items()), "C08_OUTPUT_SCOPE")
    body = {name:json.dumps(value, sort_keys=True, allow_nan=False, separators=(",",":"))+"\n"
            for name,value in reports.items()}
    output.mkdir(exist_ok=False)
    for name,value in body.items():
        with (output/name).open("x", encoding="utf-8") as handle:
            handle.write(value)
    c07.c06.prior.s2.write_json(output/"MANIFEST.json", {
        "schema":"R6_C08_REGIONAL_CONSTITUTIVE_MECHANICAL_CLOSURE_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"C07_manifest_sha256":PIN,
        "receipt_sha256":sha(RECEIPT),"files":c07.c06.inventory(output),**SCOPE})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--offline-regional-closure-only", action="store_true", required=True)
    args = parser.parse_args()
    s2 = c07.c06.prior.s2
    root, head = s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"), "C08_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink() and not OUT.resolve().is_relative_to(root),
         "C08_OUTPUT_EXISTS_OR_IN_REPO")
    write_once(OUT,build(root),head)
    print("C08_MANIFEST_SHA256",sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS,flush=True)


if __name__ == "__main__":
    main()
