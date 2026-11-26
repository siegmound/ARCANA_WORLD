import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_r1_subsolidus_diagnostic as r


def fake_headers():
    return "\n".join(k+" EoS = 3 | PMELT liquid endmember test" for k in r.LIQUID_IDS).encode()


def test_liquid_headers():
    assert set(r.liquid_headers(fake_headers()))==set(r.LIQUID_IDS)


@pytest.mark.parametrize("raw",[fake_headers().replace(b"foGL EoS = 3",b"foGL EoS = 2"),
                                 fake_headers().replace(b"PMELT liquid endmember",b"solid"),
                                 fake_headers()+b"\nfoGL EoS = 3 | PMELT liquid endmember"])
def test_liquid_identity_guard(raw):
    with pytest.raises(ValueError,match="LIQUID_IDENTITY"):
        r.liquid_headers(raw)


def test_literal_dependency_boundaries():
    assert r.token_hits("foGL\nfooGL\nfoGL_x\n1 foGL + 2 q","foGL")==[1,4]


@pytest.mark.parametrize("code",["046","049","053","017"])
def test_no_new_warning_acceptance(code):
    p=r.DiagnosticDialogue("ACT_ONLY",{},[])
    p.state="AWAIT_NEXT"
    p.requested=["B01"]
    with pytest.raises(ValueError,match="ver"+code):
        p.next_response(("**warning ver"+code+"** diagnostic").encode())
    assert p.requested==["B01"] and p.completed==[]


def test_water_and_archive_scope():
    assert not set(r.LIQUID_IDS)&{"H2O","h2oGL","h2oL","wL_q","O2"}
    assert set(r.FAILED_SPECIES)<=set(r.LIQUID_IDS)
    assert r.OUT!=r.prior.OUT and r.POINTS==r.prior.POINTS
