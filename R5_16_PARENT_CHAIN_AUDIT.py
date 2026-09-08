from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

OUTPUT_PATH = Path("R5_16_PARENT_CHAIN_AUDIT.json")
SOURCE_AUTHORITY_PATH = Path("R5_16_SOURCE_AUTHORITY.json")

EXPECTED_BRANCH = "main"
EXPECTED_SOURCE_COMMIT = "ec6c259427af188bd4f7232c21d0f4404c82380d"

R57_AUTHORITY = Path("R5_7_FINAL_BLOCK_SEAL_AUTHORITY.json")
R57_FINAL_SEAL = Path("outputs/v0_6D1_R5_7/R5_7_FINAL_BLOCK_SEAL.json")

R515_CONTRACT = Path("R5_15_BULK_LEGACY_RECONCILIATION_CONTRACT.md")
R515_DEP_GRAPH = Path("R5_15_DEPENDENCY_GRAPH_PASS2.json")

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def run_git(*args: str, check: bool = True, text: bool = True):
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        check=False,
    )
    if check and proc.returncode != 0:
        err = proc.stderr if text else proc.stderr.decode("utf-8", errors="replace")
        raise SystemExit(f"git {' '.join(args)} failed ({proc.returncode}):\n{err}")
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked_files_under(path: Path) -> list[Path]:
    proc = run_git("ls-files", "-z", "--", path.as_posix(), text=False)
    raw = proc.stdout
    out: list[Path] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        rel = item.decode("utf-8", errors="surrogateescape")
        p = Path(rel)
        if p.is_file():
            out.append(p)
    return out


def hash_index(paths: list[Path]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for p in paths:
        digest = sha256(p)
        index.setdefault(digest, []).append(p.as_posix())
    return index


def binding_path(stage_number: int) -> Path:
    return Path(
        f"outputs/v0_6D1_R5_{stage_number}/"
        f"R5_{stage_number}_PARENT_AUTHORITY_BINDING.json"
    )


def compact_stage_token(stage_number: int) -> str:
    return f"r5{stage_number}"


def expected_binding_status(stage_number: int) -> str:
    return f"R5{stage_number}_PARENT_AUTHORITY_BINDING"


def main() -> None:
    root = repo_root()
    os.chdir(root)

    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    head = git_text("rev-parse", "HEAD")

    if branch != EXPECTED_BRANCH:
        raise SystemExit(f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}")

    if head != EXPECTED_SOURCE_COMMIT:
        raise SystemExit(
            "R5.16-B is bound to the completed R5.16-A repository snapshot.\n"
            f"Expected HEAD: {EXPECTED_SOURCE_COMMIT}\n"
            f"Found HEAD:    {head}"
        )

    tracked_dirty = git_text("status", "--porcelain", "--untracked-files=no")
    if tracked_dirty:
        raise SystemExit(
            "Tracked working tree is not clean. Commit/stash tracked changes before R5.16-B:\n"
            + tracked_dirty
        )

    gaps: list[str] = []
    edges: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Prerequisite: R5.16-A source authority must already be PASS.
    # ------------------------------------------------------------------
    if not SOURCE_AUTHORITY_PATH.is_file():
        raise SystemExit(f"Missing prerequisite {SOURCE_AUTHORITY_PATH}")

    source_authority = load_json(SOURCE_AUTHORITY_PATH)
    prerequisite_ok = (
        source_authority.get("stage") == "v0.6D1-R5.16"
        and source_authority.get("subphase") == "R5.16-A2"
        and source_authority.get("status") == "PASS_R516_SOURCE_AUTHORITY"
        and source_authority.get("repository_provenance_complete") is True
        and source_authority.get("open_provenance_gap_count") == 0
        and source_authority.get("stages_verified") == 8
    )
    if not prerequisite_ok:
        gaps.append("SOURCE_AUTHORITY_PREREQUISITE_NOT_PASS")

    stage_a2 = {
        item.get("stage"): item
        for item in source_authority.get("stages", [])
        if isinstance(item, dict)
    }
    for n in range(8, 16):
        s = stage_a2.get(f"v0.6D1-R5.{n}")
        if not s or s.get("status") != "PASS":
            gaps.append(f"A2_STAGE_NOT_PASS:R5.{n}")

    # ------------------------------------------------------------------
    # Sealed root R5.7.
    # ------------------------------------------------------------------
    sealed_root: dict[str, Any] = {
        "stage": "v0.6D1-R5.7",
        "authority_path": R57_AUTHORITY.as_posix(),
        "final_seal_path": R57_FINAL_SEAL.as_posix(),
        "status": "BLOCKED",
    }

    if not R57_AUTHORITY.is_file():
        gaps.append(f"MISSING_R57_AUTHORITY:{R57_AUTHORITY}")
    if not R57_FINAL_SEAL.is_file():
        gaps.append(f"MISSING_R57_FINAL_SEAL:{R57_FINAL_SEAL}")

    if R57_AUTHORITY.is_file():
        r57_auth = load_json(R57_AUTHORITY)
        verdict = r57_auth.get("final_verdict")
        authority_ok = (
            r57_auth.get("stage") == "v0.6D1-R5.7"
            and isinstance(verdict, str)
            and verdict.endswith("_SEALED")
        )
        sealed_root["authority_final_verdict"] = verdict
        sealed_root["authority_sealed"] = authority_ok
        if not authority_ok:
            gaps.append("R57_AUTHORITY_NOT_EXPLICITLY_SEALED")

    # ------------------------------------------------------------------
    # R5.7 -> R5.8: exact sealed-parent artifact hash.
    # ------------------------------------------------------------------
    b8_path = binding_path(8)
    if not b8_path.is_file():
        gaps.append(f"MISSING_PARENT_BINDING:{b8_path}")
    else:
        b8 = load_json(b8_path)
        expected = b8.get("r57_final_seal_sha256")
        actual = sha256(R57_FINAL_SEAL) if R57_FINAL_SEAL.is_file() else None
        binding_shape_ok = (
            b8.get("stage") == "v0.6D1-R5.8"
            and b8.get("status") == expected_binding_status(8)
            and isinstance(expected, str)
            and bool(HEX64.fullmatch(expected))
        )
        exact = binding_shape_ok and actual == expected
        edge = {
            "from": "v0.6D1-R5.7",
            "to": "v0.6D1-R5.8",
            "edge_type": "SEALED_PARENT_EXACT_ARTIFACT_HASH",
            "binding_path": b8_path.as_posix(),
            "claim_key": "r57_final_seal_sha256",
            "claimed_sha256": expected,
            "resolved_path": R57_FINAL_SEAL.as_posix() if actual else None,
            "actual_sha256": actual,
            "exact": exact,
            "status": "PASS" if exact else "BLOCKED",
        }
        edges.append(edge)
        if not exact:
            gaps.append("R57_TO_R58_FINAL_SEAL_HASH_MISMATCH")

    if (
        sealed_root.get("authority_sealed") is True
        and any(e["from"] == "v0.6D1-R5.7" and e["status"] == "PASS" for e in edges)
    ):
        sealed_root["status"] = "PASS"

    # ------------------------------------------------------------------
    # R5.8 -> ... -> R5.14:
    # each child binding must contain direct-parent SHA256 claim(s), and
    # every such claim must resolve exactly to a tracked file in the
    # previous R5 stage output directory.
    # ------------------------------------------------------------------
    for child in range(9, 15):
        parent = child - 1
        bp = binding_path(child)
        parent_dir = Path(f"outputs/v0_6D1_R5_{parent}")

        edge: dict[str, Any] = {
            "from": f"v0.6D1-R5.{parent}",
            "to": f"v0.6D1-R5.{child}",
            "edge_type": "DIRECT_PARENT_EXACT_ARTIFACT_HASH",
            "binding_path": bp.as_posix(),
            "parent_output_directory": parent_dir.as_posix(),
            "status": "BLOCKED",
            "claims": [],
        }

        if not bp.is_file():
            gaps.append(f"MISSING_PARENT_BINDING:{bp}")
            edges.append(edge)
            continue

        binding = load_json(bp)
        if binding.get("stage") != f"v0.6D1-R5.{child}":
            gaps.append(f"PARENT_BINDING_STAGE_MISMATCH:R5.{child}")
        if binding.get("status") != expected_binding_status(child):
            gaps.append(f"PARENT_BINDING_STATUS_MISMATCH:R5.{child}")

        prefix = compact_stage_token(parent) + "_"
        direct_claims = {
            k: v
            for k, v in binding.items()
            if k.startswith(prefix) and k.endswith("_sha256")
        }

        if not direct_claims:
            gaps.append(f"NO_DIRECT_PARENT_HASH_CLAIM:R5.{parent}->R5.{child}")
            edges.append(edge)
            continue

        parent_files = tracked_files_under(parent_dir)
        if not parent_files:
            gaps.append(f"NO_TRACKED_PARENT_OUTPUT_FILES:R5.{parent}")
            edges.append(edge)
            continue

        idx = hash_index(parent_files)
        all_claims_pass = True

        for key, claimed in sorted(direct_claims.items()):
            valid_sha = isinstance(claimed, str) and bool(HEX64.fullmatch(claimed))
            matches = idx.get(claimed, []) if valid_sha else []
            passed = valid_sha and len(matches) >= 1
            edge["claims"].append(
                {
                    "claim_key": key,
                    "claimed_sha256": claimed,
                    "resolved_paths": matches,
                    "status": "PASS" if passed else "BLOCKED",
                }
            )
            if not passed:
                all_claims_pass = False
                gaps.append(
                    f"UNRESOLVED_DIRECT_PARENT_HASH:{key}:"
                    f"R5.{parent}->R5.{child}"
                )

        # Record other bound hashes without scientifically adjudicating them.
        edge["non_continuation_hash_claims"] = sorted(
            k
            for k, v in binding.items()
            if k.endswith("_sha256")
            and k not in direct_claims
            and isinstance(v, str)
        )
        edge["non_continuation_claim_adjudication"] = (
            "DEFERRED_TO_R5_16_C_LEGACY_RECONCILIATION_AUDIT"
        )

        shape_ok = (
            binding.get("stage") == f"v0.6D1-R5.{child}"
            and binding.get("status") == expected_binding_status(child)
        )
        if all_claims_pass and shape_ok:
            edge["status"] = "PASS"

        edges.append(edge)

    # ------------------------------------------------------------------
    # R5.14 -> R5.15:
    # R5.15 is an audit/reconciliation stage. Its parent relation is a
    # governance edge declared in the immutable contract, not a numeric
    # handoff hash claim. Do not invent a missing numeric-parent requirement.
    # ------------------------------------------------------------------
    contract_edge: dict[str, Any] = {
        "from": "v0.6D1-R5.14",
        "to": "v0.6D1-R5.15",
        "edge_type": "GOVERNANCE_PARENT_CONTRACT_BOUND",
        "contract_path": R515_CONTRACT.as_posix(),
        "status": "BLOCKED",
    }

    if not R515_CONTRACT.is_file():
        gaps.append(f"MISSING_R515_CONTRACT:{R515_CONTRACT}")
    else:
        text = R515_CONTRACT.read_text(encoding="utf-8")
        checks = {
            "stage_exact": "STAGE: v0.6D1-R5.15" in text,
            "parent_exact": "PARENT: v0.6D1-R5.14 CANDIDATE" in text,
            "sealed_ancestor_exact": "SEALED_ANCESTOR: v0.6D1-R5.7" in text,
            "auto_seal_forbidden": "AUTO_SEAL: forbidden" in text,
        }
        contract_edge["checks"] = checks
        if all(checks.values()):
            contract_edge["status"] = "PASS"
        else:
            failed = [k for k, v in checks.items() if not v]
            gaps.append(f"R515_CONTRACT_PARENT_EDGE_FAILED:{failed}")

    edges.append(contract_edge)

    # ------------------------------------------------------------------
    # Explicit extra legacy dependency graph.
    # This verifies graph identity/shape only. Scientific compatibility,
    # reuse class and negative-result semantics are intentionally deferred.
    # ------------------------------------------------------------------
    legacy_dependency_graph: dict[str, Any] = {
        "path": R515_DEP_GRAPH.as_posix(),
        "adjudication": "GRAPH_IDENTITY_ONLY_SCIENTIFIC_RECONCILIATION_DEFERRED_TO_R5_16_C",
        "status": "BLOCKED",
    }

    expected_nodes = [f"R3.{n}" for n in range(34, 40)]
    expected_edges = [[f"R3.{n}", f"R3.{n + 1}"] for n in range(34, 39)]

    if not R515_DEP_GRAPH.is_file():
        gaps.append(f"MISSING_R515_DEPENDENCY_GRAPH:{R515_DEP_GRAPH}")
    else:
        graph = load_json(R515_DEP_GRAPH)
        graph_checks = {
            "stage_exact": graph.get("stage") == "v0.6D1-R5.15",
            "pass_exact": graph.get("pass") == "DEPENDENCY_GRAPH_PASS_2",
            "repository_verified_status":
                graph.get("status") == "PASS_REPOSITORY_VERIFIED",
            "nodes_exact": graph.get("nodes") == expected_nodes,
            "internal_edges_exact":
                graph.get("verified_internal_edges") == expected_edges,
            "scope_complete":
                graph.get("scientific_dependency_graph_complete_for_scope") is True,
        }
        legacy_dependency_graph["checks"] = graph_checks
        legacy_dependency_graph["nodes"] = graph.get("nodes")
        legacy_dependency_graph["verified_internal_edges"] = graph.get(
            "verified_internal_edges"
        )
        legacy_dependency_graph["important_external_anchors"] = graph.get(
            "important_external_anchors"
        )
        if all(graph_checks.values()):
            legacy_dependency_graph["status"] = "PASS"
        else:
            failed = [k for k, v in graph_checks.items() if not v]
            gaps.append(f"R515_LEGACY_DEPENDENCY_GRAPH_FAILED:{failed}")

    continuation_edges_pass = (
        len(edges) == 8 and all(edge.get("status") == "PASS" for edge in edges)
    )
    sealed_root_pass = sealed_root.get("status") == "PASS"
    legacy_graph_explicit = legacy_dependency_graph.get("status") == "PASS"

    parent_chain_integrity = (
        prerequisite_ok
        and sealed_root_pass
        and continuation_edges_pass
        and legacy_graph_explicit
        and not gaps
    )

    result = {
        "schema": "ARCANA_R5_16_PARENT_CHAIN_AUDIT_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-B",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": head,
        "prerequisite": {
            "path": SOURCE_AUTHORITY_PATH.as_posix(),
            "status": source_authority.get("status"),
            "repository_provenance_complete":
                source_authority.get("repository_provenance_complete"),
            "open_provenance_gap_count":
                source_authority.get("open_provenance_gap_count"),
            "stages_verified": source_authority.get("stages_verified"),
            "pass": prerequisite_ok,
        },
        "method": {
            "r57_explicit_seal_authority_checked": True,
            "r57_to_r58_final_seal_sha256_exact_checked": True,
            "r58_to_r514_direct_parent_hashes_resolved_against_tracked_parent_outputs": True,
            "r514_to_r515_governance_parent_read_from_contract": True,
            "legacy_dependency_graph_identity_checked": True,
            "legacy_scientific_reconciliation_adjudication": False,
            "negative_result_adjudication": False,
            "human_lineage_governance_adjudication": False,
            "numerical_replay_adjudication": False,
            "external_engine_execution": False,
            "external_engine_governance_final_adjudication": False,
            "canonical_mutation": False,
            "automatic_repair": False,
            "seal_action": False,
        },
        "sealed_root": sealed_root,
        "continuation_edges": edges,
        "continuation_edge_count_expected": 8,
        "continuation_edge_count_verified":
            sum(1 for edge in edges if edge.get("status") == "PASS"),
        "legacy_dependency_graph": legacy_dependency_graph,
        "legacy_dependencies_explicit": legacy_graph_explicit,
        "parent_chain_integrity": parent_chain_integrity,
        "open_parent_chain_gap_count": len(gaps),
        "open_parent_chain_gaps": gaps,
        "status": (
            "PASS_R516_PARENT_CHAIN_AUDIT"
            if parent_chain_integrity
            else "BLOCKED_R516_PARENT_CHAIN_AUDIT"
        ),
        "next_if_pass": "R5.16-C_LEGACY_RECONCILIATION_AUDIT",
    }

    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {head}")
    for edge in edges:
        print(
            f"{edge['from']} -> {edge['to']}: "
            f"{edge.get('status')} [{edge.get('edge_type')}]"
        )
    print(
        "LEGACY_DEPENDENCY_GRAPH = "
        f"{legacy_dependency_graph.get('status')}"
    )
    print(
        "CONTINUATION_EDGES_VERIFIED = "
        f"{result['continuation_edge_count_verified']}/8"
    )
    print(f"OPEN_PARENT_CHAIN_GAPS = {len(gaps)}")
    print(f"STATUS = {result['status']}")

    if not parent_chain_integrity:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
