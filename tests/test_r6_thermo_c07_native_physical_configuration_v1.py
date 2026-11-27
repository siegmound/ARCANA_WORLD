import json
from pathlib import Path

import pytest

from experiments.r6_thermo_provider_pilot_v1 import run_c07_native_physical_configuration as c07


def node(domains=(3,), plates=(5,), admitted=(True,)):
    cells = [{"cell_id": f"cell{i}", "crust_domain_id": d, "plate_id": p,
              "d12_classes": ["ADMITTED_INITIALIZER_SUPPORT"] if active else ["ZERO_AGE_RIDGE"]}
             for i,(d,p,active) in enumerate(zip(domains, plates, admitted, strict=True))]
    return {"native_cells": cells, "native_plate_ids": list(set(plates)),
            "pre_numerical_owner_cell": "cell0", "boundary_ids": ["edge"] if len(set(plates))>1 else [],
            "source_PRE": {"mantle_lithosphere_thickness_m": 90000},
            "support_status": "C06_ORIGINAL", "fault_side_assignment": None}


def test_c06_manifest_pin_rejects_wrong_bytes(tmp_path):
    receipt = c07.read(c07.RECEIPT)
    folder = tmp_path/receipt["archive"]
    folder.mkdir()
    (folder/"MANIFEST.json").write_text("{}")
    with pytest.raises(ValueError, match="C07_C06_MANIFEST_PIN"):
        c07.verify_archive(folder, receipt)


def test_c06_member_mutation_fails_exact_inventory(tmp_path, monkeypatch):
    receipt = c07.read(c07.RECEIPT)
    folder = tmp_path/receipt["archive"]
    folder.mkdir()
    for name in c07.MEMBERS:
        (folder/name).write_text("{}")
    manifest = {
        "schema": "R6_C06_REGIONAL_MATERIAL_HYPOTHESIS_MANIFEST_V1",
        "source_sha": c07.ENTRY, "status": receipt["status"],
        "files": c07.c06.inventory(folder), "C05R_manifest_sha256": c07.c06.PIN,
        "contract_sha256": c07.sha(c07.c06.CONTRACT), "receipt_sha256": c07.sha(c07.c06.RECEIPT),
        **c07.SCOPE,
    }
    path = folder/"MANIFEST.json"
    path.write_text(json.dumps(manifest))
    pin = c07.sha(path)
    monkeypatch.setattr(c07, "PIN", pin)
    receipt["manifest_sha256"] = pin
    (folder/"AUTHORIAL_DECISION_SHEET.json").write_text('{"selection_id":"changed"}')
    with pytest.raises(ValueError, match="C07_C06_INVENTORY_SCOPE"):
        c07.verify_archive(folder, receipt)


def test_continental_plate_boundary_keeps_coarse_crust_role():
    out = c07.classify_node(node((3,3),(5,8),(True,True)))
    assert out["crust_support"] == "UNIFORM_CONTINENTAL_ROLE"
    assert out["mechanical_support"] == "MULTIPLE_PLATES"
    assert out["boundary_incidence"] and out["sided_ownership"] == "UNRESOLVED"
    assert out["C06_support_status"] == "C06_ORIGINAL"


def test_continental_province_and_ocean_transition_differ():
    assert c07.classify_node(node((2,3),(5,5),(True,True)))["crust_support"] == "MULTIPLE_CONTINENTAL_PROVINCES"
    assert c07.classify_node(node((1,3),(5,5),(True,True)))["crust_support"] == "OCEANIC_CONTINENTAL_TRANSITION"


def test_membership_excluded_remains_ineligible():
    excluded = c07.classify_node(node(admitted=(False,)))
    mixed = c07.classify_node(node((1,3),(5,8),(False,True)))
    assert excluded["membership"] == "EXCLUDED"
    assert mixed["membership"] == "MIXED_ADMISSION"
    assert excluded["crust_support"] == mixed["crust_support"] == "UNKNOWN_OR_EXCLUDED_SOURCE_SUPPORT"


def test_fault_side_cannot_be_fabricated_from_plate_incidence():
    with pytest.raises(ValueError, match="C07_UNVERIFIED_SIDED_OWNERSHIP"):
        c07.classify_node({**node((3,3),(5,8),(True,True)), "fault_side_assignment": 5})


def test_mantle_geometry_independent_of_crust_transition():
    value = c07.classify_node(node((1,3),(5,8),(True,True)))
    assert value["mantle_geometry"] == "AUTHORED_PRE_GEOMETRY"
    assert value["mantle_material_authority"] is None


def test_authority_fields_preserve_reference_units_and_ranges():
    c = c07.native_candidate(Path.cwd())
    nominal = c["parameters"]["reference_densities"]["continental_crust"]
    assert nominal["nominal"] == 2800 and nominal["sensitivity_range"] == [2700,2900]
    assert c["parameters"]["gMean"]["value"] == 9.82
    assert c["parameters"]["temLim"]["physical_solidus"] is False
    with pytest.raises(ValueError, match="C07_PARAMETER_UNIT_OR_VALUE"):
        c07.parameter(nominal, "W m-1 K-1")


def test_reject_eos_or_duplicated_thermal_initialization():
    p = c07.read(c07.CANDIDATE)["proposed_policy"]
    c07.validate_thermal_mode(p)
    for change in (dict(external_eos_density=2800), dict(profile="STOCK_GEOTHERM"),
                   dict(global_crust_rhoBar_override=2800), dict(density="ALREADY_CORRECTED")):
        with pytest.raises(ValueError, match="C07_THERMAL_OR_DENSITY_DOUBLE_COUNT"):
            c07.validate_thermal_mode({**p, **change})


def test_reject_unqualified_high_temperature_creep_at_surface():
    c07.native_creep_coverage([1173.15,1373.15], [1200,1300])
    with pytest.raises(ValueError, match="C07_CREEP_OUTSIDE_DECLARED_THERMAL_DOMAIN"):
        c07.native_creep_coverage([1173.15,1373.15], [280,1200])


def test_missing_boundary_inputs_are_not_zero():
    payload = {"PHYSICAL_CLOSURE_ROUTE_MATRIX.json":{"G2_G3_FULL_COUPLED":{"support":{}}}}
    result = c07.mechanical(payload, {"regions":{}})
    m = result["native_minimum"]
    assert m["outer_cut_conditions"] is m["basal_coupling"] is m["GPE_closure"] is None
    assert m["native_controls"]["trHMax_Pa"] is None


def test_immutable_output_and_no_authorization(tmp_path):
    out = tmp_path/"output"
    with pytest.raises(ValueError, match="C07_OUTPUT_AUTHORITY"):
        c07.write_once(out, {"bad.json": {**c07.SCOPE, "mechanical_solve_authorized": True}}, "head")
    assert not out.exists()
    c07.write_once(out, {"valid.json": c07.SCOPE}, "head")
    digest = c07.sha(out/"MANIFEST.json")
    with pytest.raises(ValueError, match="C07_OUTPUT_EXISTS"):
        c07.write_once(out, {}, "head")
    assert c07.sha(out/"MANIFEST.json") == digest
