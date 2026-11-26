import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_diagnostic_benchmark as r


def sample(t="498.15",p="1500",y="0"):
    return f"Stable phases at:\n T(K) = {t}\n P(bar) = {p}\n Y(CO2) = {y}\nPhase Compositions (molar proportions):\n".encode()


def test_capture_point_exact():
    x=r.capture_point(sample(),r.POINTS[0])
    assert x["id"]=="B01" and x["scientific_acceptance"] is False


@pytest.mark.parametrize("raw",[sample(t="499"),sample(p="1600"),sample(y=".1"),
                                 b"empty",sample()+b"**warning ver053** bad"])
def test_bad_point(raw):
    with pytest.raises(ValueError,match="C03EE_POINT"):
        r.capture_point(raw,r.POINTS[0])


def test_source_hash_guard():
    with pytest.raises(ValueError,match="FLIB_PIN"):
        r.verify_fluid_source(b"unverified")


def test_three_points_then_zero():
    p=r.DiagnosticDialogue("ACT_ONLY",{},[])
    p.state="AWAIT_NEXT"
    p.requested=["B01"]
    raw=b""
    prompt=r.c.dialogue.PT+b" T(K) P(bar) Y(CO2)\n"
    raw+=sample()+prompt
    assert p.next_response(raw)==b"473.15 4000 0\n"
    raw+=sample("473.15","4000")+prompt
    assert p.next_response(raw)==b"588.15 2000 0\n"
    raw+=sample("588.15","2000")+prompt
    assert p.next_response(raw)==r.r5.SENTINEL
    assert p.requested==["B01","B02","B03"]
    assert [x["id"] for x in p.completed]==p.requested
    assert p.state=="SENTINEL_SENT"


def test_unexpected_interactive_prompt_after_point():
    p=r.DiagnosticDialogue("ACT_ONLY",{},[])
    p.state="AWAIT_NEXT"
    with pytest.raises(ValueError,match="UNEXPECTED_INTERACTIVE_PROMPT"):
        p.next_response(r.c.dialogue.WARNING)


def test_no_unpinned_archive():
    assert r.OUT!=r.ed.OUT and r.OUT!=r.r5.OUT and len(r.POINTS)==3
