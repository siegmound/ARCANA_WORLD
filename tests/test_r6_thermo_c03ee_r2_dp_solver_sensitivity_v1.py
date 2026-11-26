import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ee_r2_dp_solver_sensitivity as r


def test_interval_scientific_notation():
    assert r.interval("0.733E-02")== (r.D("0.007325"),r.D("0.007335"))


def test_interval_product_signed():
    assert r.product((r.D(-2),r.D(-1)),(r.D(3),r.D(4)))==(r.D(-8),r.D(-3))


def test_option_replace_only():
    raw=b"foo 3\nMINFXC_solver 0 | comment\nbar F\n"
    assert r.solver_option(raw)==raw.replace(b"solver 0",b"solver -1")


def test_option_append():
    assert r.solver_option(b"foo 3\n")==b"foo 3\nMINFXC_solver -1\n"


@pytest.mark.parametrize("raw",[b"MINFXC_solver 1\n",b"MINFXC_solver -1\n",
                                  b"MINFXC_solver 0\nminfxc_solver 0\n",
                                  b"MINFXC_solver nonsense\n"])
def test_option_guard(raw):
    with pytest.raises(ValueError,match="SOLVER"):
        r.solver_option(raw)


def test_archive_distinct():
    assert r.OUT!=r.r1.OUT and len(r.prior.POINTS)==3
