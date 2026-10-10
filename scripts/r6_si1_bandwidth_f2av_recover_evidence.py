#!/usr/bin/env python3
"""Read-only recovery of the historical F2A-V blocked assembly evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import r6_si1_bandwidth_f2av_fair_diagnostics as f2av  # noqa: E402

ORIGINAL_RUN_HEAD="df670c8c4faaed641997f5c4bdb701e2ba0afc7d"
EVIDENCE_GIT_COMMIT="f318a217dfee2f99d51e834948bcf765d5d45c6b"
ORIGINAL_DECISION="BLOCKED_F2AV_QUALIFICATION"
EXPECTED_FAILURE="F2AVError: invalid saturation indicator"
CENSUS_HEADER=["i","j","aij","aji","abs_delta","abs_delta_saturated","relative_delta","row_scaled_discrepancy","structure"]
RESULT_NAME="BW1_F2AV_RESULT.json"
MANIFEST_NAME="BW1_F2AV_ARTIFACT_MANIFEST.json"


class RecoveryError(RuntimeError):
    pass


def _sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_identity(root:Path)->dict[str,tuple[int,str]]:
    root=root.resolve()
    if root.is_symlink() or not root.is_dir():
        raise RecoveryError("source evidence root is missing or is a symlink")
    identity={}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RecoveryError(f"symlink in original evidence is not admissible: {path.relative_to(root)}")
        if path.is_file():
            rel=path.relative_to(root).as_posix()
            identity[rel]=(path.stat().st_size,_sha256(path))
        elif not path.is_dir():
            raise RecoveryError(f"non-regular object in original evidence: {path.relative_to(root)}")
    return identity


def _verify_evidence_git_anchor(commit:str,expected_parent:str)->dict[str,str]:
    try:
        kind=subprocess.run(["git","cat-file","-t",commit],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
        parents=subprocess.run(["git","show","-s","--format=%P",commit],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip().split()
    except (OSError,subprocess.CalledProcessError) as exc:
        raise RecoveryError(f"evidence Git commit could not be verified: {commit}") from exc
    if kind!="commit" or parents!=[expected_parent]:
        raise RecoveryError("evidence Git commit is not a direct child of the original execution HEAD")
    return {"evidence_git_commit":commit,"object_type":kind,"parent":parents[0]}


def normalize_historical_census(source:Path,destination:Path)->dict[str,Any]:
    """Swap historical CSV fields 6/7 into a new canonical-order file."""
    if destination.exists() or destination.is_symlink():
        raise RecoveryError("normalized census destination must be new")
    destination.parent.mkdir(parents=True,exist_ok=True)
    count=0
    with source.open("r",encoding="utf-8-sig",newline="") as inp:
        reader=csv.reader(inp)
        header=next(reader,None)
        if header!=CENSUS_HEADER:
            raise RecoveryError("historical census header does not match the canonical schema")
        with destination.open("w",encoding="utf-8",newline="") as out:
            writer=csv.writer(out,lineterminator="\n")
            writer.writerow(header)
            for row in reader:
                if len(row)!=len(CENSUS_HEADER):
                    raise RecoveryError(f"historical census row {count+2} has {len(row)} columns")
                row[5],row[6]=row[6],row[5]
                writer.writerow(row)
                count+=1
    return {"source_sha256":_sha256(source),"normalized_sha256":_sha256(destination),
            "rows":count,"field_repair":"swap historical fields 6 and 7 only",
            "header":CENSUS_HEADER}


def _verify_original(root:Path,evidence_git_commit:str)->tuple[dict[str,Any],str,dict[str,tuple[int,str]],dict[str,Any]]:
    root=root.resolve()
    before=_tree_identity(root)
    manifest=f2av.verify_artifact_manifest(root,MANIFEST_NAME)
    result_path=root/RESULT_NAME
    result=json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("decision")!=ORIGINAL_DECISION or result.get("failure")!=EXPECTED_FAILURE:
        raise RecoveryError("original blocked F2A-V result identity/verdict changed")
    repository=result.get("repository",{})
    if repository.get("head")!=ORIGINAL_RUN_HEAD or repository.get("branch")!="r6/si1-bandwidth-f2av":
        raise RecoveryError("original run source branch/HEAD does not match the qualified run")
    if result.get("compile_only") is not False or result.get("solver_executed") is not False or result.get("factorization_executed") is not False:
        raise RecoveryError("original result does not establish a non-solver runtime")
    runtime=result.get("runtime",{})
    if runtime.get("returncode")!=f2av.F2AV_EXIT:
        raise RecoveryError("original MPI exit code is not 75")
    if runtime.get("command")!=["mpiexec","-n","2","./ShellSet.exe","-Iter","1","-InOpt","List","-Dir","RUN_OUTPUT"]:
        raise RecoveryError("original MPI command differs from the archived valid-path invocation")
    log_path=root/"logs"/"f2av_mpi_combined.log"
    if not log_path.is_file() or _sha256(log_path)!=runtime.get("log_sha256"):
        raise RecoveryError("original MPI log is missing or differs from its recorded SHA256")
    log=log_path.read_text(encoding="utf-8",errors="strict")
    if log.count("ERROR STOP 75")!=1 or log.count(f2av.F2AV_MARKER)!=1 or log.count(f2av.f2a.MARKER)!=1:
        raise RecoveryError("original MPI log lacks unique F2A/F2A-V stop markers")
    if "BW1_F2A_STOP_BEFORE_SOLVER" not in log or "BW1_F2AV_STOP_BEFORE_SOLVER" not in log:
        raise RecoveryError("original MPI log lacks explicit pre-Solver stop records")
    staged_hashes=result.get("staged_input_hashes_before")
    if not isinstance(staged_hashes,dict) or not staged_hashes:
        raise RecoveryError("original result does not record staged-input hashes")
    staged_verification=f2av.verify_staged_inputs(root/"run_f2av",staged_hashes)
    recovery_provenance=result.get("provenance",{}).get("f2a_recovery",{})
    expected_recovery_identity={
        "original_manifest_sha256":f2av.F2A_ORIGINAL_MANIFEST_SHA256,
        "manifest_sha256":f2av.F2A_RECOVERY_MANIFEST_SHA256,
        "original_run_source_commit":f2av.F2A_ORIGINAL_RUN_COMMIT,
        "result_sha256":"5dde558e5f5e8710262c6d3f72b7f909337627169004d37e73bc4055968fe762",
    }
    for key,expected in expected_recovery_identity.items():
        if recovery_provenance.get(key)!=expected:
            raise RecoveryError(f"original F2A-V record has inconsistent sealed F2A recovery provenance: {key}")
    anchor=_verify_evidence_git_anchor(evidence_git_commit,ORIGINAL_RUN_HEAD)
    return result,log,before,{"manifest":manifest,"evidence_git":anchor,"staged_inputs":staged_verification}


def _verify_f2a_reference(reference_root:Path,parsed:dict[str,Any],expected_result_sha256:str)->dict[str,Any]:
    reference_root=reference_root.resolve()
    manifest=f2av.verify_artifact_manifest(reference_root,"F2A_RECOVERY_ARTIFACT_MANIFEST.json",
        expected_sha256=f2av.F2A_RECOVERY_MANIFEST_SHA256)
    result_path=reference_root/"F2A_RECOVERY_RESULT.json"
    document=json.loads(result_path.read_text(encoding="utf-8"))
    result_sha256=_sha256(result_path)
    if result_sha256!=expected_result_sha256:
        raise RecoveryError("sealed F2A recovery result SHA256 differs from the value recorded by the original F2A-V run")
    provenance=f2av.validate_recovery_source_provenance(document)
    diagnostics=document.get("diagnostics")
    if not isinstance(diagnostics,dict):
        raise RecoveryError("sealed F2A recovery result has no diagnostic reference values")
    comparison=f2av.validate_f2a_reassembly(parsed["f2a"],diagnostics)
    return {"verified":True,"manifest":manifest,"result_sha256":result_sha256,
            "provenance":provenance,"reassembly_comparison":comparison}


def _write_output_manifest(output:Path)->str:
    artifacts=[]
    for path in sorted((item for item in output.rglob("*") if item.is_file() and item.name!="F2AV_RECOVERY_ARTIFACT_MANIFEST.json"),
                       key=lambda item:item.relative_to(output).as_posix()):
        artifacts.append({"path":path.relative_to(output).as_posix(),"bytes":path.stat().st_size,"sha256":_sha256(path)})
    document={"schema":"arcana_worldsim.r6.si1_f2av_offline_recovery_manifest.v1",
              "membership":"all regular files except this manifest","artifacts":artifacts}
    path=output/"F2AV_RECOVERY_ARTIFACT_MANIFEST.json"
    path.write_text(json.dumps(document,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    return _sha256(path)


def recover_evidence(source_root:Path,output_root:Path,*,f2a_recovery_root:Path|None=None,
                     evidence_git_commit:str=EVIDENCE_GIT_COMMIT)->dict[str,Any]:
    source_root=source_root.resolve(); output_root=output_root.resolve()
    if (output_root.exists() or output_root.is_symlink() or source_root==output_root or
            source_root in output_root.parents or output_root in source_root.parents or f2av._has_symlinked_parent(output_root)):
        raise RecoveryError("output root must be a fresh path outside the original evidence bundle")
    if f2a_recovery_root is not None:
        f2a_resolved=f2a_recovery_root.resolve()
        if f2a_resolved==output_root or f2a_resolved in output_root.parents or output_root in f2a_resolved.parents:
            raise RecoveryError("output root overlaps the sealed F2A recovery evidence")
    result:dict[str,Any]={"schema":"arcana_worldsim.r6.si1_f2av_offline_recovery.v1",
        "source_execution_head":ORIGINAL_RUN_HEAD,"source_evidence_git_commit":evidence_git_commit,
        "original_decision_preserved":ORIGINAL_DECISION,"solver_executed":False,
        "offline_only":True,"canonical_state_changed":False}
    normalized_tmp=output_root.parent/(output_root.name+".normalized.tmp")
    if normalized_tmp.exists():
        raise RecoveryError("temporary normalization path already exists")
    try:
        original,log,before,identity=_verify_original(source_root,evidence_git_commit)
        parsed=f2av.parse_f2av_log(log)
        asym=parsed["records"]["BW1_F2AV_ASYMMETRY"]
        raw_census=source_root/"run_f2av"/"BW1_F2AV_ASYMMETRY_CENSUS.csv"
        normalized_tmp.mkdir(parents=True)
        census_meta=normalize_historical_census(raw_census,normalized_tmp/"BW1_F2AV_ASYMMETRY_CENSUS.csv")
        census=f2av.read_f2av_census(normalized_tmp/"BW1_F2AV_ASYMMETRY_CENSUS.csv",
            asym["count"],asym["capacity"],n_rank=int(parsed["f2a"]["stage"]["nRank"]),
            ku=int(parsed["f2a"]["stage"]["ku"]))
        extremes=f2av.read_f2av_extremes(source_root/"run_f2av"/"BW1_F2AV_ROW_COLUMN_EXTREMES.csv",
            int(parsed["f2a"]["stage"]["nRank"]))
        f2av.validate_auxiliary_reconciliation(parsed,census,extremes)
        result.update({"original_result_sha256":_sha256(source_root/RESULT_NAME),
            "original_manifest":identity["manifest"],"evidence_git_anchor":identity["evidence_git"],
            "staged_inputs_verified":identity["staged_inputs"],
            "source_failure_preserved":original["failure"],"source_runtime":original["runtime"],
            "census_normalization":census_meta,"census_validation":census,
            "extremes_validation":extremes,"histograms":parsed["histograms"],
            "diagnostics":{"stage":parsed["f2a"]["stage"],"matrix":parsed["f2a"]["matrix"],
                "scale":parsed["f2a"]["scale"],"forcing":parsed["f2a"]["forcing"],
                "symmetry":parsed["f2a"]["symmetry"],"asymmetry":asym,
                "dominance":parsed["records"]["BW1_F2AV_DOMINANCE"],
                "scale_counts":parsed["records"]["BW1_F2AV_SCALE_COUNTS"],
                "nonfinite":parsed["records"]["BW1_F2AV_NONFINITE"],
                "scale_extrema":parsed["records"]["BW1_F2AV_SCALE_EXTREMA"],
                "ieee":parsed["ieee"]}})
        if f2a_recovery_root is None or not f2a_recovery_root.is_dir():
            result["decision"]="BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE"
            result["failure"]="sealed F2A recovery result/manifest unavailable; reassembly equivalence cannot be established"
            result["f2a_reference_comparison"]={"verified":False,"status":"UNAVAILABLE"}
        else:
            expected_recovery_sha=original.get("provenance",{}).get("f2a_recovery",{}).get("result_sha256")
            if not isinstance(expected_recovery_sha,str):
                raise RecoveryError("original F2A-V provenance has no sealed F2A recovery result identity")
            result["f2a_reference_comparison"]=_verify_f2a_reference(f2a_recovery_root,parsed,expected_recovery_sha)
            result["decision"]="F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION"
        after=_tree_identity(source_root)
        if before!=after:
            raise RecoveryError("original F2A-V evidence changed during offline processing")
        final_manifest=f2av.verify_artifact_manifest(source_root,MANIFEST_NAME)
        if final_manifest["sha256"]!=identity["manifest"]["sha256"]:
            raise RecoveryError("original artifact manifest changed during offline processing")
        result["original_evidence_reverified_after_processing"]=True
        result["original_file_count"] = len(after)
        output_root.mkdir(parents=True)
        os.replace(normalized_tmp/"BW1_F2AV_ASYMMETRY_CENSUS.csv",output_root/"BW1_F2AV_ASYMMETRY_CENSUS_NORMALIZED.csv")
        normalized_tmp.rmdir()
    except Exception as exc:
        if normalized_tmp.exists():
            for path in normalized_tmp.iterdir():
                if path.is_file(): path.unlink()
            normalized_tmp.rmdir()
        result.setdefault("decision","BLOCKED_F2AV_OFFLINE_RECOVERY")
        result["failure"]=f"{type(exc).__name__}: {exc}"
        output_root.mkdir(parents=True,exist_ok=True)
    result_path=output_root/"F2AV_RECOVERY_RESULT.json"
    result_path.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    report=("# F2A-V Offline Recovery\n\n"
        f"Decision: `{result['decision']}`\n\n"
        f"Original execution HEAD: `{ORIGINAL_RUN_HEAD}`; evidence commit: `{evidence_git_commit}`.\n\n"
        f"Original verdict preserved: `{result.get('original_decision_preserved')}`.\n\n"
        f"F2A comparison: `{result.get('f2a_reference_comparison',{}).get('status', 'VERIFIED' if result.get('f2a_reference_comparison',{}).get('verified') else 'NOT_COMPLETED')}`.\n\n"
        f"Failure/blocker: {result.get('failure','none')}\n")
    (output_root/"F2AV_RECOVERY_REPORT.md").write_text(report,encoding="utf-8",newline="\n")
    manifest_sha256=_write_output_manifest(output_root)
    # Keep the manifest digest outside the manifest-covered result to avoid a self-reference.
    print(f"F2AV_RECOVERY_ARTIFACT_MANIFEST_SHA256={manifest_sha256}")
    return result


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-evidence-root",type=Path,required=True)
    parser.add_argument("--f2a-recovery-root",type=Path)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--evidence-git-commit",default=EVIDENCE_GIT_COMMIT)
    args=parser.parse_args(argv)
    try:
        report=recover_evidence(args.source_evidence_root,args.output_dir,
            f2a_recovery_root=args.f2a_recovery_root,evidence_git_commit=args.evidence_git_commit)
    except RecoveryError as exc:
        print(f"BLOCKED_F2AV_OFFLINE_RECOVERY: {exc}",file=sys.stderr)
        return 2
    print(report["decision"])
    if report["decision"]!="F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION":
        print(report.get("failure","recovery is incomplete"),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
