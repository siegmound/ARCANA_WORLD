import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_restricted_research_closure as r

@pytest.mark.parametrize("name,values",[
    ("Bio(TCC)",{"f3b_q":".03106","east":".08929","tbi_q":".05234","ann":".38599","phl":"-.00510","obi":".44642"}),
    ("Chl(W)",{"daph":".54788","ames":".05646","afchl":".19418","f3cl_q":".12409","clin":".27157","och1":"0","och2":"-.19418"})])
def test_native_chemical_witness(name,values):
    spec=r.MODELS[name]
    defs={k:r.linear(v) for group in ("ordered","dependent") for k,v in spec[group].items()}
    result=r.witness(name,{k:r.Q(v) for k,v in values.items()},defs)
    assert result["composition_reproduced_exactly"]
    assert not result["ordering_energy_equivalence_claimed"]
    assert all(r.Q(x)>=0 for x in result["vertex_weights"].values())

def test_signed_site_reconstruction():
    result=r.check_sites({"afchl":".19418","och2":"-.19418"},
        {("M4","Mg"):{"afchl":r.Q(1),"och2":r.Q(1)}},
        [{"site":"M4","fractions":{"Mg":".0000"}}],"mnchl")
    assert result[0]["compatible"]

def test_impossible_site_rejected():
    with pytest.raises(ValueError,match="SITE_RECONSTRUCTION"):
        r.check_sites({"afchl":".10000","och2":"-.19418"},
            {("M4","Mg"):{"afchl":r.Q(1),"och2":r.Q(1)}},
            [{"site":"M4","fractions":{"Mg":".0000"}}],"mnchl")
