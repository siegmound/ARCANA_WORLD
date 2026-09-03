import json
from pathlib import Path

from arcana_worldsim.scientific_engines import r43_historical_revalidation as r43

ROOT = Path(__file__).resolve().parents[1]


def _j(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def _prepared():
    report, checks = r43.prepare(ROOT)
    assert report["status"] == r43.PREPARED
    assert all(c.passed for c in checks)
    return report


def test_r43_canonical_governance_invariants():
    c = _j(r43.CFG_REL)
    assert c["canonical_state_owner"] == "ARCANA_WorldSim"
    assert c["canonical_state_changed"] is False
    assert c["external_engine_direct_canonical_write"] is False
    assert c["automatic_external_evidence_promotion"] is False
    assert c["deep_biological_coupling"] is False


def test_r43_boundary_response_is_explicitly_not_literal_multimyr_replay():
    c = _j(r43.CFG_REL)
    e = c["execution_semantics"]
    assert e["mode"] == "NORMALIZED_BOUNDARY_RESPONSE_REVALIDATION"
    assert e["literal_multi_myr_engine_replay"] is False
    assert e["end_state_leakage_forbidden"] is True
    assert e["arcana_end_state_use"] == "COMPARISON_TARGET_ONLY"


def test_r43_does_not_adjudicate_or_claim_agreement():
    e = _j(r43.CFG_REL)["execution_semantics"]
    assert e["discordance_adjudication_in_r43"] is False
    assert e["scientific_agreement_claimed"] is False


def test_parent_r42_seal_is_exact():
    s = _j(r43.R42_SEAL_REL)
    assert s["status"] == r43.R42_SEALED


def test_exact_r42_frozen_registry_is_23_unique_jobs():
    d = _j(r43.R42_JOBS_REL)
    assert d["job_count"] == 23
    assert len(d["jobs"]) == 23
    assert len({x["job_id"] for x in d["jobs"]}) == 23
    assert all(x["execution_status"] == "FROZEN_NOT_EXECUTED_IN_R42" for x in d["jobs"])


def test_r43_registry_is_byte_source_hash_bound_to_r42():
    _prepared()
    d = _j(r43.OUT_REL / "R4_3_FROZEN_JOB_REGISTRY.json")
    assert d["unchanged_from_r42"] is True
    assert d["job_count"] == 23
    assert d["source_sha256"] == r43.sha256_file(ROOT / r43.R42_JOBS_REL)


def test_seven_frozen_windows_preserved():
    c = _j(r43.R42_CFG_REL)
    assert len(c["windows"]) == 7
    _prepared()
    d = _j(r43.OUT_REL / "R4_3_WINDOW_BASELINE_DESCRIPTORS.json")
    assert len(d["windows"]) == 7
    assert set(d["windows"]) == {x["id"] for x in c["windows"]}


def test_prepare_phase_is_21_of_21_and_performs_no_historical_engine_run():
    d = _prepared()
    assert d["checks_total"] == 21
    assert d["checks_passed"] == 21
    assert d["checks_failed"] == 0
    assert d["job_count"] == 23
    assert d["window_count"] == 7
    assert d["historical_engine_execution_performed"] is False


def test_exact_92_replicate_seeds_and_global_uniqueness():
    _prepared()
    l = _j(r43.OUT_REL / "R4_3_SEED_LEDGER.json")
    seeds = [r["seed"] for j in l["jobs"] for r in j["replicates"]]
    assert len(l["jobs"]) == 23
    assert len(seeds) == 92
    assert len(set(seeds)) == 92


def test_seed_algorithm_is_deterministic():
    a = r43._seed("R42_J10_H0_POST_CHA1_RECOVERY_NEMO", 0)
    b = r43._seed("R42_J10_H0_POST_CHA1_RECOVERY_NEMO", 0)
    c = r43._seed("R42_J10_H0_POST_CHA1_RECOVERY_NEMO", 1)
    assert a == b and a != c and 1 <= a <= 2_000_000_000


def test_every_unit_mapping_is_pre_result_and_has_authority_domains():
    _prepared()
    d = _j(r43.OUT_REL / "R4_3_PER_JOB_UNIT_MAPPING.json")
    assert d["mapping_count"] == 23
    assert all(x["pre_result_frozen"] is True for x in d["mappings"])
    assert all(x["domain_mapping"] for x in d["mappings"])
    assert all(all(y["majority_vote"] is False for y in x["domain_mapping"]) for x in d["mappings"])


def test_time_mapping_is_explicit_and_nonliteral_for_all_jobs():
    _prepared()
    d = _j(r43.OUT_REL / "R4_3_PER_JOB_UNIT_MAPPING.json")
    for m in d["mappings"]:
        t = m["time_mapping"]
        assert t["literal_history_replay"] is False
        assert t["mapping_class"] == "EXPLICIT_COMPRESSED_REPRESENTATIVE_RESPONSE"
        assert t["historical_window_duration_years"] > 0
        assert t["engine_representative_steps"] > 0


def test_population_mapping_forbids_literal_arcana_N_equivalence():
    _prepared()
    d = _j(r43.OUT_REL / "R4_3_PER_JOB_UNIT_MAPPING.json")
    assert all(m["population_mapping"]["literal_arcana_N_equivalence"] is False for m in d["mappings"])


def test_cross_engine_population_counts_are_explicitly_forbidden():
    p = _j(r43.CFG_REL)["comparability_policy"]
    assert p["direct_cross_engine_population_counts"] == "FORBIDDEN"
    assert p["madingley_cohort_species_equivalence"] == "FORBIDDEN"
    assert p["implicit_year_generation_equivalence"] == "FORBIDDEN"


def test_job_contract_separates_engine_input_from_comparison_target():
    _prepared()
    p = ROOT / r43.OUT_REL / "jobs" / "R42_J10_H0_POST_CHA1_RECOVERY_NEMO" / "JOB_CONTRACT.json"
    c = json.loads(p.read_text(encoding="utf-8"))
    assert c["engine_input"]["derived_from"] == "ARCANA_START_STATE_AND_EXOGENOUS_FORCING_ONLY"
    assert c["engine_input"]["end_state_leakage"] is False
    assert c["comparison_target"]["use"] == "POST_EXECUTION_NORMALIZATION_AND_R4.4_ADJUDICATION_ONLY"
    assert "arcana_end_state" in c["comparison_target"]


def test_engine_tsv_contains_exact_four_deterministic_seeds():
    _prepared()
    p = ROOT / r43.OUT_REL / "jobs" / "R42_J16_SAPIENT_3MA_TO_200KA_SLIM" / "ENGINE_CONFIG.tsv"
    txt = p.read_text(encoding="utf-8")
    assert "replicate_count\t4" in txt
    for i in range(4):
        assert f"seed_{i}\t" in txt


def test_normalizer_uses_only_within_engine_ratios_and_deltas():
    raw = {
        "replicates": [
            {"status": "PASS", "metrics": {"initial_abundance": 10, "final_abundance": 15, "initial_heterotroph_biomass": 2, "final_heterotroph_biomass": 3}},
            {"status": "PASS", "metrics": {"initial_abundance": 20, "final_abundance": 10, "initial_heterotroph_biomass": 4, "final_heterotroph_biomass": 4}},
        ]
    }
    contract = {"frozen_parent_job": {"job_id": "X"}, "engine_input": {"replicates": [{}, {}]}, "comparison_target": {"use": "comparison"}}
    n = r43.normalize_raw("RangeShifter", raw, contract)
    assert n["normalization_semantics"] == "WITHIN_ENGINE_DIMENSIONLESS_RESPONSE_ONLY_NO_RAW_N_EQUIVALENCE"
    assert n["normalized_metrics"]["population_response_ratio"]["n"] == 2
    assert n["normalized_metrics"]["heterotroph_biomass_response_ratio"]["n"] == 2
    assert n["discordance_class"] is None


def test_geonomics_adapter_fail_closed_as_semantic_noncomparability():
    txt = (ROOT / "benchmarks/r43/geonomics_r43.py").read_text(encoding="utf-8")
    assert "SEMANTIC_NONCOMPARABILITY" in txt
    assert "DO_NOT_INTERPRET_DEFAULT_MODEL_AS_HISTORICAL_CONCORDANCE" in txt
    assert "driver_application':'NONE__PINNED_DEFAULT_SPATIAL_MODEL_EXECUTION_ONLY" in txt


def test_rangeshifter_adapter_preserves_single_replicate_semantics():
    txt = (ROOT / "benchmarks/r43/rangeshiftr_r43.R").read_text(encoding="utf-8")
    assert "Replicates=1" in txt
    assert "positive" in txt.lower() or "occupied" in txt.lower()


def test_cdmetapop_adapter_does_not_modify_pinned_source_tree():
    txt = (ROOT / "benchmarks/r43/cdmetapop_r43.py").read_text(encoding="utf-8")
    assert "implement_disease" in txt
    assert "copy" in txt.lower()
    assert "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118" in txt


def test_smoke_set_is_fixed_one_job_per_engine_and_not_scientific_selection():
    txt = (ROOT / "capture_v0_6D1_R4_3_historical_jobs.ps1").read_text(encoding="utf-8")
    ids = [
        "R42_J01_H0_DEEP_TIME_BACKGROUND_MADINGLEY",
        "R42_J02_H0_DEEP_TIME_BACKGROUND_RANGESHIFTER",
        "R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP",
        "R42_J10_H0_POST_CHA1_RECOVERY_NEMO",
        "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
        "R42_J16_SAPIENT_3MA_TO_200KA_SLIM",
    ]
    assert all(x in txt for x in ids)
    assert "never used for result selection" in txt


def test_completion_policy_only_accepts_scientific_or_meaningful_noncomparability():
    p = _j(r43.CFG_REL)["completion_policy"]
    assert set(p["allowed_terminal_job_classes"]) == {"SCIENTIFIC_RESULT", "SEMANTIC_NONCOMPARABILITY"}
    assert set(p["blocked_job_classes"]) == {"ENGINE_EXECUTION_FAILURE", "ADAPTER_FAILURE", "MISSING_EVIDENCE"}



def test_r43_r1_nemo_adapter_uses_control_python_and_pinned_conda_engine_runtime():
    cap = (ROOT / "capture_v0_6D1_R4_3_historical_jobs.ps1").read_text(encoding="utf-8")
    nemo = (ROOT / "benchmarks/r43/nemo_r43.py").read_text(encoding="utf-8")
    assert "$ControlPythonPath" in cap
    assert "CONTROL_PYTHON=$ControlPythonQ" in cap
    assert "'$NemoEnv'" in cap
    assert "conda_exe,'run','-n',nemo_env,'nemo2.4.2'" in nemo
    assert "CONDA_RUN_NEMO_ENV" in nemo


def test_r43_r1_repair_mode_is_exactly_three_nemo_jobs_and_preserves_prior_evidence():
    cap = (ROOT / "capture_v0_6D1_R4_3_historical_jobs.ps1").read_text(encoding="utf-8")
    for jid in (
        "R42_J10_H0_POST_CHA1_RECOVERY_NEMO",
        "R42_J13_H0_LATE_CENOZOIC_NEMO",
        "R42_J17_SAPIENT_3MA_TO_200KA_NEMO",
    ):
        assert jid in cap
    assert "R43_R1_NEMO_RETURN127_PRE_REPAIR" in cap
    assert "Backup-R43EvidenceForRepair" in cap
    assert "PASS_R43_R1_THREE_NEMO_JOBS_REEXECUTED" in cap
