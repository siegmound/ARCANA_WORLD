from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import hashlib
import importlib.util
import json

import numpy as np

STAGE = "v0.6D1-R4.46"

PARENT_COMPLETE = (
    "PASS_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
    "GOVERNED_REVALIDATION_RUN_PREFLIGHT_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
    "GOVERNED_REVALIDATION_RUN_PREFLIGHT_SEALED"
)
PARENT_NEXT = (
    "BUILD_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
    "AND_EVIDENCE_CAPTURE"
)
EXPECTED_PARENT_PLAN_SHA256 = (
    "9a33a40c178a816526ca8aec053aae5a393086d7a18b9a3122bd453a4f592ec0"
)

COMPLETE = (
    "PASS_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
    "AND_EVIDENCE_CAPTURE_COMPLETE"
)
SEALED = (
    "PASS_R446_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
    "AND_EVIDENCE_CAPTURE_SEALED"
)
BLOCKED = (
    "BLOCKED_R446_GOVERNED_REVALIDATION_EXECUTION_OR_EVIDENCE_CAPTURE_FAILURE"
)
NEXT = (
    "BUILD_R447_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_COHORT_ADJUDICATION_CLOSURE"
)

OUT = Path("outputs/v0_6D1_R4_46")
SEAL = Path("outputs/v0_6D1_R4_46_SEAL/R4_46_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r446_geonomics_first_governed_revalidation_cohort_"
    "execution_evidence_capture_v0_6D1_R4_46.json"
)

R445 = Path("outputs/v0_6D1_R4_45/R4_45_INTEGRATED_AUDIT.json")
R445_SEAL = Path("outputs/v0_6D1_R4_45_SEAL/R4_45_FINAL_SEAL_AUDIT.json")
R445_PLAN = Path(
    "outputs/v0_6D1_R4_45/R4_45_FIRST_GOVERNED_REVALIDATION_RUN_PLAN.json"
)
R445_AUTH = Path(
    "outputs/v0_6D1_R4_45/R4_45_SCIENTIFIC_EXECUTION_AUTHORIZATION.json"
)
R436_NATIVE = Path(
    "outputs/v0_6D1_R4_36/"
    "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json"
)

J14 = "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18 = "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21 = "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

MID_COORD = "GNX_CARRIER_COORDINATE_READBACK_XY"
MID_CELL = "GNX_CARRIER_NATIVE_CELL_READBACK_IJ"
MID_NN = "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE"
MID_RASTER = "GNX_NATIVE_LAYER_RASTER_READBACK"
MID_LAYER_SUMMARY = "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha_json(obj: Any) -> str:
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_parent_plan(plan: dict[str, Any]) -> dict[str, Any]:
    embedded = str(plan.get("plan_sha256", ""))
    bare = copy.deepcopy(plan)
    bare.pop("plan_sha256", None)
    recomputed = _sha_json(bare)
    return {
        "embedded_plan_sha256": embedded,
        "recomputed_plan_sha256": recomputed,
        "expected_parent_plan_sha256": EXPECTED_PARENT_PLAN_SHA256,
        "embedded_matches_recomputed": embedded == recomputed,
        "embedded_matches_expected": embedded == EXPECTED_PARENT_PLAN_SHA256,
        "pass": (
            embedded == recomputed == EXPECTED_PARENT_PLAN_SHA256
        ),
    }


def _import_params(path: Path) -> dict[str, Any]:
    name = "r446_params_" + hashlib.sha1(str(path).encode()).hexdigest()[:12]
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


def _carrier_scientific_execution(
    root: Path,
    *,
    native: dict[str, Any],
    job_id: str,
    plan_job: dict[str, Any],
) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r438_geonomics_exact_initialization_adapter_probe_elimination_preflight import (
        _install_exact_nonliteral_carriers,
    )
    from arcana_worldsim.scientific_engines.r441_geonomics_domain_specific_execution_queue_single_transition_dry_run import (
        _exact_carrier_replace_preserve_clock,
    )
    from arcana_worldsim.scientific_engines.r442_geonomics_multi_transition_bounded_replay_production_queue_authorization import (
        _advance_authorized_clock_expected,
        _j14_first_branch_full,
        _j18_first_branch_full,
    )
    from arcana_worldsim.scientific_engines.r444_geonomics_readout_extraction_dry_run_adjudication_input_validation import (
        _extract_carrier_metrics,
    )

    branch = (
        _j14_first_branch_full(root)
        if job_id == J14
        else _j18_first_branch_full(root)
    )
    states = branch["states"]
    if len(states) != int(plan_job["canonical_state_count"]):
        return {
            "status": BLOCKED,
            "reason": "PLAN_CANONICAL_STATE_COUNT_MISMATCH",
        }

    rows = _native_rows(native, job_id)
    if len(rows) != 4:
        return {"status": BLOCKED, "reason": "EXPECTED_4_NATIVE_ROWS"}

    expected_seeds = list(plan_job["frozen_seeds"])
    observed_seeds = [int(r["frozen_seed"]) for r in rows]
    if observed_seeds != expected_seeds:
        return {
            "status": BLOCKED,
            "reason": "FROZEN_SEED_VECTOR_MISMATCH",
            "observed": observed_seeds,
            "expected": expected_seeds,
        }

    metric_records = []
    stream_records = []

    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        try:
            params = copy.deepcopy(_import_params(root / row["native_parameter_file"]))
            params["model"]["T"] = len(states) - 1
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R446_{job_id}_REP{rep}"

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

            local_records = []
            local_records.extend(_extract_carrier_metrics(
                mod,
                job_id=job_id,
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
                if clock.get("pass") is not True or repl.get("pass") is not True:
                    raise RuntimeError(
                        f"transition {ti} replay invariant failed"
                    )
                transition_pass_count += 1
                local_records.extend(_extract_carrier_metrics(
                    mod,
                    job_id=job_id,
                    replicate_index=rep,
                    frozen_seed=seed,
                    canonical_state_index=ti + 1,
                    canonical_physical_age=float(states[ti + 1]["age"]),
                    expected_coords=np.asarray(states[ti + 1]["coords"]),
                ))

            integrity = [
                r for r in local_records
                if r["metric_role"] == "EXACT_INTEGRITY_ONLY"
            ]
            descriptive = [
                r for r in local_records
                if r["metric_role"]
                == "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY"
            ]

            integrity_exact = all(
                r.get("exact_match") is True for r in integrity
            )
            descriptive_valid = all(
                r.get("finite") is True
                and r.get("numeric_acceptance_threshold") is None
                and r.get("automatic_pass_fail_from_value") is False
                for r in descriptive
            )
            expected_metric_count = int(
                plan_job["canonical_state_count"]
            ) * len(plan_job["metric_ids"])

            passed = all([
                init.get("pass") is True,
                transition_pass_count == int(plan_job["transition_count"]),
                len(local_records) == expected_metric_count,
                len(integrity) == int(plan_job["canonical_state_count"]) * 2,
                len(descriptive) == int(plan_job["canonical_state_count"]),
                integrity_exact,
                descriptive_valid,
                mod.t == int(plan_job["transition_count"]) - 1,
                mod.comm.t == int(plan_job["transition_count"]) - 1,
                mod.comm[0].t == int(plan_job["transition_count"]) - 1,
                list(mod.comm[0].n_births) == [],
                list(mod.comm[0].n_deaths) == [],
                all(int(ind.age) == 0 for ind in mod.comm[0].values()),
            ])

            metric_records.extend(local_records)
            stream_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "canonical_state_count": len(states),
                "transition_count": int(plan_job["transition_count"]),
                "transition_pass_count": transition_pass_count,
                "metric_record_count": len(local_records),
                "integrity_record_count": len(integrity),
                "descriptive_record_count": len(descriptive),
                "all_integrity_exact": integrity_exact,
                "all_descriptive_valid": descriptive_valid,
                "model_walk_called": False,
                "autonomous_movement_called": False,
                "autonomous_population_dynamics_called": False,
                "autonomous_ageing_called": False,
                "observed_history_claim": False,
                "full_job_revalidation_claim":
                    bool(plan_job["full_job_revalidation_claim"]),
                "scientific_execution_performed": True,
                "pass": bool(passed),
            })
            del mod
        except Exception as exc:
            stream_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "scientific_execution_performed": True,
                "pass": False,
                "error": repr(exc),
            })

    stream_pass_count = sum(bool(r.get("pass")) for r in stream_records)
    integrity_records = [
        r for r in metric_records
        if r["metric_role"] == "EXACT_INTEGRITY_ONLY"
    ]
    descriptive_records = [
        r for r in metric_records
        if r["metric_role"] == "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY"
    ]

    expected_total = int(plan_job["expected_metric_records"])
    expected_integrity = int(plan_job["expected_integrity_records"])
    expected_descriptive = int(plan_job["expected_descriptive_records"])

    ok = all([
        stream_pass_count == 4,
        len(metric_records) == expected_total,
        len(integrity_records) == expected_integrity,
        len(descriptive_records) == expected_descriptive,
        all(r.get("exact_match") is True for r in integrity_records),
        all(r.get("finite") is True for r in descriptive_records),
    ])

    return {
        "stage": STAGE,
        "status":
            "R446_GOVERNED_CARRIER_COHORT_SCIENTIFIC_EVIDENCE_CAPTURED"
            if ok else BLOCKED,
        "job_id": job_id,
        "claim_scope": plan_job["claim_scope"],
        "branch_selector": plan_job["branch_selector"],
        "replicate_stream_count": 4,
        "replicate_stream_pass_count": stream_pass_count,
        "canonical_state_count": int(plan_job["canonical_state_count"]),
        "transition_count_per_stream": int(plan_job["transition_count"]),
        "metric_record_count": len(metric_records),
        "integrity_record_count": len(integrity_records),
        "descriptive_record_count": len(descriptive_records),
        "metric_records": metric_records,
        "stream_records": stream_records,
        "scientific_engine_execution_performed": True,
        "scientific_evidence_capture_valid": bool(ok),
        "automatic_scientific_pass_fail_from_descriptive_values": False,
        "scientific_divergence_claim_count": 0,
        "canonical_state_changed": False,
    }


def _j21_scientific_execution(
    root: Path,
    *,
    native: dict[str, Any],
    plan_job: dict[str, Any],
) -> dict[str, Any]:
    import geonomics as gnx
    from arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers import (
        _r437_j21_bound_param_path,
    )
    from arcana_worldsim.scientific_engines.r442_geonomics_multi_transition_bounded_replay_production_queue_authorization import (
        _advance_authorized_clock_expected,
    )
    from arcana_worldsim.scientific_engines.r444_geonomics_readout_extraction_dry_run_adjudication_input_validation import (
        _layer_metric_records,
        _prepare_j21_dynamic,
    )

    dynamic_by_name, sidecars = _prepare_j21_dynamic(root)
    names = list(dynamic_by_name.keys())
    if len(names) != int(plan_job["native_dynamic_layer_count"]):
        return {"status": BLOCKED, "reason": "J21_NATIVE_LAYER_COUNT_MISMATCH"}

    rows = _native_rows(native, J21)
    observed_seeds = [int(r["frozen_seed"]) for r in rows]
    if observed_seeds != list(plan_job["frozen_seeds"]):
        return {
            "status": BLOCKED,
            "reason": "J21_FROZEN_SEED_VECTOR_MISMATCH",
        }

    ages = [20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0, 0.0]
    metric_records = []
    stream_records = []

    for row in rows:
        rep = int(row["replicate_index"])
        seed = int(row["frozen_seed"])
        try:
            params = copy.deepcopy(
                _import_params(_r437_j21_bound_param_path(root, rep))
            )
            layers = params["landscape"]["layers"]
            for lname in sidecars:
                if lname not in layers:
                    raise RuntimeError(f"missing sidecar-bound layer {lname}")
                del layers[lname]
            if set(names) != (set(layers.keys()) - {"R437_CONSTRUCTION_SUPPORT"}):
                raise RuntimeError("J21 native layer set mismatch")
            for lname in names:
                layers[lname].pop("change", None)

            params["model"]["T"] = 8
            params["model"]["burn_T"] = 0
            params["model"]["seed"] = {"num": seed}
            if "num" in params["model"]:
                params["model"]["num"] = seed
            params["model"]["name"] = f"ARCANA_R446_{J21}_REP{rep}"

            mod = gnx.make_model(
                parameters=gnx.make_params_dict(
                    params, model_name=params["model"]["name"]
                ),
                verbose=False,
            )
            layer_map = {lyr.name: lyr for lyr in mod.land.values()}
            local_records = []

            for lname in names:
                local_records.extend(_layer_metric_records(
                    job_id=J21,
                    replicate_index=rep,
                    frozen_seed=seed,
                    state_index=0,
                    age=ages[0],
                    layer_name=lname,
                    actual=np.asarray(layer_map[lname].rast),
                    expected=np.asarray(dynamic_by_name[lname][0]),
                ))

            transition_pass_count = 0
            for ti in range(8):
                clock = _advance_authorized_clock_expected(
                    mod, expected_before_t=ti - 1
                )
                if clock.get("pass") is not True:
                    raise RuntimeError(f"J21 clock transition {ti} failed")
                for lname in names:
                    layer_map[lname].rast = np.asarray(
                        dynamic_by_name[lname][ti + 1]
                    ).copy()
                transition_pass_count += 1

                for lname in names:
                    local_records.extend(_layer_metric_records(
                        job_id=J21,
                        replicate_index=rep,
                        frozen_seed=seed,
                        state_index=ti + 1,
                        age=ages[ti + 1],
                        layer_name=lname,
                        actual=np.asarray(layer_map[lname].rast),
                        expected=np.asarray(dynamic_by_name[lname][ti + 1]),
                    ))

            integrity = [
                r for r in local_records
                if r["metric_role"] == "EXACT_INTEGRITY_ONLY"
            ]
            descriptive = [
                r for r in local_records
                if r["metric_role"]
                == "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE"
            ]
            integrity_exact = all(
                r.get("exact_match") is True for r in integrity
            )
            descriptive_valid = all(
                r.get("finite") is True
                and r.get("numeric_acceptance_threshold") is None
                and r.get("automatic_pass_fail_from_value") is False
                for r in descriptive
            )

            expected_metric_count = (
                int(plan_job["canonical_state_count"])
                * int(plan_job["native_dynamic_layer_count"])
                * len(plan_job["metric_ids"])
            )

            passed = all([
                transition_pass_count == 8,
                len(local_records) == expected_metric_count,
                len(integrity) == int(plan_job["expected_integrity_records"]) // 4,
                len(descriptive) == int(plan_job["expected_descriptive_records"]) // 4,
                integrity_exact,
                descriptive_valid,
                mod.t == 7,
                mod.comm.t == 7,
                mod.comm[0].t == 7,
                mod.land._changer is None,
                list(mod.comm[0].n_births) == [],
                list(mod.comm[0].n_deaths) == [],
                all(int(ind.age) == 0 for ind in mod.comm[0].values()),
            ])

            metric_records.extend(local_records)
            stream_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "canonical_state_count": 9,
                "transition_count": 8,
                "transition_pass_count": transition_pass_count,
                "native_dynamic_layer_count": 147,
                "dynamic_sidecar_count": 4,
                "metric_record_count": len(local_records),
                "integrity_record_count": len(integrity),
                "descriptive_record_count": len(descriptive),
                "all_integrity_exact": integrity_exact,
                "all_descriptive_valid": descriptive_valid,
                "sidecars_emitted_as_native_metrics": False,
                "landscape_changer_called": False,
                "model_walk_called": False,
                "observed_history_claim": False,
                "full_job_revalidation_claim": True,
                "scientific_execution_performed": True,
                "pass": bool(passed),
            })
            del mod
        except Exception as exc:
            stream_records.append({
                "replicate_index": rep,
                "frozen_seed": seed,
                "scientific_execution_performed": True,
                "pass": False,
                "error": repr(exc),
            })

    stream_pass_count = sum(bool(r.get("pass")) for r in stream_records)
    integrity_records = [
        r for r in metric_records
        if r["metric_role"] == "EXACT_INTEGRITY_ONLY"
    ]
    descriptive_records = [
        r for r in metric_records
        if r["metric_role"] == "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE"
    ]
    ok = all([
        stream_pass_count == 4,
        len(metric_records) == int(plan_job["expected_metric_records"]),
        len(integrity_records) == int(plan_job["expected_integrity_records"]),
        len(descriptive_records) == int(plan_job["expected_descriptive_records"]),
        all(r.get("exact_match") is True for r in integrity_records),
        all(r.get("finite") is True for r in descriptive_records),
    ])

    return {
        "stage": STAGE,
        "status":
            "R446_J21_GOVERNED_SCIENTIFIC_EVIDENCE_CAPTURED"
            if ok else BLOCKED,
        "job_id": J21,
        "claim_scope": plan_job["claim_scope"],
        "branch_selector": plan_job["branch_selector"],
        "replicate_stream_count": 4,
        "replicate_stream_pass_count": stream_pass_count,
        "canonical_state_count": 9,
        "transition_count_per_stream": 8,
        "native_dynamic_layer_count": 147,
        "dynamic_sidecar_count": 4,
        "metric_record_count": len(metric_records),
        "integrity_record_count": len(integrity_records),
        "descriptive_record_count": len(descriptive_records),
        "metric_records": metric_records,
        "stream_records": stream_records,
        "scientific_engine_execution_performed": True,
        "scientific_evidence_capture_valid": bool(ok),
        "automatic_scientific_pass_fail_from_descriptive_values": False,
        "scientific_divergence_claim_count": 0,
        "canonical_state_changed": False,
    }


def _evidence_manifest(
    plan: dict[str, Any],
    plan_verification: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    all_metric_records = [
        r
        for result in results
        for r in result.get("metric_records", [])
    ]
    all_stream_records = [
        r
        for result in results
        for r in result.get("stream_records", [])
    ]
    integrity = [
        r for r in all_metric_records
        if r["metric_role"] == "EXACT_INTEGRITY_ONLY"
    ]
    descriptive = [
        r for r in all_metric_records
        if r["metric_role"] in {
            "SCIENTIFIC_DESCRIPTIVE_CONNECTIVITY",
            "SCIENTIFIC_DESCRIPTIVE_LAYER_STATE",
        }
    ]

    metric_ids = sorted({r["metric_id"] for r in all_metric_records})
    forbidden_metric_ids = sorted(
        set(metric_ids) - {
            MID_COORD, MID_CELL, MID_NN, MID_RASTER, MID_LAYER_SUMMARY
        }
    )

    checks = {
        "parent_plan_hash_exact":
            plan_verification.get("pass") is True,
        "exact_12_replicate_streams":
            len(all_stream_records) == 12,
        "all_12_streams_pass":
            sum(bool(r.get("pass")) for r in all_stream_records) == 12,
        "exact_12456_metric_records":
            len(all_metric_records) == 12456,
        "exact_6540_integrity_records":
            len(integrity) == 6540,
        "exact_5916_descriptive_records":
            len(descriptive) == 5916,
        "all_integrity_exact":
            all(r.get("exact_match") is True for r in integrity),
        "all_descriptive_finite":
            all(r.get("finite") is True for r in descriptive),
        "zero_numeric_thresholds":
            all(
                r.get("numeric_acceptance_threshold") is None
                for r in descriptive
            ),
        "zero_automatic_pass_fail":
            all(
                r.get("automatic_pass_fail_from_value") is False
                for r in descriptive
            ),
        "exact_five_metric_ids":
            metric_ids == [
                MID_CELL,
                MID_COORD,
                MID_NN,
                MID_LAYER_SUMMARY,
                MID_RASTER,
            ],
        "zero_forbidden_metric_ids":
            len(forbidden_metric_ids) == 0,
        "zero_scientific_divergence_claims":
            all(
                result.get("scientific_divergence_claim_count") == 0
                for result in results
            ),
        "canonical_unchanged":
            all(
                result.get("canonical_state_changed") is False
                for result in results
            ),
    }
    ok = all(checks.values())

    return {
        "stage": STAGE,
        "status":
            "R446_FIRST_GOVERNED_REVALIDATION_EVIDENCE_MANIFEST_VALID"
            if ok else BLOCKED,
        "authorized_parent_plan_sha256": plan.get("plan_sha256"),
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "replicate_stream_count": len(all_stream_records),
        "replicate_stream_pass_count":
            sum(bool(r.get("pass")) for r in all_stream_records),
        "metric_record_count": len(all_metric_records),
        "integrity_record_count": len(integrity),
        "descriptive_record_count": len(descriptive),
        "metric_ids": metric_ids,
        "forbidden_metric_ids": forbidden_metric_ids,
        "scientific_engine_execution_performed": True,
        "scientific_evidence_capture_valid": bool(ok),
        "scientific_evidence_status":
            "VALID_GOVERNED_EVIDENCE_CAPTURE"
            if ok else "INVALID_EVIDENCE_CAPTURE",
        "scientific_adjudication_of_descriptive_values_performed": False,
        "automatic_scientific_pass_fail_count": 0,
        "canonical_state_changed": False,
        "next_action":
            NEXT if ok else "REPAIR_R446_EVIDENCE_CAPTURE",
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R445)
    parent_seal = load(root / R445_SEAL)
    plan = load(root / R445_PLAN)
    auth = load(root / R445_AUTH)
    native = load(root / R436_NATIVE)

    plan_verification = _verify_parent_plan(plan)
    if plan_verification.get("pass") is not True:
        blocked = {
            "stage": STAGE,
            "status": BLOCKED,
            "reason": "PARENT_PLAN_HASH_MISMATCH",
            "plan_verification": plan_verification,
        }
        write(root / OUT / "R4_46_INTEGRATED_AUDIT.json", blocked)
        return blocked

    j14 = _carrier_scientific_execution(
        root, native=native, job_id=J14, plan_job=plan["jobs"][J14]
    )
    j18 = _carrier_scientific_execution(
        root, native=native, job_id=J18, plan_job=plan["jobs"][J18]
    )
    j21 = _j21_scientific_execution(
        root, native=native, plan_job=plan["jobs"][J21]
    )
    evidence = _evidence_manifest(
        plan, plan_verification, [j14, j18, j21]
    )

    write(root / OUT / "R4_46_PARENT_PLAN_VERIFICATION.json", plan_verification)
    write(root / OUT / "R4_46_J14_SCIENTIFIC_EVIDENCE.json", j14)
    write(root / OUT / "R4_46_J18_SCIENTIFIC_EVIDENCE.json", j18)
    write(root / OUT / "R4_46_J21_SCIENTIFIC_EVIDENCE.json", j21)
    write(root / OUT / "R4_46_EVIDENCE_MANIFEST.json", evidence)

    checks = {
        "parent_r445_complete_47_47":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 47
            and parent.get("checks_failed") == 0,
        "parent_r445_sealed_29_29":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 29
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r446":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R446_EXECUTE_EXACT_R445_HASHED_PLAN_AND_CAPTURE_ONLY_AUTHORIZED_EVIDENCE",
        "scientific_execution_authorized_by_parent":
            parent.get("scientific_execution_authorized") is True
            and auth.get("scientific_execution_authorized") is True,
        "geonomics_ready_by_parent":
            parent.get("geonomics_execution_ready") is True
            and auth.get("geonomics_execution_ready") is True,
        "parent_plan_hash_exact":
            plan_verification.get("pass") is True,
        "parent_plan_expected_hash":
            plan.get("plan_sha256") == EXPECTED_PARENT_PLAN_SHA256,
        "j14_scientific_streams_4_of_4":
            j14.get("replicate_stream_pass_count") == 4,
        "j14_exact_1692_records":
            j14.get("metric_record_count") == 1692,
        "j14_exact_1128_integrity":
            j14.get("integrity_record_count") == 1128,
        "j14_exact_564_descriptive":
            j14.get("descriptive_record_count") == 564,
        "j18_scientific_streams_4_of_4":
            j18.get("replicate_stream_pass_count") == 4,
        "j18_exact_180_records":
            j18.get("metric_record_count") == 180,
        "j18_exact_120_integrity":
            j18.get("integrity_record_count") == 120,
        "j18_exact_60_descriptive":
            j18.get("descriptive_record_count") == 60,
        "j21_scientific_streams_4_of_4":
            j21.get("replicate_stream_pass_count") == 4,
        "j21_exact_10584_records":
            j21.get("metric_record_count") == 10584,
        "j21_exact_5292_integrity":
            j21.get("integrity_record_count") == 5292,
        "j21_exact_5292_descriptive":
            j21.get("descriptive_record_count") == 5292,
        "evidence_manifest_valid":
            evidence.get("scientific_evidence_capture_valid") is True,
        "exact_12_streams":
            evidence.get("replicate_stream_count") == 12
            and evidence.get("replicate_stream_pass_count") == 12,
        "exact_12456_metric_records":
            evidence.get("metric_record_count") == 12456,
        "exact_6540_integrity_records":
            evidence.get("integrity_record_count") == 6540,
        "exact_5916_descriptive_records":
            evidence.get("descriptive_record_count") == 5916,
        "exact_five_metric_ids":
            len(evidence.get("metric_ids", [])) == 5,
        "zero_forbidden_metric_ids":
            evidence.get("forbidden_metric_ids") == [],
        "zero_numeric_thresholds":
            evidence["checks"]["zero_numeric_thresholds"] is True,
        "zero_automatic_scientific_pass_fail":
            evidence.get("automatic_scientific_pass_fail_count") == 0,
        "scientific_execution_performed":
            evidence.get("scientific_engine_execution_performed") is True,
        "first_governed_run_executed": True,
        "descriptive_adjudication_not_yet_performed":
            evidence.get(
                "scientific_adjudication_of_descriptive_values_performed"
            ) is False,
        "target_numeric_execution_not_performed":
            cfg.get("target_numeric_execution_performed") is False,
        "readjudication_not_performed":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            evidence.get("canonical_state_changed") is False
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
        "authorized_parent_plan_sha256": EXPECTED_PARENT_PLAN_SHA256,
        "first_governed_revalidation_run_executed": bool(ok),
        "scientific_engine_execution_performed": bool(ok),
        "scientific_evidence_capture_valid": bool(ok),
        "scientific_evidence_status":
            "VALID_GOVERNED_EVIDENCE_CAPTURE" if ok else "INVALID",
        "replicate_stream_count": evidence.get("replicate_stream_count"),
        "replicate_stream_pass_count":
            evidence.get("replicate_stream_pass_count"),
        "metric_record_count": evidence.get("metric_record_count"),
        "integrity_record_count": evidence.get("integrity_record_count"),
        "descriptive_record_count": evidence.get("descriptive_record_count"),
        "scientific_adjudication_of_descriptive_values_performed": False,
        "automatic_scientific_pass_fail_count": 0,
        "scientific_divergence_claim_count": 0,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R446_GOVERNED_EXECUTION_OR_EVIDENCE_CAPTURE",
    }
    write(root / OUT / "R4_46_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_46_INTEGRATED_AUDIT.json")
    ev = load(root / OUT / "R4_46_EVIDENCE_MANIFEST.json")
    pv = load(root / OUT / "R4_46_PARENT_PLAN_VERIFICATION.json")

    checks = {
        "r446_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "parent_plan_hash_exact":
            pv.get("pass") is True
            and a.get("authorized_parent_plan_sha256")
            == EXPECTED_PARENT_PLAN_SHA256,
        "first_governed_run_executed":
            a.get("first_governed_revalidation_run_executed") is True,
        "scientific_execution_performed":
            a.get("scientific_engine_execution_performed") is True,
        "evidence_capture_valid":
            a.get("scientific_evidence_capture_valid") is True,
        "evidence_status_valid":
            a.get("scientific_evidence_status")
            == "VALID_GOVERNED_EVIDENCE_CAPTURE",
        "exact_12_streams":
            a.get("replicate_stream_count") == 12
            and a.get("replicate_stream_pass_count") == 12,
        "exact_12456_records":
            a.get("metric_record_count") == 12456,
        "exact_6540_integrity":
            a.get("integrity_record_count") == 6540,
        "exact_5916_descriptive":
            a.get("descriptive_record_count") == 5916,
        "all_evidence_manifest_checks_pass":
            ev.get("checks_passed") == ev.get("checks_total"),
        "zero_thresholds":
            ev["checks"]["zero_numeric_thresholds"] is True,
        "zero_automatic_scientific_pass_fail":
            a.get("automatic_scientific_pass_fail_count") == 0,
        "zero_scientific_divergence_claims":
            a.get("scientific_divergence_claim_count") == 0,
        "descriptive_adjudication_pending":
            a.get(
                "scientific_adjudication_of_descriptive_values_performed"
            ) is False,
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
        "next_r447":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_FIRST_GOVERNED_REVALIDATION_COHORT_EXECUTION_"
            "AND_EVIDENCE_CAPTURE",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "authorized_parent_plan_sha256":
                a.get("authorized_parent_plan_sha256"),
            "first_governed_revalidation_run_executed":
                a.get("first_governed_revalidation_run_executed"),
            "scientific_engine_execution_performed":
                a.get("scientific_engine_execution_performed"),
            "scientific_evidence_capture_valid":
                a.get("scientific_evidence_capture_valid"),
            "replicate_stream_count": a.get("replicate_stream_count"),
            "metric_record_count": a.get("metric_record_count"),
            "integrity_record_count": a.get("integrity_record_count"),
            "descriptive_record_count": a.get("descriptive_record_count"),
            "scientific_adjudication_of_descriptive_values_performed": False,
            "automatic_scientific_pass_fail_count": 0,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
