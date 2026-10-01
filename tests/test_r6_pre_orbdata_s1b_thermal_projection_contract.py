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
    assert CONTRACT["status"].startswith("R6_PRE_ORBDATA_S1B_SHELLS_CONSUMER_IMPLEMENTED")
    assert CONTRACT["temperature_rule"]["integration_point"].startswith("sum(")
    assert (
        CONTRACT["temperature_rule"]["integration_point_property_authority"]
        == "NUMERICAL_RUNTIME_EFFECTIVE_PROPERTY"
    )
    assert CONTRACT["implementation_boundary"]["shells_consumer_wiring"].startswith("S1B_II_AND_S1B_III")
    assert CONTRACT["implementation_boundary"]["runtime_qualification"].startswith("NOT_CLAIMED")


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


def test_arcana_feg_reaches_all_wired_thermal_consumers_without_barrier():
    shells = (ROOT / "external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90").read_text(encoding="utf-8")
    load_at = shells.index("CALL ArcanaShellsLoadRuntime(numNod,ThID)")
    fill_at = shells.index("CALL FillIn (alphaT, basal, conduc")
    fixed_at = shells.index("CALL Fixed (alphaT, area, conduc")
    assert "ARCANA_S1B_REMAINING_CONSUMERS_NOT_YET_ENABLED" not in shells
    assert "ARCANA_S1B_CONSUMERS_NOT_YET_ENABLED" not in shells
    assert load_at < fill_at < fixed_at
    assert "CALL Result (" in shells


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


def test_activation_is_gated_by_shells_package_handshake():
    set_source = (
        ROOT / "external/ShellSet-v1.1.0/src/MOD_ShellSet.f90"
    ).read_text(encoding="utf-8")
    shells_source = (ROOT / "external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90").read_text(encoding="utf-8")
    main_source = (ROOT / "external/ShellSet-v1.1.0/src/ShellSetMain.f90").read_text(encoding="utf-8")
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
    assert "logical, save :: arcana_shells_failed = .FALSE." in set_source
    assert "logical function ArcanaShellsFailed()" in set_source
    assert "ArcanaShellsFailed=arcana_shells_failed" in set_source
    assert "arcana_shells_failed=.FALSE." in inspect
    assert "arcana_shells_failed=.TRUE." in inspect
    assert "arcana_shells_failed=.TRUE." in loader
    assert "ArcanaShellsModeActive" in set_source
    assert "ArcanaShellsRelease" in set_source and "close(17)" in set_source
    assert "arcana_shells_failed=.FALSE." not in set_source[set_source.index("subroutine ArcanaShellsRelease"):set_source.index("end subroutine ArcanaShellsRelease")]
    for tag in ("SH", "SF"):
        open_call = f'call OpenInput(ThID,ModNum,"{tag}",DirName,rpeat=rpeat)'
        position = main_source.index(open_call)
        main_path = main_source[position:position + 350]
        check = main_path.index("ArcanaShellsFailed()")
        local_abort = main_path.index("call abort(11)")
        abort = main_path.index("call MPI_Abort(MPI_COMM_WORLD,11)")
        output = main_path.index("call OpenOutput")
        shells = main_path.index("call Shells_v5p0")
        assert check < local_abort < abort < output < shells
        assert "if(ArcanaShellsFailed()) then" in main_path[:output]
    load_at = shells_source.index("CALL ArcanaShellsLoadRuntime(numNod,ThID)")
    failed_at = shells_source.index("IF (ArcanaShellsFailed()) RETURN", load_at)
    shell_lines = shells_source.splitlines()
    load_line = next(i for i, line in enumerate(shell_lines) if "CALL ArcanaShellsLoadRuntime(numNod,ThID)" in line)
    assert shell_lines[load_line + 1].strip() == "IF (ArcanaShellsFailed()) RETURN"
    fill_at = shells_source.index("CALL FillIn (alphaT, basal, conduc")
    fixed_at = shells_source.index("CALL Fixed (alphaT, area, conduc")
    assert "ARCANA_S1B_REMAINING_CONSUMERS_NOT_YET_ENABLED" not in shells_source
    assert load_at < failed_at < fill_at < fixed_at


def test_remaining_shells_thermal_consumers_use_shared_evaluator():
    shells = (ROOT / "external/ShellSet-v1.1.0/src/MOD_Shells.f90").read_text(
        encoding="utf-8"
    )
    assert CONTRACT["implementation_boundary"]["remaining_legacy_consumers"] == []
    assert CONTRACT["implementation_boundary"]["legacy_consumer_paths_wired_to_shared_evaluator"] is True
    reachability={item["path"]:item for item in CONTRACT["implementation_boundary"]["consumer_reachability"]}
    assert set(reachability)=={
        "FillIn / nodal Squeez", "OneBar", "iConve=5", "Fixed fault integration",
        "Pure orchestration", "Viscos / Diamnd", "Mohr", "Result"
    }
    for routine in ("Fixed", "Mohr", "Viscos", "Result"):
        start = shells.index(f"SUBROUTINE {routine} (")
        end = shells.index(f"END SUBROUTINE {routine}", start)
        body = shells[start:end]
        assert "ArcanaShellsModeActive()" in body
    diamnd = shells[shells.index("SUBROUTINE Diamnd "):shells.index("END SUBROUTINE Diamnd")]
    assert "IF (arcana_active) THEN" in diamnd
    assert "ArcanaRuntimeMeanEffectiveDensity" in diamnd
    assert "ArcanaRuntimeEvaluateWeighted" in diamnd
    assert "MIN(t, temLim)" in diamnd  # retained only in the stock branch
    fixed = shells[shells.index("SUBROUTINE Fixed "):shells.index("END SUBROUTINE Fixed")]
    assert "ArcanaRuntimeSqueez" in fixed
    mohr = shells[shells.index("SUBROUTINE Mohr "):shells.index("END SUBROUTINE Mohr")]
    assert "ArcanaRuntimeEffectiveDensityWeighted" in mohr
    assert "ArcanaRuntimeEvaluateWeighted" in mohr
    result = shells[shells.index("SUBROUTINE Result "):shells.index("END SUBROUTINE Result")]
    assert "ArcanaRuntimeEffectiveDensityWeighted" in result
    pure = shells[shells.index("SUBROUTINE Pure ("):shells.index("END SUBROUTINE Pure")]
    assert "CALL Viscos" in pure and "CALL Mohr" in pure
    viscos = shells[shells.index("SUBROUTINE Viscos "):shells.index("END SUBROUTINE Viscos")]
    assert "arcana_node_ids = nodes(:, i)" in viscos
    assert "arcana_weights = points(:, m)" in viscos
    assert "arcana_node_ids, arcana_weights, arcana_active" in viscos
    runtime_call=fixed.index("CALL ArcanaRuntimeSqueez")
    stock_call=fixed.index("CALL Squeez",runtime_call)
    assert fixed.rfind("ELSE",runtime_call,stock_call)>runtime_call


def test_s1b_ii_arcana_main_thermal_consumers_use_shared_evaluator_and_exact_weights():
    shells = (ROOT / "external/ShellSet-v1.1.0/src/MOD_Shells.f90").read_text(encoding="utf-8")
    fill = shells[shells.index("SUBROUTINE FillIn"):shells.index("END SUBROUTINE FillIn")]
    arc = fill[fill.index("IF (ArcanaShellsModeActive()) THEN", fill.index("!   ARCANA uses")):fill.index("ELSE\n!   Geotherm:")]
    onebar = shells[shells.index("SUBROUTINE OneBar"):shells.index("END SUBROUTINE OneBar")]
    assert "COMMON / S1S2S3 / points" in fill and "arcana_weights = points(:,m)" in arc
    assert "REAL*8 arcana_properties(ARCANA_PROPERTY_COUNT)" in fill
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


@dataclass(frozen=True)
class PiecewiseColumn:
    moho: float
    lab: float
    crust: tuple[float, float, float, float]
    mantle: tuple[float, float, float, float]
    t_lab: float
    adiabat_rate: float
    properties: dict

    @staticmethod
    def _poly(c, x):
        c3, c2, c1, c0 = c
        return ((c3*x+c2)*x+c1)*x+c0

    @staticmethod
    def _primitive(c, x):
        c3, c2, c1, c0 = c
        return c3*x**4/4+c2*x**3/3+c1*x**2/2+c0*x

    def phase(self, z):
        return "crust" if z < self.moho else "mantle" if z < self.lab else "asth"

    def temperature(self, z):
        if z < self.moho:
            return self._poly(self.crust, z)
        if z < self.lab:
            return self._poly(self.mantle, z-self.moho)
        return self.t_lab * math.exp(self.adiabat_rate*(z-self.lab))

    def temperature_integral(self, a, b):
        phase = self.phase((a+b)/2)
        if phase == "crust":
            return self._primitive(self.crust,b)-self._primitive(self.crust,a)
        if phase == "mantle":
            return self._primitive(self.mantle,b-self.moho)-self._primitive(self.mantle,a-self.moho)
        if abs(self.adiabat_rate) < 1e-14:
            return self.t_lab*(b-a)
        return self.t_lab*(math.exp(self.adiabat_rate*(b-self.lab))-math.exp(self.adiabat_rate*(a-self.lab)))/self.adiabat_rate


def exact_weighted_mean_density(columns, weights, a, b):
    breaks = sorted({a,b,*[x for c in columns for x in (c.moho,c.lab) if a < x < b]})
    total = 0.0
    for lo, hi in zip(breaks, breaks[1:]):
        mid = (lo+hi)/2
        rho = sum(w*c.properties[c.phase(mid)][0] for w,c in zip(weights,columns))
        alpha = sum(w*c.properties[c.phase(mid)][1] for w,c in zip(weights,columns))
        t_integral = sum(w*c.temperature_integral(lo,hi) for w,c in zip(weights,columns))
        total += rho*((hi-lo)-alpha*t_integral)
    return total/(b-a)


def test_diamnd_exact_mean_matches_homogeneous_cubic_stock_operator():
    coeff = (2e-11,-3e-7,0.015,300.0)
    props = {phase:(3300.0,3e-5) for phase in ("crust","mantle","asth")}
    column = PiecewiseColumn(80_000,140_000,coeff,coeff,900.0,2e-8,props)
    a,b = 10_000.0,70_000.0
    exact = exact_weighted_mean_density((column,)*3,(0.2,0.3,0.5),a,b)
    tmean = column.temperature_integral(a,b)/(b-a)
    assert math.isclose(exact,3300.0*(1-3e-5*tmean),rel_tol=2e-15)


def test_diamnd_piecewise_mean_crosses_heterogeneous_moho_and_lab_deterministically():
    props1 = {"crust":(2850.,2.4e-5),"mantle":(3300.,3.0e-5),"asth":(3250.,3.2e-5)}
    props2 = {"crust":(2950.,2.6e-5),"mantle":(3350.,3.1e-5),"asth":(3280.,3.3e-5)}
    cols = (PiecewiseColumn(28_000,92_000,(0.,0.,0.02,300.),(0.,0.,0.012,860.),1450.,2.5e-8,props1),
            PiecewiseColumn(42_000,115_000,(0.,0.,0.016,320.),(0.,0.,0.009,1000.),1650.,3.0e-8,props2),
            PiecewiseColumn(35_000,105_000,(0.,0.,0.018,310.),(0.,0.,0.011,940.),1550.,2.8e-8,props1))
    weights=(0.2,0.3,0.5)
    a,b=0.,150_000.
    exact=exact_weighted_mean_density(cols,weights,a,b)
    assert math.isfinite(exact) and exact > 0
    assert exact == exact_weighted_mean_density(cols,weights,a,b)
    breaks=sorted({a,b,*[x for c in cols for x in (c.moho,c.lab) if a<x<b]})
    numeric=0.0
    for lo,hi in zip(breaks,breaks[1:]):
        n=20_000
        dz=(hi-lo)/n
        def density(z):
            rho=sum(w*c.properties[c.phase(z)][0] for w,c in zip(weights,cols))
            alpha=sum(w*c.properties[c.phase(z)][1] for w,c in zip(weights,cols))
            temp=sum(w*c.temperature(z) for w,c in zip(weights,cols))
            return rho*(1-alpha*temp)
        numeric += dz*(0.5*density(math.nextafter(lo,hi))+sum(density(lo+j*dz) for j in range(1,n))+0.5*density(math.nextafter(hi,lo)))
    assert math.isclose(exact,numeric/(b-a),rel_tol=2e-8,abs_tol=2e-5)


def test_below_lab_adiabat_integral_is_finite_continuous_and_analytic():
    props={phase:(3300.,3e-5) for phase in ("crust","mantle","asth")}
    col=PiecewiseColumn(40_000,100_000,(0.,0.,0.01,300.),(0.,0.,0.01,900.),1500.,3e-8,props)
    a,b=100_000.,180_000.
    analytic=col.temperature_integral(a,b)/(b-a)
    expected=1500.*math.expm1(col.adiabat_rate*(b-a))/(col.adiabat_rate*(b-a))
    assert math.isfinite(analytic) and math.isclose(analytic,expected,rel_tol=1e-12)
    eps=1e-4
    assert math.isclose(col.temperature(col.lab-eps),col.temperature(col.lab+eps),abs_tol=2e-5)


def test_mohr_endpoint_trapezoid_and_source_paths_are_bound():
    rho,alpha,t0,t1=3300.,3e-5,500.,1300.
    expected=rho*(1-alpha*(t0+t1)/2)
    assert math.isclose(0.5*(rho*(1-alpha*t0)+rho*(1-alpha*t1)),expected,rel_tol=2e-16)
    source=(ROOT/"external/ShellSet-v1.1.0/src/MOD_Shells.f90").read_text(encoding="utf-8")
    mohr=source[source.index("SUBROUTINE Mohr "):source.index("END SUBROUTINE Mohr")]
    assert "arcana_fault_weights = 0.25D0" in mohr
    assert "arcana_fault_weights,4" in mohr
    assert "arcana_fault_weights,2" in mohr
    assert "ArcanaRuntimeMeanEffectiveDensity" not in mohr
    assert "ArcanaRuntimeEffectiveDensityWeighted" in mohr
    assert "tMeanC = (tSurf + tTrans) / 2.0D0" in mohr  # stock branch only


def test_mohr_mixed_support_uses_continuous_weighted_properties_and_keeps_ids_discrete():
    columns = (
        NodeColumn(30_000,100_000,800,1450,0.018,0.009,2.8e-5,1200,3),
        NodeColumn(40_000,130_000,950,1700,0.021,0.008,3.1e-5,1300,8),
    )
    weights=(0.75,0.25)
    ids=tuple(c.material_code for c in columns)
    endpoints=[]
    for z in (0.,35_000.):
        temp=sum(w*c.temperature(z) for w,c in zip(weights,columns))
        rho=sum(w*v for w,v in zip(weights,(2900.,3300.)))
        alpha=sum(w*v for w,v in zip(weights,(2.8e-5,3.1e-5)))
        endpoints.append(rho*(1-alpha*temp))
    mean=0.5*(endpoints[0]+endpoints[1])
    assert math.isfinite(mean) and min(endpoints)<=mean<=max(endpoints)
    assert ids==(3,8)  # discrete IDs are preserved as nodal identities


def test_diamnd_runtime_path_uses_analytic_reduction_not_midpoint_temperature():
    source=(ROOT/"external/ShellSet-v1.1.0/src/MOD_Shells.f90").read_text(encoding="utf-8")
    diamnd=source[source.index("SUBROUTINE Diamnd "):source.index("END SUBROUTINE Diamnd")]
    runtime=RUNTIME[RUNTIME.index("SUBROUTINE ArcanaRuntimeMeanEffectiveDensity"):RUNTIME.index("SUBROUTINE ArcanaRuntimeSqueez")]
    assert "ArcanaRuntimeMeanEffectiveDensity" in diamnd
    assert "ArcanaRuntimeEvaluateWeighted" in diamnd
    assert "PolynomialPrimitive" in runtime
    assert "EXP(exponent_b)-EXP(exponent_a)" in runtime
    assert "ArcanaRuntimeMeanEffectiveDensity(arcana_node_ids" in diamnd
    assert "Arcana_Simpson" not in runtime
    assert "weighted_temperature_integral" in runtime
    assert "local_rho * &" in runtime
    assert "tMean" not in runtime
