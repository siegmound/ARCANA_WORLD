"""S3-D5 Earth-only HGP preparation/readback. No engine launch path.

The separate execution adapter must bind authorization and FAIR allocation.
Do not change the original source fixture or sealed S2 evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tarfile

from experiments.r6_thermo_provider_pilot_v1.pilot import blob
from experiments.r6_thermo_provider_pilot_v1.run_s2_fair import git
from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import read_perplex_prn

HERE = Path(__file__).resolve().parent
EVIDENCE = Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6")
S2 = EVIDENCE / "R6_THERMO_S2_REPEATABILITY_NEW01"
MANIFEST_SHA = "74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604"
PRN_SHA = "d942bfa0e73e0d0fcb4ca06fe2a074ea7883d4116ca632638f343e2a23f02c90"
AUDIT_BLOB = "3ed4f2bb3f01f71c9026544c6f7898b759fb3b30"
UPSTREAM = "950d882bb6a9325a627109aa7154f7b526aa3087"
ARCHIVE_SHA = "ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7"
PREFIX = "PERPLEX_01/BL691_MEEMUM/"
FILES = {
    "bl691_MEEMUM.dat": "3954964480612264838636fd394043aa0fef6324",
    "bl691_MEEMUM_input.txt": "05b6c3ee09efdb0125df2793f94b6d214ac8a72e",
    "hp62ver.dat": "34ab165fe8e5856294d7a967c63e07dfc04d701b",
    "solution_model.dat": "564742a569998a768c2d8e15d2b9599ee90438d1",
}
CASES = ("HGP_UPSTREAM", "HGP_PAPER_ALPHA", "HGP_LOW_ALBITE")
AUTHORITY = {
    "D_024": "ACTIVE", "physical_T1": None,
    "mechanical_solve_authorized": False,
    "WORLD_HISTORY_PRODUCTION_AUTHORIZED": False,
    "scientifically_approved_S3_cells": 0, "S3_engine_runs": 0,
    "run_authorized": False,
}


class HGPError(ValueError):
    pass


def need(ok, code):
    if not ok:
        raise HGPError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_audit():
    raw = (HERE / "s3_d4_c_hgp_4tr_source_audit_v1.json").read_bytes()
    need(blob(raw) == AUDIT_BLOB, "HGP_SOURCE_AUDIT_BLOB_DRIFT")
    data = json.loads(raw)
    c = data["pilot_candidate"]
    need(c["authorized"] is False and c["executable"] is False
         and tuple(x["id"] for x in c["cases"]) == CASES
         and c["max_processes"] == 6 and c["fresh_processes_per_case"] == 2
         and c["walltime_cap_s_candidate"] == 150
         and c["peak_rss_budget"] is None and c["io_budget"] is None,
         "HGP_AUDIT_AUTHORITY_DRIFT")
    return data


def replace_phase_list(raw, case):
    """Only replace the single selected C1 entry inside the declared list."""
    need(case in CASES, "HGP_UNKNOWN_CASE")
    pat = rb"(?m)^begin solution phase list[ \t]*\r?\n"
    starts = list(re.finditer(pat, raw))
    need(len(starts) == 1, "HGP_PHASE_LIST_START")
    start = starts[0].end()
    ends = list(re.finditer(rb"(?m)^end solution phase list[ \t]*\r?$", raw))
    need(len(ends) == 1 and ends[0].start() > start, "HGP_PHASE_LIST_END")
    end = ends[0].start()
    section = raw[start:end]
    lines = section.splitlines()
    expected = [b"cAmph(G)", b"Augite(G)", b"melt(G)", b"Ep(HP11)",
                b"Gt(W)", b"Opx(W)", b"Bi(W)", b"Ilm(WPH)", b"Sp(WPC)", b"Fsp(C1)"]
    need([x.strip() for x in lines] == expected, "HGP_PHASE_LIST_DRIFT")
    match = list(re.finditer(rb"(?m)^([ \t]*)Fsp\(C1\)([ \t]*)(\r?\n)", section))
    need(len(match) == 1, "HGP_C1_ENTRY_NOT_UNIQUE")
    m = match[0]
    replacement = m[1] + b"Fsp(HGP)" + m[2] + m[3]
    if case == "HGP_LOW_ALBITE":
        replacement += m[1] + b"lAb(HGP)" + m[3]
    return raw[:start] + section[:m.start()] + replacement + section[m.end():] + raw[end:]


def model_block(raw):
    starts = list(re.finditer(rb"(?m)^Fsp\(HGP\)[ \t]+[^\r\n]*\r?$", raw))
    need(len(starts) == 1, "HGP_MODEL_NOT_UNIQUE")
    start = starts[0].start()
    end = re.search(rb"(?m)^end_of_model[ \t]*\r?$", raw[start:])
    need(end is not None, "HGP_MODEL_END_MISSING")
    stop = start + end.end()
    return start, stop, raw[start:stop]


def replace_alpha(raw):
    start, stop, block = model_block(raw)
    hits = list(re.finditer(rb"(?m)^([ \t]*alpha\(an\)[ \t]+)0\.555([ \t]*\r?)$", block))
    need(len(hits) == 1, "HGP_ALPHA_ENTRY_NOT_UNIQUE_OR_DRIFT")
    m = hits[0]
    new = block[:m.start()] + m[1] + b"0.550" + m[2] + block[m.end():]
    return raw[:start] + new + raw[stop:]


def prepare_inputs(original, case):
    """Pure byte transformation; originals are never written."""
    need(set(original) == set(FILES), "HGP_INPUT_FILE_SET_DRIFT")
    need(case in CASES, "HGP_UNKNOWN_CASE")
    result = dict(original)
    result["bl691_MEEMUM.dat"] = replace_phase_list(original["bl691_MEEMUM.dat"], case)
    model_block(original["solution_model.dat"])
    if case == "HGP_PAPER_ALPHA":
        result["solution_model.dat"] = replace_alpha(original["solution_model.dat"])
    return result


def member(root, manifest, rel):
    path = root / rel
    need(path.is_file() and not path.is_symlink()
         and path.resolve().is_relative_to(root.resolve()), "HGP_MEMBER_PATH_INVALID")
    raw = path.read_bytes()
    need(sha(raw) == manifest["files_sha256"].get(rel), "HGP_MEMBER_SHA_DRIFT:" + rel)
    return raw


def native_observation(raw):
    """Use D3 chemistry closure; retain exact native printed tokens."""
    text = raw.decode("utf-8", errors="replace")
    summary = read_perplex_prn(text, 4000, 1050)
    body = text.split("Phase Compositions (molar  proportions):", 1)[1].split("Phase speciation", 1)[0]
    lines = [x.strip() for x in body.splitlines() if x.strip()]
    cols = re.split(r"\s{2,}", lines[0])[4:]
    rows = {}
    for line in lines[1:]:
        fields = line.split()
        rows[fields[0]] = {"wt": fields[1], "vol": fields[2], "mol_pct": fields[3],
                           "mol": fields[4], "components": dict(zip(cols, fields[5:], strict=True))}
    need(set(rows) == set(summary["phases"]), "HGP_NATIVE_ROW_DRIFT")
    return {"prn_sha256": sha(raw), "summary": summary, "printed_rows": rows,
            "science": "UNKNOWN"}


def compare_observations(a, b, *, same_configuration):
    need(type(same_configuration) is bool, "HGP_COMPARISON_SCOPE_REQUIRED")
    left, right = a["printed_rows"], b["printed_rows"]
    parity = left == right
    return {
        "same_configuration": same_configuration,
        "phase_added": sorted(right.keys() - left.keys()),
        "phase_removed": sorted(left.keys() - right.keys()),
        "printed_rows_identical": parity,
        "raw_bytes_identical": a["prn_sha256"] == b["prn_sha256"],
        "disposition": ("PRINTED_REPEAT_IDENTICAL" if parity else "PRINTED_REPEAT_REVIEW")
            if same_configuration else "MODEL_SENSITIVITY_OBSERVATION_ONLY",
        "numeric_acceptance": "NOT_RATIFIED", "scientific_applicability": "UNKNOWN",
    }


def verify_runtime_and_inputs():
    raw = (S2 / "MANIFEST.json").read_bytes()
    need(sha(raw) == MANIFEST_SHA, "HGP_S2_MANIFEST_DRIFT")
    manifest = json.loads(raw)
    need(manifest["schema"] == "ARCANA_R6_THERMO_S2_REAL_REPEATABILITY_MANIFEST_V1"
         and manifest["perplex_fresh_meemum_process_count"] == 5
         and manifest["physical_T1"] is None, "HGP_S2_SCOPE_DRIFT")
    provenance = json.loads(member(S2, manifest, "RUN_PROVENANCE.json"))
    report = json.loads(member(S2, manifest, PREFIX + "REPORT.json"))
    runtime = provenance["runtime_paths"]
    source = Path(runtime["PERPLEX_SOURCE"]).resolve()
    binary = Path(runtime["PERPLEX_MEEMUM"]).resolve()
    archive = Path(runtime["PERPLEX_RELEASE_ARCHIVE"]).resolve()
    need(git(source, "rev-parse", "HEAD") == UPSTREAM, "HGP_UPSTREAM_HEAD_DRIFT")
    need(binary.is_file() and os.access(binary, os.X_OK), "HGP_BINARY_MISSING")
    need(file_sha(archive) == ARCHIVE_SHA == provenance["perplex_release_sha256"],
         "HGP_ARCHIVE_DRIFT")
    binary_sha = file_sha(binary)
    need(binary_sha == provenance["meemum_sha256"] == report["meemum_binary_sha256"],
         "HGP_BINARY_DRIFT")
    with tarfile.open(archive, "r:gz") as tar:
        items = [x for x in tar.getmembers() if x.isfile() and Path(x.name).name == "meemum"]
        need(len(items) == 1, "HGP_ARCHIVE_BINARY_NOT_UNIQUE")
        with tar.extractfile(items[0]) as stream:
            h = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        need(h.hexdigest() == binary_sha, "HGP_BINARY_NOT_FROM_RELEASE")
    inputs = {}
    for filename, expected_blob in FILES.items():
        data = (source / "test/bl691_MEEMUM" / filename).read_bytes()
        need(blob(data) == expected_blob, "HGP_UPSTREAM_FILE_BLOB_DRIFT:" + filename)
        historical = member(S2, manifest, PREFIX + filename)
        need(data == historical and sha(data) == report["input_sha256"][filename],
             "HGP_S2_INPUT_NOT_IDENTICAL_TO_UPSTREAM:" + filename)
        inputs[filename] = data
    historical_prn = member(S2, manifest, PREFIX + "bl691_MEEMUM.prn")
    need(sha(historical_prn) == PRN_SHA, "HGP_REFERENCE_PRN_DRIFT")
    return inputs, native_observation(historical_prn), {
        "source": str(source), "binary": str(binary), "archive": str(archive),
        "binary_sha256": binary_sha, "archive_sha256": ARCHIVE_SHA,
        "s2_manifest_sha256": MANIFEST_SHA,
    }


def resource_observation():
    # Observations only, never an allocation or enforced cap.
    result = {"disk_free_bytes": shutil.disk_usage(EVIDENCE).free,
              "cpu_affinity_count": len(os.sched_getaffinity(0)),
              "scheduler_environment": {k: os.environ.get(k) for k in
                  ("SLURM_JOB_ID", "SLURM_CPUS_PER_TASK", "SLURM_MEM_PER_NODE",
                   "SLURM_MEM_PER_CPU", "SLURM_JOB_CPUS_PER_NODE", "PBS_JOBID")},
              "cgroup_membership": Path("/proc/self/cgroup").read_text(),
              "cgroup_v2_limits": {},
              "peak_rss_budget": None, "io_budget": None,
              "allocation_verified": False}
    for line in result["cgroup_membership"].splitlines():
        if line.startswith("0::"):
            root = Path("/sys/fs/cgroup").resolve()
            leaf = (root / line[3:].lstrip("/")).resolve()
            if leaf.is_relative_to(root):
                for directory in (leaf, *leaf.parents):
                    if not directory.is_relative_to(root):
                        break
                    for name in ("memory.max", "memory.high", "memory.current", "cpu.max"):
                        path = directory / name
                        if path.is_file():
                            result["cgroup_v2_limits"][str(path)] = path.read_text().strip()
    return result


def preflight():
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
    need(root == Path.cwd().resolve() and HERE.is_relative_to(root),
         "HGP_WRONG_SOURCE_WORKTREE")
    need(sys.executable.endswith("/arcana-r6-linux/bin/python"), "HGP_WRONG_PYTHON_ENV")
    need(not git(root, "status", "--porcelain", "--untracked-files=no"),
         "HGP_TRACKED_SOURCE_DIRTY")
    load_audit()
    original, reference, runtime = verify_runtime_and_inputs()
    cases = []
    for name in CASES:
        transformed = prepare_inputs(original, name)
        changed = sorted(k for k in original if original[k] != transformed[k])
        expected = ["bl691_MEEMUM.dat"]
        if name == "HGP_PAPER_ALPHA":
            expected += ["solution_model.dat"]
        need(changed == expected, "HGP_UNEXPECTED_INPUT_DIFF")
        cases.append({"case": name, "conditional": name == "HGP_LOW_ALBITE",
                      "fresh_processes_planned": 2, "changed_files": changed,
                      "input_sha256": {k: sha(v) for k, v in transformed.items()}})
    return {"status": "HGP_PREPARATION_READONLY_PASS__NO_ENGINE",
            "source_sha": git(root, "rev-parse", "HEAD"), "runtime": runtime,
            "original_input_sha256": {k: sha(v) for k, v in original.items()},
            "reference": reference, "cases": cases, "resources": resource_observation(),
            "walltime_cap_s_candidate": 150, "max_processes_candidate": 6, **AUTHORITY}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("preflight", "run"))
    args = parser.parse_args()
    need(args.phase == "preflight", "HGP_RUN_BLOCKED_PENDING_SEPARATE_AUTHORIZATION_AND_RESOURCE_BINDING")
    print(json.dumps(preflight(), indent=2, allow_nan=False))
    print("S3_D5_HGP_PREPARATION_READONLY_PASS")
    print("S3_ENGINE_RUNS=0")


if __name__ == "__main__":
    main()
