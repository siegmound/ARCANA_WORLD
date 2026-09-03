import inspect
import json
from pathlib import Path

import pytest

import arcana_worldsim.scientific_engines.r433_target_binding_static_adjudication_geonomics_runtime_preflight as m


def _records():
    out = []
    for i in range(4):
        out.append({
            "window_id": f"W{i}",
            "domain": "d",
            "binding_kind": "AUTHORIZED_SELECTOR_SOURCE_IDENTITY",
            "binding_disposition": "EXPLICIT_SOURCE_IDENTITY_AUTHORITY_FROZEN",
            "implementation_ready": True,
        })
    out.append({
        "window_id": "Wp",
        "domain": "d",
        "binding_kind": "AUTHORIZED_SELECTOR_SOURCE_IDENTITY",
        "binding_disposition": "SOURCE_IDENTITY_AUTHORITY_PENDING_R433_STATIC_ADJUDICATION",
        "implementation_ready": False,
    })
    for i in range(39):
        out.append({
            "window_id": f"C{i}",
            "domain": "d",
            "binding_kind": "PRE_RESULT_SELECTOR_RULE_CATALOG_EXTENSION",
            "binding_disposition": "CATALOG_EXTENSION_AUTHORITY_IMPLEMENTED_NONNUMERIC_PENDING_R433_ADJUDICATION",
            "implementation_ready": True,
            "selector_chosen_in_r432": None,
        })
    for i in range(12):
        out.append({
            "window_id": f"D{i}",
            "domain": "d",
            "binding_kind": "TARGET_DESIGN_OBSERVABLE_BINDING",
            "binding_disposition": "OBSERVABLE_BINDING_AUTHORITY_IMPLEMENTED_NONNUMERIC_PENDING_R433_EXACT_SOURCE_BINDING",
            "implementation_ready": True,
        })
    out.append({
        "window_id": "P",
        "domain": "d",
        "binding_kind": "PRIMARY_MAPPING_AUTHORITY_DEFINITION",
        "binding_disposition": "PRIMARY_MAPPING_AUTHORITY_DEFINITION_IMPLEMENTED_NONNUMERIC_PENDING_R433_ELIGIBILITY_ADJUDICATION",
        "implementation_ready": True,
        "mapping_class_change_authorized": False,
        "numeric_value_change_authorized": False,
    })
    assert len(out) == 57
    return out


def test_target_static_adjudication_preserves_4_plus_1_and_never_executes():
    r = m._static_adjudicate_target_bindings({"records": _records()})
    assert r["record_count"] == 57
    assert r["blocked_count"] == 0
    assert r["exact_source_identity_future_numeric_execution_candidate_count"] == 4
    assert r["source_identity_authority_gap_deferred_count"] == 1
    assert r["catalog_extension_rule_selection_deferred_count"] == 39
    assert r["observable_binding_exact_source_deferred_count"] == 12
    assert r["primary_mapping_authority_frozen_count"] == 1
    assert r["numeric_target_execution_authorized_count"] == 0


def test_selector_requirements_have_no_defaults():
    inv = [{
        "arrays": [
            {"key": "parent_member_indices"},
            {"key": "candidate_ids"},
            {"key": "snapshot_age_ka"},
        ]
    }]
    r = m._selector_requirements(m.J18, inv)
    assert r["explicit_frozen_selector_bundle_required_before_native_params"] is True
    assert r["default_selector_values"] is None
    assert set(r["selector_requirements"]) == {
        "parent_member_indices", "candidate_ids", "snapshot_age_ka"
    }


def test_npz_inventory_is_metadata_only(tmp_path):
    import numpy as np
    p = tmp_path / "x.npz"
    np.savez(p, axis=np.array([1, 2, 3]), cube=np.zeros((2, 3, 4)))
    r = m._npz_inventory(p)
    assert r["array_count"] == 2
    by = {x["key"]: x for x in r["arrays"]}
    assert by["axis"]["axis_values_if_small"] == [1, 2, 3]
    assert by["cube"]["shape"] == [2, 3, 4]


def test_r433_source_does_not_import_or_call_geonomics():
    s = inspect.getsource(m)
    assert "import geonomics" not in s
    assert "gnx.make_model(" not in s
    assert "run_default_model(" not in s


def test_exact_three_jobs_and_r434_selector_authority_next():
    assert set(m.GEONOMICS_JOBS) == {m.J14, m.J18, m.J21}
    assert "RUNTIME_SELECTOR_AUTHORITY_FREEZE" in m.NEXT
    assert "NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT" in m.NEXT
