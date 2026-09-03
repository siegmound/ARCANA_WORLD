from pathlib import Path
import inspect
import arcana_worldsim.scientific_engines.r455_non_geonomics_80_stream_execution_evidence_capture as m
def test_parent_hashes(): assert len(m.EXPECTED_R452_PLAN_SHA256)==64 and len(m.EXPECTED_R453_REGISTRY_SHA256)==64
def test_20_contracts(): assert len(m.EXPECTED_CONTRACT_SHA256)==20 and all(len(x)==64 for x in m.EXPECTED_CONTRACT_SHA256.values())
def test_dispatch(): assert m.ADAPTERS["Madingley"]["path"].endswith("madingley_r43.R") and m.ADAPTERS["NEMO"]["path"].endswith("nemo_r421.py") and m.ADAPTERS["CDMetaPOP"]["path"].endswith("cdmetapop_r421_matched.py")
def test_10_metrics(): assert len({x for v in m.EXPECTED_METRICS.values() for x in v})==10 and all(len(v)==2 for v in m.EXPECTED_METRICS.values())
def test_no_threshold_metric_factory(): s=inspect.getsource(m._metric);assert '"numeric_acceptance_threshold":None' in s and '"automatic_pass_fail_from_value":False' in s
def test_resume_fail_closed(): s=Path("capture_v0_6D1_R4_55_scientific_jobs.ps1").read_text();assert "fails resume integrity" in s and "repair_history" in s
def test_ps_owns_wsl(): s=Path("capture_v0_6D1_R4_55_scientific_jobs.ps1").read_text();assert "bash -s" in s and "$WslExe" in s
def test_nemo_base_python(): s=Path("capture_v0_6D1_R4_55_scientific_jobs.ps1").read_text();assert "$CondaBasePython" in s and "run -n '$NemoEnv' $BasePyQ" in s
def test_cd_profile(): s=inspect.getsource(m.preflight);assert "REPAIR_PROFILE" in s and "target leakage" in s
def test_slim_tskit(): s=inspect.getsource(m.extract_slim_job);assert "tskit.load" in s and "ts.divergence(sample_sets=[a,b])" in s
def test_dynamic_cd(): s=inspect.getsource(m._cd_dynamic_summary);assert '"neutral" not in p.as_posix().lower()' in s
def test_next(): assert m.NEXT=="BUILD_R456_MULTI_ENGINE_23_JOB_FULL_EVIDENCE_REVIEW_AND_FINAL_REVALIDATION_CLOSURE"
