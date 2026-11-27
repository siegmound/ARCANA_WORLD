import json
import math
from pathlib import Path

import pytest

from experiments.r6_thermo_provider_pilot_v1 import run_c06_regional_material_hypothesis as c06


def cell(name="N", domain=3, plate=5, admitted=True):
    return {"cell_id": name, "crust_domain_id": domain, "plate_id": plate,
            "d12_classes": ["ADMITTED_INITIALIZER_SUPPORT"] if admitted else []}


def test_manifest_hash_drift_fails_before_member_read(tmp_path):
    (tmp_path / "MANIFEST.json").write_text("{}")
    with pytest.raises(ValueError, match="C05R_MANIFEST_PIN"):
        c06.prior.pinned_archive(tmp_path, "0"*64, [], "source", "schema")


def test_extra_archive_member_rejected_with_valid_manifest_hash(tmp_path):
    (tmp_path / "unexpected.json").write_text("{}")
    manifest = {"files": {}, "source_sha": "source", "schema": "schema",
                "additional_engine_runs": 0, "scientific_promotion": False, **c06.prior.c.SCOPE}
    path = tmp_path / "MANIFEST.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="C05R_ARCHIVE_SCOPE"):
        c06.prior.pinned_archive(tmp_path, c06.file_sha(path), [], "source", "schema")


def test_operator_aggregate_drift_detected():
    rec = c06.read(c06.RECEIPT)
    reports = {int(k): {"summary": r, "physical_material_assignments": 0}
               for k,r in rec["summaries"].items()}
    c06.verify_replayed_reports(reports, rec)
    rec["aggregate"]["combined"] += 1
    with pytest.raises(ValueError, match="C06_C05R_COVERAGE_DRIFT"):
        c06.verify_replayed_reports(reports, rec)


def test_native_and_source_hits_remain_distinct():
    row = {"native_exact_keys": ["a"], "source_design_link_keys": ["b"]}
    assert c06.comparison_kind("a", row) == "EXISTING_NATIVE_EXACT"
    assert c06.comparison_kind("b", row) == "EXISTING_SOURCE_LINKED"
    assert c06.comparison_kind("c", row) is None


def test_density_does_not_authorize_nodal_lithology():
    with pytest.raises(ValueError, match="C06_CRUST_DOMAIN_UNBOUND"):
        c06.classify_support([{**cell(domain=0), "density": 2890}], "N", 0, 0, False)


def test_owner_must_be_a_verified_incident_cell():
    with pytest.raises(ValueError, match="C06_PRE_OWNER_DRIFT"):
        c06.classify_support([cell()], "not-an-incident-cell", 3, 4, False)


def test_plate_conflict_and_unadmitted_support_retained():
    assert c06.classify_support([cell(), cell("S", plate=8)], "N", 3, 4, False)[:2] == (
        "MIXED_OR_CONFLICTING_SUPPORT", None)
    assert c06.classify_support([cell(admitted=False)], "N", 3, 4, False)[:2] == ("UNKNOWN", None)


def state():
    return {"model_identity": "model", "native_chemistry_sha256": "native",
            "source_chemistry_sha256": "source", "provider_record": {}}


def test_query_keys_distinguish_one_ulp_native_chemistry_and_model():
    sample = {"source_T_K": 280.0, "conditional_delta_P_kbar": 0.0, "absolute_pressure_pa": None}
    q = c06.query_identity(state(), sample)
    assert q == c06.query_identity(state(), dict(sample))
    assert q != c06.query_identity(state(), {**sample, "source_T_K": math.nextafter(280, math.inf)})
    assert q != c06.query_identity({**state(), "native_chemistry_sha256": "other"}, sample)
    assert q != c06.query_identity({**state(), "model_identity": "other"}, sample)


def test_near_surface_keeps_absolute_pressure_unknown():
    sample = {"source_T_K": 280.0, "conditional_delta_P_kbar": 0.0, "absolute_pressure_pa": None}
    assert c06.query_identity(state(), sample)["absolute_pressure_pa"] is None
    with pytest.raises(ValueError, match="C06_PT_OR_PRESSURE_AUTHORITY"):
        c06.query_identity(state(), {**sample, "absolute_pressure_pa": 0})


def test_planner_rejects_implicit_selection():
    contract = c06.read(c06.CONTRACT)
    contract["selection_id"] = "unauthorized"
    with pytest.raises(ValueError, match="C06_HYPOTHESIS_SELECTED"):
        c06.plan({}, {}, {}, contract)


def test_route_contracts_keep_independent_dependencies():
    routes = c06.closure(Path.cwd(), {}, {})
    assert routes["SHELLSET_MINIMUM"]["external_absolute_pressure_required"] is False
    full = routes["G2_G3_FULL_COUPLED"]
    assert tuple(row["id"] for row in full["groups"]) == c06.handoff.GROUP_NAMES
    assert full["core_basal_traction"] is full["GPE_load"] is None


def test_output_is_write_once_and_rejects_assignment(tmp_path):
    out = tmp_path/"new"
    with pytest.raises(ValueError, match="C06_OUTPUT_UNAUTHORIZED_SCOPE"):
        c06.write_once(out, {"asset.json": {**c06.SCOPE, "material_assignments": 1}}, {})
    assert not out.exists()
    c06.write_once(out, {"asset.json": c06.SCOPE}, {})
    digest = c06.file_sha(out/"asset.json")
    with pytest.raises(ValueError, match="C06_OUTPUT_EXISTS"):
        c06.write_once(out, {"asset.json": c06.SCOPE}, {})
    assert c06.file_sha(out/"asset.json") == digest


def test_planner_deduplicates_queries_but_retains_both_parent_occurrences():
    contract = c06.read(c06.CONTRACT)
    contract["proxies"] = [contract["proxies"][0]]
    sample = {"depth_m": 0, "fraction_of_layer": 0, "source_T_K": 280,
              "conditional_delta_P_kbar": 0, "absolute_pressure_pa": None,
              "native_exact_keys": [], "source_design_link_keys": []}
    report = {"groups": {"g": {"source_parent_ids": [1, 2],
                               "layers": {"crust": {"depths": [sample]}}}}}
    node = {"support_status": "SOURCE_DERIVED_CONDITIONAL",
            "conditional_crust_role": "CONTINENTAL"}
    geology = {"regions": {"8": {"nodes": {"1": node, "2": node}}}}
    native = {**state(), "P_kbar": 10, "T_C": 500,
              "provider_record": {"case": "C02_UCC_BASE"}}
    options, campaign = c06.plan({"states": {"native": native}}, {8: report}, geology, contract)
    assert campaign["unique_candidate_queries"] == 1
    query, = campaign["queries"].values()
    assert [x["parent_node_id"] for x in query["support"]] == [1, 2]
    assert query["comparison"] == "INHERITED_PROPERTIES_REVIEW_NO_DEFAULT_EQUILIBRIUM"
    assert query["identity"]["absolute_pressure_pa"] is None
    assert options["8"]["alternatives"][0]["physical_assignment"] is None
