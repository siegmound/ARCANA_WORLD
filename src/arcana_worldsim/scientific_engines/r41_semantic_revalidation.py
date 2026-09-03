from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
from typing import Any
import json

STAGE = "v0.6D1-R4.1"
R40_SEALED = "PASS_R40_ARCANA_MULTI_ENGINE_SCIENTIFIC_REVALIDATION_ORCHESTRATOR_AND_RUNTIME_GOVERNANCE_SEALED"
R41_READY = "PASS_R41_MULTI_ENGINE_SEMANTIC_CALIBRATION_AND_CONTROLLED_MICROBENCHMARK_READINESS"
R41_SEALED = "PASS_R41_MULTI_ENGINE_SEMANTIC_CALIBRATION_CONTROLLED_MICROBENCHMARKS_AND_HISTORICAL_REVALIDATION_GATE_SEALED"

R40_CONFIG_REL = Path("configs/world1_r40_multi_engine_revalidation_v0_6D1_R4_0.json")
R41_CONFIG_REL = Path("configs/world1_r41_semantic_calibration_v0_6D1_R4_1.json")
R40_SEAL_REL = Path("outputs/v0_6D1_R4_0_SEAL/R4_0_FINAL_SEAL_AUDIT.json")
R41_HOST_EVIDENCE_REL = Path("outputs/v0_6D1_R4_1/R4_1_HOST_MICROBENCHMARK_EVIDENCE.json")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: str | Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw).hexdigest()


def frozen_r40_matrix_hash(r40_cfg: dict[str, Any]) -> str:
    return canonical_sha256(
        {
            "frozen_revalidation_windows": r40_cfg["frozen_revalidation_windows"],
            "comparison_domains": r40_cfg["comparison_domains"],
        }
    )


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}


def _finite_number(x: Any) -> bool:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    return x == x and abs(float(x)) != float("inf")


def validate_parent(root: Path, cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[Check]]:
    seal_path = root / R40_SEAL_REL
    r40_cfg_path = root / R40_CONFIG_REL
    checks: list[Check] = []
    if not seal_path.exists():
        return {}, {}, [Check("r40_parent_seal_present", False, str(seal_path))]
    if not r40_cfg_path.exists():
        return {}, {}, [Check("r40_parent_config_present", False, str(r40_cfg_path))]
    seal = load_json(seal_path)
    r40_cfg = load_json(r40_cfg_path)
    checks += [
        Check("r40_parent_seal_present", True, str(seal_path)),
        Check("r40_parent_config_present", True, str(r40_cfg_path)),
        Check("r40_parent_status_exact", seal.get("status") == cfg["required_parent_status"] == R40_SEALED, seal.get("status")),
        Check("r40_parent_verdict_sealed", seal.get("verdict") == "SEALED", seal.get("verdict")),
        Check("r40_parent_zero_failed_checks", seal.get("checks_failed") == 0, seal.get("checks_failed")),
        Check("r40_parent_all_engines_ready", seal.get("summary", {}).get("all_required_engines_ready") is True, seal.get("summary", {}).get("ready_engines")),
    ]
    observed = frozen_r40_matrix_hash(r40_cfg)
    checks.append(Check("r40_frozen_matrix_hash_preserved", observed == cfg["r40_frozen_matrix_sha256"], {"expected": cfg["r40_frozen_matrix_sha256"], "observed": observed}))
    return seal, r40_cfg, checks


def _metric_check(benchmark_id: str, metrics: dict[str, Any], cfg_entry: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    required = cfg_entry["required_metrics"]
    missing = [k for k in required if k not in metrics]
    if missing:
        return False, {"missing": missing}

    try:
        if benchmark_id == "R41_NEMO_B1_ADMIXTURE_CONVERGENCE":
            a = metrics["initial_mean_frequency_gap"]
            b = metrics["final_mean_frequency_gap"]
            ok = all(_finite_number(metrics[k]) for k in ("initial_mean_frequency_gap", "final_mean_frequency_gap", "qfreq_rows", "generations", "patches"))
            ok = ok and float(b) < float(a) and int(metrics["qfreq_rows"]) >= 16 and int(metrics["generations"]) >= 1 and int(metrics["patches"]) == 2
            return ok, {"initial_gap": a, "final_gap": b}
        if benchmark_id == "R41_GEONOMICS_DEFAULT_SPATIAL_DEMOGRAPHY":
            ok = int(metrics["species_count"]) >= 1 and float(metrics["terminal_population_total"]) > 0 and int(metrics["occupied_cells_total"]) > 0 and bool(str(metrics["model_class"]))
            return ok, {"species": metrics["species_count"], "terminal_population_total": metrics["terminal_population_total"], "occupied_cells_total": metrics["occupied_cells_total"]}
        if benchmark_id == "R41_MADINGLEY_ONE_YEAR_ECOSYSTEM":
            ok = int(metrics["initial_cohort_count"]) > 0 and int(metrics["final_cohort_count"]) > 0 and int(metrics["initial_stock_count"]) > 0 and int(metrics["final_stock_count"]) > 0 and int(metrics["years"]) == 1
            return ok, {k: metrics[k] for k in required}
        if benchmark_id == "R41_RANGESHIFTR_DEFAULT_RANGE_DYNAMICS":
            ok = float(metrics["initial_abundance"]) > 0 and float(metrics["final_abundance"]) > 0 and int(metrics["initial_occupied_cells"]) > 0 and int(metrics["final_occupied_cells"]) > 0 and int(metrics["years"]) >= 1
            return ok, {k: metrics[k] for k in required}
        if benchmark_id == "R41_CDMETAPOP_BUNDLED_5GEN_EXAMPLE":
            ok = int(metrics["scenario_rows"]) >= 1 and int(metrics["runtime_generations"]) >= 1 and int(metrics["new_output_files"]) > 0 and int(metrics["csv_output_files"]) > 0 and str(metrics["source_commit"]) == "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118"
            return ok, {k: metrics[k] for k in required}
        if benchmark_id == "R41_SLIM_TWO_POP_TREESEQ_GENE_FLOW":
            ok = int(metrics["tree_nodes"]) > 0 and int(metrics["tree_edges"]) > 0 and int(metrics["tree_individuals"]) > 0 and int(metrics["tree_mutations"]) >= 0 and float(metrics["sequence_length"]) > 0 and int(metrics["generations"]) >= 1
            return ok, {k: metrics[k] for k in required}
    except (TypeError, ValueError, KeyError) as exc:
        return False, {"error": repr(exc), "metrics": metrics}
    return False, {"error": "unknown benchmark id"}


def validate_host_evidence(root: Path, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[Check]]:
    path = root / R41_HOST_EVIDENCE_REL
    if not path.exists():
        return {}, [Check("r41_host_microbenchmark_evidence_present", False, str(path))]
    ev = load_json(path)
    checks: list[Check] = [
        Check("r41_host_microbenchmark_evidence_present", True, str(path)),
        Check("r41_host_evidence_stage", ev.get("stage") == STAGE, ev.get("stage")),
        Check("r41_host_evidence_type", ev.get("evidence_type") == "CONTROLLED_MULTI_ENGINE_MICROBENCHMARK_EVIDENCE", ev.get("evidence_type")),
        Check("r41_host_evidence_canonical_write_false", ev.get("canonical_state_changed") is False, ev.get("canonical_state_changed")),
    ]
    rows = ev.get("benchmarks") or []
    by_id = {x.get("benchmark_id"): x for x in rows if isinstance(x, dict)}
    expected = {x["id"]: x for x in cfg["microbenchmarks"]}
    checks.append(Check("r41_exact_benchmark_set", set(by_id) == set(expected), {"expected": sorted(expected), "observed": sorted(k for k in by_id if k)}))

    for bid, spec in expected.items():
        row = by_id.get(bid)
        if not row:
            checks.append(Check(f"{bid}_present", False))
            continue
        engine = spec["engine"]
        expected_version = cfg["required_engines"][engine]
        checks.extend(
            [
                Check(f"{bid}_engine", row.get("engine") == engine, row.get("engine")),
                Check(f"{bid}_version_pin", row.get("confirmed_version") == expected_version, {"expected": expected_version, "observed": row.get("confirmed_version")}),
                Check(f"{bid}_returncode", row.get("returncode") == 0, row.get("returncode")),
                Check(f"{bid}_reported_pass", row.get("status") == "PASS", row.get("status")),
            ]
        )
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
        ok, detail = _metric_check(bid, metrics, spec)
        checks.append(Check(f"{bid}_metric_semantics", ok, detail))
    return ev, checks


def validate_semantics(cfg: dict[str, Any], r40_cfg: dict[str, Any]) -> list[Check]:
    checks: list[Check] = []
    checks += [
        Check("canonical_owner_arcana", cfg["canonical_state_owner"] == "ARCANA_WorldSim"),
        Check("canonical_state_unchanged", cfg["canonical_state_changed"] is False),
        Check("no_external_direct_write", cfg["external_engine_direct_canonical_write"] is False),
        Check("no_auto_promotion", cfg["automatic_external_evidence_promotion"] is False),
        Check("deep_off", cfg["deep_biological_coupling"] is False),
        Check("historical_windows_not_executed_in_r41", cfg["historical_window_gate"]["execute_in_r41"] is False),
        Check("no_majority_vote", cfg["historical_window_gate"]["no_majority_vote"] is True),
        Check("window_selection_not_result_based", cfg["historical_window_gate"]["selection_based_on_microbenchmark_results"] is False),
    ]
    r40_domains = set(r40_cfg.get("comparison_domains", []))
    auth = cfg["domain_authority"]
    checks.append(Check("all_r40_domains_have_authority", set(auth) == r40_domains, {"missing": sorted(r40_domains - set(auth)), "extra": sorted(set(auth) - r40_domains)}))
    bad_votes = [k for k, v in auth.items() if v.get("vote") is not False]
    checks.append(Check("domain_authority_no_vote", not bad_votes, bad_votes))
    engines = set(cfg["required_engines"])
    bad_refs = []
    for domain, row in auth.items():
        for role in ("primary", "secondary"):
            for engine in row.get(role, []):
                if engine not in engines:
                    bad_refs.append([domain, role, engine])
    checks.append(Check("domain_authority_only_pinned_engines", not bad_refs, bad_refs))
    checks.append(Check("six_required_engines", len(cfg["required_engines"]) == 6, sorted(cfg["required_engines"])))
    checks.append(Check("six_controlled_microbenchmarks", len(cfg["microbenchmarks"]) == 6, [x["id"] for x in cfg["microbenchmarks"]]))
    checks.append(Check("semantic_population_no_literal_N_equivalence", cfg["semantic_rules"]["population_scale"]["rule"] == "NO_LITERAL_CROSS_ENGINE_N_EQUIVALENCE"))
    checks.append(Check("semantic_time_mapping_explicit", cfg["semantic_rules"]["time_scale"]["historical_window_execution_requires_generation_interval"] is True))
    checks.append(Check("semantic_single_runs_not_promotional", cfg["semantic_rules"]["uncertainty"]["single_run_use"] == "SEMANTIC_AND_EXECUTABLE_GATE_ONLY"))
    return checks


def build_authority_matrix(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "status": "FROZEN_PRE_RESULT",
        "majority_vote": False,
        "domains": cfg["domain_authority"],
        "semantic_rules": cfg["semantic_rules"],
        "note": "Authority assigns interpretation responsibility by scientific domain; it does not permit any external engine to write canonical state.",
    }


def build_historical_gate(cfg: dict[str, Any], r40_cfg: dict[str, Any], all_pass: bool) -> dict[str, Any]:
    windows = []
    for row in r40_cfg["frozen_revalidation_windows"]:
        x = dict(row)
        x["selection_based_on_r41_results"] = False
        x["authorized_for_r42_execution"] = bool(all_pass)
        windows.append(x)
    return {
        "stage": STAGE,
        "next_stage": cfg["historical_window_gate"]["next_stage"],
        "status": "AUTHORIZED_FOR_R42" if all_pass else "BLOCKED_BY_R41",
        "authorization_condition": cfg["historical_window_gate"]["authorization_condition"],
        "window_count": len(windows),
        "windows": windows,
        "canonical_state_changed": False,
        "scientific_agreement_claimed": False,
    }


def build_report(root: Path) -> tuple[dict[str, Any], list[Check]]:
    cfg = load_json(root / R41_CONFIG_REL)
    seal, r40_cfg, parent_checks = validate_parent(root, cfg)
    if not r40_cfg:
        return {"stage": STAGE, "status": "BLOCKED_R41_PARENT_R40_NOT_SEALED"}, parent_checks
    ev, evidence_checks = validate_host_evidence(root, cfg)
    semantic_checks = validate_semantics(cfg, r40_cfg)
    checks = parent_checks + semantic_checks + evidence_checks
    failed = [x for x in checks if not x.passed]
    status = R41_READY if not failed else "BLOCKED_R41_CONTROLLED_MICROBENCHMARK_OR_SEMANTIC_GATE"
    report = {
        "stage": STAGE,
        "status": status,
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "parent_r40_status": seal.get("status"),
        "baseline_a_preserved": True,
        "canonical_state_changed": False,
        "deep_biological_coupling": False,
        "scientific_agreement_claimed": False,
        "microbenchmark_evidence_sha256": sha256_file(root / R41_HOST_EVIDENCE_REL) if (root / R41_HOST_EVIDENCE_REL).exists() else None,
        "benchmarks": ev.get("benchmarks", []) if ev else [],
        "checks": [x.to_dict() for x in checks],
    }
    return report, checks
