import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_r1_native_preflight as r


def raw_sites(model="GlTrTsPg"):
    return "\n".join("**warning ver059** endmember "+k+" in solution model "+model+
        " has invalid site populations." for k in r.LEGACY["GlTrTsPg"]).encode()+b"\n"


def test_exact_legacy_warning_removal():
    assert r.corrected_counts(raw_sites(),{**r.EXPECTED,"059":3},["Act(M)"])==r.EXPECTED


@pytest.mark.parametrize("raw,roster",[(raw_sites("Act(M)"),["Act(M)"]),
    (raw_sites(),["GlTrTsPg"]),(raw_sites()+raw_sites(),["Act(M)"])])
def test_no_general_warning_relaxation(raw,roster):
    with pytest.raises(ValueError,match="LEGACY"):
        r.corrected_counts(raw,{**r.EXPECTED,"059":3},roster)


def test_other_warning_drift_remains_blocking():
    with pytest.raises(ValueError,match="WARNING_PROFILE"):
        r.corrected_counts(raw_sites(),{**r.EXPECTED,"059":3,"046":1},["Act(M)"])
