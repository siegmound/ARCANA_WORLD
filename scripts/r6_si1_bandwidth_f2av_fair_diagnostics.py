#!/usr/bin/env python3
"""Isolated F2A-V matrix diagnostics; always stops before ShellSet Solver."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts"),str(ROOT/"src")]
import r6_si1_bandwidth_f2a_fair_diagnostics as f2a  # noqa: E402
import r6_si1_bandwidth_bw1_fair_preflight as bw1  # noqa: E402

BRANCH="r6/si1-bandwidth-f2av"
BASELINE="dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3"
F2A_ORIGINAL_RUN_COMMIT="e1694e18ddf1843c6709dd7e78f5de7bd6a281b4"
F2A_RECOVERY_IMPLEMENTATION_COMMIT="dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3"
F2A_ORIGINAL_MANIFEST_SHA256="605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd"
F2A_RECOVERY_MANIFEST_SHA256="451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936"
F2AV_MARKER="BW1_F2AV_STOP_BEFORE_SOLVER"
F2AV_EXIT=75
ASYMMETRY_RELATIVE_THRESHOLD=1e-12
DOMINANCE_RELATIVE_TOLERANCE=1e-12
F2A_REASSEMBLY_RELATIVE_TOLERANCE=1e-12
ASYMMETRY_CAPACITY=100_000
EXTREME_CAPACITY=16
IEEE_NAMES=("overflow","underflow","inexact")
PHASE_NAMES=("BUILD_F","BUILD_K","ADD_FST","VBCS","MATRIX_SYMMETRY",
             "ROW_COLUMN_STATISTICS","OUTPUT_AGGREGATES")
EXPECTED_N=128_884
EXPECTED_KL=EXPECTED_KU=727
EXPECTED_KROWS=2_182
EXPECTED_IDIAGONAL=1_455


class F2AVError(RuntimeError):
    pass


@dataclass(frozen=True)
class AsymmetricPair:
    i: int
    j: int
    aij: float
    aji: float
    abs_delta: float
    abs_delta_saturated: bool
    relative_delta: float
    row_scaled_discrepancy: float | None
    structure: str


def stable_abs_delta(a:float,b:float)->tuple[float,bool,float]:
    """Return saturated |a-b|, saturation flag, and local relative discrepancy."""
    if not math.isfinite(a) or not math.isfinite(b):
        raise F2AVError("asymmetry coefficients must be finite")
    scale=max(abs(a),abs(b))
    if scale==0.0: return 0.0,False,0.0
    relative=abs(a/scale-b/scale)
    limit=float.fromhex("0x1.fffffffffffffp+1023")
    if relative>1.0 and scale>limit/relative: return limit,True,relative
    return scale*relative,False,relative


def _scaled_norm(values:Sequence[float])->tuple[float,float,float]:
    scale=0.0; total=0.0; minimum=math.inf
    for value in values:
        if not math.isfinite(value): raise F2AVError("matrix contains nonfinite coefficient")
        absolute=abs(value)
        if absolute==0.0: continue
        minimum=min(minimum,absolute)
        if absolute>scale:
            total=total*(scale/absolute)+1.0 if scale else 1.0
            scale=absolute
        else: total+=absolute/scale
    return scale,total,minimum


def scan_small_band(ab:Sequence[Sequence[float]],n:int,kl:int,ku:int,idiagonal:int,
                    *,capacity:int=ASYMMETRY_CAPACITY,
                    relative_threshold:float=ASYMMETRY_RELATIVE_THRESHOLD,
                    equality_tolerance:float=DOMINANCE_RELATIVE_TOLERANCE)->dict[str,Any]:
    """Small-fixture reference for LAPACK AB(iDiagonal+i-j,j)=A(i,j), 1-based."""
    if (n<=0 or kl<0 or ku<0 or kl!=ku or capacity<0 or idiagonal<=0 or
        not math.isfinite(relative_threshold) or relative_threshold<0 or
        not math.isfinite(equality_tolerance) or equality_tolerance<0 or len(ab)<idiagonal+kl):
        raise F2AVError("invalid band dimensions")
    if any(len(column)!=n for column in ab): raise F2AVError("band column count mismatch")
    def get(i:int,j:int)->float:
        slot=idiagonal+i-j
        if not (1<=i<=n and 1<=j<=n and max(1,j-ku)<=i<=min(n,j+kl)):
            raise F2AVError("matrix coordinate outside declared band")
        if not 1<=slot<=len(ab): raise F2AVError("band storage index outside allocation")
        return float(ab[slot-1][j-1])
    rows=[]; cols=[]
    for i in range(1,n+1): rows.append([get(i,j) for j in range(max(1,i-kl),min(n,i+ku)+1)])
    for j in range(1,n+1): cols.append([get(i,j) for i in range(max(1,j-ku),min(n,j+kl)+1)])
    row_stats=[_scaled_norm(row) for row in rows]; col_stats=[_scaled_norm(col) for col in cols]
    log_tol=math.log10(1.0+equality_tolerance)
    dominance=[]; dom_counts={"strict":0,"near":0,"nonstrict":0,"undefined":0,"zero_diagonal":0,"zero_offdiagonal":0}
    weak=[]
    for index,row in enumerate(rows):
        diagonal=float(ab[idiagonal-1][index])
        if not math.isfinite(diagonal): raise F2AVError("nonfinite diagonal coefficient")
        off=[value for offset,value in enumerate(row) if max(1,index+1-kl)+offset != index+1]
        off_scale,off_sum,_=_scaled_norm(off)
        if diagonal==0.0: dom_counts["zero_diagonal"]+=1
        if off_scale==0.0: dom_counts["zero_offdiagonal"]+=1
        if diagonal==0.0 and off_scale==0.0:
            log_ratio=None; status="undefined"; dom_counts["undefined"]+=1
        elif off_scale==0.0:
            log_ratio=math.inf; status="strict"; dom_counts["strict"]+=1
        elif diagonal==0.0:
            log_ratio=-math.inf; status="nonstrict"; dom_counts["nonstrict"]+=1
        else:
            log_ratio=math.log10(abs(diagonal))-math.log10(off_scale)-math.log10(off_sum)
            if abs(log_ratio)<=log_tol: status="near"; dom_counts["near"]+=1
            elif log_ratio>log_tol: status="strict"; dom_counts["strict"]+=1
            else: status="nonstrict"; dom_counts["nonstrict"]+=1
        dominance.append({"row":index+1,"log10_ratio":log_ratio,"classification":status})
        if log_ratio is not None: weak.append((log_ratio,index+1))
    pairs=[]; observed=0
    for j in range(1,n+1):
        for i in range(max(1,j-ku),j):
            if i<max(1,j-kl): continue
            a,b=get(i,j),get(j,i)
            if not math.isfinite(a) or not math.isfinite(b): raise F2AVError("nonfinite pair in matrix")
            absolute,saturated,relative=stable_abs_delta(a,b)
            if relative<=relative_threshold: continue
            observed+=1
            if len(pairs)>=capacity: continue
            scale=max(row_stats[i-1][0],row_stats[j-1][0])
            discrepancy=None
            if scale:
                numerator=abs(a/scale-b/scale)
                denominator=max(row_stats[i-1][1]*(row_stats[i-1][0]/scale),
                                row_stats[j-1][1]*(row_stats[j-1][0]/scale))
                if denominator: discrepancy=numerator/denominator
            structure="ZERO_NONZERO" if (a==0.0)!=(b==0.0) else "NONZERO_VALUE_MISMATCH"
            pairs.append(AsymmetricPair(i,j,a,b,absolute,saturated,relative,discrepancy,structure))
    if observed>capacity: raise F2AVError(f"asymmetry census capacity exceeded: {observed}>{capacity}")
    return {"n":n,"kl":kl,"ku":ku,"idiagonal":idiagonal,"asymmetry_count":observed,
            "capacity":capacity,"census_complete":True,"pairs":[asdict(pair) for pair in pairs],
            "row_scale": [item[0] for item in row_stats],"row_scaled_sum":[item[1] for item in row_stats],
            "row_min_nonzero":[None if math.isinf(item[2]) else item[2] for item in row_stats],
            "column_scale":[item[0] for item in col_stats],"column_scaled_sum":[item[1] for item in col_stats],
            "column_min_nonzero":[None if math.isinf(item[2]) else item[2] for item in col_stats],
            "dominance":{"tolerance":equality_tolerance,"counts":dom_counts,"rows":dominance,
                         "weakest_defined_rows":[row for _,row in sorted(weak)[:EXTREME_CAPACITY]]}}


def classify_ieee_flags(inherited:dict[str,bool],observed:dict[str,bool])->str:
    if set(inherited)!=set(IEEE_NAMES) or set(observed)!=set(IEEE_NAMES):
        raise F2AVError("IEEE flag set is incomplete")
    if any(type(value) is not bool for value in (*inherited.values(),*observed.values())):
        raise F2AVError("IEEE flag values must be boolean")
    if any(observed.values()): return "FLAG_OBSERVED_IN_PHASE"
    if any(inherited.values()): return "INHERITED_ONLY_NOT_OBSERVED_IN_PHASES"
    return "NOT_OBSERVED"


def assess_dof_mapping(proof:dict[str,Any]|None=None)->dict[str,Any]:
    """Remain fail-closed until mapping artifacts and their contents are verified."""
    required=("component_basis_source_sha256","node_permutation_sha256","coordinate_mapping_sha256")
    supplied={key:(proof.get(key) if isinstance(proof,dict) else None) for key in required}
    return {"status":"DOF_MAPPING_UNVERIFIED","raw_indices_only":True,
            "reason":"AUTHORITATIVE_MAPPING_ARTIFACTS_AND_CONTENTS_NOT_VERIFIED",
            "checks":{key:False for key in required},"untrusted_supplied_tokens":supplied}


def fortran_format_descriptors(fmt:str)->list[str]:
    """Expand the small fixed-format descriptor subset used by F2A-V writes."""
    source=fmt.strip()
    if not (source.startswith("(") and source.endswith(")")): raise F2AVError("malformed Fortran FORMAT")
    source=source[1:-1]
    descriptor_re=re.compile(r"^(A|I0|ES24\.16E3)$",re.I)
    def expand(part:str)->list[str]:
        out=[]; index=0
        while index<len(part):
            if part[index].isspace() or part[index]==",": index+=1; continue
            match=re.match(r"(\d*)",part[index:]); repeat=int(match.group(1) or "1"); index+=len(match.group(1))
            if index<len(part) and part[index]=="(":
                depth=1; start=index+1; cursor=start
                while cursor<len(part) and depth:
                    if part[cursor]=="(": depth+=1
                    elif part[cursor]==")": depth-=1
                    cursor+=1
                if depth: raise F2AVError("unclosed repeated FORMAT group")
                group=expand(part[start:cursor-1]); out.extend(group*repeat); index=cursor
            else:
                token=re.match(r"A|I0|ES24\.16E3",part[index:],re.I)
                if token is None: raise F2AVError("unsupported Fortran FORMAT descriptor")
                code=token.group(0).upper();
                if descriptor_re.fullmatch(code) is None: raise F2AVError("invalid Fortran FORMAT descriptor")
                out.extend([code]*repeat); index+=len(code)
        return out
    return expand(source)


def _f2av_fortran_extension()->str:
    """Fortran declarations/executable statements appended to the F2A assembly scan."""
    return r'''! SI1-BW1-F2A-V bounded asymmetry census and row/column diagnostics.
INTEGER, PARAMETER :: f2av_capacity=100000,f2av_extreme_capacity=16
INTEGER :: f2av_q,f2av_u,f2av_bin,f2av_ios,f2av_dom_strict,f2av_dom_near
INTEGER :: f2av_dom_nonstrict,f2av_dom_undefined,f2av_zero_diag,f2av_zero_offdiag,f2av_pos
INTEGER :: f2av_p05_bin,f2av_p50_bin,f2av_p95_bin
INTEGER :: f2av_pair_count,f2av_asym_n,f2av_asym_zero_nonzero,f2av_asym_numeric_mismatch,f2av_asym_nonfinite
INTEGER :: f2av_asym_i(f2av_capacity),f2av_asym_j(f2av_capacity),f2av_asym_sat(f2av_capacity)
INTEGER :: f2av_weak_i(f2av_extreme_capacity),f2av_topri(f2av_extreme_capacity),f2av_topci(f2av_extreme_capacity)
INTEGER :: f2av_lowri(f2av_extreme_capacity),f2av_lowci(f2av_extreme_capacity)
INTEGER :: f2av_row_nonfinite(nRank),f2av_col_nonfinite(nRank)
INTEGER :: f2av_dom_defined(nRank)
INTEGER(KIND=8) :: f2av_dhist(258),f2av_rowhist(632),f2av_colhist(632)
INTEGER(KIND=8) :: f2av_cum
INTEGER(KIND=8) :: f2av_dom_valid_rows,f2av_q05_target,f2av_q50_target,f2av_q95_target
INTEGER(KIND=8) :: f2av_rowminhist(632),f2av_colminhist(632)
INTEGER(KIND=8) :: f2av_rowl1hist(632),f2av_coll1hist(632)
REAL*8 :: f2av_asym_a(f2av_capacity),f2av_asym_b(f2av_capacity)
REAL*8 :: f2av_asym_abs(f2av_capacity),f2av_asym_rel(f2av_capacity),f2av_asym_row(f2av_capacity)
REAL*8 :: f2av_asym_max,f2av_asym_min,f2av_rel_tol,f2av_abs_scale,f2av_abs_rel,f2av_abs_delta
REAL*8 :: f2av_row_scale(nRank),f2av_row_sum(nRank),f2av_row_min(nRank)
REAL*8 :: f2av_col_scale(nRank),f2av_col_sum(nRank),f2av_col_min(nRank)
REAL*8 :: f2av_dom_log(nRank),f2av_toprv(f2av_extreme_capacity),f2av_topcv(f2av_extreme_capacity)
REAL*8 :: f2av_lowrv(f2av_extreme_capacity),f2av_lowcv(f2av_extreme_capacity),f2av_weakv(f2av_extreme_capacity)
REAL*8 :: f2av_global_rmax,f2av_global_rmin,f2av_global_cmax,f2av_global_cmin
LOGICAL :: f2av_inherited(3),f2av_phase_flags(7,3),f2av_any(3)
! END SI1-BW1-F2A-V declarations.
'''


def instrument_source_text(text:str)->tuple[str,dict[str,Any]]:
    if F2AV_MARKER in text: raise F2AVError("F2A-V instrumentation already present")
    generated,base_proof=f2a.instrument_source_text(text)
    generated=generated.replace("USE, INTRINSIC :: IEEE_ARITHMETIC, ONLY: IEEE_IS_FINITE",
        "USE, INTRINSIC :: IEEE_ARITHMETIC, ONLY: IEEE_IS_FINITE, IEEE_GET_FLAG, IEEE_SET_FLAG, IEEE_OVERFLOW, IEEE_UNDERFLOW, IEEE_INEXACT",1)
    decl_end="! F2A generated declarations end."
    if generated.count(decl_end)!=1: raise F2AVError("F2A declaration anchor is not unique")
    generated=generated.replace(decl_end,_f2av_fortran_extension()+decl_end,1)
    # Phase flag probes wrap only the four existing assembly calls. Sticky flags
    # are captured at entry, cleared between phases, and restored as their union.
    for name,phase in reversed(list(zip(("BuildF","BuildK","AddFSt","VBCs"),range(1,5)))):
        start,end,_,_,_=f2a._fem_bounds(generated)
        fem=generated[start:end]
        match=list(re.finditer(rf"(?im)^\s*CALL\s+{name}\b",fem))
        if len(match)!=1: raise F2AVError(f"expected one {name} phase call")
        begin=match[0].start(); call_end=f2a.f1._call_end(fem,begin)
        line_end=fem.find("\n",call_end)
        if line_end<0: raise F2AVError(f"{name} call has no following line")
        before=_phase_begin_fortran(phase)
        after=_phase_end_fortran(phase)
        fem=fem[:line_end+1]+after+fem[line_end+1:]
        fem=fem[:begin]+before+fem[begin:]
        generated=generated[:start]+fem+generated[end:]
    # Diagnostic phase 5 is the matrix/symmetry pass, phase 6 is
    # dominance/scale finalization, and phase 7 covers all output.
    marker=f"WRITE(*,'(A)') '{f2a.MARKER}'"
    if generated.count(marker)!=1: raise F2AVError("F2A stop marker changed")
    full_extension=_f2av_executable_block()
    split_token="! Record all retained anomaly rows. Metadata marks the census incomplete on overflow."
    if full_extension.count(split_token)!=1: raise F2AVError("F2A-V output phase split anchor changed")
    pre_output,output_tail=full_extension.split(split_token,1)
    output_part=split_token+output_tail
    first_report="WRITE(*,'(A,5(A,I0))') 'BW1_F2A_STAGE '"
    if generated.count(first_report)!=1: raise F2AVError("F2A report output anchor is not unique")
    generated=generated.replace(first_report,pre_output+"\n"+_phase_end_fortran(6)+_phase_begin_fortran(7)+output_part+"\n"+first_report,1)
    generated=generated.replace(marker,_phase_end_fortran(7)+_phase_summary_fortran()+"\n"+
        "WRITE(*,'(A)') '"+F2AV_MARKER+"'\n"+marker,1)
    # Initialize V arrays alongside F2A's existing post-VBC initialization.
    init_anchor="f2a_rowscale=0.0D0; f2a_rowsum=0.0D0; f2a_rowdiag=0.0D0"
    init=init_anchor+"\nf2av_row_scale=0.0D0; f2av_row_sum=0.0D0; f2av_row_min=HUGE(1.0D0)\n" \
         "f2av_col_scale=0.0D0; f2av_col_sum=0.0D0; f2av_col_min=HUGE(1.0D0)\n" \
         "f2av_row_nonfinite=0; f2av_col_nonfinite=0; f2av_toprv=-HUGE(1.0D0); f2av_topcv=-HUGE(1.0D0)\n" \
         "f2av_lowrv=HUGE(1.0D0); f2av_lowcv=HUGE(1.0D0); f2av_topri=0; f2av_topci=0; f2av_lowri=0; f2av_lowci=0\n" \
         "f2av_weakv=HUGE(1.0D0); f2av_weak_i=0; f2av_dom_log=0.0D0\n" \
         "f2av_pair_count=0; f2av_asym_n=0; f2av_asym_zero_nonzero=0; f2av_asym_numeric_mismatch=0; f2av_asym_nonfinite=0\n" \
         "f2av_global_rmax=0.0D0; f2av_global_rmin=HUGE(1.0D0); f2av_global_cmax=0.0D0; f2av_global_cmin=HUGE(1.0D0)\n" \
         "f2av_dom_strict=0; f2av_dom_near=0; f2av_dom_nonstrict=0; f2av_dom_undefined=0; f2av_dom_defined=0\n" \
         "f2av_zero_diag=0; f2av_zero_offdiag=0; f2av_dhist=0_8; f2av_rowhist=0_8; f2av_colhist=0_8\n" \
         "f2av_p05_bin=-1; f2av_p50_bin=-1; f2av_p95_bin=-1; f2av_cum=0_8\n" \
         "f2av_rowminhist=0_8; f2av_colminhist=0_8; f2av_rowl1hist=0_8; f2av_coll1hist=0_8\n" \
         "f2av_rel_tol=LOG10(1.0D0+1.0D-12)"
    if generated.count(init_anchor)!=1: raise F2AVError("F2A row initialization anchor changed")
    generated=generated.replace(init_anchor,init,1)
    # Collect bounded row/column scaled norms and all significant pair records
    # during F2A's already-required matrix traversal; do not copy the matrix.
    finite_anchor="f2a_x=k(f2a_s,f2a_j)"
    if generated.count(finite_anchor)!=1: raise F2AVError("unique F2A matrix coefficient load not found")
    generated=generated.replace(finite_anchor,finite_anchor+"\n"+_per_coefficient_fortran()+"\n"+_f2av_pair_fortran(),1)
    scan_anchor="DO f2a_j=1,nRank"
    if generated.count(scan_anchor)!=1: raise F2AVError("unique matrix scan start not found")
    generated=generated.replace(scan_anchor,_phase_begin_fortran(5)+scan_anchor,1)
    phase_boundary="\nDO f2a_i=1,nRank"
    if phase_boundary not in generated: raise F2AVError("matrix/row-statistics phase boundary missing")
    generated=generated.replace(phase_boundary,"\n"+_phase_end_fortran(5)+_phase_begin_fortran(6)+"DO f2a_i=1,nRank",1)
    proof=inspect_instrumentation(generated)
    proof.update(base_proof)
    proof["instrumented_source_sha256"]=hashlib.sha256(generated.encode()).hexdigest()
    return generated,proof


def _phase_begin_fortran(phase:int)->str:
    prefix=""
    if phase==1:
        prefix="""! F2A-V preserve inherited sticky flags before isolated phase sampling.
CALL IEEE_GET_FLAG(IEEE_OVERFLOW,f2av_inherited(1))
CALL IEEE_GET_FLAG(IEEE_UNDERFLOW,f2av_inherited(2))
CALL IEEE_GET_FLAG(IEEE_INEXACT,f2av_inherited(3))
f2av_phase_flags=.FALSE.
f2av_any=f2av_inherited
"""
    return prefix+"""CALL IEEE_SET_FLAG(IEEE_OVERFLOW,.FALSE.)
CALL IEEE_SET_FLAG(IEEE_UNDERFLOW,.FALSE.)
CALL IEEE_SET_FLAG(IEEE_INEXACT,.FALSE.)
"""


def _phase_end_fortran(phase:int)->str:
    return f"""CALL IEEE_GET_FLAG(IEEE_OVERFLOW,f2av_phase_flags({phase},1))
CALL IEEE_GET_FLAG(IEEE_UNDERFLOW,f2av_phase_flags({phase},2))
CALL IEEE_GET_FLAG(IEEE_INEXACT,f2av_phase_flags({phase},3))
f2av_any=f2av_any .OR. f2av_phase_flags({phase},:)
"""


def _phase_summary_fortran()->str:
    return r'''WRITE(*,'(A,L1,A,L1,A,L1)') 'BW1_F2AV_IEEE_INHERITED overflow=',f2av_inherited(1), &
  ' underflow=',f2av_inherited(2),' inexact=',f2av_inherited(3)
DO f2av_q=1,7
  WRITE(*,'(A,I0,A,L1,A,L1,A,L1)') 'BW1_F2AV_IEEE_PHASE phase_id=',f2av_q, &
    ' overflow=',f2av_phase_flags(f2av_q,1),' underflow=',f2av_phase_flags(f2av_q,2), &
    ' inexact=',f2av_phase_flags(f2av_q,3)
END DO
CALL IEEE_SET_FLAG(IEEE_OVERFLOW,f2av_any(1))
CALL IEEE_SET_FLAG(IEEE_UNDERFLOW,f2av_any(2))
CALL IEEE_SET_FLAG(IEEE_INEXACT,f2av_any(3))'''


def _per_coefficient_fortran()->str:
    return r'''IF (IEEE_IS_FINITE(f2a_x)) THEN
  f2av_abs_delta=ABS(f2a_x)
  IF (f2av_abs_delta > 0.0D0) THEN
    f2av_row_min(f2a_i)=MIN(f2av_row_min(f2a_i),f2av_abs_delta)
    f2av_col_min(f2a_j)=MIN(f2av_col_min(f2a_j),f2av_abs_delta)
  END IF
  IF (f2av_abs_delta > f2av_row_scale(f2a_i)) THEN
    IF (f2av_row_scale(f2a_i) > 0.0D0) f2av_row_sum(f2a_i)=f2av_row_sum(f2a_i)*(f2av_row_scale(f2a_i)/f2av_abs_delta)
    f2av_row_scale(f2a_i)=f2av_abs_delta
    IF (f2av_abs_delta > 0.0D0) f2av_row_sum(f2a_i)=f2av_row_sum(f2a_i)+1.0D0
  ELSE IF (f2av_abs_delta > 0.0D0) THEN
    f2av_row_sum(f2a_i)=f2av_row_sum(f2a_i)+f2av_abs_delta/f2av_row_scale(f2a_i)
  END IF
  IF (f2av_abs_delta > f2av_col_scale(f2a_j)) THEN
    IF (f2av_col_scale(f2a_j) > 0.0D0) f2av_col_sum(f2a_j)=f2av_col_sum(f2a_j)*(f2av_col_scale(f2a_j)/f2av_abs_delta)
    f2av_col_scale(f2a_j)=f2av_abs_delta
    IF (f2av_abs_delta > 0.0D0) f2av_col_sum(f2a_j)=f2av_col_sum(f2a_j)+1.0D0
  ELSE IF (f2av_abs_delta > 0.0D0) THEN
    f2av_col_sum(f2a_j)=f2av_col_sum(f2a_j)+f2av_abs_delta/f2av_col_scale(f2a_j)
  END IF
ELSE
  f2av_row_nonfinite(f2a_i)=f2av_row_nonfinite(f2a_i)+1
  f2av_col_nonfinite(f2a_j)=f2av_col_nonfinite(f2a_j)+1
END IF'''


def _asymmetry_capture_fortran()->str:
    return r'''IF (f2a_rel > 1.0D-12) THEN
  f2av_asym_n=f2av_asym_n+1
  IF ((f2a_x == 0.0D0) .NEQV. (f2a_mirror == 0.0D0)) THEN
    f2av_asym_zero_nonzero=f2av_asym_zero_nonzero+1
  ELSE
    f2av_asym_numeric_mismatch=f2av_asym_numeric_mismatch+1
  END IF
  IF (f2av_asym_n <= f2av_capacity) THEN
    f2av_asym_i(f2av_asym_n)=f2a_i; f2av_asym_j(f2av_asym_n)=f2a_j
    f2av_asym_a(f2av_asym_n)=f2a_x; f2av_asym_b(f2av_asym_n)=f2a_mirror
    f2av_asym_rel(f2av_asym_n)=f2a_rel
    f2av_abs_scale=MAX(ABS(f2a_x),ABS(f2a_mirror))
    f2av_abs_rel=f2a_rel
    IF (f2av_abs_scale == 0.0D0) THEN
      f2av_abs_delta=0.0D0; f2av_asym_sat(f2av_asym_n)=0
    ELSE IF (f2av_abs_rel > 1.0D0) THEN
      IF (f2av_abs_scale > HUGE(1.0D0)/f2av_abs_rel) THEN
        f2av_abs_delta=HUGE(1.0D0); f2av_asym_sat(f2av_asym_n)=1
      ELSE
        f2av_abs_delta=f2av_abs_scale*f2av_abs_rel; f2av_asym_sat(f2av_asym_n)=0
      END IF
    ELSE
      f2av_abs_delta=f2av_abs_scale*f2av_abs_rel; f2av_asym_sat(f2av_asym_n)=0
    END IF
    f2av_asym_abs(f2av_asym_n)=f2av_abs_delta
  END IF
END IF'''


def _f2av_pair_fortran()->str:
    return """IF (f2a_i < f2a_j) THEN
  f2a_mirror=k(iDiagonal+f2a_j-f2a_i,f2a_i)
  f2av_pair_count=f2av_pair_count+1
  IF (.NOT. IEEE_IS_FINITE(f2a_x) .OR. .NOT. IEEE_IS_FINITE(f2a_mirror)) THEN
    f2av_asym_nonfinite=f2av_asym_nonfinite+1
  ELSE
    f2a_scale=MAX(ABS(f2a_x),ABS(f2a_mirror))
    IF (f2a_scale > 0.0D0) THEN
      f2a_rel=ABS(f2a_x/f2a_scale-f2a_mirror/f2a_scale)
"""+_asymmetry_capture_fortran()+"""
    END IF
  END IF
END IF"""


def _f2av_executable_block()->str:
    # V2/V3 reductions are O(nRank); input coefficient scan is fused into F2A's
    # existing O(nRank*nKRows) traversal. No extra matrix copy is allocated.
    return r'''! F2A-V finalize dominance and row/column statistics.
DO f2av_q=1,nRank
  IF (.NOT. IEEE_IS_FINITE(f2a_rowdiag(f2av_q))) THEN
    f2av_dom_undefined=f2av_dom_undefined+1; f2av_dom_defined(f2av_q)=0
  ELSE
    IF (f2a_rowdiag(f2av_q) == 0.0D0) f2av_zero_diag=f2av_zero_diag+1
    IF (f2a_rowscale(f2av_q) == 0.0D0) f2av_zero_offdiag=f2av_zero_offdiag+1
    IF (f2av_row_nonfinite(f2av_q)>0) THEN
      f2av_dom_undefined=f2av_dom_undefined+1; f2av_dom_defined(f2av_q)=0
ELSE IF (f2a_rowdiag(f2av_q)==0.0D0 .AND. f2a_rowscale(f2av_q)==0.0D0) THEN
      f2av_dom_undefined=f2av_dom_undefined+1; f2av_dom_defined(f2av_q)=0
      f2av_dom_log(f2av_q)=0.0D0
    ELSE IF (f2a_rowscale(f2av_q)==0.0D0) THEN
      f2av_dom_defined(f2av_q)=1
      f2av_dom_strict=f2av_dom_strict+1; f2av_dom_log(f2av_q)=HUGE(1.0D0)
    ELSE IF (f2a_rowdiag(f2av_q)==0.0D0) THEN
      f2av_dom_defined(f2av_q)=1
      f2av_dom_nonstrict=f2av_dom_nonstrict+1; f2av_dom_log(f2av_q)=-HUGE(1.0D0)
    ELSE
      f2av_dom_defined(f2av_q)=1
      f2av_dom_log(f2av_q)=LOG10(ABS(f2a_rowdiag(f2av_q)))-LOG10(f2a_rowscale(f2av_q))-LOG10(f2a_rowsum(f2av_q))
      IF (ABS(f2av_dom_log(f2av_q)) <= f2av_rel_tol) THEN
        f2av_dom_near=f2av_dom_near+1
      ELSE IF (f2av_dom_log(f2av_q) > f2av_rel_tol) THEN
        f2av_dom_strict=f2av_dom_strict+1
      ELSE
        f2av_dom_nonstrict=f2av_dom_nonstrict+1
      END IF
    END IF
  END IF
  IF (f2av_dom_defined(f2av_q)==0) CYCLE
  IF (f2av_dom_log(f2av_q) <= -32.0D0) THEN
    f2av_bin=1
  ELSE IF (f2av_dom_log(f2av_q) >= 32.0D0) THEN
    f2av_bin=258
  ELSE
    f2av_bin=2+INT((f2av_dom_log(f2av_q)+32.0D0)*4.0D0)
  END IF
  f2av_dhist(f2av_bin)=f2av_dhist(f2av_bin)+1_8
END DO
f2av_cum=0_8
f2av_dom_valid_rows=INT(nRank,8)-INT(f2av_dom_undefined,8)
IF (f2av_dom_valid_rows>0_8) THEN
  f2av_q05_target=(5_8*f2av_dom_valid_rows+99_8)/100_8
  f2av_q50_target=(50_8*f2av_dom_valid_rows+99_8)/100_8
  f2av_q95_target=(95_8*f2av_dom_valid_rows+99_8)/100_8
  DO f2av_bin=1,258
    f2av_cum=f2av_cum+f2av_dhist(f2av_bin)
    IF (f2av_p05_bin<0 .AND. f2av_cum>=f2av_q05_target) f2av_p05_bin=f2av_bin
    IF (f2av_p50_bin<0 .AND. f2av_cum>=f2av_q50_target) f2av_p50_bin=f2av_bin
    IF (f2av_p95_bin<0 .AND. f2av_cum>=f2av_q95_target) f2av_p95_bin=f2av_bin
  END DO
END IF
WRITE(*,'(A,I0,A,I0,A,I0,A,I0)') 'BW1_F2AV_DOM_QUANTILES p05_bin=',f2av_p05_bin, &
  ' p50_bin=',f2av_p50_bin,' p95_bin=',f2av_p95_bin,' rows=',f2av_dom_valid_rows
DO f2av_q=1,nRank
  IF (f2av_row_scale(f2av_q)>0.0D0) THEN
    f2av_global_rmax=MAX(f2av_global_rmax,f2av_row_scale(f2av_q))
    f2av_global_rmin=MIN(f2av_global_rmin,f2av_row_scale(f2av_q))
  END IF
  IF (f2av_col_scale(f2av_q)>0.0D0) THEN
    f2av_global_cmax=MAX(f2av_global_cmax,f2av_col_scale(f2av_q))
    f2av_global_cmin=MIN(f2av_global_cmin,f2av_col_scale(f2av_q))
  END IF
  IF (f2av_row_scale(f2av_q) == 0.0D0) THEN
    f2av_row_min(f2av_q)=0.0D0
  ELSE
    f2av_bin=MAX(-323,MIN(308,FLOOR(LOG10(f2av_row_scale(f2av_q)))))+324
    f2av_rowhist(f2av_bin)=f2av_rowhist(f2av_bin)+1_8
    f2av_bin=MAX(-323,MIN(308,FLOOR(LOG10(f2av_row_min(f2av_q)))))+324
    f2av_rowminhist(f2av_bin)=f2av_rowminhist(f2av_bin)+1_8
    f2av_bin=MAX(-323,MIN(308,FLOOR(LOG10(f2av_row_scale(f2av_q))+LOG10(f2av_row_sum(f2av_q)))))+324
    f2av_rowl1hist(f2av_bin)=f2av_rowl1hist(f2av_bin)+1_8
  END IF
  IF (f2av_col_scale(f2av_q) == 0.0D0) THEN
    f2av_col_min(f2av_q)=0.0D0
  ELSE
    f2av_bin=MAX(-323,MIN(308,FLOOR(LOG10(f2av_col_scale(f2av_q)))))+324
    f2av_colhist(f2av_bin)=f2av_colhist(f2av_bin)+1_8
    f2av_bin=MAX(-323,MIN(308,FLOOR(LOG10(f2av_col_min(f2av_q)))))+324
    f2av_colminhist(f2av_bin)=f2av_colminhist(f2av_bin)+1_8
    f2av_bin=MAX(-323,MIN(308,FLOOR(LOG10(f2av_col_scale(f2av_q))+LOG10(f2av_col_sum(f2av_q)))))+324
    f2av_coll1hist(f2av_bin)=f2av_coll1hist(f2av_bin)+1_8
  END IF
END DO
IF (f2av_global_rmin == HUGE(1.0D0)) f2av_global_rmin=0.0D0
IF (f2av_global_cmin == HUGE(1.0D0)) f2av_global_cmin=0.0D0
! Compute row-scaled discrepancy after stable row norms are complete.
DO f2av_q=1,MIN(f2av_asym_n,f2av_capacity)
  f2av_u=f2av_asym_i(f2av_q); f2av_bin=f2av_asym_j(f2av_q)
  f2av_abs_scale=MAX(f2av_row_scale(f2av_u),f2av_row_scale(f2av_bin))
  IF (f2av_abs_scale == 0.0D0) THEN
    f2av_asym_row(f2av_q)=-1.0D0
  ELSE
    f2av_abs_rel=MAX(f2av_row_sum(f2av_u)*(f2av_row_scale(f2av_u)/f2av_abs_scale), &
                     f2av_row_sum(f2av_bin)*(f2av_row_scale(f2av_bin)/f2av_abs_scale))
    IF (f2av_abs_rel == 0.0D0) THEN
      f2av_asym_row(f2av_q)=-1.0D0
    ELSE
      f2av_asym_row(f2av_q)=ABS(f2av_asym_a(f2av_q)/f2av_abs_scale- &
                                f2av_asym_b(f2av_q)/f2av_abs_scale)/f2av_abs_rel
    END IF
  END IF
END DO
! Record all retained anomaly rows. Metadata marks the census incomplete on overflow.
OPEN(UNIT=78,FILE='BW1_F2AV_ASYMMETRY_CENSUS.csv',STATUS='REPLACE',ACTION='WRITE',IOSTAT=f2av_ios)
IF (f2av_ios == 0) THEN
  WRITE(78,'(A)') 'i,j,aij,aji,abs_delta,abs_delta_saturated,relative_delta,row_scaled_discrepancy,structure'
  DO f2av_q=1,MIN(f2av_asym_n,f2av_capacity)
    IF ((f2av_asym_a(f2av_q) == 0.0D0) .NEQV. (f2av_asym_b(f2av_q) == 0.0D0)) THEN
      WRITE(78,'(I0,A,I0,4(A,ES24.16E3),A,I0,A,ES24.16E3,A,A)') &
        f2av_asym_i(f2av_q),',',f2av_asym_j(f2av_q),',',f2av_asym_a(f2av_q),',', &
        f2av_asym_b(f2av_q),',',f2av_asym_abs(f2av_q),',',f2av_asym_rel(f2av_q),',', &
        f2av_asym_sat(f2av_q),',',f2av_asym_row(f2av_q),',','ZERO_NONZERO'
    ELSE
      WRITE(78,'(I0,A,I0,4(A,ES24.16E3),A,I0,A,ES24.16E3,A,A)') &
        f2av_asym_i(f2av_q),',',f2av_asym_j(f2av_q),',',f2av_asym_a(f2av_q),',', &
        f2av_asym_b(f2av_q),',',f2av_asym_abs(f2av_q),',',f2av_asym_rel(f2av_q),',', &
        f2av_asym_sat(f2av_q),',',f2av_asym_row(f2av_q),',','NONZERO_VALUE_MISMATCH'
    END IF
  END DO
  CLOSE(78)
END IF
WRITE(*,'(A,I0,A,I0,A,I0,A,I0,A,I0,A,I0,A,L1)') 'BW1_F2AV_ASYMMETRY compared_pairs=',f2av_pair_count, &
  ' count=',f2av_asym_n,' capacity=',f2av_capacity,' zero_nonzero=',f2av_asym_zero_nonzero, &
  ' numeric_mismatch=',f2av_asym_numeric_mismatch,' nonfinite_pairs=',f2av_asym_nonfinite, &
  ' complete=',f2av_asym_n<=f2av_capacity .AND. f2av_asym_nonfinite==0
WRITE(*,'(A,I0,A,I0,A,I0,A,I0,A,I0,A,I0)') 'BW1_F2AV_DOMINANCE strict=',f2av_dom_strict, &
  ' near=',f2av_dom_near,' nonstrict=',f2av_dom_nonstrict,' undefined=',f2av_dom_undefined, &
  ' zero_diagonal=',f2av_zero_diag,' zero_offdiag=',f2av_zero_offdiag
DO f2av_bin=1,258
  IF (f2av_dhist(f2av_bin)>0_8) WRITE(*,'(A,I0,A,I0)') 'BW1_F2AV_DOM_HIST bin=',f2av_bin,' count=',f2av_dhist(f2av_bin)
END DO
WRITE(*,'(A,I0,A,I0,A,I0,A,I0)') 'BW1_F2AV_SCALE_COUNTS rows_zero=',COUNT(f2av_row_scale==0.0D0), &
  ' cols_zero=',COUNT(f2av_col_scale==0.0D0),' rows=',nRank,' cols=',nRank
DO f2av_bin=1,632
  IF (f2av_rowhist(f2av_bin)>0_8) THEN
    WRITE(*,'(A,I0,A,I0)') 'BW1_F2AV_ROW_MAX_HIST bin=',f2av_bin,' count=',f2av_rowhist(f2av_bin)
  END IF
  IF (f2av_colhist(f2av_bin)>0_8) THEN
    WRITE(*,'(A,I0,A,I0)') 'BW1_F2AV_COL_MAX_HIST bin=',f2av_bin,' count=',f2av_colhist(f2av_bin)
  END IF
  IF (f2av_rowminhist(f2av_bin)>0_8) THEN
    WRITE(*,'(A,I0,A,I0)') 'BW1_F2AV_ROW_MIN_HIST bin=',f2av_bin,' count=',f2av_rowminhist(f2av_bin)
  END IF
  IF (f2av_colminhist(f2av_bin)>0_8) THEN
    WRITE(*,'(A,I0,A,I0)') 'BW1_F2AV_COL_MIN_HIST bin=',f2av_bin,' count=',f2av_colminhist(f2av_bin)
  END IF
  IF (f2av_rowl1hist(f2av_bin)>0_8) THEN
    WRITE(*,'(A,I0,A,I0)') 'BW1_F2AV_ROW_L1_HIST bin=',f2av_bin,' count=',f2av_rowl1hist(f2av_bin)
  END IF
  IF (f2av_coll1hist(f2av_bin)>0_8) THEN
    WRITE(*,'(A,I0,A,I0)') 'BW1_F2AV_COL_L1_HIST bin=',f2av_bin,' count=',f2av_coll1hist(f2av_bin)
  END IF
END DO
WRITE(*,'(A,I0,A,I0,A,I0,A,I0)') 'BW1_F2AV_NONFINITE rows=',SUM(f2av_row_nonfinite), &
  ' columns=',SUM(f2av_col_nonfinite),' zero_rows=',COUNT(f2av_row_scale==0.0D0), &
  ' zero_columns=',COUNT(f2av_col_scale==0.0D0)
WRITE(*,'(A,4(A,ES24.16E3),2(A,I0))') 'BW1_F2AV_SCALE_EXTREMA ', &
  'row_max=',f2av_global_rmax,' row_min=',f2av_global_rmin, &
  ' column_max=',f2av_global_cmax,' column_min=',f2av_global_cmin, &
  ' rows=',nRank,' columns=',nRank
OPEN(UNIT=79,FILE='BW1_F2AV_ROW_COLUMN_EXTREMES.csv',STATUS='REPLACE',ACTION='WRITE',IOSTAT=f2av_ios)
IF (f2av_ios==0) THEN
  WRITE(79,'(A)') 'extreme_kind,raw_dof_index,log10_abs_value'
  DO f2av_q=1,nRank
    IF (f2av_row_scale(f2av_q)>0.0D0) THEN
      f2av_pos=f2av_extreme_capacity+1
      DO f2av_u=1,f2av_extreme_capacity
        IF (LOG10(f2av_row_scale(f2av_q))>f2av_toprv(f2av_u)) THEN
          f2av_pos=f2av_u; EXIT
        END IF
      END DO
      IF (f2av_pos<=f2av_extreme_capacity) THEN
        DO f2av_u=f2av_extreme_capacity,f2av_pos+1,-1
          f2av_toprv(f2av_u)=f2av_toprv(f2av_u-1); f2av_topri(f2av_u)=f2av_topri(f2av_u-1)
        END DO
        f2av_toprv(f2av_pos)=LOG10(f2av_row_scale(f2av_q)); f2av_topri(f2av_pos)=f2av_q
      END IF
    END IF
    IF (f2av_col_scale(f2av_q)>0.0D0) THEN
      f2av_pos=f2av_extreme_capacity+1
      DO f2av_u=1,f2av_extreme_capacity
        IF (LOG10(f2av_col_scale(f2av_q))>f2av_topcv(f2av_u)) THEN
          f2av_pos=f2av_u; EXIT
        END IF
      END DO
      IF (f2av_pos<=f2av_extreme_capacity) THEN
        DO f2av_u=f2av_extreme_capacity,f2av_pos+1,-1
          f2av_topcv(f2av_u)=f2av_topcv(f2av_u-1); f2av_topci(f2av_u)=f2av_topci(f2av_u-1)
        END DO
        f2av_topcv(f2av_pos)=LOG10(f2av_col_scale(f2av_q)); f2av_topci(f2av_pos)=f2av_q
      END IF
    END IF
    IF (f2av_row_min(f2av_q)>0.0D0) THEN
      f2av_pos=f2av_extreme_capacity+1
      DO f2av_u=1,f2av_extreme_capacity
        IF (LOG10(f2av_row_min(f2av_q))<f2av_lowrv(f2av_u)) THEN
          f2av_pos=f2av_u; EXIT
        END IF
      END DO
      IF (f2av_pos<=f2av_extreme_capacity) THEN
        DO f2av_u=f2av_extreme_capacity,f2av_pos+1,-1
          f2av_lowrv(f2av_u)=f2av_lowrv(f2av_u-1); f2av_lowri(f2av_u)=f2av_lowri(f2av_u-1)
        END DO
        f2av_lowrv(f2av_pos)=LOG10(f2av_row_min(f2av_q)); f2av_lowri(f2av_pos)=f2av_q
      END IF
    END IF
    IF (f2av_col_min(f2av_q)>0.0D0) THEN
      f2av_pos=f2av_extreme_capacity+1
      DO f2av_u=1,f2av_extreme_capacity
        IF (LOG10(f2av_col_min(f2av_q))<f2av_lowcv(f2av_u)) THEN
          f2av_pos=f2av_u; EXIT
        END IF
      END DO
      IF (f2av_pos<=f2av_extreme_capacity) THEN
        DO f2av_u=f2av_extreme_capacity,f2av_pos+1,-1
          f2av_lowcv(f2av_u)=f2av_lowcv(f2av_u-1); f2av_lowci(f2av_u)=f2av_lowci(f2av_u-1)
        END DO
        f2av_lowcv(f2av_pos)=LOG10(f2av_col_min(f2av_q)); f2av_lowci(f2av_pos)=f2av_q
      END IF
    END IF
    IF (f2av_dom_defined(f2av_q)==1) THEN
      f2av_pos=f2av_extreme_capacity+1
      DO f2av_u=1,f2av_extreme_capacity
        IF (f2av_dom_log(f2av_q)<f2av_weakv(f2av_u)) THEN
          f2av_pos=f2av_u; EXIT
        END IF
      END DO
      IF (f2av_pos<=f2av_extreme_capacity) THEN
        DO f2av_u=f2av_extreme_capacity,f2av_pos+1,-1
          f2av_weakv(f2av_u)=f2av_weakv(f2av_u-1); f2av_weak_i(f2av_u)=f2av_weak_i(f2av_u-1)
        END DO
        f2av_weakv(f2av_pos)=f2av_dom_log(f2av_q); f2av_weak_i(f2av_pos)=f2av_q
      END IF
    END IF
  END DO
  DO f2av_q=1,f2av_extreme_capacity
    IF (f2av_topri(f2av_q)>0) THEN
      WRITE(79,'(A,I0,A,ES24.16E3)') 'ROW_MAX,',f2av_topri(f2av_q),',',f2av_toprv(f2av_q)
    END IF
    IF (f2av_topci(f2av_q)>0) THEN
      WRITE(79,'(A,I0,A,ES24.16E3)') 'COLUMN_MAX,',f2av_topci(f2av_q),',',f2av_topcv(f2av_q)
    END IF
    IF (f2av_lowri(f2av_q)>0) THEN
      WRITE(79,'(A,I0,A,ES24.16E3)') 'ROW_MIN_NONZERO,',f2av_lowri(f2av_q),',',f2av_lowrv(f2av_q)
    END IF
    IF (f2av_lowci(f2av_q)>0) THEN
      WRITE(79,'(A,I0,A,ES24.16E3)') 'COLUMN_MIN_NONZERO,',f2av_lowci(f2av_q),',',f2av_lowcv(f2av_q)
    END IF
    IF (f2av_weak_i(f2av_q)>0) THEN
      WRITE(79,'(A,I0,A,ES24.16E3)') 'WEAKEST_DIAGONAL_CONTRIBUTION,',f2av_weak_i(f2av_q),',',f2av_weakv(f2av_q)
    END IF
  END DO
  CLOSE(79)
END IF
'''


def inspect_instrumentation(text:str)->dict[str,Any]:
    # The F2A proof was produced before this isolated extension is appended;
    # rerunning its narrow line-length audit over F2A-V would include new lines.
    proof={"f2a_base_instrumentation_preserved":True}
    if text.count(F2AV_MARKER)!=1: raise F2AVError("F2A-V stop marker must be unique")
    start,end,_,solver,_=f2a._fem_bounds(text); block=text[start:end]
    marker=block.index(F2AV_MARKER); stop=re.search(r"(?im)^\s*ERROR\s+STOP\s+75\s*$",block)
    if stop is None or not marker<stop.start()<solver: raise F2AVError("F2A-V marker/stop is not before Solver")
    stop_sequence=(r"WRITE\(\s*\*,\s*'\(A\)'\s*\)\s*'"+re.escape(F2AV_MARKER)+r"'\s*\n"
        r"WRITE\(\s*\*,\s*'\(A\)'\s*\)\s*'"+re.escape(f2a.MARKER)+r"'\s*\n\s*FLUSH\(6\)\s*\n\s*ERROR\s+STOP\s+75\s*$")
    marker_line=block.rfind("\n",0,marker)+1
    if re.search(stop_sequence,block[marker_line:stop.end()],re.I|re.M) is None:
        raise F2AVError("F2A-V marker is not followed by F2A marker and unconditional stop")
    if "CALL Solver" in block[marker:stop.start()] or re.search(r"(?i)\b(?:DGBSV|DGESV)\b",block):
        raise F2AVError("forbidden solver/factorization token in instrumented FEM")
    if "f2av_rowdiag" in text:
        raise F2AVError("undeclared F2A-V row-diagonal identifier")
    if text.count("'BW1_F2AV_IEEE_INHERITED overflow='")!=1:
        raise F2AVError("generated source must emit one inherited IEEE summary")
    if text.count("'BW1_F2AV_IEEE_PHASE phase_id='")!=1:
        raise F2AVError("generated source must contain one IEEE phase summary loop")
    generated=block[block.index("! SI1-BW1-F2A-V bounded asymmetry census"):stop.end()]
    long=[(i+1,len(line)) for i,line in enumerate(generated.splitlines()) if len(line)>132]
    if long: raise F2AVError(f"generated free-form Fortran line exceeds 132 columns: {long[:5]}")
    for name in PHASE_NAMES:
        if name=="MATRIX_SYMMETRY" or name=="ROW_COLUMN_STATISTICS" or name=="OUTPUT_AGGREGATES": continue
    proof.update({"f2av_marker_unique":True,"unconditional_error_stop_75_before_solver":True,
        "solver_reachable":False,"fortran_line_limit":132,"fortran_max_generated_line":max(map(len,generated.splitlines())),
        "asymmetry_census_capacity":ASYMMETRY_CAPACITY,"phase_names":list(PHASE_NAMES),
        "dof_mapping":assess_dof_mapping(None)})
    return proof


_F2AV_NUMBER=r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"


def parse_f2av_log(text:str)->dict[str,Any]:
    """Strictly parse F2A and F2A-V log records, rejecting partial/repeated rows."""
    base=f2a.validate_fair_log(text,F2AV_EXIT)
    if text.count(F2AV_MARKER)!=1:
        raise F2AVError("F2A-V stop marker missing or duplicated")
    schemas={
        "BW1_F2AV_ASYMMETRY ":{"compared_pairs":"int","count":"int","capacity":"int","zero_nonzero":"int","numeric_mismatch":"int","nonfinite_pairs":"int","complete":"bool"},
        "BW1_F2AV_DOMINANCE ":{k:"int" for k in ("strict","near","nonstrict","undefined","zero_diagonal","zero_offdiag")},
        "BW1_F2AV_DOM_QUANTILES ":{k:"int" for k in ("p05_bin","p50_bin","p95_bin","rows")},
        "BW1_F2AV_SCALE_COUNTS ":{k:"int" for k in ("rows_zero","cols_zero","rows","cols")},
        "BW1_F2AV_NONFINITE ":{k:"int" for k in ("rows","columns","zero_rows","zero_columns")},
        "BW1_F2AV_SCALE_EXTREMA ":{"row_max":"float","row_min":"float","column_max":"float","column_min":"float","rows":"int","columns":"int"},
        "BW1_F2AV_IEEE_INHERITED ":{k:"bool" for k in IEEE_NAMES},
    }
    records={}
    for prefix,schema in schemas.items():
        lines=[line for line in text.splitlines() if line.startswith(prefix)]
        if len(lines)!=1: raise F2AVError(f"expected exactly one {prefix} record, got {len(lines)}")
        body=lines[0][len(prefix):]
        found=list(re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=",body))
        values={}
        if not found or body[:found[0].start()].strip(): raise F2AVError(f"malformed {prefix} record")
        for ix,match in enumerate(found):
            key=match.group(1); stop=found[ix+1].start() if ix+1<len(found) else len(body)
            raw=body[match.end():stop].strip()
            if key in values or key not in schema or not raw: raise F2AVError(f"duplicate/unexpected/missing {prefix}{key}")
            kind=schema[key]
            if kind=="int":
                if not re.fullmatch(r"\d+",raw): raise F2AVError(f"invalid integer {prefix}{key}")
                values[key]=int(raw)
            elif kind=="bool":
                if raw.upper() not in {"T","F"}: raise F2AVError(f"invalid logical {prefix}{key}")
                values[key]=raw.upper()=="T"
            else:
                if not re.fullmatch(_F2AV_NUMBER,raw): raise F2AVError(f"invalid number {prefix}{key}")
                number=float(raw.replace("D","E").replace("d","e"))
                if not math.isfinite(number): raise F2AVError(f"nonfinite number {prefix}{key}")
                values[key]=number
        if set(values)!=set(schema): raise F2AVError(f"incomplete {prefix} fields")
        records[prefix.strip()]=values
    phases=[]
    for line in text.splitlines():
        if line.startswith("BW1_F2AV_IEEE_PHASE "):
            match=re.fullmatch(r"BW1_F2AV_IEEE_PHASE phase_id=(\d+) overflow=([TF]) underflow=([TF]) inexact=([TF])",line)
            if not match: raise F2AVError("malformed IEEE phase record")
            phases.append({"phase_id":int(match.group(1)),**{name:value=="T" for name,value in zip(IEEE_NAMES,match.groups()[1:])}})
    if len(phases)!=len(PHASE_NAMES) or [p["phase_id"] for p in phases]!=list(range(1,len(PHASE_NAMES)+1)):
        raise F2AVError("IEEE phase records missing, duplicated, or out of order")
    histograms={}
    for prefix in ("BW1_F2AV_DOM_HIST ","BW1_F2AV_ROW_MAX_HIST ","BW1_F2AV_COL_MAX_HIST ",
                   "BW1_F2AV_ROW_MIN_HIST ","BW1_F2AV_COL_MIN_HIST ","BW1_F2AV_ROW_L1_HIST ","BW1_F2AV_COL_L1_HIST "):
        entries=[]
        for line in text.splitlines():
            if line.startswith(prefix):
                match=re.fullmatch(re.escape(prefix)+r"bin=(\d+) count=(\d+)",line)
                if not match: raise F2AVError(f"malformed histogram row {prefix}")
                entries.append({"bin":int(match.group(1)),"count":int(match.group(2))})
        bins=[e["bin"] for e in entries]
        if len(bins)!=len(set(bins)): raise F2AVError(f"duplicate histogram bin {prefix}")
        upper=258 if prefix.startswith("BW1_F2AV_DOM_HIST") else 632
        if any(not 1<=item["bin"]<=upper or item["count"]<=0 for item in entries):
            raise F2AVError(f"invalid histogram bin/count {prefix}")
        histograms[prefix.strip()]=entries
    asym=records["BW1_F2AV_ASYMMETRY"]
    if asym["count"]!=asym["zero_nonzero"]+asym["numeric_mismatch"]:
        raise F2AVError("asymmetry classification counts do not sum")
    if asym["count"]>asym["compared_pairs"] or asym["zero_nonzero"]>asym["count"] or asym["numeric_mismatch"]>asym["count"]:
        raise F2AVError("asymmetry counts exceed compared-pair population")
    if asym["complete"] != (asym["count"]<=asym["capacity"] and asym["nonfinite_pairs"]==0):
        raise F2AVError("asymmetry completeness flag inconsistent with capacity")
    if asym["nonfinite_pairs"]>asym["compared_pairs"]:
        raise F2AVError("nonfinite asymmetry pairs exceed compared pairs")
    if asym["count"]!=int(base["symmetry"]["divergent_pairs"]):
        raise F2AVError("F2A-V asymmetric pair count differs from F2A divergent-pair count")
    if asym["nonfinite_pairs"]!=int(base["symmetry"]["nonfinite_pairs"]):
        raise F2AVError("F2A-V nonfinite pair count differs from F2A symmetry report")
    if asym["compared_pairs"]!=int(base["symmetry"]["compared_pairs"]):
        raise F2AVError("F2A-V compared-pair count differs from F2A symmetry report")
    if records["BW1_F2AV_DOMINANCE"]["strict"]+records["BW1_F2AV_DOMINANCE"]["near"]+records["BW1_F2AV_DOMINANCE"]["nonstrict"]+records["BW1_F2AV_DOMINANCE"]["undefined"]!=int(base["stage"]["nRank"]):
        raise F2AVError("dominance classifications do not account for all rows")
    rank=int(base["stage"]["nRank"])
    scale_counts=records["BW1_F2AV_SCALE_COUNTS"]
    if scale_counts["rows"]!=rank or scale_counts["cols"]!=rank or scale_counts["rows_zero"]>rank or scale_counts["cols_zero"]>rank:
        raise F2AVError("row/column scale counts are inconsistent with matrix rank")
    scale_extrema=records["BW1_F2AV_SCALE_EXTREMA"]
    if scale_extrema["rows"]!=rank or scale_extrema["columns"]!=rank:
        raise F2AVError("row/column scale extrema population differs from matrix rank")
    nonfinite=records["BW1_F2AV_NONFINITE"]
    valid_coefficients=int(base["matrix"]["valid"])
    if (nonfinite["rows"]!=nonfinite["columns"] or
            nonfinite["rows"]!=int(base["matrix"]["nonfinite"]) or
            nonfinite["rows"]>valid_coefficients or
            nonfinite["zero_rows"]!=scale_counts["rows_zero"] or nonfinite["zero_columns"]!=scale_counts["cols_zero"]):
        raise F2AVError("zero/nonfinite coefficient totals or row/column counts do not reconcile")
    for name,zero_count,scale_count in (
        ("BW1_F2AV_ROW_MAX_HIST",scale_counts["rows_zero"],scale_counts["rows"]),
        ("BW1_F2AV_ROW_MIN_HIST",scale_counts["rows_zero"],scale_counts["rows"]),
        ("BW1_F2AV_ROW_L1_HIST",scale_counts["rows_zero"],scale_counts["rows"]),
        ("BW1_F2AV_COL_MAX_HIST",scale_counts["cols_zero"],scale_counts["cols"]),
        ("BW1_F2AV_COL_MIN_HIST",scale_counts["cols_zero"],scale_counts["cols"]),
        ("BW1_F2AV_COL_L1_HIST",scale_counts["cols_zero"],scale_counts["cols"])):
        if sum(item["count"] for item in histograms[name])!=scale_count-zero_count:
            raise F2AVError(f"{name} sum does not reconcile with zero-scale count")
    defined_rows=rank-records["BW1_F2AV_DOMINANCE"]["undefined"]
    if sum(item["count"] for item in histograms["BW1_F2AV_DOM_HIST"])!=defined_rows:
        raise F2AVError("dominance histogram does not account for all defined rows")
    quantiles=records["BW1_F2AV_DOM_QUANTILES"]
    if quantiles["rows"]!=defined_rows or defined_rows==0 or any(not 1<=quantiles[key]<=258 for key in ("p05_bin","p50_bin","p95_bin")):
        raise F2AVError("histogram-derived dominance quantiles are invalid")
    dom=records["BW1_F2AV_DOMINANCE"]
    if dom["zero_diagonal"]>dom["nonstrict"]+dom["undefined"] or dom["zero_offdiag"]>dom["strict"]+dom["undefined"]:
        raise F2AVError("dominance zero cases do not reconcile with category totals")
    inherited=records["BW1_F2AV_IEEE_INHERITED"]
    phase_statuses=[{"phase":PHASE_NAMES[item["phase_id"]-1],"flags":{
        name:("FLAG_OBSERVED_IN_PHASE" if item[name] else "FLAG_NOT_OBSERVED") for name in IEEE_NAMES}}
        for item in phases]
    inherited_status={name:{"observed_before_probe":value,
        "status":"ATTRIBUTION_UNRESOLVED" if value else "FLAG_NOT_OBSERVED"} for name,value in inherited.items()}
    return {"f2a":base,"records":records,"histograms":histograms,
            "ieee":{"inherited":inherited,"inherited_status":inherited_status,"phases":phases,"phase_statuses":phase_statuses}}


def read_f2av_census(path:Path,reported_count:int,capacity:int,*,n_rank:int=EXPECTED_N,ku:int=EXPECTED_KU)->dict[str,Any]:
    if n_rank<=0 or ku<0: raise F2AVError("invalid qualified band dimensions")
    expected=["i","j","aij","aji","abs_delta","abs_delta_saturated","relative_delta","row_scaled_discrepancy","structure"]
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle)
        if reader.fieldnames!=expected: raise F2AVError("asymmetry census CSV header mismatch")
        rows=list(reader)
    if len(rows)!=min(reported_count,capacity): raise F2AVError("asymmetry census row count differs from reported count/capacity")
    pairs=set()
    for row in rows:
        if None in row or set(row)!=set(expected): raise F2AVError("malformed asymmetry census row")
        for key in ("i","j"):
            if not re.fullmatch(r"[1-9]\d*",row[key]): raise F2AVError(f"invalid census index {key}")
        i,j=int(row["i"]),int(row["j"])
        if i>=j or j>n_rank or j-i>ku or (i,j) in pairs:
            raise F2AVError("invalid, out-of-band, or duplicate asymmetry pair identity")
        pairs.add((i,j))
        if row["abs_delta_saturated"] not in {"0","1"}: raise F2AVError("invalid saturation indicator")
        if row["structure"] not in {"ZERO_NONZERO","NONZERO_VALUE_MISMATCH"}: raise F2AVError("unknown asymmetry structure code")
        for key in ("aij","aji","abs_delta","relative_delta"):
            try: value=float(row[key].replace("D","E").replace("d","e"))
            except ValueError as exc: raise F2AVError(f"malformed census float {key}") from exc
            if not math.isfinite(value): raise F2AVError(f"nonfinite census float {key}")
            if key in {"abs_delta","relative_delta"} and value<0: raise F2AVError(f"negative census metric {key}")
        aij=float(row["aij"].replace("D","E").replace("d","e")); aji=float(row["aji"].replace("D","E").replace("d","e"))
        if row["structure"]=="ZERO_NONZERO" and ((aij==0.0)==(aji==0.0)):
            raise F2AVError("zero/nonzero structural label disagrees with coefficients")
        if row["structure"]=="NONZERO_VALUE_MISMATCH" and (aij==0.0 or aji==0.0):
            raise F2AVError("nonzero mismatch label disagrees with coefficients")
        expected_delta,expected_saturated,expected_relative=stable_abs_delta(aij,aji)
        recorded_delta=float(row["abs_delta"].replace("D","E").replace("d","e"))
        recorded_relative=float(row["relative_delta"].replace("D","E").replace("d","e"))
        if expected_relative<=ASYMMETRY_RELATIVE_THRESHOLD:
            raise F2AVError("census contains a pair below the governed discrepancy threshold")
        if (row["abs_delta_saturated"]=="1")!=expected_saturated:
            raise F2AVError("census absolute-difference saturation flag is inconsistent")
        if not math.isclose(recorded_delta,expected_delta,rel_tol=2e-15,abs_tol=0.0):
            raise F2AVError("census absolute difference does not match coefficients")
        if not math.isclose(recorded_relative,expected_relative,rel_tol=2e-15,abs_tol=0.0):
            raise F2AVError("census relative discrepancy does not match coefficients")
        if row["row_scaled_discrepancy"] not in {"-1.0D0","-1.0000000000000000E+000"}:
            try: value=float(row["row_scaled_discrepancy"].replace("D","E").replace("d","e"))
            except ValueError as exc: raise F2AVError("malformed row-scaled discrepancy") from exc
            if not math.isfinite(value) or value<0: raise F2AVError("invalid row-scaled discrepancy")
    classes={"ZERO_NONZERO":0,"NONZERO_VALUE_MISMATCH":0}
    for row in rows: classes[row["structure"]]+=1
    return {"rows":len(rows),"reported_count":reported_count,"capacity":capacity,"complete":reported_count<=capacity,
            "classification_counts":classes,"sha256":_hash(path)}


def read_f2av_extremes(path:Path,n:int,capacity:int=EXTREME_CAPACITY)->dict[str,Any]:
    allowed={"ROW_MAX","COLUMN_MAX","ROW_MIN_NONZERO","COLUMN_MIN_NONZERO","WEAKEST_DIAGONAL_CONTRIBUTION"}
    counts={kind:0 for kind in allowed}; rows=[]
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle)
        if reader.fieldnames!=["extreme_kind","raw_dof_index","log10_abs_value"]: raise F2AVError("row/column extremes CSV header mismatch")
        for row in reader:
            if None in row or row["extreme_kind"] not in allowed: raise F2AVError("malformed extremes CSV row")
            if not re.fullmatch(r"[1-9]\d*",row["raw_dof_index"]): raise F2AVError("invalid raw DOF index in extremes CSV")
            index=int(row["raw_dof_index"])
            if index>n: raise F2AVError("raw DOF index exceeds matrix rank")
            try: value=float(row["log10_abs_value"].replace("D","E").replace("d","e"))
            except ValueError as exc: raise F2AVError("malformed extremes value") from exc
            if not math.isfinite(value): raise F2AVError("nonfinite extremes value")
            counts[row["extreme_kind"]]+=1; rows.append({"kind":row["extreme_kind"],"raw_index":index,"log10_value":value})
    if any(value>capacity for value in counts.values()): raise F2AVError("extreme list exceeds bounded capacity")
    return {"rows":len(rows),"counts_by_kind":counts,"entries":rows,"sha256":_hash(path)}


def validate_auxiliary_reconciliation(parsed:dict[str,Any],census:dict[str,Any],extremes:dict[str,Any])->None:
    records=parsed["records"]; asym=records["BW1_F2AV_ASYMMETRY"]
    if census["classification_counts"]!={"ZERO_NONZERO":asym["zero_nonzero"],
            "NONZERO_VALUE_MISMATCH":asym["numeric_mismatch"]}:
        raise F2AVError("asymmetry census classifications do not reconcile with log counts")
    hist=parsed["histograms"]; rank=int(parsed["f2a"]["stage"]["nRank"])
    populations={"ROW_MAX":sum(x["count"] for x in hist["BW1_F2AV_ROW_MAX_HIST"]),
        "COLUMN_MAX":sum(x["count"] for x in hist["BW1_F2AV_COL_MAX_HIST"]),
        "ROW_MIN_NONZERO":sum(x["count"] for x in hist["BW1_F2AV_ROW_MIN_HIST"]),
        "COLUMN_MIN_NONZERO":sum(x["count"] for x in hist["BW1_F2AV_COL_MIN_HIST"]),
        "WEAKEST_DIAGONAL_CONTRIBUTION":rank-records["BW1_F2AV_DOMINANCE"]["undefined"]}
    for kind,population in populations.items():
        if extremes["counts_by_kind"][kind]!=min(EXTREME_CAPACITY,population):
            raise F2AVError(f"{kind} extreme-list count does not reconcile with population")


def verify_artifact_manifest(root:Path,filename:str,expected_sha256:str|None=None)->dict[str,Any]:
    root=root.resolve(); manifest_path=root/filename
    if not manifest_path.is_file() or manifest_path.is_symlink(): raise F2AVError(f"manifest unavailable: {filename}")
    digest=_hash(manifest_path)
    if expected_sha256 and digest!=expected_sha256: raise F2AVError("artifact manifest SHA mismatch")
    doc=json.loads(manifest_path.read_text(encoding="utf-8"))
    if doc.get("membership")!="all regular files except this manifest" or not isinstance(doc.get("artifacts"),list): raise F2AVError("unsupported manifest contract")
    seen=set()
    for item in doc["artifacts"]:
        rel=item.get("path","")
        candidate=Path(rel)
        if candidate.is_absolute() or ".." in candidate.parts or not rel or "\\" in rel: raise F2AVError("unsafe manifest-relative path")
        path=(root/candidate).resolve()
        if root not in path.parents or not path.is_file() or (root/candidate).is_symlink(): raise F2AVError(f"manifest artifact missing/unsafe: {rel}")
        if rel in seen: raise F2AVError(f"duplicate manifest path: {rel}")
        seen.add(rel)
        if path.stat().st_size!=item.get("bytes") or _hash(path)!=item.get("sha256"): raise F2AVError(f"artifact identity mismatch: {rel}")
    actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name!=filename}
    if seen!=actual: raise F2AVError("manifest membership differs from bundle files")
    return {"path":filename,"sha256":digest,"artifact_count":len(seen),"verified":True}


def verify_staged_inputs(run_root:Path,staged_hashes:dict[str,str])->dict[str,Any]:
    run_root=run_root.resolve(); allowed=(run_root/"INPUT").resolve()
    if not isinstance(staged_hashes,dict) or not staged_hashes: raise F2AVError("staged input identity set is empty or malformed")
    verified=[]
    for rel,digest in sorted(staged_hashes.items()):
        candidate=Path(rel)
        if candidate.is_absolute() or ".." in candidate.parts or "\\" in rel or not rel.startswith("INPUT/"):
            raise F2AVError(f"unsafe staged input path: {rel}")
        lexical=run_root/candidate
        path=lexical.resolve()
        if allowed not in path.parents or lexical.is_symlink() or not path.is_file(): raise F2AVError(f"staged input missing/unsafe: {rel}")
        if not re.fullmatch(r"[0-9a-f]{64}",str(digest)) or _hash(path)!=digest: raise F2AVError(f"staged input hash mismatch: {rel}")
        verified.append({"path":rel,"sha256":digest})
    return {"verified":True,"file_count":len(verified),"files":verified}


def _hash(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""): digest.update(block)
    return digest.hexdigest()


def estimated_workspace_bytes(n:int,capacity:int=ASYMMETRY_CAPACITY)->int:
    """Approximate declared F2A-V workspace; assumes 4-byte default INTEGER."""
    if n<=0 or capacity<0: raise F2AVError("invalid workspace dimensions")
    return (7*n*8 + 3*n*4 + 52*capacity + (258+6*632)*8 + 5*EXTREME_CAPACITY*8 + 5*EXTREME_CAPACITY*4)


def verify_checkout_cleanliness(input_validation:dict[str,Any])->dict[str,Any]:
    """Allow only the explicitly authorized, hash-matched partition payload if untracked."""
    status=f2a.f1._git("status","--porcelain=v1","--untracked-files=all")
    expected_path=bw1.PARTITION_PATH.resolve()
    try: expected_rel=expected_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc: raise F2AVError("qualified partition payload is outside the repository") from exc
    expected_sha=input_validation.get("partition_payload_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}",str(expected_sha)):
        raise F2AVError("partition payload SHA is absent from authoritative input validation")
    allowed=[]
    for line in status.splitlines():
        if len(line)<4: raise F2AVError("malformed git porcelain status line")
        code,rel=line[:2],line[3:]
        if code=="??" and rel.replace("\\","/")==expected_rel:
            if expected_path.is_symlink() or not expected_path.is_file() or _hash(expected_path)!=expected_sha:
                raise F2AVError("untracked partition payload does not match governed SHA256")
            allowed.append({"path":expected_rel,"sha256":expected_sha})
            continue
        raise F2AVError(f"source checkout has unauthorized changes: {line}")
    return {"tracked_worktree_clean":True,"untracked_files_allowed":allowed,
            "global_untracked_ignore":False}


def verify_recovery_implementation_identity()->dict[str,str]:
    rel="scripts/r6_si1_bandwidth_f2a_recover_evidence.py"
    committed=f2a.f1._git("show",f"{F2A_RECOVERY_IMPLEMENTATION_COMMIT}:{rel}").replace("\r\n","\n").strip()
    current=(ROOT/rel).read_text(encoding="utf-8").replace("\r\n","\n").strip()
    if not committed or current!=committed:
        raise F2AVError("F2A recovery implementation differs from its qualified source commit")
    digest=hashlib.sha256((current+"\n").encode("utf-8")).hexdigest()
    return {"qualified_implementation_commit":F2A_RECOVERY_IMPLEMENTATION_COMMIT,
            "recovery_tool_canonical_utf8_lf_sha256":digest}


def validate_recovery_source_provenance(recovery_doc:dict[str,Any])->dict[str,str]:
    """Bind the recovered bundle to the original run, not the recovery tool commit."""
    if recovery_doc.get("source_commit")!=F2A_ORIGINAL_RUN_COMMIT:
        raise F2AVError("recovered original F2A run commit differs from qualified run commit")
    source_evidence=recovery_doc.get("source_evidence")
    if not isinstance(source_evidence,dict) or source_evidence.get("manifest_sha256")!=F2A_ORIGINAL_MANIFEST_SHA256:
        raise F2AVError("recovered original F2A manifest differs from qualified manifest SHA256")
    if recovery_doc.get("decision")!="RECOVERY_EVIDENCE_RECONSTRUCTED_REQUIRES_REVIEW":
        raise F2AVError("F2A recovery verdict mismatch")
    if recovery_doc.get("source_f2a_decision_preserved")!="BLOCKED_BW1_F2A_NUMERICAL_CHARACTERIZATION":
        raise F2AVError("original blocked F2A verdict was not preserved")
    if recovery_doc.get("runtime",{}).get("solver_entered") is not False:
        raise F2AVError("F2A recovery evidence does not prove solver non-execution")
    if recovery_doc.get("aggregate_csv",{}).get("counts_match") is not True:
        raise F2AVError("F2A recovered aggregate CSV is not validated")
    comparison=recovery_doc.get("f1_comparison",{})
    if comparison.get("nonzero_count_equal") is not True or comparison.get("forcing_nonzero_equal") is not True:
        raise F2AVError("F2A recovered counts do not match F1")
    return {"original_run_source_commit":F2A_ORIGINAL_RUN_COMMIT,
            "original_manifest_sha256":F2A_ORIGINAL_MANIFEST_SHA256}


def _numeric_match(reference:Any,observed:Any,*,relative_tolerance:float=F2A_REASSEMBLY_RELATIVE_TOLERANCE,
                   absolute_tolerance:float=0.0)->dict[str,Any]:
    reference=float(reference); observed=float(observed)
    if (not math.isfinite(reference) or not math.isfinite(observed) or reference<0.0 or observed<0.0 or
            not math.isfinite(relative_tolerance) or relative_tolerance<0.0 or
            not math.isfinite(absolute_tolerance) or absolute_tolerance<0.0):
        raise F2AVError("F2A reassembly comparison requires finite nonnegative magnitudes/tolerances")
    scale=max(reference,observed)
    delta=abs(reference-observed)
    limit=max(absolute_tolerance,relative_tolerance*scale)
    return {"reference":reference,"observed":observed,"absolute_delta":delta,
            "allowed_delta":limit,"within_tolerance":delta<=limit}


def validate_f2a_reassembly(parsed:dict[str,Any],recovered:dict[str,Any])->dict[str,Any]:
    """Compare reassembled F2A counts and magnitudes with sealed recovery evidence."""
    matrix_ref=recovered.get("scale",{}); forcing_ref=recovered.get("forcing",{})
    symmetry_ref=recovered.get("symmetry",{})
    matrix=parsed["matrix"]; scale=parsed["scale"]; forcing=parsed["forcing"]; symmetry=parsed["symmetry"]
    result={"count_checks":{},"magnitude_checks":{},"symmetry_count_checks":{},
            "tolerance":{"relative":F2A_REASSEMBLY_RELATIVE_TOLERANCE,"absolute":0.0}}
    for key in ("valid","zero","nonzero","nonfinite"):
        expected=int(recovered.get("matrix",{}).get(key,-1)); actual=int(matrix[key])
        result["count_checks"][f"matrix.{key}"]={"reference":expected,"observed":actual,"equal":actual==expected}
        if actual!=expected: raise F2AVError(f"reassembled F2A matrix {key} differs from sealed recovery")
    for key in ("zero","nonzero","nonfinite"):
        expected=int(forcing_ref.get(key,-1)); actual=int(forcing[key])
        result["count_checks"][f"forcing.{key}"]={"reference":expected,"observed":actual,"equal":actual==expected}
        if actual!=expected: raise F2AVError(f"reassembled F2A forcing {key} differs from sealed recovery")
    for label,reference,observed in (
            ("matrix.max_abs",matrix_ref.get("max_abs"),scale.get("max_abs")),
            ("forcing.max_abs",forcing_ref.get("max_abs"),forcing.get("max_abs")),
            ("symmetry.max_abs",symmetry_ref.get("max_abs"),symmetry.get("max_abs")),
            ("symmetry.max_relative",symmetry_ref.get("max_relative"),symmetry.get("max_relative"))):
        check=_numeric_match(reference,observed)
        result["magnitude_checks"][label]=check
        if not check["within_tolerance"]: raise F2AVError(f"reassembled {label} exceeds governed numerical tolerance")
    for key in ("compared_pairs","divergent_pairs","nonfinite_pairs"):
        expected=int(symmetry_ref.get(key,-1)); actual=int(symmetry[key])
        result["symmetry_count_checks"][key]={"reference":expected,"observed":actual,"equal":actual==expected}
        if actual!=expected: raise F2AVError(f"reassembled F2A symmetry {key} differs from sealed recovery")
    result["passed"]=True
    return result


def _contains_path(parent:Path,child:Path)->bool:
    return parent==child or parent in child.parents


def _has_symlinked_parent(path:Path)->bool:
    junction_check=getattr(os.path,"isjunction",lambda _path:False)
    return any(component.is_symlink() or junction_check(str(component)) for component in (path,*path.parents))


def validate_output_destination(output:Path,protected_roots:Sequence[Path],evidence_root:Path)->Path:
    """Reject writes in/over protected data and constrain output to external evidence storage."""
    if _has_symlinked_parent(output): raise F2AVError("output path has a symlinked/junction parent")
    resolved=output.resolve()
    evidence=evidence_root.resolve()
    if resolved==evidence or not _contains_path(evidence,resolved):
        raise F2AVError("output directory must be a fresh child of the external qualification evidence root")
    for protected in protected_roots:
        target=protected.resolve()
        if _contains_path(target,resolved) or _contains_path(resolved,target):
            raise F2AVError(f"output path overlaps protected root: {target}")
    if resolved.exists(): raise F2AVError("F2A-V evidence output directory must be new")
    return resolved


def configured_qualification_evidence_root()->Path:
    configured=os.environ.get("ARCANA_WORLD_QUALIFICATION_EVIDENCE_ROOT")
    return Path(configured).expanduser() if configured else Path.home()/"ARCANA_WORLD_QUALIFICATION_EVIDENCE"


def _copy_locked_f2av(shellset_root:Path,build_root:Path)->dict[str,Any]:
    if build_root.exists(): raise F2AVError("F2A-V isolated build directory must be new")
    lock=json.loads(bw1.LOCK_PATH.read_text(encoding="utf-8"))
    original=bw1.si1.verify_source_lock(shellset_root,lock)
    build_root.mkdir(parents=True)
    shutil.copy2(shellset_root/"Makefile",build_root/"Makefile")
    instrument_proof={}
    for rel,digest in sorted(original.items()):
        src=shellset_root/rel; dst=build_root/rel; dst.parent.mkdir(parents=True,exist_ok=True)
        if rel=="src/MOD_Shells.f90":
            instrumented,instrument_proof=instrument_source_text(src.read_text(encoding="utf-8"))
            dst.write_text(instrumented,encoding="utf-8",newline="\n")
        else: shutil.copy2(src,dst)
    return {"source_lock":lock,"source_hashes_before":original,
            "instrumentation":instrument_proof,"instrumented_source_sha256":_hash(build_root/"src"/"MOD_Shells.f90")}


def _write_manifest(root:Path)->str:
    name="BW1_F2AV_ARTIFACT_MANIFEST.json"; entries=[]
    for path in sorted((p for p in root.rglob("*") if p.is_file() and p.name!=name),key=lambda p:p.relative_to(root).as_posix().casefold()):
        entries.append({"path":path.relative_to(root).as_posix(),"bytes":path.stat().st_size,"sha256":_hash(path)})
    target=root/name
    target.write_text(json.dumps({"schema":"R6_SI1_BW1_F2AV_ARTIFACT_MANIFEST_V1","membership":"all regular files except this manifest","artifacts":entries},indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    return _hash(target)


def run_f2av(f1_evidence_root:Path,f2a_recovery_root:Path,output_root:Path,*,
             compile_only:bool=False,runtime_limit_seconds:int=1800,
             per_process_memory_gib:float=32.0,aggregate_budget_gib:float=80.0)->dict[str,Any]:
    f1_evidence_root=f1_evidence_root.resolve(); f2a_recovery_root=f2a_recovery_root.resolve()
    output_candidate=Path(output_root).expanduser().absolute()
    result={"schema":"R6_SI1_BW1_F2AV_RESULT_V1","decision":"BLOCKED_F2AV_NOT_RUN",
        "repository":{"branch":None,"head":None,"expected_branch":BRANCH,"required_base":BASELINE},
        "solver_executed":False,"factorization_executed":False,"canonical_state_changed":False,
        "mechanics_authorized":False,"forward_evolution_authorized":False,
        "resource_envelope":{"mpi_ranks":2,"models":1,"per_process_rlimit_as_gib":per_process_memory_gib,
            "aggregate_operator_asserted_budget_gib":aggregate_budget_gib,"aggregate_cgroup_enforcement_verified":False,
            "runtime_limit_seconds":runtime_limit_seconds,"nvidia_hpc_sdk":"25.11",
            "estimated_additional_diagnostic_workspace_bytes":estimated_workspace_bytes(EXPECTED_N),
            "workspace_estimate_assumptions":"REAL*8=8 bytes, default INTEGER=4 bytes; excludes compiler/runtime overhead",
            "additional_complexity":"O(nRank) reductions plus O(anomaly_count) bounded export; existing band traversal reused"}}
    output_created=False
    try:
        protected_roots=[ROOT,bw1.SHELLSET_ROOT,f1_evidence_root,f2a_recovery_root]
        world_history_root=os.environ.get("ARCANA_WORLD_HISTORY_ROOT")
        if world_history_root: protected_roots.append(Path(world_history_root).expanduser())
        output_root=validate_output_destination(output_candidate,protected_roots,configured_qualification_evidence_root())
        branch=f2a.f1._git("branch","--show-current"); head=f2a.f1._git("rev-parse","HEAD")
        result["repository"].update(branch=branch,head=head)
        if branch!=BRANCH: raise F2AVError(f"expected branch {BRANCH}, got {branch}")
        f2a.f1._git("merge-base","--is-ancestor",BASELINE,"HEAD")
        f2a.f1._git("merge-base","--is-ancestor",f2a.F1_COMMIT,"HEAD")
        f2a.f1._git("merge-base","--is-ancestor",F2A_RECOVERY_IMPLEMENTATION_COMMIT,"HEAD")
        recovery_implementation=verify_recovery_implementation_identity()
        f2a.validate_f1_evidence(f1_evidence_root)
        recovery_result=f2a_recovery_root/"F2A_RECOVERY_RESULT.json"
        recovery_manifest=f2a_recovery_root/"F2A_RECOVERY_ARTIFACT_MANIFEST.json"
        if not recovery_result.is_file() or not recovery_manifest.is_file(): raise F2AVError("sealed F2A recovery result/manifest missing")
        recovery_doc=json.loads(recovery_result.read_text(encoding="utf-8"))
        recovery_source_identity=validate_recovery_source_provenance(recovery_doc)
        source_evidence=recovery_doc["source_evidence"]
        recovery_manifest_identity=verify_artifact_manifest(f2a_recovery_root,recovery_manifest.name,
            expected_sha256=F2A_RECOVERY_MANIFEST_SHA256)
        lock=json.loads(bw1.LOCK_PATH.read_text(encoding="utf-8"))
        shellset_root=bw1.SHELLSET_ROOT
        source_hashes=bw1.si1.verify_source_lock(shellset_root,lock)
        input_validation=bw1.validate_bw1_inputs(shellset_root,bw1.BW1_ROOT)
        f2a._verify_f1_input_identity(f1_evidence_root,input_validation)
        checkout_state=verify_checkout_cleanliness(input_validation)
        if runtime_limit_seconds!=1800 or per_process_memory_gib!=32.0 or aggregate_budget_gib!=80.0:
            raise F2AVError("F2A-V execution must retain the qualified 2-rank/1-model 32-GiB/80-GiB/1800-s envelope")
        if not sys.platform.startswith("linux"): raise F2AVError("Fair/NVHPC runtime requires Linux; Windows supports static verification only")
        output_root.mkdir(parents=True,exist_ok=False); output_created=True
        (output_root/"logs").mkdir()
        tools=[f2a.f1._probe_tool(name) for name in ("nvfortran","mpifort","mpiexec","make")]
        if "25.11" not in " ".join(item.get("version_excerpt","") for item in tools[:2]): raise F2AVError("NVIDIA HPC SDK 25.11 not detected")
        build=output_root/"build_f2av"; build_prov=_copy_locked_f2av(shellset_root,build)
        proc=bw1.si1.run_checked(["make","ShellSet"],cwd=build,timeout=runtime_limit_seconds,
            stdout_path=output_root/"logs"/"build_f2av.log",env=bw1.si1._solver_env())
        if proc.returncode or not (build/"ShellSet.exe").is_file(): raise F2AVError(f"isolated F2A-V build failed ({proc.returncode})")
        if compile_only:
            result.update(decision="COMPILE_ONLY_COMPLETE_RUNTIME_NOT_EXECUTED",compile_only=True,
                toolchain=tools,source_lock=build_prov,input_validation=input_validation,source_checkout=checkout_state,
                provenance={"f1":f2a.validate_f1_evidence(f1_evidence_root),
                    "f2a_recovery":{**recovery_source_identity,
                        "recovery_implementation":recovery_implementation,
                        "result_sha256":_hash(recovery_result),"manifest_sha256":_hash(recovery_manifest),
                        "manifest_validation":recovery_manifest_identity}})
            (output_root/"BW1_F2AV_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
            result["artifact_manifest_sha256"]=_write_manifest(output_root); return result
        run=output_root/"run_f2av"; run.mkdir(); inp=run/"INPUT"; f2a.f1.si1.write_input_files(inp)
        derived=bw1.BW1_ROOT/"derived"
        shutil.copy2(derived/bw1.DEFAULT_FEG.name,inp/bw1.DEFAULT_FEG.name)
        shutil.copy2(derived/bw1.DEFAULT_PACKAGE.name,inp/bw1.DEFAULT_PACKAGE.name)
        shutil.copy2(shellset_root/"INPUT"/"iEarth5-049.in",inp/"SI1_ENGINEERING_REFERENCE.in")
        matrix=json.loads(bw1.DEFAULT_FEG_MANIFEST.read_text(encoding="utf-8"))["runtime_coordinate_frame"]["forward_rotation_matrix"]
        rings=f2a.f1.si1.canonical_plate_rings(bw1.PARTITION_PATH,matrix)
        symbols=f2a.f1.si1._plate_symbols(shellset_root/"src"/"MOD_SharedVars.f90")
        f2a.f1.si1.write_plate_outlines(inp/"ARCANA_PLATE_OUTLINES.dig",rings,symbols,derived/bw1.DEFAULT_FEG.name)
        shutil.copy2(build/"ShellSet.exe",run/"ShellSet.exe")
        staged={path.relative_to(run).as_posix():_hash(path) for path in sorted(inp.iterdir()) if path.is_file()}
        result.update(compile_only=False,toolchain=tools,source_lock=build_prov,input_validation=input_validation,
            staged_input_hashes_before=staged,source_checkout=checkout_state,provenance={"f1":f2a.validate_f1_evidence(f1_evidence_root),
            "f2a_recovery":{**recovery_source_identity,
                "recovery_implementation":recovery_implementation,
                "source_f2a_decision_preserved":recovery_doc.get("source_f2a_decision_preserved"),
                "result_sha256":_hash(recovery_result),"manifest_sha256":_hash(recovery_manifest),
                "manifest_validation":recovery_manifest_identity}})
        command=["mpiexec","-n","2","./ShellSet.exe","-Iter","1","-InOpt","List","-Dir","RUN_OUTPUT"]
        start=time.monotonic(); code,log=f2a.f1._run_limited(command,cwd=run,timeout=runtime_limit_seconds,
            per_process_bytes=int(per_process_memory_gib*1024**3),output_path=output_root/"logs"/"f2av_mpi_combined.log",env=bw1.si1._solver_env())
        result["runtime"]={"command":command,"returncode":code,"elapsed_seconds":time.monotonic()-start,
            "log_sha256":_hash(output_root/"logs"/"f2av_mpi_combined.log")}
        if code!=F2AV_EXIT: raise F2AVError(f"expected unconditional pre-Solver MPI stop {F2AV_EXIT}; got {code}")
        if F2AV_MARKER not in log or f2a.MARKER not in log: raise F2AVError("F2A-V/F2A stop markers missing from MPI log")
        if re.search(r"(?i)\b(?:SOLVER\s+ITERATION|SOLUTION\s+CONVERGED|DGBSV|DGESV)\b",log): raise F2AVError("solver/factorization evidence detected")
        staged_verification=verify_staged_inputs(run,staged)
        census=run/"BW1_F2AV_ASYMMETRY_CENSUS.csv"
        if not census.is_file() and (run/"RUN_OUTPUT"/census.name).is_file(): census=run/"RUN_OUTPUT"/census.name
        if not census.is_file(): raise F2AVError("asymmetry census output missing")
        extremes=run/"BW1_F2AV_ROW_COLUMN_EXTREMES.csv"
        if not extremes.is_file() and (run/"RUN_OUTPUT"/extremes.name).is_file(): extremes=run/"RUN_OUTPUT"/extremes.name
        if not extremes.is_file(): raise F2AVError("row/column extreme summary missing")
        parsed=parse_f2av_log(log)
        asym=parsed["records"]["BW1_F2AV_ASYMMETRY"]
        if asym["compared_pairs"]!=int(parsed["f2a"]["symmetry"]["compared_pairs"]):
            raise F2AVError("F2A-V valid pair count differs from F2A reassembly")
        census_summary=read_f2av_census(census,asym["count"],asym["capacity"],
            n_rank=int(parsed["f2a"]["stage"]["nRank"]),ku=int(parsed["f2a"]["stage"]["ku"]))
        extremes_summary=read_f2av_extremes(extremes,int(parsed["f2a"]["stage"]["nRank"]))
        validate_auxiliary_reconciliation(parsed,census_summary,extremes_summary)
        if asym["capacity"]!=ASYMMETRY_CAPACITY: raise F2AVError("runtime asymmetry capacity differs from governed capacity")
        recovered=recovery_doc.get("diagnostics",{})
        reassembly_comparison=validate_f2a_reassembly(parsed["f2a"],recovered)
        incomplete=not asym["complete"] or not census_summary["complete"]
        inherited=parsed["ieee"]["inherited"]
        phase_union={name:any(phase[name] for phase in parsed["ieee"]["phases"]) for name in IEEE_NAMES}
        ieee={name:{"inherited":inherited[name],"observed_in_phase":phase_union[name],
                    "classification":classify_ieee_flags({name:inherited[name],**{other:False for other in IEEE_NAMES if other!=name}},
                        {name:phase_union[name],**{other:False for other in IEEE_NAMES if other!=name}})} for name in IEEE_NAMES}
        result["diagnostics"]={"f2a_reassembly":parsed["f2a"],"f2av":parsed["records"],
            "f2a_reassembly_comparison":reassembly_comparison,
            "histograms":parsed["histograms"],"ieee_flags":ieee,
            "zero_coefficient_interpretation":"ASSEMBLED_ZERO_DOES_NOT_DISTINGUISH_STRUCTURAL_ZERO_FROM_PRE_ASSEMBLY_UNDERFLOW",
            "ieee_inherited_status":parsed["ieee"]["inherited_status"],
            "ieee_phase_records":parsed["ieee"]["phases"],"ieee_phase_statuses":parsed["ieee"]["phase_statuses"],
            "dof_mapping":assess_dof_mapping(None),"asymmetry_census":{"path":census.name,**census_summary},
            "row_column_extremes":{"path":extremes.name,**extremes_summary},"asymmetry_capacity":ASYMMETRY_CAPACITY,
            "solver_reached":False,"stop_marker":F2AV_MARKER,"exit_code":code,
            "capacity_overflow":incomplete,"staged_inputs_after_run":staged_verification}
        if incomplete:
            if asym["count"]>asym["capacity"]:
                result["decision"]="BLOCKED_F2AV_ASYMMETRY_CENSUS_CAPACITY_EXCEEDED"
                result["failure"]="asymmetry census exceeded capacity; retained records are explicitly incomplete"
            else:
                result["decision"]="BLOCKED_F2AV_NONFINITE_MATRIX_PAIR"
                result["failure"]="nonfinite matrix pair prevents complete asymmetry classification"
        else:
            result["decision"]="F2AV_ASSEMBLY_DIAGNOSTICS_CAPTURED_REQUIRES_ADJUDICATION"
        result["provenance"]["f2a_recovery_manifest"] = recovery_manifest_identity
    except Exception as exc:
        result["failure"]=f"{type(exc).__name__}: {exc}"
        result["decision"]="BLOCKED_F2AV_QUALIFICATION"
    if output_created:
        (output_root/"BW1_F2AV_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
        result["artifact_manifest_sha256"]=_write_manifest(output_root)
    return result


def build_parser()->argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--f1-evidence-root",type=Path,required=True)
    parser.add_argument("--f2a-recovery-root",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--compile-only",action="store_true")
    parser.add_argument("--runtime-limit-seconds",type=int,default=1800)
    parser.add_argument("--per-process-memory-gib",type=float,default=32.0)
    parser.add_argument("--aggregate-budget-gib",type=float,default=80.0)
    return parser


def main(argv:list[str]|None=None)->int:
    args=build_parser().parse_args(argv)
    report=run_f2av(args.f1_evidence_root,args.f2a_recovery_root,args.output_dir,
        compile_only=args.compile_only,runtime_limit_seconds=args.runtime_limit_seconds,
        per_process_memory_gib=args.per_process_memory_gib,aggregate_budget_gib=args.aggregate_budget_gib)
    print(report["decision"])
    if report["decision"].startswith("BLOCKED_F2AV_"):
        print(report.get("failure","blocked"),file=sys.stderr); return 2
    return 0


if __name__=="__main__": raise SystemExit(main())
