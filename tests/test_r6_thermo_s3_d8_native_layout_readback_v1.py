import pytest
from experiments.r6_thermo_provider_pilot_v1 import s3_d8_native_layout_readback as d

OX="Na2O MgO Al2O3 K2O CaO TiO2 FeO O2 H2O SiO2".split()
PRN=("T(K) = 1000.00\nP(bar) = 4000.00\n"
     "Phase Compositions (molar  proportions):\n"
     "wt %  vol %  mol %  mol  "+"  ".join(OX)+"\n"
     "p 100.00 100.00 100.00 10.00 "+" ".join(["1.00000"]*10)+"\n"
     "Phase speciation\n"
     "Molar Properties and Density:\n"
     "N(g) G(J) S(J/K) V(J/bar) Cp(J/K) Alpha(1/K) Beta(1/bar) Cp/Cv Density(kg/m3)\n"
     "p 1000 -20 4 40.00 1000.0 0.0000 0.1E-5 1.1 2500.0\n"
     "System 1000 -20 4 40.00 1000.0 0.3E-4 0.1E-5 1.1 2500.0\n"
     "Seismic Properties:\n"
     "Gruneisen_T Ks(bar) Mu(bar) V0(km/s) Vp(km/s) Vs(km/s) Poisson ratio\n"
     "p 1 100 25 2 3 1 0.35\nSystem 1 100 25 2 3 1 0.35\n"
     "Bulk Composition:\nmol g wt % mol/kg\n"+
     "".join(x+" 10.000 100.000 10.000 10.000\n" for x in OX)+
     "Other Bulk Properties:\nHeat Capacity (J/K/kg) = 1000.0\nChemical Potentials (J/mol):\n")
LOG="**warning ver178** at T(K)= 1000\n the shear modulus of: p\n**warning ver049** warning 178 will not be repeated"

def test_single_aggregate():
    x=d.read(PRN,LOG,4000,1000)
    assert x["layout"]=="SINGLE_AGGREGATE"
    assert x["chemistry"]["printed_component_coverage"]==10
    m=x["material"]
    assert "System - Fluid" not in m["thermal_native"]
    assert m["solid_separate_aggregate"]=="NOT_REPORTED"
    assert m["elastic_native"]["System"]["mu_bar"]["status"].startswith("NATIVE_AGGREGATE_WITH")
    assert m["elastic_export_authorized"] is False
    assert m["shear_warning_suppressed"]

@pytest.mark.parametrize("before,after",[
    ("Na2O 10.000","Na2O 8.000"),
    ("Na2O 10.000 100.000 10.000 10.000","Na2O 10.000 100.000 10.000"),
    ("mol g wt % mol/kg","bad header"),
    ("Heat Capacity (J/K/kg) = 1000.0","Heat Capacity (J/K/kg) = 900.0"),
    ("System 1000 -20 4 40.00 1000.0 0.3E-4 0.1E-5 1.1 2500.0","System 1000 -20 4 40.00 1000.0 0.3E-4 0.1E-5 1.1 3000.0"),
    ("T(K) = 1000.00","T(K) = 1100.00"),
])
def test_reject_drift(before,after):
    with pytest.raises(ValueError):
        d.read(PRN.replace(before,after),LOG,4000,1000)

def test_no_solid_invention():
    with pytest.raises(ValueError):
        d.read(PRN.replace("Chemical Potentials","Solid Heat Capacity (J/K/kg) = 1000.0\nChemical Potentials"),LOG,4000,1000)
