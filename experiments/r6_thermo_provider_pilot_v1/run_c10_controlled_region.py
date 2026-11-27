"""C10 offline controlled-region deck and hard-stop native qualification."""
import argparse
import json
from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg

from experiments.r6_thermo_provider_pilot_v1 import c10_boundary as bc
from experiments.r6_thermo_provider_pilot_v1 import c10_native as native
from experiments.r6_thermo_provider_pilot_v1 import c10_vertical as vertical
from experiments.r6_thermo_provider_pilot_v1 import run_c09_physical_scenario as c09
from experiments.r6_thermo_provider_pilot_v1.run_c08_regional_closure import need, read, sha

ENTRY = "230193c12463c0301b02c9e5f45ac91e853a7de3"
PIN = "19c2b072d7b74dd8f707170e36de25b8d5fdf0a0777b896ae59909df2b2969c2"
DEV_PIN = "c09d80060c51a5ad516cb05b85366a31887b9cb95d86a8689311fa5aeabe10c0"
DEV = c09.OUT.with_name("R6_THERMO_C09_PHYSICAL_SCENARIO_DEVELOPMENT_NEW01")
OUT = c09.OUT.with_name("R6_THERMO_C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_NEW01")
STATUS = "C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_COMPLETE__AUTHORIAL_RATIFICATION_REQUIRED"
RECEIPT = Path(__file__).with_name("c09_fair_receipt_v1.json")
SCOPE = c09.SCOPE
PARENT_REPORTS = {
    "C08_REPLAY.json","SCIENTIFIC_AUTHORITY_CROSSWALK.json","PUBLISHED_CONSTITUTIVE_MODELS.json",
    "WHOLE_COLUMN_SCENARIO_COMPARISON.json","NATIVE_REDUCTION_ADEQUACY.json",
    "REGIONAL_GLOBAL_ROUTE_COMPARISON.json","BASAL_AND_BOUNDARY_SCENARIOS.json",
    "CANDIDATE_NATIVE_INPUT_PACKAGE.json","FIRST_SOLVE_ACCEPTANCE_PROTOCOL.json",
    "AUTHORIAL_RATIFICATION_SHEET.json",
}
VERTICAL_AUTHORITY = "R6_PRE_ORBDATA_CHEMICAL_DENSITY_MECHANICS_AUTHORITY.json"
VERTICAL_PIN = "5ea81cda7d9fa60c6600dc2a2a2da61262bce654cf06c232d3c1b94cdb17846a"


def verify_c09(folder, *, development=False):
    pin = DEV_PIN if development else PIN
    need(folder.is_dir() and not folder.is_symlink(),"C10_C09_ARCHIVE")
    manifest = read(c09.c08.pinned(folder/"MANIFEST.json",pin))
    files = c09.c08.c07.c06.inventory(folder)
    files.pop("MANIFEST.json")
    need(set(manifest)=={"schema","source_sha","C08_manifest_sha256","status","receipt_sha256",
                          "files","development_only",*SCOPE}
         and manifest["source_sha"]==ENTRY
         and manifest["schema"]=="R6_C09_PHYSICAL_SCENARIO_FIRST_SOLVE_PREPARATION_MANIFEST_V1"
         and manifest["C08_manifest_sha256"]==c09.PIN and manifest["receipt_sha256"]==sha(c09.RECEIPT)
         and manifest["status"]==c09.STATUS and manifest["development_only"] is development
         and set(files)==PARENT_REPORTS|c09.FRAGMENTS and files==manifest["files"]
         and all(manifest[k]==v for k,v in SCOPE.items()),"C10_C09_MANIFEST_INVENTORY")
    return files


def replay(root):
    receipt=read(RECEIPT)
    need(receipt["archive"]==c09.OUT.name and receipt["source_sha"]==ENTRY
         and receipt["manifest_sha256"]==PIN and receipt["status"]==c09.STATUS
         and receipt["regression_passed"]==receipt["regression_total"]==736
         and receipt["explicit_C09_EXIT_marker_supplied"] is False and receipt["exit"] is None,
         "C10_C09_OPERATOR_RECEIPT")
    files=verify_c09(c09.OUT)
    earlier=verify_c09(DEV,development=True)
    reports,native_files=c09.build(root)
    need(set(reports)==PARENT_REPORTS and set(native_files)==c09.FRAGMENTS,"C10_C09_REPLAY_INVENTORY")
    for k,v in reports.items():
        need(json.loads(json.dumps(v,allow_nan=False))==read(c09.OUT/k),"C10_C09_REPORT_REPLAY:"+k)
    for k,v in native_files.items():
        need(v.encode()==(c09.OUT/k).read_bytes(),"C10_C09_NATIVE_REPLAY:"+k)
    return reports,native_files,{
        "reported_qualification":receipt,"verified_files":files,"replayed_reports":sorted(reports),
        "native_byte_replay":sorted(native_files),
        "development_archive_manifest_sha256":DEV_PIN,"development_governance_verified":True,
        "development_verified_files":earlier,"retained_material_states":35,
        "retained_source_chemistries":14,"retained_comparative_query_identities":951,
        "C09_EXIT":None,**SCOPE}


def acceptance():
    return {
        "before_solver":["Ratify C10 scenario, branch, initial geometry, frame, selected trace and pore/vertical/basal choices.",
                         "Build the separately authorized continuation executable and prove same reader and precompute behavior. Save pre- and post-constraint operator and RHS with native order; inspect finite entries, actual free-DOF rank, conditioning and memory.",
                         "Set condition-scaled solve tolerances before inspection of solve results; proposed 120 s, 1 GiB aggregate and at most two MPI ranks for a later wrapper, subject to instrumentation. This pre-solve fixture is serial."],
        "fixed_checks":{
            "prescribed":"Match all 64 components in SI. Parser-only difference allowed <2e-22 m/s, based on angle serialization roundoff. Solver error uses condition-scaled linear backward error and the imposed motion scale.",
            "linear_backward_error":"Report ||A x-b||inf/(||A||inf||x||inf+||b||inf) for each linearization. Use audited operation count and a gamma_k roundoff floor; also check free equilibrium on a re-evaluated nonlinear operator.",
            "reaction":"Original unconstrained native residual on held components, opposite to the modeled force by sign convention. Compare independent side traction quadrature with mapped nodal work; separate native Fixed edge force from Dirichlet reaction.",
            "force_torque_work":"Sum force in common canonical XYZ and torque r cross F. Divide defects by sums of component magnitudes, with meaningful floor from resolved native loads. Work uses imposed velocity dot held reaction and native Fixed work separately. Match dissipation with sign/units and include all native internal terms.",
            "basal":"Assert exactly zero eta, tangential traction and work for selected free slip; preserve the nonzero normal reference anomaly in native GPE.",
            "pressures_caps":"Require finite effective pressures, track Biot choice, report negative beyond tolerance if present. Record dCreep and numeric visMax activation, numerical conditioning and sensitivity before interpreting rheology.",
            "independent_error_budget":"Predeclare application error budget for strain, work and accepted G4 geometry and material flux, then use tighter numerical criteria. C10 sets no empirical residual percentile or post-hoc threshold.",
            "sensitivity":"Compare linear versus smooth trace, hydrostatic Biot 1 versus dry Biot 0, and a tighter nonlinear threshold plus half/double okDelV. Do not compare different trace/hydro choices as solver regressions."},
        "G4_requires":["Accepted 1-year trial and 0.5-year same-start sensitivity only after checking actual gradients and event limit.",
                       "Canonical geometry, positive areas/Jacobians and thickness, explicit boundary flux for crust/mantle mass, preserve PRE owner lineage and chosen thermal transport.",
                       "Separate-process restart and replay from admissible state before any experimental T1 publication."],
        "equilibrium_alone_is_T1":False,**SCOPE}


def prepare(root):
    prior,files,evidence=replay(root)
    case=prior["CANDIDATE_NATIVE_INPUT_PACKAGE.json"]
    c08=c09.c08
    edges=read(c08.OUT/"REGIONAL_BOUNDARY_CONDITION_CANDIDATES.json")
    crosswalk=read(c08.c07.OUT/"ORTHOGONAL_GEOLOGICAL_SUPPORT.json")["regions"]["8"]["nodes"]
    traces,rank=bc.controlled_traces(case,edges)
    selected=traces["candidates"][bc.PREFERRED]["rows"]
    need(all(d["rank"]==64 and d["unconstrained_dof"]==98
             and d["remaining_rigid_rotation_modes"]==0 for d in rank.values()),"C10_CONSTRAINT_SCOPE")
    owner=native.reporting_plate_map(case,crosswalk)
    model=case["native_parameter_values_unselected"]
    need([model[k] for k in ("A_Pa_s_to_e","B_K","C_K_per_m","dCreep_Pa","eCreep","cFric")]
         ==[[1.38e6,2.23e4],[10524.,16494.],[.0079,.0104],[5e8,5e8],.267,.85],
         "C10_DIORITE2_COEFFICIENT_SCOPE")
    lr=native.lr_values(case["baseline"],model,1.)
    files |= {
        "controlled.bcs":bc.serialize_bc(selected),
        "linear_arc_sensitivity.bcs":bc.serialize_bc(traces["candidates"]["linear_arc"]["rows"]),
        "regional.in":native.serialize_lr(lr),
        "regional_dry.in":native.serialize_lr(dict(lr,Biot=0.)),
        "regional_compatibility_2km.in":native.serialize_lr(dict(lr,zBAsth=2000.)),
        "runtime.control":"C10_PRE_SOLVE_ONLY\n",
        "regional_reporting_plates.dat":"".join(f"{x['local_id']} {x['native_slot']}\n" for x in owner),
    }
    authority=read(c08.pinned(root/VERTICAL_AUTHORITY,VERTICAL_PIN))
    need(authority["chemical_density_policy"]["runtime_value"]==0.
         and authority["squeez_residual_classification"]["convert_to_chemical_density"] is False,
         "C10_VERTICAL_AUTHORITY_MUTATION")
    mesh = parse_feg(files["regional.feg"], mode="SHELLS_READY")
    case={
        "feg_columns": [[n.node_id, n.elevation_m, n.crustal_thickness_m, n.mantle_lithosphere_thickness_m]
                        for n in mesh.nodes],
        "linear_trace_rows":traces["candidates"]["linear_arc"]["rows"],
        "scenario":bc.SCENARIO,"package_status_before_native_preflight":"CONDITIONAL_DECK_PENDING_NATIVE_PREFLIGHT",
        "boundary_recommendation":bc.PREFERRED,"selected_trace_rows":selected,
        "native_override_authority":None,"existing_pre_authority":case["baseline"],
        "geometry":case["geometry"],"G4_mapping":case["G4_mapping"],
        "initial_time_proposal":case["time"],"lr_native_parameters":lr,
        "reporting_plate_binding":owner,
        "frame":case["frame"],"native_control":"Standalone regional wrapper, rpeat=1, no Earth motion, no torque iteration.",
        "source_pins":case["source_pins"]|{"C09_manifest_sha256":PIN,"vertical_authority_sha256":VERTICAL_PIN},
        "expected_outputs_after_later_authorization":case["expected_outputs"],
        "surface_to_history":"Use existing G4 output mapping and conservation policy. No present state advance.",
        **SCOPE}
    reports={
        "C09_REPLAY.json":evidence,
        "CONSTITUTIVE_BASELINE.json":{"C09_model":model,"cohesion_Pa":0.,"baseline_Biot":1.,
                    "dry_Biot_sensitivity":0.,
                    "authorial_assumption":"Effective terrestrial analogue, no assignment of natural ARCANA lithology, water or absolute pressure.",
                    "reference":"Published C09 Diorite2 and unchanged PRE/S1B parameters. Alternatives retained by C09 identity.",**SCOPE},
        "CONTINUOUS_BOUNDARY_TRACE_CANDIDATES.json":traces|SCOPE,
        "REGIONAL_CONSTRAINT_ANALYSIS.json":{"column_order":"parent source order, slots south/east","options":rank,
                "stiffness_rank":None,"important":"Boundary rows independent. Full operator not assembled.",**SCOPE},
        "NATIVE_NUMERICAL_CONTROL_PROPOSAL.json":native.numerical_controls()|SCOPE,
        "COMPLETE_CANDIDATE_INPUT_PACKAGE.json":case,
        "FIRST_SOLVE_ACCEPTANCE_PROTOCOL.json":acceptance(),
        "AUTHORIAL_RATIFICATION_SHEET.json":{
            "scenario":bc.SCENARIO,"approval_id":None,
            "proposed_choices":[
                {"id":"G2","choice":"Diorite2 effective shared continuum","values":model},
                {"id":"PORE","choice":"Surface-relative hydrostatic Biot=1; dry Biot=0 sensitivity","rho_water_kg_m3":lr["rhoH2O"]},
                {"id":"CUT","choice":bc.PREFERRED,"consequence":"One imposed continuous tangent velocity trace on each N/S cut; linear sensitivity, unknown natural exterior loading remains."},
                {"id":"MESH","choice":"R8 original shared FEG with unchanged all-parent ownership; no sided faults"},
                {"id":"NORMAL","choice":"Thin-shell vertical reference native S1B, retain tauZZ and sigZZB","consequence":"Normal reference is hydrostatic and elevation-aware. It is not a separately calibrated 3-D support."},
                {"id":"BASAL","choice":"Free-slip tangential limiting model","values":{"iConve":0,"trHMax_Pa":0.,"inert_zBAsth_m":1000.,"frame_token":"RF"}},
                {"id":"NUMERIC","choice":"Initial standalone numerical controls from historical smoke","values":native.numerical_controls()},
                {"id":"SCOPE","choice":"Separate authority needed for actual operator and solve","consequence":"Controlled synthetic response only, exterior A and global routes separate. No T1 authority."}
            ],**SCOPE},
    }
    index, extent, _, _, _, _=c08.primary_inputs(root)
    pre=c08.c07.PACKET/"OUTER_A_08x08_PRE_T0_PASSIVE.dat"
    profiles,_=c09.g3.regional_pre(pre,index,extent)
    pt=read(c08.OUT/"REGIONAL_PT_RATE_SUPPORT.json")["native_Moho_PT_projection"]
    return reports,files,profiles,pt,authority


def write_new(path,value):
    text=value if isinstance(value,str) else json.dumps(value,sort_keys=True,allow_nan=False,separators=(",",":"))+"\n"
    with path.open("x",encoding="utf-8") as handle:
        handle.write(text)


def execute(root, output, head, *, development=False):
    need(not output.exists() and not output.is_symlink() and not output.resolve().is_relative_to(root),
         "C10_OUTPUT_EXISTS_OR_IN_REPOSITORY")
    reports,files,profiles,pt,authority=prepare(root)
    output.mkdir(exist_ok=False)
    for key,body in files.items():
        write_new(output/key,body)
    case=reports["COMPLETE_CANDIDATE_INPUT_PACKAGE.json"]
    measurements,receipt=native.run_native_probe(root,output,files,case["lr_native_parameters"])
    nums=vertical.diagnostics(case,profiles,pt,measurements)
    manifest=c09.c08.c07.c06.inventory(output)
    case["package_status"]="COMPLETE_CANDIDATE_NOT_AUTHORIZED"
    case["native_deck_file_pins"]={k:manifest[k] for k in sorted(files)}
    case["native_pre_solve_finding"]=nums["matrix_size"]
    reports["NATIVE_VERTICAL_SUPPORT_AND_GPE.json"]={
        "authority_sha256":VERTICAL_PIN,"authority_scope":authority["squeez_residual_classification"],
        "meaning":"Thin-shell vertical equilibrium: sigma_zz anomaly = P_reference(z_sea)-P_column. P_reference uses the S1B 300-km piecewise reference column; integrate over actual datum-offset depth for tauZZ.",
        "surface_water":"Sea-level datum, no reference pressure above it. Positive terrain load starts at the local land surface; submerged column adds water to the floor before rock. All C10 nodes/IPs are land.",
        "pore":"Viscos starts pw0=0 at local surface and rho_w*g*thickC at Moho; Diamnd uses PRE-weighted rho_w and adds Biot times pore pressure to compressive negative sigma_z. No elevation term for pore head and no ocean load on this land fixture.",
        "GPE_ownership":"Native Fixed, including topographic integrated stress, basal anomaly on sloping base and native edge anomaly. No separate G2/G3 GPE forcing. Preserve composition compatibility zero.",
        "solver_scope":"No imposed 3-D normal traction. Accept native reduced vertical balance as a model choice with derived nonzero sigZZB and tauZZ.",
        "measurement":nums,**SCOPE}
    reports["BASAL_FREE_SLIP_RUNTIME_AUDIT.json"]={
        "native_consumers":{"FillIn":"Convec then Flow then OneBar then pulled. iConve=0 gives static with zero wrapper omega and same bookkeeping slot; no Earth frame or mantle flow supplied.",
            "OneBar":"Before pulled, floor(zBAsth/oneKm+0.5) must be positive. A 1000m depth evaluates one cell at 500m; 2000m evaluates two. Glue is finite in both and irrelevant to measured zero traction.",
            "ReadPm":"zBAsth positive guard alone does not prevent empty OneBar at 400m. Wrapper adds actual cell-count guard.",
            "Limits":"etaMax is exactly zero when trHMax=0. visMax remains positive for the continuum and is a numerical limit.",
            "THOnB":"iConve=0 and pulled false zero eta and sigHB explicitly, even for nonzero fixture velocity.",
            "Pure_and_Balanc":"Future Pure invokes THOnB. Basal assembly and force/output accounting guard on pulled and trHMax. Full solve path has not run.",
            "mode6":"Excluded; stock torque mode interpolates basal tractions and is not the controlled limit.",
            "Result":"Adds tauZZI to in-plane totals and retains tauZZI as integrated vertical reference; zero tangential basal does not zero these terms."},
        "parameter_activity":{"physical_limit":["trHMax=0","hydrostatic Biot=1"],
            "inactive_compatibility":["zBAsth=1000m","zero fault friction/Byerly/tauMax since native nFl=0","RF slot token and zero omega in the mantle/static lookup interfaces","tAdiab/gradie scalar fallback inactive in S1B OneBar"],
            "unresolved_natural":["actual mantle flow","finite coupling","physical mechanical LAB","outer traction"]},
        "same_native_fixed_and_thickness_under_depth_sensitivity":True,
        "glue_ranges":nums["glue_range_by_compatibility_depth"],"negative_checks":receipt["stops"],
        "zero_tangential_traction_measured":True,**SCOPE}
    reports["NATIVE_PRE_SOLVE_QUALIFICATION_PLAN.json"]={
        "development_or_operator":("DEVELOPMENT" if development else "OPERATOR_OFFLINE"),
        "scope_receipt":receipt,"native_size":nums["matrix_size"],
        "deterministic_stop":"C10_STOP_AFTER_FIXED_BEFORE_PURE. The generated entry routine omits every instruction at and after the call to Pure.",
        "future_assembly":"Separate executable and scope required for actual operator assembly, rank/conditioning and solve.",
        "resource_proposals":{"models":1,"MPI_ranks_at_most":2,"wall_s":120,"aggregate_RAM_bytes":1073741824,
                              "attested_for_physical_stage":False},**SCOPE}
    for key,report in reports.items():
        need(all(report[k]==v for k,v in SCOPE.items()),"C10_OUTPUT_AUTHORITY")
        write_new(output/key,report)
    write_new(output/"MANIFEST.json",{
        "schema":"R6_C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"development_only":development,"C09_manifest_sha256":PIN,
        "C09_development_manifest_sha256":DEV_PIN,"receipt_sha256":sha(RECEIPT),
        "files":c09.c08.c07.c06.inventory(output),**SCOPE})
    return nums


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha",required=True)
    parser.add_argument("--offline-controlled-region-only",action="store_true",required=True)
    args=parser.parse_args()
    s2=c09.c08.c07.c06.prior.s2
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C10_CHECKOUT")
    execute(root,OUT,head)
    print("C10_MANIFEST_SHA256",sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS,flush=True)


if __name__=="__main__":
    main()
