from pathlib import Path
import hashlib,re
POST_SHA="e3e607a5a9a9d1154d507797ce93f70f12680f1041ba6d7672e771cddc2d7111"
def _s(): return Path("capture_v0_6D1_R4_55_scientific_jobs.ps1").read_text(encoding="utf-8")
def test_exact_postpatch_hash():
 p=Path("capture_v0_6D1_R4_55_scientific_jobs.ps1");assert hashlib.sha256(p.read_bytes()).hexdigest()==POST_SHA
def test_observed_parser_defect_removed():
 s=_s();assert "}throw" not in s;assert '}throw "unsupported path' not in s
def test_risky_minified_token_patterns_removed():
 s=_s()
 for pat in [r"-not\$",r'Write-Host"',r"-eq\d",r"-ne\d",r"-ge\$",r"\)throw"]:
  assert re.search(pat,s) is None,pat
def test_dispatch_paths_unchanged():
 s=_s()
 for x in ["benchmarks/r43/madingley_r43.R","benchmarks/r43/rangeshiftr_r43.R","benchmarks/r421/nemo_r421.py","benchmarks/r421/slim_r421.py","benchmarks/r421/cdmetapop_r421_matched.py"]: assert x in s
def test_original_nemo_base_python_symbol_preserved():
 s=_s();assert "$CondaBasePython" in s and "run -n '$NemoEnv' $BasePyQ" in s
def test_timeouts_unchanged():
 s=_s();assert s.count("$timeout = 3600")==4;assert s.count("$timeout = 5400")==1;assert "1800" in s
def test_resume_semantics_preserved():
 s=_s();assert "RESUME VALID, SKIP" in s and "Archive-Partial" in s and "fails resume integrity" in s
def test_powershell_owns_wsl_boundary():
 s=_s();assert '$psi.Arguments = "bash -s"' in s and "Invoke-WslScript" in s
def test_failure_evidence_preserved():
 s=_s();assert "ENGINE_EXECUTION_FAILURE" in s and "RAW_ENGINE_EVIDENCE.json" in s and "Prior jobs remain resumable." in s
