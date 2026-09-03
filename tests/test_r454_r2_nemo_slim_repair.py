from pathlib import Path
import hashlib

POST={'benchmarks/r454/run_nemo_r454.sh': '6b4cadda339c7c253a3bbde42fa45ad7a59173cb3284309c3691e2dbf7b3930c', 'benchmarks/r454/nemo_collect_r454.py': '4e588c5ac9be22ef6a7de11f3f8611bd750d4d7f2a86c416ac9a73f7730c7ffb', 'benchmarks/r454/slim_collect_r454.py': '91dd0851b709664ed51dffdce2c65ae34ff7a0418ead57aca16cef33adb41c6e'}

def test_exact_postpatch_hashes():
    for rel,h in POST.items():
        assert hashlib.sha256(Path(rel).read_bytes()).hexdigest()==h

def test_nemo_wrapper_always_has_failure_json_paths():
    s=Path("benchmarks/r454/run_nemo_r454.sh").read_text()
    assert "NEMO qfreq output missing" in s
    assert "NEMO collector failed before result materialization" in s
    assert "find . -maxdepth 1 -type f -name '*.qfreq'" in s

def test_nemo_seed_readback_uses_native_stdout():
    s=Path("benchmarks/r454/nemo_collect_r454.py").read_text()
    assert "setting\\s+random\\s+seed\\s+from\\s+input\\s+value" in s
    assert "bound_ini==seed and bound_stdout==seed" in s

def test_nemo_schema_is_fail_closed():
    s=Path("benchmarks/r454/nemo_collect_r454.py").read_text()
    assert 'header[:4] != ["pop","trait","locus","allele"]' in s
    assert "qfreq row" in s

def test_slim_uses_documented_two_sample_set_divergence_call():
    s=Path("benchmarks/r454/slim_collect_r454.py").read_text()
    assert "ts.divergence(sample_sets=[a,b])" in s
    assert "indexes=[(0,1)]" not in s

def test_slim_seed_readback_is_native_stdout():
    s=Path("benchmarks/r454/slim_collect_r454.py").read_text()
    assert "Initial\\s+random\\s+seed" in s
    assert "seed_ok=(seed_readback==seed)" in s

def test_metric_ids_unchanged():
    n=Path("benchmarks/r454/nemo_collect_r454.py").read_text()
    s=Path("benchmarks/r454/slim_collect_r454.py").read_text()
    assert "NEMO_ALLELE_FREQUENCY_TRAJECTORY" in n
    assert "NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY" in n
    assert "SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY" in s
    assert "SLIM_ANCESTRY_GENE_FLOW_SUMMARY" in s

def test_no_numeric_threshold_added():
    txt="\n".join(Path(rel).read_text() for rel in POST)
    assert '"numeric_acceptance_threshold":None' in txt
