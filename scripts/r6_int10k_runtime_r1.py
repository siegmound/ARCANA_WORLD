#!/usr/bin/env python3
"""Bounded R1 oracle and timing audit. Never starts a 1000Y/10k simulation.

Run with arcana-r6-linux, PYTHONPATH=src and --output NEW_EXTERNAL_DIRECTORY.
Optional --audit-all-snapshots reads the original archive without evolution.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import cProfile
import hashlib
import json
import os
from pathlib import Path
import pstats
import resource
import statistics
import subprocess
import sys
import time

from arcana_worldsim.r6 import regional_geological_evolution as regional
from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS, load_verified_r6_initial_columns
from arcana_worldsim.r6.unified_multiphysics_microdomain import _state_from_payload
from arcana_worldsim.r6.int10k_history_independent import verify_history_independent_checkpoint

BASE = "2c71370eb9a959c78121ce1c88ec8e9e37187787"
MANIFEST_SHA = "e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a"
EVIDENCE = Path.home() / "HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
ORACLE = EVIDENCE / "INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y"
INPUT = EVIDENCE / "INT10K_E1_R2_I6OODuU9/original_inputs"
WORK = Path(__file__).resolve().parents[1]
SOURCE_HASHES = {
    "RESULT.json": "24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5",
    "MANIFEST.json": "a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21",
    "RESULT.json.sha256": "8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0",
}


def canonical(value):
    return regional._canonical(value)


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(WORK), *args], text=True).strip()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def initial():
    for name, expected in SOURCE_HASHES.items():
        assert file_sha(INPUT / name) == expected, ("E0_INPUT_CHANGED", name)
    raw, identity = load_verified_r6_initial_columns(INPUT)
    return {support: _state_from_payload(raw[support]) for support in SUPPORTS}, identity


def indexed():
    return [json.loads(line) for line in (ORACLE / "INDEX.jsonl").open()]


def anchor_reference(year):
    rows = []
    active = False
    for row in indexed():
        if row["kind"] == "UNIFIED_STEP":
            active = row["time_year"] == year
        if active:
            rows.append((row["kind"], row["payload_sha256"]))
    assert len(rows) == 61
    return rows


def run_segment(years, candidate, cp=None, consumer=None):
    states, identity = initial()
    return regional.run_regional_segment(
        states, identity, config=regional.RegionalConfig(duration_years=1000),
        segment_years=years, checkpoint=cp, history_independent_continuation=True,
        history_consumer=consumer, runtime_copy_optimization=candidate)


def worker(year, candidate, out):
    """One fresh process per mode/anchor; startup and oracle reads untimed."""
    cp = json.loads((ORACLE / f"CHECKPOINT_{year-1:04d}.json").read_bytes())
    states, identity = initial()
    refs = anchor_reference(year)
    samples = []
    results = []
    for repetition in range(8):  # Discard one warm-up, then seven measured runs.
        seen = []
        costs = defaultdict(float)
        output = out / f"y{year}_{candidate}_{repetition}.jsonl"
        with output.open("wb") as stream:
            def emit(kind, payload):
                tick = time.perf_counter()
                encoded = canonical(dict(payload))
                costs["payload_encode_wall_s"] += time.perf_counter() - tick
                tick = time.perf_counter()
                sha = hashlib.sha256(encoded).hexdigest()
                costs["consumer_sha_wall_s"] += time.perf_counter() - tick
                seen.append((kind, sha))
                tick = time.perf_counter()
                # Full-value equivalent writer; no delta or hidden decoder.
                stream.write(b'{"kind":' + canonical(kind) + b',"payload":' + encoded + b'}\n')
                costs["writer_write_wall_s"] += time.perf_counter() - tick
            before = resource.getrusage(resource.RUSAGE_SELF)
            tick = time.perf_counter()
            result = regional.run_regional_segment(
                states, identity, config=regional.RegionalConfig(duration_years=1000),
                segment_years=1, checkpoint=cp, history_independent_continuation=True,
                history_consumer=emit, runtime_copy_optimization=candidate)
            flush_tick = time.perf_counter()
            stream.flush()
            costs["writer_write_wall_s"] += time.perf_counter() - flush_tick
            elapsed = time.perf_counter() - tick
            after = resource.getrusage(resource.RUSAGE_SELF)
        assert seen == refs, (year, candidate, repetition, "ORDERED_ORACLE_MISMATCH")
        verify_history_independent_checkpoint(result["checkpoint"], source_identity=identity,
                                             configuration=result["checkpoint"]["configuration"])
        frontier = result["checkpoint"]["regional_checkpoint"]["regional_state"]
        assert not regional._HISTORY_EXCLUDED_FROM_FRONTIER.intersection(frontier)
        assert "records" not in result["checkpoint"]["regional_checkpoint"]["unified_checkpoint"]["state"]
        results.append(digest(result))
        if repetition:
            samples.append({"wall_s": elapsed, "cpu_user_s": after.ru_utime-before.ru_utime,
                            "cpu_system_s": after.ru_stime-before.ru_stime,
                            "output_bytes": output.stat().st_size, **costs})
    assert len(set(results)) == 1
    profiler = cProfile.Profile()
    from arcana_worldsim.r6 import unified_multiphysics_microdomain as unified
    from arcana_worldsim.r6 import int10k_history_independent as history
    phase_wall = defaultdict(float)
    active = []
    originals = []
    def instrument(module, name, phase):
        original = getattr(module, name)
        originals.append((module, name, original))
        def wrapped(*args, **kwargs):
            frame = [time.perf_counter(), 0.0]
            active.append(frame)
            try:
                return original(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - frame[0]
                active.pop()
                phase_wall[phase] += elapsed - frame[1]
                if active:
                    active[-1][1] += elapsed
        setattr(module, name, wrapped)
    for module, name, phase in (
        (regional, "advance_region", "regional_operator_other"),
        (regional, "_canonical", "regional_json_serialization"),
        (regional, "_clone_canonical_json", "regional_copy"),
        (regional, "_project_validated_history_free_frontier", "frontier_projection_other"),
        (regional, "seal_regional_checkpoint", "regional_checkpoint_other"),
        (regional, "verify_regional_checkpoint", "regional_checkpoint_other"),
        (history, "seal_history_independent_checkpoint", "outer_checkpoint"),
        (history, "verify_history_independent_checkpoint", "outer_checkpoint"),
        (unified, "seal_unified_checkpoint", "unified_checkpoint"),
        (unified, "verify_unified_checkpoint", "unified_checkpoint"),
        (unified, "solve_layered_interface_increment", "numerical_mechanics"),
        (unified, "pure_shear_thermal_step", "numerical_thermal"),
        (unified, "_new_hydrology_state", "numerical_hydrology"),
    ):
        instrument(module, name, phase)
    try:
        profiler.runcall(regional.run_regional_segment, states, identity,
                        config=regional.RegionalConfig(duration_years=1000), segment_years=1,
                        checkpoint=cp, history_independent_continuation=True,
                        history_consumer=lambda kind, payload: digest(payload),
                        runtime_copy_optimization=candidate)
    finally:
        for module, name, original in originals:
            setattr(module, name, original)
    profile_path = out / f"y{year}_{candidate}.pstats"
    profiler.dump_stats(str(profile_path))
    # Exclusive CPU only. These categories are disjoint and additive.
    groups = defaultdict(float)
    for (filename, line, function), (_, _, exclusive, _, _) in pstats.Stats(profiler).stats.items():
        if "json/encoder.py" in filename or "json/decoder.py" in filename:
            group = "json_encode_decode"
        elif "openssl_sha256" in function or "hexdigest" in function:
            group = "hashing"
        elif function in {"clone", "_clone_canonical_json"}:
            group = "candidate_copy"
        elif any(name in filename for name in ("thermomechanical", "thermal", "hydrology", "deep_")):
            group = "domain_modules"
        else:
            group = "orchestration_and_other"
        groups[group] += exclusive
    return {"year": year, "candidate": candidate, "samples": samples,
            "median_wall_s": statistics.median(s["wall_s"] for s in samples),
            "p95_wall_s": sorted(s["wall_s"] for s in samples)[-1],
            "max_wall_s": max(s["wall_s"] for s in samples),
            "peak_rss_kib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "result_sha256": results[0], "checkpoint_bytes": len(canonical(result["checkpoint"])),
            "profile_exclusive_cpu_s": dict(groups), "ordered_oracle_items": len(refs),
            "profile_instrumented_exclusive_wall_s": dict(phase_wall),
            "writer_durability": "buffer_flush_only_no_fsync"}


def short_parity():
    report = []
    index = indexed()
    for years, split in ((3, 1), (10, 5)):
        expected = defaultdict(list)
        for row in index:
            if row["kind"] == "UNIFIED_STEP" and row["time_year"] == years + 1:
                break
            expected[row["kind"]].append(row["payload_sha256"])
        def run(n, prior=None):
            seen = defaultdict(list)
            result = run_segment(n, True, prior,
                                 lambda kind, payload: seen[kind].append(digest(payload)))
            return result, seen
        direct, seen = run(years)
        prefix, pseen = run(split)
        resumed, rseen = run(years-split, prefix["checkpoint"])
        assert dict(seen) == dict(expected)
        assert {kind: pseen[kind] + rseen[kind] for kind in expected} == dict(expected)
        for field in ("checkpoint", "balances", "subsurface_by_support"):
            assert canonical(direct[field]) == canonical(resumed[field]), (years, field)
        baseline = run_segment(years, False, consumer=lambda kind, payload: None)
        assert canonical(direct) == canonical(baseline)
        report.append({"years": years, "split": split, "status": "EXACT_PASS",
                       "items": sum(map(len, expected.values())), "result_sha256": digest(direct)})
    return report


def snapshot_audit():
    """Copier proof on every authentic full snapshot, not a new writer proof."""
    refs = [row for row in indexed() if row["kind"] == "REGIONAL_SNAPSHOT"]
    counts = 0
    with (ORACLE / "HISTORY.jsonl").open("rb") as stream:
        for year, row in enumerate(refs):
            stream.seek(row["offset"])
            envelope = json.loads(stream.read(row["length"]))
            payload = envelope["payload"]
            assert digest(payload) == row["payload_sha256"]
            assert payload["time_year"] == year and len(payload["cells"]) == 9
            cloned = regional._clone_canonical_json(payload)
            assert digest(cloned) == row["payload_sha256"]
            counts = sum(len(cell["deposits"]) for cell in cloned["cells"])
    assert len(refs) == 1001 and counts == 11000
    return {"status": "EXACT_COPIER_PASS", "snapshots": len(refs), "final_deposits": counts,
            "scope": "authentic_full_snapshot_copy; not a candidate 1000Y evolution or delta writer proof"}


def main(args):
    out = args.output.resolve()
    assert not out.exists(), "OUTPUT_MUST_BE_NEW"
    assert not out.is_relative_to(WORK), "OUTPUT_MUST_BE_EXTERNAL"
    out.mkdir(parents=True)
    assert git("rev-parse", "HEAD") == BASE, "WRONG_BASE_HEAD"
    assert git("branch", "--show-current") == "r6/runtime-copy-r1-fair"
    assert file_sha(ORACLE / "MANIFEST.json") == MANIFEST_SHA
    manifest = json.loads((ORACLE / "MANIFEST.json").read_bytes())
    for row in manifest["members"]:
        path = ORACLE / row["path"]
        assert path.stat().st_size == row["byte_length"] and file_sha(path) == row["sha256"], path
    measured_paths = [*sorted((WORK / "src/arcana_worldsim/r6").glob("*.py")),
                      Path(__file__).resolve(), WORK / "tests/test_r6_runtime_copy_r1.py"]
    sources = {str(p.relative_to(WORK)): file_sha(p) for p in measured_paths}
    save(out / "SOURCE_SHA256.json", sources)
    (out / "SOURCE_DIFF.patch").write_text(git("diff", "--", "src/arcana_worldsim/r6"))
    report = {"base_commit": BASE, "source_branch": git("branch", "--show-current"),
              "original_manifest_sha256": MANIFEST_SHA, "python": sys.version,
              "input_sha256": {name: file_sha(INPUT / name) for name in SOURCE_HASHES},
              "git_status": git("status", "--porcelain", "--untracked-files=all"),
              "classification": "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY",
              "status": "BLOCKED_FULL_CANDIDATE_1000Y_ORACLE_AND_AUTHORIZATION_PENDING",
              "short_parity": short_parity(), "benchmarks": []}
    for year in (101, 501, 751):
        pair = []
        for mode in ((False, True) if year != 501 else (True, False)):
            path = out / f"WORKER_{year}_{mode}.json"
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--output", str(out),
                            "--worker", str(year), "--mode", str(int(mode)), "--worker-report", str(path)],
                           check=True, env=os.environ.copy())
            pair.append(json.loads(path.read_text()))
        baseline = next(item for item in pair if not item["candidate"])
        candidate = next(item for item in pair if item["candidate"])
        assert baseline["result_sha256"] == candidate["result_sha256"]
        assert baseline["checkpoint_bytes"] == candidate["checkpoint_bytes"]
        assert {s["output_bytes"] for s in baseline["samples"]} == {s["output_bytes"] for s in candidate["samples"]}
        report["benchmarks"].append({"year": year, "baseline": baseline, "candidate": candidate,
                                     "median_speedup": baseline["median_wall_s"]/candidate["median_wall_s"]})
        save(out / "REPORT.json", report)
        print(year, "speedup", report["benchmarks"][-1]["median_speedup"], flush=True)
    if args.audit_all_snapshots:
        report["all_snapshot_copy_proof"] = snapshot_audit()
    assert sources == {name: file_sha(WORK / name) for name in sources}, "SOURCE_MUTATED_DURING_AUDIT"
    assert report["input_sha256"] == {name: file_sha(INPUT / name) for name in SOURCE_HASHES}
    assert file_sha(ORACLE / "MANIFEST.json") == MANIFEST_SHA
    report["limitations"] = ["Seven samples per anchor; p95 is nearest-rank maximum, not a tail estimate.",
                              "Writer does full payload output and flush, without fsync or persistent index.",
                              "Profile run uses SHA consumer only; exclusive CPU is separate from writer benchmark.",
                              "No new 1000Y evolution; no claim of asymptotic improvement or 10k qualification."]
    save(out / "REPORT.json", report)
    save(out / "FILE_MANIFEST.json", {"members": [
        {"name": str(p.relative_to(out)), "bytes": p.stat().st_size, "sha256": file_sha(p)}
        for p in sorted(out.iterdir()) if p.is_file()]})
    print("R6_INT10K_RUNTIME_R1=" + report["status"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-all-snapshots", action="store_true")
    parser.add_argument("--worker", type=int, choices=(101, 501, 751), help=argparse.SUPPRESS)
    parser.add_argument("--mode", type=int, choices=(0, 1), help=argparse.SUPPRESS)
    parser.add_argument("--worker-report", type=Path, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    if arguments.worker:
        save(arguments.worker_report, worker(arguments.worker, bool(arguments.mode), arguments.output))
    else:
        main(arguments)
