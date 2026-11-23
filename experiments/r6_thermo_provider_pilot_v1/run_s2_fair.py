"""ARCANA R6 S2 write-once FAIR runner, candidate; explicitly invoked only.

Two phases:
 --phase preflight : source-bound pure software tests; no thermodynamic engine.
 --phase run       : five fresh Julia and five fresh Perple_X MEEMUM processes.
No command runs on import. Never touch S1 or re-use evidence paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

from experiments.r6_thermo_provider_pilot_v1.s2_repro_protocol import load, check
from experiments.r6_thermo_provider_pilot_v1.validate_s2_native import (
    check_perplex_native_prn, read_magemin,
    compare_magemin_runs, compare_perplex_runs,
)

BASE = Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6")
S1 = BASE / "R6_THERMO_EXTERNAL_OFFICIAL_NEW02"
PRE = BASE / "R6_THERMO_S2_SOFTWARE_PREFLIGHT_NEW01"
OUT = BASE / "R6_THERMO_S2_REPEATABILITY_NEW01"
SOURCE_PATHS = [
    "experiments/r6_thermo_provider_pilot_v1/run_magemin_s2_native.jl",
    "experiments/r6_thermo_provider_pilot_v1/validate_s2_native.py",
    "experiments/r6_thermo_provider_pilot_v1/run_s2_fair.py",
    "experiments/r6_thermo_provider_pilot_v1/s2_repro_protocol.py",
    "experiments/r6_thermo_provider_pilot_v1/s2_repeatability_protocol_v1.json",
    "experiments/r6_thermo_provider_pilot_v1/run_perplex_official.py",
    "experiments/r6_thermo_provider_pilot_v1/pilot.py",
    "tests/test_r6_thermo_s2_protocol_v1.py",
    "tests/test_r6_thermo_s2_native_v1.py",
]
PYTEST = [
    "tests/test_r6_thermo_provider_pilot.py",
    "tests/test_r6_thermo_s1_v2.py",
    "tests/test_r6_thermo_s2_protocol_v1.py",
    "tests/test_r6_thermo_s2_native_v1.py",
]

class S2RunnerError(RuntimeError):
    pass

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True, stderr=subprocess.PIPE
    ).strip()

def write_json(path: Path, value: dict) -> None:
    # All work-directory filenames are new and never replaced.
    with path.open("x", encoding="utf-8") as file:
        json.dump(value, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")

def verify_checkout() -> tuple[Path, str]:
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
    check(root == Path.cwd().resolve(), "S2_MUST_RUN_FROM_REPO_ROOT")
    check(sys.executable.endswith("/arcana-r6-linux/bin/python"),
          "S2_PYTHON_ENVIRONMENT_NOT_ISOLATED")
    check(not git(root, "status", "--porcelain", "--untracked-files=no"),
          "S2_TRACKED_FILES_DIRTY")
    code_sha = git(root, "rev-parse", "HEAD")
    check(len(code_sha) == 40, "S2_SOURCE_GIT_SHA_INVALID")
    load()
    return root, code_sha

def verify_s1(policy: dict) -> str:
    manifest = S1/"MANIFEST.json"
    check(manifest.is_file() and
          sha(manifest) == policy["s1_evidence_manifest_sha256"],
          "S2_S1_MANIFEST_SHA_NOT_PINNED")
    m = json.loads(manifest.read_text())
    check(m["schema"] == "ARCANA_R6_THERMO_S1_CORRECTED_REAL_EXECUTION_V2"
          and m["source_R6_git_head"] == policy["s1_source_sha"]
          and m["physical_T1"] is None and m["D_024"] == "ACTIVE",
          "S2_ORIGIN_S1_EVIDENCE_SCOPE_INVALID")
    check(len(m["files_sha256"]) == 13, "S2_ORIGIN_S1_FILE_COUNT_DRIFT")
    for rel, expected in m["files_sha256"].items():
        src = (S1/rel).resolve()
        check(src.is_relative_to(S1) and src.is_file() and sha(src) == expected,
              "S2_ORIGIN_S1_MEMBER_DRIFT: "+rel)
    return sha(manifest)

def target_file_hashes(root: Path) -> dict:
    return {rel:sha(root/rel) for rel in SOURCE_PATHS}

def verify_preflight(root: Path, code_sha: str) -> dict:
    check((PRE/"MANIFEST.json").is_file(), "S2_PREFLIGHT_ABSENT")
    p = json.loads((PRE/"MANIFEST.json").read_text())
    check(p.get("schema") == "ARCANA_R6_THERMO_S2_PREFLIGHT_V1"
          and p.get("decision") == "S2_SOURCE_CONTRACT_TESTS_PASS_ONLY"
          and p.get("code_sha") == code_sha
          and p.get("s2_real_runs") == 0,
          "S2_PREFLIGHT_NOT_SOURCE_BOUND")
    check(p.get("source_sha256") == target_file_hashes(root),
          "S2_POST_PREFLIGHT_SOURCE_DRIFT")
    check(p.get("pytest_stdout_sha256") == sha(PRE/"PYTEST.log"),
          "S2_PREFLIGHT_PYTEST_LOG_DRIFT")
    return p

def software_preflight(root: Path, code_sha: str, policy: dict) -> None:
    verify_s1(policy)
    check(not PRE.exists(), "S2_PREFLIGHT_WRITE_ONCE_ALREADY_EXISTS")
    PRE.mkdir(parents=False, exist_ok=False)
    env = os.environ.copy()
    env.update(PYTHONPATH=str(root/"src")+":"+str(root),
               PYTHONDONTWRITEBYTECODE="1",
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
               MKL_NUM_THREADS="1")
    with (PRE/"PYTEST.log").open("xb") as f:
        r = subprocess.run(
            [sys.executable,"-m","pytest","-q","-ra","--tb=short",*PYTEST],
            cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,
            timeout=300,check=False
        )
    print((PRE/"PYTEST.log").read_text(errors="replace"))
    check(r.returncode == 0, "S2_PREFLIGHT_PYTEST_FAIL_PRESERVE_PARTIAL")
    write_json(PRE/"MANIFEST.json", {
        "schema":"ARCANA_R6_THERMO_S2_PREFLIGHT_V1",
        "decision":"S2_SOURCE_CONTRACT_TESTS_PASS_ONLY",
        "code_sha":code_sha,
        "source_sha256":target_file_hashes(root),
        "pytest_stdout_sha256":sha(PRE/"PYTEST.log"),
        "s1_evidence_manifest_sha256":policy["s1_evidence_manifest_sha256"],
        "s2_real_runs":0,
        "physical_T1":None,"D_024":"ACTIVE",
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False
    })
    print("S2_SOURCE_PREFLIGHT_PASS")
    print("S2_PREFLIGHT_MANIFEST_SHA256="+sha(PRE/"MANIFEST.json"))

def real_runtime(root: Path, policy: dict) -> dict:
    env_names = [
        "JULIA_BIN","JULIA_PROJECT","JULIA_DEPOT_PATH",
        "PERPLEX_SOURCE","PERPLEX_MEEMUM","PERPLEX_RELEASE_ARCHIVE"
    ]
    runtime = {key:Path(os.environ.get(key,"")).expanduser().resolve()
               for key in env_names}
    for key in env_names:
        check(bool(os.environ.get(key)), "S2_MISSING_RUNTIME_"+key)
    jb,jp,jd = [runtime[k] for k in env_names[:3]]
    ps,pm,pa = [runtime[k] for k in env_names[3:]]
    check(jb.is_file() and os.access(jb,os.X_OK)
          and (jp/"Project.toml").is_file()
          and (jp/"Manifest.toml").is_file()
          and jd.is_dir() and ps.is_dir()
          and pm.is_file() and os.access(pm,os.X_OK)
          and pa.is_file(), "S2_RUNTIME_PATH_INVALID")
    version=subprocess.check_output([str(jb),"--version"],text=True).strip()
    check(version == "julia version "+policy["pins"]["julia_version"],
          "S2_JULIA_VERSION_DRIFT")
    raw=(jp/"Manifest.toml").read_text()
    check(policy["pins"]["magemin_c_upstream_commit"] in raw
          and policy["pins"]["magemin_jll_version"] in raw,
          "S2_MAGEMIN_MANIFEST_PIN_MISSING")
    check(git(ps,"rev-parse","HEAD")==policy["pins"]["perplex_source_commit"],
          "S2_PERPLEX_SOURCE_COMMIT_DRIFT")
    check(sha(pa)==policy["pins"]["perplex_linux_archive_sha256"],
          "S2_PERPLEX_ARCHIVE_SHA_DRIFT")
    # Source-backed original S1 Perple_X hash, NOT just an executable filename.
    s1_per=json.loads(
        (S1/"PERPLEX_BL691_MEEMUM/REPORT.json").read_text())
    check(sha(pm)==s1_per["meemum_binary_sha256"],
          "S2_PERPLEX_BINARY_SHA_DRIFT")
    return {key:str(val) for key,val in runtime.items()}

def launch(root: Path, command: list[str], run_dir: Path,
           env: dict, timeout: int) -> dict:
    check(run_dir.is_dir(), "S2_RUN_DIR_MISSING")
    start=time.monotonic()
    with (run_dir/"LAUNCH_STDOUT.log").open("xb") as f:
        process = subprocess.Popen(command,cwd=root,env=env,stdout=f,
                                   stderr=subprocess.STDOUT)
        pid=process.pid
        try:
            code=process.wait(timeout=timeout)
            timed_out=False
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            code=process.returncode
            timed_out=True
    info = {"pid":pid,"exit_code":code,"timeout":timed_out,
            "elapsed_s":time.monotonic()-start,
            "command":command}
    write_json(run_dir/"LAUNCH.json",info)
    check(code==0 and not timed_out,
          "S2_REAL_ENGINE_PROCESS_FAILED_PRESERVE_OUTPUT")
    return info

def run_real(root: Path, code_sha: str, policy: dict) -> None:
    pre=verify_preflight(root,code_sha)
    s1sha=verify_s1(policy)
    runtime=real_runtime(root,policy)
    check(not OUT.exists(), "S2_REAL_OUTPUT_WRITE_ONCE_ALREADY_EXISTS")
    env=os.environ.copy()
    env.update(PYTHONPATH=str(root/"src")+":"+str(root),
               PYTHONDONTWRITEBYTECODE="1",JULIA_NUM_THREADS="1",
               JULIA_NUM_PRECOMPILE_TASKS="1",JULIA_PKG_PRECOMPILE_AUTO="0",
               OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",
               MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False, exist_ok=False)
    try:
        write_json(OUT/"RUN_PROVENANCE.json",{
            "code_sha":code_sha,
            "source_sha256":target_file_hashes(root),
            "s2_protocol_sha256":sha(
                root/"experiments/r6_thermo_provider_pilot_v1/s2_repeatability_protocol_v1.json"),
            "s1_manifest_sha256":s1sha,
            "preflight_manifest_sha256":sha(PRE/"MANIFEST.json"),
            "runtime_paths":runtime,
            "julia_project_sha256":sha(Path(runtime["JULIA_PROJECT"])/"Project.toml"),
            "julia_manifest_sha256":sha(Path(runtime["JULIA_PROJECT"])/"Manifest.toml"),
            "meemum_sha256":sha(Path(runtime["PERPLEX_MEEMUM"])),
            "perplex_release_sha256":sha(Path(runtime["PERPLEX_RELEASE_ARCHIVE"])),
            "s2_engine_runs_planned":10,"D_024":"ACTIVE",
            "physical_T1":None,"WORLD_HISTORY_PRODUCTION_AUTHORIZED":False
        })
        mag=[]
        per=[]
        for index in range(policy["runs_per_case"]):
            n=index+1
            d=OUT/("MAGEMIN_%02d"%n)
            d.mkdir(exist_ok=False)
            command=[
                runtime["JULIA_BIN"],"--startup-file=no",
                "--project="+runtime["JULIA_PROJECT"],
                str(root/"experiments/r6_thermo_provider_pilot_v1/run_magemin_s2_native.jl"),
                str(d/"NATIVE.toml")
            ]
            launch(root,command,d,env,600)
            mag.append(read_magemin(d/"NATIVE.toml",policy))
            print("S2_FRESH_JULIA_PROCESS_PASS="+str(n),flush=True)
        for index in range(policy["runs_per_case"]):
            n=index+1
            d=OUT/("PERPLEX_%02d"%n)
            d.mkdir(exist_ok=False)
            command=[
                sys.executable,"-m",
                "experiments.r6_thermo_provider_pilot_v1.run_perplex_official",
                "--repo-root",str(root),
                "--perplex-source",runtime["PERPLEX_SOURCE"],
                "--meemum",runtime["PERPLEX_MEEMUM"],
                "--release-archive",runtime["PERPLEX_RELEASE_ARCHIVE"],
                "--output",str(d/"BL691_MEEMUM")
            ]
            launch(root,command,d,env,300)
            raw=d/"BL691_MEEMUM"
            report=json.loads((raw/"REPORT.json").read_text())
            check(report["status"]=="PERPLEX_ORIGINAL_MEEMUM_REFERENCE_NUMERICAL_PASS"
                  and report["physical_T1"] is None
                  and report["cross_provider_equivalence"] is False,
                  "S2_PERPLEX_REFERENCE_REPORT_INVALID")
            check(sha(raw/"bl691_MEEMUM.prn")==report["output_prn_sha256"]
                  and sha(raw/"RUN_STDOUT.log")==report["stdout_sha256"],
                  "S2_PERPLEX_NATIVE_HASH_MISMATCH")
            check(abs(report["official_P_bar"]-4000.0)<=
                  policy["perplex_tolerances"]["pressure_abs_bar"]
                  and abs(report["official_T_K"]-1050.0)<=
                  policy["perplex_tolerances"]["temperature_abs_kelvin"],
                  "S2_PERPLEX_PT_DRIFT")
            chemical=check_perplex_native_prn(
                (raw/"bl691_MEEMUM.prn").read_text(errors="replace"),policy)
            check(report["phase_wt_percent"]==chemical["phase_wt_percent"],
                  "S2_PERPLEX_REPORT_PHASE_DRIFT")
            entry={**chemical,"status":report["status"],
                   "official_P_bar":report["official_P_bar"],
                   "official_T_K":report["official_T_K"],
                   "raw_prn_sha256":report["output_prn_sha256"],
                   "raw_stdout_sha256":report["stdout_sha256"]}
            write_json(d/"CHEMICAL_AUDIT.json",entry)
            per.append(entry)
            print("S2_FRESH_MEEMUM_PROCESS_PASS="+str(n),flush=True)
        evaluation={
            "schema":"ARCANA_R6_THERMO_S2_REPRO_EVALUATION_V1",
            "status":"S2_FRESH_PROCESS_REPEATABILITY_AND_NATIVE_CHEMISTRY_SCREEN_PASS",
            "magemin_runs":len(mag),
            "perplex_runs":len(per),
            "magemin_stability":compare_magemin_runs(mag,policy),
            "perplex_stability":compare_perplex_runs(per,policy),
            "chemical_scope":"MAGEMIN_NATIVE_EXACT__PERPLEX_PRINTED_ROUNDING_ONLY",
            "cross_provider_equivalence":False,
            "D_024":"ACTIVE","physical_T1":None,
            "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False
        }
        write_json(OUT/"EVALUATION.json",evaluation)
        write_json(OUT/"STATUS.json",{
            "state":"S2_REPEATABILITY_UPSTREAM_EARTH_SCREEN_PASS",
            "science":"NO_INDEPENDENT_EXPERIMENTAL_VALIDATION",
            "D_024":"ACTIVE","physical_T1":None,
            "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False
        })
        files={str(p.relative_to(OUT)):sha(p)
               for p in sorted(OUT.rglob("*")) if p.is_file()}
        check(len(files)>=60,"S2_EVIDENCE_FILE_COVERAGE_TOO_SMALL")
        write_json(OUT/"MANIFEST.json",{
            "schema":"ARCANA_R6_THERMO_S2_REAL_REPEATABILITY_MANIFEST_V1",
            "source_sha":code_sha,
            "preflight_sha256":sha(PRE/"MANIFEST.json"),
            "protocol_sha256":sha(
                root/"experiments/r6_thermo_provider_pilot_v1/s2_repeatability_protocol_v1.json"),
            "evaluation_sha256":sha(OUT/"EVALUATION.json"),
            "files_sha256":files,
            "magemin_fresh_process_count":5,
            "perplex_fresh_meemum_process_count":5,
            "D_024":"ACTIVE","physical_T1":None,
            "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False
        })
        print("S2_REAL_ENGINE_REPEATABILITY_SCREEN_PASS")
        print("S2_REAL_MANIFEST_SHA256="+sha(OUT/"MANIFEST.json"))
    except BaseException as exc:
        # No deletion or retry; preserve the entire partial destination.
        write_json(OUT/"FAILURE.json",{
            "status":"S2_REAL_ATTEMPT_FAILED_PRESERVE_ALL_FILES",
            "error_type":type(exc).__name__,
            "error_message":str(exc),
            "traceback":traceback.format_exc(),
            "D_024":"ACTIVE","physical_T1":None,
            "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False
        })
        raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase",choices=("preflight","run"),required=True)
    args=p.parse_args()
    root,head=verify_checkout()
    policy=load()
    if args.phase=="preflight":
        software_preflight(root,head,policy)
    else:
        run_real(root,head,policy)

if __name__=="__main__":
    main()
