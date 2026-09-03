from pathlib import Path
import inspect
import arcana_worldsim.scientific_engines.r456_multi_engine_23_job_full_evidence_review_final_revalidation_closure as m

def test_exact_parent_hashes():
    assert len(m.EXPECTED_R452_PLAN_SHA256)==64
    assert len(m.EXPECTED_R453_REGISTRY_SHA256)==64

def test_exact_geonomics_jobs():
    assert m.GEONOMICS_JOB_IDS == [
        "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
        "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS",
        "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS",
    ]

def test_exact_engine_distribution():
    assert m.EXPECTED_ENGINE_COUNTS == {
        "Madingley":4,"RangeShifter":5,"CDMetaPOP":5,
        "NEMO":3,"Geonomics":3,"SLiM":3,
    }

def test_final_verdict_has_no_numeric_corroboration_claim():
    assert "NO_NUMERIC_CORROBORATION_CLAIM" in m.FINAL_VERDICT

def test_non_geonomics_review_is_bundle_level_not_parent_only():
    s=inspect.getsource(m.review_non_geonomics)
    for name in [
        "RAW_ENGINE_EVIDENCE.json",
        "SCIENTIFIC_READOUT_EVIDENCE.json",
        "JOB_AUDIT.json",
        "JOB_COMPLETE.json",
    ]:
        assert name in s
    assert "corpus_stream_records_exact_reconstruction" in s
    assert "corpus_metric_records_exact_reconstruction" in s

def test_metric_sources_must_exist():
    s=inspect.getsource(m._verify_metric_sources)
    assert "p.exists()" in s

def test_r450_rehashes_all_manifest_files():
    s=inspect.getsource(m.review_geonomics)
    assert "sha256(path)" in s
    assert "all_35_corpus_hashes_exact" in s

def test_r456_has_no_engine_execution_surface():
    s=Path("src/arcana_worldsim/scientific_engines/r456_multi_engine_23_job_full_evidence_review_final_revalidation_closure.py").read_text()
    assert "subprocess" not in s
    assert "runpy" not in s
    assert "conda run" not in s
    assert "nemo2.4.2" not in s
    assert "slim -s" not in s

def test_no_majority_or_numeric_threshold_authority():
    s=inspect.getsource(m.build)
    assert '"no_majority_vote"' in s
    assert '"numeric_cross_engine_corroboration_claimed": False' in s

def test_next_returns_to_worldsim_roadmap_not_another_required_r4_stage():
    assert m.NEXT == "R4_MULTI_ENGINE_REVALIDATION_COMPLETE_RETURN_TO_WORLDSIM_ROADMAP"
