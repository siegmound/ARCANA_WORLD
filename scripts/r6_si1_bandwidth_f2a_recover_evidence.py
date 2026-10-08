#!/usr/bin/env python3
"""Read-only reconstruction of blocked F2A evidence into a separate sealed report."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import r6_si1_bandwidth_f2a_fair_diagnostics as f2a  # noqa: E402
import r6_si1_bandwidth_bw1_fair_preflight as bw1  # noqa: E402

F2A_TYPES={"heatmap":"xy","heatmap_valid":"xy","matrix_log10_abs":"x",
           "diagonal_log10_abs":"x","forcing_log10_abs":"x",
           "dominance_log10_ratio_quarter_decade":"x"}


class RecoveryError(RuntimeError):
    pass


def _safe_relative_parts(rel:Any,label:str)->tuple[str,...]:
    if not isinstance(rel,str) or not rel:
        raise RecoveryError(f"unsafe {label} path: expected a non-empty relative path")
    posix=PurePosixPath(rel)
    if (posix.is_absolute() or not posix.parts or
            any(part in ("", ".", "..") for part in posix.parts) or
            "\\" in rel or ":" in rel or posix.as_posix()!=rel):
        raise RecoveryError(f"unsafe {label} path: {rel!r}")
    return posix.parts


def _sha(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest()


def verify_source_manifest(root:Path)->dict[str,Any]:
    """Verify the immutable original bundle's manifest, hashes, and membership."""
    root=root.resolve(); manifest_path=root/"BW1_F2A_ARTIFACT_MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink(): raise RecoveryError("original F2A artifact manifest missing/unsafe")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    entries=manifest.get("artifacts")
    if manifest.get("schema")!="R6_SI1_BW1_F2A_ARTIFACT_MANIFEST_V1" or not isinstance(entries,list):
        raise RecoveryError("original F2A artifact manifest schema invalid")
    listed=set()
    for entry in entries:
        rel=entry.get("path")
        parts=_safe_relative_parts(rel,"manifest artifact")
        candidate=root.joinpath(*parts)
        resolved=candidate.resolve()
        if root not in resolved.parents or candidate.is_symlink() or not candidate.is_file(): raise RecoveryError(f"missing/unsafe manifest artifact: {rel}")
        if rel in listed: raise RecoveryError(f"duplicate manifest path: {rel}")
        if candidate.stat().st_size!=entry.get("bytes") or _sha(candidate)!=entry.get("sha256"):
            raise RecoveryError(f"original evidence hash/size mismatch: {rel}")
        listed.add(rel)
    actual=set()
    for path in root.rglob("*"):
        if path.is_symlink(): raise RecoveryError(f"symlink in original evidence bundle: {path.relative_to(root).as_posix()}")
        if path.is_file() and path.name!="BW1_F2A_ARTIFACT_MANIFEST.json":
            actual.add(path.relative_to(root).as_posix())
    if actual!=listed: raise RecoveryError("original bundle membership differs from manifest")
    return {"manifest_sha256":_sha(manifest_path),"manifest_artifact_count":len(entries),"membership_verified":True}


def read_aggregates(path:Path)->dict[str,Any]:
    """Read current 4-column CSV and recover the historical 3-column histogram rows."""
    with path.open(newline="",encoding="utf-8") as stream:
        reader=csv.reader(stream)
        header=next(reader,None)
        if header!=["kind","bin_x","bin_y","count"]: raise RecoveryError("aggregate CSV header differs from four-column contract")
        counts={kind:0 for kind in F2A_TYPES}; rows=0; legacy_hist_rows=0
        for line_number,fields in enumerate(reader,start=2):
            if not fields: raise RecoveryError(f"blank aggregate CSV row at line {line_number}")
            kind=fields[0]
            if kind not in F2A_TYPES: raise RecoveryError(f"unknown aggregate kind at line {line_number}: {kind!r}")
            if len(fields)==3 and F2A_TYPES[kind]=="x":
                _,bin_x,count=fields; bin_y=""; legacy_hist_rows+=1
            elif len(fields)==4:
                _,bin_x,bin_y,count=fields
            else: raise RecoveryError(f"wrong aggregate CSV column count at line {line_number}")
            if not re.fullmatch(r"[+-]?\d+",bin_x) or not re.fullmatch(r"\d+",count):
                raise RecoveryError(f"invalid bin/count at line {line_number}")
            if int(count)<0: raise RecoveryError(f"negative aggregate count at line {line_number}")
            if F2A_TYPES[kind]=="xy":
                if len(fields)!=4 or not re.fullmatch(r"\d+",bin_y): raise RecoveryError(f"heatmap bin_y missing/invalid at line {line_number}")
                if not (1<=int(bin_x)<=256 and 1<=int(bin_y)<=256): raise RecoveryError(f"heatmap bin outside 1..256 at line {line_number}")
            elif len(fields)==4 and bin_y!="":
                raise RecoveryError(f"histogram bin_y must be blank at line {line_number}")
            elif kind=="dominance_log10_ratio_quarter_decade" and not (1<=int(bin_x)<=130):
                raise RecoveryError(f"dominance histogram bin outside 1..130 at line {line_number}")
            elif kind!="dominance_log10_ratio_quarter_decade" and not (-323<=int(bin_x)<=308):
                raise RecoveryError(f"magnitude histogram bin outside -323..308 at line {line_number}")
            counts[kind]+=int(count); rows+=1
    if rows==0: raise RecoveryError("aggregate CSV contains no data rows")
    return {"row_count":rows,"legacy_three_column_histogram_rows":legacy_hist_rows,"summed_counts":counts,"sha256":_sha(path)}


def _expected_aggregate_counts(diag:dict[str,Any])->dict[str,int]:
    matrix=diag["matrix"]; scale=diag["scale"]; forcing=diag["forcing"]; stage=diag["stage"]
    return {"heatmap":int(matrix["nonzero"]),"heatmap_valid":int(matrix["valid"]),
            "matrix_log10_abs":int(matrix["nonzero"]),
            "diagonal_log10_abs":int(scale["diag_pos"])+int(scale["diag_neg"]),
            "forcing_log10_abs":int(forcing["nonzero"]),
            "dominance_log10_ratio_quarter_decade":int(stage["nRank"])}


def _verify_staged_files(root:Path,result:dict[str,Any])->dict[str,Any]:
    before=result.get("staged_input_hashes_before")
    if not isinstance(before,dict) or not before: raise RecoveryError("pre-run staged-input hashes are missing")
    evidence_root=root.resolve()
    staged_root=root/"run_f2a"
    if staged_root.is_symlink() or not staged_root.is_dir():
        raise RecoveryError("retained staged run_f2a directory missing/unsafe")
    staged_root=staged_root.resolve()
    if staged_root.parent!=evidence_root:
        raise RecoveryError("retained staged run_f2a directory escapes original evidence")
    def is_link_or_junction(path:Path)->bool:
        junction_check=getattr(path,"is_junction",None)
        return path.is_symlink() or (junction_check is not None and junction_check())
    checked=[]
    for rel,digest in before.items():
        if not isinstance(rel,str) or not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):
            raise RecoveryError("staged-input path/hash entry is malformed")
        parts=_safe_relative_parts(rel,"staged-input")
        path=staged_root.joinpath(*parts)
        # Reject links/reparse junctions at every component before opening the
        # file. This also avoids relying on Windows realpath permissions for
        # files while keeping the check lexically confined to run_f2a.
        cursor=staged_root
        for part in parts:
            cursor=cursor/part
            if is_link_or_junction(cursor): raise RecoveryError(f"symlink/junction in staged input path: {rel}")
        try:
            path.relative_to(staged_root)
        except ValueError as exc:
            raise RecoveryError(f"unsafe staged-input path: {rel!r}") from exc
        if not path.is_file(): raise RecoveryError(f"staged file unavailable: {rel}")
        if _sha(path)!=digest: raise RecoveryError(f"staged input changed since pre-run hash: {rel}")
        checked.append(rel)
    return {"verified_after_run_against_pre_run_hashes":len(checked),
            "all_recorded_inputs_preserved":True,"paths":sorted(checked),
            "posthoc_unreconstructible_controls":[
                "historical IEEE flag causal instruction/location",
                "whether corrected instrumentation clears IEEE flags on a fresh Fair run",
                "runtime conditions not captured in retained staged files, logs, or manifests"]}


def _verify_lock_provenance(root:Path,result:dict[str,Any])->dict[str,Any]:
    lock=json.loads(bw1.LOCK_PATH.read_text(encoding="utf-8"))
    build=result.get("instrumented_build",{})
    recorded=build.get("source_hashes")
    if recorded!=lock.get("files"): raise RecoveryError("recorded original ShellSet source hashes differ from current source lock")
    proof=build.get("instrumentation",{})
    if proof.get("original_sha256")!=lock.get("files",{}).get("src/MOD_Shells.f90"):
        raise RecoveryError("instrumentation original MOD_Shells hash differs from source lock")
    instrumented=root/"build_f2a"/"src"/"MOD_Shells.f90"
    if not instrumented.is_file() or instrumented.is_symlink() or _sha(instrumented)!=proof.get("instrumented_sha256"):
        raise RecoveryError("retained instrumented MOD_Shells source hash mismatch")
    f2a.inspect_instrumentation(instrumented.read_text(encoding="utf-8"))
    return {"locked_file_count":len(recorded),"source_lock_matches":True,
            "instrumented_source_hash_matches":True,"pre_solver_stop_static_audit":True,
            "parameter_reference_sha256":lock.get("parameter_reference_sha256"),
            "qualified_vendored_source_commit":lock.get("vendored_arcana_source_commit")}


def _write_manifest(out:Path)->str:
    name="F2A_RECOVERY_ARTIFACT_MANIFEST.json"; entries=[]
    for path in sorted((p for p in out.rglob("*") if p.is_file() and p.name!=name),key=lambda p:p.relative_to(out).as_posix().casefold()):
        entries.append({"path":path.relative_to(out).as_posix(),"bytes":path.stat().st_size,"sha256":_sha(path)})
    target=out/name
    target.write_text(json.dumps({"schema":"R6_SI1_BW1_F2A_RECOVERY_MANIFEST_V1","membership":"all regular files except this manifest","artifacts":entries},indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return _sha(target)


def recover(source_root:Path,f1_root:Path,output_dir:Path)->dict[str,Any]:
    source_root=source_root.resolve(); f1_root=f1_root.resolve(); output_dir=output_dir.resolve()
    if output_dir.exists(): raise RecoveryError("recovery output directory must be new")
    if source_root in output_dir.parents or output_dir in source_root.parents:
        raise RecoveryError("recovery output and immutable original evidence must be separate")
    source_manifest=verify_source_manifest(source_root)
    result_path=source_root/"BW1_F2A_RESULT.json"
    if not result_path.is_file(): raise RecoveryError("original F2A result JSON missing")
    original=json.loads(result_path.read_text(encoding="utf-8"))
    if original.get("decision")!="BLOCKED_BW1_F2A_NUMERICAL_CHARACTERIZATION":
        raise RecoveryError("source bundle is not the blocked F2A attempt to be recovered")
    if "KeyError" not in original.get("failure","") or "max_abs" not in original.get("failure",""):
        raise RecoveryError("source bundle is not the known parser-KeyError attempt")
    f1_provenance=f2a.validate_f1_evidence(f1_root)
    recorded_f1=original.get("f1_provenance",{})
    for key in ("source_commit","result_sha256","manifest_sha256"):
        if recorded_f1.get(key)!=f1_provenance.get(key): raise RecoveryError(f"embedded F1 provenance mismatch: {key}")
    if original.get("repository",{}).get("branch")!=f2a.EXPECTED_BRANCH:
        raise RecoveryError("original F2A branch provenance mismatch")
    head=original.get("repository",{}).get("head","")
    if not re.fullmatch(r"[0-9a-f]{40}",head): raise RecoveryError("original F2A source commit is missing/invalid")
    lock_provenance=_verify_lock_provenance(source_root,original)
    input_comparison=original.get("f1_input_identity_comparison",{})
    if input_comparison.get("equal") is not True: raise RecoveryError("recorded F1 input identity comparison did not pass")
    # Re-run the comparison from the preserved F1 result and F2A input validation payload.
    f2a._verify_f1_input_identity(f1_root,original.get("input_validation",{}))
    staged=_verify_staged_files(source_root,original)
    logs=list((source_root/"logs").glob("f2a_mpi_combined.log"))
    if len(logs)!=1: raise RecoveryError("original combined MPI log missing or ambiguous")
    log_path=logs[0]
    runtime=original.get("runtime",{})
    if _sha(log_path)!=runtime.get("log_sha256"): raise RecoveryError("MPI log SHA does not match blocked result metadata")
    if runtime.get("returncode")!=f2a.EXIT_CODE: raise RecoveryError("recorded MPI exit code is not intentional stop 75")
    log_text=log_path.read_text(encoding="utf-8",errors="replace")
    diagnostics=f2a.validate_fair_log(log_text,f2a.EXIT_CODE)
    csv_candidates=[p for p in (source_root/"run_f2a"/"BW1_F2A_AGGREGATES.csv",source_root/"BW1_F2A_AGGREGATES.csv") if p.is_file()]
    if len(csv_candidates)!=1: raise RecoveryError("original aggregate CSV is missing or ambiguous")
    aggregate=read_aggregates(csv_candidates[0])
    expected=_expected_aggregate_counts(diagnostics)
    if aggregate["summed_counts"]!=expected: raise RecoveryError("aggregate CSV sums disagree with parsed MPI diagnostics")
    aggregate["counts_match"]=True
    comparison=f2a.compare_reassembly_to_f1(diagnostics,f1_provenance["f1_reference_metrics"])
    if not comparison["nonzero_count_equal"] or not comparison["forcing_nonzero_equal"]:
        raise RecoveryError("reassembled matrix/forcing counts disagree with F1")
    report={"schema":"R6_SI1_BW1_F2A_OFFLINE_RECOVERY_V1",
        "decision":"RECOVERY_EVIDENCE_RECONSTRUCTED_REQUIRES_REVIEW",
        "source_f2a_decision_preserved":original["decision"],
        "source_evidence":{"bundle_name":source_root.name,"result_sha256":_sha(result_path),**source_manifest},
        "source_commit":head,"f1_provenance":f1_provenance,"shellset_source_lock":lock_provenance,
        "runtime":{"exit_code":runtime["returncode"],"log_sha256":_sha(log_path),"intentional_stop_validated":True,"solver_entered":False},
        "diagnostics":diagnostics,"aggregate_csv":{"bundle_relative_path":csv_candidates[0].relative_to(source_root).as_posix(),**aggregate,"expected_summed_counts":expected,"counts_match":True},
        "f1_comparison":comparison,"staged_input_preservation":staged,
        "ieee_warning_audit":{"observed_flags":["ieee_overflow","ieee_underflow","ieee_inexact"],
            "overflow":"The old symmetry saturation guard can overflow in HUGE/relative when 0 < relative < 1; the source correction removes that known avoidable operation, but the historical flag cannot be causally attributed from aggregate logs.",
            "underflow":"May arise from normalization/scaled accumulation of coefficients spanning extreme magnitudes; the exact operation is not logged, so attribution remains unresolved.",
            "inexact":"Expected from ordinary floating-point divisions, logarithms, and rounding in the diagnostics; it is not itself evidence of invalid output.",
            "historical_flag_causality_recoverable":False},
        "unrecoverable_checks":["causal location of historical IEEE flags","whether corrected instrumentation clears overflow/underflow flags on a fresh Fair execution"],
        "original_evidence_modified":False,"solver_or_factorization_executed":False,
        "interpretation":"This post-processing recovery validates retained records only. It does not change the original BLOCKED decision or grant F2A PASS."}
    output_dir.mkdir(parents=True,exist_ok=False)
    (output_dir/"F2A_RECOVERY_RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    md=["# F2A Offline Evidence Recovery","",f"Decision: `{report['decision']}`.","",
        f"Original F2A decision remains `{original['decision']}`; the historical result is unchanged.",
        f"Original result SHA256: `{report['source_evidence']['result_sha256']}`.",
        f"Original F2A manifest SHA256: `{report['source_evidence']['manifest_sha256']}`.",
        f"Recovered log and aggregate checks: `{len(diagnostics)} diagnostics`, `{aggregate['row_count']} CSV rows`, counts match `{aggregate['counts_match']}`.",
        "","IEEE flags are classified in the JSON, but their historical causal instruction is not recoverable from the retained logs. A new Fair run is required to test corrected instrumentation's runtime flags.",
        "","This report is post-processing evidence only. It does not convert the original blocked execution into a PASS.",""]
    (output_dir/"F2A_RECOVERY_RESULT.md").write_text("\n".join(md),encoding="utf-8",newline="\n")
    report["recovery_manifest_sha256"]=_write_manifest(output_dir)
    return report


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-evidence-root",type=Path,required=True)
    parser.add_argument("--f1-evidence-root",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        report=recover(args.source_evidence_root,args.f1_evidence_root,args.output_dir)
    except Exception as exc:
        print(f"BLOCKED_F2A_OFFLINE_RECOVERY: {type(exc).__name__}: {exc}",file=sys.stderr); return 2
    print(report["decision"]); print(f"F2A_RECOVERY_RESULT={args.output_dir/'F2A_RECOVERY_RESULT.json'}")
    print(f"F2A_RECOVERY_MANIFEST_SHA256={report['recovery_manifest_sha256']}")
    return 0


if __name__=="__main__": raise SystemExit(main())
