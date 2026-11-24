"""Bounded, separately authorized HGP anchor exploration; never production.

No execution on import. An operator-supplied, exact-source authorization JSON
is mandatory. RLIMIT_AS bounds address space, not physical RSS; RLIMIT_FSIZE
bounds individual file size, not aggregate disk IO. Aggregate retained bytes
are observed with a stop between runs, not claimed to be a hard IO quota.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

from experiments.r6_thermo_provider_pilot_v1 import s3_d5_hgp_prepare as prep
from experiments.r6_thermo_provider_pilot_v1.pilot import blob
from experiments.r6_thermo_provider_pilot_v1.run_s2_fair import git, write_json

RECEIPT = prep.HERE / "s3_d5_hgp_fair_preparation_receipt_v1.json"
RECEIPT_BLOB = "3d7d9c6b0e73ca2f10561a0f828e7490ab95f790"
PREP_BLOB = "c86ad28b0e8e96ea32b0c6c92812a932dc737b10"
STAGE_AB = ("HGP_UPSTREAM", "HGP_PAPER_ALPHA")
STAGE_C = ("HGP_LOW_ALBITE",)
AUTH_KEYS = {"schema", "source_sha", "receipt_git_blob", "scope", "stage",
             "evidence_id", "site_policy_basis", "address_space_limit_bytes",
             "file_size_limit_bytes", "retained_bytes_stop_threshold",
             "walltime_s", "operator_authorizes_explore"}


def need(ok, message):
    if not ok:
        raise prep.HGPError(message)


def validate_authorization(a, head):
    need(type(a) is dict and set(a) == AUTH_KEYS, "HGP_AUTH_FIELDS")
    need(a["schema"] == "R6_HGP_OPERATOR_EXPLORE_AUTH_V1"
         and a["scope"] == "EARTH_BL691_ONLY"
         and a["source_sha"] == head and len(head) == 40
         and a["receipt_git_blob"] == RECEIPT_BLOB
         and a["operator_authorizes_explore"] is True, "HGP_AUTH_SCOPE")
    need(a["stage"] in ("AB", "C"), "HGP_AUTH_STAGE")
    eid = a["evidence_id"]
    import re
    need(type(eid) is str and re.fullmatch(r"R6_THERMO_S3_D5_HGP_(AB|C)_NEW[0-9]{2,}", eid)
         and eid.startswith("R6_THERMO_S3_D5_HGP_" + a["stage"] + "_"), "HGP_EVIDENCE_ID")
    need(type(a["site_policy_basis"]) is str and bool(a["site_policy_basis"].strip()),
         "HGP_SITE_POLICY_REQUIRED")
    for key in ("address_space_limit_bytes", "file_size_limit_bytes",
                "retained_bytes_stop_threshold", "walltime_s"):
        need(type(a[key]) is int and a[key] > 0, "HGP_LIMIT_REQUIRED:" + key)
    need(a["walltime_s"] <= 150 and a["file_size_limit_bytes"] <=
         a["retained_bytes_stop_threshold"], "HGP_LIMIT_RANGE")
    return a


def read_receipt():
    raw = RECEIPT.read_bytes()
    need(blob(raw) == RECEIPT_BLOB, "HGP_FAIR_RECEIPT_DRIFT")
    need(blob((prep.HERE / "s3_d5_hgp_prepare.py").read_bytes()) == PREP_BLOB,
         "HGP_QUALIFIED_PREPARATION_SOURCE_DRIFT")
    return json.loads(raw)


def check_preparation(current, receipt):
    need(current["original_input_sha256"] == receipt["original_input_sha256"]
         and current["runtime"]["binary_sha256"] == receipt["binary_sha256"]
         and current["runtime"]["archive_sha256"] == receipt["archive_sha256"]
         and current["runtime"]["s2_manifest_sha256"] == receipt["s2_manifest_sha256"]
         and current["reference"]["prn_sha256"] == receipt["reference_prn_sha256"]
         and {x["case"]: x["input_sha256"] for x in current["cases"]} == receipt["cases"],
         "HGP_FAIR_PREPARATION_PARITY_DRIFT")


def inventory(root):
    result = {}
    for p in sorted(root.rglob("*")):
        need(not p.is_symlink(), "HGP_OUTPUT_SYMLINK")
        if p.is_file():
            result[str(p.relative_to(root))] = {"sha256": prep.file_sha(p),
                                                "bytes": p.stat().st_size}
    return result


def retained_bytes(root):
    total = 0
    for p in root.rglob("*"):
        need(not p.is_symlink(), "HGP_OUTPUT_SYMLINK")
        if p.is_file():
            total += p.stat().st_size
    return total


def seal(root, state, head, launched):
    members = inventory(root)
    write_json(root / "MANIFEST.json", {
        "schema": "R6_HGP_EXPLORE_MANIFEST_V1", "state": state,
        "source_sha": head, "engine_processes_started": launched,
        "files": members, "retained_member_bytes": sum(x["bytes"] for x in members.values()),
        "scientific_applicability": "UNKNOWN", "numeric_acceptance": "NOT_RATIFIED",
        "scientifically_approved_S3_cells": 0, "physical_T1": None,
        "mechanical_solve_authorized": False, "WORLD_HISTORY_PRODUCTION_AUTHORIZED": False,
        "D_024": "ACTIVE",
    })
    print("HGP_MANIFEST_SHA256=" + prep.file_sha(root / "MANIFEST.json"), flush=True)


def launch(binary, work, a):
    def limits():
        resource.setrlimit(resource.RLIMIT_AS, (a["address_space_limit_bytes"],)*2)
        resource.setrlimit(resource.RLIMIT_FSIZE, (a["file_size_limit_bytes"],)*2)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", BLIS_NUM_THREADS="1", LC_ALL="C")
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    with (work / "bl691_MEEMUM_input.txt").open("rb") as stdin, \
         (work / "RUN_STDOUT.log").open("xb") as stdout:
        proc = subprocess.Popen([str(binary)], stdin=stdin, stdout=stdout,
                                stderr=subprocess.STDOUT, cwd=work, env=env,
                                start_new_session=True, preexec_fn=limits)
        timeout = False
        try:
            status = proc.wait(timeout=a["walltime_s"])
        except BaseException as exc:
            timeout = isinstance(exc, subprocess.TimeoutExpired)
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            status = proc.wait()
            if not timeout:
                raise
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    # ru_maxrss is cumulative maximum over reaped children of this Python
    # process, not per-run; label correctly. CPU and block ops are deltas.
    info = {"pid": proc.pid, "exit_code": status, "timeout": timeout,
            "wall_s": time.monotonic()-start,
            "children_cumulative_maxrss_KiB": after.ru_maxrss,
            "child_user_cpu_s": after.ru_utime-before.ru_utime,
            "child_system_cpu_s": after.ru_stime-before.ru_stime,
            "child_input_block_ops": after.ru_inblock-before.ru_inblock,
            "child_output_block_ops": after.ru_oublock-before.ru_oublock,
            "address_space_limit_bytes": a["address_space_limit_bytes"],
            "individual_file_size_limit_bytes": a["file_size_limit_bytes"]}
    write_json(work / "LAUNCH.json", info)
    need(status == 0 and not timeout, "HGP_ENGINE_FAILED_PRESERVE")
    return info


def verify_ab(root, manifest_sha, receipt):
    """Bind conditional C to a completed AB evidence directory and its digest."""
    need(type(manifest_sha) is str and len(manifest_sha) == 64, "HGP_AB_SHA_REQUIRED")
    mpath = root / "MANIFEST.json"
    need(prep.file_sha(mpath) == manifest_sha, "HGP_AB_MANIFEST_DRIFT")
    m = json.loads(mpath.read_bytes())
    need(m["schema"] == "R6_HGP_EXPLORE_MANIFEST_V1"
         and m["state"] == "HGP_AB_DIAGNOSTIC_COMPLETE"
         and m["engine_processes_started"] == 4
         and m["physical_T1"] is None, "HGP_AB_SCOPE")
    actual = inventory(root)
    actual.pop("MANIFEST.json")
    need(actual == m["files"], "HGP_AB_MEMBER_DRIFT")
    result = json.loads((root / "RESULT.json").read_bytes())
    need(result["stage"] == "AB" and result["receipt_git_blob"] == RECEIPT_BLOB
         and set(result["observations"]) == set(STAGE_AB)
         and all(len(result["observations"][x]) == 2 for x in STAGE_AB)
         and all(result["repeatability"][x]["printed_rows_identical"] for x in STAGE_AB),
         "HGP_AB_NOT_READY_FOR_C")
    return result


def run(auth_path, *, ab_root=None, ab_manifest_sha=None):
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
    head = git(root, "rev-parse", "HEAD")
    a = validate_authorization(json.loads(Path(auth_path).read_bytes()), head)
    receipt = read_receipt()
    current = prep.preflight()
    check_preparation(current, receipt)
    need(current["source_sha"] == head, "HGP_HEAD_DRIFT")
    original, reference, runtime = prep.verify_runtime_and_inputs()
    need(runtime == current["runtime"] and reference == current["reference"],
         "HGP_INPUT_RECHECK_DRIFT")
    out = prep.EVIDENCE / a["evidence_id"]
    need(not out.exists() and not out.is_symlink(), "HGP_OUTPUT_ALREADY_EXISTS")
    need(current["resources"]["disk_free_bytes"] >= a["retained_bytes_stop_threshold"],
         "HGP_INSUFFICIENT_DISK")
    if a["stage"] == "C":
        need(ab_root is not None and ab_manifest_sha is not None, "HGP_AB_REQUIRED")
        ab_root = Path(ab_root).resolve()
        need(ab_root.parent == prep.EVIDENCE.resolve() and ab_root.name.startswith(
            "R6_THERMO_S3_D5_HGP_AB_NEW"), "HGP_AB_PATH")
        ab = verify_ab(ab_root, ab_manifest_sha, receipt)
    else:
        need(ab_root is None and ab_manifest_sha is None, "HGP_UNEXPECTED_AB_ARGUMENTS")
        ab = None
    out.mkdir(exist_ok=False)
    launched = 0
    try:
        write_json(out / "AUTHORIZATION.json", a)
        write_json(out / "PREPARATION.json", current)
        write_json(out / "PROVENANCE.json", {
            "source_sha": head, "receipt_git_blob": RECEIPT_BLOB,
            "ab_manifest_sha256": ab_manifest_sha,
            "scope": "EARTH_ONLY_EXPERIMENTAL_NONCANONICAL",
            "limits_are_operator_declared": True,
            "site_allocation_independently_verified": False})
        observations = {}
        repeatability = {}
        for case in STAGE_AB if a["stage"] == "AB" else STAGE_C:
            observations[case] = []
            for i in (1, 2):
                need(retained_bytes(out) < a["retained_bytes_stop_threshold"],
                     "HGP_RETAINED_BYTES_STOP")
                work = out / (case + "_%02d" % i)
                work.mkdir()
                inputs = prep.prepare_inputs(original, case)
                need({k: prep.sha(v) for k, v in inputs.items()} == receipt["cases"][case],
                     "HGP_CASE_HASH_DRIFT")
                for name, raw in inputs.items():
                    with (work / name).open("xb") as f:
                        f.write(raw)
                need(retained_bytes(out) < a["retained_bytes_stop_threshold"],
                     "HGP_RETAINED_BYTES_STOP_BEFORE_LAUNCH")
                need(prep.file_sha(runtime["binary"]) == runtime["binary_sha256"],
                     "HGP_BINARY_DRIFT_BEFORE_LAUNCH")
                launched += 1  # attempted launch; actual PID recorded by LAUNCH.json
                launch(Path(runtime["binary"]), work, a)
                prn = work / "bl691_MEEMUM.prn"
                need(prn.is_file() and not prn.is_symlink(), "HGP_NATIVE_PRN_MISSING")
                readback = prep.native_observation(prn.read_bytes())
                need("Fsp(C1)" not in readback["printed_rows"], "HGP_STALE_C1_OUTPUT")
                write_json(work / "READBACK.json", readback)
                observations[case].append(readback)
                need(retained_bytes(out) < a["retained_bytes_stop_threshold"],
                     "HGP_RETAINED_BYTES_STOP_AFTER_LAUNCH")
            repeatability[case] = prep.compare_observations(*observations[case],
                                                           same_configuration=True)
            write_json(out / (case + "_REPEAT.json"), repeatability[case])
            need(repeatability[case]["printed_rows_identical"],
                 "HGP_PRINTED_REPEAT_REVIEW")
        comparisons = {}
        if a["stage"] == "AB":
            comparisons["S2_to_A"] = prep.compare_observations(
                reference, observations[STAGE_AB[0]][0], same_configuration=False)
            comparisons["A_to_B"] = prep.compare_observations(
                observations[STAGE_AB[0]][0], observations[STAGE_AB[1]][0],
                same_configuration=False)
        else:
            comparisons["A_to_C"] = prep.compare_observations(
                ab["observations"][STAGE_AB[0]][0], observations[STAGE_C[0]][0],
                same_configuration=False)
        write_json(out / "RESULT.json", {
            "stage": a["stage"], "receipt_git_blob": RECEIPT_BLOB,
            "observations": observations, "repeatability": repeatability,
            "comparisons": comparisons, "science": "UNKNOWN",
            "numeric_acceptance": "NOT_RATIFIED"})
        seal(out, "HGP_" + a["stage"] + "_DIAGNOSTIC_COMPLETE", head, launched)
    except BaseException as exc:
        if not (out / "MANIFEST.json").exists():
            write_json(out / "FAILURE.json", {"type": type(exc).__name__,
                                             "message": str(exc), "launch_attempts": launched})
            seal(out, "HGP_ATTEMPT_FAILED_OR_REVIEW_REQUIRED", head, launched)
        raise
    print("HGP_" + a["stage"] + "_DIAGNOSTIC_COMPLETE")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--authorization", required=True, type=Path)
    p.add_argument("--ab-root", type=Path)
    p.add_argument("--ab-manifest-sha")
    args = p.parse_args()
    run(args.authorization, ab_root=args.ab_root, ab_manifest_sha=args.ab_manifest_sha)


if __name__ == "__main__":
    main()
