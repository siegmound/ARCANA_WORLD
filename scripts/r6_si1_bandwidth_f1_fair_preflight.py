#!/usr/bin/env python3
"""Fail-closed SI1-BW1 assembly-only Fair preflight.

Builds one temporary ShellSet executable with an unconditional ERROR STOP 74
inside FEM, after BuildF/BuildK/AddFSt/VBCs and before Solver. There is no
normal-executable or solve mode. Windows supports source/parser tests only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import r6_si1_bandwidth_bw1_fair_preflight as bw1  # noqa: E402


class _LazyModule:
    """Defer Fair-only scientific dependencies until the execution path runs."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.module: Any | None = None

    def __getattr__(self, name: str) -> Any:
        if self.module is None:
            import importlib
            self.module = importlib.import_module(self.name)
        return getattr(self.module, name)


si1 = _LazyModule("r6_shells_si1_engineering_solve")

SHELLSET_ROOT = ROOT / "external" / "ShellSet-v1.1.0"
BW1_ROOT = ROOT / "outputs" / "r6_si1_bandwidth_bw1"
PARTITION_PATH = ROOT / "R6_T0_VECTOR_PLATE_PARTITION.npz"
MPI_RANKS = 2
EXIT_CODE = 74
MARKER = "BW1_F1_STOP_BEFORE_SOLVER"
EXPECTED_BRANCH = "r6/si1-bandwidth-f1"
F0_BASELINE = "c23fac9de2bd8893ac5e7dbfbe41903f14e16a73"
FEM_START_RE = re.compile(r"(?im)^\s*SUBROUTINE\s+FEM\s*\(")
ERROR_STOP_RE = re.compile(r"(?im)^\s*ERROR\s+STOP\s+74\s*$")
SOLVER_CALL_RE = re.compile(r"(?im)^\s*CALL\s+Solver\s*\(")
SOLVE_LOG_RE = re.compile(r"(?i)(?:\bDG[BE]SV\b|\bCONVERGED\b\s*!{3,}|\bSOLVER\s+ITERATION\b|\bSOLUTION\s+CONVERGED\b)")
RUNTIME_ERROR_RE = re.compile(
    r"(?i)(?:NVFORTRAN-[A-Z]-|FORTRAN\s+RUNTIME\s+ERROR|SEGMENTATION\s+FAULT|"
    r"SIGSEGV|MPI_ABORT|OUT OF MEMORY|CANNOT ALLOCATE|ALLOCATION FAILED)"
)
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"


class F1Error(RuntimeError):
    """F1 source, execution, or evidence validation failed closed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise F1Error(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _fem_block(text: str) -> tuple[int, int, int, int]:
    starts = list(FEM_START_RE.finditer(text))
    if len(starts) != 1:
        raise F1Error(f"expected one SUBROUTINE FEM definition, found {len(starts)}")
    end = re.search(r"(?im)^\s*END\s+SUBROUTINE\s+FEM\b", text[starts[0].start():])
    if end is None:
        raise F1Error("FEM end anchor missing")
    body_start = starts[0].start()
    body_end = body_start + end.end()
    block = text[body_start:body_end]
    calls: dict[str, list[re.Match[str]]] = {}
    for name in ("BuildF", "BuildK", "AddFSt", "VBCs", "Solver"):
        calls[name] = list(re.finditer(rf"(?im)^\s*CALL\s+{name}\b", block))
        if len(calls[name]) != 1:
            raise F1Error(f"FEM must contain exactly one CALL {name}, found {len(calls[name])}")
        tail = block[calls[name][0].end():].lstrip()
        if not tail.startswith("("):
            raise F1Error(f"FEM CALL {name} syntax no longer has a parenthesized argument list")
    ordered = [calls[name][0].start() for name in ("BuildF", "BuildK", "AddFSt", "VBCs", "Solver")]
    if ordered != sorted(ordered):
        raise F1Error("FEM assembly/solver call order changed")
    # Return absolute offsets for the unique procedure, VBCs and Solver anchors.
    return body_start, body_end, body_start + calls["VBCs"][0].start(), body_start + calls["Solver"][0].start()


def _call_end(block: str, call_start: int) -> int:
    """Find a complete free-form Fortran call through its closing parenthesis."""
    opening = block.find("(", call_start)
    if opening < 0:
        raise F1Error("VBCs call opening parenthesis missing")
    depth = 0
    for pos in range(opening, len(block)):
        char = block[pos]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return pos + 1
    raise F1Error("VBCs call closing parenthesis missing")


def instrument_source_text(text: str) -> tuple[str, dict[str, Any]]:
    """Instrument only the unique FEM assembly site in a disposable copy."""
    if MARKER in text or "BW1_F1_MATRIX" in text or "ERROR STOP 74" in text:
        raise F1Error("F1 instrumentation is already present")
    start, end, vbc_abs, solver_abs = _fem_block(text)
    block = text[start:end]
    vbc_local = vbc_abs - start
    solver_local = solver_abs - start
    vbc_end = _call_end(block, vbc_local)
    if not (vbc_end < solver_local):
        raise F1Error("VBCs and Solver anchors are not in the required order")
    implicit = re.search(r"(?im)^\s*IMPLICIT\s+NONE\s*$", block)
    if implicit is None:
        raise F1Error("FEM IMPLICIT NONE anchor missing")
    real_decl = re.search(r"(?im)^\s*REAL\*8\s+bDenom,\s*bDen,\s*bDenoN,\s*dVSize\s*$", block)
    if real_decl is None:
        raise F1Error("FEM diagnostic declaration anchor changed")

    declarations = (
        "USE, INTRINSIC :: IEEE_ARITHMETIC, ONLY: IEEE_IS_FINITE\n"
    )
    local_declarations = (
        "INTEGER :: f1_i, f1_j\n"
        "INTEGER(KIND=8) :: f1_finite, f1_nonfinite, f1_nonzero\n"
        "INTEGER(KIND=8) :: f1_diag_zero, f1_diag_nonzero, f1_force_finite\n"
        "INTEGER(KIND=8) :: f1_force_nonfinite, f1_force_nonzero\n"
        "INTEGER(KIND=8) :: f1_matrix_bytes\n"
        "REAL*8 :: f1_max_abs, f1_force_max_abs\n"
    )
    diagnostic = f"""! SI1-BW1-F1 temporary assembly-only instrumentation.
f1_finite = 0_8
f1_nonfinite = 0_8
f1_nonzero = 0_8
f1_diag_zero = 0_8
f1_diag_nonzero = 0_8
f1_force_finite = 0_8
f1_force_nonfinite = 0_8
f1_force_nonzero = 0_8
f1_max_abs = 0.0D0
f1_force_max_abs = 0.0D0
f1_matrix_bytes = 8_8 * INT(nKRows, KIND=8) * INT(nRank, KIND=8)
DO f1_j = 1, nRank
  DO f1_i = 1, nKRows
    IF (IEEE_IS_FINITE(k(f1_i, f1_j))) THEN
      f1_finite = f1_finite + 1_8
      IF (k(f1_i, f1_j) /= 0.0D0) f1_nonzero = f1_nonzero + 1_8
      f1_max_abs = MAX(f1_max_abs, ABS(k(f1_i, f1_j)))
    ELSE
      f1_nonfinite = f1_nonfinite + 1_8
    END IF
  END DO
END DO
IF (iDiagonal >= 1 .AND. iDiagonal <= nKRows) THEN
  DO f1_j = 1, nRank
    IF (IEEE_IS_FINITE(k(iDiagonal, f1_j))) THEN
      IF (k(iDiagonal, f1_j) == 0.0D0) THEN
        f1_diag_zero = f1_diag_zero + 1_8
      ELSE
        f1_diag_nonzero = f1_diag_nonzero + 1_8
      END IF
    END IF
  END DO
ELSE
  f1_diag_zero = -1_8
  f1_diag_nonzero = -1_8
END IF
DO f1_i = 1, nRank
  IF (IEEE_IS_FINITE(f(f1_i, 1))) THEN
    f1_force_finite = f1_force_finite + 1_8
    IF (f(f1_i, 1) /= 0.0D0) f1_force_nonzero = f1_force_nonzero + 1_8
    f1_force_max_abs = MAX(f1_force_max_abs, ABS(f(f1_i, 1)))
  ELSE
    f1_force_nonfinite = f1_force_nonfinite + 1_8
  END IF
END DO
WRITE(*,'(A,I0,A,I0,A,I0,A,I0,A)') &
  'BW1_F1_STAGE nRank=', nRank, ' nKRows=', nKRows, &
  ' nCodiagonals=', nCodiagonals, ' iDiagonal=', iDiagonal, &
  ' stiff_allocated=1 fem_entered=1 BuildF_done=1 BuildK_done=1', &
  ' AddFSt_done=1 VBCs_done=1'
WRITE(*,'(A,I0,A,I0,A,I0,A,I0,A,I0,A,I0,A,I0,A,I0,A,I0,A,ES24.16E3)') &
  'BW1_F1_MATRIX rows=', nKRows, ' cols=', nRank, &
  ' bytes=', f1_matrix_bytes, ' finite=', f1_finite, &
  ' nonfinite=', f1_nonfinite, ' nonzero=', f1_nonzero, &
  ' diagonal_row=', iDiagonal, ' diag_zero=', f1_diag_zero, &
  ' diag_nonzero=', f1_diag_nonzero, ' max_abs=', f1_max_abs
WRITE(*,'(A,I0,A,I0,A,I0,A,I0,A,ES24.16E3)') &
  'BW1_F1_FORCING count=', nRank, ' finite=', f1_force_finite, &
  ' nonfinite=', f1_force_nonfinite, ' nonzero=', f1_force_nonzero, &
  ' max_abs=', f1_force_max_abs
WRITE(*,'(A)') '{MARKER}'
FLUSH(6)
ERROR STOP 74
"""
    # Insert USE before IMPLICIT NONE, declarations after existing local declarations,
    # and an unconditional diagnostic block after VBCs but before Solver.
    transformed_block = (
        block[: implicit.start()] + declarations + block[implicit.start():]
    )
    real_decl = re.search(r"(?im)^\s*REAL\*8\s+bDenom,\s*bDen,\s*bDenoN,\s*dVSize\s*$", transformed_block)
    assert real_decl is not None
    line_end = transformed_block.find("\n", real_decl.end())
    if line_end < 0:
        raise F1Error("FEM local declaration has no newline")
    transformed_block = transformed_block[:line_end + 1] + local_declarations + transformed_block[line_end + 1:]
    # Offsets have changed after declarations; relocate the unique calls.
    _, _, vbc_abs2, solver_abs2 = _fem_block(transformed_block)
    vbc_local2 = vbc_abs2
    solver_local2 = solver_abs2
    call_end = _call_end(transformed_block, vbc_local2)
    line_end = transformed_block.find("\n", call_end)
    if line_end < 0 or line_end >= solver_local2:
        raise F1Error("VBCs closing line no longer precedes Solver")
    if transformed_block[line_end + 1:solver_local2].strip() != "":
        raise F1Error("FEM source between VBCs and Solver is no longer empty; refusing ambiguous insertion")
    transformed_block = transformed_block[:line_end + 1] + diagnostic + transformed_block[line_end + 1:]
    result = text[:start] + transformed_block + text[end:]
    proof = inspect_instrumentation(result)
    proof["instrumented_source_sha256"] = hashlib.sha256(result.encode("utf-8")).hexdigest()
    return result, proof


def inspect_instrumentation(text: str) -> dict[str, Any]:
    """Static proof of diagnostic placement and unconditional pre-Solver stop."""
    start, end, vbc_abs, solver_abs = _fem_block(text)
    block = text[start:end]
    vbc_local, solver_local = vbc_abs - start, solver_abs - start
    error_stops = list(ERROR_STOP_RE.finditer(block))
    markers = [m.start() for m in re.finditer(re.escape(MARKER), block)]
    flushes = list(re.finditer(r"(?im)^\s*FLUSH\s*\(\s*6\s*\)\s*$", block))
    def write_label_positions(label: str) -> list[int]:
        positions = [match.start() for match in re.finditer(rf"['\"]{re.escape(label)}\b", block)]
        for pos in positions:
            preceding_write = block.rfind("WRITE", max(0, pos - 180), pos)
            if preceding_write < 0:
                raise F1Error(f"{label} is not emitted by a nearby WRITE statement")
        return positions

    matrix_lines = write_label_positions("BW1_F1_MATRIX")
    forcing_lines = write_label_positions("BW1_F1_FORCING")
    stage_lines = write_label_positions("BW1_F1_STAGE")
    if len(error_stops) != 1 or len(markers) != 1 or len(flushes) != 1:
        raise F1Error("F1 marker, FLUSH, or unconditional ERROR STOP 74 is missing/duplicated")
    if len(matrix_lines) != 1 or len(forcing_lines) != 1 or len(stage_lines) != 1:
        raise F1Error("F1 matrix/forcing/stage diagnostic write is missing or duplicated")
    stop = error_stops[0].start()
    flush = flushes[0].start()
    marker = markers[0]
    # The stop immediately follows the flush; no conditional or branch can bypass it.
    between_flush_stop = block[flushes[0].end():stop]
    if between_flush_stop.strip():
        raise F1Error("F1 stop is not immediately after diagnostic flush")
    if not (vbc_local < matrix_lines[0] < marker < flush < stop < solver_local):
        raise F1Error("FEM VBCs / diagnostics / stop / Solver ordering is invalid")
    # The F1 stop is the sole path between VBCs and Solver and is unconditional.
    gap = block[_call_end(block, vbc_local):solver_local]
    stop_in_gap = stop - _call_end(block, vbc_local)
    if re.search(r"(?im)^\s*(?:GO\s*TO\b|GOTO\b|RETURN\b|STOP\b|ERROR\s+STOP\b)", gap[:stop_in_gap]):
        raise F1Error("alternate termination/control flow exists before the required F1 stop")
    if text.count(MARKER) != 1 or len(re.findall(r"(?im)^\s*ERROR\s+STOP\s+74\s*$", text)) != 1:
        raise F1Error("instrumentation must contain exactly one marker and one unconditional stop")
    return {
        "procedure": "FEM",
        "assembly_call_order": ["BuildF", "BuildK", "AddFSt", "VBCs"],
        "instrumentation_after_vbcs": True,
        "instrumentation_before_solver": True,
        "unconditional_error_stop": EXIT_CODE,
        "marker": MARKER,
        "flush_before_stop": True,
        "normal_solver_reachable": False,
        "normal_executable_mode": False,
        "full_matrix_dump": False,
    }


def _parse_key_values(line: str, prefix: str) -> dict[str, str]:
    match = re.search(rf"{re.escape(prefix)}\s+(.+)$", line)
    if match is None:
        raise F1Error(f"malformed {prefix} diagnostic")
    pairs = re.findall(rf"([A-Za-z][A-Za-z0-9_]*)=[ \t]*({NUMBER})", match.group(1))
    if not pairs:
        raise F1Error(f"empty {prefix} diagnostic")
    values = dict(pairs)
    if len(values) != len(pairs):
        raise F1Error(f"duplicate key in {prefix} diagnostic")
    residue = re.sub(rf"[A-Za-z][A-Za-z0-9_]*=[ \t]*{NUMBER}", "", match.group(1)).strip()
    if residue:
        raise F1Error(f"malformed token(s) in {prefix} diagnostic: {residue}")
    return values


def _int_value(values: dict[str, str], key: str) -> int:
    if key not in values:
        raise F1Error(f"missing {key} diagnostic")
    try:
        number = float(values[key].replace("D", "E").replace("d", "e"))
    except ValueError as exc:
        raise F1Error(f"invalid integer diagnostic {key}") from exc
    if not number.is_integer():
        raise F1Error(f"non-integral diagnostic {key}")
    return int(number)


def _float_value(values: dict[str, str], key: str) -> float:
    if key not in values:
        raise F1Error(f"missing {key} diagnostic")
    value = float(values[key].replace("D", "E").replace("d", "e"))
    if not (float("-inf") < value < float("inf")):
        raise F1Error(f"nonfinite summary diagnostic {key}")
    return value


def _records(text: str, prefix: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if prefix in line]
    if not lines:
        raise F1Error(f"{prefix} diagnostic missing")
    if len(lines) > MPI_RANKS:
        raise F1Error(f"{prefix} diagnostic count exceeds {MPI_RANKS} MPI ranks")
    return [_parse_key_values(line, prefix) for line in lines]


def validate_f1_log(text: str, *, mpi_exit_code: int) -> dict[str, Any]:
    """Validate complete compact assembly summaries independent of stream order."""
    if mpi_exit_code != EXIT_CODE:
        raise F1Error(f"MPI exit code must be intentional code {EXIT_CODE}, found {mpi_exit_code}")
    if RUNTIME_ERROR_RE.search(text):
        raise F1Error(f"unexpected runtime/MPI/allocation error: {RUNTIME_ERROR_RE.search(text).group(0)}")
    if SOLVE_LOG_RE.search(text):
        raise F1Error("solver/LAPACK/convergence output appeared in assembly-only log")
    stops = list(re.finditer(r"(?im)^\s*ERROR\s+STOP\s+(\d+)\s*$", text))
    if not stops or any(int(match.group(1)) != EXIT_CODE for match in stops) or len(stops) > MPI_RANKS:
        raise F1Error("log must contain only one or two intentional ERROR STOP 74 lines")
    markers = len(re.findall(re.escape(MARKER), text))
    if not 1 <= markers <= MPI_RANKS:
        raise F1Error("assembly stop marker missing or duplicated beyond MPI rank count")

    stage = _records(text, "BW1_F1_STAGE")
    matrix = _records(text, "BW1_F1_MATRIX")
    forcing = _records(text, "BW1_F1_FORCING")
    if not (len(stage) == len(matrix) == len(forcing) == markers == len(stops)):
        raise F1Error("stage, matrix and forcing diagnostics have different rank counts")
    parsed: list[dict[str, Any]] = []
    for s, m, f in zip(stage, matrix, forcing, strict=True):
        expected_stage = {
            "nRank": 128884, "nKRows": 2182, "nCodiagonals": 727,
            "iDiagonal": 1455, "stiff_allocated": 1, "fem_entered": 1,
            "BuildF_done": 1, "BuildK_done": 1, "AddFSt_done": 1, "VBCs_done": 1,
        }
        if {key: _int_value(s, key) for key in expected_stage} != expected_stage:
            raise F1Error("inconsistent stage diagnostics: dimensions or assembly completion differ from BW1 contract")
        rows, cols = _int_value(m, "rows"), _int_value(m, "cols")
        total = rows * cols
        mat = {
            "rows": rows, "cols": cols, "bytes": _int_value(m, "bytes"),
            "finite": _int_value(m, "finite"), "nonfinite": _int_value(m, "nonfinite"),
            "nonzero": _int_value(m, "nonzero"), "diagonal_row": _int_value(m, "diagonal_row"),
            "diag_zero": _int_value(m, "diag_zero"), "diag_nonzero": _int_value(m, "diag_nonzero"),
            "max_abs": _float_value(m, "max_abs"),
        }
        if (rows, cols, mat["bytes"]) != (2182, 128884, 8 * total):
            raise F1Error("matrix dimensions or byte calculation do not match qualified BW1 KSize")
        if mat["finite"] + mat["nonfinite"] != total or mat["nonzero"] > mat["finite"]:
            raise F1Error("matrix finite/nonfinite/nonzero counts are inconsistent")
        if mat["nonfinite"] != 0:
            raise F1Error("assembled matrix contains NaN or infinity")
        if mat["diagonal_row"] != 1455 or mat["diag_zero"] + mat["diag_nonzero"] != cols:
            raise F1Error("LAPACK diagonal-row counts are inconsistent")
        if mat["max_abs"] < 0 or (mat["nonzero"] == 0) != (mat["max_abs"] == 0):
            raise F1Error("matrix max_abs conflicts with nonzero count")
        fc, fnf, force_nonfinite, fnz = (_int_value(f, key) for key in ("count", "finite", "nonfinite", "nonzero"))
        fmaxv = _float_value(f, "max_abs")
        if fc != cols or fnf + force_nonfinite != fc or force_nonfinite != 0 or fnz > fnf:
            raise F1Error("forcing count/finiteness/nonzero diagnostics are inconsistent")
        if fmaxv < 0 or (fnz == 0) != (fmaxv == 0):
            raise F1Error("forcing max_abs conflicts with nonzero count")
        parsed.append({"stage": expected_stage, "matrix": mat, "forcing": {
            "count": fc, "finite": fnf, "nonfinite": force_nonfinite,
            "nonzero": fnz, "max_abs": fmaxv, "all_zero": fnz == 0,
        }})
    if any(item != parsed[0] for item in parsed[1:]):
        raise F1Error("MPI ranks emitted inconsistent assembled-system diagnostics")
    return {
        "rank_diagnostic_count": len(parsed), "intentional_error_stop_count": len(stops),
        "marker_count": markers, "mpi_exit_code": mpi_exit_code,
        "system": parsed[0], "solver_entered": False,
        "ieee_warning_counts": {word: len(re.findall(word, text, re.I)) for word in ("ieee_underflow", "ieee_inexact")},
        "memory_observation": "No RSS/peak memory measurement is claimed; RLIMIT_AS limits per-process virtual address space and is inherited by local MPI descendants.",
    }


def _require_inside(path: Path, root: Path, label: str) -> Path:
    resolved, resolved_root = path.resolve(), root.resolve()
    if resolved == resolved_root or resolved_root in resolved.parents:
        raise F1Error(f"{label} may not be inside the ShellSet checkout")
    return resolved


def _instrumented_build_tree(source_root: Path, build_root: Path) -> dict[str, Any]:
    if build_root.exists():
        raise F1Error("isolated F1 build directory unexpectedly exists")
    build_root.mkdir(parents=True)
    shutil.copy2(source_root / "Makefile", build_root / "Makefile")
    source_out = build_root / "src"
    source_out.mkdir()
    lock = json.loads(bw1.LOCK_PATH.read_text(encoding="utf-8"))
    locked = si1.verify_source_lock(source_root, lock)
    copied: dict[str, str] = {}
    proof: dict[str, Any] | None = None
    for rel, digest in sorted(locked.items()):
        src = source_root / rel
        target = build_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel == "src/MOD_Shells.f90":
            transformed, proof = instrument_source_text(src.read_text(encoding="utf-8"))
            target.write_text(transformed, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, target)
        copied[rel] = _sha256(target)
        if rel != "src/MOD_Shells.f90" and copied[rel] != digest:
            raise F1Error(f"temporary source copy differs from locked source: {rel}")
    if proof is None:
        raise F1Error("MOD_Shells.f90 was not included in the source lock")
    proof["original_sha256"] = locked["src/MOD_Shells.f90"]
    proof["instrumented_sha256"] = copied["src/MOD_Shells.f90"]
    inspect_instrumentation((build_root / "src" / "MOD_Shells.f90").read_text(encoding="utf-8"))
    return {"source_hashes": copied, "instrumentation": proof, "only_instrumented_executable_build": True}


def _probe_tool(name: str) -> dict[str, Any]:
    result = subprocess.run([name, "--version"], capture_output=True, text=True, check=False, timeout=30)
    output = (result.stdout + result.stderr).strip()
    if result.returncode:
        raise F1Error(f"tool probe failed: {name}")
    return {"tool": name, "returncode": result.returncode, "version_excerpt": output[:1200]}


def _run_limited(command: list[str], *, cwd: Path, timeout: int, per_process_bytes: int,
                 output_path: Path, env: dict[str, str]) -> tuple[int, str]:
    if not sys.platform.startswith("linux"):
        raise F1Error("F1 runtime is Linux/Fair-only; Windows performs static validation only")
    try:
        import resource
    except ImportError as exc:
        raise F1Error("resource.RLIMIT_AS unavailable; refusing an unbounded MPI run") from exc

    def limit_address_space() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (per_process_bytes, per_process_bytes))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as stream:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True, preexec_fn=limit_address_space)
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise F1Error(f"MPI assembly-only run exceeded {timeout}s; process group terminated") from exc
    return returncode, output_path.read_text(encoding="utf-8", errors="replace")


def _write_report(out: Path, result: dict[str, Any]) -> None:
    (out / "BW1_F1_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    diag = result.get("diagnostics", {}).get("system", {})
    matrix = diag.get("matrix", {})
    forcing = diag.get("forcing", {})
    lines = [
        "# SI1-BW1-F1 assembly-only preflight", "",
        f"Decision: `{result.get('decision')}`.", "",
        "This preflight stops unconditionally in `FEM` after BuildF, BuildK, AddFSt and VBCs, and before Solver. It does not solve the linear system.", "",
        f"- Source baseline: `{result.get('repository', {}).get('head')}`.",
        f"- Matrix: {matrix.get('rows')} × {matrix.get('cols')}; bytes={matrix.get('bytes')}; finite={matrix.get('finite')}; nonfinite={matrix.get('nonfinite')}; nonzero={matrix.get('nonzero')}; diagonal zero/nonzero={matrix.get('diag_zero')}/{matrix.get('diag_nonzero')}.",
        f"- Forcing: count={forcing.get('count')}; finite={forcing.get('finite')}; nonfinite={forcing.get('nonfinite')}; nonzero={forcing.get('nonzero')}; all_zero={forcing.get('all_zero')}.",
        f"- Solver entered: {result.get('diagnostics', {}).get('solver_entered', False)}.",
        f"- Failure: {result.get('failure', 'none')}.", "",
        "Memory note: the runner applies per-process RLIMIT_AS and a wall-clock process-group timeout. It does not measure RSS or enforce an aggregate RSS cgroup limit; the operator must approve aggregate RAM headroom before running.", "",
    ]
    (out / "BW1_F1_RESULT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _seal_manifest(out: Path) -> None:
    name = "BW1_F1_ARTIFACT_MANIFEST.json"
    entries = []
    for path in sorted((p for p in out.rglob("*") if p.is_file() and p.name != name),
                       key=lambda p: (p.relative_to(out).as_posix().casefold(), p.relative_to(out).as_posix())):
        rel = path.relative_to(out).as_posix()
        entries.append({"path": rel, "bytes": path.stat().st_size, "sha256": _sha256(path),
                        "role": "BUILD_OR_MPI_LOG" if rel.startswith("logs/") else "ISOLATED_BUILD_OR_STAGED_RUNTIME_ARTIFACT" if rel.startswith(("build_f1/", "run_f1/")) else "F1_DECISION_EVIDENCE"})
    manifest = {"schema": "R6_SI1_BW1_F1_ARTIFACT_MANIFEST_V1", "membership": "all regular files recursively except this manifest", "artifacts": entries}
    (out / name).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shellset-root", type=Path, default=SHELLSET_ROOT)
    parser.add_argument("--bw1-root", type=Path, default=BW1_ROOT)
    parser.add_argument("--partition-payload", type=Path, default=PARTITION_PATH)
    parser.add_argument("--output-dir", type=Path, required=True, help="new external evidence directory")
    parser.add_argument("--runtime-limit-seconds", type=int, required=True, help="operator-approved wall-clock process-group limit")
    parser.add_argument("--memory-cap-gib-per-process", type=float, required=True, help="operator-approved inherited RLIMIT_AS per process")
    parser.add_argument("--aggregate-memory-budget-gib", type=float, required=True, help="operator-confirmed aggregate RAM budget; informational, not RSS-enforced")
    return parser


def run_f1(shellset_root: Path, bw1_root: Path, partition_payload: Path, output_dir: Path, *,
           runtime_limit_seconds: int, memory_cap_gib_per_process: float,
           aggregate_memory_budget_gib: float) -> dict[str, Any]:
    shellset_root = Path(shellset_root).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise F1Error(f"evidence output must be new: {output_dir}")
    if (runtime_limit_seconds <= 0 or not math.isfinite(memory_cap_gib_per_process)
            or not math.isfinite(aggregate_memory_budget_gib)
            or memory_cap_gib_per_process <= 0 or aggregate_memory_budget_gib <= 0):
        raise F1Error("operator execution limits must be positive")
    if memory_cap_gib_per_process * MPI_RANKS > aggregate_memory_budget_gib:
        raise F1Error("two per-process address-space caps exceed the operator aggregate memory budget")
    _require_inside(output_dir, shellset_root, "evidence output")
    output_dir.mkdir(parents=True, exist_ok=False)
    result: dict[str, Any] = {
        "schema": "R6_SI1_BW1_F1_RESULT_V1", "classification": "NONCANONICAL_BW1_ASSEMBLY_DIAGNOSTIC",
        "decision": "BLOCKED_BW1_F1_ASSEMBLY_PREFLIGHT",
        "scope": "temporary instrumented build and assembly only; unconditional ERROR STOP 74 before Solver",
        "repository": {"branch": None, "head": None},
        "execution_limits": {"mpi_ranks": MPI_RANKS, "runtime_limit_seconds": runtime_limit_seconds,
            "memory_cap_gib_per_process": memory_cap_gib_per_process,
            "aggregate_memory_budget_gib_operator_assertion": aggregate_memory_budget_gib,
            "address_space_limit_inherited_by_local_mpi_descendants": True,
            "aggregate_rss_enforced": False, "rss_measured": False},
        "preserved_gates": {"original_feg_modified": False, "bw1_feg_modified": False,
            "original_runtime_package_modified": False, "bw1_runtime_package_modified": False,
            "source_checkout_modified": False, "world_history_changed": False,
            "solver_or_dgbsv_executed": False, "t1_or_t2_created": False},
    }
    try:
        result["repository"] = {"branch": _git("branch", "--show-current"), "head": _git("rev-parse", "HEAD")}
        if result["repository"]["branch"] != EXPECTED_BRANCH:
            raise F1Error(f"expected branch {EXPECTED_BRANCH}, found {result['repository']['branch']}")
        _git("merge-base", "--is-ancestor", F0_BASELINE, "HEAD")
        result["repository"]["f0_baseline_is_ancestor"] = True
        if not sys.platform.startswith("linux"):
            raise F1Error("Fair runtime is Linux-only; Windows supports validation/tests only")
        bw1_inputs = bw1.validate_bw1_inputs(shellset_root, Path(bw1_root))
        if Path(partition_payload).resolve() != bw1.PARTITION_PATH.resolve() or si1.sha256(Path(partition_payload)) != bw1_inputs["partition_payload_sha256"]:
            raise F1Error("partition input differs from manifested canonical partition")
        lock = json.loads(bw1.LOCK_PATH.read_text(encoding="utf-8"))
        original_hashes = {"source_lock": si1.verify_source_lock(shellset_root, lock),
            "original_feg": bw1_inputs["source_inputs"]["feg_sha256"],
            "original_runtime": bw1_inputs["source_inputs"]["runtime_package_sha256"],
            "bw1_feg": bw1_inputs["derived_inputs"]["feg_sha256"],
            "bw1_runtime": bw1_inputs["derived_inputs"]["runtime_package_sha256"]}
        result["input_validation"] = bw1_inputs
        tools = [_probe_tool(name) for name in ("nvfortran", "mpifort", "mpiexec", "make")]
        nvhpc_text = "\n".join(x["version_excerpt"] for x in tools[:2]).lower()
        if "nvfortran" not in nvhpc_text or "25.11" not in nvhpc_text:
            raise F1Error("toolchain does not identify qualified NVIDIA HPC SDK 25.11")
        result["toolchain"] = tools
        build_root = output_dir / "build_f1"
        result["instrumented_build"] = _instrumented_build_tree(shellset_root, build_root)
        build = si1.run_checked(["make", "ShellSet"], cwd=build_root, timeout=runtime_limit_seconds,
            stdout_path=output_dir / "logs" / "build_f1.log", env=si1._solver_env())
        if build.returncode != 0 or not (build_root / "ShellSet.exe").is_file():
            raise F1Error(f"instrumented F1 build failed with status {build.returncode}")
        executables = list(build_root.rglob("ShellSet.exe"))
        if executables != [build_root / "ShellSet.exe"]:
            raise F1Error("build did not produce exactly one isolated ShellSet executable")
        run_dir = output_dir / "run_f1"
        run_dir.mkdir()
        input_dir = run_dir / "INPUT"
        si1.write_input_files(input_dir)
        derived = Path(bw1_root).resolve() / "derived"
        shutil.copy2(derived / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg", input_dir / bw1.DEFAULT_FEG.name)
        shutil.copy2(derived / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat", input_dir / bw1.DEFAULT_PACKAGE.name)
        shutil.copy2(shellset_root / "INPUT" / "iEarth5-049.in", input_dir / "SI1_ENGINEERING_REFERENCE.in")
        matrix = json.loads(bw1.DEFAULT_FEG_MANIFEST.read_text(encoding="utf-8"))["runtime_coordinate_frame"]["forward_rotation_matrix"]
        rings = si1.canonical_plate_rings(Path(partition_payload), matrix)
        symbols = si1._plate_symbols(shellset_root / "src" / "MOD_SharedVars.f90")
        si1.write_plate_outlines(input_dir / "ARCANA_PLATE_OUTLINES.dig", rings, symbols, derived / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg")
        shutil.copy2(build_root / "ShellSet.exe", run_dir / "ShellSet.exe")
        expected = {"InputFiles.in", "ListInput.in", "SI1_NO_VELOCITY.bcs", "SI1_UNUSED_PLATE_PAIR.dig",
            bw1.DEFAULT_FEG.name, bw1.DEFAULT_PACKAGE.name, "SI1_ENGINEERING_REFERENCE.in", "ARCANA_PLATE_OUTLINES.dig"}
        if {p.name for p in input_dir.iterdir() if p.is_file()} != expected:
            raise F1Error("staged ShellSet input set is incomplete or includes unexpected files")
        if [p.name for p in run_dir.glob("*.exe")] != ["ShellSet.exe"]:
            raise F1Error("runtime staging must contain only the instrumented F1 executable")
        staged_hashes = {p.relative_to(run_dir).as_posix(): _sha256(p)
                         for p in sorted(input_dir.iterdir()) if p.is_file()}
        result["staged_input_hashes_before"] = staged_hashes
        command = ["mpiexec", "-n", str(MPI_RANKS), "./ShellSet.exe", "-Iter", "1", "-InOpt", "List", "-Dir", "RUN_OUTPUT"]
        result["mpi_command"] = command
        env = si1._solver_env()
        started = time.monotonic()
        code, log_text = _run_limited(command, cwd=run_dir, timeout=runtime_limit_seconds,
            per_process_bytes=int(memory_cap_gib_per_process * 1024**3),
            output_path=output_dir / "logs" / "f1_mpi_combined.log", env=env)
        elapsed = time.monotonic() - started
        result["runtime"] = {"returncode": code, "elapsed_seconds": elapsed,
            "combined_stdout_stderr_preserved": True, "log_sha256": _sha256(output_dir / "logs" / "f1_mpi_combined.log")}
        result["diagnostics"] = validate_f1_log(log_text, mpi_exit_code=code)
        result["instrumented_build"]["static_proof"] = inspect_instrumentation((build_root / "src" / "MOD_Shells.f90").read_text(encoding="utf-8"))
        for relative, digest in staged_hashes.items():
            staged_path = run_dir / relative
            if not staged_path.is_file() or _sha256(staged_path) != digest:
                raise F1Error(f"staged FEG/runtime/control input changed during run: {relative}")
        result["staged_inputs_unchanged"] = True
        if original_hashes["source_lock"] != si1.verify_source_lock(shellset_root, lock):
            raise F1Error("locked ShellSet source changed during F1 run")
        for name, path, expected_sha in (
            ("original_feg", bw1.DEFAULT_FEG, original_hashes["original_feg"]),
            ("original_runtime", bw1.DEFAULT_PACKAGE, original_hashes["original_runtime"]),
            ("bw1_feg", derived / bw1.DEFAULT_FEG.name, original_hashes["bw1_feg"]),
            ("bw1_runtime", derived / bw1.DEFAULT_PACKAGE.name, original_hashes["bw1_runtime"]),
        ):
            if _sha256(path) != expected_sha:
                raise F1Error(f"preservation hash changed: {name}")
        result["preservation_hashes_verified"] = True
        result["decision"] = "PASS_BW1_FAIR_ASSEMBLY_ONLY"
    except Exception as exc:
        result["failure"] = f"{type(exc).__name__}: {exc}"
    _write_report(output_dir, result)
    _seal_manifest(output_dir)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_f1(args.shellset_root, args.bw1_root, args.partition_payload, args.output_dir,
            runtime_limit_seconds=args.runtime_limit_seconds,
            memory_cap_gib_per_process=args.memory_cap_gib_per_process,
            aggregate_memory_budget_gib=args.aggregate_memory_budget_gib)
    except (OSError, ValueError, F1Error, subprocess.SubprocessError) as exc:
        parser.exit(2, f"BLOCKED_BW1_F1_ASSEMBLY_PREFLIGHT: {exc}\n")
    print(result["decision"])
    if result["decision"] != "PASS_BW1_FAIR_ASSEMBLY_ONLY":
        print(result.get("failure", "assembly-only qualification failed"), file=sys.stderr)
        return 2
    print(f"BW1_F1_MATRIX={json.dumps(result['diagnostics']['system']['matrix'], sort_keys=True)}")
    print(f"BW1_F1_FORCING={json.dumps(result['diagnostics']['system']['forcing'], sort_keys=True)}")
    print(f"BW1_F1_EVIDENCE={args.output_dir / 'BW1_F1_RESULT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
