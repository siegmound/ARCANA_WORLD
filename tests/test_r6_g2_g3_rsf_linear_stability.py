"""Analytical one/two-state quasistatic rate-state stability benchmarks."""
import math
import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.g2_g3_rsf_linear_stability import (
    StabilityInputError,critical_normalized_stiffness,
    roots_at_normalized_stiffness,analyze_model_fit_records,
    build_source_bound_evidence,
)

def row(a=.01,b1=.015,dc1=2e-6,b2=None,dc2=None,source_line=10,published=None):
    states=[{"b":b1,"Dc_m":dc1}]
    if b2 is not None:states.append({"b":b2,"Dc_m":dc2})
    return {"source_line":source_line,"event":"LAB_EVENT","sample_label":"LAB_SAMPLE",
            "experiment":"A","v0_m_s":1e-8,"v1_m_s":1e-7,
            "a":a,"states":states,
            "published_a_minus_b":(a-b1-(b2 if b2 is not None else 0)) if published is None else published}

def test_one_state_exact_critical_stiffness_pressure_normalized():
    r=row();out=critical_normalized_stiffness(r)
    assert out["critical_K_over_sigma_effective_m_inv"]==pytest.approx(2500)
    assert out["critical_K_Pa_per_m"] is None
    assert out["physical_normal_stress_pa"] is None
    assert out["physical_instability_predicted"] is False

@pytest.mark.parametrize("factor,expect",[(.5,"UNSTABLE_FOR_THIS_HYPOTHETICAL_KAPPA"),(2.,"STABLE_FOR_THIS_HYPOTHETICAL_KAPPA")])
def test_one_state_linearized_eigenvalues_match_critical_stiffness(factor,expect):
    r=row();k=critical_normalized_stiffness(r)["critical_K_over_sigma_effective_m_inv"]
    p=roots_at_normalized_stiffness(r,k*factor)
    assert p["classification"]==expect
    assert p["K_Pa_per_m"] is None


def test_one_state_rate_strengthening_stable_at_all_positive_stiffness():
    r=row(a=.02,b1=.01)
    assert critical_normalized_stiffness(r)["critical_K_over_sigma_effective_m_inv"]==0
    for k in [1e-3,1,1e4]:
        assert roots_at_normalized_stiffness(r,k)["classification"]=="STABLE_FOR_THIS_HYPOTHETICAL_KAPPA"


def test_two_equal_state_distances_reduce_to_one_state_total_b():
    r=row(a=.01,b1=.009,dc1=2e-6,b2=.007,dc2=2e-6)
    out=critical_normalized_stiffness(r)
    assert out["critical_K_over_sigma_effective_m_inv"]==pytest.approx((.009+.007-.01)/2e-6,rel=1e-10)
    assert out["qualification"]=="CRITICAL_STIFFNESS_TWO_STATE_ROUTH_HURWITZ"


def test_two_unequal_state_distances_dynamic_stability_critical_not_mean_dc():
    r=row(a=.01,b1=.013,dc1=1e-6,b2=.007,dc2=5e-6)
    k=critical_normalized_stiffness(r)["critical_K_over_sigma_effective_m_inv"]
    assert k>0 and math.isfinite(k)
    assert roots_at_normalized_stiffness(r,k*0.5)["classification"]=="UNSTABLE_FOR_THIS_HYPOTHETICAL_KAPPA"
    assert roots_at_normalized_stiffness(r,k*2)["classification"]=="STABLE_FOR_THIS_HYPOTHETICAL_KAPPA"
    naive=(.013+.007-.01)/((1e-6+5e-6)/2)
    assert not math.isclose(k,naive,rel_tol=.1)


def test_two_state_stronger_at_any_positive_kappa():
    r=row(a=.03,b1=.011,dc1=1e-6,b2=.009,dc2=4e-6)
    out=critical_normalized_stiffness(r)
    assert out["critical_K_over_sigma_effective_m_inv"]==0
    for k in [1e-4,1e2]:
        assert roots_at_normalized_stiffness(r,k)["classification"]=="STABLE_FOR_THIS_HYPOTHETICAL_KAPPA"

@pytest.mark.parametrize("change,expected",[
    ("a_nonpositive","EXCLUDED_NONPOSITIVE_DIRECT_EFFECT_OR_NEGATIVE_STATE_WEIGHT"),
    ("b_negative","EXCLUDED_NONPOSITIVE_DIRECT_EFFECT_OR_NEGATIVE_STATE_WEIGHT"),
    ("round_zero","EXCLUDED_SOURCE_ROUNDED_ZERO_A_MINUS_B")])
def test_fail_closed_nonadmissible_source_parameters(change,expected):
    r=row()
    if change=="a_nonpositive":r["a"]=-.01
    if change=="b_negative":r["states"][0]["b"]=-.01
    if change=="round_zero":r["published_a_minus_b"]=0.
    out=critical_normalized_stiffness(r)
    assert out["qualification"]==expected
    assert out["critical_K_over_sigma_effective_m_inv"] is None
    with pytest.raises(StabilityInputError,match="NOT_QUALIFIED"):
        roots_at_normalized_stiffness(r,1.)

@pytest.mark.parametrize("field,value",[("a",float('nan')),("v0_m_s",0.),("Dc_m",-3.)])
def test_fail_closed_nonfinite_and_numerically_invalid_parameter(field,value):
    r=row()
    if field=="Dc_m":r["states"][0]["Dc_m"]=value
    else:r[field]=value
    with pytest.raises(StabilityInputError):critical_normalized_stiffness(r)


def test_duplicate_source_rows_are_not_silently_double_counted():
    with pytest.raises(StabilityInputError,match="DUPLICATED_SOURCE_LINE"):
        analyze_model_fit_records([row(),row()])


def test_inventory_retains_all_fit_rows_but_never_infers_observed_events():
    a=analyze_model_fit_records([row(),row(a=.02,b1=.01,source_line=11),
             row(a=.01,b1=.015,source_line=12,published=0.)])
    assert a["inventory"]["fitted_model_rows"]==3
    assert a["inventory"]["positive_critical_ratio_rows"]==1
    assert a["inventory"]["pressure_values_assigned"]==0
    assert a["inventory"]["arcana_faults_assigned"]==0
    assert a["inventory"]["independent_experimental_trials_inferred"] is None


def test_source_sha_fails_closed_before_writing_evidence(tmp_path):
    raw=tmp_path/"source.tab";raw.write_bytes(b"synthetic not publisher")
    out=tmp_path/"new"
    with pytest.raises(StabilityInputError,match="SOURCE_SHA_MISMATCH"):
        build_source_bound_evidence(raw,tmp_path,out)
    assert not out.exists()


def test_evidence_dir_not_overwritten(tmp_path):
    raw=tmp_path/"source.tab";raw.write_bytes(b"synthetic not publisher")
    out=tmp_path/"new";out.mkdir()
    with pytest.raises(StabilityInputError,match="OUTPUT_ALREADY_EXISTS"):
        build_source_bound_evidence(raw,tmp_path,out)


def synthetic_table_for_pipeline(rows=66):
    header=["Event", "Latitude", "Longitude", "Sample label", "Exp", "Location",
      "V [µm/s] (Vo)", "V [µm/s] (V)", "Const (a)", "Const (b1)",
      "Dc [µm] (Dc1)","Const (b2)","Dc [µm] (Dc2)","Parameter (a-b)",
      "Std dev (a)","Std dev (b1)","Std dev (Dc1)","Std dev (b2)",
      "Std dev (Dc2)"]
    # Model FIT rows, never passed off as published laboratory measurements.
    entries=[]
    for i in range(rows):
        entries.append(["SYNTHETIC_EVENT","44.0","-125.0",f"SYNTHETIC_{i}",
           "STEP_A","X","0.01","0.1","0.012","0.007","1.5",
           "0.003","2.5","0.002","","","","",""])
    return ("/* DATA DESCRIPTION:\nCitation: Ikari MJ; Kopf AJ PANGAEA.921284 - SYNTHETIC TEST ONLY\n*/\n"+
            "\t".join(header)+"\n"+"\n".join("\t".join(x) for x in entries)+"\n").encode()


def test_complete_sha_bound_66_fitted_row_pipeline_and_immutability(tmp_path,monkeypatch):
    import sys
    import hashlib
    import json
    from experiments.plate58_deforming_explore_v1 import g2_g3_rsf_linear_stability as stab
    from experiments.plate58_deforming_explore_v1.g2_g3_rsf_pangaea import main as ingest_main
    raw=tmp_path/"original_synthetic.tab"
    raw.write_bytes(synthetic_table_for_pipeline())
    digest=hashlib.sha256(raw.read_bytes()).hexdigest()
    monkeypatch.setattr(stab,"SOURCE_SHA256",digest)
    ingest_dir=tmp_path/"INGEST01"
    monkeypatch.setattr(sys,"argv",["ingest","--source",str(raw),"--output",str(ingest_dir)])
    ingest_main()
    output=tmp_path/"STABILITY01"
    result=build_source_bound_evidence(raw,ingest_dir,output)
    assert result["summary"]["fitted_model_rows"]==66
    assert result["summary"]["pressure_values_assigned"]==0
    assert (output/"MANIFEST.json").is_file()
    assert json.loads((output/"REPORT.json").read_text())["physical_T1"] is None
    with pytest.raises(StabilityInputError,match="OUTPUT_ALREADY_EXISTS"):
        build_source_bound_evidence(raw,ingest_dir,output)
    tamper=json.loads((ingest_dir/"REPORT.json").read_text())
    tamper["fitted_model_rows"][0]["a"]=0.5
    (ingest_dir/"REPORT.json").write_text(json.dumps(tamper))
    with pytest.raises(StabilityInputError,match="REPORT_MANIFEST_NOT_SOURCE_BOUND"):
        build_source_bound_evidence(raw,ingest_dir,tmp_path/"NEW_NEVER_CREATED")
    assert not (tmp_path/"NEW_NEVER_CREATED").exists()


def test_conflicting_rounded_and_derived_friction_signs_are_unqualified():
    r=row(a=.01,b1=.0102,published=.0001)
    out=critical_normalized_stiffness(r)
    assert out["qualification"]=="EXCLUDED_PUBLISHED_AND_DERIVED_SIGN_CONFLICT"
    assert out["critical_K_over_sigma_effective_m_inv"] is None
