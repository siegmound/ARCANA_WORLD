from __future__ import annotations

import csv
import json
import math
import re
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import r6_si1_bandwidth_f2av_fair_diagnostics as f2av  # noqa: E402
import r6_si1_bandwidth_bw1_fair_preflight as bw1  # noqa: E402


def _band(matrix):
    # n=3, kl=ku=1, iDiagonal=2; row slots are one-based in the contract.
    return [[0.0,matrix[0][1],matrix[1][2]],
            [matrix[0][0],matrix[1][1],matrix[2][2]],
            [matrix[1][0],matrix[2][1],0.0]]


def _fortran_block_depth(fragment,kind):
    depth=0
    if kind=="IF":
        opener=re.compile(r"^\s*IF\b.*\bTHEN\s*$",re.I)
        closer=re.compile(r"^\s*END\s*IF\b",re.I)
        alternate=re.compile(r"^\s*ELSE\s*IF\b",re.I)
    else:
        opener=re.compile(r"^\s*DO\s+\w+\s*=",re.I)
        closer=re.compile(r"^\s*END\s*DO\b",re.I)
        alternate=None
    for number,line in enumerate(fragment.splitlines(),1):
        code=line.split("!",1)[0]
        if alternate and alternate.match(code):
            continue
        if closer.match(code):
            depth-=1
            assert depth>=0, f"unmatched END {kind} at generated line {number}"
        elif opener.match(code):
            depth+=1
    return depth


def test_small_band_symmetric_and_actual_lapack_band_indexing():
    matrix=[[4.0,2.0,0.0],[2.0,5.0,1.0],[0.0,1.0,6.0]]
    result=f2av.scan_small_band(_band(matrix),3,1,1,2)
    assert result["asymmetry_count"]==0
    assert result["row_scale"]==[4.0,5.0,6.0]
    assert result["column_scale"]==[4.0,5.0,6.0]


def test_small_band_finds_one_sided_and_multiple_asymmetries():
    one=[[4.0,2.0,0.0],[3.0,5.0,1.0],[0.0,1.0,6.0]]
    result=f2av.scan_small_band(_band(one),3,1,1,2)
    assert result["asymmetry_count"]==1
    pair=result["pairs"][0]
    assert (pair["i"],pair["j"],pair["structure"])==(1,2,"NONZERO_VALUE_MISMATCH")
    assert pair["aij"]==2 and pair["aji"]==3
    assert pair["relative_delta"]==pytest.approx(1/3)
    multiple=[[4.0,0.0,0.0],[3.0,5.0,1.0],[0.0,2.0,6.0]]
    result=f2av.scan_small_band(_band(multiple),3,1,1,2)
    assert result["asymmetry_count"]==2
    assert {pair["structure"] for pair in result["pairs"]}=={"ZERO_NONZERO","NONZERO_VALUE_MISMATCH"}


def test_small_band_capacity_fails_closed_and_indexing_is_validated():
    matrix=[[4.0,0.0,0.0],[3.0,5.0,1.0],[0.0,2.0,6.0]]
    with pytest.raises(f2av.F2AVError,match="capacity exceeded"):
        f2av.scan_small_band(_band(matrix),3,1,1,2,capacity=1)
    with pytest.raises(f2av.F2AVError,match="invalid band dimensions"):
        f2av.scan_small_band([[1.0]*3],3,1,1,2)
    with pytest.raises(f2av.F2AVError,match="invalid band dimensions"):
        f2av.scan_small_band(_band(matrix),3,0,1,2)


def test_zero_rows_columns_equal_dominance_and_stable_extremes():
    matrix=[[1.0,1.0,0.0],[1.0,2.0,0.0],[0.0,0.0,0.0]]
    result=f2av.scan_small_band(_band(matrix),3,1,1,2)
    dom=result["dominance"]
    assert dom["counts"]["near"]==1
    assert dom["counts"]["undefined"]==1
    assert dom["counts"]["zero_diagonal"]==1
    assert dom["counts"]["zero_offdiagonal"]==1
    extreme=[[1.0e308,1.0e-308,0.0],[1.0e-308,1.0e308,1.0e-308],[0.0,1.0e-308,1.0e308]]
    result=f2av.scan_small_band(_band(extreme),3,1,1,2)
    assert all(math.isfinite(value) for value in result["row_scaled_sum"])
    assert result["pairs"]==[]


def test_asymmetry_delta_saturates_without_overflow_and_rejects_nonfinite():
    maximum=float.fromhex("0x1.fffffffffffffp+1023")
    delta,saturated,relative=f2av.stable_abs_delta(maximum,-maximum)
    assert saturated and delta==maximum and relative==2.0
    tiny=float.fromhex("0x0.0000000000001p-1022")
    assert f2av.stable_abs_delta(tiny,0.0)==(tiny,False,1.0)
    with pytest.raises(f2av.F2AVError): f2av.stable_abs_delta(math.inf,0.0)
    with pytest.raises(f2av.F2AVError): f2av.scan_small_band(_band([[math.nan,0,0],[0,1,0],[0,0,1]]),3,1,1,2)


def test_dof_mapping_fails_closed_without_all_source_identities():
    assert f2av.assess_dof_mapping(None)["status"]=="DOF_MAPPING_UNVERIFIED"
    proof={"dof_formula":"2*node-1 / 2*node","component_basis_source_sha256":"a"*64,
           "node_permutation_sha256":"b"*64,"coordinate_mapping_sha256":"c"*64}
    assessed=f2av.assess_dof_mapping(proof)
    assert assessed["status"]=="DOF_MAPPING_UNVERIFIED"
    assert assessed["checks"]=={key:False for key in proof if key!="dof_formula"}
    assert assessed["untrusted_supplied_tokens"]["node_permutation_sha256"]=="b"*64


def test_ieee_phase_classification_separates_inherited_from_new():
    clean={name:False for name in f2av.IEEE_NAMES}
    inherited={**clean,"overflow":True}
    observed={**clean,"underflow":True}
    assert f2av.classify_ieee_flags(inherited,clean)=="INHERITED_ONLY_NOT_OBSERVED_IN_PHASES"
    assert f2av.classify_ieee_flags(clean,observed)=="FLAG_OBSERVED_IN_PHASE"
    assert f2av.classify_ieee_flags(clean,clean)=="NOT_OBSERVED"
    with pytest.raises(f2av.F2AVError): f2av.classify_ieee_flags({"overflow":False},{"overflow":False})


def test_fortran_generated_contract_marker_phases_format_and_line_limits():
    source=(bw1.SHELLSET_ROOT/"src"/"MOD_Shells.f90").read_text(encoding="utf-8")
    generated,proof=f2av.instrument_source_text(source)
    start,end,_,solver,_=f2av.f2a._fem_bounds(generated); block=generated[start:end]
    marker=block.index(f2av.F2AV_MARKER); stop=block.index("ERROR STOP 75",marker)
    assert marker<stop<solver
    assert block.count(f2av.F2AV_MARKER)==1
    assert "CALL Solver" not in block[marker:stop]
    assert not __import__("re").search(r"(?i)\b(?:DGBSV|DGESV)\b",block)
    assert all(len(line)<=132 for line in generated.splitlines() if "F2A-V" in line or "f2av_" in line or "BW1_F2AV" in line)
    assert proof["dof_mapping"]["status"]=="DOF_MAPPING_UNVERIFIED"
    assert generated.count("USE, INTRINSIC :: IEEE_ARITHMETIC") == 1
    for name in ("BuildF","BuildK","AddFSt","VBCs"):
        assert generated.index("CALL "+name)<generated.index("BW1_F2A_STAGE")
    assert "CALL IEEE_SET_FLAG(IEEE_OVERFLOW,.FALSE.)" in generated
    assert "CALL IEEE_SET_FLAG(IEEE_OVERFLOW,f2av_any(1))" in generated
    assert "f2av_rowdiag" not in generated
    assert generated.count("'BW1_F2AV_IEEE_INHERITED overflow='")==1
    assert generated.count("'BW1_F2AV_IEEE_PHASE phase_id='")==1
    assert "f2av_asym_roundoff" not in generated and "roundoff_class=" not in generated
    census_fmt="(I0,A,I0,4(A,ES24.16E3),A,I0,A,ES24.16E3,A,A)"
    descriptors=f2av.fortran_format_descriptors(census_fmt)
    assert descriptors==["I0","A","I0","A","ES24.16E3","A","ES24.16E3","A","ES24.16E3","A","ES24.16E3","A","I0","A","ES24.16E3","A","A"]
    assert generated.count("WRITE(78,'"+census_fmt+"')")==2
    assert "f2av_asym_n<=f2av_capacity .AND. f2av_asym_nonfinite==0" in generated


def test_pair_fragment_and_generated_matrix_scan_have_balanced_control_blocks():
    pair=f2av._f2av_pair_fortran()
    assert _fortran_block_depth(pair,"IF")==0
    source=(bw1.SHELLSET_ROOT/"src"/"MOD_Shells.f90").read_text(encoding="utf-8")
    generated,_=f2av.instrument_source_text(source)
    start=generated.index("DO f2a_j=1,nRank")
    phase5_end=generated.index("CALL IEEE_GET_FLAG(IEEE_OVERFLOW,f2av_phase_flags(5,1))",start)
    scan=generated[start:phase5_end]
    assert _fortran_block_depth(scan,"IF")==0
    assert _fortran_block_depth(scan,"DO")==0
    assert len(re.findall(r"(?im)^\s*DO\s+\w+\s*=",scan))==2
    assert len(re.findall(r"(?im)^\s*END\s*DO\b",scan))==2
    dominance=generated.index("! F2A-V finalize dominance and row/column statistics.")
    assert phase5_end<dominance


def test_strict_f2av_log_parser_and_malformed_record_rejection():
    n=128884; valid=n*(727+727+1)-727*728
    f2alog=(f"ERROR STOP 75\nBW1_F2A_STAGE nRank={n} nKRows=2182 kl=727 ku=727 iDiagonal=1455\n"
        f"BW1_F2A_MATRIX valid={valid} zero={valid-1} nonzero=1 nonfinite=0 fill_nonzero=0 fill_nonfinite=0 pad_nonzero=0 pad_nonfinite=0\n"
        "BW1_F2A_SCALE min_nonzero=1E+000 max_abs=2E+000 diag_pos=128884 diag_neg=0 diag_zero=0\n"
        "BW1_F2A_SYMMETRY max_abs=0E+000 max_relative=0E+000 compared_pairs=93434040 divergent_pairs=0 nonfinite_pairs=0\n"
        "BW1_F2A_DOMINANCE strict=128884 nonstrict=0\nBW1_F2A_FORCING zero=128883 nonzero=1 nonfinite=0 max_abs=1E+000\n"
        "BW1_F2A_RANGE coefficient_log10_max_min=0 forcing_min_nonzero=1 forcing_p50_log10_bin=0 forcing_p95_log10_bin=0\n"
        "BW1_F2A_SYMMETRY_WORST i=0 j=0 aij=0 aji=0\nBW1_F2A_AGGREGATES_WRITTEN=1\n"
        "BW1_F2A_RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING\nBW1_F2A_STOP_BEFORE_SOLVER\n")
    v=("BW1_F2AV_ASYMMETRY compared_pairs=93434040 count=0 capacity=100000 zero_nonzero=0 numeric_mismatch=0 nonfinite_pairs=0 complete=T\n"
       "BW1_F2AV_DOMINANCE strict=128884 near=0 nonstrict=0 undefined=0 zero_diagonal=0 zero_offdiag=0\n"
       "BW1_F2AV_SCALE_COUNTS rows_zero=0 cols_zero=0 rows=128884 cols=128884\n"
       "BW1_F2AV_NONFINITE rows=0 columns=0 zero_rows=0 zero_columns=0\n"
       "BW1_F2AV_SCALE_EXTREMA row_max=2E+000 row_min=2E+000 column_max=2E+000 column_min=2E+000 rows=128884 columns=128884\n"
       "BW1_F2AV_IEEE_INHERITED overflow=F underflow=F inexact=F\n")
    v+="".join(f"BW1_F2AV_IEEE_PHASE phase_id={i} overflow=F underflow=F inexact=F\n" for i in range(1,8))
    v+="BW1_F2AV_DOM_HIST bin=130 count=128884\n"
    for prefix in ("ROW_MAX","ROW_MIN","ROW_L1"):
        v+=f"BW1_F2AV_{prefix}_HIST bin=324 count=128884\n"
    for prefix in ("COL_MAX","COL_MIN","COL_L1"):
        v+=f"BW1_F2AV_{prefix}_HIST bin=324 count=128884\n"
    v+="BW1_F2AV_DOM_QUANTILES p05_bin=130 p50_bin=130 p95_bin=130 rows=128884\n"
    parsed=f2av.parse_f2av_log(f2alog+v+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    assert parsed["records"]["BW1_F2AV_ASYMMETRY"]["complete"]
    assert len(parsed["ieee"]["phases"])==7
    assert len([line for line in (f2alog+v).splitlines() if line.startswith("BW1_F2AV_IEEE_INHERITED ")])==1
    extremes={"counts_by_kind":{kind:16 for kind in ("ROW_MAX","COLUMN_MAX","ROW_MIN_NONZERO","COLUMN_MIN_NONZERO","WEAKEST_DIAGONAL_CONTRIBUTION")}}
    census={"classification_counts":{"ZERO_NONZERO":0,"NONZERO_VALUE_MISMATCH":0}}
    f2av.validate_auxiliary_reconciliation(parsed,census,extremes)
    broken_hist=v.replace("BW1_F2AV_ROW_MAX_HIST bin=324 count=128884","BW1_F2AV_ROW_MAX_HIST bin=324 count=128883",1)
    with pytest.raises(f2av.F2AVError,match="HIST sum"):
        f2av.parse_f2av_log(f2alog+broken_hist+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    broken_zero=v.replace("zero_rows=0","zero_rows=1",1)
    with pytest.raises(f2av.F2AVError,match="zero/nonfinite"):
        f2av.parse_f2av_log(f2alog+broken_zero+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    broken_nonfinite=v.replace("rows=0 columns=0","rows=2 columns=1",1)
    with pytest.raises(f2av.F2AVError,match="nonfinite coefficient totals"):
        f2av.parse_f2av_log(f2alog+broken_nonfinite+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    too_many_nonfinite=v.replace("rows=0 columns=0",f"rows={valid+1} columns={valid+1}",1)
    with pytest.raises(f2av.F2AVError,match="nonfinite coefficient totals"):
        f2av.parse_f2av_log(f2alog+too_many_nonfinite+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    broken_dom=v.replace("strict=128884","strict=128883",1)
    with pytest.raises(f2av.F2AVError,match="dominance classifications"):
        f2av.parse_f2av_log(f2alog+broken_dom+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    row_col_agree_but_base_differs=v.replace("rows=0 columns=0","rows=1 columns=1",1)
    with pytest.raises(f2av.F2AVError,match="zero/nonfinite coefficient totals"):
        f2av.parse_f2av_log(f2alog+row_col_agree_but_base_differs+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    asym_count_mismatch=v.replace("count=0 capacity=100000","count=1 capacity=100000",1).replace("numeric_mismatch=0","numeric_mismatch=1",1)
    with pytest.raises(f2av.F2AVError,match="divergent-pair count"):
        f2av.parse_f2av_log(f2alog+asym_count_mismatch+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    nonfinite_pair_mismatch=v.replace("nonfinite_pairs=0","nonfinite_pairs=1",1)
    nonfinite_pair_mismatch=nonfinite_pair_mismatch.replace("complete=T","complete=F",1)
    with pytest.raises(f2av.F2AVError,match="nonfinite pair count"):
        f2av.parse_f2av_log(f2alog+nonfinite_pair_mismatch+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    with pytest.raises(f2av.F2AVError,match="census classifications"):
        f2av.validate_auxiliary_reconciliation(parsed,{"classification_counts":{"ZERO_NONZERO":1,"NONZERO_VALUE_MISMATCH":0}},extremes)
    bad_extremes={"counts_by_kind":{**extremes["counts_by_kind"],"ROW_MAX":15}}
    with pytest.raises(f2av.F2AVError,match="ROW_MAX extreme-list"):
        f2av.validate_auxiliary_reconciliation(parsed,census,bad_extremes)
    with pytest.raises(f2av.F2AVError): f2av.parse_f2av_log(f2alog+v.replace("count=0 capacity", "count=0 count=1 capacity",1)+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    with pytest.raises(f2av.F2AVError): f2av.parse_f2av_log(f2alog+v.replace("near=0", "near=bad",1)+"BW1_F2AV_STOP_BEFORE_SOLVER\n")
    duplicate_inherited=v+"BW1_F2AV_IEEE_INHERITED overflow=F underflow=F inexact=F\n"
    with pytest.raises(f2av.F2AVError,match="exactly one BW1_F2AV_IEEE_INHERITED"):
        f2av.parse_f2av_log(f2alog+duplicate_inherited+"BW1_F2AV_STOP_BEFORE_SOLVER\n")


def test_manifest_and_staged_input_integrity_are_path_safe(tmp_path):
    root=tmp_path/"bundle"; root.mkdir(); content=root/"evidence.txt"; content.write_text("fixture\n",encoding="utf-8")
    digest=f2av._hash(content)
    manifest=root/"manifest.json"
    manifest.write_text(json.dumps({"membership":"all regular files except this manifest","artifacts":[{"path":"evidence.txt","bytes":content.stat().st_size,"sha256":digest}]}),encoding="utf-8")
    assert f2av.verify_artifact_manifest(root,"manifest.json")["verified"]
    run=tmp_path/"run"; (run/"INPUT").mkdir(parents=True); staged=run/"INPUT"/"data.dat"; staged.write_bytes(b"fixture")
    hashes={"INPUT/data.dat":f2av._hash(staged)}
    assert f2av.verify_staged_inputs(run,hashes)["file_count"]==1
    with pytest.raises(f2av.F2AVError,match="unsafe staged"):
        f2av.verify_staged_inputs(run,{"INPUT/../outside":hashes["INPUT/data.dat"]})
    with pytest.raises(f2av.F2AVError,match="hash mismatch"):
        f2av.verify_staged_inputs(run,{"INPUT/data.dat":"0"*64})


def test_census_and_bounded_extreme_csv_validation(tmp_path):
    census=tmp_path/"pairs.csv"
    census.write_text("i,j,aij,aji,abs_delta,abs_delta_saturated,relative_delta,row_scaled_discrepancy,structure\n"
        "1,2,2.0E+000,3.0E+000,1.0E+000,0,3.3333333333333331E-001,1.0E-001,NONZERO_VALUE_MISMATCH\n",encoding="utf-8",newline="\n")
    census_summary=f2av.read_f2av_census(census,1,100)
    assert census_summary["complete"]
    assert census_summary["classification_counts"]=={"ZERO_NONZERO":0,"NONZERO_VALUE_MISMATCH":1}
    with pytest.raises(f2av.F2AVError,match="row count"):
        f2av.read_f2av_census(census,2,100)
    census.write_text(census.read_text(encoding="utf-8").replace("1,2,","1,3,",1),encoding="utf-8",newline="\n")
    with pytest.raises(f2av.F2AVError,match="out-of-band"):
        f2av.read_f2av_census(census,1,100,n_rank=4,ku=1)
    census.write_text("i,j,aij,aji,abs_delta,abs_delta_saturated,relative_delta,row_scaled_discrepancy,structure\n"
        "1,2,NaN,3.0,1.0,0,0.3,0.1,NONZERO_VALUE_MISMATCH\n",encoding="utf-8",newline="\n")
    with pytest.raises(f2av.F2AVError,match="nonfinite"):
        f2av.read_f2av_census(census,1,100)
    extremes=tmp_path/"extremes.csv"
    extremes.write_text("extreme_kind,raw_dof_index,log10_abs_value\nROW_MAX,3,2.5\n",encoding="utf-8",newline="\n")
    assert f2av.read_f2av_extremes(extremes,3)["counts_by_kind"]["ROW_MAX"]==1
    with pytest.raises(f2av.F2AVError,match="exceeds matrix rank"):
        f2av.read_f2av_extremes(extremes,2)


def test_manifest_rejects_member_hash_mismatch(tmp_path):
    root=tmp_path/"bundle"; root.mkdir(); artifact=root/"item.txt"; artifact.write_text("original",encoding="utf-8")
    manifest=root/"manifest.json"
    manifest.write_text(json.dumps({"membership":"all regular files except this manifest","artifacts":[
        {"path":"item.txt","bytes":artifact.stat().st_size,"sha256":f2av._hash(artifact)}]}),encoding="utf-8")
    artifact.write_text("changed",encoding="utf-8")
    with pytest.raises(f2av.F2AVError,match="identity mismatch"):
        f2av.verify_artifact_manifest(root,"manifest.json")


def test_manifest_expected_digest_is_checked_independently(tmp_path):
    root=tmp_path/"bundle"; root.mkdir(); artifact=root/"item.txt"; artifact.write_text("qualified identity fixture",encoding="utf-8")
    manifest=root/"manifest.json"
    manifest.write_text(json.dumps({"membership":"all regular files except this manifest","artifacts":[
        {"path":"item.txt","bytes":artifact.stat().st_size,"sha256":f2av._hash(artifact)}]}),encoding="utf-8")
    expected=f2av._hash(manifest)
    assert f2av.verify_artifact_manifest(root,"manifest.json",expected_sha256=expected)["verified"]
    with pytest.raises(f2av.F2AVError,match="manifest SHA"):
        f2av.verify_artifact_manifest(root,"manifest.json",expected_sha256="0"*64)


def _recovery_doc(source_commit=f2av.F2A_ORIGINAL_RUN_COMMIT, manifest_sha=f2av.F2A_ORIGINAL_MANIFEST_SHA256):
    return {"decision":"RECOVERY_EVIDENCE_RECONSTRUCTED_REQUIRES_REVIEW",
        "source_f2a_decision_preserved":"BLOCKED_BW1_F2A_NUMERICAL_CHARACTERIZATION",
        "source_commit":source_commit,"source_evidence":{"manifest_sha256":manifest_sha},
        "runtime":{"solver_entered":False},"aggregate_csv":{"counts_match":True},
        "f1_comparison":{"nonzero_count_equal":True,"forcing_nonzero_equal":True}}


def test_recovery_provenance_uses_original_run_commit_and_qualified_manifest():
    assert f2av.F2A_ORIGINAL_RUN_COMMIT=="e1694e18ddf1843c6709dd7e78f5de7bd6a281b4"
    assert f2av.F2A_RECOVERY_IMPLEMENTATION_COMMIT=="dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3"
    assert f2av.F2A_ORIGINAL_MANIFEST_SHA256=="605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd"
    assert f2av.F2A_RECOVERY_MANIFEST_SHA256=="451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936"
    identity=f2av.validate_recovery_source_provenance(_recovery_doc())
    assert identity["original_run_source_commit"]=="e1694e18ddf1843c6709dd7e78f5de7bd6a281b4"
    assert identity["original_manifest_sha256"]=="605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd"
    for bad in (_recovery_doc(source_commit=f2av.F2A_RECOVERY_IMPLEMENTATION_COMMIT),
                _recovery_doc(manifest_sha="0"*64)):
        with pytest.raises(f2av.F2AVError): f2av.validate_recovery_source_provenance(bad)


def test_f2a_reassembly_magnitudes_and_symmetry_reconcile_with_tolerance():
    parsed={"matrix":{"valid":10,"zero":2,"nonzero":8,"nonfinite":0},
        "scale":{"max_abs":4.0},"forcing":{"zero":2,"nonzero":2,"nonfinite":0,"max_abs":3.0},
        "symmetry":{"max_abs":0.5,"max_relative":0.25,"compared_pairs":6,"divergent_pairs":1,"nonfinite_pairs":0}}
    recovered={"matrix":{"valid":10,"zero":2,"nonzero":8,"nonfinite":0},"scale":{"max_abs":4.0*(1+5e-13)},
        "forcing":{"zero":2,"nonzero":2,"nonfinite":0,"max_abs":3.0},
        "symmetry":{"max_abs":0.5,"max_relative":0.25,"compared_pairs":6,"divergent_pairs":1,"nonfinite_pairs":0}}
    result=f2av.validate_f2a_reassembly(parsed,recovered)
    assert result["passed"]
    assert result["magnitude_checks"]["matrix.max_abs"]["within_tolerance"]
    recovered["scale"]["max_abs"]=4.0*(1+2e-12)
    with pytest.raises(f2av.F2AVError,match="matrix.max_abs exceeds governed"):
        f2av.validate_f2a_reassembly(parsed,recovered)
    recovered["scale"]["max_abs"]=4.0
    recovered["symmetry"]["divergent_pairs"]=0
    with pytest.raises(f2av.F2AVError,match="divergent_pairs differs"):
        f2av.validate_f2a_reassembly(parsed,recovered)
    recovered["symmetry"]["divergent_pairs"]=1
    recovered["forcing"]["max_abs"]=math.inf
    with pytest.raises(f2av.F2AVError,match="finite nonnegative"):
        f2av.validate_f2a_reassembly(parsed,recovered)


def _install_compile_only_mocks(monkeypatch,tmp_path,recovery_doc=None,branch=f2av.BRANCH,compile_rc=0):
    f1_root=tmp_path/"f1"; f1_root.mkdir()
    recovery_root=tmp_path/"recovery"; recovery_root.mkdir()
    recovery_doc=recovery_doc or _recovery_doc()
    result=recovery_root/"F2A_RECOVERY_RESULT.json"
    result.write_text(json.dumps(recovery_doc),encoding="utf-8",newline="\n")
    report=recovery_root/"F2A_RECOVERY_RESULT.md"; report.write_text("fixture\n",encoding="utf-8",newline="\n")
    entries=[]
    for path in (result,report):
        entries.append({"path":path.name,"bytes":path.stat().st_size,"sha256":f2av._hash(path)})
    (recovery_root/"F2A_RECOVERY_ARTIFACT_MANIFEST.json").write_text(json.dumps(
        {"membership":"all regular files except this manifest","artifacts":entries}),encoding="utf-8",newline="\n")
    real_manifest_verifier=f2av.verify_artifact_manifest
    def verify_recovery_manifest(root,filename,expected_sha256=None):
        assert expected_sha256==f2av.F2A_RECOVERY_MANIFEST_SHA256
        verified=real_manifest_verifier(root,filename)
        return {**verified,"qualified_expected_sha256":expected_sha256}
    monkeypatch.setattr(f2av,"verify_artifact_manifest",verify_recovery_manifest)
    monkeypatch.setenv("ARCANA_WORLD_QUALIFICATION_EVIDENCE_ROOT",str(tmp_path/"external-evidence"))
    monkeypatch.setattr(f2av,"ROOT",tmp_path/"repository")
    lock=tmp_path/"source-lock.json"; lock.write_text("{}\n",encoding="utf-8")
    monkeypatch.setattr(f2av.bw1,"LOCK_PATH",lock)
    monkeypatch.setattr(f2av.f2a.f1,"_git",lambda *args: branch if args==("branch","--show-current") else
        "9999999999999999999999999999999999999999" if args==("rev-parse","HEAD") else "")
    monkeypatch.setattr(f2av,"verify_recovery_implementation_identity",lambda:{"qualified_implementation_commit":f2av.F2A_RECOVERY_IMPLEMENTATION_COMMIT,"recovery_tool_canonical_utf8_lf_sha256":"a"*64})
    monkeypatch.setattr(f2av.f2a,"validate_f1_evidence",lambda _root:{"decision":"PASS_BW1_FAIR_ASSEMBLY_ONLY"})
    monkeypatch.setattr(f2av.f2a,"_verify_f1_input_identity",lambda *_:{"equal":True})
    mock_si1=SimpleNamespace(verify_source_lock=lambda *_:{"verified":True},
        run_checked=None,_solver_env=lambda:{})
    def compile_mock(_cmd,*,cwd,**_kwargs):
        if compile_rc==0: (cwd/"ShellSet.exe").write_bytes(b"mock executable")
        return SimpleNamespace(returncode=compile_rc)
    mock_si1.run_checked=compile_mock
    monkeypatch.setitem(f2av.bw1.__dict__,"si1",mock_si1)
    monkeypatch.setattr(f2av.bw1,"validate_bw1_inputs",lambda *_:{"partition_payload_sha256":"a"*64})
    monkeypatch.setattr(f2av,"verify_checkout_cleanliness",lambda _inputs:{"tracked_worktree_clean":True,"untracked_files_allowed":[]})
    monkeypatch.setattr(f2av.f2a.f1,"_probe_tool",lambda name:{"name":name,"version_excerpt":"NVIDIA HPC SDK 25.11"})
    def copy_build(_source,build):
        build.mkdir(parents=True)
        return {"instrumentation":{"verified":True}}
    monkeypatch.setattr(f2av,"_copy_locked_f2av",copy_build)
    monkeypatch.setattr(f2av.sys,"platform","linux")
    return f1_root,recovery_root


def test_compile_only_runner_orchestration_completes_and_seals_correct_provenance(monkeypatch,tmp_path):
    runner_source=(ROOT/"scripts"/"r6_si1_bandwidth_f2av_fair_diagnostics.py").read_text(encoding="utf-8")
    assert "f2a.f1._run_limited" in runner_source
    assert "bw1.f1._run_limited" not in runner_source
    assert "f1.validate_f1_evidence" not in runner_source
    f1_root,recovery_root=_install_compile_only_mocks(monkeypatch,tmp_path)
    out=tmp_path/"external-evidence"/"compiled"
    result=f2av.run_f2av(f1_root,recovery_root,out,compile_only=True)
    assert result["decision"]=="COMPILE_ONLY_COMPLETE_RUNTIME_NOT_EXECUTED"
    assert result["solver_executed"] is False and result["factorization_executed"] is False
    provenance=result["provenance"]["f2a_recovery"]
    assert provenance["original_run_source_commit"]==f2av.F2A_ORIGINAL_RUN_COMMIT
    assert provenance["original_manifest_sha256"]==f2av.F2A_ORIGINAL_MANIFEST_SHA256
    assert provenance["recovery_implementation"]["qualified_implementation_commit"]==f2av.F2A_RECOVERY_IMPLEMENTATION_COMMIT
    assert provenance["manifest_validation"]["qualified_expected_sha256"]==f2av.F2A_RECOVERY_MANIFEST_SHA256
    assert (out/"BW1_F2AV_ARTIFACT_MANIFEST.json").is_file()


@pytest.mark.parametrize("doc,expected_fragment",[
    (_recovery_doc(source_commit=f2av.F2A_RECOVERY_IMPLEMENTATION_COMMIT),"original F2A run commit"),
    (_recovery_doc(manifest_sha="0"*64),"qualified manifest SHA256"),
])
def test_compile_only_runner_fails_closed_on_recovery_provenance(monkeypatch,tmp_path,doc,expected_fragment):
    f1_root,recovery_root=_install_compile_only_mocks(monkeypatch,tmp_path,recovery_doc=doc)
    result=f2av.run_f2av(f1_root,recovery_root,tmp_path/"external-evidence"/"blocked",compile_only=True)
    assert result["decision"]=="BLOCKED_F2AV_QUALIFICATION"
    assert expected_fragment in result["failure"]


def test_compile_only_runner_fails_closed_on_compile_error(monkeypatch,tmp_path):
    f1_root,recovery_root=_install_compile_only_mocks(monkeypatch,tmp_path,compile_rc=1)
    result=f2av.run_f2av(f1_root,recovery_root,tmp_path/"external-evidence"/"compile-failed",compile_only=True)
    assert result["decision"]=="BLOCKED_F2AV_QUALIFICATION"
    assert "isolated F2A-V build failed" in result["failure"]


@pytest.mark.parametrize("protected_name",["f1-sealed","recovery-sealed"])
def test_runner_rejects_new_output_inside_sealed_evidence_without_writing(monkeypatch,tmp_path,protected_name):
    evidence_root=tmp_path/"external-evidence"; evidence_root.mkdir()
    f1_root=evidence_root/"f1-sealed"; f1_root.mkdir()
    recovery_root=evidence_root/"recovery-sealed"; recovery_root.mkdir()
    monkeypatch.setattr(f2av,"ROOT",tmp_path/"repository")
    monkeypatch.setenv("ARCANA_WORLD_QUALIFICATION_EVIDENCE_ROOT",str(evidence_root))
    protected=f1_root if protected_name=="f1-sealed" else recovery_root
    destination=protected/"nested-new-output"
    result=f2av.run_f2av(f1_root,recovery_root,destination,compile_only=True)
    assert result["decision"]=="BLOCKED_F2AV_QUALIFICATION"
    assert "overlaps protected root" in result["failure"]
    assert not destination.exists()


def test_output_path_requires_external_evidence_child_and_rejects_symlink_parent(tmp_path):
    evidence=tmp_path/"evidence"; evidence.mkdir()
    protected=evidence/"repository"; protected.mkdir()
    with pytest.raises(f2av.F2AVError,match="fresh child"):
        f2av.validate_output_destination(evidence,[protected],evidence)
    inside=protected/"new-output"
    with pytest.raises(f2av.F2AVError,match="overlaps protected"):
        f2av.validate_output_destination(inside,[protected],evidence)
    link=tmp_path/"evidence-link"
    try:
        link.symlink_to(evidence,target_is_directory=True)
    except (OSError,NotImplementedError):
        pytest.skip("directory symlinks unavailable on this Windows host")
    with pytest.raises(f2av.F2AVError,match="symlinked/junction"):
        f2av.validate_output_destination(link/"new-output",[protected],evidence)


def test_checkout_cleanliness_allows_only_hash_matched_untracked_partition(monkeypatch,tmp_path):
    partition=tmp_path/"R6_T0_VECTOR_PLATE_PARTITION.npz"; partition.write_bytes(b"authorized fixture")
    monkeypatch.setattr(f2av,"ROOT",tmp_path)
    monkeypatch.setattr(f2av.bw1,"PARTITION_PATH",partition)
    sha=f2av._hash(partition)
    monkeypatch.setattr(f2av.f2a.f1,"_git",lambda *args:"?? R6_T0_VECTOR_PLATE_PARTITION.npz")
    result=f2av.verify_checkout_cleanliness({"partition_payload_sha256":sha})
    assert result["untracked_files_allowed"]==[{"path":partition.name,"sha256":sha}]
    monkeypatch.setattr(f2av.f2a.f1,"_git",lambda *args:"?? unrelated.txt")
    with pytest.raises(f2av.F2AVError,match="unauthorized changes"):
        f2av.verify_checkout_cleanliness({"partition_payload_sha256":sha})
    monkeypatch.setattr(f2av.f2a.f1,"_git",lambda *args:"?? R6_T0_VECTOR_PLATE_PARTITION.npz\n?? unrelated.txt")
    with pytest.raises(f2av.F2AVError,match="unauthorized changes"):
        f2av.verify_checkout_cleanliness({"partition_payload_sha256":sha})
