"""Read-only C06 replay and source-bound ShellSet configuration preparation."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from arcana_worldsim.r6.material_rheology_provider import DEFAULT_BENCHMARK
from experiments.r6_thermo_provider_pilot_v1 import run_c06_regional_material_hypothesis as c06

HERE = Path(__file__).resolve().parent
BASE = c06.prior.s2.BASE
OUT = BASE / "R6_THERMO_C07_NATIVE_PHYSICAL_CONFIGURATION_NEW01"
ENTRY = "2d4da091b6a4ccd40c43642a04202265b4270262"
PIN = "c6f9a8fec5769a1d0e32be7c6c696aec6a4bfa93c9ed91f3b16d7d9a7b31123d"
STATUS = "C07_NATIVE_PHYSICAL_CONFIGURATION_PREPARED__MECHANICAL_AUTHORITY_REVIEW_REQUIRED"
MEMBERS = {
    "C05R_REPLAY.json", "GEOLOGICAL_SOURCE_AUTHORITY.json",
    "REGION_8X8_MATERIAL_ALTERNATIVES.json", "REGION_16X16_SENSITIVITY.json",
    "TARGETED_THERMODYNAMIC_CAMPAIGN_PLAN.json", "PHYSICAL_CLOSURE_ROUTE_MATRIX.json",
    "AUTHORIAL_DECISION_SHEET.json",
}
RECEIPT = HERE / "c06_fair_receipt_v1.json"
CANDIDATE = HERE / "native_physical_configuration_candidate_v1.json"
SCOPE = c06.SCOPE
need, read, sha = c06.need, c06.read, c06.file_sha
PLATE = Path("experiments/plate58_deforming_explore_v1")
PRE = "R6_PRE_ORBDATA_"
REFERENCE = PRE + "MATERIAL_REFERENCE_COLUMN_V1.json"
MINIMUM = "R6_SHELLSET_MINIMUM_THERMOMECHANICAL_STATE_CONTRACT.json"
PACKET = BASE / "PLATE58_G3_A_OUTER_MULTISCALE_NEW_01"


def verify_archive(folder, receipt):
    need(receipt["source_sha"] == ENTRY and receipt["manifest_sha256"] == PIN
         and receipt["archive"] == folder.name and receipt["import_check"] == "PASS"
         and receipt["regression_passed"] == receipt["regression_total"] == 707
         and receipt["explicit_terminal_exit_line_supplied"] is False
         and receipt["exit"] is None, "C07_C06_RECEIPT")
    path = folder / "MANIFEST.json"
    need(folder.is_dir() and not folder.is_symlink() and not path.is_symlink()
         and path.is_file() and sha(path) == PIN, "C07_C06_MANIFEST_PIN")
    manifest = read(path)
    inventory = c06.inventory(folder)
    inventory.pop(path.name)
    need(set(inventory) == MEMBERS and inventory == manifest["files"]
         and manifest["schema"] == "R6_C06_REGIONAL_MATERIAL_HYPOTHESIS_MANIFEST_V1"
         and manifest["source_sha"] == ENTRY and manifest["status"] == receipt["status"] == c06.STATUS
         and manifest["C05R_manifest_sha256"] == c06.PIN
         and manifest["contract_sha256"] == sha(c06.CONTRACT)
         and manifest["receipt_sha256"] == sha(c06.RECEIPT)
         and all(manifest[k] == v for k,v in SCOPE.items()), "C07_C06_INVENTORY_SCOPE")
    need(tuple(manifest[k] for k in ("library_states", "source_chemistries", "previous_research_solves",
            "reference_diagnostic_equilibria", "cold_MORB_research_candidates")) == (35,14,62,6,4),
         "C07_C06_LIBRARY_SCOPE")
    payload = {name: read(folder/name) for name in sorted(MEMBERS)}
    need(all(all(item.get(k) == v for k,v in SCOPE.items()) for item in payload.values()),
         "C07_C06_PAYLOAD_SCOPE")
    return manifest, payload


def replay(root):
    receipt = read(RECEIPT)
    manifest, payload = verify_archive(c06.OUT, receipt)
    lib, reports, packets, handoff, evidence = c06.replay(root)
    geo = c06.geological(root, packets)
    alternatives, campaign = c06.plan(lib, reports, geo, read(c06.CONTRACT))
    routes = c06.closure(root, packets, handoff)
    checks = {
        "C05R_REPLAY.json": evidence, "GEOLOGICAL_SOURCE_AUTHORITY.json": geo,
        "REGION_8X8_MATERIAL_ALTERNATIVES.json": alternatives["8"],
        "REGION_16X16_SENSITIVITY.json": alternatives["16"],
        "TARGETED_THERMODYNAMIC_CAMPAIGN_PLAN.json": campaign,
        "PHYSICAL_CLOSURE_ROUTE_MATRIX.json": routes,
    }
    need(all(json.loads(json.dumps(v)) == payload[k] for k,v in checks.items()),
         "C07_C06_RECONSTRUCTION_DRIFT")
    need(campaign["unique_candidate_queries"] == 951 and campaign["executable_new_queries"] == 0
         and evidence["aggregate"]["native_exact"] == 912
         and evidence["aggregate"]["additional_source_coordinate"] == 456,
         "C07_C06_COUNTS")
    return payload, {"operator_receipt": receipt, "verified_inventory": manifest["files"],
                     "reconstructed_payload_members": sorted(checks),
                     "decision_sheet_verified_by_manifest_and_scope": True, **SCOPE}


def classify_node(node):
    cells = node["native_cells"]
    domains = {cell["crust_domain_id"] for cell in cells}
    plates = {cell["plate_id"] for cell in cells}
    need(plates == set(node["native_plate_ids"]) and node["fault_side_assignment"] is None,
         "C07_UNVERIFIED_SIDED_OWNERSHIP")
    need(not cells or node["pre_numerical_owner_cell"] in {c["cell_id"] for c in cells},
         "C07_PRE_NONINCIDENT_OWNER")
    admitted = ["ADMITTED_INITIALIZER_SUPPORT" in c["d12_classes"]
                if c["d12_classes"] else None for c in cells]
    membership = ("UNKNOWN" if not admitted or None in admitted else "ADMITTED" if all(admitted)
                  else "MIXED_ADMISSION" if any(admitted) else "EXCLUDED")
    if membership != "ADMITTED" or not domains or not domains <= set(range(1,7)):
        crust = "UNKNOWN_OR_EXCLUDED_SOURCE_SUPPORT"
    elif domains == {1}:
        crust = "UNIFORM_OCEANIC_ROLE"
    elif 1 in domains:
        crust = "OCEANIC_CONTINENTAL_TRANSITION"
    elif len(domains) == 1:
        crust = "UNIFORM_CONTINENTAL_ROLE"
    else:
        crust = "MULTIPLE_CONTINENTAL_PROVINCES"
    thickness = node["source_PRE"]["mantle_lithosphere_thickness_m"]
    mantle = "AUTHORED_PRE_GEOMETRY" if math.isfinite(thickness) and thickness > 0 else "UNKNOWN"
    boundary = bool(node["boundary_ids"])
    return {"C06_support_status": node["support_status"], "crust_support": crust,
            "mechanical_support": "MULTIPLE_PLATES" if len(plates)>1 else "SINGLE_PLATE" if plates else "UNKNOWN",
            "boundary_incidence": boundary, "native_plate_ids": sorted(plates),
            "sided_ownership": "UNRESOLVED" if boundary or len(plates)>1 else "NOT_APPLICABLE",
            "membership": membership, "mantle_geometry": mantle, "mantle_material_authority": None,
            "fault_side_assignment": None, "natural_lithology": None,
            "reason": "Composition uses native crust domains and membership; mechanical ownership uses plates and boundary incidence.",
            "pre_numerical_owner_cell": node["pre_numerical_owner_cell"],
            "native_cells": cells, "boundary_ids": node["boundary_ids"]}


def crosswalk(geology):
    regions = {}
    for extent, region in geology["regions"].items():
        nodes = {k: classify_node(v) for k,v in region["nodes"].items()}
        regions[extent] = {"nodes": nodes, "source_hashes": region["source_hashes"],
                           "counts": {axis: dict(Counter(v[axis] for v in nodes.values()))
                                      for axis in ("crust_support", "mechanical_support", "membership",
                                                   "mantle_geometry", "C06_support_status")},
                           "old_to_new_crust_counts": {
                               old: dict(Counter(v["crust_support"] for v in nodes.values()
                                                 if v["C06_support_status"] == old))
                               for old in sorted({v["C06_support_status"] for v in nodes.values()})},
                           "boundary_incident_nodes": sum(v["boundary_incidence"] for v in nodes.values())}
    return {"primary_extent": 8, "extent_16_is_domain_sensitivity": True, "regions": regions, **SCOPE}


def parameter(row, units, *, allow_zero=False):
    raw = row.get("nominal", row.get("value"))
    need(row["units"] == units and type(raw) in (int,float) and math.isfinite(raw)
         and (raw >= 0 if allow_zero else raw > 0), "C07_PARAMETER_UNIT_OR_VALUE")
    for key in ("range", "sensitivity_range", "literature_range"):
        if key in row:
            lo,hi = row[key]
            need(all(type(x) in (float,int) and math.isfinite(x) for x in (lo,hi))
                 and 0 <= lo <= raw <= hi, "C07_PARAMETER_RANGE")
    return dict(row)


def native_candidate(root):
    template = read(CANDIDATE)
    need(all(key not in template or template[key] == val for key,val in SCOPE.items())
         and all(template[k] is None for k in ("constitutive_LR", "fault_law", "outer_cut_conditions",
                                               "basal_conditions", "regional_reference_frame_selection")),
         "C07_CANDIDATE_UNAUTHORIZED_SCOPE")
    validate_thermal_mode(template["proposed_policy"])
    reference = read(root / REFERENCE)
    lineage = {}
    for filename, pin in reference["authority_sources"].items():
        path = root / filename
        need(sha(path) == pin["sha256"] and read(path)["decision"] == pin["decision"],
             "C07_REFERENCE_SOURCE_DRIFT")
        lineage[filename] = pin
    astro = reference["reference_temperatures"]["potential_temperature_K"]
    densities = {k: parameter(v, "kg m-3 at Tref=Tp" if k == "asthenosphere" else "kg m-3")
                 for k,v in reference["density"].items()}
    thermal = {k: {sym: parameter(reference["thermal_properties"][k][sym], unit)
                   for sym,unit in (("k","W m-1 K-1"),("Cp","J kg-1 K-1"),("alpha","K-1"))}
               for k in ("continental_crust","oceanic_crust","mantle")}
    heats = {k: parameter(reference["radiogenic_heat"][k], "W m-3", allow_zero=True)
             for k in ("continental_crust","oceanic_crust","mantle_lithosphere")}
    ceiling = reference["temLim_K"]
    need(ceiling["physical_solidus"] is False, "C07_TEMPERATURE_CEILING")
    minimum = read(root / MINIMUM)
    need(minimum["parent_pressure_gap"]["external_absolute_pressure_field_required"] is False
         and minimum["parent_pressure_gap"]["external_eos_density_required"] is False,
         "C07_MINIMUM_PRESSURE_CONTRACT_DRIFT")
    chemical = read(root / (PRE+"CHEMICAL_DENSITY_MECHANICS_AUTHORITY.json"))
    feg = read(root / (PRE+"SHELLSET_T0_FEG_V1.json"))
    anomaly = chemical["chemical_density_policy"]
    curvature = feg["nodal_fields"]["cooling_curvature_k_m2"]
    need(anomaly["runtime_value"] == 0 and anomaly["independent_composition_inference"] is False
         and curvature["authority"] == "LEGACY_FEG_COMPATIBILITY_ONLY" and curvature["value"] == 0,
         "C07_LEGACY_FIELD_AUTHORITY")
    return {**template, "reference_column_sha256": sha(root/REFERENCE), "authority_lineage": lineage,
            "parameters": {"gMean": parameter(reference["gravity"],"m s-2"),
                           "reference_densities": densities, "thermal": thermal, "heat_production": heats,
                           "surface_temperature": parameter(reference["thermal_properties"]["surface_temperature"],"K"),
                           "potential_temperature": parameter({**astro,"units":"K"},"K"),
                           "temLim": ceiling},
            "native_nodal_chemical_delta_rho": anomaly, "legacy_cooling_curvature": curvature,
            "thermal_preference_explanation": "Earlier hybrid steady/transient failure retained. Explicit ARCANA S1B consumes transient PRE and bypasses stock geotherm reconstruction.",
            "density_semantics": "Owner-bound reference rho; apply native thermal correction once. No local EOS substitution or residual fitting.",
            "native_thermal_symbols": {
                "rhoBar": "Owner-bound regional reference densities in compatible S1B paths; scalar stock fallback deliberately unselected",
                "rhoAst": "3300 kg/m³ at Tp via authored reference",
                "rhoH2O": "Seawater reference, not pore pressure",
                "thermCond_radio_alphaT": "Use PRE as encoded in explicit mode; no second thermal initialization",
                "tAdiab_gradie": "Tp at z=0 and a local derivative for compatibility; mantle T follows the governed integrated adiabat",
            },
            "remaining_runtime_adapter_check": "Audit each residual global rhoBar/asthenosphere consumer and frame on the proposed setup before solve.",
            "solver_ready": False, **SCOPE}


def validate_thermal_mode(policy):
    need(policy["profile"] == "PRESERVE_ORIGINAL_TRANSIENT_PRE"
         and policy["density"] == "S1B_REFERENCE_THERMAL_CORRECTION_ONCE"
         and policy["external_eos_density"] is None
         and policy["global_crust_rhoBar_override"] is None
         and policy["external_absolute_pressure"] is None
         and policy["LAB_meaning"] == "THERMAL_ONLY", "C07_THERMAL_OR_DENSITY_DOUBLE_COUNT")


def nodal_crosswalk(geology, candidate):
    validate_thermal_mode(candidate["proposed_policy"])
    regions = {}
    source_fields = {
        "elevation_m": ("elevation_m", None),
        "heat_flow_w_m2": ("heat_flow_w_m2", "surface_heat_flow_w_m2"),
        "crustal_thickness_m": ("crustal_thickness_m", "crust_thickness_m"),
        "mantle_lithosphere_thickness_m": ("mantle_lithosphere_thickness_m", "mantle_lithosphere_thickness_m"),
        "chemical_delta_rho_kg_m3": ("chemical_density_anomaly_kg_m3", None),
        "cooling_curvature_k_m2": ("cooling_curvature_k_m2", None),
    }
    for e, region in geology["regions"].items():
        path = PACKET / f"OUTER_A_{int(e):02d}x{int(e):02d}.feg"
        need(sha(path) == region["source_hashes"]["original_FEG_sha256"], "C07_FEG_PIN")
        mesh = parse_feg(path.read_text(), mode="SHELLS_READY")
        # Packet preserves native parent order. Read it from the authenticated index.
        packet = BASE / f"R6_G2G3_PHYSICAL_SOURCE_PACKET_{e}X{e}_NEW02"
        index, _, _ = c06.handoff.load_packet(packet, int(e))
        nodes = {}
        need(not mesh.faults and set(map(str,index["original_parent_node_order"])) == set(region["nodes"]),
             "C07_NATIVE_FEG_TOPOLOGY")
        for parent, row in zip(index["original_parent_node_order"], mesh.nodes, strict=True):
            src = region["nodes"][str(parent)]
            pre = src["source_PRE"]
            need(list(src["original_FEG_lat_lon_deg"]) == [row.latitude_deg,row.longitude_deg],
                 "C07_FEG_PARENT_COORDINATE")
            densities = candidate["parameters"]["reference_densities"]
            crust_ref = "oceanic_crust" if pre["owner_domain_id"] == 1 else "continental_crust"
            need(pre["crust_density_kg_m3"] == densities[crust_ref]["nominal"]
                 and pre["mantle_density_kg_m3"] == densities["lithospheric_mantle"]["nominal"],
                 "C07_PRE_REFERENCE_DENSITY_MISMATCH")
            values = {}
            for field,(attr,pre_key) in source_fields.items():
                value = getattr(row,attr)
                need(value is not None and math.isfinite(value) and
                     (pre_key is None or value == pre[pre_key] and value > 0),
                     "C07_FEG_PRE_FIELD_MISMATCH:" + field)
                values[field] = value
            need(values["chemical_delta_rho_kg_m3"] == candidate["native_nodal_chemical_delta_rho"]["runtime_value"]
                 and values["cooling_curvature_k_m2"] == candidate["legacy_cooling_curvature"]["value"],
                 "C07_NATIVE_PLACEHOLDER_AUTHORITY")
            nodes[str(parent)] = {**values, "pre_owner": src["pre_numerical_owner_cell"],
                                  "source_PRE_T_surface_K": pre["surface_temperature_k"],
                                  "source_PRE_T_Moho_K": pre["moho_temperature_k"],
                                  "source_PRE_T_thermal_LAB_K": pre["lab_temperature_k"],
                                  "reference_crust_density_kg_m3": pre["crust_density_kg_m3"],
                                  "reference_mantle_density_kg_m3": pre["mantle_density_kg_m3"],
                                  "local_EOS_density": None, "fault_side_assignment": None}
        regions[e] = {"nodes": nodes, "complete_numerical_fields": len(nodes),
                      "source_hashes": region["source_hashes"], "native_feg_fault_elements": 0,
                      "field_ranges": {name: [min(x[name] for x in nodes.values()),
                                               max(x[name] for x in nodes.values())]
                                       for name in source_fields}}
    return {"regions": regions,
            "density_runtime_operation": "Use rho_ref*(1-alpha*T) in the existing S1B consumer once",
            "zero_fields_scope": "Original FEG numerical compatibility values only; physical anomaly and curvature unassigned",
            "bathymetry_scope": "Finite source FEG support, without additional bathymetry inference",
            "thermal_policy": "No stock Assign geotherm or extra radiogenic term on an already evaluated PRE temperature",
            **SCOPE}


def native_creep_coverage(bounds, temperatures):
    need(len(bounds) == 2 and bounds[0] <= bounds[1] and all(math.isfinite(x) for x in bounds)
         and all(math.isfinite(t) and bounds[0] <= t <= bounds[1] for t in temperatures),
         "C07_CREEP_OUTSIDE_DECLARED_THERMAL_DOMAIN")


def constitutive(root, nodal):
    assessment = read(root/PLATE/"R6_G2_G3_CALIBRATION_ASSESSMENT_20261120.json")
    curves = read(root/PLATE/"R6_ZENODO_8304793_FAIR_CURVE_AXIS_ADJUDICATION_20261120.json")
    raw_curves = curves["raw_archive"]
    curve_path = BASE / "R6_G2_ZENODO_8304793_RAW_NEW_01" / "data.zip"
    need(curve_path.is_file() and not curve_path.is_symlink()
         and sha(curve_path) == raw_curves["zip_sha256"], "C07_RAW_CURVE_ARCHIVE_DRIFT")
    regional = [x["source_PRE_T_surface_K"] for x in nodal["regions"]["8"]["nodes"].values()]
    try:
        native_creep_coverage([1173.15, 1373.15], regional)
    except ValueError:
        bhq_surface_eligible = False
    else:
        bhq_surface_eligible = True
    return {
        "primary_crust_surface_T_range_K": [min(regional),max(regional)],
        "BHQ_surface_in_calibrated_temperature_domain": bhq_surface_eligible,
        "native_symbols": {
            "aCreep": "Pa s^e, two layers", "bCreep": "K, two layers",
            "cCreep": "K/m, absolute depth, two layers", "dCreep": "Pa, two layers",
            "eCreep": "dimensionless shared inverse stress exponent",
            "cFric": "dimensionless continuum coefficient tan(phi)",
            "fFric": "dimensionless fault coefficient", "Biot": "dimensionless effective-pressure factor",
            "Byerly": "fault offset-dependent friction reduction factor",
            "visMax": "Pa s computed via refStr, characteristic side and okDelV",
        },
        "invariants": "e_z=-(e_1+e_2); J2=-(e_1*e_2+e_1*e_z+e_2*e_z); Diamnd uses 2 sqrt(J2) and integrated horizontal principal stress relative to vertical",
        "native_lr_conversion": str(PLATE/"shells_lr_bridge.py"),
        "creep_regime": "One effective native creep branch per layer. A diffusion/dislocation composite needs justified parameters and a supported effective reduction or separately qualified implementation.",
        "research_candidates": {
            "BHQ": {"status": "LAB_RESEARCH_ONLY", "T_K": [1173.15,1373.15],
                    "P_reference_GPa": 1.5, "n": [4,0.9], "Q_kJ_mol": [223,56],
                    "log10_A_MPa_convention": [-3.96,1.96]},
            "wet_quartz": {"status": "RESEARCH_ONLY", "n": 4, "Q_kJ_mol": [135,15],
                           "log10_A_MPa_stress_and_fugacity": [-11.2,0.6], "fugacity_exponent": 1,
                           "fugacity": None},
            "dry_olivine": vars(DEFAULT_BENCHMARK),
        },
        "calibration_assessment": assessment["decision"], "curve_axis_receipt": curves["status"],
        "raw_curve_archive_sha256": raw_curves["zip_sha256"],
        "blocking": [
            "Cold upper crust: specify a supported brittle or low-temperature law and justify the transition; reject direct high-T extrapolation.",
            "Steady-state stress-rate observations with T/P/water and invariant conversion are required for a new fit. Stress-strain curve rows are not independent creep-rate measurements.",
            "Approve material roles, water activity/fugacity, effective pressure and Biot independently; qualify integrated strength and strain-rate range.",
            "BHQ n=4 and mantle benchmark n=3.5 do not map exactly to one shared eCreep. Slope-only minimax screening cannot qualify the whole column.",
            "Separate native dCreep and numerical visMax/regularization from measured material strength; specify and check each.",
            "Native FEG contains no sided faults; a fault route needs sided geometry, effective pressure and fFric/Byerly calibration.",
        ],
        "selected_LR": None, "selected_fault_parameters": None, **SCOPE,
    }


def mechanical(payload, geocross):
    routes = payload["PHYSICAL_CLOSURE_ROUTE_MATRIX.json"]
    return {
        "native_minimum": {
            "native_controls": {"iCond": "ReadBC/VBCs consume native constrained components; arbitrary cut continuity/traction mapping remains unqualified",
                                "iConve": None, "trHMax_Pa": None, "zBAsth_m": None,
                                "pltRef": None, "tOffs_or_interval": None},
            "reference_frame_numerical": "ARCANA_SHELLSET_RUNTIME_RX_PLUS_0P5_DEG_V1",
            "selected_regional_frame_and_gauge": None, "outer_cut_conditions": None,
            "basal_coupling": None, "mantle_traction": None, "GPE_closure": None,
            "available": "Parent topology, cuts and plate-side Euler. Euler may constrain approved distal velocity components only.",
            "requirements": ["Bind per-edge or native nodal BC and reference frame; confirm compatibility and rank.",
                             "Choose and justify normal support and basal coupling, including separate mantle velocity if used.",
                             "Use native ShellSet force accounting and reactions. Validate frame, work, residual, normalization and G4 transport/restart."],
        },
        "original_coupled_support": routes["G2_G3_FULL_COUPLED"]["support"],
        "boundary_nodes": {e:r["boundary_incident_nodes"] for e,r in geocross["regions"].items()},
        "historical_reconciliation": {
            "F2AV": "BLOCKED_F2AV_QUALIFICATION preserved; RO6 attests bounded historical observations. The historical matrix audit is not an automatic prerequisite for a distinct native regional adapter.",
            "F2B": "Original operator class, threshold, resource attestation and solver authorization stay unresolved. The native route needs its own rank, residual, runtime/resource and configuration checks.",
            "SI1": "Engineering solver evidence and PRE/FEG compatibility do not establish ARCANA SI1 mechanics qualification.",
            "G4": "Reuse solution_mapping parent/frame normalization after an authorized solve. Current mechanical solution, transport, mass conservation and restart are unqualified.",
        }, **SCOPE,
    }


def source_pins(root):
    names = [MINIMUM, REFERENCE, "R6_TECTONIC_THERMODYNAMIC_BINDING.json",
             PRE+"CHEMICAL_DENSITY_MECHANICS_AUTHORITY.json", PRE+"SHELLSET_T0_FEG_V1.json",
             PRE+"FEG_RUNTIME_COMPATIBILITY_CLOSURE.json", PRE+"SHELLSET_RUNTIME_PACKAGE_V1.json",
             PRE+"S1B_INTEGRATION_POINT_THERMAL_PROJECTION_CONTRACT.json",
             "experiments/shellset_regional_explore_v1/solution_mapping.py",
             "docs/arcana/SI1_BW1_F2B_D3D_RO6_FAIR_EVIDENCE_CONSOLIDATION.md",
             "docs/arcana/SI1_BW1_F2AV_DIAGNOSTIC.md",
             "docs/arcana/SI1_BW1_F2B_N2C_W3C_RUNTIME_AUTHORITY_AND_MPI_STOP_DESIGN.md",
             PLATE/"R6_G2_G3_CALIBRATION_ASSESSMENT_20261120.json",
             PLATE/"R6_ZENODO_8304793_FAIR_CURVE_AXIS_ADJUDICATION_20261120.json",
             PLATE/"PHYSICAL_EXPERIMENT_DECISION_PROPOSAL.json", PLATE/"shells_lr_bridge.py",
             "src/arcana_worldsim/r6/material_rheology_provider.py", c06.PROVIDER_MATRIX]
    names += [Path("external/ShellSet-v1.1.0/src") / (name+".f90")
              for name in ("MOD_ArcanaRuntime","MOD_Shells","MOD_ShellSet","SHELLS_v5.0")]
    return {str(name):sha(root/name) for name in names}


def build(root):
    payload, evidence = replay(root)
    geo = payload["GEOLOGICAL_SOURCE_AUTHORITY.json"]
    support = crosswalk(geo)
    candidate = native_candidate(root)
    nodal = nodal_crosswalk(geo, candidate)
    candidate["PRE_reference_rhoBar_by_scope_kg_m3"] = {
        e: sorted({n["reference_crust_density_kg_m3"] for n in region["nodes"].values()})
        for e,region in nodal["regions"].items()
    }
    rheology = constitutive(root, nodal)
    mechanics = mechanical(payload, support)
    refinement = {
        "C06_query_plan_sha256": evidence["verified_inventory"]["TARGETED_THERMODYNAMIC_CAMPAIGN_PLAN.json"]["sha256"],
        "comparative_identities": 951, "executable_new_queries": 0,
        "retained_routes": payload["PHYSICAL_CLOSURE_ROUTE_MATRIX.json"],
        "unselected_options": {str(e):payload[name]["alternatives"] for e,name in
                               [(8,"REGION_8X8_MATERIAL_ALTERNATIVES.json"),(16,"REGION_16X16_SENSITIVITY.json")]},
        "refinement_requires": "Property need and tolerance at a physically consistent checkpoint, selected source-keyed chemistry, qualified provider/phase-fluid policy and absolute P if required by equilibrium",
        "candidate_demands": ["Reference-to-EOS density or phase buoyancy sensitivity under coupled loading",
                              "Independent evidence for phase transitions, hydration or constitutive mechanism",
                              "High-resolution checkpoint refinement with parent lineage and uncertainty"],
        **SCOPE,
    }
    decision = {
        "propose_for_review": candidate["parameters"],
        "option": "Owner-bound S1B for extent 8. Extent 16 is domain sensitivity.",
        "physical_consequences": [
            "Accept original PRE reference fields with their ranges and thermal history, preserving the S1B column without duplicate thermal corrections.",
            "Qualify each remaining native rhoBar consumer. A global scalar can change plate-edge/mixed-domain stresses; do not silently flatten owner-bound properties.",
            "Decide scope-specific continuum or sided contact, a defensible whole-column law and effective pressure. Selection would authorize only configuration review.",
            "Define a regional frame and admissible cut/basal support. Native setup can proceed independently of the coupled equilibrium planner.",
        ],
        "remaining": [rheology["blocking"], mechanics["native_minimum"]["requirements"]],
        "approval_id": None, **SCOPE,
    }
    return {
        "C06_REPLAY.json": evidence, "ORTHOGONAL_GEOLOGICAL_SUPPORT.json": support,
        "EXISTING_PHYSICAL_AUTHORITY_MATRIX.json": {
            "sources": source_pins(root), "parameter_authority": candidate["parameters"],
            "reference_authority_lineage": candidate["authority_lineage"],
            "qualified_numerical_authority": ["FEG/PRE owner binding", "S1B runtime thermal evaluation"],
            "research_only": rheology["research_candidates"],
            "engineering_fixture_only": "Prior regional Earth LR / synthetic BC smoke",
            "missing": rheology["blocking"] + mechanics["native_minimum"]["requirements"],
            **SCOPE},
        "NATIVE_SHELLSET_CONFIGURATION_CANDIDATE.json": candidate,
        "NODAL_STATE_CROSSWALK.json": nodal, "CONSTITUTIVE_AND_FAULT_CLOSURE.json": rheology,
        "REGIONAL_MECHANICAL_CLOSURE.json": mechanics,
        "TARGETED_HIGH_FIDELITY_REFINEMENT_REQUIREMENTS.json": refinement,
        "AUTHORIAL_DECISION_SHEET.json": decision,
    }


def write_once(output, reports, head):
    need(not output.exists() and not output.is_symlink(), "C07_OUTPUT_EXISTS")
    need(all(Path(name).name == name and name != "MANIFEST.json"
             and all(value.get(k) == v for k,v in SCOPE.items())
             for name,value in reports.items()), "C07_OUTPUT_AUTHORITY")
    payload = {name: json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
               for name,value in reports.items()}
    output.mkdir(exist_ok=False)
    for name, body in payload.items():
        with (output/name).open("x", encoding="utf-8") as handle:
            handle.write(body)
    c06.prior.s2.write_json(output/"MANIFEST.json", {
        "schema": "R6_C07_NATIVE_PHYSICAL_CONFIGURATION_MANIFEST_V1",
        "source_sha": head, "C06_manifest_sha256": PIN, "status": STATUS,
        "candidate_sha256": sha(CANDIDATE), "files": c06.inventory(output), **SCOPE,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--offline-native-physical-configuration-only", action="store_true", required=True)
    args = parser.parse_args()
    s2 = c06.prior.s2
    root, head = s2.verify_checkout()
    need(head == args.expected_sha and not s2.git(root,"status","--porcelain"), "C07_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink() and not OUT.resolve().is_relative_to(root),
         "C07_OUTPUT_EXISTS_OR_IN_REPO")
    write_once(OUT, build(root), head)
    print("C07_MANIFEST_SHA256", sha(OUT/"MANIFEST.json"), flush=True)
    print(STATUS, flush=True)


if __name__ == "__main__":
    main()
