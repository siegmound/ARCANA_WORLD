"""Offline C09 scenario construction. No solver, provider or history calls."""
import argparse
import json
from pathlib import Path

from arcana_worldsim.r6.state import AuthorityClass
from experiments.r6_thermo_provider_pilot_v1 import c09_column_scenarios as g2
from experiments.r6_thermo_provider_pilot_v1 import c09_mechanical_case as g3
from experiments.r6_thermo_provider_pilot_v1 import run_c08_regional_closure as c08

ENTRY = "dd6d22243dcfdcfcdb0c1c9cd4fefef2e009a76b"
PIN = "5ef64cd06b6be89f52fcd1f757928744ba8f1e5ade513fb3edccad710a6f60d0"
STATUS = "C09_WHOLE_COLUMN_SCENARIOS_PREPARED__BLOCKED_REGIONAL_LOAD_AND_BASAL_SELECTION"
OUT = c08.c07.BASE/"R6_THERMO_C09_PHYSICAL_SCENARIO_FIRST_SOLVE_PREPARATION_NEW01"
RECEIPT = Path(__file__).with_name("c08_fair_receipt_v1.json")
SCOPE = c08.SCOPE
need, read, sha = c08.need, c08.read, c08.sha
MEMBERS = {
    "C07_REPLAY.json","CONSTITUTIVE_SOURCE_EVIDENCE.json","REGIONAL_PT_RATE_SUPPORT.json",
    "WHOLE_COLUMN_STRENGTH_CANDIDATES.json","NATIVE_COMMON_EXPONENT_COMPARISON.json",
    "REGIONAL_BOUNDARY_CONDITION_CANDIDATES.json","CONSTRAINT_RANK_AND_GAUGE_ANALYSIS.json",
    "BASAL_SUPPORT_AND_FORCE_OWNERSHIP.json","AUTHORIAL_PHYSICAL_DECISION_SHEET.json",
}
FRAGMENTS = {"regional.feg","regional_PRE.dat","MOD_ArcanaRuntime.regional.f90"}


def verify_c08(folder):
    receipt = read(RECEIPT)
    need(receipt["source_sha"]==ENTRY and receipt["manifest_sha256"]==PIN
         and receipt["archive"]==folder.name and receipt["status"]==c08.STATUS
         and receipt["regression_passed"]==receipt["regression_total"]==728
         and receipt["explicit_C08_EXIT_marker_supplied"] is False and receipt["exit"] is None,
         "C09_C08_RECEIPT")
    manifest_path = folder/"MANIFEST.json"
    need(folder.is_dir() and not folder.is_symlink(),"C09_C08_ARCHIVE")
    manifest = read(c08.pinned(manifest_path,PIN))
    files = c08.c07.c06.inventory(folder)
    files.pop("MANIFEST.json")
    need(set(manifest)=={"schema","source_sha","C07_manifest_sha256","status",
                         "receipt_sha256","files",*SCOPE}
         and manifest["schema"]=="R6_C08_REGIONAL_CONSTITUTIVE_MECHANICAL_CLOSURE_MANIFEST_V1"
         and manifest["source_sha"]==ENTRY and manifest["C07_manifest_sha256"]==c08.PIN
         and manifest["receipt_sha256"]==sha(c08.RECEIPT) and manifest["status"]==c08.STATUS
         and set(files)==MEMBERS and files==manifest["files"]
         and all(manifest[k]==v for k,v in SCOPE.items()),"C09_C08_INVENTORY")
    return receipt,files


def replay(root):
    receipt,files = verify_c08(c08.OUT)
    rebuilt = c08.build(root)
    need(set(rebuilt)==MEMBERS,"C09_C08_REPLAY_INVENTORY")
    for name,value in rebuilt.items():
        need(json.loads(json.dumps(value,allow_nan=False))==read(c08.OUT/name),
             "C09_C08_REPLAY_DRIFT:"+name)
    return rebuilt,{"operator_report":receipt,"verified_members":files,
                    "replayed_members":sorted(rebuilt),"parent_C07_manifest_sha256":c08.PIN,
                    "retained_material_states":35,"retained_source_chemistries":14,
                    "retained_query_identities":951,**SCOPE}


def authorities():
    return {
        "existing_runtime_enum_values":[row.value for row in AuthorityClass],
        "CANONICAL_ARCANA_AUTHORITY":{"scope":"T0 PRE, FEG, topology, Euler realization and established reference values. Derived supported mappings do not grant forecast authority.",
                                     "existing":"DIRECT_AUTHORITY for original source; DERIVED_AUTHORITY for explicit transformations"},
        "SCIENTIFIC_LAW_OR_TERRESTRIAL_ANALOGUE":{"scope":"Momentum balance, published creep and failure parameters; no ARCANA observational or spatial imports.",
                                                "existing":"External attribution; no ARCANA material authority assigned"},
        "PROPOSED_SYNTHETIC_INITIAL_HYPOTHESIS":{"scope":"Apply a complete published constitutive model to original PRE as a bounded scenario and label extrapolation.",
                                                 "existing":"No runtime state emitted or material assigned"},
        "EMERGENT_SIMULATION_RESULT":{"scope":"Would require actual solve, G4, validation and reproducible record.",
                                      "existing":"No result emitted in C09"},
        **SCOPE}


def mechanical_boundary(old, outer16):
    previous = old["BASAL_SUPPORT_AND_FORCE_OWNERSHIP.json"]
    return {
        "regional":{"west_east":"Full 36 Dirichlet components with original plate IDs; removes the three rigid rotations.",
                    "north_south":{
                        "preferred":"Physically supplied exterior continuation A. Supply one compatible tangent velocity trace or balanced interface force exchange.",
                        "implementation":"plate58_deforming_explore_v1/spherical_exterior.assemble_spherical_exterior and g2_g3_source_core_exterior_stitch.stitch_source_core_exterior.",
                        "minimum_missing":["Closed exterior constitutive state to its outer edge; one admissible external condition per free component",
                                           "Common frame, basal law and native or exterior-only gravity allocation",
                                           "Conservative transfer at original edge IDs with displacement/velocity compatibility, equal/opposite force and consistent interface work"],
                        "outer_boundary_velocity_m_s":None,"outer_boundary_traction_N_per_m":None,
                        "native_representability":"ReadBC code 2 supports fully specified velocity traces. Code 1 leaves a natural component. Fixed codes 0/-1 give native weak-margin/ridge reference conditions. A generic exterior traction or impedance requires a qualified force adapter or the existing coupled weak form.",
                        "north_south_uniform_continuation_rejected":"Orientation and forcing change around 12 original contact segments.",
                        "simple_native_weak_margin_limit":"Review only if adjacent thin sheet is represented as mechanically weak under the same reference vertical load, with its own geological justification. C08 does not establish that limit."}},
        "16x16":{"nodes":len(outer16["parent_node_ids"]),"triangles":len(outer16["parent_triangle_ids"]),
                 "plates":outer16["source_plates_present"],"new_outer_cut_physical_closure":None,
                 "meaning":"Parent extent sensitivity. Enlarging the domain relocates the artificial cut and introduces source plate 11; it supplies no missing external traction."},
        "native_controls":previous["native_controls"],
        "free_slip_limit":{"name":"NO_TANGENTIAL_BASAL_EXCHANGE_ISOSTATIC_SHELL",
                           "trHMax_Pa":0.,"normal_support_hypothesis":"Quasi-static hydrostatic/isostatic column support using the original S1B depth-dependent density and native reference potential",
                           "normal_support_selected":None,
                           "limitation":"Test normal compensation residual using original elevation/column mass against proposed common reference surface. No mechanical LAB inferred; normal reference and native settings remain subject to approval.",
                           "iConve":None,"zBAsth_m":None,"pltRef":None,
                           "orchestrator_scope":"User Guide Table 2: iConve 0 is zero initial flow; full ShellSet orchestration may iterate from torque. Verify the standalone route keeps trHMax=0 and skips torque iteration."},
        "finite_coupling":{"traction_equation":"tau_t=beta (v_mantle-v_lithosphere)",
                           "beta_Pa_s_per_m":None,"mantle_velocity_in_selected_frame_m_s":None,
                           "mechanical_interface_depth_m":None,"selection":"Unavailable; no authorized mantle motion or beta. Euler surface velocity alone sets neither."},
        "native_GPE":previous["native_GPE"],"existing_coupled_GPE":previous["coupled_GPE"],
        "reaction_accounting":previous["reactions"],**SCOPE}


def acceptance():
    return {"ordered_stages":[
        ["01","Ratify a named immutable hypothesis and external support choice; bind its authorial record and source SHAs."],
        ["02","Qualify native executable, compiler/MPI/library identities, local PRE reader and active S1B branches. Exclude OrbData synthesis, OrbScore and stock density fallback."],
        ["03","Assemble the actual regional operator under explicit authority; verify constraints, scaled rank/conditioning, units and resource measurements. Review free-DOF residual tolerances after assembly conditioning and before the solve."],
        ["04","Separately authorize one bounded mechanical equilibrium solve. Verify finite velocities, stress/strain, capped-volume fractions and native convergence."],
        ["05","Compute free-DOF residual norm, held-DOF reactions, total force and torque, external/reaction/internal work and nonnegative dissipation. Normalize by sum of load/work magnitudes; give scale for near-zero net balances."],
        ["06","Using a predeclared G4 deformation/mass error budget, establish a smaller shared tolerated local/integrated constitutive error and vary solver and regularization controls. Converged velocity RMS alone is insufficient."],
        ["07","Bind G4 local IDs back to parent. Compare same-start proposed trial and half-trial, check cell Jacobians, layer volumes, mass/material flux and event interval. If contacts change, requalify topology before transport."],
        ["08","Start new experimental lineage only after a positive accepted step meets balances. Restore the full state in a separate process, compare fields, identity, clocks and causality. Keep existing archive immutable."],
        ],"acceptance_budget":{
            "unselected_constitutive_fraction":None,
            "numerical_floor_rule":"Use norm/component scaling and measured operator conditioning to distinguish floating residuals from physical balances.",
            "requirement":"Tie stiffness and constitutive error to work, reaction and maximum geometry/thickness increment in the prospective experiment before numerical acceptance. No percentage inferred from the observed C08 or C09 differences."},
        "mechanical_equilibrium_alone_is_T1":False,**SCOPE}


def build(root):
    old,evidence = replay(root)
    index,extent,profiles,feg,_,_ = c08.primary_inputs(root)
    pre = c08.c07.PACKET/"OUTER_A_08x08_PRE_T0_PASSIVE.dat"
    rows,pre_text = g3.regional_pre(pre,index,extent)
    need(set(rows)==set(profiles) and all(all(rows[p][k]==v for k,v in profile.items())
         for p,profile in profiles.items()),"C09_REGIONAL_PRE_BINDING")
    models = g2.model_catalog(root,sha)
    baseline = old["AUTHORIAL_PHYSICAL_DECISION_SHEET.json"]["native_initialization"]["parameters"]
    rates = old["REGIONAL_PT_RATE_SUPPORT.json"]["rates_s_inv"]
    thermal = baseline["thermal"]
    depth,bins,pivot,sensitivities = g2.assess(
        rows,models,rates,baseline["gMean"]["value"],
        baseline["reference_densities"]["seawater"]["nominal"],
        baseline["surface_temperature"]["range"],
        {"crust":thermal["continental_crust"]["alpha"]["sensitivity_range"],
         "mantle":thermal["mantle"]["alpha"]["range"]})
    outside = read(c08.c07.PACKET/"CONTINUATION_A.json")
    outer16, = (r for r in outside["topological_comparative_extents"] if r["cell_extent_per_side"]==16)
    bc = mechanical_boundary(old,outer16)
    global_result = g3.global_route(root)
    case,files = g3.candidate_package(root,index,extent,pre_text,rows,feg,old,models)
    coupl = "experiments/plate58_deforming_explore_v1/nonlinear_layered_g3.py"
    reports = {
        "C08_REPLAY.json":evidence,"SCIENTIFIC_AUTHORITY_CROSSWALK.json":authorities(),
        "PUBLISHED_CONSTITUTIVE_MODELS.json":models|SCOPE,
        "WHOLE_COLUMN_SCENARIO_COMPARISON.json":{
            "conditional_synthetic_columns":81,"empirically_validated_ARCANA_columns":0,
            "extrapolation_policy":"Use published whole-model branches as conditional effective strength laws. Preserve C08 lab screens. No unknown is filled with a numerical viscosity cap.",
            "P_policy":"One rho_ref*(1-alpha*T) correction for the pressure proxy, integrate PRE by layer. Dry and hydrostatic pore pressure use Biot 0 and 1 equivalents respectively. No absolute or dynamical pressure asserted.",
            "pressure_in_creep":"Native existing absolute-depth exponential retains published C; layered uses corrected overburden P as conditional thermodynamic proxy in activation term.",
            "native_diagnostic":"At imposed pure strike-slip sqrt(J2), min of creep, Mohr-Anderson factor sin(atan cFric)*effective vertical load, and physical dCreep. Zero cohesion. Approximate column strength diagnostic, not actual native visMax, sigHBi, brittle interpolation or solved tauMat.",
            "layered_diagnostic":"Yu Eq.12–18 at initial conditions. Solve summed diffusion/dislocation rates at common stress; apply 2-D Drucker-Prager minimum. Future plate-scale tensor model needs a separate applicability and numerical check.",
            "portrait_depth_data":"Each parent, all hypotheses and both fluids at 100-km rate, with support, stress, viscosity and mechanisms. Other rates retain integrated and transition data.",
            "rates_s_inv":rates,"results":bins,"paired_PT_sensitivities":sensitivities,"by_parent":depth,**SCOPE},
        "NATIVE_REDUCTION_ADEQUACY.json":{
            "eCreep_test":g2.COMMON_E,"pivot_rate_s_inv":pivot,
            "C08_partial_mantle_max_relative_error":.0308336396439,
            "C09_common_exponent_scope":"Matched uncapped dislocation branches at pivot in stress invariant. Change slope only and retain yield/caps and any diffusion branch; Yu common slope test is not a faithful native representation.",
            "statistics":bins,"existing_separate_exponent":coupl,
            "native_dimensional_form":"eta=0.5*A*(2*sqrt(J2))**(e-1)*exp((B+Cz)/T), stress_II=2*eta*sqrt(J2). A units Pa s^e, z and C in m and K/m. A pivot rescaling uses 2*sqrt(J2).",
            "existing_separate_exponent_sha256":sha(root/coupl),
            "native_diorite2_exact_exponent":.267,"native_authorial_acceptance":None,
            "unrepresented_by_reduction":"Multi-branch composition and nonzero cohesion in Yu; the retained research tangent is ductile-only and must not silently run the full viscoplastic scenario.",
            "adequacy_controls":"Use physical cap exposure, native numerical visMax/refStr/okDelV sensitivity, free DOF residuals, reaction/work and deformation budgets before accepting a reduction.",
            **SCOPE},
        "REGIONAL_GLOBAL_ROUTE_COMPARISON.json":{
            "recommended_first":"R_8x8_DIORITE2_SHARED_CONTINUUM_AFTER_CLOSURE",
            "why":"Much smaller test with source distal support. Test selected load physics and material transport once. Global avoids artificial cuts but expands material and force hypotheses to six crust domains and all plate interfaces.",
            "regional_parameters":case["geometry"],"global":global_result,
            "global_may_be_preferred_when":"Closed basal driving, global constitutive coverage and qualified rotation-removal/operator exist, or regional closure proves more uncertain than one globally consistent experiment.",
            "deferred_full_coupling":"C06/C07 all eight groups, targeted equilibrium where required; retained 35 material states/14 chemistries/951 identities, zero new engines.",**SCOPE},
        "BASAL_AND_BOUNDARY_SCENARIOS.json":bc,"CANDIDATE_NATIVE_INPUT_PACKAGE.json":case,
        "FIRST_SOLVE_ACCEPTANCE_PROTOCOL.json":acceptance(),
        "AUTHORIAL_RATIFICATION_SHEET.json":{
            "proposal":"C09_R_DIORITE2_EFFECTIVE_CONTINUUM","approval_id":None,
            "recommendations":[
                {"choose":"Diorite2 effective continental and mantle; original PRE geometry and density.",
                 "values":models["native_diorite2"],
                 "consequence":"Complete conditional column strength with homogeneous effective crust, native exponent .267 and published low-temperature stress ceiling.",
                 "uncertainty":"Legacy coefficients and layered Yu bounds in comparison as model spreads; no ARCANA lithology or statistical error assigned."},
                {"choose":"Review hydrostatic Biot=1 as published baseline and Biot=0 as dry sensitivity.","values":{"Biot":[1.,0.],"rho_water_kg_m3":baseline["reference_densities"]["seawater"]["nominal"]},
                 "consequence":"Changes effective pressure and resistance even if the dislocation law and PRE temperature remain fixed."},
                {"choose":"Keep source 18 distal nodes and distributed continuum; close N/S via continuation A.",
                 "values":{"distal_rank":36,"north_south_provider":None,"mechanical_width_m":None},
                 "consequence":"Produces forcing-defined deformation only after outer loads/work and an observable width are specified. Reject dual Euler, marker-based faults and unsupported periodicity."},
                {"choose":"Start with named free-slip tangential limit and test independently specified normal support.",
                 "values":{"trHMax_Pa":0.,"basal_normal_reference":None,"native_basal_depth_m":None},
                 "consequence":"Zero basal tangential work by model. The cut and body loads still need closure. Finite drag requires separately supported mantle motion and interface."},
            ],"rejected_as_first_solve":["Global because additional basal, constitutive and contact requirements remain",
                     "Native deployment of the layered composite because distinct exponents, diffusion and cohesive yield differ",
                     "Inheriting Earth stress/flow fields, boundary geometry, or adopting numerical visMax as cold strength"],
            "mandatory_open_values":case["required_input_values"],**SCOPE},
    }
    return reports,files


def write_once(output, reports, fragments, head, *, development=False):
    need(not output.exists() and not output.is_symlink(),"C09_OUTPUT_EXISTS")
    need(set(fragments)==FRAGMENTS and all(Path(name).name==name
         and name!="MANIFEST.json" and all(value.get(k)==v for k,v in SCOPE.items())
         for name,value in reports.items())
         and reports["CANDIDATE_NATIVE_INPUT_PACKAGE.json"]["status"]=="NOT_EXECUTABLE",
         "C09_OUTPUT_SCOPE")
    body = {name:json.dumps(value,sort_keys=True,allow_nan=False,separators=(",",":"))+"\n"
            for name,value in reports.items()}
    output.mkdir(exist_ok=False)
    for name,text in (body|fragments).items():
        with (output/name).open("x",encoding="utf-8") as handle:
            handle.write(text)
    c08.c07.c06.prior.s2.write_json(output/"MANIFEST.json",{
        "schema":"R6_C09_PHYSICAL_SCENARIO_FIRST_SOLVE_PREPARATION_MANIFEST_V1",
        "source_sha":head,"development_only":development,"status":STATUS,"C08_manifest_sha256":PIN,
        "receipt_sha256":sha(RECEIPT),"files":c08.c07.c06.inventory(output),**SCOPE})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--offline-physical-scenario-only",action="store_true",required=True)
    args = parser.parse_args()
    s2 = c08.c07.c06.prior.s2
    root,head = s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C09_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink() and not OUT.resolve().is_relative_to(root),
         "C09_OUTPUT_EXISTS_OR_IN_REPO")
    reports,files = build(root)
    write_once(OUT,reports,files,head)
    print("C09_MANIFEST_SHA256",sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS,flush=True)


if __name__=="__main__":
    main()
