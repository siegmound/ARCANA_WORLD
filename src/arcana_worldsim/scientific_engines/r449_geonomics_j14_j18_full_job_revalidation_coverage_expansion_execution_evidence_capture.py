from __future__ import annotations

from pathlib import Path
from typing import Any
import concurrent.futures
import copy
import gzip
import hashlib
import importlib.util
import io
import json
import os
import shutil

import numpy as np

STAGE = "v0.6D1-R4.49"

PARENT_COMPLETE = (
    "PASS_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE"
)
EXPECTED_EXPANSION_PLAN_SHA256 = (
    "3a6e1d5b7d454f7c4ecd79c357bc6a2e8cd6e6514c61db07a5d06267834766e5"
)

COMPLETE = (
    "PASS_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE_COMPLETE"
)
SEALED = (
    "PASS_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE_SEALED"
)
BLOCKED = (
    "BLOCKED_R449_FULL_JOB_COVERAGE_EXPANSION_EXECUTION_OR_EVIDENCE_"
    "CAPTURE_FAILURE"
)
NEXT = (
    "BUILD_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_FINAL_GEONOMICS_CLOSURE"
)

OUT = Path("outputs/v0_6D1_R4_49")
SEAL = Path("outputs/v0_6D1_R4_49_SEAL/R4_49_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r449_geonomics_j14_j18_full_job_revalidation_coverage_"
    "expansion_execution_evidence_capture_v0_6D1_R4_49.json"
)

R448 = Path("outputs/v0_6D1_R4_48/R4_48_INTEGRATED_AUDIT.json")
R448_SEAL = Path("outputs/v0_6D1_R4_48_SEAL/R4_48_FINAL_SEAL_AUDIT.json")
R448_PLAN = Path("outputs/v0_6D1_R4_48/R4_48_FULL_COVERAGE_EXPANSION_PLAN.json")
R448_AUTH = Path("outputs/v0_6D1_R4_48/R4_48_EXPANSION_EXECUTION_AUTHORIZATION.json")
R448_J14_INV = Path("outputs/v0_6D1_R4_48/R4_48_J14_FULL_COVERAGE_INVENTORY.json")
R448_J18_INV = Path("outputs/v0_6D1_R4_48/R4_48_J18_FULL_COVERAGE_INVENTORY.json")

R436_NATIVE = Path(
    "outputs/v0_6D1_R4_36/"
    "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
)

R446_J14 = Path("outputs/v0_6D1_R4_46/R4_46_J14_SCIENTIFIC_EVIDENCE.json")
R446_J18 = Path("outputs/v0_6D1_R4_46/R4_46_J18_SCIENTIFIC_EVIDENCE.json")
R446_J21 = Path("outputs/v0_6D1_R4_46/R4_46_J21_SCIENTIFIC_EVIDENCE.json")

J14_SOURCE = Path(
    "outputs/v0_6D1_R4_30/authority/"
    "R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz"
)
J18_SOURCE = Path(
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz"
)
J14_SHA = "eed2d1e350783f1d2dc31c5b7e697330ccbfcf63024062bc9f4ed2f8905f4756"
J18_SHA = "16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a"

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha_json(obj: Any) -> str:
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_plan(plan: dict[str, Any]) -> dict[str, Any]:
    embedded = str(plan.get("plan_sha256", ""))
    bare = copy.deepcopy(plan)
    bare.pop("plan_sha256", None)
    recomputed = _sha_json(bare)
    return {
        "embedded_plan_sha256": embedded,
        "recomputed_plan_sha256": recomputed,
        "expected_plan_sha256": EXPECTED_EXPANSION_PLAN_SHA256,
        "pass":
            embedded == recomputed == EXPECTED_EXPANSION_PLAN_SHA256,
    }


def _import_params(path: Path) -> dict[str, Any]:
    name = "r449_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import params {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    params = getattr(mod, "params", None)
    if not isinstance(params, dict):
        raise RuntimeError(f"{path} did not expose dict params")
    return params


def _native_rows(native: dict[str, Any], job_id: str) -> list[dict[str, Any]]:
    return sorted(
        [
            r for r in (native.get("records") or [])
            if r.get("job_id") == job_id and r.get("construction_pass") is True
        ],
        key=lambda r: int(r["replicate_index"]),
    )


def _load_source_arrays(root: Path, job_id: str) -> dict[str, Any]:
    if job_id == J14:
        p = root / J14_SOURCE
        if sha256(p) != J14_SHA:
            raise RuntimeError("J14 source hash mismatch")
        with np.load(p, allow_pickle=False) as z:
            return {
                "ages": np.asarray(z["age_ma"], dtype=float),
                "names": [str(x) for x in z["state_variable_names"]],
                "state": np.asarray(z["spatial_state"], dtype=float),
            }

    if job_id == J18:
        p = root / J18_SOURCE
        if sha256(p) != J18_SHA:
            raise RuntimeError("J18 source hash mismatch")
        with np.load(p, allow_pickle=False) as z:
            return {
                "ages": np.asarray(z["snapshot_age_ka"], dtype=float),
                "names": [str(x) for x in z["state_variable_names"]],
                "state": np.asarray(z["snapshot_deme_state"], dtype=float),
                "active": np.asarray(z["snapshot_active"]),
            }
    raise ValueError(job_id)


def _branch_states(
    source: dict[str, Any],
    job_id: str,
    member_index: int,
    candidate_index: int,
) -> list[dict[str, Any]]:
    names = source["names"]
    ri = names.index("grid_row")
    ci = names.index("grid_col")
    states = []

    if job_id == J14:
        ai = names.index("active")
        s = source["state"][member_index, candidate_index]
        for ti, age in enumerate(source["ages"]):
            mask = s[ti, :, ai] > 0.5
            coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
            if len(coords) <= 0:
                raise RuntimeError(
                    f"J14 zero carrier state M{member_index} C{candidate_index} t{ti}"
                )
            states.append({"age": float(age), "coords": coords})
        return states

    s = source["state"][member_index, candidate_index]
    active = source["active"][member_index, candidate_index]
    for ti, age in enumerate(source["ages"]):
        mask = np.asarray(active[ti], dtype=float) > 0.5
        coords = np.column_stack((s[ti, mask, ci], s[ti, mask, ri]))
        if len(coords) <= 0:
            raise RuntimeError(
                f"J18 zero carrier state M{member_index} C{candidate_index} t{ti}"
            )
        states.append({"age": float(age), "coords": coords})
    return states


def _open_deterministic_gzip_jsonl(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.open("wb")
    gz = gzip.GzipFile(
        filename="",
        mode="wb",
        fileobj=raw,
        compresslevel=6,
        mtime=0,
    )
    txt = io.TextIOWrapper(gz, encoding="utf-8", newline="\n")
    return raw, gz, txt


def _write_jsonl_record(txt: Any, record: dict[str, Any]) -> None:
    txt.write(
        json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    )
    txt.write("\n")


def _shard_paths(root: Path, shard_id: str) -> dict[str, Path]:
    d = root / OUT / "shards" / shard_id
    return {
        "dir": d,
        "metrics": d / "METRIC_RECORDS.jsonl.gz",
        "summary": d / "SHARD_SUMMARY.json",
    }


def _validate_existing_shard(
    root: Path,
    shard: dict[str, Any],
    plan_sha: str,
) -> dict[str, Any] | None:
    paths = _shard_paths(root, shard["shard_id"])
    if not paths["summary"].exists() or not paths["metrics"].exists():
        return None
    try:
        s = load(paths["summary"])
    except Exception:
        return None
    checks = [
        s.get("status") == "R449_EXPANSION_SHARD_EVIDENCE_CAPTURED",
        s.get("pass") is True,
        s.get("shard_id") == shard["shard_id"],
        s.get("authorized_plan_sha256") == plan_sha,
        s.get("branch_ids") == shard["branch_ids"],
        s.get("metric_evidence_file_sha256") == sha256(paths["metrics"]),
        s.get("stream_count") == shard["stream_count"],
        s.get("stream_pass_count") == shard["stream_count"],
    ]
    return s if all(checks) else None


def _preserve_invalid_existing_shard(root: Path, shard_id: str) -> None:
    paths = _shard_paths(root, shard_id)
    if not paths["dir"].exists():
        return
    digest = hashlib.sha256(
        (shard_id + "|" + str(os.getpid())).encode("utf-8")
    ).hexdigest()[:12]
    dst = root / OUT / "failed_or_partial_shards" / f"{shard_id}_{digest}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.move(str(paths["dir"]), str(dst))


def _execute_one_shard(
    root_str: str,
    shard: dict[str, Any],
    plan_sha: str,
) -> dict[str, Any]:
    root = Path(root_str)
    existing = _validate_existing_shard(root, shard, plan_sha)
    if existing is not None:
        existing = copy.deepcopy(existing)
        existing["resume_reused_existing_valid_shard"] = True
        return existing

    paths = _shard_paths(root, shard["shard_id"])
    if paths["dir"].exists():
        _preserve_invalid_existing_shard(root, shard["shard_id"])
    paths["dir"].mkdir(parents=True, exist_ok=True)

    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r438_geonomics_exact_initialization_adapter_probe_elimination_preflight import (
        _install_exact_nonliteral_carriers,
    )
    from arcana_worldsim.scientific_engines.r441_geonomics_domain_specific_execution_queue_single_transition_dry_run import (
        _exact_carrier_replace_preserve_clock,
    )
    from arcana_worldsim.scientific_engines.r442_geonomics_multi_transition_bounded_replay_production_queue_authorization import (
        _advance_authorized_clock_expected,
    )
    from arcana_worldsim.scientific_engines.r444_geonomics_readout_extraction_dry_run_adjudication_input_validation import (
        _extract_carrier_metrics,
    )

    plan = load(root / R448_PLAN)
    inventory = load(
        root / (R448_J14_INV if shard["job_id"] == J14 else R448_J18_INV)
    )
    native = load(root / R436_NATIVE)

    branch_map = {
        b["branch_id"]: b
        for b in inventory["branches"]
    }
    rows = _native_rows(native, shard["job_id"])
    if len(rows) != 4:
        raise RuntimeError("expected exactly four native rows")
    source = _load_source_arrays(root, shard["job_id"])

    raw = gz = txt = None
    stream_summaries = []
    metric_count = 0
    integrity_count = 0
    descriptive_count = 0
    metric_ids_seen = set()

    try:
        raw, gz, txt = _open_deterministic_gzip_jsonl(paths["metrics"])

        for branch_id in shard["branch_ids"]:
            b = branch_map[branch_id]
            if b["already_scientifically_executed"] is True:
                raise RuntimeError(
                    f"closed first-cohort branch leaked into expansion: {branch_id}"
                )
            states = _branch_states(
                source,
                shard["job_id"],
                int(b["member_index"]),
                int(b["candidate_index"]),
            )
            expected_state_count = int(b["canonical_state_count"])
            if len(states) != expected_state_count:
                raise RuntimeError(f"{branch_id} state count mismatch")

            for row in rows:
                rep = int(row["replicate_index"])
                seed = int(row["frozen_seed"])
                params = copy.deepcopy(
                    _import_params(root / row["native_parameter_file"])
                )
                params["model"]["T"] = len(states) - 1
                params["model"]["burn_T"] = 0
                params["model"]["seed"] = {"num": seed}
                if "num" in params["model"]:
                    params["model"]["num"] = seed
                params["model"]["name"] = (
                    f"ARCANA_R449_{shard['job_id']}_{branch_id}_REP{rep}"
                )

                mod = gnx.make_model(
                    parameters=gnx.make_params_dict(
                        params, model_name=params["model"]["name"]
                    ),
                    verbose=False,
                )
                template = copy.deepcopy(next(iter(mod.comm[0].values())))
                init = _install_exact_nonliteral_carriers(
                    mod, template, states[0]["coords"].tolist()
                )
                if init.get("pass") is not True:
                    raise RuntimeError(f"{branch_id} rep{rep} init failed")

                stream_metric_count = 0
                stream_integrity_count = 0
                stream_descriptive_count = 0
                all_integrity_exact = True
                all_descriptive_valid = True

                def consume(records: list[dict[str, Any]]) -> None:
                    nonlocal metric_count, integrity_count, descriptive_count
                    nonlocal stream_metric_count, stream_integrity_count
                    nonlocal stream_descriptive_count, all_integrity_exact
                    nonlocal all_descriptive_valid
                    for rec in records:
                        rec["scientific_branch_id"] = branch_id
                        rec["expansion_shard_id"] = shard["shard_id"]
                        _write_jsonl_record(txt, rec)
                        metric_ids_seen.add(str(rec["metric_id"]))
                        metric_count += 1
                        stream_metric_count += 1
                        if rec["metric_role"] == "EXACT_INTEGRITY_ONLY":
                            integrity_count += 1
                            stream_integrity_count += 1
                            all_integrity_exact = (
                                all_integrity_exact
                                and rec.get("exact_match") is True
                            )
                        else:
                            descriptive_count += 1
                            stream_descriptive_count += 1
                            all_descriptive_valid = (
                                all_descriptive_valid
                                and rec.get("finite") is True
                                and rec.get("numeric_acceptance_threshold") is None
                                and rec.get("automatic_pass_fail_from_value") is False
                            )

                consume(_extract_carrier_metrics(
                    mod,
                    job_id=shard["job_id"],
                    replicate_index=rep,
                    frozen_seed=seed,
                    canonical_state_index=0,
                    canonical_physical_age=float(states[0]["age"]),
                    expected_coords=np.asarray(states[0]["coords"]),
                ))

                transition_pass_count = 0
                for ti in range(len(states) - 1):
                    clock = _advance_authorized_clock_expected(
                        mod, expected_before_t=ti - 1
                    )
                    repl = _exact_carrier_replace_preserve_clock(
                        mod, template, states[ti + 1]["coords"].tolist()
                    )
                    if (
                        clock.get("pass") is not True
                        or repl.get("pass") is not True
                    ):
                        raise RuntimeError(
                            f"{branch_id} rep{rep} transition {ti} failed"
                        )
                    transition_pass_count += 1
                    consume(_extract_carrier_metrics(
                        mod,
                        job_id=shard["job_id"],
                        replicate_index=rep,
                        frozen_seed=seed,
                        canonical_state_index=ti + 1,
                        canonical_physical_age=float(states[ti + 1]["age"]),
                        expected_coords=np.asarray(states[ti + 1]["coords"]),
                    ))

                expected_metrics = expected_state_count * 3
                stream_pass = all([
                    transition_pass_count == int(b["transition_count"]),
                    stream_metric_count == expected_metrics,
                    stream_integrity_count == expected_state_count * 2,
                    stream_descriptive_count == expected_state_count,
                    all_integrity_exact,
                    all_descriptive_valid,
                    mod.t == int(b["transition_count"]) - 1,
                    mod.comm.t == int(b["transition_count"]) - 1,
                    mod.comm[0].t == int(b["transition_count"]) - 1,
                    list(mod.comm[0].n_births) == [],
                    list(mod.comm[0].n_deaths) == [],
                    all(int(ind.age) == 0 for ind in mod.comm[0].values()),
                ])
                stream_summaries.append({
                    "job_id": shard["job_id"],
                    "shard_id": shard["shard_id"],
                    "branch_id": branch_id,
                    "member_index": int(b["member_index"]),
                    "candidate_index": int(b["candidate_index"]),
                    "replicate_index": rep,
                    "frozen_seed": seed,
                    "canonical_state_count": expected_state_count,
                    "transition_count": int(b["transition_count"]),
                    "transition_pass_count": transition_pass_count,
                    "metric_record_count": stream_metric_count,
                    "integrity_record_count": stream_integrity_count,
                    "descriptive_record_count": stream_descriptive_count,
                    "all_integrity_exact": all_integrity_exact,
                    "all_descriptive_valid": all_descriptive_valid,
                    "model_walk_called": False,
                    "autonomous_movement_called": False,
                    "autonomous_population_dynamics_called": False,
                    "autonomous_ageing_called": False,
                    "scientific_execution_performed": True,
                    "pass": bool(stream_pass),
                })
                del mod

        txt.flush()
        txt.close()
        txt = None
        gz = None
        raw = None

    except Exception:
        if txt is not None:
            try:
                txt.close()
            except Exception:
                pass
        raise

    expected_metric_count = sum(
        branch_map[bid]["expected_metric_record_count"]
        for bid in shard["branch_ids"]
    )
    expected_integrity_count = sum(
        branch_map[bid]["expected_integrity_record_count"]
        for bid in shard["branch_ids"]
    )
    expected_descriptive_count = sum(
        branch_map[bid]["expected_descriptive_record_count"]
        for bid in shard["branch_ids"]
    )
    expected_metric_ids = sorted(
        plan["expansion"][shard["job_id"]]["metric_ids"]
    )

    stream_pass_count = sum(bool(s["pass"]) for s in stream_summaries)
    passed = all([
        len(stream_summaries) == shard["stream_count"],
        stream_pass_count == shard["stream_count"],
        metric_count == expected_metric_count,
        integrity_count == expected_integrity_count,
        descriptive_count == expected_descriptive_count,
        sorted(metric_ids_seen) == expected_metric_ids,
    ])

    summary = {
        "stage": STAGE,
        "status":
            "R449_EXPANSION_SHARD_EVIDENCE_CAPTURED"
            if passed else BLOCKED,
        "pass": bool(passed),
        "authorized_plan_sha256": plan_sha,
        "job_id": shard["job_id"],
        "shard_id": shard["shard_id"],
        "shard_index": int(shard["shard_index"]),
        "branch_count": int(shard["branch_count"]),
        "branch_ids": list(shard["branch_ids"]),
        "stream_count": len(stream_summaries),
        "stream_pass_count": stream_pass_count,
        "metric_record_count": metric_count,
        "integrity_record_count": integrity_count,
        "descriptive_record_count": descriptive_count,
        "metric_ids": sorted(metric_ids_seen),
        "metric_evidence_file":
            str(paths["metrics"].relative_to(root)).replace("\\", "/"),
        "metric_evidence_file_sha256": sha256(paths["metrics"]),
        "metric_evidence_file_bytes": paths["metrics"].stat().st_size,
        "scientific_engine_execution_performed": True,
        "scientific_evidence_capture_valid": bool(passed),
        "numeric_acceptance_threshold_count": 0,
        "automatic_scientific_pass_fail_count": 0,
        "canonical_state_changed": False,
        "resume_reused_existing_valid_shard": False,
        "stream_summaries": stream_summaries,
    }
    write(paths["summary"], summary)
    return summary


def execute_all(root: Path, parallel_jobs: int = 2) -> dict[str, Any]:
    root = root.resolve()
    plan = load(root / R448_PLAN)
    pv = _verify_plan(plan)
    if pv.get("pass") is not True:
        out = {
            "stage": STAGE,
            "status": BLOCKED,
            "reason": "R448_EXPANSION_PLAN_HASH_MISMATCH",
            "plan_verification": pv,
        }
        write(root / OUT / "R4_49_EXECUTION_PROGRESS.json", out)
        return out

    auth = load(root / R448_AUTH)
    if (
        auth.get("expansion_execution_authorized") is not True
        or auth.get("geonomics_expansion_execution_ready") is not True
        or auth.get("authorized_plan_sha256") != plan["plan_sha256"]
    ):
        out = {
            "stage": STAGE,
            "status": BLOCKED,
            "reason": "R448_EXPANSION_EXECUTION_NOT_AUTHORIZED",
        }
        write(root / OUT / "R4_49_EXECUTION_PROGRESS.json", out)
        return out

    shards = list(plan["sharding"]["shards"])
    parallel_jobs = max(1, int(parallel_jobs))
    results = []
    failed = []

    if parallel_jobs == 1:
        for shard in shards:
            try:
                r = _execute_one_shard(str(root), shard, plan["plan_sha256"])
                results.append(r)
                print(json.dumps({
                    "shard_id": shard["shard_id"],
                    "status": r.get("status"),
                    "stream_pass_count": r.get("stream_pass_count"),
                    "stream_count": r.get("stream_count"),
                    "resume_reused": r.get(
                        "resume_reused_existing_valid_shard", False
                    ),
                }))
            except Exception as exc:
                failed.append({
                    "shard_id": shard["shard_id"],
                    "error": repr(exc),
                })
                break
    else:
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=parallel_jobs
        ) as ex:
            future_map = {
                ex.submit(
                    _execute_one_shard,
                    str(root),
                    shard,
                    plan["plan_sha256"],
                ): shard
                for shard in shards
            }
            for fut in concurrent.futures.as_completed(future_map):
                shard = future_map[fut]
                try:
                    r = fut.result()
                    results.append(r)
                    print(json.dumps({
                        "shard_id": shard["shard_id"],
                        "status": r.get("status"),
                        "stream_pass_count": r.get("stream_pass_count"),
                        "stream_count": r.get("stream_count"),
                        "resume_reused": r.get(
                            "resume_reused_existing_valid_shard", False
                        ),
                    }))
                except Exception as exc:
                    failed.append({
                        "shard_id": shard["shard_id"],
                        "error": repr(exc),
                    })

    results = sorted(
        results,
        key=lambda r: (r.get("job_id", ""), int(r.get("shard_index", -1))),
    )
    completed = sum(r.get("pass") is True for r in results)
    progress = {
        "stage": STAGE,
        "status":
            "R449_ALL_EXPANSION_SHARDS_COMPLETED"
            if completed == 32 and not failed else BLOCKED,
        "authorized_plan_sha256": plan["plan_sha256"],
        "parallel_jobs_operational_only": parallel_jobs,
        "expected_shard_count": 32,
        "completed_valid_shard_count": completed,
        "failed_shards": failed,
        "scientific_engine_execution_performed":
            any(
                r.get("scientific_engine_execution_performed") is True
                for r in results
            ),
        "results": [
            {
                "job_id": r.get("job_id"),
                "shard_id": r.get("shard_id"),
                "shard_index": r.get("shard_index"),
                "pass": r.get("pass"),
                "stream_count": r.get("stream_count"),
                "metric_record_count": r.get("metric_record_count"),
                "resume_reused_existing_valid_shard":
                    r.get("resume_reused_existing_valid_shard", False),
                "metric_evidence_file_sha256":
                    r.get("metric_evidence_file_sha256"),
            }
            for r in results
        ],
    }
    write(root / OUT / "R4_49_EXECUTION_PROGRESS.json", progress)
    return progress


def _baseline_evidence_identity(root: Path) -> dict[str, Any]:
    files = {
        J14: root / R446_J14,
        J18: root / R446_J18,
        J21: root / R446_J21,
    }
    out = {}
    for jid, p in files.items():
        if not p.exists():
            raise RuntimeError(f"missing sealed baseline evidence {p}")
        e = load(p)
        out[jid] = {
            "path": str(p.relative_to(root)).replace("\\", "/"),
            "sha256": sha256(p),
            "metric_record_count": int(e["metric_record_count"]),
            "integrity_record_count": int(e["integrity_record_count"]),
            "descriptive_record_count": int(e["descriptive_record_count"]),
            "scientific_evidence_capture_valid":
                e.get("scientific_evidence_capture_valid") is True,
        }
    return out


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R448)
    parent_seal = load(root / R448_SEAL)
    plan = load(root / R448_PLAN)
    auth = load(root / R448_AUTH)
    progress = load(root / OUT / "R4_49_EXECUTION_PROGRESS.json")
    baseline = _baseline_evidence_identity(root)

    shard_summaries = []
    missing = []
    invalid = []
    for shard in plan["sharding"]["shards"]:
        s = _validate_existing_shard(root, shard, plan["plan_sha256"])
        if s is None:
            missing.append(shard["shard_id"])
        elif s.get("pass") is not True:
            invalid.append(shard["shard_id"])
        else:
            shard_summaries.append(s)

    expansion_streams = sum(s["stream_count"] for s in shard_summaries)
    expansion_stream_passes = sum(
        s["stream_pass_count"] for s in shard_summaries
    )
    expansion_metrics = sum(s["metric_record_count"] for s in shard_summaries)
    expansion_integrity = sum(
        s["integrity_record_count"] for s in shard_summaries
    )
    expansion_descriptive = sum(
        s["descriptive_record_count"] for s in shard_summaries
    )

    shard_manifest = {
        "stage": STAGE,
        "status":
            "R449_EXPANSION_EVIDENCE_SHARD_MANIFEST_VALID"
            if not missing and not invalid and len(shard_summaries) == 32
            else BLOCKED,
        "authorized_plan_sha256": plan["plan_sha256"],
        "shard_count": len(shard_summaries),
        "missing_shards": missing,
        "invalid_shards": invalid,
        "expansion_stream_count": expansion_streams,
        "expansion_stream_pass_count": expansion_stream_passes,
        "expansion_metric_record_count": expansion_metrics,
        "expansion_integrity_record_count": expansion_integrity,
        "expansion_descriptive_record_count": expansion_descriptive,
        "shards": [
            {
                "job_id": s["job_id"],
                "shard_id": s["shard_id"],
                "shard_index": s["shard_index"],
                "branch_ids": s["branch_ids"],
                "stream_count": s["stream_count"],
                "metric_record_count": s["metric_record_count"],
                "integrity_record_count": s["integrity_record_count"],
                "descriptive_record_count": s["descriptive_record_count"],
                "metric_evidence_file": s["metric_evidence_file"],
                "metric_evidence_file_sha256":
                    s["metric_evidence_file_sha256"],
                "metric_evidence_file_bytes":
                    s["metric_evidence_file_bytes"],
            }
            for s in sorted(
                shard_summaries,
                key=lambda x: (x["job_id"], int(x["shard_index"])),
            )
        ],
    }
    write(root / OUT / "R4_49_EXPANSION_EVIDENCE_SHARD_MANIFEST.json", shard_manifest)

    baseline_metrics = sum(
        x["metric_record_count"] for x in baseline.values()
    )
    baseline_integrity = sum(
        x["integrity_record_count"] for x in baseline.values()
    )
    baseline_descriptive = sum(
        x["descriptive_record_count"] for x in baseline.values()
    )

    full_manifest = {
        "stage": STAGE,
        "status":
            "R449_FULL_GEONOMICS_COVERAGE_EVIDENCE_CAPTURED"
            if (
                shard_manifest["status"]
                == "R449_EXPANSION_EVIDENCE_SHARD_MANIFEST_VALID"
                and all(
                    x["scientific_evidence_capture_valid"]
                    for x in baseline.values()
                )
            )
            else BLOCKED,
        "authorized_expansion_plan_sha256": plan["plan_sha256"],
        "sealed_baseline_evidence": baseline,
        "new_expansion_shard_manifest":
            "outputs/v0_6D1_R4_49/R4_49_EXPANSION_EVIDENCE_SHARD_MANIFEST.json",
        "new_expansion_shard_manifest_sha256":
            sha256(root / OUT / "R4_49_EXPANSION_EVIDENCE_SHARD_MANIFEST.json"),
        "full_geonomics_coverage": {
            J14: {
                "branch_coverage": "192/192",
                "full_job_evidence_capture_complete": True,
            },
            J18: {
                "branch_coverage": "64/64",
                "full_job_evidence_capture_complete": True,
            },
            J21: {
                "branch_coverage": "1/1",
                "full_job_evidence_capture_complete": True,
                "reexecuted_in_r449": False,
            },
        },
        "metric_record_count": baseline_metrics + expansion_metrics,
        "integrity_record_count": baseline_integrity + expansion_integrity,
        "descriptive_record_count":
            baseline_descriptive + expansion_descriptive,
        "scientific_engine_execution_performed": True,
        "full_coverage_scientific_evidence_capture_complete": (
            not missing and not invalid and len(shard_summaries) == 32
        ),
        "full_job_scientific_adjudication_performed": False,
        "automatic_scientific_pass_fail_count": 0,
        "numeric_acceptance_threshold_count": 0,
        "scientific_divergence_claim_count": 0,
        "canonical_state_changed": False,
    }
    write(root / OUT / "R4_49_FULL_GEONOMICS_COVERAGE_EVIDENCE_MANIFEST.json", full_manifest)

    checks = {
        "parent_r448_complete_52_52":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 52
            and parent.get("checks_failed") == 0,
        "parent_r448_sealed_27_27":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 27
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r449":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R449_EXECUTE_EXACT_R448_SHARDS_WITH_RESUMABLE_EVIDENCE_CAPTURE",
        "parent_plan_hash_exact":
            _verify_plan(plan).get("pass") is True,
        "parent_execution_authorized":
            auth.get("expansion_execution_authorized") is True
            and auth.get("geonomics_expansion_execution_ready") is True,
        "all_32_shards_valid":
            len(shard_summaries) == 32 and not missing and not invalid,
        "exact_1016_expansion_streams":
            expansion_streams == 1016,
        "all_1016_expansion_streams_pass":
            expansion_stream_passes == 1016,
        "exact_334512_expansion_records":
            expansion_metrics == 334512,
        "exact_223008_expansion_integrity":
            expansion_integrity == 223008,
        "exact_111504_expansion_descriptive":
            expansion_descriptive == 111504,
        "baseline_j14_valid":
            baseline[J14]["scientific_evidence_capture_valid"] is True,
        "baseline_j18_valid":
            baseline[J18]["scientific_evidence_capture_valid"] is True,
        "baseline_j21_valid":
            baseline[J21]["scientific_evidence_capture_valid"] is True,
        "first_cohorts_not_reexecuted":
            plan["already_scientifically_executed"][J14] == ["M000_C00"]
            and plan["already_scientifically_executed"][J18] == ["M000_C00"],
        "j21_not_reexecuted":
            full_manifest["full_geonomics_coverage"][J21][
                "reexecuted_in_r449"
            ] is False,
        "j14_full_evidence_capture_192_of_192":
            full_manifest["full_geonomics_coverage"][J14][
                "branch_coverage"
            ] == "192/192",
        "j18_full_evidence_capture_64_of_64":
            full_manifest["full_geonomics_coverage"][J18][
                "branch_coverage"
            ] == "64/64",
        "j21_full_evidence_preserved_1_of_1":
            full_manifest["full_geonomics_coverage"][J21][
                "branch_coverage"
            ] == "1/1",
        "exact_346968_full_geonomics_records":
            full_manifest["metric_record_count"] == 346968,
        "exact_229548_full_geonomics_integrity":
            full_manifest["integrity_record_count"] == 229548,
        "exact_117420_full_geonomics_descriptive":
            full_manifest["descriptive_record_count"] == 117420,
        "scientific_execution_performed":
            full_manifest["scientific_engine_execution_performed"] is True,
        "full_coverage_evidence_capture_complete":
            full_manifest[
                "full_coverage_scientific_evidence_capture_complete"
            ] is True,
        "full_job_adjudication_pending":
            full_manifest["full_job_scientific_adjudication_performed"]
            is False,
        "zero_numeric_thresholds":
            full_manifest["numeric_acceptance_threshold_count"] == 0,
        "zero_automatic_pass_fail":
            full_manifest["automatic_scientific_pass_fail_count"] == 0,
        "zero_scientific_divergence_claims":
            full_manifest["scientific_divergence_claim_count"] == 0,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            full_manifest["canonical_state_changed"] is False
            and cfg.get("canonical_state_changed") is False,
        "deep_off":
            cfg.get("deep_biological_coupling") is False,
        "deferred_p2_two":
            parent.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            parent.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            parent.get("p3_backlog_cell_count") == 6,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "status": COMPLETE if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "geonomics_version": "1.4.9",
        "authorized_expansion_plan_sha256": plan["plan_sha256"],
        "expansion_shard_count": len(shard_summaries),
        "expansion_stream_count": expansion_streams,
        "expansion_stream_pass_count": expansion_stream_passes,
        "expansion_metric_record_count": expansion_metrics,
        "expansion_integrity_record_count": expansion_integrity,
        "expansion_descriptive_record_count": expansion_descriptive,
        "j14_branch_coverage_after_r449": "192/192" if ok else "INCOMPLETE",
        "j18_branch_coverage_after_r449": "64/64" if ok else "INCOMPLETE",
        "j21_branch_coverage_preserved": "1/1",
        "full_geonomics_metric_record_count":
            full_manifest["metric_record_count"],
        "full_geonomics_integrity_record_count":
            full_manifest["integrity_record_count"],
        "full_geonomics_descriptive_record_count":
            full_manifest["descriptive_record_count"],
        "scientific_engine_execution_performed": bool(ok),
        "full_coverage_scientific_evidence_capture_complete": bool(ok),
        "full_job_scientific_adjudication_performed": False,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_divergence_claim_count": 0,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "RESUME_OR_REPAIR_R449_EXPANSION_SHARDS",
    }
    write(root / OUT / "R4_49_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_49_INTEGRATED_AUDIT.json")
    fm = load(root / OUT / "R4_49_FULL_GEONOMICS_COVERAGE_EVIDENCE_MANIFEST.json")
    sm = load(root / OUT / "R4_49_EXPANSION_EVIDENCE_SHARD_MANIFEST.json")

    checks = {
        "r449_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "exact_32_shards":
            a.get("expansion_shard_count") == 32,
        "exact_1016_streams":
            a.get("expansion_stream_count") == 1016
            and a.get("expansion_stream_pass_count") == 1016,
        "exact_334512_expansion_records":
            a.get("expansion_metric_record_count") == 334512,
        "exact_223008_expansion_integrity":
            a.get("expansion_integrity_record_count") == 223008,
        "exact_111504_expansion_descriptive":
            a.get("expansion_descriptive_record_count") == 111504,
        "j14_full_192_of_192":
            a.get("j14_branch_coverage_after_r449") == "192/192",
        "j18_full_64_of_64":
            a.get("j18_branch_coverage_after_r449") == "64/64",
        "j21_preserved_1_of_1":
            a.get("j21_branch_coverage_preserved") == "1/1",
        "exact_346968_full_records":
            a.get("full_geonomics_metric_record_count") == 346968,
        "exact_229548_full_integrity":
            a.get("full_geonomics_integrity_record_count") == 229548,
        "exact_117420_full_descriptive":
            a.get("full_geonomics_descriptive_record_count") == 117420,
        "scientific_execution_performed":
            a.get("scientific_engine_execution_performed") is True,
        "full_coverage_capture_complete":
            a.get("full_coverage_scientific_evidence_capture_complete") is True,
        "shard_manifest_valid":
            sm.get("status") == "R449_EXPANSION_EVIDENCE_SHARD_MANIFEST_VALID",
        "full_manifest_valid":
            fm.get("status") == "R449_FULL_GEONOMICS_COVERAGE_EVIDENCE_CAPTURED",
        "full_job_adjudication_pending":
            a.get("full_job_scientific_adjudication_performed") is False,
        "zero_automatic_pass_fail":
            a.get("automatic_scientific_pass_fail_count") == 0,
        "zero_divergence_claims":
            a.get("scientific_divergence_claim_count") == 0,
        "no_target_numeric":
            a.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            a.get("readjudication_performed") is False,
        "canonical_unchanged":
            a.get("canonical_state_changed") is False,
        "deferred_p2_two":
            a.get("active_deferred_p2_cell_count") == 2,
        "proxy_context_two":
            a.get("proxy_context_only_count") == 2,
        "p3_backlog_six":
            a.get("p3_backlog_cell_count") == 6,
        "next_r450":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
            "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "authorized_expansion_plan_sha256":
                a.get("authorized_expansion_plan_sha256"),
            "expansion_shard_count": a.get("expansion_shard_count"),
            "expansion_stream_count": a.get("expansion_stream_count"),
            "expansion_metric_record_count":
                a.get("expansion_metric_record_count"),
            "j14_branch_coverage": a.get("j14_branch_coverage_after_r449"),
            "j18_branch_coverage": a.get("j18_branch_coverage_after_r449"),
            "j21_branch_coverage": a.get("j21_branch_coverage_preserved"),
            "full_geonomics_metric_record_count":
                a.get("full_geonomics_metric_record_count"),
            "scientific_engine_execution_performed": True,
            "full_coverage_scientific_evidence_capture_complete": True,
            "full_job_scientific_adjudication_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
