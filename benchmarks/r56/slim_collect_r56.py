from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import tskit

import hashlib

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def summarize_ancestry_segments(segments_by_haplotype, sequence_length: float, donor_label: int = 1):
    if not (sequence_length > 0):
        raise RuntimeError("sequence length must be positive")
    donor_total = 0.0; tract_count = 0; max_tract = 0.0; per_hap = []; any_count = 0
    for segments in segments_by_haplotype:
        ordered = sorted(segments, key=lambda x: (float(x[0]), float(x[1])))
        cursor = 0.0; current = 0.0; hap_donor = 0.0
        for left, right, label in ordered:
            left, right = float(left), float(right)
            if abs(left - cursor) > 1e-6 or right < left or right > sequence_length + 1e-9:
                raise RuntimeError("incomplete/overlapping ancestry segment geometry")
            cursor = right; span = right - left
            if int(label) == donor_label:
                donor_total += span; hap_donor += span
                if current <= 0.0: tract_count += 1
                current += span; max_tract = max(max_tract, current)
            else:
                current = 0.0
        if abs(cursor - sequence_length) > 1e-6:
            raise RuntimeError("ancestry segments do not cover full sequence")
        frac = hap_donor / sequence_length; per_hap.append(frac); any_count += int(hap_donor > 0.0)
    n = len(segments_by_haplotype)
    if n == 0: raise RuntimeError("no recipient haplotypes")
    return {
        "recipient_haplotype_count": n,
        "donor_ancestry_fraction_mean": float(donor_total / (n * sequence_length)),
        "donor_ancestry_fraction_haplotype_minmax": [float(min(per_hap)), float(max(per_hap))],
        "recipient_haplotype_with_any_donor_ancestry_fraction": float(any_count / n),
        "donor_tract_count_total": int(tract_count),
        "donor_tract_length_mean_bp": float(donor_total / tract_count) if tract_count else 0.0,
        "donor_tract_length_max_bp": float(max_tract),
    }



def _pop_metadata(pop: Any) -> dict[str, Any]:
    md = pop.metadata
    if md is None:
        return {}
    if isinstance(md, dict):
        return md
    if isinstance(md, (bytes, bytearray)):
        try:
            return json.loads(bytes(md).decode("utf-8"))
        except Exception:
            return {}
    if isinstance(md, str):
        try:
            return json.loads(md)
        except Exception:
            return {}
    return {}


def _slim_pop_maps(ts: tskit.TreeSequence) -> tuple[dict[int, int], dict[int, int]]:
    slim_to_tskit: dict[int, int] = {}
    tskit_to_slim: dict[int, int] = {}
    for pop in ts.populations():
        md = _pop_metadata(pop)
        if "slim_id" in md:
            sid = int(md["slim_id"])
            slim_to_tskit[sid] = int(pop.id)
            tskit_to_slim[int(pop.id)] = sid
    return slim_to_tskit, tskit_to_slim


def _final_sample_nodes(ts: tskit.TreeSequence, population_index: int) -> list[int]:
    out = []
    for u in ts.samples():
        n = ts.node(int(u))
        if int(n.population) == int(population_index) and abs(float(n.time)) <= 1e-9:
            out.append(int(u))
    return out


def _segments_for_recipient(ts: tskit.TreeSequence, recipient_slim_id: int, donor_slim_id: int) -> tuple[list[list[tuple[float, float, int]]], dict[str, Any]]:
    slim_to_tskit, tskit_to_slim = _slim_pop_maps(ts)
    if recipient_slim_id not in slim_to_tskit or donor_slim_id not in slim_to_tskit:
        raise RuntimeError(f"SLiM population IDs missing from tree sequence metadata: {slim_to_tskit}")
    recip_idx = slim_to_tskit[recipient_slim_id]
    nodes = _final_sample_nodes(ts, recip_idx)
    if not nodes:
        raise RuntimeError(f"no final recipient sample nodes for SLiM population {recipient_slim_id}")
    segs: dict[int, list[tuple[float, float, int]]] = {u: [] for u in nodes}
    unknown_roots: set[int] = set()
    root_pop_counts: dict[int, int] = {}
    for tree in ts.trees():
        left, right = float(tree.interval.left), float(tree.interval.right)
        for u in nodes:
            v = u
            parent = tree.parent(v)
            while parent != tskit.NULL:
                v = int(parent)
                parent = tree.parent(v)
            pop_idx = int(ts.node(v).population)
            sid = tskit_to_slim.get(pop_idx, -1)
            root_pop_counts[sid] = root_pop_counts.get(sid, 0) + 1
            if sid == donor_slim_id:
                label = 1
            elif sid == recipient_slim_id:
                label = 0
            else:
                label = -1
                unknown_roots.add(v)
            segs[u].append((left, right, label))
    if unknown_roots:
        raise RuntimeError(f"ancestry roots outside founder populations: {sorted(unknown_roots)[:20]}")
    return [segs[u] for u in nodes], {
        "recipient_slim_population_id": recipient_slim_id,
        "donor_slim_population_id": donor_slim_id,
        "recipient_tskit_population_index": recip_idx,
        "final_recipient_haplotype_count": len(nodes),
        "root_population_observation_counts": {str(k): int(v) for k, v in sorted(root_pop_counts.items())},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trees", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--stdout", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    ts = tskit.load(str(a.trees))
    p1seg, p1meta = _segments_for_recipient(ts, 1, 2)
    p2seg, p2meta = _segments_for_recipient(ts, 2, 1)
    p1 = summarize_ancestry_segments(p1seg, float(ts.sequence_length), donor_label=1)
    p2 = summarize_ancestry_segments(p2seg, float(ts.sequence_length), donor_label=1)
    expected_haps = int(cfg["founder_size_per_population"]) * 2
    checks = {
        "tree_sequence_nonempty": ts.num_nodes > 0 and ts.num_edges > 0 and ts.num_individuals > 0,
        "sequence_length_exact": abs(float(ts.sequence_length) - float(cfg["sequence_length_bp"])) <= 1e-9,
        "p1_final_haplotype_count_exact": int(p1["recipient_haplotype_count"]) == expected_haps,
        "p2_final_haplotype_count_exact": int(p2["recipient_haplotype_count"]) == expected_haps,
        "p1_ancestry_fraction_bounded": 0.0 <= float(p1["donor_ancestry_fraction_mean"]) <= 1.0,
        "p2_ancestry_fraction_bounded": 0.0 <= float(p2["donor_ancestry_fraction_mean"]) <= 1.0,
    }
    failed = [k for k, v in checks.items() if not bool(v)]
    slim_md = ts.metadata.get("SLiM", {}) if isinstance(ts.metadata, dict) else {}
    result = {
        "stage": "v0.6D1-R5.6",
        "status": "PASS_R56_ANCESTRY_RESULT" if not failed else "FAILED_R56_ANCESTRY_RESULT",
        "failed": failed,
        "checks": checks,
        "schedule_id": cfg["schedule_id"],
        "variant": cfg["variant"],
        "migration_rate": float(cfg["migration_rate"]),
        "seed": int(cfg["seed"]),
        "active_contact_state_count": int(cfg["active_contact_state_count"]),
        "tree_sequence": {
            "nodes": int(ts.num_nodes),
            "edges": int(ts.num_edges),
            "individuals": int(ts.num_individuals),
            "trees": int(ts.num_trees),
            "mutations": int(ts.num_mutations),
            "sequence_length": float(ts.sequence_length),
            "slim_tick": slim_md.get("tick"),
            "slim_cycle": slim_md.get("cycle"),
            "tree_sha256": sha256_file(a.trees),
        },
        "p1_from_p2": {**p1meta, **p1},
        "p2_from_p1": {**p2meta, **p2},
        "interpretation_semantics": "TRUE_LOCAL_ANCESTRY_FROM_REMEMBERED_FOUNDER_ROOTS_UNDER_STANDARDIZED_SLIM_CHALLENGE_NOT_REALIZED_HISTORICAL_ADMIXTURE",
        "automatic_scientific_pass_fail_from_ancestry_value": False,
        "stdout_tail": a.stdout.read_text(encoding="utf-8", errors="replace")[-4000:] if a.stdout.exists() else "",
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
