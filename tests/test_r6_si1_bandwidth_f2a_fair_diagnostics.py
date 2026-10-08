from __future__ import annotations
import importlib.util
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
    log="""ERROR STOP 75
BW1_F2A_STAGE nRank=128884 nKRows=2182 kl=727 ku=727 iDiagonal=1455
BW1_F2A_MATRIX valid=PHYSICAL zero=ZEROS nonzero=1 nonfinite=0 fill_nonzero=0 fill_nonfinite=0 pad_nonzero=0 pad_nonfinite=0
BW1_F2A_SCALE min_nonzero=1.0E+000 max_abs=2.0E+000 diag_pos=1 diag_neg=0 diag_zero=0
BW1_F2A_SYMMETRY max_abs=0.0E+000 max_relative=0.0E+000 compared_pairs=0 divergent_pairs=0 nonfinite_pairs=0
BW1_F2A_DOMINANCE strict=1 nonstrict=0
BW1_F2A_FORCING zero=0 nonzero=1 nonfinite=0 max_abs=1.0E+000
BW1_F2A_RANGE coefficient_log10_max_min=0.3E+000 forcing_min_nonzero=1.0E+000 forcing_p50_log10_bin=0 forcing_p95_log10_bin=0
BW1_F2A_SYMMETRY_WORST i=0 j=0 aij=0.0E+000 aji=0.0E+000
BW1_F2A_AGGREGATES_WRITTEN=1
BW1_F2A_RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING
BW1_F2A_STOP_BEFORE_SOLVER
""".replace("valid=PHYSICAL",f"valid={valid}").replace("zero=ZEROS",f"zero={valid-1}")
    assert f2a.validate_fair_log(log,75)["solver_entered"] is False
    bad=log.replace("fill_nonzero=0","fill_nonzero=1")
    with pytest.raises(f2a.F2AError): f2a.validate_fair_log(bad,75)
