import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r2_phase_policy_audit as r


def test_projection_exact_and_water_separate():
    v=r.project_vector({"H2O":"1","O2":"-0.5"},["O2"],["H2O"])
    assert v["full_sum"]=="1/2" and v["conserved_sum"]=="-1/2"
    assert v["nonpositive_conserved_sum"] and v["outside_basis"]==[]


def test_projection_outside_basis_and_zero():
    v=r.project_vector({"SIO2":"1","O2":"-1","C":"1","ZERO":"0"},["SIO2","O2"],["H2O"])
    assert v["outside_basis"]==["C"] and v["conserved_sum"]=="0"


def test_projection_overlap_rejected():
    with pytest.raises(ValueError,match="OVERLAPPING_BASIS"):
        r.project_vector({"H2O":"1"},["H2O"],["H2O"])


def test_literal_token_boundaries():
    assert [x["line"] for x in r.reference_hits("H2O\nH2\nfoo_H2\nH2(s)\nH2O2","H2")]==[2,4]


def test_r1_still_rejects_h2_after_two_si():
    p=r.c.PreflightDialogue()
    raw=r.c.dialogue.PROJECT
    assert p.next_response(raw)==b"c03d\n"
    for _ in range(2):
        raw+=b"\n"+r.c.dialogue.SI013+b"\n"+r.c.dialogue.WARNING
        assert p.next_response(raw)==b"y\n"
    raw+=b"\n"+r.H2_WARNING+b"\n"+r.c.dialogue.WARNING
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw)


def test_write_once_audit_archive():
    assert r.OUT not in (r.c.OUT,r.c.FAILED_OUT)
    assert r.FAILED==r.c.OUT
