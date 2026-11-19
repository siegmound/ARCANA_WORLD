#!/usr/bin/env python3
"""Prepared explicit-only bounded P1 qualification. CREATED_NOT_RUN at delivery.

No numerical imports or tests occur without --execute-manufactured-method-tests.
The CLI has no input-dataset, arbitrary mesh, 1000Y/10k/100k or production mode.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from xml.etree import ElementTree


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def check_pins(work, contract):
    for name, expected in {**contract["new_file_pins"], **contract["preserved_source_pins"]}.items():
        if sha(work / name) != expected:
            raise ValueError("QUALIFICATION_SOURCE_MISMATCH: " + name)


def process_tree_rss(pid):
    """Sample descendants; shared session/cgroup memory is not process RSS."""
    queue, seen, rss_kib = [pid], set(), 0
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        try:
            lines = Path(f"/proc/{current}/status").read_text().splitlines()
            for line in lines:
                if line.startswith("VmRSS:"):
                    rss_kib += int(line.split()[1])
            queue.extend(map(int, Path(f"/proc/{current}/task/{current}/children").read_text().split()))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return {"process_ids": sorted(seen), "sampled_tree_rss_kib": rss_kib}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-contract-sha256", required=True)
    parser.add_argument("--execute-manufactured-method-tests", action="store_true")
    args = parser.parse_args()
    if not args.execute_manufactured_method_tests:
        parser.error("explicit bounded-test opt-in required; delivery does not execute qualification")
    work = Path(__file__).resolve().parents[1]
    contract_path = work / "experiments/hr2_p1/SOURCE_CONTRACT.json"
    if sha(contract_path) != args.expected_contract_sha256:
        raise ValueError("REVIEWED_SOURCE_CONTRACT_SHA256_MISMATCH")
    contract = json.loads(contract_path.read_bytes())
    check_pins(work, contract)  # Before any model/pytest process exists.
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    save(output / "INVOCATION.json", {"argv": sys.argv, "contract_sha256": sha(contract_path),
        "source_contract": contract, "head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=work, text=True).strip(),
        "scope": "BOUNDED_MANUFACTURED_METHOD_ONLY", "original_archives_read": False})
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join([str(work / "src"), str(work / "experiments")]),
                   "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
                   "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "HR2_P1_QUAL_OUTPUT": str(output)}
    tests = [str(work / name) for name in contract["test_files"]]
    command = [sys.executable, "-B", "-m", "pytest", "-c", "/dev/null", "-o", "addopts=",
               "--noconftest", "-p", "no:cacheprovider", "--confcutdir=" + str(work / "experiments/hr2_p1_checks"),
               "--basetemp=" + str(output / "pytest-tmp"), "--junitxml=" + str(output / "JUNIT.xml"),
               "-q", *tests]
    started = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    with (output / "PYTEST.stdout").open("xb") as stdout, (output / "PYTEST.stderr").open("xb") as stderr:
        child = subprocess.Popen(command, cwd=work, env=environment, stdout=stdout, stderr=stderr)
        with (output / "RESOURCE_SAMPLES.jsonl").open("x") as samples:
            while child.poll() is None:
                samples.write(json.dumps({"elapsed_s": time.perf_counter() - started,
                                           **process_tree_rss(child.pid)}) + "\n")
                samples.flush()
                time.sleep(.25)
        code = child.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    check_pins(work, contract)
    names, failures = set(), []
    path = output / "JUNIT.xml"
    if path.is_file():
        for case in ElementTree.parse(path).getroot().iter("testcase"):
            names.add(case.attrib["name"].split("[", 1)[0])
            if any(case.find(key) is not None for key in ["failure", "error", "skipped"]):
                failures.append(case.attrib["name"])
    required = set(contract["required_test_functions"])
    metrics = ["SPATIAL_CONVERGENCE_latitude.json", "SPATIAL_CONVERGENCE_longitude.json",
               "TEMPORAL_CONVERGENCE.json", "NATIVE_B0_SERVICE_PROFILE.json"]
    complete = (code == 0 and required <= names and not failures
                and all((output / name).is_file() for name in metrics))
    marker = ("HR2_P1=PASS_MANUFACTURED_SPHERICAL_DIFFUSION_CONSERVATION_AND_CONVERGENCE"
              if complete else "HR2_P1=BLOCKED_BOUNDED_METHOD_TEST_OR_EVIDENCE_INCOMPLETE")
    save(output / "RESULT.json", {"marker": marker, "pytest_exit": code, "failing_or_skipped": failures,
        "missing_tests": sorted(required - names), "required_metric_files": metrics,
        "wall_observed_s": time.perf_counter() - started, "cpu_user_s": after.ru_utime - before.ru_utime,
        "cpu_system_s": after.ru_stime - before.ru_stime,
        "sampling": "0.25s process-tree RSS; <=0.25s exit-observation slack; no disk-cold claim",
        "scientific_authority": False, "production_authority": False,
        "crash_linked_tail_qualified": False, "global_T0_input_admission": False,
        "six_grid_physical_qualification": False, "new_long_run_authorized": False})
    members = [{"path": str(p.relative_to(output)), "bytes": p.stat().st_size, "sha256": sha(p)}
               for p in sorted(output.rglob("*")) if p.is_file()]
    save(output / "MANIFEST.json", {"kind": "BOUNDED_MANUFACTURED_P1_METHOD_EVIDENCE", "members": members})
    print(marker, flush=True)
    return 0 if complete else (code or 4)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("HR2_P1=BLOCKED_PRECONDITION_OR_RUNNER_ERROR", type(exc).__name__, str(exc), flush=True)
        raise SystemExit(4)
