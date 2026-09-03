from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math
import shutil

import numpy as np

from arcana_worldsim.state_query import r55_contact_history as r55

STAGE = "v0.6D1-R5.6"
OUT_REL = Path("outputs/v0_6D1_R5_6")
R55_OUT_REL = Path("outputs/v0_6D1_R5_5")
R55_AUDIT_REL = R55_OUT_REL / "R5_5_INTEGRATED_AUDIT.json"
R55_HISTORY_REL = R55_OUT_REL / "R5_5_CONTACT_ZONE_HISTORY.json"
R55_ATLAS_REL = R55_OUT_REL / "R5_5_CONTACT_OPPORTUNITY_ATLAS.npz"
R55_CONTEXT_REL = R55_OUT_REL / "R5_5_CROSS_ENGINE_CONTACT_CONTEXT.json"
R55_BINDING_REL = R55_OUT_REL / "R5_5_PARENT_CANDIDATE_BINDING.json"
R55_OUTPUT_MANIFEST_REL = R55_OUT_REL / "R5_5_OUTPUT_MANIFEST.json"
R55_SOURCE_REL = Path("src/arcana_worldsim/state_query/r55_contact_history.py")
R41_SLIM_REL = Path("benchmarks/r41/R41_two_pop_gene_flow.slim")
SOURCE_MANIFEST_REL = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_6.json")

EXPECTED_R55_SOURCE_SHA256 = "1b74257bce2397e9456330e5122a95fe4b4a16d5ddb56039c06d8a866092f716"
EXPECTED_R41_SLIM_SHA256 = "a38178b2332d46d4a71a3ce51b2d9ed2b8d8767adfeefb40c1b1e408a43b0068"
EXPECTED_PAIR_COUNT = 35
EXPECTED_FAMILY_COUNT = 12
EXPECTED_AGE_STATE_COUNT = 141
EXPECTED_CONTEXT_COUNT = 105
SEEDS = (560601, 560602)
VARIANTS = {
    "NO_FLOW": 0.0,
    "LOW_BIDIRECTIONAL": 0.005,
    "HIGH_BIDIRECTIONAL": 0.020,
}
FOUNDER_SIZE_PER_POP = 200
SEQUENCE_LENGTH_BP = 1_000_000
RECOMBINATION_RATE_PER_BP = 1e-8
MUTATION_RATE_PER_BP = 0.0
CONTACT_ACTIVE_RULE = "ONE_CELL_MATCHED_ENSEMBLE_SUPPORT_GT_ZERO_AT_STATE"
STATE_TO_SLIM_TIME_RULE = "ONE_R55_J14_AGE_STATE_TO_ONE_STANDARDIZED_SLIM_REPRODUCTIVE_TRANSITION_NOT_LITERAL_GENERATION_TIME"


class R56Error(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def semantic_sha256(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _verify_manifest(root: Path, rel: Path) -> bool:
    p = Path(root) / rel
    if not p.is_file():
        return False
    try:
        doc = load_json(p)
        files = dict(doc.get("files") or {})
        if not files:
            return False
        for name, meta in files.items():
            fp = p.parent / name
            if not fp.is_file():
                return False
            if fp.stat().st_size != int(meta.get("bytes", -1)):
                return False
            if sha256_file(fp) != meta.get("sha256"):
                return False
        return True
    except Exception:
        return False


def validate_parent_authority(root: Path, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    strict = not allow_non_scientific_dev
    required = {
        "r55_audit": R55_AUDIT_REL,
        "r55_history": R55_HISTORY_REL,
        "r55_atlas": R55_ATLAS_REL,
        "r55_context": R55_CONTEXT_REL,
        "r55_binding": R55_BINDING_REL,
        "r55_output_manifest": R55_OUTPUT_MANIFEST_REL,
        "r55_source": R55_SOURCE_REL,
        "r41_slim_reference": R41_SLIM_REL,
    }
    checks: dict[str, bool] = {f"present::{k}": (root / rel).is_file() for k, rel in required.items()}
    try:
        audit = load_json(root / R55_AUDIT_REL)
        s = audit.get("summary") or {}
        checks["r55_candidate_semantics"] = (
            audit.get("status") == "PASS_R55_CONTACT_ZONE_AND_GENE_FLOW_HISTORY_CONSOLIDATION_CANDIDATE"
            and audit.get("scientific_candidate_eligible") is True
            and int(s.get("family_count", -1)) == EXPECTED_FAMILY_COUNT
            and int(s.get("cross_lineage_pair_count", -1)) == EXPECTED_PAIR_COUNT
            and int(s.get("age_state_count", -1)) == EXPECTED_AGE_STATE_COUNT
            and int(s.get("cross_engine_context_record_count", -1)) == EXPECTED_CONTEXT_COUNT
            and int(s.get("pair_with_one_cell_contact_opportunity_count", -1)) == EXPECTED_PAIR_COUNT
            and s.get("new_external_engine_execution_performed") is False
            and s.get("r53_cdmetapop_used_as_contact_geometry") is False
            and s.get("r54_nemo_used_as_contact_geometry") is False
            and s.get("realized_admixture_claimed") is False
            and s.get("numeric_gene_flow_truth_claimed") is False
            and s.get("single_contact_history_winner_selected") is False
            and s.get("majority_vote") is False
            and s.get("canonical_state_changed") is False
            and s.get("derived_refinement_promoted_to_canon") is False
            and s.get("deep_biological_coupling") is False
        )
    except Exception:
        checks["r55_candidate_semantics"] = False
    try:
        h = load_json(root / R55_HISTORY_REL)
        records = h.get("pair_records") or []
        checks["r55_history_semantics"] = (
            h.get("status") == "R55_ARCANA_NATIVE_CONTACT_ZONE_HISTORY"
            and "NOT_REALIZED_ADMIXTURE" in str(h.get("semantics"))
            and int(h.get("cross_lineage_pair_count", -1)) == EXPECTED_PAIR_COUNT
            and int(h.get("age_state_count", -1)) == EXPECTED_AGE_STATE_COUNT
            and len(records) == EXPECTED_PAIR_COUNT
            and all(r.get("any_one_cell_contact_opportunity_state") is True for r in records)
            and all(r.get("single_contact_zone_winner_selected") is False for r in records)
            and h.get("support_thresholds_are_majority_vote") is False
        )
    except Exception:
        checks["r55_history_semantics"] = False
    try:
        ctx = load_json(root / R55_CONTEXT_REL)
        checks["r55_context_semantics"] = (
            ctx.get("status") == "R55_CONTACT_HISTORY_WITH_HETEROGENEOUS_R53_R54_CONTEXT"
            and int(ctx.get("record_count", -1)) == EXPECTED_CONTEXT_COUNT
            and len(ctx.get("records") or []) == EXPECTED_CONTEXT_COUNT
            and "DO_NOT_CREATE_OR_MOVE_CONTACT_WINDOWS" in str(ctx.get("semantics"))
        )
    except Exception:
        checks["r55_context_semantics"] = False
    try:
        with np.load(root / R55_ATLAS_REL, allow_pickle=False) as z:
            ages = np.asarray(z["age_ma"], dtype=float)
            pair_ids = np.asarray(z["pair_ids"]).astype(str)
            near = np.asarray(z["one_cell_contact_ensemble_fraction"], dtype=float)
            exact = np.asarray(z["exact_contact_ensemble_fraction"], dtype=float)
        checks["r55_atlas_shape_semantics"] = (
            ages.shape == (EXPECTED_AGE_STATE_COUNT,)
            and pair_ids.shape == (EXPECTED_PAIR_COUNT,)
            and near.shape == (EXPECTED_PAIR_COUNT, EXPECTED_AGE_STATE_COUNT)
            and exact.shape == near.shape
            and np.all((near >= 0.0) & (near <= 1.0))
            and np.all((exact >= 0.0) & (exact <= 1.0))
            and np.all(exact <= near + 1e-12)
        )
    except Exception:
        checks["r55_atlas_shape_semantics"] = False
    checks["r55_output_manifest_integrity"] = _verify_manifest(root, R55_OUTPUT_MANIFEST_REL)
    checks["r55_source_exact_hash"] = (sha256_file(root / R55_SOURCE_REL) == EXPECTED_R55_SOURCE_SHA256) if strict and (root / R55_SOURCE_REL).is_file() else (root / R55_SOURCE_REL).is_file()
    checks["r41_slim_reference_exact_hash"] = (sha256_file(root / R41_SLIM_REL) == EXPECTED_R41_SLIM_SHA256) if strict and (root / R41_SLIM_REL).is_file() else (root / R41_SLIM_REL).is_file()
    inherited = r55.validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev)
    checks["r55_inherited_r54_r53_r52_r51_j14_chain_pass"] = not inherited.get("failed")
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    return {
        "stage": STAGE,
        "status": "PASS_R56_IMMUTABLE_R55_PARENT_CANDIDATE_AUTHORITY" if not failed else "BLOCKED_R56_PARENT_AUTHORITY",
        "scientific_parent_mode": strict,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
        "r55_inherited_parent_authority": inherited,
    }


def build_schedule_classes(pair_ids: Iterable[str], one_cell_contact_fraction: np.ndarray) -> tuple[list[dict[str, Any]], dict[str, str]]:
    pair_ids = [str(x) for x in pair_ids]
    x = np.asarray(one_cell_contact_fraction, dtype=float)
    if x.ndim != 2 or x.shape[0] != len(pair_ids):
        raise R56Error("pair/contact atlas shape mismatch")
    if np.any((x < 0.0) | (x > 1.0)):
        raise R56Error("contact support fraction outside [0,1]")
    by_hash: dict[str, dict[str, Any]] = {}
    pair_map: dict[str, str] = {}
    for i, pair_id in enumerate(pair_ids):
        mask = np.asarray(x[i] > 0.0, dtype=np.uint8)
        if not np.any(mask):
            raise R56Error(f"R5.5 parent says pair has contact opportunity but atlas has none: {pair_id}")
        h = hashlib.sha256(mask.tobytes()).hexdigest()
        if h not in by_hash:
            by_hash[h] = {"schedule_sha256": h, "mask": mask, "pair_ids": []}
        by_hash[h]["pair_ids"].append(pair_id)
    schedules: list[dict[str, Any]] = []
    for n, h in enumerate(sorted(by_hash), start=1):
        rec = by_hash[h]
        sid = f"SCH{n:03d}"
        rec["schedule_id"] = sid
        rec["pair_ids"] = sorted(rec["pair_ids"])
        rec["active_state_count"] = int(np.sum(rec["mask"]))
        schedules.append(rec)
        for pair_id in rec["pair_ids"]:
            pair_map[pair_id] = sid
    return schedules, pair_map


def _slim_vector(mask: np.ndarray) -> str:
    vals = ",".join(str(int(v)) for v in np.asarray(mask, dtype=np.uint8).tolist())
    return f"c({vals})"


def render_slim_script(mask: np.ndarray, migration_rate: float) -> str:
    mask = np.asarray(mask, dtype=np.uint8)
    if mask.ndim != 1 or mask.size != EXPECTED_AGE_STATE_COUNT:
        raise R56Error(f"SLiM contact mask must have {EXPECTED_AGE_STATE_COUNT} states")
    if not (0.0 <= float(migration_rate) < 0.5):
        raise R56Error("SLiM standardized migration challenge rate outside safe contract")
    end_bp = SEQUENCE_LENGTH_BP - 1
    return f'''// ARCANA WorldSim {STAGE} standardized ancestry/admixture challenge\n// Contact schedule comes only from R5.5 one-cell contact opportunity (>0 matched-ensemble support).\n// One SLiM reproductive transition per R5.5 age state is computational indexing, NOT literal biological time.\ninitialize() {{\n    initializeTreeSeq();\n    initializeMutationRate({MUTATION_RATE_PER_BP:.1f});\n    initializeMutationType("m1", 0.5, "f", 0.0);\n    initializeGenomicElementType("g1", m1, 1.0);\n    initializeGenomicElement(g1, 0, {end_bp});\n    initializeRecombinationRate({RECOMBINATION_RATE_PER_BP:.12g});\n    defineConstant("CONTACT", {_slim_vector(mask)});\n    defineConstant("STATE_COUNT", {EXPECTED_AGE_STATE_COUNT});\n    defineConstant("MIGRATION_RATE", {float(migration_rate):.12g});\n}}\n1 early() {{\n    sim.addSubpop("p1", {FOUNDER_SIZE_PER_POP});\n    sim.addSubpop("p2", {FOUNDER_SIZE_PER_POP});\n    sim.treeSeqRememberIndividuals(p1.individuals);\n    sim.treeSeqRememberIndividuals(p2.individuals);\n    if (CONTACT[0] == 1) {{\n        p1.setMigrationRates(p2, MIGRATION_RATE);\n        p2.setMigrationRates(p1, MIGRATION_RATE);\n    }} else {{\n        p1.setMigrationRates(p2, 0.0);\n        p2.setMigrationRates(p1, 0.0);\n    }}\n}}\n2:STATE_COUNT early() {{\n    idx = community.tick - 1;\n    if (CONTACT[idx] == 1) {{\n        p1.setMigrationRates(p2, MIGRATION_RATE);\n        p2.setMigrationRates(p1, MIGRATION_RATE);\n    }} else {{\n        p1.setMigrationRates(p2, 0.0);\n        p2.setMigrationRates(p1, 0.0);\n    }}\n}}\n(STATE_COUNT + 1) late() {{\n    catn("R56_FINAL_P1=" + p1.individualCount);\n    catn("R56_FINAL_P2=" + p2.individualCount);\n    catn("R56_ACTIVE_STATES=" + sum(CONTACT));\n    sim.treeSeqOutput("r56.trees");\n    sim.simulationFinished();\n}}\n'''


def summarize_ancestry_segments(segments_by_haplotype: list[list[tuple[float, float, int]]], sequence_length: float, donor_label: int = 1) -> dict[str, Any]:
    if not (sequence_length > 0):
        raise R56Error("sequence length must be positive")
    donor_total = 0.0
    tract_count = 0
    max_tract = 0.0
    per_hap: list[float] = []
    any_count = 0
    for segments in segments_by_haplotype:
        ordered = sorted(segments, key=lambda x: (float(x[0]), float(x[1])))
        cursor = 0.0
        current = 0.0
        hap_donor = 0.0
        for left, right, label in ordered:
            left, right = float(left), float(right)
            if abs(left - cursor) > 1e-6 or right < left or right > sequence_length + 1e-9:
                raise R56Error("incomplete/overlapping ancestry segment geometry")
            cursor = right
            span = right - left
            if int(label) == donor_label:
                donor_total += span
                hap_donor += span
                if current <= 0.0:
                    tract_count += 1
                current += span
                max_tract = max(max_tract, current)
            else:
                current = 0.0
        if abs(cursor - sequence_length) > 1e-6:
            raise R56Error("ancestry segments do not cover full sequence")
        frac = hap_donor / sequence_length
        per_hap.append(frac)
        any_count += int(hap_donor > 0.0)
    n = len(segments_by_haplotype)
    if n == 0:
        raise R56Error("no recipient haplotypes")
    return {
        "recipient_haplotype_count": n,
        "donor_ancestry_fraction_mean": float(donor_total / (n * sequence_length)),
        "donor_ancestry_fraction_haplotype_minmax": [float(min(per_hap)), float(max(per_hap))],
        "recipient_haplotype_with_any_donor_ancestry_fraction": float(any_count / n),
        "donor_tract_count_total": int(tract_count),
        "donor_tract_length_mean_bp": float(donor_total / tract_count) if tract_count else 0.0,
        "donor_tract_length_max_bp": float(max_tract),
    }


def prepare_ancestry_challenges(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R56Error(f"R5.6 parent authority failed: {auth['failed']}")
    out = root / OUT_REL
    out.mkdir(parents=True, exist_ok=True)

    with np.load(root / R55_ATLAS_REL, allow_pickle=False) as z:
        ages = np.asarray(z["age_ma"], dtype=float)
        pair_ids = np.asarray(z["pair_ids"]).astype(str).tolist()
        near = np.asarray(z["one_cell_contact_ensemble_fraction"], dtype=float)
    if ages.shape != (EXPECTED_AGE_STATE_COUNT,) or len(pair_ids) != EXPECTED_PAIR_COUNT:
        raise R56Error("R5.5 atlas differs from R5.6 fixed parent contract")
    schedules, pair_map = build_schedule_classes(pair_ids, near)

    history = load_json(root / R55_HISTORY_REL)
    hist_by_pair = {str(r["pair_id"]): r for r in history.get("pair_records") or []}
    if set(hist_by_pair) != set(pair_ids):
        raise R56Error("R5.5 history/atlas pair IDs mismatch")

    streams: list[dict[str, Any]] = []
    work_root = out / "slim_work"
    if work_root.exists():
        shutil.rmtree(work_root)
    for sched in schedules:
        mask = np.asarray(sched["mask"], dtype=np.uint8)
        for variant, rate in VARIANTS.items():
            for seed in SEEDS:
                wd_rel = OUT_REL / "slim_work" / sched["schedule_id"] / variant / f"seed_{seed}"
                wd = root / wd_rel
                wd.mkdir(parents=True, exist_ok=True)
                slim_path = wd / "ARCANA_R56.slim"
                slim_path.write_text(render_slim_script(mask, rate), encoding="utf-8")
                cfg = {
                    "stage": STAGE,
                    "status": "R56_PREPARED_STREAM_INPUT",
                    "schedule_id": sched["schedule_id"],
                    "schedule_sha256": sched["schedule_sha256"],
                    "pair_ids": sched["pair_ids"],
                    "active_contact_state_count": int(sched["active_state_count"]),
                    "contact_state_count": EXPECTED_AGE_STATE_COUNT,
                    "contact_active_rule": CONTACT_ACTIVE_RULE,
                    "state_to_slim_time_rule": STATE_TO_SLIM_TIME_RULE,
                    "variant": variant,
                    "migration_rate": float(rate),
                    "seed": int(seed),
                    "founder_size_per_population": FOUNDER_SIZE_PER_POP,
                    "sequence_length_bp": SEQUENCE_LENGTH_BP,
                    "recombination_rate_per_bp": RECOMBINATION_RATE_PER_BP,
                    "mutation_rate_per_bp": MUTATION_RATE_PER_BP,
                    "r55_contact_support_fraction_used_as_migration_magnitude": False,
                    "r55_contact_geometry_used_only_as_binary_availability_schedule": True,
                    "numeric_admixture_truth_claimed": False,
                    "automatic_scientific_pass_fail_from_ancestry_value": False,
                }
                write_json(wd / "STREAM_CONFIG.json", cfg)
                streams.append({
                    "stream_numeric_id": len(streams) + 1,
                    "schedule_id": sched["schedule_id"],
                    "schedule_sha256": sched["schedule_sha256"],
                    "pair_ids": sched["pair_ids"],
                    "variant": variant,
                    "migration_rate": float(rate),
                    "seed": int(seed),
                    "work_dir": str(wd_rel).replace("\\", "/"),
                    "slim_sha256": sha256_file(slim_path),
                    "stream_config_sha256": sha256_file(wd / "STREAM_CONFIG.json"),
                })

    schedule_records = []
    for s in schedules:
        mask_arr = np.asarray(s["mask"], dtype=np.uint8)
        active_idx = np.flatnonzero(mask_arr).astype(int).tolist()
        schedule_records.append({
            "schedule_id": s["schedule_id"],
            "schedule_sha256": s["schedule_sha256"],
            "pair_ids": s["pair_ids"],
            "pair_count": len(s["pair_ids"]),
            "active_contact_state_count": int(s["active_state_count"]),
            "active_state_indices": active_idx,
            "active_age_ma": [float(ages[i]) for i in active_idx],
            "contact_mask_semantic_sha256": semantic_sha256(mask_arr.astype(int).tolist()),
        })
    plan = {
        "stage": STAGE,
        "status": "PASS_R56_SLIM_ANCESTRY_ADMIXTURE_CHALLENGE_PLAN_PREPARED",
        "scientific_parent_mode": not allow_non_scientific_dev_parent,
        "pair_count": EXPECTED_PAIR_COUNT,
        "age_state_count": EXPECTED_AGE_STATE_COUNT,
        "age_ma": [float(x) for x in ages.tolist()],
        "schedule_class_count": len(schedules),
        "variant_count": len(VARIANTS),
        "seed_count": len(SEEDS),
        "planned_stream_count": len(streams),
        "seeds": list(SEEDS),
        "variants": [{"name": k, "migration_rate": float(v)} for k, v in VARIANTS.items()],
        "schedule_deduplication_semantics": "ONLY_IDENTICAL_BINARY_R55_CONTACT_SCHEDULES_ARE_DEDUPLICATED_NO_PAIR_IS_REMOVED_OR_RANKED",
        "contact_active_rule": CONTACT_ACTIVE_RULE,
        "state_to_slim_time_rule": STATE_TO_SLIM_TIME_RULE,
        "model": {
            "founder_size_per_population": FOUNDER_SIZE_PER_POP,
            "sequence_length_bp": SEQUENCE_LENGTH_BP,
            "recombination_rate_per_bp": RECOMBINATION_RATE_PER_BP,
            "mutation_rate_per_bp": MUTATION_RATE_PER_BP,
            "tree_sequence_recording": True,
            "founders_permanently_remembered_for_local_ancestry": True,
        },
        "selection_rules": {
            "result_selected_tuning": False,
            "majority_vote": False,
            "single_pair_winner": False,
            "single_admixture_history_winner": False,
            "external_engine_defines_arcana_target": False,
            "automatic_numeric_scientific_pass_fail": False,
        },
        "semantics": {
            "r55_contact_support_fraction_used_as_migration_magnitude": False,
            "r55_binary_contact_schedule_is_input_authority": True,
            "migration_rates_are_standardized_engine_challenges_not_literal_hominid_rates": True,
            "slim_ticks_are_standardized_computational_index_not_literal_arcana_generations": True,
            "simulated_ancestry_is_not_promoted_to_realized_historical_admixture": True,
        },
        "pair_to_schedule": pair_map,
        "schedules": schedule_records,
        "streams": streams,
    }
    write_json(out / "R5_6_SLIM_EXECUTION_PLAN.json", plan)
    binding = {
        "stage": STAGE,
        "status": "R56_PARENT_CANDIDATE_BINDING",
        "r55_audit_sha256": sha256_file(root / R55_AUDIT_REL),
        "r55_history_sha256": sha256_file(root / R55_HISTORY_REL),
        "r55_atlas_sha256": sha256_file(root / R55_ATLAS_REL),
        "r55_context_sha256": sha256_file(root / R55_CONTEXT_REL),
        "r55_output_manifest_sha256": sha256_file(root / R55_OUTPUT_MANIFEST_REL),
        "r55_source_sha256": sha256_file(root / R55_SOURCE_REL),
        "binding_semantics": "R55_CANDIDATE_BOUND_BY_SEMANTICS_MANIFEST_AND_HASH_AFTER_VALIDATION_NO_MICRO_SEAL_REQUIRED",
    }
    write_json(out / "R5_6_PARENT_CANDIDATE_BINDING.json", binding)
    return plan


def _load_stream_results(root: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for s in plan.get("streams") or []:
        wd = root / Path(str(s["work_dir"]))
        cfgp = wd / "STREAM_CONFIG.json"
        resp = wd / "ANCESTRY_RESULT.json"
        runp = wd / "STREAM_RUNTIME.json"
        treep = wd / "r56.trees"
        if not all(p.is_file() for p in (cfgp, resp, runp, treep)):
            raise R56Error(f"missing R5.6 stream evidence: {wd}")
        cfg = load_json(cfgp); res = load_json(resp); run = load_json(runp)
        if sha256_file(cfgp) != s.get("stream_config_sha256") or sha256_file(wd / "ARCANA_R56.slim") != s.get("slim_sha256"):
            raise R56Error(f"prepared input hash drift: {wd}")
        if run.get("status") != "PASS_R56_SLIM_STREAM" or int(run.get("returncode", -1)) != 0:
            raise R56Error(f"stream runtime not PASS: {wd}")
        if run.get("tree_sha256") != sha256_file(treep) or run.get("ancestry_result_sha256") != sha256_file(resp):
            raise R56Error(f"stream evidence hash mismatch: {wd}")
        if res.get("status") != "PASS_R56_ANCESTRY_RESULT":
            raise R56Error(f"ancestry result not PASS: {wd}")
        if int(res.get("seed", -1)) != int(s["seed"]) or str(res.get("variant")) != str(s["variant"]):
            raise R56Error(f"stream identity mismatch: {wd}")
        rows.append({"stream": s, "config": cfg, "result": res, "runtime": run})
    return rows


def _minmax(vals: Iterable[float]) -> list[float]:
    a = [float(v) for v in vals]
    if not a:
        raise R56Error("cannot compute minmax of empty values")
    return [float(min(a)), float(max(a))]


def analyze_ancestry_challenges(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R56Error(f"R5.6 parent authority failed: {auth['failed']}")
    out = root / OUT_REL
    plan = load_json(out / "R5_6_SLIM_EXECUTION_PLAN.json")
    runtime = load_json(out / "R5_6_SLIM_RUNTIME_IDENTITY.json")
    bridge = load_json(out / "R5_6_EXECUTION_BRIDGE.json")
    rows = _load_stream_results(root, plan)

    by_sched_variant: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        k = (str(row["stream"]["schedule_id"]), str(row["stream"]["variant"]))
        by_sched_variant.setdefault(k, []).append(row)
    schedule_summary: dict[str, Any] = {}
    for sched in plan.get("schedules") or []:
        sid = str(sched["schedule_id"])
        variants: dict[str, Any] = {}
        for variant in VARIANTS:
            rr = by_sched_variant.get((sid, variant), [])
            if len(rr) != len(SEEDS) or {int(x["stream"]["seed"]) for x in rr} != set(SEEDS):
                raise R56Error(f"seed/variant membership mismatch for {sid} {variant}")
            p1 = [float(x["result"]["p1_from_p2"]["donor_ancestry_fraction_mean"]) for x in rr]
            p2 = [float(x["result"]["p2_from_p1"]["donor_ancestry_fraction_mean"]) for x in rr]
            p1_any = [float(x["result"]["p1_from_p2"]["recipient_haplotype_with_any_donor_ancestry_fraction"]) for x in rr]
            p2_any = [float(x["result"]["p2_from_p1"]["recipient_haplotype_with_any_donor_ancestry_fraction"]) for x in rr]
            p1_tract = [float(x["result"]["p1_from_p2"]["donor_tract_length_mean_bp"]) for x in rr]
            p2_tract = [float(x["result"]["p2_from_p1"]["donor_tract_length_mean_bp"]) for x in rr]
            variants[variant] = {
                "migration_rate_engine_challenge": float(VARIANTS[variant]),
                "p1_from_p2_donor_ancestry_fraction_minmax": _minmax(p1),
                "p2_from_p1_donor_ancestry_fraction_minmax": _minmax(p2),
                "p1_haplotype_with_any_p2_ancestry_fraction_minmax": _minmax(p1_any),
                "p2_haplotype_with_any_p1_ancestry_fraction_minmax": _minmax(p2_any),
                "p1_donor_tract_mean_bp_minmax": _minmax(p1_tract),
                "p2_donor_tract_mean_bp_minmax": _minmax(p2_tract),
                "automatic_scientific_pass_fail_from_values": False,
            }
        schedule_summary[sid] = variants

    history = load_json(root / R55_HISTORY_REL)
    hist_by_pair = {str(r["pair_id"]): r for r in history.get("pair_records") or []}
    records: list[dict[str, Any]] = []
    for pair_id in sorted(plan.get("pair_to_schedule") or {}):
        sid = str(plan["pair_to_schedule"][pair_id])
        h = hist_by_pair[pair_id]
        records.append({
            "pair_id": pair_id,
            "family_a": h["family_a"],
            "family_b": h["family_b"],
            "schedule_id": sid,
            "active_contact_state_count": next(int(s["active_contact_state_count"]) for s in plan["schedules"] if s["schedule_id"] == sid),
            "r55_contact_history": {
                "exact_overlap_state_count": int(h["exact_overlap_state_count"]),
                "one_cell_contact_opportunity_state_count": int(h["one_cell_contact_opportunity_state_count"]),
                "contact_opportunity_windows_by_support_threshold": h["contact_opportunity_windows_by_support_threshold"],
            },
            "slim_standardized_ancestry_challenges": schedule_summary[sid],
            "same_schedule_results_reused_only_when_binary_contact_schedule_is_identical": True,
            "r55_contact_support_fraction_used_as_migration_magnitude": False,
            "simulated_ancestry_claimed_as_realized_historical_admixture": False,
            "single_history_winner_selected": False,
            "automatic_scientific_pass_fail_from_values": False,
        })

    sensitivity = {
        "stage": STAGE,
        "status": "R56_FIXED_ANCESTRY_ADMIXTURE_CHALLENGE_SENSITIVITY",
        "selection_semantics": "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL_NO_RESULT_SELECTED_TUNING",
        "pair_count": len(records),
        "schedule_class_count": int(plan["schedule_class_count"]),
        "record_count": len(records),
        "records": records,
    }
    write_json(out / "R5_6_ANCESTRY_ADMIXTURE_SENSITIVITY.json", sensitivity)

    # Runtime/model integrity checks are distinct from scientific values.
    noflow_rows = [r for r in rows if r["stream"]["variant"] == "NO_FLOW"]
    control_clean = all(
        abs(float(r["result"]["p1_from_p2"]["donor_ancestry_fraction_mean"])) <= 1e-12
        and abs(float(r["result"]["p2_from_p1"]["donor_ancestry_fraction_mean"])) <= 1e-12
        for r in noflow_rows
    )
    checks = {
        "parent_authority_pass": not auth["failed"],
        "runtime_status_pass": runtime.get("status") == "PASS_R56_SLIM_5_2_PINNED_RUNTIME_IDENTITY",
        "runtime_slim_version_exact": runtime.get("slim_version") == "5.2",
        "runtime_tskit_exact": runtime.get("tskit_version") == "1.0.3",
        "bridge_status_exact": bridge.get("status") == "R56_POWERSHELL_WSL_SLIM_EXECUTION_BRIDGE",
        "bridge_stream_count_exact": int(bridge.get("stream_count", -1)) == int(plan["planned_stream_count"]),
        "bridge_all_exit_zero": int(bridge.get("exit_zero_count", -1)) == int(plan["planned_stream_count"]),
        "plan_status_exact": plan.get("status") == "PASS_R56_SLIM_ANCESTRY_ADMIXTURE_CHALLENGE_PLAN_PREPARED",
        "pair_count_exact": int(plan.get("pair_count", -1)) == EXPECTED_PAIR_COUNT,
        "age_state_count_exact": int(plan.get("age_state_count", -1)) == EXPECTED_AGE_STATE_COUNT,
        "stream_count_exact": len(rows) == int(plan["planned_stream_count"]),
        "variant_set_exact": set(VARIANTS) == {str(v["name"]) for v in plan.get("variants") or []},
        "seed_set_exact": set(SEEDS) == set(int(x) for x in plan.get("seeds") or []),
        "control_no_flow_has_zero_cross_ancestry": control_clean,
        "all_results_bound_to_prepared_input_hashes": True,
        "r55_contact_support_fraction_not_used_as_migration_magnitude": plan.get("semantics", {}).get("r55_contact_support_fraction_used_as_migration_magnitude") is False,
        "r55_binary_contact_schedule_is_input_authority": plan.get("semantics", {}).get("r55_binary_contact_schedule_is_input_authority") is True,
        "slim_time_not_claimed_literal_arcana_generations": plan.get("semantics", {}).get("slim_ticks_are_standardized_computational_index_not_literal_arcana_generations") is True,
        "simulated_ancestry_not_promoted_to_realized_admixture": plan.get("semantics", {}).get("simulated_ancestry_is_not_promoted_to_realized_historical_admixture") is True,
        "no_majority_vote": plan.get("selection_rules", {}).get("majority_vote") is False,
        "no_result_selected_tuning": plan.get("selection_rules", {}).get("result_selected_tuning") is False,
        "no_single_pair_winner": plan.get("selection_rules", {}).get("single_pair_winner") is False,
        "no_single_admixture_history_winner": plan.get("selection_rules", {}).get("single_admixture_history_winner") is False,
        "no_automatic_numeric_scientific_pass_fail": plan.get("selection_rules", {}).get("automatic_numeric_scientific_pass_fail") is False,
        "engine_does_not_define_arcana_target": plan.get("selection_rules", {}).get("external_engine_defines_arcana_target") is False,
        "canonical_state_unchanged": True,
        "derived_refinement_not_promoted": True,
        "deep_biological_coupling_off": True,
    }
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    audit = {
        "stage": STAGE,
        "status": "PASS_R56_TARGETED_ANCESTRY_AND_ADMIXTURE_CHALLENGE_EVIDENCE_CANDIDATE" if not failed else "BLOCKED_R56_ANCESTRY_ADMIXTURE_EVIDENCE",
        "scientific_candidate_eligible": bool(not failed and not allow_non_scientific_dev_parent),
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "summary": {
            "pair_count": EXPECTED_PAIR_COUNT,
            "schedule_class_count": int(plan["schedule_class_count"]),
            "scientific_stream_count": len(rows),
            "variant_count": len(VARIANTS),
            "seed_count": len(SEEDS),
            "external_engine": "SLiM",
            "external_engine_version": "5.2",
            "new_external_engine_execution_performed": True,
            "tree_sequence_ancestry_analysis_performed": True,
            "numeric_admixture_truth_claimed": False,
            "realized_historical_admixture_claimed": False,
            "r55_contact_support_fraction_used_as_migration_magnitude": False,
            "result_selected_tuning": False,
            "majority_vote": False,
            "single_history_winner_selected": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
        },
        "recommended_next_action": "CONSOLIDATE_R53_R54_R55_R56_AS_ONE_LARGE_HOMINID_DEMOGRAPHY_GENE_FLOW_ANCESTRY_BLOCK_AND_SEAL_ONCE_IF_AUDIT_COMPLETE",
        "checks": checks,
    }
    write_json(out / "R5_6_INTEGRATED_AUDIT.json", audit)

    # Raw evidence manifest: trees, ancestry results and runtime bridges are all immutable inputs to audit.
    raw_files: dict[str, Any] = {}
    for row in rows:
        wd = root / Path(str(row["stream"]["work_dir"]))
        for name in ("ARCANA_R56.slim", "STREAM_CONFIG.json", "r56.trees", "ANCESTRY_RESULT.json", "STREAM_RUNTIME.json"):
            p = wd / name
            rel = str(p.relative_to(out)).replace("\\", "/")
            raw_files[rel] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    raw_manifest = {"stage": STAGE, "status": "R56_RAW_SLIM_TREE_SEQUENCE_EVIDENCE_MANIFEST", "file_count": len(raw_files), "files": raw_files}
    write_json(out / "R5_6_RAW_EVIDENCE_MANIFEST.json", raw_manifest)

    artifacts = [
        "R5_6_PARENT_CANDIDATE_BINDING.json",
        "R5_6_SLIM_RUNTIME_IDENTITY.json",
        "R5_6_SLIM_EXECUTION_PLAN.json",
        "R5_6_EXECUTION_BRIDGE.json",
        "R5_6_RAW_EVIDENCE_MANIFEST.json",
        "R5_6_ANCESTRY_ADMIXTURE_SENSITIVITY.json",
        "R5_6_INTEGRATED_AUDIT.json",
    ]
    files: dict[str, Any] = {}
    for name in artifacts:
        p = out / name
        files[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    write_json(out / "R5_6_OUTPUT_MANIFEST.json", {"stage": STAGE, "status": audit["status"], "files": files})
    return audit
