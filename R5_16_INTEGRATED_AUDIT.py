from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

OUTPUT_PATH = Path("R5_16_INTEGRATED_AUDIT.json")
EXPECTED_BRANCH = "main"
EXPECTED_SOURCE_COMMIT = "b7384eda2062da9356a86850247642df1723beb8"

A_PATH = Path("R5_16_SOURCE_AUTHORITY.json")
B_PATH = Path("R5_16_PARENT_CHAIN_AUDIT.json")
C_PATH = Path("R5_16_LEGACY_RECONCILIATION_AUDIT.json")
D_PATH = Path("R5_16_NEGATIVE_RESULT_PRESERVATION.json")
E_PATH = Path("R5_16_EXTERNAL_ENGINE_GOVERNANCE_AUDIT.json")
R515_PATH = Path("R5_15_FINAL_AUDIT_PASS2.json")
R336_SEAL_PATH = Path("outputs/v0_6D1_R3_36_SEAL/R3_36_FINAL_SEAL_AUDIT.json")

R5_STAGE_PATHS = {
    8: Path("outputs/v0_6D1_R5_8/R5_8_INTEGRATED_RECONCILIATION.json"),
    9: Path("outputs/v0_6D1_R5_9/R5_9_INTEGRATED_RECONCILIATION.json"),
    10: Path("outputs/v0_6D1_R5_10/R5_10_INTEGRATED_RECONCILIATION.json"),
    11: Path("outputs/v0_6D1_R5_11/R5_11_INTEGRATED_RECONCILIATION.json"),
    12: Path("outputs/v0_6D1_R5_12/R5_12_INTEGRATED_RECONCILIATION.json"),
    13: Path("outputs/v0_6D1_R5_13/R5_13_INTEGRATED_RECONCILIATION.json"),
    14: Path("outputs/v0_6D1_R5_14/R5_14_INTEGRATED_RECONCILIATION.json"),
}

INPUT_PATHS = [
    A_PATH,
    B_PATH,
    C_PATH,
    D_PATH,
    E_PATH,
    R515_PATH,
    R336_SEAL_PATH,
    *R5_STAGE_PATHS.values(),
]


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise SystemExit(
            f"git {' '.join(args)} failed ({proc.returncode}):\n{proc.stderr}"
        )
    return proc


def git_text(*args: str) -> str:
    return run_git(*args).stdout.strip()


def repo_root() -> Path:
    return Path(git_text("rev-parse", "--show-toplevel")).resolve()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot parse JSON {path}: {exc}") from exc


def blob_at(ref: str, path: Path) -> str | None:
    proc = run_git("rev-parse", f"{ref}:{path.as_posix()}", check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def pass_check(checks: Any, name: str) -> bool:
    if not isinstance(checks, list):
        return False
    return any(
        isinstance(item, dict)
        and item.get("name") == name
        and item.get("pass") is True
        for item in checks
    )


def write_output(output: dict[str, Any]) -> None:
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    root = repo_root()
    os.chdir(root)

    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    head = git_text("rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise SystemExit(f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}")

    ancestor = run_git(
        "merge-base", "--is-ancestor", EXPECTED_SOURCE_COMMIT, "HEAD", check=False
    )
    if ancestor.returncode != 0:
        raise SystemExit(
            f"Expected R5.16-E source snapshot {EXPECTED_SOURCE_COMMIT} is not an ancestor of HEAD {head}"
        )

    tracked_dirty = git_text("status", "--porcelain", "--untracked-files=no")
    if tracked_dirty:
        raise SystemExit(
            "Tracked working tree is not clean. Commit/stash tracked changes before R5.16-F:\n"
            + tracked_dirty
        )

    gaps: list[str] = []
    drift: list[str] = []

    for path in INPUT_PATHS:
        if not path.is_file():
            gaps.append(f"MISSING_INPUT:{path.as_posix()}")
            continue
        source_blob = blob_at(EXPECTED_SOURCE_COMMIT, path)
        current_blob = blob_at("HEAD", path)
        if source_blob is None:
            gaps.append(f"INPUT_NOT_PRESENT_AT_SOURCE_SNAPSHOT:{path.as_posix()}")
        elif source_blob != current_blob:
            drift.append(path.as_posix())

    if drift:
        gaps.extend(f"INPUT_BLOB_DRIFT:{path}" for path in drift)

    if gaps:
        output = {
            "schema": "ARCANA_R5_16_INTEGRATED_AUDIT_V1",
            "stage": "v0.6D1-R5.16",
            "subphase": "R5.16-F",
            "repository": "siegmound/ARCANA_WORLD",
            "branch": branch,
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "head": head,
            "integrated_audit_pass": False,
            "candidate_eligible_for_explicit_final_seal": False,
            "open_integrated_gap_count": len(gaps),
            "open_integrated_gaps": gaps,
            "status": "BLOCKED_R516_INTEGRATED_AUDIT",
            "next_if_pass": "R5.16-G_EXPLICIT_FINAL_SEAL_AUDIT_AND_MANIFEST",
        }
        write_output(output)
        raise SystemExit(1)

    A = load_json(A_PATH)
    B = load_json(B_PATH)
    C = load_json(C_PATH)
    D = load_json(D_PATH)
    E = load_json(E_PATH)
    r515 = load_json(R515_PATH)
    r336 = load_json(R336_SEAL_PATH)
    stages = {n: load_json(path) for n, path in R5_STAGE_PATHS.items()}

    gate_inputs = {
        "A_repository_provenance": {
            "path": A_PATH.as_posix(),
            "status": A.get("status"),
            "open_gap_count": A.get("open_provenance_gap_count"),
            "pass": (
                A.get("status") == "PASS_R516_SOURCE_AUTHORITY"
                and A.get("repository_provenance_complete") is True
                and A.get("open_provenance_gap_count") == 0
            ),
        },
        "B_parent_chain": {
            "path": B_PATH.as_posix(),
            "status": B.get("status"),
            "continuation_edges_verified": B.get("continuation_edge_count_verified"),
            "open_gap_count": B.get("open_parent_chain_gap_count"),
            "pass": (
                B.get("status") == "PASS_R516_PARENT_CHAIN_AUDIT"
                and B.get("parent_chain_integrity") is True
                and B.get("continuation_edge_count_verified") == 8
                and B.get("open_parent_chain_gap_count") == 0
            ),
        },
        "C_legacy_reconciliation": {
            "path": C_PATH.as_posix(),
            "status": C.get("status"),
            "legacy_stages_verified": C.get("stages_verified"),
            "open_gap_count": C.get("open_legacy_reconciliation_gap_count"),
            "pass": (
                C.get("status") == "PASS_R516_LEGACY_RECONCILIATION_AUDIT"
                and C.get("legacy_reconciliation_integrity") is True
                and C.get("stages_verified") == 6
                and C.get("scientific_incompatibility_count") == 0
                and C.get("open_legacy_reconciliation_gap_count") == 0
            ),
        },
        "D_negative_and_human_governance": {
            "path": D_PATH.as_posix(),
            "status": D.get("status"),
            "open_gap_count": D.get("open_negative_or_governance_gap_count"),
            "pass": (
                D.get("status") == "PASS_R516_NEGATIVE_RESULT_AND_HUMAN_GOVERNANCE_AUDIT"
                and D.get("negative_results_preserved") is True
                and D.get("human_lineage_governance_preserved") is True
                and D.get("open_negative_or_governance_gap_count") == 0
            ),
        },
        "E_numerical_and_engine_governance": {
            "path": E_PATH.as_posix(),
            "status": E.get("status"),
            "open_gap_count": E.get("open_numerical_or_engine_governance_gap_count"),
            "pass": (
                E.get("status") == "PASS_R516_NUMERICAL_REPLAY_AND_EXTERNAL_ENGINE_GOVERNANCE_AUDIT"
                and E.get("numerical_replay_claims_supported") is True
                and E.get("external_engine_governance_preserved") is True
                and E.get("open_numerical_or_engine_governance_gap_count") == 0
            ),
        },
    }

    for name, gate in gate_inputs.items():
        if not gate["pass"]:
            gaps.append(f"GATE_FAILED:{name}")

    stage_mutation_keys = {
        8: None,
        9: "r328_not_rerun_or_mutated",
        10: "r329_not_rerun_or_mutated",
        11: "r330_not_rerun_or_mutated",
        12: "r331_not_scientifically_rerun_or_mutated",
        13: "r332_not_scientifically_rerun_or_mutated",
        14: "r333_not_scientifically_rerun_or_mutated",
    }

    canonical_stage_evidence: dict[str, Any] = {}
    all_stage_canonical_unchanged = True
    all_derived_not_promoted = True
    all_legacy_not_mutated = True

    for n, stage in stages.items():
        checks = stage.get("checks")
        canonical_unchanged = (
            isinstance(checks, dict) and checks.get("canonical_state_unchanged") is True
        )
        derived_not_promoted = (
            isinstance(checks, dict)
            and checks.get("derived_refinement_not_promoted") is True
        )
        mutation_key = stage_mutation_keys[n]
        legacy_not_mutated = True if mutation_key is None else (
            isinstance(checks, dict) and checks.get(mutation_key) is True
        )

        canonical_stage_evidence[f"r5_{n}"] = {
            "canonical_state_changed": not canonical_unchanged,
            "derived_refinement_promoted_to_canon": not derived_not_promoted,
            **(
                {"legacy_stage_rerun_or_mutated": not legacy_not_mutated}
                if mutation_key is not None
                else {}
            ),
        }

        all_stage_canonical_unchanged &= canonical_unchanged
        all_derived_not_promoted &= derived_not_promoted
        all_legacy_not_mutated &= legacy_not_mutated

    r515_checks = r515.get("checks") if isinstance(r515.get("checks"), dict) else {}
    r515_exact_nonmutating = (
        r515_checks.get("all_stages_exact_artifact_reuse_class_A") is True
        and r515_checks.get("new_simulation_not_required") is True
        and r515.get("repair_block_required") is False
        and r515.get("result_counts", {}).get("scientific_incompatibility_proven") == 0
    )
    canonical_stage_evidence["r5_15"] = {
        "all_legacy_reuse_class_A_exact": r515_checks.get("all_stages_exact_artifact_reuse_class_A") is True,
        "new_simulation_required": not (r515_checks.get("new_simulation_not_required") is True),
        "repair_block_required": r515.get("repair_block_required"),
        "scientific_incompatibility_count": r515.get("result_counts", {}).get("scientific_incompatibility_proven"),
    }

    threshold_not_relaxed = pass_check(r336.get("checks"), "thresholds_not_relaxed")
    source_stages = A.get("stages") if isinstance(A.get("stages"), list) else []
    no_inventory_blob_drift = (
        len(source_stages) == 8
        and all(
            isinstance(item, dict)
            and item.get("provenance_complete") is True
            and item.get("inventory_blob_drift_count") == 0
            for item in source_stages
        )
    )

    canonical_mutation_audit = {
        "earlier_sealed_scientific_law_changed": not (
            all_stage_canonical_unchanged and all_derived_not_promoted and no_inventory_blob_drift
        ),
        "earlier_sealed_stage_rerun_or_mutated": not (
            all_legacy_not_mutated and r515_exact_nonmutating
        ),
        "threshold_relaxation_to_force_outcome_detected": not threshold_not_relaxed,
        "untracked_canonical_rewrite_detected": not no_inventory_blob_drift,
    }
    unauthorized_canonical_mutation = any(canonical_mutation_audit.values())
    canonical_mutation_audit["unauthorized_canonical_mutation"] = unauthorized_canonical_mutation

    if unauthorized_canonical_mutation:
        gaps.append("UNAUTHORIZED_CANONICAL_MUTATION_DETECTED")

    open_provenance_gap_count = (
        A.get("open_provenance_gap_count", 0)
        + B.get("open_parent_chain_gap_count", 0)
        + C.get("open_legacy_reconciliation_gap_count", 0)
    )
    open_scientific_gap_count = (
        C.get("scientific_incompatibility_count", 0)
        + D.get("open_negative_or_governance_gap_count", 0)
        + E.get("open_numerical_or_engine_governance_gap_count", 0)
    )

    if open_provenance_gap_count != 0:
        gaps.append(f"OPEN_PROVENANCE_GAPS:{open_provenance_gap_count}")
    if open_scientific_gap_count != 0:
        gaps.append(f"OPEN_SCIENTIFIC_GAPS:{open_scientific_gap_count}")

    contract_domains = {
        "repository_provenance_complete": gate_inputs["A_repository_provenance"]["pass"],
        "parent_chain_integrity": gate_inputs["B_parent_chain"]["pass"],
        "legacy_reconciliation_integrity": gate_inputs["C_legacy_reconciliation"]["pass"],
        "negative_results_preserved": D.get("negative_results_preserved") is True,
        "human_lineage_governance_preserved": D.get("human_lineage_governance_preserved") is True,
        "numerical_replay_claims_supported": E.get("numerical_replay_claims_supported") is True,
        "external_engine_governance_preserved": E.get("external_engine_governance_preserved") is True,
        "unauthorized_canonical_mutation": unauthorized_canonical_mutation,
    }

    integrated_pass = (
        all(gate["pass"] for gate in gate_inputs.values())
        and not unauthorized_canonical_mutation
        and open_provenance_gap_count == 0
        and open_scientific_gap_count == 0
        and not gaps
    )

    output = {
        "schema": "ARCANA_R5_16_INTEGRATED_AUDIT_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-F",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "gate_inputs": gate_inputs,
        "contract_domains": contract_domains,
        "canonical_mutation_stage_evidence": canonical_stage_evidence,
        "canonical_mutation_audit": canonical_mutation_audit,
        "open_provenance_gap_count": open_provenance_gap_count,
        "open_scientific_gap_count": open_scientific_gap_count,
        "open_integrated_gap_count": len(gaps),
        "open_integrated_gaps": gaps,
        "integrated_audit_pass": integrated_pass,
        "candidate_eligible_for_explicit_final_seal": integrated_pass,
        "explicit_final_seal": {
            "audit_performed": False,
            "manifest_created": False,
            "required_next": integrated_pass,
            "r5_16_sealed": False,
        },
        "method": {
            "all_required_r5_16_gate_artifacts_repository_bound": True,
            "stage_level_canonical_mutation_evidence_checked": True,
            "threshold_forcing_checked_against_sealed_legacy_and_reconciliation_evidence": True,
            "fresh_scientific_rerun": False,
            "external_engine_execution": False,
            "automatic_repair": False,
            "canonical_mutation": False,
            "seal_action": False,
        },
        "status": (
            "PASS_R516_INTEGRATED_AUDIT_ELIGIBLE_FOR_EXPLICIT_FINAL_SEAL"
            if integrated_pass
            else "BLOCKED_R516_INTEGRATED_AUDIT"
        ),
        "next_if_pass": "R5.16-G_EXPLICIT_FINAL_SEAL_AUDIT_AND_MANIFEST",
    }

    write_output(output)
    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {EXPECTED_SOURCE_COMMIT}")
    print(f"HEAD = {head}")
    print(f"OPEN_PROVENANCE_GAPS = {open_provenance_gap_count}")
    print(f"OPEN_SCIENTIFIC_GAPS = {open_scientific_gap_count}")
    print(f"UNAUTHORIZED_CANONICAL_MUTATION = {unauthorized_canonical_mutation}")
    print(f"INTEGRATED_PASS = {integrated_pass}")
    print(f"STATUS = {output['status']}")

    if not integrated_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
