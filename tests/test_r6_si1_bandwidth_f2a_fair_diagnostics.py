from __future__ import annotations
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

import pytest

ROOT=Path(__file__).resolve().parents[1]
def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
f2a=_load("si1_bw1_f2a",ROOT/"scripts"/"r6_si1_bandwidth_f2a_fair_diagnostics.py")
visualizer=_load("si1_bw1_f2a_visualizer",ROOT/"scripts"/"r6_si1_bandwidth_f2a_visualize.py")
recovery=_load("si1_bw1_f2a_recovery",ROOT/"scripts"/"r6_si1_bandwidth_f2a_recover_evidence.py")


def _expand_format(fmt: str) -> list[str]:
    tokens=re.findall(r"\d+|ES24\.16E3|I0|A|[()]",fmt.upper().replace(" ",""))
    pos=0
    def group():
        nonlocal pos
        result=[]
        while pos<len(tokens) and tokens[pos]!=")":
            repeat=1
            if tokens[pos].isdigit(): repeat=int(tokens[pos]); pos+=1
            if tokens[pos]=="(":
                pos+=1; nested=group(); assert tokens[pos]==")"; pos+=1
                result.extend(nested*repeat)
            else:
                result.extend([tokens[pos]]*repeat); pos+=1
        return result
    assert tokens[pos]=="("; pos+=1; expanded=group(); assert tokens[pos]==")"
    return expanded


def _declared_names(declaration_block: str) -> list[str]:
    """Return entity names in the generated Fortran declaration block."""
    names=[]
    for statement in declaration_block.splitlines():
        if "::" not in statement:
            continue
        entities=statement.split("::",1)[1]
        # Split entity lists on commas outside array-shape parentheses.
        parts=[]; start=0; depth=0
        for index,char in enumerate(entities):
            if char=="(": depth+=1
            elif char==")": depth-=1
            elif char=="," and depth==0:
                parts.append(entities[start:index]); start=index+1
        parts.append(entities[start:])
        for entity in parts:
            match=re.match(r"\s*([a-z][a-z0-9_]*)",entity,re.I)
            assert match is not None, f"unrecognized Fortran entity: {entity!r}"
            names.append(match.group(1).lower())
    return names


def _split_fortran_args(argument_text: str) -> list[str]:
    args=[]; start=0; depth=0; in_string=False; index=0
    while index<len(argument_text):
        char=argument_text[index]
        if char=="'":
            if in_string and index+1<len(argument_text) and argument_text[index+1]=="'":
                index+=1
            else:
                in_string=not in_string
        elif not in_string and char=="(": depth+=1
        elif not in_string and char==")": depth-=1
        elif not in_string and depth==0 and char==",":
            args.append(argument_text[start:index].strip()); start=index+1
        index+=1
    args.append(argument_text[start:].strip())
    return args


def _fixture():
    # kl=ku=1, LDAB=4, diagonal row=3; mathematical 3x3 symmetric matrix.
    a=[[4.,1.,0.],[1.,3.,1.],[0.,1.,2.]]
    ab=[[0.]*3 for _ in range(4)]
    for j in range(1,4):
        for i in range(1,4):
            if abs(i-j)<=1: ab[3+i-j-1][j-1]=a[i-1][j-1]
    ab[0][1]=99.0      # reserved LAPACK fill-in region
    ab[1][0]=88.0      # mathematically invalid edge padding
    return ab


def test_small_band_mapping_fill_padding_symmetry_and_dominance():
    result=f2a.analyze_band(_fixture(),n_rank=3,kl=1,ldab=4,diagonal_row=3,force=[1.,0.,-2.])
    assert result["valid"]==7
    assert result["fill_nonzero"]==1 and result["padding_nonzero"]==1
    assert result["symmetry_pairs"]==2 and result["symmetry_divergent_pairs"]==0
    assert result["diagonal_positive"]==3 and result["diagonal_negative"]==0
    assert result["strictly_diagonally_dominant_rows"]==3
    assert result["forcing_zero"]==1 and result["forcing_nonzero"]==2


def test_fixture_detects_asymmetry_zero_negative_diagonal_nonfinite_and_ratio():
    ab=_fixture(); ab[2][1]=float("nan"); ab[3][0]=-3.0; ab[2][0]=-4.0
    result=f2a.analyze_band(ab,n_rank=3,kl=1,ldab=4,diagonal_row=3,force=[0.,float("inf"),1e300])
    assert result["nonfinite"]==1
    assert result["symmetry_divergent_pairs"]==1
    assert result["diagonal_negative"]==1
    assert result["forcing_nonfinite"]==1
    assert result["matrix_log10_abs"]["0"]>=1


def test_scaled_accumulators_survive_large_values_and_heatmap_uses_mathematical_indices():
    ab=_fixture(); ab[2][0]=1.7e308; ab[3][0]=1.7e308; ab[1][1]=-1.7e308
    result=f2a.analyze_band(ab,n_rank=3,kl=1,ldab=4,diagonal_row=3,force=[1.7e308,0.,1.])
    assert result["symmetry_max_relative_delta"]==2.0
    assert math.isfinite(result["symmetry_max_abs_delta"])
    assert result["coefficient_log10_dynamic_range"]>300
    assert f2a.coarse_index(1,128884)==1
    assert f2a.coarse_index(128884,128884)==256
    with pytest.raises(f2a.F2AError): f2a.coarse_index(0,128884)


def test_instrumentation_is_after_vbcs_before_solver_and_unconditional():
    source=(ROOT/"external"/"ShellSet-v1.1.0"/"src"/"MOD_Shells.f90").read_text(encoding="utf-8")
    transformed,proof=f2a.instrument_source_text(source)
    fem=transformed[transformed.index("SUBROUTINE FEM"):transformed.index("END SUBROUTINE FEM")]
    assert fem.index("CALL BuildF")<fem.index("CALL BuildK")<fem.index("CALL AddFSt")<fem.index("CALL VBCs")<fem.index("BW1_F2A_STAGE")
    assert fem.index("BW1_F2A_STOP_BEFORE_SOLVER")<fem.index("ERROR STOP 75")<fem.index("CALL Solver")
    assert proof["solver_reachable"] is False
    assert f2a.inspect_instrumentation(transformed)["unconditional_error_stop_75"]


def test_fortran_formats_types_counts_and_generated_line_lengths():
    transformed,_=f2a.instrument_source_text((ROOT/"external"/"ShellSet-v1.1.0"/"src"/"MOD_Shells.f90").read_text(encoding="utf-8"))
    block=transformed[transformed.index("SUBROUTINE FEM"):transformed.index("END SUBROUTINE FEM")]
    expected={"BW1_F2A_STAGE":("(A,5(A,I0))",["A"]+["A","I0"]*5),
              "BW1_F2A_MATRIX":("(A,8(A,I0))",["A"]+["A","I0"]*8),
              "BW1_F2A_SCALE":("(A,2(A,ES24.16E3),3(A,I0))",["A"]+["A","ES24.16E3"]*2+["A","I0"]*3),
              "BW1_F2A_SYMMETRY":("(A,2(A,ES24.16E3),3(A,I0))",["A"]+["A","ES24.16E3"]*2+["A","I0"]*3),
              "BW1_F2A_DOMINANCE":("(A,2(A,I0))",["A"]+["A","I0"]*2),
              "BW1_F2A_FORCING":("(A,3(A,I0),A,ES24.16E3)",["A"]+["A","I0"]*3+["A","ES24.16E3"]),
              "BW1_F2A_RANGE":("(A,2(A,ES24.16E3),2(A,I0))",["A"]+["A","ES24.16E3"]*2+["A","I0"]*2),
              "BW1_F2A_SYMMETRY_WORST":("(A,2(A,I0),2(A,ES24.16E3))",["A"]+["A","I0"]*2+["A","ES24.16E3"]*2)}
    for label,(fmt,argument_types) in expected.items():
        position=block.index(label); write=block.rfind("WRITE(*,",0,position); assert fmt in block[write:position]
        assert _expand_format(fmt)==argument_types
        assert len(_expand_format(fmt))==len(argument_types)
    declaration_block=block[block.index("! F2A generated declarations begin."):block.index("! F2A generated declarations end.")]
    diagnostic_block=block[block.index("! SI1-BW1-F2A: read-only numerical characterization"):block.index("ERROR STOP 75")]
    assert all(len(line)<=132 for line in (declaration_block+diagnostic_block).splitlines())
    assert f2a.MARKER in block
    assert "' forcing_min_nonzero='" in block
    assert "'forcing_min_nonzero='" not in block


def test_fortran_csv_writes_preserve_four_column_contract_and_argument_formats():
    source=(ROOT/"external"/"ShellSet-v1.1.0"/"src"/"MOD_Shells.f90").read_text(encoding="utf-8")
    transformed,_=f2a.instrument_source_text(source)
    fem=transformed[transformed.index("SUBROUTINE FEM"):transformed.index("END SUBROUTINE FEM")]
    writes={
        "heatmap":("(A,I0,A,I0,A,I0)",["A","I0","A","I0","A","I0"],"',',f2a_bj,',',f2a_heat("),
        "heatmap_valid":("(A,I0,A,I0,A,I0)",["A","I0","A","I0","A","I0"],"',',f2a_bj,',',f2a_heat_valid("),
        "matrix_log10_abs":("(A,I0,A,I0)",["A","I0","A","I0"],"',,',f2a_hist("),
        "diagonal_log10_abs":("(A,I0,A,I0)",["A","I0","A","I0"],"',,',f2a_dhist("),
        "forcing_log10_abs":("(A,I0,A,I0)",["A","I0","A","I0"],"',,',f2a_fhist("),
        "dominance_log10_ratio_quarter_decade":("(A,I0,A,I0)",["A","I0","A","I0"],"',,',f2a_rhist("),
    }
    for kind,(fmt,descriptors,tail) in writes.items():
        line=next(line for line in fem.splitlines() if f"'{kind},'" in line)
        match=re.search(r"WRITE\(77,'([^']+)'\)\s*(.*)$",line,re.I)
        assert match is not None and match.group(1)==fmt
        assert _expand_format(fmt)==descriptors
        assert len(_expand_format(fmt))==len(descriptors)
        assert len(_split_fortran_args(match.group(2)))==len(descriptors)
        assert tail in line
        assert len(line)<=132


def test_visualizer_validates_and_reads_all_six_four_column_aggregates(tmp_path):
    content=("kind,bin_x,bin_y,count\n"
             "heatmap,10,20,7\n"
             "heatmap_valid,10,20,9\n"
             "matrix_log10_abs,24,,1500\n"
             "diagonal_log10_abs,-2,,8\n"
             "forcing_log10_abs,18,,4\n"
             "dominance_log10_ratio_quarter_decade,12,,33\n")
    path=tmp_path/"aggregates.csv"; path.write_text(content,encoding="utf-8",newline="")
    rows=visualizer.load_aggregates(path)
    assert len(rows)==6
    assert [(row["bin_x"],row["bin_y"],row["count"]) for row in rows[:2]]==[("10","20","7"),("10","20","9")]
    assert all(rows[index]["bin_y"]=="" for index in range(2,6))
    assert visualizer.histogram_series(rows,"matrix_log10_abs")==[(24,1500)]
    assert visualizer.histogram_series(rows,"diagonal_log10_abs")==[(-2,8)]
    assert visualizer.histogram_series(rows,"forcing_log10_abs")==[(18,4)]
    assert visualizer.histogram_series(rows,"dominance_log10_ratio_quarter_decade")==[(12,33)]


@pytest.mark.parametrize("row",["matrix_log10_abs,24,", "matrix_log10_abs,24,,not-a-count", "matrix_log10_abs,24,,-1"])
def test_visualizer_rejects_missing_invalid_or_negative_count(tmp_path,row):
    path=tmp_path/"bad.csv"; path.write_text("kind,bin_x,bin_y,count\n"+row+"\n",encoding="utf-8")
    with pytest.raises(ValueError): visualizer.load_aggregates(path)


def test_visualizer_rejects_noncanonical_csv_header(tmp_path):
    path=tmp_path/"bad-header.csv"
    path.write_text("kind,bin_x,count,bin_y\nheatmap,1,2,3\n",encoding="utf-8")
    with pytest.raises(ValueError): visualizer.load_aggregates(path)


def test_generated_fortran_declarations_have_no_duplicate_names_in_fem_scope():
    source=(ROOT/"external"/"ShellSet-v1.1.0"/"src"/"MOD_Shells.f90").read_text(encoding="utf-8")
    transformed,_=f2a.instrument_source_text(source)
    fem=transformed[transformed.index("SUBROUTINE FEM"):transformed.index("END SUBROUTINE FEM")]
    declarations=fem[fem.index("! F2A generated declarations begin."):fem.index("! F2A generated declarations end.")]
    names=_declared_names(declarations)
    duplicates=sorted({name for name in names if names.count(name)>1})
    assert duplicates==[]


def test_every_f2a_fortran_local_is_explicitly_declared():
    block=f2a.instrument_source_text((ROOT/"external"/"ShellSet-v1.1.0"/"src"/"MOD_Shells.f90").read_text(encoding="utf-8"))[0]
    fem=block[block.index("SUBROUTINE FEM"):block.index("END SUBROUTINE FEM")]
    declarations=fem[fem.index("! F2A generated declarations begin."):fem.index("! F2A generated declarations end.")]
    body=fem[fem.index("! SI1-BW1-F2A: read-only numerical characterization"):fem.index("ERROR STOP 75")]
    declared=set(re.findall(r"\bf2a_[a-z0-9_]+\b",declarations,re.I))
    used=set(re.findall(r"\bf2a_[a-z0-9_]+\b",body,re.I))
    assert used-declared==set()


def test_solver_and_factorization_never_authorized_by_parser_or_instrumentation():
    proof=f2a.inspect_instrumentation(f2a.instrument_source_text((ROOT/"external"/"ShellSet-v1.1.0"/"src"/"MOD_Shells.f90").read_text(encoding="utf-8"))[0])
    parser=f2a.build_parser()
    option_strings={opt for action in parser._actions for opt in action.option_strings}
    assert not any("solve" in opt.lower() or "exe" in opt.lower() for opt in option_strings)
    assert proof["solver_reachable"] is False
    assert "RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING" in proof["rigid_mode_test"]


def test_f1_evidence_hash_gate_fails_closed_on_absence(tmp_path):
    with pytest.raises((OSError,f2a.F2AError)):
        f2a.validate_f1_evidence(tmp_path)


def test_visualizer_requires_observed_aggregate_schema(tmp_path):
    path=tmp_path/"bad.csv"; path.write_text("hello\n",encoding="utf-8")
    with pytest.raises(ValueError): visualizer.load_aggregates(path)


def test_fair_log_parser_accepts_reordered_diagnostics_and_rejects_unexpected_storage():
    n=128884; kl=ku=727; valid=n*(kl+ku+1)-kl*(kl+1)//2-ku*(ku+1)//2
    log=f"""ERROR STOP 75
BW1_F2A_STAGE nRank=128884 nKRows=2182 kl=727 ku=727 iDiagonal=1455
BW1_F2A_MATRIX valid={valid} zero={valid-1} nonzero=1 nonfinite=0 fill_nonzero=0 fill_nonfinite=0 pad_nonzero=0 pad_nonfinite=0
BW1_F2A_SCALE min_nonzero=1.0E+000 max_abs=2.0E+000 diag_pos=128884 diag_neg=0 diag_zero=0
BW1_F2A_SYMMETRY max_abs=0.0E+000 max_relative=0.0E+000 compared_pairs=0 divergent_pairs=0 nonfinite_pairs=0
BW1_F2A_DOMINANCE strict=128884 nonstrict=0
BW1_F2A_FORCING zero=128883 nonzero=1 nonfinite=0 max_abs=1.0E+000
BW1_F2A_RANGE coefficient_log10_max_min=0.3E+000 forcing_min_nonzero=1.0E+000 forcing_p50_log10_bin=0 forcing_p95_log10_bin=0
BW1_F2A_SYMMETRY_WORST i=0 j=0 aij=0.0E+000 aji=0.0E+000
BW1_F2A_AGGREGATES_WRITTEN=1
BW1_F2A_RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING
BW1_F2A_STOP_BEFORE_SOLVER
"""
    assert f2a.validate_fair_log(log,75)["solver_entered"] is False
    bad=log.replace("fill_nonzero=0","fill_nonzero=1")
    with pytest.raises(f2a.F2AError): f2a.validate_fair_log(bad,75)


def test_fair_parser_recovers_realistic_spaced_and_adjacent_numeric_fields():
    scale=f2a._parse_line(
        "BW1_F2A_SCALE min_nonzero= 1.234E-300 max_abs= 3.6508239112970148E+032 diag_pos=7 diag_neg=2 diag_zero=0\n",
        "BW1_F2A_SCALE ",
    )
    assert float(scale["max_abs"])==3.6508239112970148e32
    assert float(scale["min_nonzero"])==1.234e-300
    adjacent=f2a._parse_line(
        "BW1_F2A_RANGE coefficient_log10_max_min= 1.25E+001forcing_min_nonzero= 2.5D-004 forcing_p50_log10_bin=-323 forcing_p95_log10_bin=+2\n",
        "BW1_F2A_RANGE ",
    )
    assert float(adjacent["coefficient_log10_max_min"])==12.5
    assert float(adjacent["forcing_min_nonzero"])==2.5e-4
    assert int(adjacent["forcing_p50_log10_bin"])==-323
    assert int(adjacent["forcing_p95_log10_bin"])==2


@pytest.mark.parametrize("line",[
    "BW1_F2A_FORCING zero=1 nonzero=2 nonfinite=0\n",
    "BW1_F2A_FORCING zero=1 nonzero=2 nonzero=2 nonfinite=0 max_abs=1.0E+000\n",
    "BW1_F2A_FORCING zero=1 nonzero=2 nonfinite=0 max_abs=not-a-number\n",
    "BW1_F2A_FORCING zero=1 nonzero=2 nonfinite=0 max_abs=NaN\n",
    "BW1_F2A_FORCING zero=1 nonzero=2 nonfinite=0 max_abs=1.0E+9999\n",
])
def test_fair_parser_rejects_missing_duplicate_malformed_and_nonfinite_fields(line):
    with pytest.raises(f2a.F2AError): f2a._parse_line(line,"BW1_F2A_FORCING ")


def test_symmetry_abs_difference_avoids_overflow_and_preserves_finite_cases():
    maximum=float.fromhex("0x1.fffffffffffffp+1023")
    smallest=float.fromhex("0x0.0000000000001p-1022")
    assert f2a.scaled_abs_difference(0.0,0.0)==0.0
    assert f2a.scaled_abs_difference(1e-300,-1e-300)==2e-300
    assert f2a.scaled_abs_difference(maximum,maximum)==0.0
    assert f2a.scaled_abs_difference(maximum,-maximum)==maximum
    assert f2a.scaled_abs_difference(maximum,smallest)==maximum
    assert f2a.scaled_abs_difference(smallest,0.0)==smallest
    with pytest.raises(f2a.F2AError): f2a.scaled_abs_difference(float("inf"),0.0)
    source=(ROOT/"scripts"/"r6_si1_bandwidth_f2a_fair_diagnostics.py").read_text(encoding="utf-8")
    assert "IF (f2a_rel > 0.0D0 .AND. f2a_scale > HUGE(1.0D0)/f2a_rel)" not in source
    assert "IF (f2a_rel > 1.0D0) THEN\n                  IF (f2a_scale > HUGE(1.0D0)/f2a_rel) THEN" in source


def _write_recovery_fixture(root:Path,*,legacy_histogram_rows:bool=False)->dict:
    n=128884; kl=ku=727; valid=n*(kl+ku+1)-kl*(kl+1)//2-ku*(ku+1)//2
    log=f"""ERROR STOP 75
BW1_F2A_STAGE nRank=128884 nKRows=2182 kl=727 ku=727 iDiagonal=1455
BW1_F2A_MATRIX valid={valid} zero={valid-1804327} nonzero=1804327 nonfinite=0 fill_nonzero=0 fill_nonfinite=0 pad_nonzero=0 pad_nonfinite=0
BW1_F2A_SCALE min_nonzero= 1.0E-012 max_abs= 3.6508239112970148E+032 diag_pos=128884 diag_neg=0 diag_zero=0
BW1_F2A_SYMMETRY max_abs=0.0E+000 max_relative=0.0E+000 compared_pairs=1 divergent_pairs=0 nonfinite_pairs=0
BW1_F2A_DOMINANCE strict=128884 nonstrict=0
BW1_F2A_FORCING zero=0 nonzero=128884 nonfinite=0 max_abs=1.3496974460580477E+018
BW1_F2A_RANGE coefficient_log10_max_min= 1.0E+001forcing_min_nonzero= 1.0D-006 forcing_p50_log10_bin=-6 forcing_p95_log10_bin=-3
BW1_F2A_SYMMETRY_WORST i=1 j=2 aij=0.0E+000 aji=0.0E+000
BW1_F2A_AGGREGATES_WRITTEN=1
BW1_F2A_RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING
BW1_F2A_STOP_BEFORE_SOLVER
"""
    root.mkdir(parents=True)
    (root/"logs").mkdir(); (root/"run_f2a"/"INPUT").mkdir(parents=True)
    (root/"build_f2a"/"src").mkdir(parents=True)
    log_path=root/"logs"/"f2a_mpi_combined.log"; log_path.write_text(log,encoding="utf-8")
    staged_files={
        "INPUT/ARCANA_PLATE_OUTLINES.dig":b"synthetic staged plate outlines\n",
        "INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat":b"synthetic runtime package\n",
        "INPUT/sample.dat":b"staged synthetic input fixture\n",
    }
    for rel,content in staged_files.items():
        target=root/"run_f2a"/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    csv_path=root/"run_f2a"/"BW1_F2A_AGGREGATES.csv"
    histogram=lambda kind,x,count: f"{kind},{x},{count}\n" if legacy_histogram_rows else f"{kind},{x},,{count}\n"
    csv_path.write_text("kind,bin_x,bin_y,count\n"
        f"heatmap,1,1,1804327\nheatmap_valid,1,1,{valid}\n"
        +histogram("matrix_log10_abs",32,1804327)
        +histogram("diagonal_log10_abs",32,128884)
        +histogram("forcing_log10_abs",18,128884)
        +histogram("dominance_log10_ratio_quarter_decade",70,128884),encoding="utf-8")
    lock=json.loads(recovery.bw1.LOCK_PATH.read_text(encoding="utf-8"))
    source=(ROOT/"external"/"ShellSet-v1.1.0"/"src"/"MOD_Shells.f90").read_text(encoding="utf-8")
    instrumented,proof=f2a.instrument_source_text(source)
    instrumented_path=root/"build_f2a"/"src"/"MOD_Shells.f90"
    instrumented_path.write_text(instrumented,encoding="utf-8")
    f1_prov={"source_commit":f2a.F1_COMMIT,"result_sha256":f2a.F1_RESULT_SHA256,
             "manifest_sha256":f2a.F1_MANIFEST_SHA256,"artifact_count":1,
             "decision":"PASS_BW1_FAIR_ASSEMBLY_ONLY",
             "f1_reference_metrics":{"matrix":{"nonzero":1804327,"rows":2182,"cols":128884,"bytes":2249799104,"max_abs":3.650823911297015e32},
                                     "forcing":{"nonzero":128884,"max_abs":1.3496974460580477e18}}}
    input_validation={"source_inputs":{"fegr_sha256":"a"*64},"derived_inputs":{"runtime_sha256":"b"*64},"partition_payload_sha256":"c"*64}
    result={"decision":"BLOCKED_BW1_F2A_NUMERICAL_CHARACTERIZATION","failure":"KeyError: 'max_abs'",
        "repository":{"branch":f2a.EXPECTED_BRANCH,"head":"e1694e18ddf1843c6709dd7e78f5de7bd6a281b4"},
        "f1_provenance":f1_prov,"f1_input_identity_comparison":{"equal":True},"input_validation":input_validation,
        "instrumented_build":{"source_hashes":lock["files"],"instrumentation":{"original_sha256":lock["files"]["src/MOD_Shells.f90"],"instrumented_sha256":recovery._sha(instrumented_path)}},
        "runtime":{"returncode":75,"log_sha256":recovery._sha(log_path)},
        "staged_input_hashes_before":{rel:hashlib.sha256(content).hexdigest() for rel,content in staged_files.items()}}
    (root/"BW1_F2A_RESULT.json").write_text(json.dumps(result,sort_keys=True),encoding="utf-8")
    entries=[]
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        entries.append({"path":path.relative_to(root).as_posix(),"bytes":path.stat().st_size,"sha256":recovery._sha(path)})
    (root/"BW1_F2A_ARTIFACT_MANIFEST.json").write_text(json.dumps({"schema":"R6_SI1_BW1_F2A_ARTIFACT_MANIFEST_V1","artifacts":entries}),encoding="utf-8")
    return f1_prov,input_validation


@pytest.mark.parametrize("legacy_histogram_rows",[False,True])
def test_offline_recovery_is_separate_sealed_and_does_not_modify_source(tmp_path,monkeypatch,legacy_histogram_rows):
    original=tmp_path/"original"; f1root=tmp_path/"f1"; output=tmp_path/"recovery"
    f1root.mkdir(); f1prov,input_validation=_write_recovery_fixture(original,legacy_histogram_rows=legacy_histogram_rows)
    (f1root/"BW1_F1_RESULT.json").write_text(json.dumps({"input_validation":input_validation}),encoding="utf-8")
    monkeypatch.setattr(recovery.f2a,"validate_f1_evidence",lambda _root:f1prov)
    before={p.relative_to(original).as_posix():recovery._sha(p) for p in original.rglob("*") if p.is_file()}
    report=recovery.recover(original,f1root,output)
    after={p.relative_to(original).as_posix():recovery._sha(p) for p in original.rglob("*") if p.is_file()}
    assert before==after
    assert report["decision"]=="RECOVERY_EVIDENCE_RECONSTRUCTED_REQUIRES_REVIEW"
    assert report["source_f2a_decision_preserved"]=="BLOCKED_BW1_F2A_NUMERICAL_CHARACTERIZATION"
    assert report["aggregate_csv"]["counts_match"] is True
    assert report["staged_input_preservation"]["verified_after_run_against_pre_run_hashes"]==3
    assert report["staged_input_preservation"]["all_recorded_inputs_preserved"] is True
    assert "INPUT/ARCANA_PLATE_OUTLINES.dig" in report["staged_input_preservation"]["paths"]
    assert report["staged_input_preservation"]["posthoc_unreconstructible_controls"]
    assert report["aggregate_csv"]["legacy_three_column_histogram_rows"]==(4 if legacy_histogram_rows else 0)
    assert (output/"F2A_RECOVERY_ARTIFACT_MANIFEST.json").is_file()
    assert report["ieee_warning_audit"]["historical_flag_causality_recoverable"] is False
    manifest=json.loads((output/"F2A_RECOVERY_ARTIFACT_MANIFEST.json").read_text(encoding="utf-8"))
    assert {entry["path"] for entry in manifest["artifacts"]}=={"F2A_RECOVERY_RESULT.json","F2A_RECOVERY_RESULT.md"}
    for entry in manifest["artifacts"]:
        artifact=output/entry["path"]
        assert artifact.stat().st_size==entry["bytes"]
        assert recovery._sha(artifact)==entry["sha256"]


def test_offline_recovery_rejects_modified_original_manifest_artifact(tmp_path,monkeypatch):
    original=tmp_path/"original"; f1root=tmp_path/"f1"; output=tmp_path/"recovery"
    f1root.mkdir(); f1prov,_=_write_recovery_fixture(original)
    monkeypatch.setattr(recovery.f2a,"validate_f1_evidence",lambda _root:f1prov)
    (original/"logs"/"f2a_mpi_combined.log").write_text("modified\n",encoding="utf-8")
    with pytest.raises(recovery.RecoveryError): recovery.recover(original,f1root,output)
    assert not output.exists()


def test_offline_recovery_rejects_f1_input_identity_mismatch(tmp_path,monkeypatch):
    original=tmp_path/"original"; f1root=tmp_path/"f1"; output=tmp_path/"recovery"
    f1root.mkdir(); f1prov,input_validation=_write_recovery_fixture(original)
    input_validation["source_inputs"]["fegr_sha256"]="d"*64
    (f1root/"BW1_F1_RESULT.json").write_text(json.dumps({"input_validation":input_validation}),encoding="utf-8")
    monkeypatch.setattr(recovery.f2a,"validate_f1_evidence",lambda _root:f1prov)
    with pytest.raises(recovery.f2a.F2AError): recovery.recover(original,f1root,output)
    assert not output.exists()


@pytest.mark.parametrize("unsafe",[
    "../outside.dat", "INPUT/../../outside.dat", "/tmp/outside.dat",
    "C:/outside.dat", "INPUT\\outside.dat", "",
])
def test_staged_input_verification_rejects_unsafe_paths(tmp_path,unsafe):
    evidence=tmp_path/"evidence"
    (evidence/"run_f2a"/"INPUT").mkdir(parents=True)
    with pytest.raises(recovery.RecoveryError,match="unsafe staged-input path"):
        recovery._verify_staged_files(evidence,{"staged_input_hashes_before":{unsafe:"a"*64}})


def test_staged_input_verification_rejects_missing_and_hash_mismatch(tmp_path):
    evidence=tmp_path/"evidence"
    (evidence/"run_f2a"/"INPUT").mkdir(parents=True)
    with pytest.raises(recovery.RecoveryError,match="staged file unavailable"):
        recovery._verify_staged_files(evidence,{"staged_input_hashes_before":{"INPUT/missing.dat":"a"*64}})
    target=evidence/"run_f2a"/"INPUT"/"changed.dat"
    target.write_bytes(b"current bytes")
    with pytest.raises(recovery.RecoveryError,match="changed since pre-run hash"):
        recovery._verify_staged_files(evidence,{"staged_input_hashes_before":{"INPUT/changed.dat":"a"*64}})


def test_staged_input_verification_rejects_symlink_escape(tmp_path):
    evidence=tmp_path/"evidence"
    staged=evidence/"run_f2a"/"INPUT"
    staged.mkdir(parents=True)
    outside=tmp_path/"outside.dat"
    outside.write_bytes(b"outside")
    link=staged/"escape.dat"
    try:
        link.symlink_to(outside)
    except (OSError,NotImplementedError):
        pytest.skip("symlink creation is unavailable in this Windows environment")
    with pytest.raises(recovery.RecoveryError):
        recovery._verify_staged_files(evidence,{"staged_input_hashes_before":{"INPUT/escape.dat":recovery._sha(outside)}})


@pytest.mark.parametrize("unsafe",["C:/outside.dat","../outside.dat","/tmp/outside.dat","INPUT\\outside.dat"])
def test_original_manifest_rejects_unsafe_relative_paths(tmp_path,unsafe):
    evidence=tmp_path/"evidence"
    evidence.mkdir()
    manifest={"schema":"R6_SI1_BW1_F2A_ARTIFACT_MANIFEST_V1",
              "artifacts":[{"path":unsafe,"bytes":0,"sha256":"a"*64}]}
    (evidence/"BW1_F2A_ARTIFACT_MANIFEST.json").write_text(json.dumps(manifest),encoding="utf-8")
    with pytest.raises(recovery.RecoveryError,match="unsafe manifest artifact path"):
        recovery.verify_source_manifest(evidence)
