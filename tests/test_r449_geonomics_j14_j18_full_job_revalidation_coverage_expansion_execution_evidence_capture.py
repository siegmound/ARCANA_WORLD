import inspect
import arcana_worldsim.scientific_engines.r449_geonomics_j14_j18_full_job_revalidation_coverage_expansion_execution_evidence_capture as m


def test_parent_plan_hash_is_frozen():
    assert m.EXPECTED_EXPANSION_PLAN_SHA256 == (
        "3a6e1d5b7d454f7c4ecd79c357bc6a2e8cd6e6514c61db07a5d06267834766e5"
    )


def test_plan_hash_is_recomputed():
    s = inspect.getsource(m._verify_plan)
    assert 'bare.pop("plan_sha256", None)' in s
    assert "embedded == recomputed == EXPECTED_EXPANSION_PLAN_SHA256" in s


def test_evidence_is_written_as_deterministic_gzip_jsonl():
    s = inspect.getsource(m._open_deterministic_gzip_jsonl)
    assert "gzip.GzipFile" in s
    assert "mtime=0" in s
    assert 'filename=""' in s


def test_shard_resume_requires_evidence_hash():
    s = inspect.getsource(m._validate_existing_shard)
    assert 's.get("metric_evidence_file_sha256") == sha256(paths["metrics"])' in s
    assert 's.get("authorized_plan_sha256") == plan_sha' in s


def test_partial_or_invalid_shard_is_preserved():
    s = inspect.getsource(m._preserve_invalid_existing_shard)
    assert "failed_or_partial_shards" in s
    assert "shutil.move" in s


def test_expansion_count_contract():
    assert 323172 + 11340 == 334512
    assert 215448 + 7560 == 223008
    assert 107724 + 3780 == 111504
    assert 334512 + 12456 == 346968


def test_full_geonomics_integrity_and_descriptive_math():
    assert 223008 + 6540 == 229548
    assert 111504 + 5916 == 117420
    assert 229548 + 117420 == 346968


def test_closed_evidence_not_executed_in_shards():
    s = inspect.getsource(m._execute_one_shard)
    assert "closed first-cohort branch leaked into expansion" in s
    assert m.J21 not in inspect.getsource(m._load_source_arrays)


def test_scientific_execution_uses_sealed_helpers():
    s = inspect.getsource(m._execute_one_shard)
    assert "_install_exact_nonliteral_carriers" in s
    assert "_exact_carrier_replace_preserve_clock" in s
    assert "_advance_authorized_clock_expected" in s
    assert "_extract_carrier_metrics" in s


def test_no_default_geonomics_queue():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r450():
    assert m.NEXT == (
        "BUILD_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
        "AND_FINAL_GEONOMICS_CLOSURE"
    )
