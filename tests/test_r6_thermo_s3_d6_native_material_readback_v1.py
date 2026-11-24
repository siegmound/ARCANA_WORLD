"""Synthetic format tests only; actual PRNs are independently read on FAIR."""
import json
import pytest
from experiments.r6_thermo_provider_pilot_v1 import s3_d6_native_material_readback as d

PRN = """Molar Properties and Density:
N(g) G(J) S(J/K) V(J/bar) Cp(J/K) Alpha(1/K) Beta(1/bar) Cp/Cv Density(kg/m3)
p 1000 -20 4 40.00 1000.0 0.0000 0.1E-5 1.1 2500.0
System 1000 -20 4 40.00 1000.0 0.3E-4 0.1E-5 1.1 2500.0
System - Fluid 1000 -20 4 40.00 1000.0 0.3E-4 0.1E-5 1.1 2500.0
Seismic Properties:
Gruneisen_T Ks(bar) Mu(bar) V0(km/s) Vp(km/s) Vs(km/s) Poisson ratio
p 1 100 25 2 3 1 0.35
System NaN NaN NaN NaN NaN NaN NaN
System - Fluid NaN NaN NaN NaN NaN NaN NaN
Bulk Composition:
Other Bulk Properties:
Heat Capacity (J/K/kg) = 1000.0
Solid Heat Capacity (J/K/kg) = 1000.0
Chemical Potentials (J/mol):
"""
LOG = """**warning ver178** at T(K)= 1050
the shear modulus of: p
is missing or invalid
**warning ver177** at T(K)= 1050
"""


def test_native_properties():
    x = d.parse_properties(PRN, LOG, {"p":100})
    assert x["thermal_native"]["System"]["density_kg_m3"]["value_si"] == "2500.0"
    assert x["thermal_native"]["System"]["cp_J_kg_K"]["value_si"] == "1000.0"
    assert x["thermal_native"]["System"]["beta_bar_inv"]["value_si"] == "1E-11"
    assert x["thermal_native"]["p"]["alpha_K_inv"]["status"] == "NATIVE_ZERO_UNADJUDICATED"
    assert x["elastic_native"]["System"]["mu_bar"]["value_si"] is None
    assert x["elastic_native"]["p"]["mu_bar"]["status"].startswith("NATIVE_POISSON")
    assert x["elastic_export_authorized"] is False
    assert all(x["printed_identity_checks"]["System"].values())
    json.dumps(x,allow_nan=False)


@pytest.mark.parametrize("before,after", [
    ("Density(kg/m3)","Density(g/cm3)"),
    ("System - Fluid 1000","Other 1000"),
    ("1000 -20 4 40.00","1000 -20 4 -40.00"),
    ("0.1E-5","Inf"),
    ("Heat Capacity (J/K/kg) = 1000.0","Heat Capacity (J/K/kg) = 800.0"),
    ("2500.0","2000.0"),
    ("Molar Properties and Density:","Unknown section:"),
    ("p 1000 -20 4 40.00 1000.0 0.0000 0.1E-5 1.1 2500.0",""),
])
def test_reject_mutations(before,after):
    with pytest.raises(d.MaterialReadbackError):
        d.parse_properties(PRN.replace(before,after),LOG,{"p":100})


def test_unknown_warning_phase():
    with pytest.raises(d.MaterialReadbackError):
        d.parse_properties(PRN,LOG.replace("of: p","of: unknown"),{"p":100})


def test_ratio_rounding():
    assert d.ratio_overlap("6162.82","209.99","100","2934.7")
    assert d.ratio_overlap("7273.9","6162.82","1000","1180.29")
    assert not d.ratio_overlap("6162.82","209.99","100","2900.0")


def test_fluid_zero_not_nan():
    x = d.parse_properties(PRN.replace("p 1000","melt(G) 1000").replace(
        "p 1 100 25 2 3 1 0.35","melt(G) 1 100 0 2 3 0 0.5"),
        "",{"melt(G)":100})
    assert x["elastic_native"]["melt(G)"]["mu_bar"]["status"] == "NATIVE_FLUID_ZERO"
    assert x["elastic_native"]["System"]["mu_bar"]["value_si"] is None


def test_solid_cp_upstream_denominator_discrepancy():
    native = PRN.replace(
        "System - Fluid 1000 -20 4 40.00 1000.0 0.3E-4 0.1E-5 1.1 2500.0",
        "System - Fluid 900 -20 4 30.00 600.0 0.3E-4 0.1E-5 1.1 3000.0"
    ).replace("Solid Heat Capacity (J/K/kg) = 1000.0",
              "Solid Heat Capacity (J/K/kg) = 800.0")
    out = d.parse_properties(native,LOG,{"p":100})
    checks = out["printed_identity_checks"]["System - Fluid"]
    assert checks["cp_mass_printed_interval_overlap"] is False
    assert checks["cp_upstream_total_density_formula_overlap"] is True
    solid = out["thermal_native"]["System - Fluid"]
    assert "DO_NOT_EXPORT" in solid["cp_J_kg_K"]["status"]
    assert abs(float(solid["cp_mass_normalized_derived_J_kg_K"]["value_si"])-666.6666667)<1e-6
