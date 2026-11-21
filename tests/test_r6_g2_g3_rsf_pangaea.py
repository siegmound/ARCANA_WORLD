"""R6 Earth laboratory fitted-parameter RSF; synthetic row fixtures ONLY."""
import math
import json
import sys
import pytest
from experiments.plate58_deforming_explore_v1.g2_g3_rsf_pangaea import (
  ingest_pangaea_table2,steady_reference_states,advance_aging_states,
  relative_friction_response,RSFSourceError,
)

def source(b2="0.003",dc2="2.5",a_minus_b="0.002"):
    fields=["Event", "Latitude", "Longitude", "Sample label", "Exp", "Location",
      "V [µm/s] (Vo)", "V [µm/s] (V)", "Const (a)", "Const (b1)",
      "Dc [µm] (Dc1)","Const (b2)","Dc [µm] (Dc2)","Parameter (a-b)",
      "Std dev (a)","Std dev (b1)","Std dev (Dc1)","Std dev (b2)",
      "Std dev (Dc2)"]
    vals=["146-891B","44.0","-125.0","LAB_TEST","STEP_A","X",
      "0.01","0.1","0.012","0.007","1.5",b2,dc2,a_minus_b,"","","","",""]
    return ("/* DATA DESCRIPTION:\nCitation: Ikari, MJ; Kopf, AJ (2020) PANGAEA.921284\n*/\n"+
           "\t".join(fields)+"\n"+"\t".join(vals)+"\n").encode()

def fit():return ingest_pangaea_table2(source())["fitted_model_rows"][0]

def test_valid_model_extracted_source_has_provenance_and_no_arcana_authority():
    doc=ingest_pangaea_table2(source())
    assert len(doc["fitted_model_rows"])==1
    assert len(doc["source_sha256"])==64
    assert doc["lab_temperature_k"]==293.15
    assert not doc["arcana_fault_bound"]
    assert doc["physical_T1"] is None

def test_two_state_velocity_step_exact_aging_and_steady_limits():
    row=fit()
    th=steady_reference_states(row)
    v0,v1=row["v0_m_s"],row["v1_m_s"]
    at_v0=relative_friction_response(row,v0,th)
    assert at_v0["delta_mu"]==pytest.approx(0.,abs=1e-14)
    immediate=relative_friction_response(row,v1,th)
    assert immediate["delta_mu"]==pytest.approx(row["a"]*math.log(v1/v0))
    long_term=advance_aging_states(row,th,v1,1e9)
    after=relative_friction_response(row,v1,long_term)
    assert after["delta_mu"]==pytest.approx((row["a"]-sum(s["b"] for s in row["states"]))*math.log(v1/v0))
    assert after["absolute_shear_traction_pa"] is None
    assert after["steady_delta_tau_pa"]==pytest.approx(after["steady_delta_mu"]*1e7)

def test_time_step_semigroup():
    row=fit();th=steady_reference_states(row);v=row["v1_m_s"]
    x=advance_aging_states(row,th,v,0.75)
    y=advance_aging_states(row,x,v,3.25)
    z=advance_aging_states(row,th,v,4.)
    assert y==pytest.approx(z,rel=1e-12)

def test_one_state_when_second_parameters_both_blank():
    doc=ingest_pangaea_table2(source(b2="",dc2="",a_minus_b="0.005"))
    row=doc["fitted_model_rows"][0]
    assert len(row["states"])==1
    assert len(advance_aging_states(row,steady_reference_states(row),row["v1_m_s"],2.))==1

@pytest.mark.parametrize("change",["missing_source","bad_schema","bad_b2","a_minus_b_mismatch"])
def test_table_identity_schema_and_model_weak_law_check(change):
    s=source()
    if change=="missing_source":s=s.replace(b"PANGAEA.921284",b"PANGAEA.999999")
    elif change=="bad_schema":s=s.replace(b"Const (a)",b"Not-a-column")
    elif change=="bad_b2":s=s.replace(b"\t0.003\t2.5\t",b"\t\t2.5\t")
    else:s=s.replace(b"\t0.002\t",b"\t0.500\t")
    with pytest.raises(RSFSourceError):ingest_pangaea_table2(s)

@pytest.mark.parametrize("change",["speed","sigma","state","dt"])
def test_no_extrapolation_nor_hidden_zero(change):
    row=fit();theta=steady_reference_states(row)
    with pytest.raises(RSFSourceError):
        if change=="speed": relative_friction_response(row,row["v1_m_s"]*100,theta)
        elif change=="sigma":relative_friction_response(row,row["v1_m_s"],theta,effective_normal_pa=2e7)
        elif change=="state":relative_friction_response(row,row["v1_m_s"],theta[:-1])
        else:advance_aging_states(row,theta,row["v1_m_s"],-1.)

def test_cli_immutable_provenance_and_manifest(tmp_path,monkeypatch):
    from experiments.plate58_deforming_explore_v1.g2_g3_rsf_pangaea import main
    source_path=tmp_path/"source.tab"
    source_path.write_bytes(source())
    target=tmp_path/"NEW_EVIDENCE"
    monkeypatch.setattr(sys,"argv",["rsf","--source",str(source_path),
                                      "--output",str(target)])
    main()
    payload=json.loads((target/"REPORT.json").read_text())
    manifest=json.loads((target/"MANIFEST.json").read_text())
    assert payload["doi"]=="10.1594/PANGAEA.921284"
    assert manifest["source_sha256"]==payload["source_sha256"]
    assert manifest["no_physical_solve"]
    with pytest.raises(RSFSourceError,match="RSF_OUTPUT_EXISTS_NO_OVERWRITE"):
        main()
