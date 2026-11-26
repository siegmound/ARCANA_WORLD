import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ed_scientific_readiness as r


def test_warning_context_keeps_actual_text():
    raw=b"before\n**warning ver099** diagnostic text\ncontinuation\n"
    assert r.warning_context(raw,"099")==[
        {"line":2,"lines":["before","**warning ver099** diagnostic text","continuation"]}]
    assert r.warning_context(raw,"114")==[]


@pytest.mark.parametrize("arm",list(r.COUNTS))
def test_counts_and_duplicate_rejection(arm):
    amph,n=r.AMPH[arm]
    rows=[{"model":"m"+str(i),"count":1} for i in range(15)]
    rows += [{"model":"other","count":1056},{"model":amph,"count":n}]
    result={"native_model_details":{"pseudocompound_reports":rows}}
    assert sum(r.summarize_counts(result,arm).values())==1071
    rows[-1]["model"]="other"
    with pytest.raises(ValueError,match="COUNT_DRIFT"):
        r.summarize_counts(result,arm)


def test_no_native_launch_in_audit():
    assert r.OUT!=r.r5.OUT and r.OUT.name.endswith("NEW01")
    assert r.STATUS.endswith("SCIENTIFIC_REVIEW_REQUIRED")
