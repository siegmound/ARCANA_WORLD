from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import r6_si1_bandwidth_f2av_fair_diagnostics as f2av  # noqa: E402
import r6_si1_bandwidth_f2av_recover_evidence as recovery  # noqa: E402


def _parsed():
    return {"f2a":{"stage":{"nRank":"3","ku":"1"},"matrix":{},"scale":{},"forcing":{},"symmetry":{}},
        "records":{"BW1_F2AV_ASYMMETRY":{"count":1,"capacity":10,
                "zero_nonzero":0,"numeric_mismatch":1},
            "BW1_F2AV_DOMINANCE":{"strict":1,"near":0,"nonstrict":1,"undefined":1,
                "zero_diagonal":0,"zero_offdiag":0},
            "BW1_F2AV_SCALE_COUNTS":{"rows":3,"cols":3,"rows_zero":0,"cols_zero":0},
            "BW1_F2AV_NONFINITE":{"rows":0,"columns":0,"zero_rows":0,"zero_columns":0},
            "BW1_F2AV_SCALE_EXTREMA":{"rows":3,"columns":3}},
        "histograms":{},"ieee":{"inherited":{},"phases":[]}}


def test_recovery_without_sealed_f2a_reference_is_blocked_and_source_is_unchanged(tmp_path,monkeypatch):
    source=tmp_path/"original"; (source/"run_f2av").mkdir(parents=True)
    (source/"run_f2av"/"BW1_F2AV_ASYMMETRY_CENSUS.csv").write_text(
        "i,j,aij,aji,abs_delta,abs_delta_saturated,relative_delta,row_scaled_discrepancy,structure\n"
        "1,2,2.0E+000,3.0E+000,1.0E+000,3.3333333333333331E-001,0,1.0E-001,NONZERO_VALUE_MISMATCH\n",
        encoding="utf-8",newline="")
    (source/"run_f2av"/"BW1_F2AV_ROW_COLUMN_EXTREMES.csv").write_text("fixture\n",encoding="utf-8")
    (source/recovery.RESULT_NAME).write_text("{}\n",encoding="utf-8")
    original_bytes={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob("*") if p.is_file()}
    before=recovery._tree_identity(source)
    original={"failure":recovery.EXPECTED_FAILURE,"runtime":{"returncode":75}}
    identity={"manifest":{"verified":True,"sha256":"a"*64},
        "evidence_git":{"evidence_git_commit":recovery.EVIDENCE_GIT_COMMIT},
        "staged_inputs":{"verified":True,"file_count":8,"files":[]}}
    monkeypatch.setattr(recovery,"_verify_original",lambda *_:(original,"log",before,identity))
    monkeypatch.setattr(f2av,"parse_f2av_log",lambda _text:_parsed())
    monkeypatch.setattr(f2av,"read_f2av_extremes",lambda *_:{"rows":0,"counts_by_kind":{},"entries":[]})
    monkeypatch.setattr(f2av,"validate_auxiliary_reconciliation",lambda *_:None)
    monkeypatch.setattr(f2av,"verify_artifact_manifest",lambda *_args,**_kwargs:{"verified":True,"sha256":"a"*64})
    output=tmp_path/"recovered"
    result=recovery.recover_evidence(source,output)
    assert result["decision"]=="BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE", result
    assert result["original_decision_preserved"]==recovery.ORIGINAL_DECISION
    assert result["f2a_reference_comparison"]["verified"] is False
    assert result["original_evidence_reverified_after_processing"] is True
    assert {p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob("*") if p.is_file()}==original_bytes
    manifest=json.loads((output/"F2AV_RECOVERY_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    assert {item["path"] for item in manifest["artifacts"]}=={
        "BW1_F2AV_ASYMMETRY_CENSUS_NORMALIZED.csv","F2AV_RECOVERY_REPORT.md","F2AV_RECOVERY_RESULT.json"}


def test_output_cannot_overlap_or_replace_original_evidence(tmp_path):
    source=tmp_path/"sealed"; source.mkdir()
    with pytest.raises(recovery.RecoveryError,match="outside the original"):
        recovery.recover_evidence(source,source/"new-output")
    output=tmp_path/"existing"; output.mkdir()
    with pytest.raises(recovery.RecoveryError,match="fresh path"):
        recovery.recover_evidence(source,output)
