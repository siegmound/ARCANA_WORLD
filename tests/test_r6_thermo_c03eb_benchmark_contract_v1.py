from decimal import Decimal
import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03eb_benchmark_contract as b

BLOCK="""cAmph(DP)
begin_dqf_corrections
DQF(ts_q) = 10000 | ds5/ds6
DQF(gl) = -3000 | ds6
DQF(parg) = -10000 | ds6
DQF(grun) = -3000 | ds6
DQF(mrb_q) = 0 | ds6
| DQF(cumm) = 0 | ds6
| DQF(mrb_q) = 8000 | ds5
| DQF(gl) = 3000 | ds5
| DQF(parg) = 15000 | ds5
| DQF(grun) = -5000 | ds5
| DQF(cumm) = -6400 | ds5
end_dqf_corrections
end_of_model
"""


def test_switch_exact_source_lines():
    out,changes=b.switch_block(BLOCK)
    assert b.active_dqf(out)==b.DS5
    assert len(changes)==9
    assert b.active_dqf(BLOCK)==b.DS6


def test_switch_preserves_crlf():
    out,_=b.switch_block(BLOCK.replace("\n","\r\n"))
    assert out.count("\r\n")==BLOCK.count("\n")


def test_switch_rejects_source_drift():
    with pytest.raises(ValueError,match="ORIGINAL_DQF_DRIFT"):
        b.switch_block(BLOCK.replace("-3000","-2999",1))


def test_switch_rejects_missing_ds5_row():
    with pytest.raises(ValueError,match="SWITCH_DRIFT"):
        b.switch_block(BLOCK.replace("| DQF(cumm) = -6400 | ds5\n",""))


def test_dry_basis_ferric_inventory():
    masses={k:100 for k in b.DRY}
    mol=b.benchmark_moles(masses,"0.10")
    assert Decimal(mol["O2"])*4/Decimal(mol["FEO"])==Decimal("0.10")
    assert "H2O" not in mol


def test_contract_is_nonexact_and_not_authorized():
    z=b.benchmark_contract({k:100 for k in b.DRY},{k:{} for k in b.EXCLUSIONS.values()})
    assert z["reference"]["exact_O2_input"] is None
    assert len(z["arms"])==2 and len(z["points"])==3
    assert z["first_batch_design"]["total_requested_points"]==6
    assert not z["first_batch_design"]["authorization"] and not z["executable"]
    assert all("GlTrTsPg" not in x["solution_models"] for x in z["arms"].values())
    assert all(len(x["solution_models"])==17 for x in z["arms"].values())
