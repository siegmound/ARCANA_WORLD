import json
import math
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "R6_PRE_ORBDATA_S1B_INTEGRATION_POINT_THERMAL_PROJECTION_CONTRACT.json")
    .read_text(encoding="utf-8")
)
RUNTIME = (
    ROOT / "external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90"
).read_text(encoding="utf-8")


def test_contract_selects_evaluate_then_interpolate_without_new_authority():
    assert CONTRACT["decision"] == "EVALUATE_THEN_INTERPOLATE_FEM_THERMAL_FIELD"
    assert CONTRACT["status"].startswith("R6_PRE_ORBDATA_S1B_SHELLS_CONSUMER_INCOMPLETE")
    assert CONTRACT["temperature_rule"]["integration_point"].startswith("sum(")
    assert (
        CONTRACT["temperature_rule"]["integration_point_property_authority"]
        == "NUMERICAL_RUNTIME_EFFECTIVE_PROPERTY"
    )
    assert CONTRACT["implementation_boundary"]["shells_consumer_wiring"].startswith("S1B_II_MAIN_CONTINUUM_WIRED")
    assert CONTRACT["implementation_boundary"]["runtime_qualification"] == "NOT_CLAIMED"


def test_shared_evaluator_uses_nodal_phase_then_fem_weighted_continuous_values():
    assert "SUBROUTINE ArcanaRuntimeEvaluateNode" in RUNTIME
    assert "SUBROUTINE ArcanaRuntimeEvaluateIP" in RUNTIME
    assert "depth_m < v(I_CRUST)" in RUNTIME
    assert "depth_m <= v(I_LAB)" in RUNTIME
    assert "v(I_LAB_T) * EXP(exponent)" in RUNTIME
    assert "v(I_MANTLE_ALPHA) * ARCANA_G_M_S2" in RUNTIME
    assert "ARCANA_G_M_S2 = 9.82D0" in RUNTIME
    assert "temperature_k = temperature_k + weights(j)*local_temperature" in RUNTIME
    assert "properties = properties + weights(j)*local_properties" in RUNTIME


def test_contract_records_required_diagnostics_and_all_gates_closed():
    assert CONTRACT["mesh_diagnostics"]["mixed_crust_material_elements"] == 1816
    assert CONTRACT["mesh_diagnostics"]["mixed_ridge_ocean_elements"] == 325
    gates = CONTRACT["implementation_boundary"]
    for key in (
        "pre_orbdata_ready",
        "t0_orbdata_executed",
        "shellset_mechanics_authorized",
        "dt_selected",
        "t1_created",
        "forward_evolution_authorized",
    ):
        assert gates[key] is False


def test_arcana_feg_runs_core_fillin_then_fails_closed_before_s1b_iii():
    shells = (ROOT / "external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90").read_text(encoding="utf-8")
    load_at = shells.index("CALL ArcanaShellsLoadRuntime(numNod,ThID)")
    fill_at = shells.index("CALL FillIn (alphaT, basal, conduc")
    fixed_at = shells.index("CALL Fixed (alphaT, area, conduc")
    fail_at = shells.index("ARCANA_S1B_REMAINING_CONSUMERS_NOT_YET_ENABLED")
    assert "ARCANA_S1B_CONSUMERS_NOT_YET_ENABLED" not in shells
    assert load_at < fill_at < fail_at < fixed_at
    assert "IF (ArcanaShellsModeActive()) THEN" in shells[fail_at-350:fail_at]


@dataclass(frozen=True)
class NodeColumn:
    moho: float
    lab: float
    t_moho: float
    t_lab: float
    crust_slope: float
    mantle_slope: float
    alpha: float
    cp: float
    material_code: int

    def temperature(self, depth):
        if depth <= self.moho:
            return self.t_moho + self.crust_slope * (depth - self.moho)
        if depth <= self.lab:
            return self.t_moho + self.mantle_slope * (depth - self.moho)
        return self.t_lab * math.exp(
            self.alpha * 9.82 * (depth - self.lab) / self.cp
        )


def fem(values, weights):
    assert len(values) == len(weights) == 3
    assert all(w >= 0 for w in weights)
    assert math.isclose(sum(weights), 1.0, abs_tol=1e-12)
    return sum(w * x for w, x in zip(weights, values))


def test_projection_reference_vertex_identity_and_homogeneous_profile():
    column = NodeColumn(35_000, 120_000, 900, 1600, 0.02, 0.01, 3e-5, 1250, 7)
    depth = 50_000
    nodal = [column.temperature(depth)] * 3
    assert fem(nodal, (1, 0, 0)) == column.temperature(depth)
    assert fem(nodal, (0.2, 0.3, 0.5)) == column.temperature(depth)


def test_projection_reference_piecewise_joins_and_adiabat_anchor():
    column = NodeColumn(
        35_000, 120_000, 900, 1600, 0.02,
        (1600-900)/(120_000-35_000), 3e-5, 1250, 1
    )
    eps = 1e-5
    assert math.isclose(column.temperature(column.moho-eps), column.temperature(column.moho+eps), abs_tol=1e-5)
    assert math.isclose(column.temperature(column.lab-eps), column.temperature(column.lab+eps), abs_tol=1e-5)
    assert column.temperature(column.lab) == column.t_lab
    assert math.isclose(column.temperature(column.lab+eps), column.t_lab, abs_tol=1e-5)


def test_projection_reference_mixed_element_is_finite_bounded_and_ids_stay_discrete():
    columns = (
        NodeColumn(30_000, 100_000, 800, 1450, 0.018, (1450-800)/(100_000-30_000), 2.8e-5, 1200, 3),
        NodeColumn(40_000, 130_000, 950, 1700, 0.021, (1700-950)/(130_000-40_000), 3.1e-5, 1300, 8),
        NodeColumn(25_000, 90_000, 750, 1350, 0.016, (1350-750)/(90_000-25_000), 2.5e-5, 1100, 12),
    )
    weights = (0.2, 0.3, 0.5)
    for depth in (0, 25_000, 40_000, 90_000, 100_000, 130_000, 150_000):
        nodal_t = [column.temperature(depth) for column in columns]
        tip = fem(nodal_t, weights)
        assert math.isfinite(tip)
        assert min(nodal_t) <= tip <= max(nodal_t)
    # IDs remain three discrete nodal observations; no weighted ID is formed.
    assert tuple(c.material_code for c in columns) == (3, 8, 12)
    alpha_values = [c.alpha for c in columns]
    alpha_ip = fem(alpha_values, weights)
    assert min(alpha_values) <= alpha_ip <= max(alpha_values)


def test_activation_is_not_enabled_without_shells_package_handshake():
    set_source = (
        ROOT / "external/ShellSet-v1.1.0/src/MOD_ShellSet.f90"
    ).read_text(encoding="utf-8")
    shells_source = (ROOT / "external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90").read_text(encoding="utf-8")
    setup = set_source[set_source.index("subroutine InputSetup"):set_source.index("end subroutine", set_source.index("subroutine InputSetup"))]
    inspect = set_source[set_source.index("subroutine ArcanaShellsInspectFEG"):set_source.index("end subroutine ArcanaShellsInspectFEG")]
    loader = set_source[set_source.index("subroutine ArcanaShellsLoadRuntime"):set_source.index("end subroutine ArcanaShellsLoadRuntime")]
    assert CONTRACT["implementation_boundary"]["activation_handshake"].startswith("S1B_I_RUNTIME_LIFECYCLE_IMPLEMENTED")
    assert setup.count("R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat") >= 4
    assert setup.count("trim(filename)//'17'") >= 4
    assert "case(\"SH\")" in setup and "case(\"SF\")" in setup
    assert "if(.not.marker_present) return" in inspect  # stock marker + absent package
    assert "marker_present .neqv. package_present" in inspect
    assert "open(unit=17,file=trim(package_path)" in inspect
    assert "ArcanaRuntimeRead(17,expected_nodes,ierr,message)" in loader
    assert "ArcanaRuntimeIsLoaded()" in loader
    assert "ArcanaShellsModeActive" in set_source
    assert "ArcanaShellsRelease" in set_source and "close(17)" in set_source
    load_at = shells_source.index("CALL ArcanaShellsLoadRuntime(numNod,ThID)")
    fill_at = shells_source.index("CALL FillIn (alphaT, basal, conduc")
    fail_at = shells_source.index("ARCANA_S1B_REMAINING_CONSUMERS_NOT_YET_ENABLED")
    fixed_at = shells_source.index("CALL Fixed (alphaT, area, conduc")
    assert load_at < fill_at < fail_at < fixed_at


def test_known_shells_thermal_gaps_are_explicitly_kept_blocked():
    shells = (ROOT / "external/ShellSet-v1.1.0/src/MOD_Shells.f90").read_text(
        encoding="utf-8"
    )
    expected_gaps = CONTRACT["implementation_boundary"]["remaining_legacy_consumers"]
    assert len(expected_gaps) == 4
    assert CONTRACT["implementation_boundary"]["legacy_consumer_paths_wired_to_shared_evaluator"] is False
    assert "SUBROUTINE FillIn" in shells and "geothC(2, m, i) = q / conduc(1)" in shells
    assert "SUBROUTINE OneBar" in shells and "gt(1) = geothM(1, m, i)" in shells
    assert "SUBROUTINE Diamnd" in shells and "MIN(temLim, geoth1)" in shells
    assert "SUBROUTINE Result" in shells and "tMid = geothC(1, m, i)" in shells


def test_s1b_ii_arcana_main_thermal_consumers_use_shared_evaluator_and_exact_weights():
    shells = (ROOT / "external/ShellSet-v1.1.0/src/MOD_Shells.f90").read_text(encoding="utf-8")
    fill = shells[shells.index("SUBROUTINE FillIn"):shells.index("END SUBROUTINE FillIn")]
    arc = fill[fill.index("IF (ArcanaShellsModeActive()) THEN", fill.index("!   ARCANA uses")):fill.index("ELSE\n!   Geotherm:")]
    onebar = shells[shells.index("SUBROUTINE OneBar"):shells.index("END SUBROUTINE OneBar")]
    assert "COMMON / S1S2S3 / points" in fill and "arcana_weights = points(:,m)" in arc
    assert "arcana_node_ids = nodes(:,i)" in arc
    assert "CALL ArcanaRuntimeSqueez" in arc and "0.0D0, elev(i)" in arc
    assert "arcana_elevation = elev(nodes(1,i))*points(1,m)" in arc
    assert "delta_rho = 0.0D0" in fill and "temLim" not in arc
    assert "geothC = 0.0D0" in arc and "geothM = 0.0D0" in arc
    assert "ArcanaRuntimeEvaluateIP" in onebar and "geothM" not in onebar[onebar.index("IF (ArcanaShellsModeActive()) THEN"):onebar.index("ELSE", onebar.index("IF (ArcanaShellsModeActive()) THEN"))]
    assert "MIN(tg, ta)" in onebar and "MAX(t, 200.0D0)" in onebar
    assert "ARCANA_ONEBAR_GOVERNED_TEMPERATURE_BELOW_200K" in onebar
    assert "ARCANA_ONEBAR_EVALUATOR_FAILED" in onebar
    assert "arcana_weights = points(:,m)" in onebar
    assert "zMoho(m,i)+tLInt(m,i)," in fill
    assert "baseT < 1273.0D0" in fill
    assert "ARCANA_ICONVE5_EVALUATOR_FAILED" in fill
    assert "ARCANA_SQUEEZ_EVALUATOR_FAILED" in fill
