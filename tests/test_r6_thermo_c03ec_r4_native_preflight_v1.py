import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r4_native_preflight as r


def prompt(block):
    return b"\n"+block+b"\n"+r.dialogue.WARNING


def initial():
    p=r.PreflightDialogue()
    raw=r.dialogue.PROJECT
    assert p.next_response(raw)==b"c03d\n"
    return p,raw


def test_interleaved_repetitions_and_complete_replay():
    p,raw=initial()
    species=["Si(s)","Si(s)","H2","Si(s)","H2","Si(s)","Si(s)","H2"]
    for i,k in enumerate(species,1):
        raw+=prompt(r.dialogue.SI013 if k=="Si(s)" else r.r2.H2_WARNING)
        assert p.next_response(raw)==b"y\n"
        assert p.events[-1]["global_occurrence"]==i
        assert p.next_response(raw) is None
    raw+=r.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    raw+=r.dialogue.PT
    assert p.next_response(raw)==b"0 0\n"
    dia={"events":p.events,"acknowledged_warning_codes":["013"]*len(species),
         "state":"SENTINEL_SENT","scientific_warning_acceptance":False}
    result={"dialogue":dia,"acknowledged_species":species,"warning_codes":["013"]*len(species)}
    stdin=b"c03d\n"+b"y\n"*len(species)+b"n\n0 0\n"
    r.verify_readback(raw,stdin,result)
    with pytest.raises(ValueError,match="DIALOGUE_RECONCILIATION"):
        r.verify_readback(raw,stdin+b"y\n",result)


def test_total_budget():
    p,raw=initial()
    for i in range(r.MAX_EXACT_ACKNOWLEDGEMENTS):
        raw+=prompt(r.dialogue.SI013 if i%2==0 else r.r2.H2_WARNING)
        assert p.next_response(raw)==b"y\n"
    cursor=p.cursor
    with pytest.raises(ValueError,match="TOTAL_DIAGNOSTIC_BUDGET"):
        p.next_response(raw+prompt(r.r2.H2_WARNING))
    assert p.cursor==cursor


@pytest.mark.parametrize("block",[r.r2.H2_WARNING.replace(b"H2",b"H2O"),
                                 r.dialogue.SI013.replace(b"legitimate",b"unknown"),
                                 b"**warning ver999** unknown"])
def test_unknown_or_changed(block):
    p,raw=initial()
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw+prompt(block))


@pytest.mark.parametrize("code",["017","059","966","968","536"])
def test_forbidden(code):
    p,raw=initial()
    with pytest.raises(ValueError,match="FORBIDDEN_NATIVE_DIAGNOSTIC"):
        p.next_response(raw+prompt(b"**warning ver"+code.encode()+b"** bad"))


def test_wrong_state():
    p,raw=initial()
    raw+=r.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw+prompt(r.dialogue.SI013))


def test_warning_source_contract():
    raw=(b"      subroutine wrnstp\n"
         b"      write (*,'(a)') 'Continue execution despite this warning (Y/N)?'\n"
         b"      if (lopt(56)) then\n"
         b"         if (.not.readyn()) then\n"
         b"         end if\n"
         b"1010  format ('**warning ver536**')\n"
         b"      end\n      logical function readyn()\n")
    assert r.verify_warning_source(raw)["diagnostic_budget"]==32
    with pytest.raises(ValueError,match="WRNSTP_SOURCE_DRIFT"):
        r.verify_warning_source(raw.replace(b"lopt(56)",b"lopt(55)"))


def test_new_archive():
    assert r.OUT.name.endswith("NEW04")
    assert r.OUT not in (r.r3.OUT,r.r2.FAILED,r.r2.OUT)
