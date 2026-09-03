from pathlib import Path
import hashlib,importlib.util
POST_SHA="870001cabd0708ca1c2ccb8c1fc23987af6daf7635fe2fb590901ed63df57a20"
def _m():
 p=Path("src/arcana_worldsim/scientific_engines/r455_non_geonomics_80_stream_execution_evidence_capture.py")
 spec=importlib.util.spec_from_file_location("r455r1",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def test_postpatch_hash_exact():
 p=Path("src/arcana_worldsim/scientific_engines/r455_non_geonomics_80_stream_execution_evidence_capture.py");assert hashlib.sha256(p.read_bytes()).hexdigest()==POST_SHA
def test_seed_ledger_order_is_not_authority():
 m=_m();assert m._same_seed_ledger([1,2,3,4],[4,1,3,2])
def test_seed_ledger_membership_still_exact():
 m=_m();assert not m._same_seed_ledger([1,2,3,4],[1,2,3,5]);assert not m._same_seed_ledger([1,1,2,3],[1,2,3,4])
def test_r43_config_accepts_seed_zero_to_three(tmp_path):
 m=_m();p=tmp_path/"ENGINE_CONFIG.tsv";p.write_text("seed_0\t40\nseed_1\t10\nseed_2\t30\nseed_3\t20\n",encoding="utf-8");assert m._r43_config_seeds(p)==[40,10,30,20];assert m._same_seed_ledger(m._r43_config_seeds(p),[10,20,30,40])
def test_r43_config_rejects_wrong_seed_key_count(tmp_path):
 m=_m();p=tmp_path/"ENGINE_CONFIG.tsv";p.write_text("seed_0\t1\nseed_1\t2\nseed_2\t3\n",encoding="utf-8")
 try:m._r43_config_seeds(p)
 except RuntimeError:pass
 else:raise AssertionError("expected fail closed")
def test_order_semantics_explicit():
 s=Path("src/arcana_worldsim/scientific_engines/r455_non_geonomics_80_stream_execution_evidence_capture.py").read_text();assert "seed_list_order_semantics" in s
def test_raw_extractors_use_membership():
 s=Path("src/arcana_worldsim/scientific_engines/r455_non_geonomics_80_stream_execution_evidence_capture.py").read_text();assert s.count('_same_seed_ledger(observed_seeds,job["frozen_seeds"])')==2
