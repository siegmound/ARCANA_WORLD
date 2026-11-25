from pathlib import Path
import pytest
from experiments.r6_thermo_provider_pilot_v1 import c01_readiness_audit as c

ROOT=Path(__file__).resolve().parents[1]


def test_source_and_scope():
    d,a=c.check_design(ROOT)
    assert a["continental_lower_oxide_sum"]==pytest.approx(99.98)
    assert a["nmorb_transcribed_oxide_sum"]==pytest.approx(99.30499999999999)
    assert not a["nmorb_raw_source_bytes_verified"]
    assert not a["provider_native_input_qualified"]
    assert d["authorial_selection"] is None
    assert d["engine_executions_authorized"]==0


def test_source_pt_and_coverage_not_calibration():
    d,_=c.check_design(ROOT)
    p=d["experimental_PT"]
    assert p["P_kbar"]==pytest.approx(5.77416)
    assert p["T_C"]==pytest.approx(619.3514857175009)
    assert d["source_state"]["absolute_pressure_pa"] is None
    assert d["provider"]["mbCpx"] is None


def test_m04_receipt_pin():
    import json
    r=json.loads((c.m.HERE/"m04_fair_library_receipt_v1.json").read_text())
    assert r["manifest_sha256"]==c.M04_SHA
    assert r["base_chemistry_sha256"]==c.BASE_X
    assert r["states"]==21 and r["additional_engine_runs"]==0
