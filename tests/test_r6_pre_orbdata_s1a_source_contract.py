"""Windows static contract checks for the S1A Fortran source change.

These assertions inspect source and the canonical fixture. They do not execute
Fortran, OrbData, SHELLS, or establish NVHPC/FAIR qualification.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "external" / "ShellSet-v1.1.0" / "src"
MOD_SHELLSET = (SRC / "MOD_ShellSet.f90").read_text(encoding="utf-8")
ORBDATA = (SRC / "OrbData5.f90").read_text(encoding="utf-8")
PARSER = (SRC / "MOD_ArcanaRuntime.f90").read_text(encoding="utf-8")
MOD_DATA = (SRC / "MOD_Data.f90").read_text(encoding="utf-8")
MAKEFILE = (ROOT / "external" / "ShellSet-v1.1.0" / "Makefile").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json").read_text(encoding="utf-8"))


def test_activation_matrix_is_explicit_and_fail_closed():
    setup = MOD_SHELLSET[MOD_SHELLSET.index("subroutine InputSetup"):MOD_SHELLSET.index("end subroutine", MOD_SHELLSET.index("subroutine InputSetup"))]
    assert "INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat" in setup
    assert "arcDomainExists .neqv. arcLithosphereExists" in setup
    assert "arcDomainExists .and. arcLithosphereExists .and. .not.arcanaRuntimeExists" in setup
    assert "arcDomainExists .and. arcLithosphereExists .and. arcanaRuntimeExists" in setup
    assert "arcanaInputMode=arcanaRuntimeExists" in setup
    assert "'17'" in setup and "'12'" in setup
    op = MOD_SHELLSET[MOD_SHELLSET.index("subroutine OpenInput"):MOD_SHELLSET.index("end subroutine", MOD_SHELLSET.index("subroutine OpenInput"))]
    assert "arcanaRuntimeExists=FileExist" in op
    assert "open(unit=17" in op
    assert "Predecessor ARCANA pair is not valid S1 runtime authority" in op
    assert "Incomplete predecessor ARCANA OrbData pair in INPUT/" in setup
    assert "Stale staged ARCANA runtime package without canonical INPUT authority" in setup
    assert "Canonical ARCANA runtime package was not staged for OrbData" in setup


def test_parser_pins_header_count_and_exact_manifest_field_order():
    assert "ARCANA_NODE_COUNT = 64442" in PARSER
    assert "ARCANA_FIELD_COUNT = 51" in PARSER
    assert "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1" in PARSER
    assert "arcana_worldsim.r6.shellset_owner_bound_runtime.v1" in PARSER
    assert "token_count /= ARCANA_FIELD_COUNT" in PARSER
    assert "ARCANA_RUNTIME_TRAILING_RECORD_OR_DATA" in PARSER
    assert "ARCANA_RUNTIME_NODE_ID_ORDER_OR_DUPLICATE" in PARSER
    assert len(MANIFEST["field_order"]) == 51
    expected_constants = {
        "node_id": "I_NODE", "owner_row": "I_OWNER_ROW", "owner_column": "I_OWNER_COL",
        "owner_domain_id": "I_OWNER_DOMAIN", "incident_domain_mask": "I_DOMAIN_MASK",
        "mixed_support": "I_MIXED", "thermal_class_present": "I_CLASS_PRESENT",
        "owner_thermal_class_id": "I_CLASS_ID", "runtime_branch_code": "I_BRANCH",
        "physical_age_present": "I_AGE_PRESENT", "physical_age_ma": "I_AGE",
        "effective_age_present": "I_EFF_PRESENT", "effective_age_ma": "I_EFF_AGE",
        "surface_temperature_k": "I_SURFACE_T", "surface_heat_flow_w_m2": "I_SURFACE_Q",
        "crust_thickness_m": "I_CRUST", "mantle_lithosphere_thickness_m": "I_MANTLE",
        "lab_depth_m": "I_LAB", "moho_temperature_k": "I_MOHO_T", "moho_flux_w_m2": "I_MOHO_Q",
        "lab_temperature_k": "I_LAB_T", "lab_flux_w_m2": "I_LAB_Q",
        "transient_rate_present": "I_RATE_PRESENT", "transient_rate_k_s": "I_RATE",
        "material_configuration_code": "I_MATERIAL_CONFIG", "crust_material_code": "I_CRUST_MATERIAL",
        "mantle_material_code": "I_MANTLE_MATERIAL", "crust_density_kg_m3": "I_CRUST_RHO",
        "crust_conductivity_w_m_k": "I_CRUST_K", "crust_expansivity_k_1": "I_CRUST_ALPHA",
        "crust_heat_production_w_m3": "I_CRUST_RADIO", "crust_cp_j_kg_k": "I_CRUST_CP",
        "mantle_density_kg_m3": "I_MANTLE_RHO", "mantle_conductivity_w_m_k": "I_MANTLE_K",
        "mantle_expansivity_k_1": "I_MANTLE_ALPHA", "mantle_heat_production_w_m3": "I_MANTLE_RADIO",
        "mantle_cp_j_kg_k": "I_MANTLE_CP", "rho_asthenosphere_kg_m3": "I_RHO_ASTH",
        "rho_water_kg_m3": "I_RHO_WATER", "layer1_z0_m": "I_L1_Z0", "layer1_z1_m": "I_L1_Z1",
        "layer1_c3_k_m3": "I_L1_C3", "layer1_c2_k_m2": "I_L1_C2", "layer1_c1_k_m": "I_L1_C1",
        "layer1_c0_k": "I_L1_C0", "layer2_z0_m": "I_L2_Z0", "layer2_z1_m": "I_L2_Z1",
        "layer2_c3_k_m3": "I_L2_C3", "layer2_c2_k_m2": "I_L2_C2", "layer2_c1_k_m": "I_L2_C1",
        "layer2_c0_k": "I_L2_C0",
    }
    assert list(expected_constants) == MANIFEST["field_order"]
    for index, field in enumerate(MANIFEST["field_order"], 1):
        assert re.search(rf"\b{expected_constants[field]}\s*=\s*{index}\b", PARSER)


def test_parser_fails_closed_for_required_identity_record_and_state_errors():
    for reason in (
        "ARCANA_RUNTIME_HEADER_MISSING",
        "ARCANA_RUNTIME_HEADER_MALFORMED",
        "ARCANA_RUNTIME_BAD_MAGIC",
        "ARCANA_RUNTIME_BAD_SCHEMA",
        "ARCANA_RUNTIME_BAD_NODE_COUNT",
        "ARCANA_RUNTIME_RECORD_MISSING",
        "ARCANA_RUNTIME_RECORD_FIELD_COUNT_INVALID",
        "ARCANA_RUNTIME_RECORD_TOKEN_INVALID",
        "ARCANA_RUNTIME_RECORD_NUMBER_INVALID",
        "ARCANA_RUNTIME_RECORD_NONFINITE",
        "ARCANA_RUNTIME_NODE_ID_ORDER_OR_DUPLICATE",
        "ARCANA_RUNTIME_IDENTITY_OR_FLAG_INVALID",
        "ARCANA_RUNTIME_MATERIAL_BINDING_INVALID",
        "ARCANA_RUNTIME_MATERIAL_VALUE_INVALID",
        "ARCANA_RUNTIME_GOVERNED_GEOMETRY_OR_Q_INVALID",
        "ARCANA_RUNTIME_PROFILE_GEOMETRY_INVALID",
        "ARCANA_RUNTIME_LAYER1_BOUNDARY_MISMATCH",
        "ARCANA_RUNTIME_LAYER2_BOUNDARY_MISMATCH",
        "ARCANA_RUNTIME_GOVERNED_RECORD_COUNTS_MISMATCH",
        "ARCANA_RUNTIME_TRAILING_RECORD_OR_DATA",
    ):
        assert reason in PARSER
    assert "IF (expected_nodes /= ARCANA_NODE_COUNT)" in PARSER
    assert "IF (ALLOCATED(runtime_nodes)) DEALLOCATE(runtime_nodes)" in PARSER
    assert "IEEE_IS_FINITE(values(j))" in PARSER
    assert "IsIntegerInRange(v(I_OWNER_ROW), 0, 179)" in PARSER
    assert "IsIntegerInRange(v(I_OWNER_COL), 0, 358)" in PARSER


def test_package_identity_and_validation_are_pinned_without_claiming_runtime():
    data_path = ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    assert digest == "2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584"
    assert "CALL ValidateRecord(values, i, message)" in PARSER
    assert "branch_count(INT(values(I_BRANCH)))" in PARSER
    assert "branch_count /= (/14258,108,50076/)" in PARSER
    assert "mixed_count /= 2697" in PARSER
    assert "ARCANA_RUNTIME_RIDGE_STATE_INVALID" in PARSER
    assert "v(I_AGE) /= 0.0D0" in PARSER
    assert "v(I_SURFACE_Q) /= 0.300D0" in PARSER
    # Source/data checks do not execute the Fortran consumer.
    assert "Windows static contract checks" in __doc__


def test_arcana_binding_bypasses_assign_and_preserves_runtime_values():
    node_loop = ORBDATA[ORBDATA.index("DO 680 iNode = 1, numNod"):ORBDATA.index("680  CONTINUE")]
    arc_branch = node_loop[node_loop.index("IF (arcanaMode) THEN"):node_loop.index("ELSE", node_loop.index("IF (arcanaMode) THEN"))]
    assert "ArcanaRuntimeGet(iNode,runtimeValues,runtimeStatus)" in arc_branch
    assert "heatFl=runtimeValues(15)" in arc_branch
    assert "thickC=runtimeValues(16)" in arc_branch
    assert "thickM=runtimeValues(17)" in arc_branch
    assert "dQdTdA(iNode)=heatFl" in arc_branch
    assert "zMNode(iNode)=thickC" in arc_branch
    assert "tLNode(iNode)=thickM" in arc_branch
    assert "chemical_delta_rho=0.0D0" in arc_branch
    assert "cooling_curvature=0.0D0" in arc_branch
    assert "CALL Assign" not in arc_branch
    assert "CALL Assign" in node_loop[node_loop.index("ELSE", node_loop.index("IF (arcanaMode) THEN")):]
    assert "IF (.NOT.arcanaMode) THEN" in ORBDATA
    assert "qLimit = qLim0 + dQL_dE * elev(i)" in ORBDATA  # stock-only block remains
    assert "IF (arcanaMode) THEN" in ORBDATA and "CALL ArcanaRuntimeRead" in ORBDATA
    assert "IF (.NOT.arcanaMode) THEN\n!   Read in heat-flow array" in ORBDATA
    assert "IF (arcanaMode) THEN\n                 CALL ArcanaRuntimeGet" in ORBDATA
    assert "GDH1" not in arc_branch
    assert "qLim" not in arc_branch
    assert "cooling_curvature_list(iNode)=cooling_curvature" in arc_branch
    assert "cooling_curvature=0.0D0" in arc_branch
    assert "S1B must read the canonical package profile" in ORBDATA


def test_canonical_fixture_exercises_over_q_limit_and_exact_ridge_state():
    data_path = ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    with data_path.open(encoding="ascii") as stream:
        header = stream.readline().split()
        assert header == ["ARCANA_R6_PRE_ORBDATA_RUNTIME_V1", "arcana_worldsim.r6.shellset_owner_bound_runtime.v1", "64442"]
        seen_ridge = False
        over_limit = False
        for expected_id, line in enumerate(stream, 1):
            values = [float(token) for token in line.split()]
            assert len(values) == 51
            assert values[0] == expected_id
            over_limit |= values[14] > 0.300
            if values[8] == 2:
                seen_ridge = True
                assert values[10] == 0.0
                assert values[14] == 0.300
        assert expected_id == 64442
    assert over_limit
    assert seen_ridge
    assert "heatFl=runtimeValues(15)" in ORBDATA  # direct binding, no q clipping
    assert "thickC=runtimeValues(16)" in ORBDATA
    assert "thickM=runtimeValues(17)" in ORBDATA


def test_feg_handshake_and_nine_field_stock_writer_are_preserved():
    assert "title1=ARCANA_FEG_MARKER" in ORBDATA
    assert "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1" in PARSER
    assert "RejectArcanaFEGForLegacyShells(1,ModNum)" in MOD_SHELLSET
    assert "requires the S1B canonical Shells consumer" in MOD_SHELLSET
    assert re.search(r"WRITE\s*\(iUnitO,\s*91\).*?cooling_curvature_list\(i\)", MOD_DATA, re.S)
    assert re.search(r"FORMAT\s*\(I8,\s*2F11\.5,\s*6ES10\.2\)", MOD_DATA)
    assert "MOD_ArcanaRuntime.o" in MAKEFILE
    assert "MOD_ArcanaRuntime.DB.o" in MAKEFILE
    assert "MOD_ArcanaRuntime.OPT.o" in MAKEFILE

