import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03b_low_grade_morb_readiness as c


def test_bare_and_commented_model_headers():
    raw=b"Pu(M)\r\nabbreviation Pu\r\npump fpum ffpu\r\nend_of_model\r\nFsp(HGP) | solution name\r\nabbreviation Fsp\r\nend_of_model\r\n"
    z=c.model_blocks(raw,("Pu(M)","Fsp(HGP)","Chl(W)"))
    assert z["Pu(M)"]["line"]==1 and z["Fsp(HGP)"]["line"]==5
    assert z["Chl(W)"] is None


def test_duplicate_model_header_rejected():
    raw=b"Pu(M)\nabbreviation Pu\nend_of_model\n"*2
    with pytest.raises(ValueError,match="C03B_AMBIGUOUS_MODEL"):
        c.model_blocks(raw,("Pu(M)",))


def test_eos_headers_ignore_comments_and_glossary():
    assert c.endmember_names(b"pump EoS = 2\n| fpum EoS = 2\nffpu EoS = 2\npump description\n")=={"pump","ffpu"}


def test_native_components():
    assert c.components(b"begin_components | title\nFEO 71.844\nO2 31.999\nend_components\n")=={"FEO":71.844,"O2":31.999}


def test_morb_ferric_oxygen_uses_o2_molecules():
    names=list(c.d.a.p.p.NAMES)
    inp={"names":names,"wt_amounts":[c.m.MASS[k] if k in ("FeO","Fe2O3") else 0. for k in names],
         "omitted_source_oxides_wt":{}}
    masses={k.upper():c.m.MASS[k] for k in names if k!="Fe2O3"}
    masses["O2"]=31.999
    out=c.native_morb_basis(inp,masses)
    assert out["native_moles_per_source_recipe"]["FEO"]==3
    assert out["native_moles_per_source_recipe"]["O2"]==.5
    assert sum(out["normalized_native_wt_percent"].values())==pytest.approx(100)
    assert out["native_engine_conversion_verified"] is False


def test_missing_o2_fails_closed():
    names=list(c.d.a.p.p.NAMES)
    inp={"names":names,"wt_amounts":[1.]*len(names),"omitted_source_oxides_wt":{}}
    masses={k.upper():c.m.MASS[k] for k in names if k!="Fe2O3"}
    with pytest.raises(ValueError,match="C03B_NATIVE_STOICHIOMETRY"):
        c.native_morb_basis(inp,masses)
