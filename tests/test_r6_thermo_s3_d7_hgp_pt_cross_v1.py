"""D7 synthetic checks; no real solver starts in tests."""
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_s3_d7_hgp_pt_cross_fair as d

RAW=b"bl691_MEEMUM\r\nn\r\n1050 4000\r\n0 0"

@pytest.mark.parametrize("p,t",d.POINTS)
def test_exact_single_line_change(p,t):
    assert d.point_stdin(RAW,p,t)==b"bl691_MEEMUM\r\nn\r\n"+f"{t} {p}".encode()+b"\r\n0 0"

@pytest.mark.parametrize("p,t",[(4000,1050),(4000,950),(6000,1050),(4000.0,1000)])
def test_unapproved_point(p,t):
    with pytest.raises(ValueError):
        d.point_stdin(RAW,p,t)

@pytest.mark.parametrize("raw",[b"1050 3000",b"1050 4000\n1050 4000\n"])
def test_bad_stdin(raw):
    with pytest.raises(ValueError):
        d.point_stdin(raw,4000,1000)

LOG=b"Summary of included solution models:\n Fsp(HGP) lAb(HGP)\n-----\n"
PRN=b" T(K) = 1000.00\n P(bar) = 4000.00\n"

def test_review_preserves_raw(monkeypatch):
    def bad(*args):
        raise ValueError("format review")
    monkeypatch.setattr(d,"read_perplex_prn",bad)
    x=d.observe(PRN,LOG,4000,1000)
    assert x["chemistry"] is None and x["readback_review"]==["D3: format review"]
    assert x["native_review_excerpt"]==PRN.decode()

def test_admission_required():
    with pytest.raises(ValueError):
        d.observe(PRN,LOG.replace(b"lAb(HGP)",b""),4000,1000)

def test_pt_required():
    with pytest.raises(ValueError):
        d.observe(PRN,LOG,3000,1050)

def test_repetition_no_promotion():
    a={"prn_sha256":"x","readback_review":[]}
    b={"prn_sha256":"y","readback_review":["review"]}
    assert d.repeat(a,a)["raw_bytes_identical"]
    assert not d.repeat(a,b)["readbacks_both_complete"]
    assert d.repeat(a,a)["numeric_acceptance"]=="NOT_RATIFIED"
