"""Pure preparation checks; no actual MEEMUM process."""
import copy
import pytest
from experiments.r6_thermo_provider_pilot_v1 import s3_d5_hgp_prepare as h


@pytest.fixture(params=[b"\n", b"\r\n"])
def inputs(request):
    nl = request.param
    dat = nl.join([b"header", b"begin solution phase list", b"cAmph(G)",
        b"Augite(G)", b"melt(G)   ", b"Ep(HP11)", b"Gt(W)", b"Opx(W)",
        b"Bi(W)", b"Ilm(WPH)", b"Sp(WPC)", b"Fsp(C1)", b"end solution phase list",
        b"tail Fsp(C1)", b""])
    model = nl.join([b"alpha(an) 0.555", b"Fsp(HGP) | solution name",
        b"begin_van_laar_sizes", b"alpha(an)     0.555",
        b"end_van_laar_sizes", b"end_of_model", b"alpha(an) 0.555", b""])
    return {"bl691_MEEMUM.dat": dat, "solution_model.dat": model,
            "hp62ver.dat": b"database", "bl691_MEEMUM_input.txt": b"stdin"}


@pytest.mark.parametrize("case", h.CASES)
def test_precise_changes(inputs, case):
    old = copy.deepcopy(inputs)
    result = h.prepare_inputs(inputs, case)
    assert inputs == old
    assert result["hp62ver.dat"] == old["hp62ver.dat"]
    assert result["bl691_MEEMUM_input.txt"] == old["bl691_MEEMUM_input.txt"]
    nl = b"\r\n" if b"\r\n" in old["bl691_MEEMUM.dat"] else b"\n"
    original = b"Fsp(C1)" + nl + b"end solution phase list"
    new = b"Fsp(HGP)" + nl
    if case == "HGP_LOW_ALBITE":
        new += b"lAb(HGP)" + nl
    new += b"end solution phase list"
    assert result["bl691_MEEMUM.dat"] == old["bl691_MEEMUM.dat"].replace(original, new)
    if case == "HGP_PAPER_ALPHA":
        assert result["solution_model.dat"] == old["solution_model.dat"].replace(
            b"alpha(an)     0.555", b"alpha(an)     0.550")
    else:
        assert result["solution_model.dat"] == old["solution_model.dat"]


@pytest.mark.parametrize("old,new", [(b"Fsp(C1)", b"Fsp(I1)"),
    (b"Augite(G)", b"Other"), (b"begin solution phase list", b"missing"),
    (b"end solution phase list", b"missing")])
def test_phase_list_drift(inputs, old, new):
    inputs["bl691_MEEMUM.dat"] = inputs["bl691_MEEMUM.dat"].replace(old, new)
    with pytest.raises(h.HGPError):
        h.prepare_inputs(inputs, "HGP_UPSTREAM")


@pytest.mark.parametrize("value", [b"0.550", b"0.556", b"NaN"])
def test_alpha_drift(inputs, value):
    inputs["solution_model.dat"] = inputs["solution_model.dat"].replace(b"0.555", value)
    with pytest.raises(h.HGPError):
        h.prepare_inputs(inputs, "HGP_PAPER_ALPHA")


def test_unknown_case(inputs):
    with pytest.raises(h.HGPError):
        h.prepare_inputs(inputs, "I1")


def test_extra_input(inputs):
    inputs["perplex_option.dat"] = b"hidden"
    with pytest.raises(h.HGPError):
        h.prepare_inputs(inputs, "HGP_UPSTREAM")


def test_duplicate_model(inputs):
    inputs["solution_model.dat"] += inputs["solution_model.dat"]
    with pytest.raises(h.HGPError):
        h.prepare_inputs(inputs, "HGP_UPSTREAM")


def test_audit_pinned():
    assert h.load_audit()["pilot_candidate"]["authorized"] is False


def test_run_blocked(monkeypatch):
    monkeypatch.setattr(h.sys, "argv", ["hgp", "--phase", "run"])
    monkeypatch.setattr(h, "preflight", lambda: pytest.fail("unexpected preflight"))
    with pytest.raises(h.HGPError, match="HGP_RUN_BLOCKED"):
        h.main()


@pytest.mark.parametrize("same", [True, False])
def test_comparison_not_approval(same):
    a = {"printed_rows": {"C1": {"wt": "31.05"}}, "prn_sha256": "a"}
    b = {"printed_rows": {"HGP": {"wt": "31.05"}}, "prn_sha256": "b"}
    out = h.compare_observations(a, b, same_configuration=same)
    assert out["phase_added"] == ["HGP"]
    assert out["phase_removed"] == ["C1"]
    assert out["scientific_applicability"] == "UNKNOWN"
    assert out["numeric_acceptance"] == "NOT_RATIFIED"
    assert out["disposition"] == ("PRINTED_REPEAT_REVIEW" if same else "MODEL_SENSITIVITY_OBSERVATION_ONLY")


def test_identical_not_numeric_approval():
    a = {"printed_rows": {"HGP": {"wt": "100.00"}}, "prn_sha256": "a"}
    result = h.compare_observations(a, a, same_configuration=True)
    assert result["disposition"] == "PRINTED_REPEAT_IDENTICAL"
    assert result["numeric_acceptance"] == "NOT_RATIFIED"
