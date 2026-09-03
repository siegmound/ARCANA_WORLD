from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

import numpy as np

STAGE = "v0.6D1-R4.48"

PARENT_COMPLETE = (
    "PASS_R447_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_COHORT_ADJUDICATION_CLOSURE_COMPLETE"
)
PARENT_SEALED = (
    "PASS_R447_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
    "AND_COHORT_ADJUDICATION_CLOSURE_SEALED"
)
PARENT_NEXT = (
    "BUILD_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_PREFLIGHT"
)

COMPLETE = (
    "PASS_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_PREFLIGHT_COMPLETE"
)
SEALED = (
    "PASS_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_PREFLIGHT_SEALED"
)
BLOCKED = (
    "BLOCKED_R448_FULL_JOB_COVERAGE_EXPANSION_PREFLIGHT_FAILURE"
)
NEXT = (
    "BUILD_R449_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
    "EXPANSION_EXECUTION_AND_EVIDENCE_CAPTURE"
)

OUT = Path("outputs/v0_6D1_R4_48")
SEAL = Path("outputs/v0_6D1_R4_48_SEAL/R4_48_FINAL_SEAL_AUDIT.json")
CFG = Path(
    "configs/world1_r448_geonomics_j14_j18_full_job_revalidation_"
    "coverage_expansion_preflight_v0_6D1_R4_48.json"
)

R447 = Path("outputs/v0_6D1_R4_47/R4_47_INTEGRATED_AUDIT.json")
R447_SEAL = Path("outputs/v0_6D1_R4_47_SEAL/R4_47_FINAL_SEAL_AUDIT.json")
R443_REGISTRY = Path(
    "outputs/v0_6D1_R4_43/R4_43_SCIENTIFIC_READOUT_AUTHORITY_REGISTRY.json"
)

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

FROZEN_SEEDS = {
    J14: [310746493, 1894477382, 1291996560, 1554786554],
    J18: [999124684, 1705133798, 1085091276, 555097754],
}

AUTHORIZED_METRICS = {
    J14: [
        "GNX_CARRIER_COORDINATE_READBACK_XY",
        "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
        "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
    ],
    J18: [
        "GNX_CARRIER_COORDINATE_READBACK_XY",
        "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
        "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
    ],
}

MAX_BRANCHES_PER_SHARD = 8
FIRST_COHORT_BRANCH = (0, 0)


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


def _branch_id(member_index: int, candidate_index: int) -> str:
    return f"M{member_index:03d}_C{candidate_index:02d}"


def _make_shards(job_id: str, branches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shards = []
    for start in range(0, len(branches), MAX_BRANCHES_PER_SHARD):
        chunk = branches[start:start + MAX_BRANCHES_PER_SHARD]
        shard_index = len(shards)
        shards.append({
            "job_id": job_id,
            "shard_index": shard_index,
            "shard_id": f"{job_id}_EXPANSION_SHARD_{shard_index:03d}",
            "branch_count": len(chunk),
            "branch_ids": [b["branch_id"] for b in chunk],
            "stream_count": len(chunk) * 4,
            "seed_policy": "ALL_FOUR_FROZEN_SEEDS_PER_BRANCH",
            "scientific_branch_order":
                "FROZEN_MEMBER_MAJOR_THEN_CANDIDATE_MINOR",
        })
    return shards


def _inventory_j14(root: Path) -> dict[str, Any]:
    p = root / J14_SOURCE
    if sha256(p) != J14_SHA:
        return {"status": BLOCKED, "reason": "J14_SOURCE_HASH_MISMATCH"}

    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["age_ma"], dtype=float)
        names = [str(x) for x in z["state_variable_names"]]
        state = np.asarray(z["spatial_state"], dtype=float)

    if state.ndim != 5 or tuple(state.shape[:3]) != (96, 2, 141):
        return {
            "status": BLOCKED,
            "reason": "J14_SPATIAL_STATE_SHAPE_MISMATCH",
            "shape": list(state.shape),
        }
    if len(ages) != 141:
        return {"status": BLOCKED, "reason": "J14_AGE_AXIS_COUNT_MISMATCH"}

    ri = names.index("grid_row")
    ci = names.index("grid_col")
    ai = names.index("active")

    branches = []
    zero_state_count = 0
    nonfinite_coord_count = 0
    out_of_grid_coord_count = 0

    for mi in range(state.shape[0]):
        for ci_idx in range(state.shape[1]):
            carrier_counts = []
            for ti in range(state.shape[2]):
                s = state[mi, ci_idx, ti]
                mask = s[:, ai] > 0.5
                coords = np.column_stack((s[mask, ci], s[mask, ri]))
                n = int(len(coords))
                carrier_counts.append(n)
                if n == 0:
                    zero_state_count += 1
                if n:
                    nonfinite_coord_count += int(np.size(coords) - np.isfinite(coords).sum())
                    out_of_grid_coord_count += int(
                        np.sum(
                            (coords[:, 0] < 0.0)
                            | (coords[:, 0] >= 180.0)
                            | (coords[:, 1] < 0.0)
                            | (coords[:, 1] >= 90.0)
                        )
                    )

            branch = {
                "job_id": J14,
                "branch_id": _branch_id(mi, ci_idx),
                "member_index": mi,
                "candidate_index": ci_idx,
                "canonical_state_count": 141,
                "transition_count": 140,
                "min_carrier_count": min(carrier_counts),
                "max_carrier_count": max(carrier_counts),
                "all_states_nonempty": min(carrier_counts) > 0,
                "already_scientifically_executed":
                    (mi, ci_idx) == FIRST_COHORT_BRANCH,
                "frozen_seeds": FROZEN_SEEDS[J14],
                "metric_ids": AUTHORIZED_METRICS[J14],
                "expected_stream_count": 4,
                "expected_metric_record_count": 141 * 4 * 3,
                "expected_integrity_record_count": 141 * 4 * 2,
                "expected_descriptive_record_count": 141 * 4,
            }
            branches.append(branch)

    ids = [b["branch_id"] for b in branches]
    expansion = [b for b in branches if not b["already_scientifically_executed"]]
    shards = _make_shards(J14, expansion)

    checks = {
        "source_hash_exact": sha256(p) == J14_SHA,
        "shape_96_2_141": tuple(state.shape[:3]) == (96, 2, 141),
        "exact_192_frozen_branches": len(branches) == 192,
        "branch_ids_unique": len(set(ids)) == 192,
        "exact_one_first_cohort_branch":
            sum(b["already_scientifically_executed"] for b in branches) == 1,
        "first_cohort_is_M000_C00":
            branches[0]["branch_id"] == "M000_C00"
            and branches[0]["already_scientifically_executed"] is True,
        "exact_191_expansion_branches": len(expansion) == 191,
        "all_states_have_carriers": zero_state_count == 0,
        "all_coords_finite": nonfinite_coord_count == 0,
        "all_coords_inside_90x180": out_of_grid_coord_count == 0,
        "exact_24_shards": len(shards) == 24,
        "all_shards_at_most_8_branches":
            all(1 <= s["branch_count"] <= 8 for s in shards),
        "exact_764_expansion_streams":
            sum(s["stream_count"] for s in shards) == 764,
    }
    ok = all(checks.values())

    return {
        "stage": STAGE,
        "status": "R448_J14_FULL_COVERAGE_INVENTORY_FROZEN" if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "source_sha256": J14_SHA,
        "canonical_state_count": 141,
        "total_frozen_branch_count": 192,
        "already_executed_branch_count": 1,
        "expansion_branch_count": 191,
        "full_job_expected_stream_count": 192 * 4,
        "expansion_expected_stream_count": 191 * 4,
        "full_job_expected_metric_record_count": 192 * 141 * 4 * 3,
        "expansion_expected_metric_record_count": 191 * 141 * 4 * 3,
        "full_job_expected_integrity_record_count": 192 * 141 * 4 * 2,
        "expansion_expected_integrity_record_count": 191 * 141 * 4 * 2,
        "full_job_expected_descriptive_record_count": 192 * 141 * 4,
        "expansion_expected_descriptive_record_count": 191 * 141 * 4,
        "zero_state_count": zero_state_count,
        "nonfinite_coord_count": nonfinite_coord_count,
        "out_of_grid_coord_count": out_of_grid_coord_count,
        "branch_order": "MEMBER_MAJOR_THEN_CANDIDATE_MINOR",
        "branches": branches,
        "expansion_shards": shards,
        "shard_count": len(shards),
        "pass": ok,
    }


def _inventory_j18(root: Path) -> dict[str, Any]:
    p = root / J18_SOURCE
    if sha256(p) != J18_SHA:
        return {"status": BLOCKED, "reason": "J18_SOURCE_HASH_MISMATCH"}

    with np.load(p, allow_pickle=False) as z:
        ages = np.asarray(z["snapshot_age_ka"], dtype=float)
        names = [str(x) for x in z["state_variable_names"]]
        state = np.asarray(z["snapshot_deme_state"], dtype=float)
        active = np.asarray(z["snapshot_active"])

    if state.ndim != 5 or tuple(state.shape[:3]) != (32, 2, 15):
        return {
            "status": BLOCKED,
            "reason": "J18_SNAPSHOT_STATE_SHAPE_MISMATCH",
            "shape": list(state.shape),
        }
    if active.shape[:3] != (32, 2, 15) or len(ages) != 15:
        return {"status": BLOCKED, "reason": "J18_ACTIVE_OR_AGE_AXIS_MISMATCH"}

    ri = names.index("grid_row")
    ci = names.index("grid_col")

    branches = []
    zero_state_count = 0
    nonfinite_coord_count = 0
    out_of_grid_coord_count = 0

    for mi in range(state.shape[0]):
        for ci_idx in range(state.shape[1]):
            carrier_counts = []
            for ti in range(state.shape[2]):
                mask = np.asarray(active[mi, ci_idx, ti], dtype=float) > 0.5
                s = state[mi, ci_idx, ti]
                coords = np.column_stack((s[mask, ci], s[mask, ri]))
                n = int(len(coords))
                carrier_counts.append(n)
                if n == 0:
                    zero_state_count += 1
                if n:
                    nonfinite_coord_count += int(np.size(coords) - np.isfinite(coords).sum())
                    out_of_grid_coord_count += int(
                        np.sum(
                            (coords[:, 0] < 0.0)
                            | (coords[:, 0] >= 180.0)
                            | (coords[:, 1] < 0.0)
                            | (coords[:, 1] >= 90.0)
                        )
                    )

            branch = {
                "job_id": J18,
                "branch_id": _branch_id(mi, ci_idx),
                "member_index": mi,
                "candidate_index": ci_idx,
                "canonical_state_count": 15,
                "transition_count": 14,
                "min_carrier_count": min(carrier_counts),
                "max_carrier_count": max(carrier_counts),
                "all_states_nonempty": min(carrier_counts) > 0,
                "already_scientifically_executed":
                    (mi, ci_idx) == FIRST_COHORT_BRANCH,
                "frozen_seeds": FROZEN_SEEDS[J18],
                "metric_ids": AUTHORIZED_METRICS[J18],
                "expected_stream_count": 4,
                "expected_metric_record_count": 15 * 4 * 3,
                "expected_integrity_record_count": 15 * 4 * 2,
                "expected_descriptive_record_count": 15 * 4,
            }
            branches.append(branch)

    ids = [b["branch_id"] for b in branches]
    expansion = [b for b in branches if not b["already_scientifically_executed"]]
    shards = _make_shards(J18, expansion)

    checks = {
        "source_hash_exact": sha256(p) == J18_SHA,
        "shape_32_2_15": tuple(state.shape[:3]) == (32, 2, 15),
        "exact_64_frozen_branches": len(branches) == 64,
        "branch_ids_unique": len(set(ids)) == 64,
        "exact_one_first_cohort_branch":
            sum(b["already_scientifically_executed"] for b in branches) == 1,
        "first_cohort_is_M000_C00":
            branches[0]["branch_id"] == "M000_C00"
            and branches[0]["already_scientifically_executed"] is True,
        "exact_63_expansion_branches": len(expansion) == 63,
        "all_states_have_carriers": zero_state_count == 0,
        "all_coords_finite": nonfinite_coord_count == 0,
        "all_coords_inside_90x180": out_of_grid_coord_count == 0,
        "exact_8_shards": len(shards) == 8,
        "all_shards_at_most_8_branches":
            all(1 <= s["branch_count"] <= 8 for s in shards),
        "exact_252_expansion_streams":
            sum(s["stream_count"] for s in shards) == 252,
    }
    ok = all(checks.values())

    return {
        "stage": STAGE,
        "status": "R448_J18_FULL_COVERAGE_INVENTORY_FROZEN" if ok else BLOCKED,
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "source_sha256": J18_SHA,
        "canonical_state_count": 15,
        "total_frozen_branch_count": 64,
        "already_executed_branch_count": 1,
        "expansion_branch_count": 63,
        "full_job_expected_stream_count": 64 * 4,
        "expansion_expected_stream_count": 63 * 4,
        "full_job_expected_metric_record_count": 64 * 15 * 4 * 3,
        "expansion_expected_metric_record_count": 63 * 15 * 4 * 3,
        "full_job_expected_integrity_record_count": 64 * 15 * 4 * 2,
        "expansion_expected_integrity_record_count": 63 * 15 * 4 * 2,
        "full_job_expected_descriptive_record_count": 64 * 15 * 4,
        "expansion_expected_descriptive_record_count": 63 * 15 * 4,
        "zero_state_count": zero_state_count,
        "nonfinite_coord_count": nonfinite_coord_count,
        "out_of_grid_coord_count": out_of_grid_coord_count,
        "branch_order": "MEMBER_MAJOR_THEN_CANDIDATE_MINOR",
        "branches": branches,
        "expansion_shards": shards,
        "shard_count": len(shards),
        "pass": ok,
    }


def _freeze_expansion_plan(
    j14: dict[str, Any],
    j18: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    if j14.get("pass") is not True or j18.get("pass") is not True:
        return {"status": BLOCKED, "reason": "BRANCH_INVENTORY_NOT_VALID"}

    registry_j14 = list(registry["jobs"][J14]["authorized_metrics"])
    registry_j18 = list(registry["jobs"][J18]["authorized_metrics"])

    expansion_shards = (
        list(j14["expansion_shards"]) + list(j18["expansion_shards"])
    )

    plan = {
        "stage": STAGE,
        "status": "R448_J14_J18_FULL_COVERAGE_EXPANSION_PLAN_FROZEN",
        "scientific_authority": {
            "execution_queue":
                "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
            "readout_registry":
                "R4.43_SEALED_FIVE_METRIC_DEFINITION_AUTHORITY",
            "adjudication_semantics":
                "EXACT_INTEGRITY_PLUS_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_THRESHOLD",
        },
        "already_scientifically_executed": {
            J14: ["M000_C00"],
            J18: ["M000_C00"],
        },
        "expansion": {
            J14: {
                "branch_count": 191,
                "stream_count": 764,
                "shard_count": 24,
                "metric_ids": registry_j14,
                "expected_metric_record_count": 323172,
                "expected_integrity_record_count": 215448,
                "expected_descriptive_record_count": 107724,
            },
            J18: {
                "branch_count": 63,
                "stream_count": 252,
                "shard_count": 8,
                "metric_ids": registry_j18,
                "expected_metric_record_count": 11340,
                "expected_integrity_record_count": 7560,
                "expected_descriptive_record_count": 3780,
            },
        },
        "combined_expansion": {
            "branch_count": 254,
            "stream_count": 1016,
            "shard_count": 32,
            "expected_metric_record_count": 334512,
            "expected_integrity_record_count": 223008,
            "expected_descriptive_record_count": 111504,
        },
        "post_expansion_full_coverage": {
            J14: {
                "branch_count": 192,
                "stream_count": 768,
                "expected_metric_record_count": 324864,
                "expected_integrity_record_count": 216576,
                "expected_descriptive_record_count": 108288,
            },
            J18: {
                "branch_count": 64,
                "stream_count": 256,
                "expected_metric_record_count": 11520,
                "expected_integrity_record_count": 7680,
                "expected_descriptive_record_count": 3840,
            },
            "J14_J18_COMBINED": {
                "branch_count": 256,
                "stream_count": 1024,
                "expected_metric_record_count": 336384,
                "expected_integrity_record_count": 224256,
                "expected_descriptive_record_count": 112128,
            },
            "GEONOMICS_ALL_THREE_JOBS_WITH_EXISTING_J21": {
                "expected_metric_record_count": 346968,
                "expected_integrity_record_count": 229548,
                "expected_descriptive_record_count": 117420,
            },
        },
        "sharding": {
            "policy": "DETERMINISTIC_CONTIGUOUS_FROZEN_BRANCH_ORDER",
            "max_branches_per_shard": MAX_BRANCHES_PER_SHARD,
            "all_four_seeds_per_branch": True,
            "shard_membership_is_scientific_plan_authority": True,
            "execution_concurrency_is_scientific_authority": False,
            "resume_unit": "WHOLE_SHARD",
            "shards": expansion_shards,
        },
        "result_selected_branch_choice": False,
        "result_selected_metric_choice": False,
        "result_selected_threshold": False,
        "majority_vote_authorized": False,
        "numeric_acceptance_threshold_count": 0,
        "engine_output_defines_arcana_target": False,
        "canonical_rewrite_authorized": False,
        "j21_reexecution_required": False,
        "scientific_execution_performed_in_r448": False,
    }
    plan["plan_sha256"] = _sha_json(plan)
    return plan


def _authorization(plan: dict[str, Any]) -> dict[str, Any]:
    ok = all([
        plan.get("status")
            == "R448_J14_J18_FULL_COVERAGE_EXPANSION_PLAN_FROZEN",
        plan["combined_expansion"]["branch_count"] == 254,
        plan["combined_expansion"]["stream_count"] == 1016,
        plan["combined_expansion"]["shard_count"] == 32,
        plan["combined_expansion"]["expected_metric_record_count"] == 334512,
        plan["combined_expansion"]["expected_integrity_record_count"] == 223008,
        plan["combined_expansion"]["expected_descriptive_record_count"] == 111504,
        plan["result_selected_branch_choice"] is False,
        plan["result_selected_metric_choice"] is False,
        plan["result_selected_threshold"] is False,
        plan["majority_vote_authorized"] is False,
        plan["numeric_acceptance_threshold_count"] == 0,
        plan["engine_output_defines_arcana_target"] is False,
        plan["canonical_rewrite_authorized"] is False,
        plan["scientific_execution_performed_in_r448"] is False,
    ])
    return {
        "stage": STAGE,
        "status":
            "R448_J14_J18_FULL_COVERAGE_EXPANSION_EXECUTION_AUTHORIZED"
            if ok else BLOCKED,
        "authorization_scope":
            "EXACT_254_REMAINING_FROZEN_BRANCHES_ONLY",
        "expansion_execution_authorized": bool(ok),
        "geonomics_expansion_execution_ready": bool(ok),
        "authorized_plan_sha256": plan.get("plan_sha256") if ok else None,
        "authorized_branch_count": 254 if ok else 0,
        "authorized_stream_count": 1016 if ok else 0,
        "authorized_shard_count": 32 if ok else 0,
        "J14_first_cohort_reexecution_authorized": False,
        "J18_first_cohort_reexecution_authorized": False,
        "J21_reexecution_authorized": False,
        "scientific_execution_performed": False,
        "canonical_state_changed": False,
    }


def build(root: Path) -> dict[str, Any]:
    root = root.resolve()
    cfg = load(root / CFG)
    parent = load(root / R447)
    parent_seal = load(root / R447_SEAL)
    registry = load(root / R443_REGISTRY)

    j14 = _inventory_j14(root)
    j18 = _inventory_j18(root)
    plan = _freeze_expansion_plan(j14, j18, registry)
    auth = _authorization(plan)

    write(root / OUT / "R4_48_J14_FULL_COVERAGE_INVENTORY.json", j14)
    write(root / OUT / "R4_48_J18_FULL_COVERAGE_INVENTORY.json", j18)
    write(root / OUT / "R4_48_FULL_COVERAGE_EXPANSION_PLAN.json", plan)
    write(root / OUT / "R4_48_EXPANSION_EXECUTION_AUTHORIZATION.json", auth)

    checks = {
        "parent_r447_complete_34_34":
            parent.get("status") == PARENT_COMPLETE
            and parent.get("checks_passed") == 34
            and parent.get("checks_failed") == 0,
        "parent_r447_sealed_23_23":
            parent_seal.get("status") == PARENT_SEALED
            and parent_seal.get("verdict") == "SEALED"
            and parent_seal.get("checks_passed") == 23
            and parent_seal.get("checks_failed") == 0,
        "parent_next_action_r448":
            parent.get("next_action") == PARENT_NEXT
            and parent_seal.get("next_action") == PARENT_NEXT,
        "policy_frozen":
            cfg.get("policy")
            == "R448_FREEZE_ALL_REMAINING_J14_J18_BRANCHES_BEFORE_FULL_COVERAGE_EXECUTION",
        "j14_parent_coverage_exact_1_of_192":
            parent.get("j14_branch_coverage") == "1/192"
            and parent.get("j14_full_job_revalidation_closed") is False,
        "j18_parent_coverage_exact_1_of_64":
            parent.get("j18_branch_coverage") == "1/64"
            and parent.get("j18_full_job_revalidation_closed") is False,
        "j21_parent_full_job_closed":
            parent.get("j21_branch_coverage") == "1/1"
            and parent.get("j21_full_job_revalidation_closed") is True,
        "j14_inventory_valid":
            j14.get("pass") is True,
        "j14_exact_192_branches":
            j14.get("total_frozen_branch_count") == 192,
        "j14_exact_191_remaining":
            j14.get("expansion_branch_count") == 191,
        "j14_no_zero_carrier_states":
            j14.get("zero_state_count") == 0,
        "j14_all_coords_finite_and_in_grid":
            j14.get("nonfinite_coord_count") == 0
            and j14.get("out_of_grid_coord_count") == 0,
        "j14_exact_24_shards":
            j14.get("shard_count") == 24,
        "j18_inventory_valid":
            j18.get("pass") is True,
        "j18_exact_64_branches":
            j18.get("total_frozen_branch_count") == 64,
        "j18_exact_63_remaining":
            j18.get("expansion_branch_count") == 63,
        "j18_no_zero_carrier_states":
            j18.get("zero_state_count") == 0,
        "j18_all_coords_finite_and_in_grid":
            j18.get("nonfinite_coord_count") == 0
            and j18.get("out_of_grid_coord_count") == 0,
        "j18_exact_8_shards":
            j18.get("shard_count") == 8,
        "exact_254_remaining_branches":
            plan["combined_expansion"]["branch_count"] == 254,
        "exact_1016_new_streams":
            plan["combined_expansion"]["stream_count"] == 1016,
        "exact_32_expansion_shards":
            plan["combined_expansion"]["shard_count"] == 32,
        "exact_334512_new_metric_records":
            plan["combined_expansion"]["expected_metric_record_count"] == 334512,
        "exact_223008_new_integrity_records":
            plan["combined_expansion"]["expected_integrity_record_count"] == 223008,
        "exact_111504_new_descriptive_records":
            plan["combined_expansion"]["expected_descriptive_record_count"] == 111504,
        "post_expansion_j14_full_192":
            plan["post_expansion_full_coverage"][J14]["branch_count"] == 192,
        "post_expansion_j18_full_64":
            plan["post_expansion_full_coverage"][J18]["branch_count"] == 64,
        "post_expansion_all_geonomics_346968_records":
            plan["post_expansion_full_coverage"][
                "GEONOMICS_ALL_THREE_JOBS_WITH_EXISTING_J21"
            ]["expected_metric_record_count"] == 346968,
        "same_r443_metrics_preserved":
            plan["expansion"][J14]["metric_ids"]
                == AUTHORIZED_METRICS[J14]
            and plan["expansion"][J18]["metric_ids"]
                == AUTHORIZED_METRICS[J18],
        "all_four_frozen_seeds_preserved":
            all(
                b["frozen_seeds"] == FROZEN_SEEDS[J14]
                for b in j14["branches"]
            )
            and all(
                b["frozen_seeds"] == FROZEN_SEEDS[J18]
                for b in j18["branches"]
            ),
        "first_cohort_not_in_expansion":
            "M000_C00"
                not in {
                    bid
                    for s in plan["sharding"]["shards"]
                    for bid in s["branch_ids"]
                },
        "deterministic_sharding_frozen":
            plan["sharding"]["policy"]
            == "DETERMINISTIC_CONTIGUOUS_FROZEN_BRANCH_ORDER"
            and plan["sharding"]["max_branches_per_shard"] == 8,
        "execution_concurrency_not_scientific_authority":
            plan["sharding"][
                "execution_concurrency_is_scientific_authority"
            ] is False,
        "no_result_selected_branch":
            plan["result_selected_branch_choice"] is False,
        "no_result_selected_metric":
            plan["result_selected_metric_choice"] is False,
        "no_result_selected_threshold":
            plan["result_selected_threshold"] is False,
        "zero_numeric_thresholds":
            plan["numeric_acceptance_threshold_count"] == 0,
        "no_majority_vote":
            plan["majority_vote_authorized"] is False,
        "engine_cannot_define_target":
            plan["engine_output_defines_arcana_target"] is False,
        "canonical_rewrite_forbidden":
            plan["canonical_rewrite_authorized"] is False,
        "expansion_execution_authorized":
            auth.get("expansion_execution_authorized") is True,
        "expansion_execution_ready":
            auth.get("geonomics_expansion_execution_ready") is True,
        "authorization_plan_hash_exact":
            auth.get("authorized_plan_sha256") == plan.get("plan_sha256"),
        "no_reexecution_of_closed_evidence":
            auth.get("J14_first_cohort_reexecution_authorized") is False
            and auth.get("J18_first_cohort_reexecution_authorized") is False
            and auth.get("J21_reexecution_authorized") is False,
        "no_scientific_execution_in_r448":
            auth.get("scientific_execution_performed") is False,
        "no_target_numeric":
            cfg.get("target_numeric_execution_performed") is False,
        "no_readjudication":
            cfg.get("readjudication_performed") is False,
        "canonical_unchanged":
            cfg.get("canonical_state_changed") is False,
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
        "j14_current_branch_coverage": "1/192",
        "j14_remaining_branch_count": 191,
        "j18_current_branch_coverage": "1/64",
        "j18_remaining_branch_count": 63,
        "j21_full_job_already_closed": True,
        "combined_remaining_branch_count": 254,
        "combined_new_stream_count": 1016,
        "expansion_shard_count": 32,
        "expansion_expected_metric_record_count": 334512,
        "expansion_expected_integrity_record_count": 223008,
        "expansion_expected_descriptive_record_count": 111504,
        "post_expansion_geonomics_total_metric_record_count": 346968,
        "expansion_plan_sha256": plan.get("plan_sha256"),
        "full_coverage_expansion_execution_authorized": bool(ok),
        "geonomics_expansion_execution_ready": bool(ok),
        "scientific_engine_execution_performed": False,
        "target_numeric_execution_performed": False,
        "readjudication_performed": False,
        "canonical_state_changed": False,
        "active_deferred_p2_cell_count": 2,
        "proxy_context_only_count": 2,
        "p3_backlog_cell_count": 6,
        "next_action":
            NEXT if ok else "REPAIR_R448_FULL_COVERAGE_EXPANSION_PREFLIGHT",
    }
    write(root / OUT / "R4_48_INTEGRATED_AUDIT.json", out)
    return out


def final_seal(root: Path) -> dict[str, Any]:
    root = root.resolve()
    a = load(root / OUT / "R4_48_INTEGRATED_AUDIT.json")
    plan = load(root / OUT / "R4_48_FULL_COVERAGE_EXPANSION_PLAN.json")
    auth = load(root / OUT / "R4_48_EXPANSION_EXECUTION_AUTHORIZATION.json")

    checks = {
        "r448_complete":
            a.get("status") == COMPLETE and a.get("checks_failed") == 0,
        "j14_191_remaining":
            a.get("j14_remaining_branch_count") == 191,
        "j18_63_remaining":
            a.get("j18_remaining_branch_count") == 63,
        "exact_254_remaining":
            a.get("combined_remaining_branch_count") == 254,
        "exact_1016_new_streams":
            a.get("combined_new_stream_count") == 1016,
        "exact_32_shards":
            a.get("expansion_shard_count") == 32,
        "exact_334512_new_records":
            a.get("expansion_expected_metric_record_count") == 334512,
        "exact_223008_new_integrity":
            a.get("expansion_expected_integrity_record_count") == 223008,
        "exact_111504_new_descriptive":
            a.get("expansion_expected_descriptive_record_count") == 111504,
        "post_expansion_total_346968":
            a.get("post_expansion_geonomics_total_metric_record_count") == 346968,
        "plan_hash_exact":
            a.get("expansion_plan_sha256")
            == plan.get("plan_sha256")
            == auth.get("authorized_plan_sha256"),
        "expansion_execution_authorized":
            a.get("full_coverage_expansion_execution_authorized") is True,
        "expansion_execution_ready":
            a.get("geonomics_expansion_execution_ready") is True,
        "first_cohorts_not_reexecuted":
            auth.get("J14_first_cohort_reexecution_authorized") is False
            and auth.get("J18_first_cohort_reexecution_authorized") is False,
        "j21_not_reexecuted":
            auth.get("J21_reexecution_authorized") is False,
        "no_result_selected_branch":
            plan.get("result_selected_branch_choice") is False,
        "no_result_selected_metric":
            plan.get("result_selected_metric_choice") is False,
        "zero_numeric_thresholds":
            plan.get("numeric_acceptance_threshold_count") == 0,
        "no_majority_vote":
            plan.get("majority_vote_authorized") is False,
        "no_scientific_execution_in_r448":
            a.get("scientific_engine_execution_performed") is False,
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
        "next_r449":
            a.get("next_action") == NEXT,
    }
    ok = all(checks.values())

    out = {
        "stage": STAGE,
        "audit":
            "FINAL_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
            "EXPANSION_PREFLIGHT",
        "status": SEALED if ok else BLOCKED,
        "verdict": "SEALED" if ok else "BLOCKED",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks_failed": len(checks) - sum(checks.values()),
        "summary": {
            "j14_current_coverage": "1/192",
            "j14_remaining_branches": 191,
            "j18_current_coverage": "1/64",
            "j18_remaining_branches": 63,
            "combined_remaining_branches": 254,
            "new_streams": 1016,
            "expansion_shards": 32,
            "expansion_expected_metric_records": 334512,
            "expansion_plan_sha256": a.get("expansion_plan_sha256"),
            "full_coverage_expansion_execution_authorized": True,
            "geonomics_expansion_execution_ready": True,
            "scientific_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "next_action": NEXT,
        },
        "next_action": NEXT,
    }
    write(root / SEAL, out)
    return out
