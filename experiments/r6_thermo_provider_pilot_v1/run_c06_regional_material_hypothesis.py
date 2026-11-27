"""C06 read-only source replay and regional material hypothesis planner."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import json
import math

from arcana_worldsim.r6.geological_source_t0_adapter import DOMAINS
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from experiments.plate58_deforming_explore_v1 import g2_g3_source_to_coupled_handoff as handoff
from experiments.plate58_deforming_explore_v1.g2_g3_core_exterior_source_runner import source_core_geometry
from experiments.r6_thermo_provider_pilot_v1 import run_c05_source_identity_design as prior
from experiments.r6_thermo_provider_pilot_v1 import s3_d12_native_membership as d12
from experiments.t0_authorial_composition_v1 import provider

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "c05r_fair_receipt_v1.json"
CONTRACT = HERE / "regional_material_hypothesis_contract_v1.json"
SOURCE = "e37d68092c140455dc97213200097ce5ef407a6a"
PIN = "cc854bdd67132471f87c64beeb285550fc3e48b881b40ea69c2396472e058b1a"
OUT = prior.s2.BASE / "R6_THERMO_C06_REGIONAL_MATERIAL_HYPOTHESIS_NEW01"
STATUS = "C06_SOURCE_KEYED_REGIONAL_HYPOTHESES_READY_FOR_AUTHORIAL_REVIEW"
need = prior.need
read = prior.c.read
file_sha = prior.hgp.file_sha
inventory = prior.q.z.d.launcher.inventory
SCOPE = {**prior.c.SCOPE, "D_024": "ACTIVE", "D_025": "ACTIVE",
         "authorial_selection_confirmed": False, "selection_id": None,
         "physical_material_assignments": 0, "additional_engine_runs": 0,
         "scientific_promotion": False}
PROVIDER_MATRIX = Path("experiments/plate58_deforming_explore_v1/"
                       "R6_G2_G3_INTEGRATED_PHYSICAL_PROVIDER_MATRIX_20261121.json")


def coverage(reports):
    totals = Counter()
    for report in reports.values():
        summary = report["summary"]
        totals["regional_columns"] += summary["crust"]["columns"]
        for row in summary.values():
            totals["layer_profiles"] += row["columns"]
            totals["depth_samples"] += 5 * row["columns"]
            totals["native_exact"] += row["native_exact_depth_hits"]
            totals["additional_source_coordinate"] += row["additional_source_link_depth_hits"]
            totals["combined"] += row["combined_depth_hits"]
            totals["complete_any_profiles"] += row["all_five_any_candidate_columns"]
            totals["complete_same_recipe_profiles"] += row["same_recipe_complete_columns"]
        totals["physical_material_assignments"] += report["physical_material_assignments"]
    totals["unmatched"] = totals["depth_samples"] - totals["combined"]
    return dict(totals)


def verify_replayed_reports(reports, receipt):
    need({str(e): r["summary"] for e, r in reports.items()} == receipt["summaries"]
         and coverage(reports) == receipt["aggregate"], "C06_C05R_COVERAGE_DRIFT")


def replay(root):
    receipt = read(RECEIPT)
    folder = prior.OUT
    need(receipt["manifest_sha256"] == PIN and receipt["source_sha"] == SOURCE
         and receipt["archive"] == folder.name and receipt["exit"] == 0
         and receipt["regression_passed"] == receipt["regression_total"] == 223
         and receipt["additional_engine_runs"] == 0, "C06_OPERATOR_RECEIPT")
    manifest = prior.pinned_archive(folder, PIN, receipt["members"], SOURCE, receipt["archive_schema"])
    need(manifest["C04_manifest_sha256"] == prior.v.PIN
         and manifest["C05_manifest_sha256"] == prior.PIN
         and manifest["status"] == receipt["status"] == prior.STATUS
         and manifest["source_design_links"] == 2, "C06_C05R_PARENT_SCOPE")
    library, regions, packets = prior.load_inputs()
    rebuilt_lib, c04_report = prior.v.replay_c04()
    templates, original_pt, source_handoff, source = prior.v.replay_source(root)
    need(rebuilt_lib == library, "C06_C04_REPLAY")
    for e, template, pt in zip((8, 16), templates, original_pt, strict=True):
        rebuilt = prior.v.compile_region(e, template, pt, c04_report, library["states"])
        need(rebuilt == regions[e], "C06_C05_ORIGINAL_SOURCE_REPLAY")
    links = prior.design_links(library, regions)
    need(list(links.values()) == read(folder / "SOURCE_DESIGN_LINKS.json"), "C06_DESIGN_LINK_DRIFT")
    reports = {e: prior.group_region(r, packets[e], library["states"], links)
               for e, r in regions.items()}
    # The writer serializes Python coordinate tuples as JSON arrays.
    for e, report in reports.items():
        name = f"REGION_{e}X{e}_HYPOTHESIS_DESIGN.json"
        need(json.loads(json.dumps(report)) == read(folder / name), "C06_GROUP_MEMBERSHIP_DRIFT")
    verify_replayed_reports(reports, receipt)
    evidence = {"independent_archive_replay": "PASS", "operator_receipt": receipt,
                "parent_manifest_sha256": {"C04": prior.v.PIN, "C05": prior.PIN},
                "source_manifest_sha256": source, "design_links": list(links.values()),
                "aggregate": coverage(reports),
                "groups": {str(e): {k: g["source_parent_ids"] for k,g in r["groups"].items()}
                           for e,r in reports.items()}, **SCOPE}
    return library, reports, packets, source_handoff, evidence


def load_native(root):
    receipt = read(HERE / "s3_d12_fair_native_membership_receipt_v1.json")
    manifest_path = d12.OUT / "MANIFEST.json"
    need(not d12.OUT.is_symlink() and not manifest_path.is_symlink()
         and file_sha(manifest_path) == receipt["manifest_sha256"], "C06_D12_MANIFEST")
    manifest = read(manifest_path)
    names = {name + ".txt" for name in receipt["classes"]}
    need(set(manifest["files"]) == names and set(inventory(d12.OUT)) == names | {"MANIFEST.json"}
         and manifest["schema"] == "R6_T0_B6N8N_EXACT_MEMBERSHIP_V1"
         and manifest["field_sha256"] == provider.FIELD_SHA
         and manifest["plate_sha256"] == provider.PLATE_SHA
         and manifest["boundary_git_blob"] == d12.BOUNDARY_BLOB
         and all(manifest[k] == prior.c.SCOPE[k] for k in prior.c.SCOPE if k in manifest)
         and manifest["material_assignments"] == 0, "C06_D12_SCOPE")
    memberships = {}
    index = provider.source_index(root)
    for name, row in receipt["classes"].items():
        filename = name + ".txt"
        need(manifest["files"][filename] == row["sha256"] == index["membership_sha256"][name],
             "C06_D12_CLASS_PIN")
        body = (d12.OUT / filename).read_bytes()
        members = body.decode("utf-8").splitlines()
        need(file_sha(d12.OUT / filename) == row["sha256"]
             and len(members) == row["count"] and members == sorted(set(members))
             and all(provider.CELL_ID.fullmatch(cell) for cell in members)
             and body == ("".join(cell + "\n" for cell in members)).encode(),
             "C06_D12_MEMBERSHIP_DRIFT")
        for cell in members:
            memberships.setdefault(cell, []).append(name)
    fields = provider.pinned_npz(d12.FIELD, provider.FIELD_SHA)
    part = provider.pinned_npz(d12.PLATE, provider.PLATE_SHA)
    mesh = load_canonical_mesh(root)
    return fields, part, mesh, memberships


def classify_support(native_cells, owner_id, owner_domain, mask, mixed):
    """Classify support on native cells and retain PRE's numerical owner."""
    by_id = {x["cell_id"]: x for x in native_cells}
    need(len(by_id) == len(native_cells), "C06_DUPLICATE_NATIVE_SUPPORT")
    need(all(type(x["crust_domain_id"]) is int and x["crust_domain_id"] in DOMAINS
             for x in native_cells), "C06_CRUST_DOMAIN_UNBOUND")
    owner = by_id.get(owner_id)
    need(owner is not None and owner_id == min(by_id) and owner["crust_domain_id"] == owner_domain,
         "C06_PRE_OWNER_DRIFT")
    domains = {x["crust_domain_id"] for x in native_cells}
    plates = sorted({x["plate_id"] for x in native_cells})
    need(mask == sum(1 << (d-1) for d in domains) and mixed == (len(domains) > 1),
         "C06_PRE_INCIDENT_SUPPORT_DRIFT")
    if mixed or len(plates) > 1:
        return "MIXED_OR_CONFLICTING_SUPPORT", None, plates
    if any("ADMITTED_INITIALIZER_SUPPORT" not in x["d12_classes"] for x in native_cells):
        return "UNKNOWN", None, plates
    role = "OCEANIC" if domains == {1} else "CONTINENTAL" if domains <= {2,3,4,5,6} else None
    return ("SOURCE_DERIVED_CONDITIONAL" if role else "UNKNOWN"), role, plates


def geological(root, packets):
    fields, part, mesh, memberships = load_native(root)
    wanted = {n for packet in packets.values() for n in packet["original_parent_node_order"]}
    incident = defaultdict(set)
    for i, tri in enumerate(mesh.triangles):
        for n in wanted.intersection(map(int, tri)):
            incident[n].add(int(mesh.triangle_parent_face[i]))
    boundary = defaultdict(list)
    for edge, name in zip(mesh.boundary_edge_nodes, mesh.boundary_ids, strict=True):
        for n in wanted.intersection(edge):
            boundary[n].append(name)
    result = {}
    for e, packet in packets.items():
        base = prior.s2.BASE
        core = source_core_geometry(base / "PLATE58_G3_A_OUTER_MULTISCALE_NEW_01",
                                    base / "PLATE58_G3_A_MECHANICAL_INTERFACE_NEW_01",
                                    base / "PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01", e)
        need(core["source_FEG_sha256"] == packet["source_hashes"]["original_FEG_sha256"]
             and core["source_PRE_sha256"] == packet["source_hashes"]["original_PRE_sha256"],
             "C06_FEG_PRE_BINDING")
        for tid, nodes in packet["source_original_full_basal_triangle_nodes"].items():
            need(set(nodes) == set(map(int, mesh.triangles[int(tid)-1])), "C06_FEG_NATIVE_TRIANGLE_DRIFT")
        rows = {}
        for n in packet["original_parent_node_order"]:
            pre = core["source_PRE"][n]
            need(handoff.content_sha(pre) == packet["source_pre_record_sha256_by_parent_node"][str(n)],
                 "C06_PRE_RECORD")
            cells = []
            for i in sorted(incident[n]):
                r, col = int(part["face_row"][i]), int(part["face_col"][i])
                cell = f"R6G1D-R{r:03d}-C{col:03d}"
                cells.append({"cell_id": cell, "plate_id": int(part["face_plate_id"][i]),
                              "crust_domain_id": int(fields["physical_crust_domain_id"][r,col]),
                              "crust_domain_name": DOMAINS[int(fields["physical_crust_domain_id"][r,col])],
                              "continental_thermal_domain_id": int(fields["continental_thermal_domain_id"][r,col]),
                              "d12_classes": sorted(memberships[cell]),
                              "authority": "DIRECT_SOURCE_NATIVE_CELL_CLASSIFICATION"})
            owner = f"R6G1D-R{int(pre['owner_row']):03d}-C{int(pre['owner_column']):03d}"
            status, role, plates = classify_support(cells, owner, pre["owner_domain_id"],
                                                     pre["incident_domain_mask"], bool(pre["mixed_support"]))
            rows[str(n)] = {"parent_node_id": n, "native_cells": cells, "native_plate_ids": plates,
                            "boundary_ids": sorted(boundary[n]), "fault_side_assignment": None,
                            "original_FEG_lat_lon_deg": core["source_lat_lon_deg"][n],
                            "pre_numerical_owner_cell": owner, "source_PRE": pre,
                            "PRE_authority": "AUTHORED_REFERENCE_THERMOPHYSICAL_MODEL",
                            "support_status": status, "conditional_crust_role": role,
                            "natural_lithology": None, "physical_assignment": None}
        result[str(e)] = {"source_hashes": packet["source_hashes"], "nodes": rows,
                          "status_counts": dict(Counter(x["support_status"] for x in rows.values())),
                          "local_triple_junctions": packet["source_actual_3plus_plate_junctions"],
                          "outer_cut_edges": packet["source_external_cut_edges"],
                          "fault_ownership_status": "SIDED_FAULT_AUTHORITY_UNRESOLVED"}
    return {"field_sha256": provider.FIELD_SHA, "plate_partition_sha256": provider.PLATE_SHA,
            "D12_manifest_sha256": file_sha(d12.OUT / "MANIFEST.json"), "regions": result, **SCOPE}


def provider_identity(state):
    model = state["model_identity"]
    rec = state["provider_record"]
    return {
        "provider": rec.get("provider", "MAGEMin_C"),
        "model_identity": model,
        "native_chemistry_sha256": state["native_chemistry_sha256"],
        "source_chemistry_sha256": state["source_chemistry_sha256"],
        "phase_and_fluid_policy": {
            "native_configuration_identity": model,
            "application_policy": "UNSELECTED",
            "bulk_inventory_does_not_authorize_free_fluid": True,
            "pore_pressure_and_fugacity": None,
        },
    }


def query_identity(state, sample):
    p = sample["conditional_delta_P_kbar"]
    t = sample["source_T_K"]
    need(math.isfinite(p) and p >= 0 and math.isfinite(t) and t > 0
         and sample["absolute_pressure_pa"] is None, "C06_PT_OR_PRESSURE_AUTHORITY")
    return {**provider_identity(state), "conditional_delta_P_kbar_hex": float(p).hex(),
            "source_T_K_hex": float(t).hex(), "absolute_pressure_pa": None}


def eligible(proxy, node):
    role = proxy["role"]
    if role == "ENGINEERING_ONLY":
        return True  # explicitly unresolved support may be considered only by the author
    if node["support_status"] != "SOURCE_DERIVED_CONDITIONAL":
        return False
    if role == "LITHOSPHERIC_MANTLE":
        return node["source_PRE"]["mantle_lithosphere_thickness_m"] > 0
    return node["conditional_crust_role"] == role


def comparison_kind(state_key, sample):
    if state_key in sample["native_exact_keys"]:
        return "EXISTING_NATIVE_EXACT"
    if state_key in sample["source_design_link_keys"]:
        return "EXISTING_SOURCE_LINKED"
    return None


def plan(library, reports, geology, contract):
    need(contract["schema"] == "R6_C06_REGIONAL_MATERIAL_HYPOTHESIS_CONTRACT_V1"
         and contract["selection_id"] is None and contract["authorial_selection_confirmed"] is False
         and contract["material_assignments"] == 0
         and all(contract["governance"][key] == SCOPE[key] for key in contract["governance"]),
         "C06_HYPOTHESIS_SELECTED")
    states = library["states"]
    alternatives = {}
    queries = {}
    for extent, report in reports.items():
        support = geology["regions"][str(extent)]["nodes"]
        group_by_node = {str(n): g for g in report["groups"].values() for n in g["source_parent_ids"]}
        need(set(group_by_node) == set(support), "C06_GROUP_GEOLOGY_MISMATCH")
        options = []
        for proxy in contract["proxies"]:
            relevant = {key: state for key,state in states.items()
                        if (state["provider_record"].get("case") or
                            state["provider_record"].get("recipe")) in proxy["cases"]}
            families = defaultdict(list)
            for key, state in relevant.items():
                identity = provider_identity(state)
                families[prior.q.digest(identity)].append(key)
            need(relevant and {states[key]["provider_record"].get("case") or
                               states[key]["provider_record"].get("recipe") for key in relevant}
                 == set(proxy["cases"]), "C06_PROXY_RECIPE_NOT_IN_LIBRARY")
            matched = set()
            counts = Counter()
            option_queries = set()
            supported = [node for node,row in support.items() if eligible(proxy,row)]
            envelopes = {
                family: ((min(states[k]["P_kbar"] for k in keys), max(states[k]["P_kbar"] for k in keys)),
                         (min(states[k]["T_C"] for k in keys), max(states[k]["T_C"] for k in keys)))
                for family, keys in families.items()
            }
            for node in supported:
                for sample in group_by_node[node]["layers"][proxy["layer"]]["depths"]:
                    for family, keys in families.items():
                        hits = {key: comparison_kind(key, sample) for key in keys
                                if comparison_kind(key, sample) is not None}
                        no_eq = (sample["fraction_of_layer"] == 0 and proxy["layer"] == "crust"
                                 and sample["conditional_delta_P_kbar"] == 0)
                        (p_lo, p_hi), (t_lo, t_hi) = envelopes[family]
                        p = sample["conditional_delta_P_kbar"]
                        t = sample["source_T_K"] - 273.15
                        if hits:
                            domain = "ARCHIVED_POINT_RESEARCH_ONLY"
                        elif not (p_lo <= p <= p_hi and t_lo <= t <= t_hi):
                            domain = "OUTSIDE_ARCHIVED_RECIPE_COMPARATIVE_ENVELOPE"
                        else:
                            domain = "INSIDE_ARCHIVED_EXTREMA_UNQUALIFIED"
                        # Archive extrema are a diagnostic, not a domain of scientific validity.
                        if hits:
                            kind = ("EXISTING_NATIVE_EXACT" if "EXISTING_NATIVE_EXACT" in hits.values()
                                    else "EXISTING_SOURCE_LINKED")
                        elif no_eq:
                            kind = "INHERITED_PROPERTIES_REVIEW_NO_DEFAULT_EQUILIBRIUM"
                        else:
                            kind = "MISSING_CONDITIONAL_PT_DOMAIN_NOT_QUALIFIED"
                        counts[kind] += 1
                        matched.update(hits)
                        identity = query_identity(states[keys[0]], sample)
                        qkey = prior.q.digest(identity)
                        row = queries.setdefault(qkey, {
                            "identity": identity, "comparison": kind, "archived_state_keys": hits,
                            "existing_recipe_state_keys": sorted(keys),
                            "provider_domain": domain,
                            "absolute_pressure_blocked": True,
                            "chemistry_authority_blocked": True,
                            "execution_authorized": False, "support": [],
                        })
                        need(row["comparison"] == kind and row["archived_state_keys"] == hits,
                             "C06_DEDUP_POLICY_OR_IDENTITY_DRIFT")
                        row["support"].append({"extent": extent, "parent_node_id": int(node),
                                               "depth_m": sample["depth_m"], "layer": proxy["layer"],
                                               "proxy": proxy["id"], "fraction": sample["fraction_of_layer"]})
                        option_queries.add(qkey)
            options.append({**proxy, "applicable_support": supported,
                            "unsupported_parent_nodes": sorted(set(support)-set(supported),key=int),
                            "mixed_support": [n for n,r in support.items()
                                              if r["support_status"] == "MIXED_OR_CONFLICTING_SUPPORT"],
                            "available_recipe_state_keys": sorted(relevant),
                            "comparatively_reusable_keys": sorted(matched),
                            "target_counts_by_occurrence": dict(counts),
                            "unique_query_ids": sorted(option_queries),
                            "authorizable_now": False, "selection_id": None,
                            "authority_required": "Explicit bulk proxy, geographic support and independent fluid/redox policy",
                            "constitutive_law": "UNBOUND: lab law, applicable P/T/rate, water and pressure required",
                            "hydration_and_redox": "Native variants only; approve inventory and redox separately from pore pressure and fugacity",
                            "physical_assignment": None})
        alternatives[str(extent)] = {"extent": extent, "primary": extent == 8,
                                     "sensitivity_not_mesh_convergence": extent == 16,
                                     "alternatives": options, **SCOPE}
    return alternatives, {
        "unique_candidate_queries": len(queries),
        "unique_by_comparison": dict(Counter(row["comparison"] for row in queries.values())),
        "unique_by_provider_domain": dict(Counter(row["provider_domain"] for row in queries.values())),
        "executable_new_queries": 0,
        "pressure_policy": "No absolute P authority. Conditional zero is not a solver pressure.",
        "domain_policy": "Archive points do not certify a connected provider envelope. Cold felsic remain unqualified.",
        "minimization_policy": "Review physical property need then choose proxy and provider. Missing comparisons are not required solves.",
        "queries": queries, **SCOPE,
    }


def closure(root, packets, source_handoff):
    minimum_file = root / "R6_SHELLSET_MINIMUM_THERMOMECHANICAL_STATE_CONTRACT.json"
    minimum = read(minimum_file)
    pressure = minimum["parent_pressure_gap"]
    need(pressure["external_absolute_pressure_field_required"] is False
         and pressure["external_eos_density_required"] is False, "C06_MINIMUM_CONTRACT_DRIFT")
    matrix = read(root / PROVIDER_MATRIX)
    need(tuple(x["id"] for x in matrix["groups"]) == handoff.GROUP_NAMES, "C06_COUPLED_GROUP_DRIFT")
    support = {}
    for extent, packet in packets.items():
        counts = packet["counts"]
        sc = source_handoff[str(extent)]
        nodes = counts["original_parent_nodes"]
        row = {"parent_nodes": nodes, "EN_DOF": 2*nodes,
               "outer_cut_edges": len(sc["line_tractions_by_edge"]),
               "exterior_basal_facets": len(sc["basal_tractions_by_triangle"]),
               "core_basal_facets": counts["source_core_basal_triangles"],
               "full_basal_facets": counts["source_original_full_basal_triangles"]}
        need(tuple(row.values()) == {8:(81,162,32,120,8,128),16:(289,578,64,504,8,512)}[extent],
             "C06_COUPLED_COUNTS")
        support[str(extent)] = row
    return {"SHELLSET_MINIMUM": {
                "contract_sha256": file_sha(minimum_file), "external_absolute_pressure_required": False,
                "full_thermodynamic_coverage_required": False,
                "minimum_node_fields": minimum["shells_consumed_nodal_state"]["minimum_node_fields"],
                "configuration_contract": minimum["model_configuration_parameters"],
                "native_toolchain": minimum["minimum_toolchain"],
                "available": ["Original FEG elevations and topology", "PRE thickness, thermal profiles and reference properties"],
                "unresolved": ["Applicability of PRE reference properties for selected native configuration",
                               "Continuum creep and fault/friction parameters, basal and lateral conditions",
                               "Regional runtime, frame, solver and G4 qualification"],
                "next": "Approve a native reference material/constitutive configuration and regional BC/mechanical support independently of equilibrium campaign",
            }, "G2_G3_FULL_COUPLED": {
                "provider_matrix_sha256": file_sha(root / PROVIDER_MATRIX),
                "groups": matrix["groups"], "support": support,
                "hypothesis_can_inform": ["g2_material_and_phases", "g2_pressure_water", "g2_lab_law_and_coverage"],
                "still_independent": list(handoff.GROUP_NAMES[3:]),
                "core_basal_traction": None, "GPE_load": None, "mechanical_LAB": None,
                "rule": "Thermal LAB and Euler motion do not fix mechanical LAB or basal traction",
            }, **SCOPE}


def write_once(output, reports, metadata):
    need(not output.exists() and not output.is_symlink(), "C06_OUTPUT_EXISTS")
    for name, record in reports.items():
        need(Path(name).name == name and name != "MANIFEST.json"
             and all(record.get(key) == value for key, value in SCOPE.items()),
             "C06_OUTPUT_UNAUTHORIZED_SCOPE")
    payload = {name: json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n"
               for name,value in reports.items()}
    output.mkdir(exist_ok=False)
    for name, body in payload.items():
        with (output/name).open("x", encoding="utf-8") as handle:
            handle.write(body)
    prior.s2.write_json(output/"MANIFEST.json", {
        "schema": "R6_C06_REGIONAL_MATERIAL_HYPOTHESIS_MANIFEST_V1", "status": STATUS,
        "files": inventory(output), **metadata, **SCOPE,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--offline-regional-hypothesis-only", required=True, action="store_true")
    args = parser.parse_args()
    root, head = prior.s2.verify_checkout()
    need(head == args.expected_sha and not prior.s2.git(root,"status","--porcelain"), "C06_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink() and not OUT.resolve().is_relative_to(root),
         "C06_OUTPUT_EXISTS_OR_IN_REPO")
    library, reports, packets, source_handoff, receipt = replay(root)
    geology = geological(root, packets)
    contract = read(CONTRACT)
    alternatives, campaign = plan(library, reports, geology, contract)
    routes = closure(root, packets, source_handoff)
    choices = [{key: option[key] for key in ("id", "role", "cases", "qualification", "authorizable_now")}
               | {"eligible_parent_count": len(option["applicable_support"])}
               for option in alternatives["8"]["alternatives"]]
    decision = {
        "scope": "Approve a conditional research proxy only. No placements or solver authority.",
        "choices": ["Approve one applicable bulk proxy with parent support and explicit exclusions",
                    "Choose hydration and redox within native provider chemistry and state limits",
                    "Approve absolute loading, pore pressure and fluid policy separately",
                    "Select minimum native ShellSet or coupled G2/G3 and bind independent BC/loads/faults"],
        "alternatives_in_primary_scope": choices,
        "primary_extent": 8, "extent_16_is_domain_sensitivity": True,
        "engineering_fallback": "Homogeneous proxy requires explicit approval of all included support, including mixed nodes",
        "authorization": None, **SCOPE,
    }
    write_once(OUT, {
        "C05R_REPLAY.json": receipt, "GEOLOGICAL_SOURCE_AUTHORITY.json": geology,
        "REGION_8X8_MATERIAL_ALTERNATIVES.json": alternatives["8"],
        "REGION_16X16_SENSITIVITY.json": alternatives["16"],
        "TARGETED_THERMODYNAMIC_CAMPAIGN_PLAN.json": campaign,
        "PHYSICAL_CLOSURE_ROUTE_MATRIX.json": routes, "AUTHORIAL_DECISION_SHEET.json": decision,
    }, {"source_sha": head, "C05R_manifest_sha256": PIN,
        "contract_sha256": file_sha(CONTRACT), "receipt_sha256": file_sha(RECEIPT),
        "library_states": len(library["states"]), "source_chemistries": library["source_chemistry_count"],
        "previous_research_solves": library["source_solver_processes_legacy"],
        "reference_diagnostic_equilibria": library["reference_diagnostic_equilibria_excluded"],
        "cold_MORB_research_candidates": library["conditional_cold_MORB_state_count"]})
    print("C06_MANIFEST_SHA256", file_sha(OUT/"MANIFEST.json"), flush=True)
    print(STATUS, flush=True)


if __name__ == "__main__":
    main()
