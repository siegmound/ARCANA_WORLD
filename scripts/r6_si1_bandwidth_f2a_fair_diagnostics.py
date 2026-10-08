#!/usr/bin/env python3
"""Build/run a disposable SI1-BW1-F2A matrix characterization; never solve."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
import r6_si1_bandwidth_bw1_fair_preflight as bw1  # noqa: E402
import r6_si1_bandwidth_f1_fair_preflight as f1  # noqa: E402

F1_COMMIT = "3b8ab7a588d3b658255e41bd5a92e5a31b78604a"
F1_RESULT_SHA256 = "174577051c58375346e27c4fe5382e3635706ba00a863924ab59d4bf37b3849a"
F1_MANIFEST_SHA256 = "18a935a841e04e52b7e8a0d4d7d0919b004a00f9e35a64b1febd9c9a3667b7cd"
EXPECTED_BRANCH = "r6/si1-bandwidth-f2a"
EXIT_CODE = 75
MARKER = "BW1_F2A_STOP_BEFORE_SOLVER"
EXPECTED = {"nRank": 128884, "kl": 727, "ku": 727, "nKRows": 2182, "iDiagonal": 1455}
FEM_START_RE = f1.FEM_START_RE
SOLVE_RE = re.compile(r"(?i)(?:\bDGBSV\b|\bDGESV\b|\bSOLUTION\s+CONVERGED\b|\bSOLVER\s+ITERATION\b)")
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"


class F2AError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_f1_evidence(root: Path) -> dict[str, Any]:
    """Verify sealed F1 summary/manifest and every manifest-listed byte file."""
    root = Path(root).resolve()
    result_path, manifest_path = root / "BW1_F1_RESULT.json", root / "BW1_F1_ARTIFACT_MANIFEST.json"
    if _sha(result_path) != F1_RESULT_SHA256 or _sha(manifest_path) != F1_MANIFEST_SHA256:
        raise F2AError("F1 result/manifest SHA256 does not match the qualified evidence seal")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if result.get("decision") != "PASS_BW1_FAIR_ASSEMBLY_ONLY":
        raise F2AError("F1 evidence is not a PASS")
    if result.get("repository", {}).get("head") != F1_COMMIT:
        raise F2AError("F1 source commit in evidence differs from qualified commit")
    matrix = result.get("diagnostics", {}).get("system", {}).get("matrix", {})
    force = result.get("diagnostics", {}).get("system", {}).get("forcing", {})
    stage = result.get("diagnostics", {}).get("system", {}).get("stage", {})
    expected = {"rows": 2182, "cols": 128884, "bytes": 2249799104, "nonzero": 1804327,
                "nonfinite": 0, "diag_nonzero": 128884, "max_abs": 3.650823911297015e32}
    for key, val in expected.items():
        if matrix.get(key) != val:
            raise F2AError(f"F1 matrix evidence mismatch for {key}: {matrix.get(key)!r}")
    for key,val in {"nRank":128884,"nKRows":2182,"nCodiagonals":727,"iDiagonal":1455}.items():
        if stage.get(key)!=val: raise F2AError(f"F1 stage evidence mismatch for {key}")
    if matrix.get("finite")!=matrix["rows"]*matrix["cols"] or matrix.get("diag_zero")!=0 or matrix.get("diagonal_row")!=1455:
        raise F2AError("F1 finite/diagonal evidence does not match the qualified baseline")
    if force.get("count")!=128884 or force.get("finite")!=128884 or force.get("nonfinite")!=0:
        raise F2AError("F1 forcing cardinality/finiteness evidence is inconsistent")
    if force.get("nonzero") != 128884 or force.get("max_abs") != 1.3496974460580477e18:
        raise F2AError("F1 forcing evidence differs from qualified baseline")
    if result.get("diagnostics", {}).get("mpi_exit_code") != 74 or result.get("diagnostics", {}).get("solver_entered") is not False or result.get("staged_inputs_unchanged") is not True or result.get("preservation_hashes_verified") is not True:
        raise F2AError("F1 stop/solver/input-preservation evidence is invalid")
    entries = manifest.get("artifacts")
    if not isinstance(entries, list):
        raise F2AError("F1 manifest artifacts missing")
    listed=set()
    for entry in entries:
        path = (root / entry["path"]).resolve()
        if root not in path.parents or not path.is_file() or path.stat().st_size != entry["bytes"] or _sha(path) != entry["sha256"]:
            raise F2AError(f"F1 manifest artifact failed verification: {entry.get('path')}")
        listed.add(Path(entry["path"]).as_posix())
    actual={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name!="BW1_F1_ARTIFACT_MANIFEST.json"}
    if actual!=listed: raise F2AError("F1 evidence directory membership differs from its sealed manifest")
    return {"source_commit": F1_COMMIT, "result_sha256": F1_RESULT_SHA256,
            "manifest_sha256": F1_MANIFEST_SHA256, "artifact_count": len(entries),
            "decision": result["decision"], "f1_reference_metrics": {"matrix": matrix, "forcing": force}}


def _verify_f1_input_identity(f1_root: Path, current: dict[str, Any]) -> dict[str, Any]:
    prior=json.loads((Path(f1_root)/"BW1_F1_RESULT.json").read_text(encoding="utf-8"))
    old=prior.get("input_validation",{})
    pairs=[]
    for section in ("source_inputs","derived_inputs"):
        before=old.get(section,{}); now=current.get(section,{})
        for key,value in before.items():
            if key.endswith("_sha256"):
                if now.get(key)!=value: raise F2AError(f"current input identity differs from F1: {section}.{key}")
                pairs.append(f"{section}.{key}")
    for key in ("partition_payload_sha256",):
        if old.get(key)!=current.get(key): raise F2AError(f"current F1 spatial/mesh identity differs: {key}")
        pairs.append(key)
    if not pairs: raise F2AError("F1 evidence has no comparable FEG/runtime input identities")
    return {"same_f1_input_sha256_fields":pairs,"equal":True}


def compare_reassembly_to_f1(diagnostics:dict[str,Any], f1_metrics:dict[str,Any]) -> dict[str,Any]:
    f1matrix=f1_metrics["matrix"]; f1force=f1_metrics["forcing"]
    f2matrix=diagnostics["matrix"]; f2scale=diagnostics["scale"]; f2force=diagnostics["forcing"]
    f2_total=int(f2matrix["nonzero"])+int(f2matrix["fill_nonzero"])+int(f2matrix["pad_nonzero"])
    f2max=float(f2scale["max_abs"]); f1max=float(f1matrix["max_abs"])
    f2fmax=float(f2force["max_abs"]); f1fmax=float(f1force["max_abs"])
    def relative(a:float,b:float)->float:
        return abs(a-b)/max(abs(a),abs(b)) if max(abs(a),abs(b)) else 0.0
    return {"f1_total_storage_nonzero":f1matrix["nonzero"],"f2a_total_storage_nonzero":f2_total,
        "nonzero_count_equal":f2_total==f1matrix["nonzero"],"f1_storage_max_abs":f1max,"f2a_physical_max_abs":f2max,
        "max_abs_relative_delta":relative(f2max,f1max),"forcing_nonzero_equal":int(f2force["nonzero"])==int(f1force["nonzero"]),
        "f1_forcing_max_abs":f1fmax,"f2a_forcing_max_abs":f2fmax,"forcing_max_abs_relative_delta":relative(f2fmax,f1fmax),
        "interpretation":"numeric comparison only; not a claim of bitwise reproducibility or solver conditioning"}


def analyze_band(k: list[list[float]], *, n_rank: int, kl: int, ldab: int,
                 diagonal_row: int, force: list[float]) -> dict[str, Any]:
    """Small-fixture reference for AB(diagonal_row+i-j,j)=A(i,j), 1-based."""
    if len(k) != ldab or any(len(row) != n_rank for row in k) or len(force) != n_rank:
        raise F2AError("fixture dimensions do not match band storage")
    entries: dict[tuple[int,int],float] = {}; fill=[]; padding=[]; rows=[[] for _ in range(n_rank)]
    for j in range(1,n_rank+1):
        for s in range(1,ldab+1):
            x=k[s-1][j-1]
            if s<=kl: fill.append(x); continue
            i=s-diagonal_row+j
            if not 1<=i<=n_rank: padding.append(x); continue
            entries[(i,j)]=x; rows[i-1].append((j,x))
    diag=[entries.get((i,i),0.0) for i in range(1,n_rank+1)]
    dominant=[]
    for i,row in enumerate(rows,1):
        off=[abs(x) for j,x in row if j!=i and math.isfinite(x)]
        scale=max(off,default=0.0)
        scaled=math.fsum(x/scale for x in off) if scale else 0.0
        dominant.append(abs(diag[i-1])/scale>scaled if scale else diag[i-1]!=0.0)
    pairs=[]; divergent=0; max_abs=0.0; max_rel=0.0
    for (i,j),x in entries.items():
        y=entries.get((j,i))
        if i<j and y is not None and math.isfinite(x) and math.isfinite(y):
            scale=max(abs(x),abs(y)); rel=abs(x/scale-y/scale) if scale else 0.0
            delta=min(float.fromhex('0x1.fffffffffffffp+1023'),scale*rel)
            pairs.append((x,y)); max_abs=max(max_abs,delta); max_rel=max(max_rel,rel); divergent+=rel>1e-12
    valid=list(entries.values()); finite=[abs(x) for x in valid if math.isfinite(x)]; nonzero=[x for x in finite if x]
    def hist(values:list[float])->dict[str,int]:
        out:dict[str,int]={}
        for x in values:
            if math.isfinite(x) and x:
                b=max(-323,min(308,math.floor(math.log10(abs(x))))); out[str(b)]=out.get(str(b),0)+1
        return out
    return {"valid":len(valid),"zero":sum(math.isfinite(x) and x==0 for x in valid),
        "nonzero":len(nonzero),"nonfinite":sum(not math.isfinite(x) for x in valid),
        "fill_nonzero":sum(math.isfinite(x) and x!=0 for x in fill),"padding_nonzero":sum(math.isfinite(x) and x!=0 for x in padding),
        "min_nonzero_abs":min(map(abs,nonzero),default=None),"max_abs":max(map(abs,nonzero),default=0.0),
        "coefficient_log10_dynamic_range":math.log10(max(map(abs,nonzero)))-math.log10(min(map(abs,nonzero))) if nonzero else None,
        "matrix_log10_abs":hist(nonzero),"diagonal_log10_abs":hist(diag),
        "diagonal_positive":sum(math.isfinite(x) and x>0 for x in diag),"diagonal_negative":sum(math.isfinite(x) and x<0 for x in diag),
        "diagonal_zero":sum(math.isfinite(x) and x==0 for x in diag),
        "strictly_diagonally_dominant_rows":sum(dominant),"nondominant_rows":len(dominant)-sum(dominant),
        "symmetry_pairs":len(pairs),"symmetry_divergent_pairs":divergent,"symmetry_max_abs_delta":max_abs,"symmetry_max_relative_delta":max_rel,
        "forcing_zero":sum(math.isfinite(x) and x==0 for x in force),"forcing_nonzero":sum(math.isfinite(x) and x!=0 for x in force),
        "forcing_nonfinite":sum(not math.isfinite(x) for x in force),"forcing_log10_abs":hist(force)}


def coarse_index(index_1based: int, dimension: int, bins: int=256) -> int:
    if dimension<=0 or bins<=0 or not 1<=index_1based<=dimension:
        raise F2AError("coarse heatmap index outside one-based mathematical dimension")
    return 1+min(bins-1,((index_1based-1)*bins)//dimension)


def _fem_bounds(text: str) -> tuple[int, int, int, int, int]:
    starts = list(FEM_START_RE.finditer(text))
    if len(starts) != 1:
        raise F2AError(f"expected one FEM definition; found {len(starts)}")
    start = starts[0].start()
    end_match = re.search(r"(?im)^\s*END\s+SUBROUTINE\s+FEM\b", text[start:])
    if not end_match:
        raise F2AError("FEM end anchor missing")
    end = start + end_match.end()
    block = text[start:end]
    offsets: dict[str, int] = {}
    for name in ("BuildF", "BuildK", "AddFSt", "VBCs", "Solver"):
        hits = list(re.finditer(rf"(?im)^\s*CALL\s+{name}\b", block))
        if len(hits) != 1:
            raise F2AError(f"expected one {name} call in FEM; found {len(hits)}")
        offsets[name] = hits[0].start()
    order = [offsets[n] for n in ("BuildF", "BuildK", "AddFSt", "VBCs", "Solver")]
    if order != sorted(order):
        raise F2AError("FEM assembly call order changed")
    vbc_end = f1._call_end(block, offsets["VBCs"])
    vbc_line_end = block.find("\n", vbc_end)
    if vbc_line_end < 0:
        raise F2AError("VBCs call line ending missing")
    return start, end, vbc_line_end + 1, offsets["Solver"], len(block)


def _fortran_block() -> str:
    # Scan physical A entries through LAPACK's AB mapping. No matrix copy/factorization.
    return r'''! SI1-BW1-F2A: read-only numerical characterization, before Solver.
f2a_valid=0_8; f2a_zero=0_8; f2a_nonzero=0_8; f2a_nonfinite=0_8
f2a_fill_nonzero=0_8; f2a_fill_nonfinite=0_8; f2a_pad_nonzero=0_8; f2a_pad_nonfinite=0_8
f2a_sym_pairs=0_8; f2a_sym_div=0_8; f2a_sym_nonfinite=0_8
f2a_dom_strict=0_8; f2a_dom_nonstrict=0_8; f2a_diag_pos=0_8; f2a_diag_neg=0_8; f2a_diag_zero=0_8
f2a_maxabs=0.0D0; f2a_minabs=HUGE(1.0D0); f2a_sym_abs=0.0D0; f2a_sym_rel=0.0D0
f2a_force_zero=0_8; f2a_force_nonzero=0_8; f2a_force_nonfinite=0_8
f2a_force_max=0.0D0; f2a_force_min=HUGE(1.0D0)
f2a_p50=-9999; f2a_p95=-9999; f2a_cum=0_8
f2a_range=0.0D0
f2a_worst_i=0; f2a_worst_j=0; f2a_worst_a=0.0D0; f2a_worst_b=0.0D0
f2a_heat=0_8; f2a_heat_valid=0_8
f2a_hist=0_8; f2a_dhist=0_8; f2a_rhist=0_8; f2a_fhist=0_8
f2a_rowscale=0.0D0; f2a_rowsum=0.0D0; f2a_rowdiag=0.0D0
DO f2a_j=1,nRank
  DO f2a_s=1,nKRows
    IF (f2a_s <= nCodiagonals) THEN
      IF (.NOT. IEEE_IS_FINITE(k(f2a_s,f2a_j))) THEN
        f2a_fill_nonfinite=f2a_fill_nonfinite+1_8
      ELSE IF (k(f2a_s,f2a_j) /= 0.0D0) THEN
        f2a_fill_nonzero=f2a_fill_nonzero+1_8
      END IF
    ELSE
      f2a_i=f2a_s-iDiagonal+f2a_j
      IF (f2a_i < 1 .OR. f2a_i > nRank) THEN
        IF (.NOT. IEEE_IS_FINITE(k(f2a_s,f2a_j))) THEN
          f2a_pad_nonfinite=f2a_pad_nonfinite+1_8
        ELSE IF (k(f2a_s,f2a_j) /= 0.0D0) THEN
          f2a_pad_nonzero=f2a_pad_nonzero+1_8
        END IF
      ELSE
        f2a_valid=f2a_valid+1_8
        f2a_bi=1+MIN(255,INT(256.0D0*DBLE(f2a_i-1)/DBLE(nRank)))
        f2a_bj=1+MIN(255,INT(256.0D0*DBLE(f2a_j-1)/DBLE(nRank)))
        f2a_heat_valid(f2a_bi,f2a_bj)=f2a_heat_valid(f2a_bi,f2a_bj)+1_8
        f2a_x=k(f2a_s,f2a_j)
        IF (.NOT. IEEE_IS_FINITE(f2a_x)) THEN
          f2a_nonfinite=f2a_nonfinite+1_8
        ELSE IF (f2a_x == 0.0D0) THEN
          f2a_zero=f2a_zero+1_8
        ELSE
          f2a_nonzero=f2a_nonzero+1_8
          f2a_ax=ABS(f2a_x); f2a_maxabs=MAX(f2a_maxabs,f2a_ax); f2a_minabs=MIN(f2a_minabs,f2a_ax)
          f2a_bin=MAX(-323,MIN(308,FLOOR(LOG10(f2a_ax))))+324
          f2a_hist(f2a_bin)=f2a_hist(f2a_bin)+1_8
          f2a_heat(f2a_bi,f2a_bj)=f2a_heat(f2a_bi,f2a_bj)+1_8
        END IF
        IF (f2a_i == f2a_j) THEN
          f2a_rowdiag(f2a_i)=k(f2a_s,f2a_j)
        ELSE IF (IEEE_IS_FINITE(k(f2a_s,f2a_j))) THEN
          f2a_ax=ABS(k(f2a_s,f2a_j))
          IF (f2a_ax > f2a_rowscale(f2a_i)) THEN
            IF (f2a_rowscale(f2a_i) > 0.0D0) THEN
              f2a_rowsum(f2a_i)=f2a_rowsum(f2a_i)*(f2a_rowscale(f2a_i)/f2a_ax)
            END IF
            f2a_rowscale(f2a_i)=f2a_ax
            f2a_rowsum(f2a_i)=f2a_rowsum(f2a_i)+1.0D0
          ELSE IF (f2a_ax > 0.0D0) THEN
            f2a_rowsum(f2a_i)=f2a_rowsum(f2a_i)+f2a_ax/f2a_rowscale(f2a_i)
          END IF
          IF (f2a_i < f2a_j) THEN
            f2a_sym_pairs=f2a_sym_pairs+1_8
            f2a_mirror=k(iDiagonal+f2a_j-f2a_i,f2a_i)
            IF (.NOT. IEEE_IS_FINITE(f2a_mirror)) THEN
              f2a_sym_nonfinite=f2a_sym_nonfinite+1_8
            ELSE
              f2a_scale=MAX(ABS(f2a_x),ABS(f2a_mirror))
              IF (f2a_scale > 0.0D0) THEN
                f2a_rel=ABS(f2a_x/f2a_scale-f2a_mirror/f2a_scale)
                IF (f2a_rel > f2a_sym_rel) THEN
                  f2a_worst_i=f2a_i; f2a_worst_j=f2a_j
                  f2a_worst_a=f2a_x; f2a_worst_b=f2a_mirror
                END IF
                f2a_sym_rel=MAX(f2a_sym_rel,f2a_rel)
                IF (f2a_rel > 1.0D-12) f2a_sym_div=f2a_sym_div+1_8
                IF (f2a_rel > 0.0D0 .AND. f2a_scale > HUGE(1.0D0)/f2a_rel) THEN
                  f2a_sym_abs=HUGE(1.0D0)
                ELSE
                  f2a_sym_abs=MAX(f2a_sym_abs,f2a_scale*f2a_rel)
                END IF
              END IF
            END IF
          END IF
        END IF
      END IF
    END IF
  END DO
END DO
DO f2a_i=1,nRank
  f2a_x=f2a_rowdiag(f2a_i)
  IF (.NOT. IEEE_IS_FINITE(f2a_x)) CYCLE
  IF (f2a_x > 0.0D0) THEN
    f2a_diag_pos=f2a_diag_pos+1_8
  ELSE IF (f2a_x < 0.0D0) THEN
    f2a_diag_neg=f2a_diag_neg+1_8
  ELSE
    f2a_diag_zero=f2a_diag_zero+1_8
  END IF
  IF (f2a_x /= 0.0D0) THEN
    f2a_bin=MAX(-323,MIN(308,FLOOR(LOG10(ABS(f2a_x)))))+324
    f2a_dhist(f2a_bin)=f2a_dhist(f2a_bin)+1_8
  END IF
  IF (f2a_rowscale(f2a_i) == 0.0D0) THEN
    IF (f2a_x /= 0.0D0) THEN
      f2a_dom_strict=f2a_dom_strict+1_8; f2a_rbin=130
    ELSE
      f2a_dom_nonstrict=f2a_dom_nonstrict+1_8; f2a_rbin=129
    END IF
  ELSE
    IF (f2a_x == 0.0D0) THEN
      f2a_logratio=-HUGE(1.0D0)
    ELSE
      f2a_logratio=LOG10(ABS(f2a_x))-LOG10(f2a_rowscale(f2a_i))-LOG10(f2a_rowsum(f2a_i))
    END IF
    IF (f2a_logratio > 0.0D0) THEN
      f2a_dom_strict=f2a_dom_strict+1_8
    ELSE
      f2a_dom_nonstrict=f2a_dom_nonstrict+1_8
    END IF
    IF (f2a_logratio <= -300.0D0) THEN
      f2a_rbin=1
    ELSE
      f2a_rbin=2+MAX(0,MIN(126,INT((f2a_logratio+16.0D0)*4.0D0)))
    END IF
  END IF
  f2a_rhist(f2a_rbin)=f2a_rhist(f2a_rbin)+1_8
END DO
DO f2a_i=1,nRank
  f2a_x=f(f2a_i,1)
  IF (.NOT. IEEE_IS_FINITE(f2a_x)) THEN
    f2a_force_nonfinite=f2a_force_nonfinite+1_8
  ELSE IF (f2a_x == 0.0D0) THEN
    f2a_force_zero=f2a_force_zero+1_8
  ELSE
    f2a_force_nonzero=f2a_force_nonzero+1_8
    f2a_force_max=MAX(f2a_force_max,ABS(f2a_x))
    f2a_force_min=MIN(f2a_force_min,ABS(f2a_x))
    f2a_bin=MAX(-323,MIN(308,FLOOR(LOG10(ABS(f2a_x)))))+324
    f2a_fhist(f2a_bin)=f2a_fhist(f2a_bin)+1_8
  END IF
END DO
IF (f2a_force_nonzero > 0_8) THEN
  DO f2a_bi=1,632
    f2a_cum=f2a_cum+f2a_fhist(f2a_bi)
    IF (f2a_p50 == -9999 .AND. f2a_cum >= (f2a_force_nonzero+1_8)/2_8) f2a_p50=f2a_bi-324
    IF (f2a_p95 == -9999 .AND. f2a_cum >= (95_8*f2a_force_nonzero+99_8)/100_8) f2a_p95=f2a_bi-324
  END DO
END IF
IF (f2a_nonzero > 0_8) f2a_range=LOG10(f2a_maxabs)-LOG10(f2a_minabs)
WRITE(*,'(A,5(A,I0))') 'BW1_F2A_STAGE ', &
  'nRank=',nRank,' nKRows=',nKRows,' kl=',nCodiagonals, &
  ' ku=',nCodiagonals,' iDiagonal=',iDiagonal
WRITE(*,'(A,8(A,I0))') 'BW1_F2A_MATRIX ', &
  'valid=',f2a_valid,' zero=',f2a_zero,' nonzero=',f2a_nonzero, &
  ' nonfinite=',f2a_nonfinite,' fill_nonzero=',f2a_fill_nonzero, &
  ' fill_nonfinite=',f2a_fill_nonfinite,' pad_nonzero=',f2a_pad_nonzero, &
  ' pad_nonfinite=',f2a_pad_nonfinite
WRITE(*,'(A,2(A,ES24.16E3),3(A,I0))') 'BW1_F2A_SCALE ', &
  'min_nonzero=',f2a_minabs,' max_abs=',f2a_maxabs, &
  ' diag_pos=',f2a_diag_pos,' diag_neg=',f2a_diag_neg,' diag_zero=',f2a_diag_zero
WRITE(*,'(A,2(A,ES24.16E3),3(A,I0))') 'BW1_F2A_SYMMETRY ', &
  'max_abs=',f2a_sym_abs,' max_relative=',f2a_sym_rel, &
  ' compared_pairs=',f2a_sym_pairs,' divergent_pairs=',f2a_sym_div, &
  ' nonfinite_pairs=',f2a_sym_nonfinite
WRITE(*,'(A,2(A,I0))') 'BW1_F2A_DOMINANCE ', &
  'strict=',f2a_dom_strict,' nonstrict=',f2a_dom_nonstrict
WRITE(*,'(A,3(A,I0),A,ES24.16E3)') 'BW1_F2A_FORCING ', &
  'zero=',f2a_force_zero,' nonzero=',f2a_force_nonzero, &
  ' nonfinite=',f2a_force_nonfinite,' max_abs=',f2a_force_max
WRITE(*,'(A,2(A,ES24.16E3),2(A,I0))') 'BW1_F2A_RANGE ', &
  'coefficient_log10_max_min=',f2a_range, &
  'forcing_min_nonzero=',f2a_force_min,' forcing_p50_log10_bin=',f2a_p50, &
  ' forcing_p95_log10_bin=',f2a_p95
WRITE(*,'(A,2(A,I0),2(A,ES24.16E3))') 'BW1_F2A_SYMMETRY_WORST ', &
  'i=',f2a_worst_i,' j=',f2a_worst_j,' aij=',f2a_worst_a,' aji=',f2a_worst_b
OPEN(UNIT=77,FILE='BW1_F2A_AGGREGATES.csv',STATUS='REPLACE',ACTION='WRITE',IOSTAT=f2a_ios)
IF (f2a_ios == 0) THEN
  WRITE(77,'(A)') 'kind,bin_x,bin_y,count'
  DO f2a_bi=1,256
    DO f2a_bj=1,256
      IF (f2a_heat(f2a_bi,f2a_bj)>0_8) THEN
        WRITE(77,'(A,I0,A,I0,A,I0)') 'heatmap,',f2a_bi,',',f2a_bj,',',f2a_heat(f2a_bi,f2a_bj)
      END IF
      IF (f2a_heat_valid(f2a_bi,f2a_bj)>0_8) THEN
        WRITE(77,'(A,I0,A,I0,A,I0)') 'heatmap_valid,',f2a_bi,',',f2a_bj,',',f2a_heat_valid(f2a_bi,f2a_bj)
      END IF
    END DO
  END DO
  DO f2a_bi=1,632
    IF (f2a_hist(f2a_bi)>0_8) WRITE(77,'(A,I0,A,I0)') 'matrix_log10_abs,',f2a_bi-324,',,',f2a_hist(f2a_bi)
    IF (f2a_dhist(f2a_bi)>0_8) WRITE(77,'(A,I0,A,I0)') 'diagonal_log10_abs,',f2a_bi-324,',,',f2a_dhist(f2a_bi)
    IF (f2a_fhist(f2a_bi)>0_8) WRITE(77,'(A,I0,A,I0)') 'forcing_log10_abs,',f2a_bi-324,',,',f2a_fhist(f2a_bi)
  END DO
  DO f2a_bi=1,130
    IF (f2a_rhist(f2a_bi)>0_8) WRITE(77,'(A,I0,A,I0)') 'dominance_log10_ratio_quarter_decade,',f2a_bi,',,',f2a_rhist(f2a_bi)
  END DO
  CLOSE(77)
  f2a_csv_ok=1
ELSE
  f2a_csv_ok=0
END IF
WRITE(*,'(A,I0)') 'BW1_F2A_AGGREGATES_WRITTEN=',f2a_csv_ok
WRITE(*,'(A)') 'BW1_F2A_RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING'
WRITE(*,'(A)') 'BW1_F2A_STOP_BEFORE_SOLVER'
FLUSH(6)
ERROR STOP 75
'''


def instrument_source_text(text: str) -> tuple[str, dict[str, Any]]:
    if MARKER in text or "ERROR STOP 75" in text or "BW1_F2A_MATRIX" in text:
        raise F2AError("F2A instrumentation already present")
    start, end, after_vbc, solver, _ = _fem_bounds(text)
    block = text[start:end]
    if block[after_vbc:solver].strip():
        raise F2AError("FEM source between VBCs and Solver is not empty")
    real_decl = re.search(r"(?im)^\s*REAL\*8\s+bDenom,\s*bDen,\s*bDenoN,\s*dVSize\s*$", block)
    if not real_decl:
        raise F2AError("FEM local declaration anchor changed")
    decl = """! F2A generated declarations begin.
INTEGER :: f2a_i,f2a_j,f2a_s,f2a_bi,f2a_bj,f2a_bin,f2a_rbin,f2a_ios,f2a_csv_ok,f2a_p50,f2a_p95,f2a_worst_i,f2a_worst_j
INTEGER(KIND=8) :: f2a_valid,f2a_zero,f2a_nonzero,f2a_nonfinite
INTEGER(KIND=8) :: f2a_fill_nonzero,f2a_fill_nonfinite,f2a_pad_nonzero,f2a_pad_nonfinite
INTEGER(KIND=8) :: f2a_sym_pairs,f2a_sym_div,f2a_sym_nonfinite
INTEGER(KIND=8) :: f2a_dom_strict,f2a_dom_nonstrict,f2a_diag_pos,f2a_diag_neg,f2a_diag_zero
INTEGER(KIND=8) :: f2a_force_zero,f2a_force_nonzero,f2a_force_nonfinite
INTEGER(KIND=8) :: f2a_cum
INTEGER(KIND=8) :: f2a_heat(256,256),f2a_hist(632),f2a_dhist(632),f2a_rhist(130),f2a_fhist(632)
INTEGER(KIND=8) :: f2a_heat_valid(256,256)
REAL*8 :: f2a_x,f2a_ax,f2a_minabs,f2a_maxabs,f2a_force_max,f2a_sym_abs,f2a_sym_rel,f2a_range,f2a_force_min
REAL*8 :: f2a_mirror,f2a_scale,f2a_rel,f2a_logratio,f2a_worst_a,f2a_worst_b
REAL*8 :: f2a_rowscale(nRank),f2a_rowsum(nRank),f2a_rowdiag(nRank)
! F2A generated declarations end.
"""
    use_stmt = "USE, INTRINSIC :: IEEE_ARITHMETIC, ONLY: IEEE_IS_FINITE\n"
    implicit = re.search(r"(?im)^\s*IMPLICIT\s+NONE\s*$", block)
    if not implicit:
        raise F2AError("FEM IMPLICIT NONE missing")
    block = block[:implicit.start()] + use_stmt + block[implicit.start():]
    real_decl = re.search(r"(?im)^\s*REAL\*8\s+bDenom,\s*bDen,\s*bDenoN,\s*dVSize\s*$", block)
    assert real_decl
    eol = block.find("\n", real_decl.end())
    if eol < 0:
        raise F2AError("FEM declaration lacks newline")
    block = block[:eol+1] + decl + block[eol+1:]
    _, _, after_vbc, solver, _ = _fem_bounds(block)
    insert = block.find("\n", after_vbc)
    if insert < 0:
        raise F2AError("VBCs line ending missing")
    block = block[:insert+1] + _fortran_block() + block[insert+1:]
    result = text[:start] + block + text[end:]
    proof = inspect_instrumentation(result)
    proof["instrumented_source_sha256"] = hashlib.sha256(result.encode()).hexdigest()
    return result, proof


def inspect_instrumentation(text: str) -> dict[str, Any]:
    start,end,after_vbc,solver,_ = _fem_bounds(text)
    block=text[start:end]
    marker=[m.start() for m in re.finditer(re.escape(MARKER),block)]
    stops=list(re.finditer(r"(?im)^\s*ERROR\s+STOP\s+75\s*$",block))
    if len(marker)!=1 or len(stops)!=1 or not (after_vbc < marker[0] < stops[0].start() < solver):
        raise F2AError("marker/stop placement is not a unique unconditional pre-Solver stop")
    direct_stop=re.compile(r"(?im)^\s*WRITE\(\s*\*,\s*'\(A\)'\s*\)\s*'"+re.escape(MARKER)+r"'\s*\n\s*FLUSH\(6\)\s*\n\s*ERROR\s+STOP\s+75\s*$")
    if not direct_stop.search(block) or "CALL Solver" in block[marker[0]:stops[0].start()]:
        raise F2AError("F2A marker is not followed directly by FLUSH and unconditional ERROR STOP 75")
    decl_start=block.find("! F2A generated declarations begin.")
    decl_end=block.find("! F2A generated declarations end.",decl_start)
    code_start=block.find("! SI1-BW1-F2A: read-only numerical characterization")
    generated=block[decl_start:decl_end+len("! F2A generated declarations end.")] + block[code_start:stops[0].end()]
    too_long=[(i+1,len(line)) for i,line in enumerate(generated.splitlines()) if len(line)>132]
    if too_long:
        raise F2AError(f"generated FEM source exceeds 132-column free-form limit: {too_long[:5]}")
    return {"after_vbcs_before_solver":True,"unconditional_error_stop_75":True,
            "marker_count":1,"solver_reachable":False,"max_fortran_line_length":max(map(len,block.splitlines())),
            "free_form_line_limit":132,"rigid_mode_test":"RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING"}


def _format_descriptors(fmt: str) -> list[str]:
    # Expand only the descriptor subset used by these constant WRITE formats.
    desc=[]
    for repeat, code in re.findall(r"(\d*)\s*(A|I0|ES24\.16E3)",fmt.upper().replace(" ","")):
        desc.extend([code] * int(repeat or "1"))
    return desc


def _copy_locked(source_root: Path, build_root: Path) -> dict[str, Any]:
    if build_root.exists(): raise F2AError("F2A build directory must be new")
    build_root.mkdir(parents=True)
    shutil.copy2(source_root / "Makefile", build_root / "Makefile")
    lock=json.loads(bw1.LOCK_PATH.read_text(encoding="utf-8"))
    locked=f1.si1.verify_source_lock(source_root,lock)
    for rel,digest in sorted(locked.items()):
        target=build_root/rel; target.parent.mkdir(parents=True,exist_ok=True)
        src=source_root/rel
        if rel=="src/MOD_Shells.f90":
            transformed,proof=instrument_source_text(src.read_text(encoding="utf-8")); target.write_text(transformed,encoding="utf-8",newline="\n")
        else:
            shutil.copy2(src,target)
            if _sha(target)!=digest: raise F2AError(f"locked copy hash mismatch: {rel}")
    if "proof" not in locals(): raise F2AError("MOD_Shells missing from source lock")
    proof["original_sha256"]=locked["src/MOD_Shells.f90"]
    proof["instrumented_sha256"]=_sha(build_root/"src/MOD_Shells.f90")
    return {"source_hashes":locked,"instrumentation":proof,"source_checkout_modified":False}


def _parse_line(text: str, prefix: str) -> dict[str,str]:
    lines=[line for line in text.splitlines() if line.startswith(prefix)]
    if len(lines)!=1: raise F2AError(f"expected one {prefix} line, found {len(lines)}")
    vals=dict(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)",lines[0]))
    return vals


def validate_fair_log(text: str, code: int) -> dict[str,Any]:
    if code!=EXIT_CODE: raise F2AError(f"expected intentional MPI stop {EXIT_CODE}, got {code}")
    if text.count(MARKER)!=1 or len(re.findall(r"(?im)^\s*ERROR\s+STOP\s+75\s*$",text))!=1: raise F2AError("missing/duplicate F2A stop marker")
    if SOLVE_RE.search(text) or re.search(r"(?i)solver entered|factoriz",text): raise F2AError("solver/factorization output detected")
    if f1.RUNTIME_ERROR_RE.search(text): raise F2AError("runtime/compiler/MPI failure text detected in stop log")
    stage=_parse_line(text,"BW1_F2A_STAGE "); matrix=_parse_line(text,"BW1_F2A_MATRIX ")
    scale=_parse_line(text,"BW1_F2A_SCALE "); symmetry=_parse_line(text,"BW1_F2A_SYMMETRY ")
    dominance=_parse_line(text,"BW1_F2A_DOMINANCE "); forcing=_parse_line(text,"BW1_F2A_FORCING ")
    range_metrics=_parse_line(text,"BW1_F2A_RANGE ")
    symmetry_worst=_parse_line(text,"BW1_F2A_SYMMETRY_WORST ")
    for key,val in EXPECTED.items():
        if int(stage[key])!=val: raise F2AError(f"F2A stage {key} differs from F1 qualified dimensions")
    expected_valid=EXPECTED["nRank"]*(EXPECTED["kl"]+EXPECTED["ku"]+1)-EXPECTED["kl"]*(EXPECTED["kl"]+1)//2-EXPECTED["ku"]*(EXPECTED["ku"]+1)//2
    if int(matrix["valid"])!=expected_valid: raise F2AError("physical band-slot count disagrees with mathematical band bounds")
    if int(matrix["zero"])+int(matrix["nonzero"])+int(matrix["nonfinite"])!=expected_valid: raise F2AError("physical matrix category counts do not sum to valid slots")
    if int(matrix["nonfinite"]) or int(matrix["fill_nonfinite"]) or int(matrix["pad_nonfinite"]) or int(forcing["nonfinite"]):
        raise F2AError("nonfinite values detected; characterization blocked pending adjudication")
    if int(matrix["fill_nonzero"]) or int(matrix["pad_nonzero"]):
        raise F2AError("nonzero values in reserved fill-in or invalid padding storage")
    for group in (scale,symmetry,range_metrics,forcing,symmetry_worst):
        for value in group.values():
            if re.fullmatch(NUMBER,value,re.I) and not math.isfinite(float(value.replace("D","E").replace("d","e"))):
                raise F2AError("nonfinite reported scalar statistic")
    if not re.search(r"(?m)^BW1_F2A_AGGREGATES_WRITTEN=1$",text): raise F2AError("aggregate CSV was not written")
    return {"stage":stage,"matrix":matrix,"scale":scale,"symmetry":symmetry,"symmetry_worst_pair":symmetry_worst,
            "range":range_metrics,"dominance":dominance,"forcing":forcing,
            "rigid_rotation_mode_test":"RIGID_ROTATION_MODE_TEST_NOT_AUTHORIZED_BY_CURRENT_BASIS_MAPPING",
            "solver_entered":False,"mpi_exit_code":code,"no_solve_output":True}


def _manifest(out: Path) -> None:
    name="BW1_F2A_ARTIFACT_MANIFEST.json"; arts=[]
    for path in sorted((p for p in out.rglob("*") if p.is_file() and p.name!=name),key=lambda p:p.relative_to(out).as_posix().casefold()):
        rel=path.relative_to(out).as_posix(); arts.append({"path":rel,"bytes":path.stat().st_size,"sha256":_sha(path),"role":"MPI_OR_BUILD_LOG" if rel.startswith("logs/") else "F2A_DIAGNOSTIC_EVIDENCE"})
    (out/name).write_text(json.dumps({"schema":"R6_SI1_BW1_F2A_ARTIFACT_MANIFEST_V1","membership":"all regular files except this manifest","artifacts":arts},indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")


def _report(out:Path, doc:dict[str,Any])->None:
    (out/"BW1_F2A_RESULT.json").write_text(json.dumps(doc,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    d=doc.get("diagnostics",{})
    lines=["# SI1-BW1-F2A numerical structure characterization","",f"Decision: `{doc['decision']}`.","",
           "The temporary executable scans LAPACK band storage after assembly/BC application and stops before Solver. No solve, factorization, eigenanalysis, or matrix dump is performed.","",
           f"- Source: `{doc.get('repository',{}).get('head')}`.",f"- Dimensions: `{d.get('stage')}`.",f"- Matrix: `{d.get('matrix')}`.",f"- Scaling: `{d.get('scale')}`.",f"- Symmetry: `{d.get('symmetry')}`.",f"- Dominance: `{d.get('dominance')}`.",f"- Forcing: `{d.get('forcing')}`.","",
           "F1 bandwidth metric ratio is not a condition number. No SPD, invertibility, or rigid-mode conclusion is inferred. Auxiliary workspace is approximately 4.0 MiB at the qualified shape: three nRank-sized REAL*8 row vectors, two 256×256 integer heatmaps, and fixed exponent histograms. Matrix scan time is O(nRank×nKRows); no dense copy, factorization, eigensolver, or full matrix dump is created.",
           "The Fair runner applies per-process RLIMIT_AS and wall-clock process-group timeout. It does not measure RSS or enforce aggregate cgroup memory; aggregate budget remains an operator assertion.","",
           f"Failure: `{doc.get('failure','none')}`."]
    (out/"BW1_F2A_RESULT.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")


def build_parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--f1-evidence-root",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--runtime-limit-seconds",type=int,required=True)
    p.add_argument("--memory-cap-gib-per-process",type=float,required=True)
    p.add_argument("--aggregate-memory-budget-gib",type=float,required=True)
    return p


def run_f2a(f1_root:Path,output_dir:Path,*,runtime_limit_seconds:int,memory_cap_gib_per_process:float,aggregate_memory_budget_gib:float)->dict[str,Any]:
    output_dir=output_dir.resolve(); shellset_root=bw1.ROOT/"external"/"ShellSet-v1.1.0"
    f1_root=Path(f1_root).resolve()
    doc={"schema":"R6_SI1_BW1_F2A_RESULT_V1","classification":"NONCANONICAL_NUMERICAL_ASSEMBLY_DIAGNOSTIC","decision":"BLOCKED_BW1_F2A_NUMERICAL_CHARACTERIZATION","repository":{},"preserved_gates":{"source_checkout_modified":False,"FEG_modified":False,"runtime_package_modified":False,"WORLD_HISTORY_changed":False,"solver_or_dgbsv_executed":False}}
    doc["execution_limits"]={"mpi_ranks":2,"runtime_limit_seconds":runtime_limit_seconds if isinstance(runtime_limit_seconds,int) else None,
        "memory_cap_gib_per_process":memory_cap_gib_per_process if math.isfinite(memory_cap_gib_per_process) else None,
        "aggregate_memory_budget_gib_operator_assertion":aggregate_memory_budget_gib if math.isfinite(aggregate_memory_budget_gib) else None,
        "aggregate_memory_enforced":False,"rss_measured":False}
    output_is_safe=False
    try:
        doc["repository"]={"branch":f1._git("branch","--show-current"),"head":f1._git("rev-parse","HEAD")}
        if doc["repository"]["branch"]!=EXPECTED_BRANCH: raise F2AError(f"expected {EXPECTED_BRANCH}, got {doc['repository']['branch']}")
        f1._git("merge-base","--is-ancestor",F1_COMMIT,"HEAD"); doc["repository"]["f1_qualified_commit_ancestor"]=True
        doc["f1_provenance"]=validate_f1_evidence(f1_root)
        if output_dir.exists(): raise F2AError("output directory must be new")
        f1._require_inside(output_dir,shellset_root,"output directory")
        f1._require_inside(output_dir,f1_root,"output directory")
        f1._require_inside(output_dir,ROOT,"output directory")
        history_root=os.environ.get("ARCANA_WORLD_HISTORY_ROOT")
        if history_root: f1._require_inside(output_dir,Path(history_root),"output directory")
        output_dir.mkdir(parents=True,exist_ok=False); output_is_safe=True
        inputs=bw1.validate_bw1_inputs(shellset_root,bw1.BW1_ROOT)
        doc["input_validation"]=inputs
        doc["f1_input_identity_comparison"]=_verify_f1_input_identity(f1_root,inputs)
        source_lock=json.loads(bw1.LOCK_PATH.read_text(encoding="utf-8"))
        source_hashes_before=f1.si1.verify_source_lock(shellset_root,source_lock)
        if runtime_limit_seconds<=0 or not all(math.isfinite(v) and v>0 for v in (memory_cap_gib_per_process,aggregate_memory_budget_gib)) or memory_cap_gib_per_process*2>aggregate_memory_budget_gib: raise F2AError("operator resource limits invalid or aggregate budget insufficient")
        if not sys.platform.startswith("linux"): raise F2AError("Fair runtime requires Linux; Windows supports static tests only")
        (output_dir/"logs").mkdir()
        tools=[f1._probe_tool(n) for n in ("nvfortran","mpifort","mpiexec","make")]
        if "25.11" not in " ".join(x["version_excerpt"] for x in tools[:2]): raise F2AError("qualified NVIDIA HPC SDK 25.11 not detected")
        doc["toolchain"]=tools
        build=output_dir/"build_f2a"; doc["instrumented_build"]=_copy_locked(shellset_root,build)
        proc=f1.si1.run_checked(["make","ShellSet"],cwd=build,timeout=runtime_limit_seconds,stdout_path=output_dir/"logs"/"build_f2a.log",env=f1.si1._solver_env())
        if proc.returncode or not (build/"ShellSet.exe").is_file(): raise F2AError(f"F2A temporary build failed ({proc.returncode})")
        if list(build.rglob("ShellSet.exe"))!=[build/"ShellSet.exe"]: raise F2AError("expected exactly one isolated diagnostic executable")
        run=output_dir/"run_f2a"; run.mkdir(); inp=run/"INPUT"; f1.si1.write_input_files(inp)
        derived=bw1.BW1_ROOT/"derived"
        shutil.copy2(derived/bw1.DEFAULT_FEG.name,inp/bw1.DEFAULT_FEG.name); shutil.copy2(derived/bw1.DEFAULT_PACKAGE.name,inp/bw1.DEFAULT_PACKAGE.name)
        shutil.copy2(shellset_root/"INPUT"/"iEarth5-049.in",inp/"SI1_ENGINEERING_REFERENCE.in")
        matrix=json.loads(bw1.DEFAULT_FEG_MANIFEST.read_text(encoding="utf-8"))["runtime_coordinate_frame"]["forward_rotation_matrix"]
        rings=f1.si1.canonical_plate_rings(bw1.PARTITION_PATH,matrix); symbols=f1.si1._plate_symbols(shellset_root/"src"/"MOD_SharedVars.f90")
        f1.si1.write_plate_outlines(inp/"ARCANA_PLATE_OUTLINES.dig",rings,symbols,derived/bw1.DEFAULT_FEG.name)
        shutil.copy2(build/"ShellSet.exe",run/"ShellSet.exe")
        before={p.relative_to(run).as_posix():_sha(p) for p in sorted(inp.iterdir()) if p.is_file()}
        doc["staged_input_hashes_before"]=before
        command=["mpiexec","-n","2","./ShellSet.exe","-Iter","1","-InOpt","List","-Dir","RUN_OUTPUT"]; doc["mpi_command"]=command
        start=time.monotonic(); code,log=f1._run_limited(command,cwd=run,timeout=runtime_limit_seconds,per_process_bytes=int(memory_cap_gib_per_process*1024**3),output_path=output_dir/"logs"/"f2a_mpi_combined.log",env=f1.si1._solver_env())
        doc["runtime"]={"returncode":code,"elapsed_seconds":time.monotonic()-start,"log_sha256":_sha(output_dir/"logs"/"f2a_mpi_combined.log")}
        doc["diagnostics"]=validate_fair_log(log,code)
        doc["f1_reassembly_comparison"]=compare_reassembly_to_f1(
            doc["diagnostics"],doc["f1_provenance"]["f1_reference_metrics"])
        csv=run/"BW1_F2A_AGGREGATES.csv"
        if not csv.is_file(): raise F2AError("F2A aggregate data file missing")
        shutil.copy2(csv,output_dir/csv.name)
        for rel,digest in before.items():
            if _sha(run/rel)!=digest: raise F2AError(f"staged input changed: {rel}")
        doc["staged_inputs_unchanged"]=True
        source_hashes_after=f1.si1.verify_source_lock(shellset_root,source_lock)
        if source_hashes_after!=source_hashes_before: raise F2AError("ShellSet locked source changed during F2A")
        inputs_after=bw1.validate_bw1_inputs(shellset_root,bw1.BW1_ROOT)
        if inputs_after.get("source_inputs")!=inputs.get("source_inputs") or inputs_after.get("derived_inputs")!=inputs.get("derived_inputs"):
            raise F2AError("governed/derived FEG or runtime package changed during F2A")
        doc["preservation_verification"]={"locked_shellset_source_unchanged":True,"input_hashes_unchanged":True}
        doc["decision"]="PASS_BW1_F2A_NUMERICAL_CHARACTERIZATION"
    except Exception as exc: doc["failure"]=f"{type(exc).__name__}: {exc}"
    if output_is_safe:
        _report(output_dir,doc); _manifest(output_dir)
    return doc


def main(argv:list[str]|None=None)->int:
    p=build_parser(); a=p.parse_args(argv)
    result=run_f2a(a.f1_evidence_root,a.output_dir,runtime_limit_seconds=a.runtime_limit_seconds,memory_cap_gib_per_process=a.memory_cap_gib_per_process,aggregate_memory_budget_gib=a.aggregate_memory_budget_gib)
    print(result["decision"])
    if result["decision"]!="PASS_BW1_F2A_NUMERICAL_CHARACTERIZATION": print(result.get("failure","blocked"),file=sys.stderr); return 2
    print(f"BW1_F2A_EVIDENCE={a.output_dir / 'BW1_F2A_RESULT.json'}")
    print(f"BW1_F2A_MANIFEST={a.output_dir / 'BW1_F2A_ARTIFACT_MANIFEST.json'}")
    return 0


if __name__=="__main__": raise SystemExit(main())
