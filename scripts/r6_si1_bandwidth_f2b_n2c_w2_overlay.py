"""Build a reproducible N2C-W2 candidate copy without editing source-locked ShellSet."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LOCK_PATH = ROOT / "configs" / "r6_shells_si1" / "shellset_source_lock.json"
SOURCE_LOCK_SHA256 = "8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2"
SOURCE_MOD_SHA256 = "860b1311e3e2f856b86c7e4f5e988d0591ddf95ff958add1753672dfa9c737f4"
SOURCE_MAKEFILE_SHA256 = "56d6e03690674055d7a8bb1e8ae9b494bc6e4bc35ba8d63febc3aab43150a37c"
SOURCE_WRITER_SHA256 = "243d698e6d180ebfa22448d88f37f21976be69fc1eeeac0506953192c74f3a32"
SOURCE_MAIN_SHA256 = "603174fb0fae80ea48199750e4c5c255eef7005d353cc42ed8c90f46c6bfecec"
SOURCE_SHELLS_SHA256 = "eb306bfb11c577f2a98ec091f6450b6df35ba0188ae97eca2f77c4603bb78e32"
VBC_ANCHOR = "CALL VBCs (iCond, mxBn, mxDOF, &           ! input\n&            nCond, nDOF, nLB, nodCon, nUB, &\n&            vBCArg, vBCMag, &\n&            f, k)                           ! modify\n"
SOLVER_ANCHOR = "CALL Solver (iUnitT, &         ! input\n"
FEM_USE_ANCHOR = "SUBROUTINE FEM (alpha, area, constr, detJ, &  ! input\n"
MAKE_OBJECT_LINES = {
    "OBJS    =": "r6_sparse_snapshot_writer.o r6_n2c_shellset_capture_bridge.o ",
    "OBJSDB  =": "r6_sparse_snapshot_writer.DB.o r6_n2c_shellset_capture_bridge.DB.o ",
    "OBJSOPT =": "r6_sparse_snapshot_writer.OPT.o r6_n2c_shellset_capture_bridge.OPT.o ",
}


class OverlayError(ValueError):
    """Candidate overlay could not be applied safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise OverlayError(f"expected one {label} anchor, found {count}")
    return text.replace(old, new, 1)


def _verify_full_source_lock(source_package: Path) -> dict[str, object]:
    lock_bytes = SOURCE_LOCK_PATH.read_bytes()
    if hashlib.sha256(lock_bytes).hexdigest() != SOURCE_LOCK_SHA256:
        raise OverlayError("checked-in ShellSet source lock SHA256 differs from the pinned identity")
    try:
        lock = json.loads(lock_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OverlayError("checked-in ShellSet source lock is not valid UTF-8 JSON") from exc
    if lock.get("schema") != "arcana_worldsim.r6.shells_si1_source_lock.v1":
        raise OverlayError("unexpected ShellSet source lock schema")
    locked_files = lock.get("files")
    if not isinstance(locked_files, dict) or not locked_files:
        raise OverlayError("ShellSet source lock has no file membership")

    source_root = os.path.normcase(os.path.abspath(source_package))

    def regular_member(relative: Path, label: str) -> Path:
        candidate = source_package / relative
        candidate_absolute = os.path.normcase(os.path.abspath(candidate))
        if candidate_absolute == source_root or not candidate_absolute.startswith(source_root + os.sep):
            raise OverlayError(f"{label} escapes source package")
        current = source_package
        for component in relative.parts:
            current = current / component
            if current.is_symlink():
                raise OverlayError(f"{label} traverses a symlink")
        if not candidate.is_file():
            raise OverlayError(f"{label} is missing or is not a regular file")
        return candidate

    verified: dict[str, str] = {}
    for relative_name, expected in sorted(locked_files.items()):
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts or not isinstance(expected, str):
            raise OverlayError(f"unsafe or malformed source-lock member: {relative_name!r}")
        path = regular_member(relative, f"source-lock member {relative_name}")
        actual = _sha256(path)
        if actual != expected:
            raise OverlayError(f"source-lock SHA256 differs for {relative_name}")
        verified[relative_name] = actual

    parameter_relative = Path("INPUT/iEarth5-049.in")
    parameter_path = regular_member(parameter_relative, "parameter reference")
    parameter_sha = _sha256(parameter_path)
    if parameter_sha != lock.get("parameter_reference_sha256"):
        raise OverlayError("parameter reference SHA256 differs from the checked-in source lock")
    return {
        "lock_sha256": SOURCE_LOCK_SHA256,
        "vendored_arcana_source_commit_claim": lock.get("vendored_arcana_source_commit"),
        "locked_file_sha256": verified,
        "parameter_reference_sha256": parameter_sha,
    }


def _patch_mod_shells(text: str) -> str:
    pure_end = "&                  ThID,SHELLSconv)\n"
    text = _replace_once(
        text, pure_end,
        "&                  ThID,SHELLSconv,n2c_model_num,n2c_rpeat)\n",
        "Pure signature",
    )
    text = _replace_once(
        text,
        "INTEGER,INTENT(IN) :: ThID\nLOGICAL,INTENT(INOUT) :: SHELLSconv\n",
        "INTEGER,INTENT(IN) :: ThID\n"
        "INTEGER,INTENT(IN) :: n2c_model_num,n2c_rpeat\n"
        "LOGICAL,INTENT(INOUT) :: SHELLSconv\n",
        "Pure invocation declarations",
    )
    text = _replace_once(
        text, "INTEGER i, ios, iprint, iter, m, memory\n",
        "INTEGER i, ios, iprint, iter, m, memory, n2c_fem_call_ordinal\n",
        "Pure ordinal declaration",
    )
    text = _replace_once(
        text, "DO 1000 iter = 1, maxItr\n",
        "n2c_fem_call_ordinal = 0\nDO 1000 iter = 1, maxItr\n",
        "Pure ordinal initialization",
    )
    text = _replace_once(
        text,
        FEM_USE_ANCHOR,
        FEM_USE_ANCHOR,
        "FEM declaration",
    )
    # USE statements must precede IMPLICIT NONE. Anchor only the FEM routine's
    # first declaration block by including its routine-specific argument list.
    fem_decl_end = "&                 f, k, ipiv)                   ! work\n"
    text = _replace_once(
        text,
        fem_decl_end,
        "&                 f, k, ipiv, &                   ! work\n"
        "&                 n2c_model_num, n2c_process_rank, n2c_rpeat, &\n"
        "&                 n2c_iteration, n2c_fem_call_ordinal)\n"
        "USE r6_n2c_shellset_capture_bridge, ONLY: n2c_capture_pre_solver\n",
        "FEM USE insertion",
    )
    local_anchor = "INTEGER i, j\nREAL*8 bDenom, bDen, bDenoN, dVSize\n"
    text = _replace_once(
        text,
        local_anchor,
        local_anchor
        + "INTEGER, INTENT(IN) :: n2c_model_num, n2c_process_rank, n2c_rpeat\n"
        + "INTEGER, INTENT(IN) :: n2c_iteration, n2c_fem_call_ordinal\n"
        + "LOGICAL n2c_solver_may_proceed\nCHARACTER(192) n2c_message\n",
        "FEM capture locals",
    )
    text = _replace_once(
        text,
        VBC_ANCHOR + "\n" + SOLVER_ANCHOR,
        VBC_ANCHOR
        + "CALL n2c_capture_pre_solver(k, f(:,1), iDiagonal, &\n"
        + "&                                n2c_solver_may_proceed, n2c_message)\n"
        + "IF (.NOT. n2c_solver_may_proceed) THEN\n"
        + "  WRITE(*,'(A)') TRIM(n2c_message)\n"
        + "  ERROR STOP 86\n"
        + "END IF\n\n"
        + SOLVER_ANCHOR,
        "post-VBCs/pre-Solver gate",
    )
    text = _replace_once(
        text,
        "CALL FEM (alpha, area, constr, detJ, &  ! input\n",
        "n2c_fem_call_ordinal = n2c_fem_call_ordinal + 1\n"
        "CALL FEM (alpha, area, constr, detJ, &  ! input\n",
        "Pure FEM ordinal increment",
    )
    text = _replace_once(
        text,
        "&                f, k, ipiv)                   ! work\n",
        "&                f, k, ipiv, &                   ! work\n"
        "&                n2c_model_num, ThID, n2c_rpeat, iter, &\n"
        "&                n2c_fem_call_ordinal)\n",
        "Pure FEM invocation arguments",
    )
    call_anchor = "CALL n2c_capture_pre_solver(k, f(:,1), iDiagonal, &\n"
    text = _replace_once(
        text,
        call_anchor,
        "CALL n2c_capture_pre_solver(k, f(:,1), iDiagonal, &\n"
        "&                                n2c_model_num, n2c_process_rank, &\n"
        "&                                n2c_rpeat, n2c_iteration, &\n"
        "&                                n2c_fem_call_ordinal, &\n",
        "capture context propagation",
    )
    return text


def _patch_main(text: str) -> str:
    old = "call Shells_v5p0(ListVarNames,ListVarValues(1,:),rpeat,SHELLSconv)"
    new = "call Shells_v5p0(ListVarNames,ListVarValues(1,:),rpeat,SHELLSconv,ModNum)"
    if text.count(old) != 2:
        raise OverlayError(f"expected the two Shells_v5p0 call sites, found {text.count(old)}")
    return text.replace(old, new)


def _patch_shells(text: str) -> str:
    text = _replace_once(
        text,
        "subroutine Shells_v5p0(VarNames,VarValues,rpeat,SHELLSconv)\n",
        "subroutine Shells_v5p0(VarNames,VarValues,rpeat,SHELLSconv,n2c_model_num)\n",
        "Shells_v5p0 signature",
    )
    text = _replace_once(
        text,
        "INTEGER,INTENT(IN) :: rpeat\n",
        "INTEGER,INTENT(IN) :: rpeat, n2c_model_num\n",
        "Shells_v5p0 model declaration",
    )
    return _replace_once(
        text,
        "&            outVec, stiff, ipiv, tOfset, ThID, SHELLSconv)\n",
        "&            outVec, stiff, ipiv, tOfset, ThID, SHELLSconv, &\n"
        "&            n2c_model_num, rpeat)\n",
        "Pure call identity arguments",
    )


def _patch_makefile(text: str) -> str:
    for prefix, objects in MAKE_OBJECT_LINES.items():
        line = next((line for line in text.splitlines(keepends=True) if line.startswith(prefix)), None)
        if line is None or objects.strip() in line:
            raise OverlayError(f"missing or already-patched Makefile object line: {prefix}")
        first_object = line.split("=", 1)[1].lstrip()
        text = _replace_once(text, first_object, objects + first_object, f"{prefix} object list")

    rules = (
        "r6_sparse_snapshot_writer.o : r6_sparse_snapshot_writer.f90\n"
        "r6_n2c_shellset_capture_bridge.o : r6_n2c_shellset_capture_bridge.f90 | r6_sparse_snapshot_writer.o\n"
        "MOD_Shells.o     : MOD_Shells.f90   MOD_SharedVars.o MOD_ShellSet.o MOD_ArcanaRuntime.o DMods.o | r6_n2c_shellset_capture_bridge.o\n"
        "r6_sparse_snapshot_writer.DB.o : r6_sparse_snapshot_writer.f90\n"
        "r6_n2c_shellset_capture_bridge.DB.o : r6_n2c_shellset_capture_bridge.f90 | r6_sparse_snapshot_writer.DB.o\n"
        "MOD_Shells.DB.o : MOD_Shells.f90 MOD_SharedVars.DB.o MOD_ShellSet.DB.o MOD_ArcanaRuntime.DB.o DMods.DB.o | r6_n2c_shellset_capture_bridge.DB.o\n"
        "r6_sparse_snapshot_writer.OPT.o : r6_sparse_snapshot_writer.f90\n"
        "r6_n2c_shellset_capture_bridge.OPT.o : r6_n2c_shellset_capture_bridge.f90 | r6_sparse_snapshot_writer.OPT.o\n"
        "MOD_Shells.OPT.o : MOD_Shells.f90 MOD_SharedVars.OPT.o MOD_ShellSet.OPT.o MOD_ArcanaRuntime.OPT.o DMods.OPT.o | r6_n2c_shellset_capture_bridge.OPT.o\n"
    )
    anchor = "# ----- Dependency chains -----\n"
    return _replace_once(text, anchor, anchor + rules, "dependency chain")


def create_candidate(source_package: Path, output_root: Path) -> dict[str, object]:
    # pathlib.resolve() traverses Windows reparse points and may require
    # privileges unavailable in the sandbox. Use normalized absolute lexical
    # paths here; copytree/open still fail closed if an input is inaccessible.
    source_package = Path(os.path.abspath(source_package))
    output_root = Path(os.path.abspath(output_root))
    source_mod = source_package / "src" / "MOD_Shells.f90"
    source_main = source_package / "src" / "ShellSetMain.f90"
    source_shells = source_package / "src" / "SHELLS_v5.0.f90"
    source_makefile = source_package / "Makefile"
    writer = ROOT / "src" / "fortran" / "r6_sparse_snapshot_writer.f90"
    bridge = ROOT / "src" / "fortran" / "r6_n2c_shellset_capture_bridge.f90"
    source_identity = _verify_full_source_lock(source_package)
    for path, expected, name in (
        (source_mod, SOURCE_MOD_SHA256, "source-locked MOD_Shells.f90"),
        (source_main, SOURCE_MAIN_SHA256, "source-locked ShellSetMain.f90"),
        (source_shells, SOURCE_SHELLS_SHA256, "source-locked SHELLS_v5.0.f90"),
        (source_makefile, SOURCE_MAKEFILE_SHA256, "ShellSet Makefile"),
        (writer, SOURCE_WRITER_SHA256, "N2C-W1 writer"),
    ):
        if _sha256(path) != expected:
            raise OverlayError(f"{name} SHA256 differs from the pinned overlay input")
    if not bridge.is_file():
        raise OverlayError("candidate bridge source is missing")
    if output_root.exists():
        raise OverlayError("candidate output must be a new, nonexistent directory")
    source_norm = os.path.normcase(str(source_package))
    output_norm = os.path.normcase(str(output_root))
    if output_norm == source_norm or output_norm.startswith(source_norm + os.sep) or source_norm.startswith(output_norm + os.sep):
        raise OverlayError("source and output roots must be disjoint")

    shutil.copytree(source_package, output_root)
    candidate_mod = output_root / "src" / "MOD_Shells.f90"
    candidate_main = output_root / "src" / "ShellSetMain.f90"
    candidate_shells = output_root / "src" / "SHELLS_v5.0.f90"
    candidate_makefile = output_root / "Makefile"
    candidate_mod.write_text(_patch_mod_shells(candidate_mod.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    candidate_main.write_text(_patch_main(candidate_main.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    candidate_shells.write_text(_patch_shells(candidate_shells.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    candidate_makefile.write_text(_patch_makefile(candidate_makefile.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    shutil.copy2(writer, output_root / "src" / writer.name)
    shutil.copy2(bridge, output_root / "src" / bridge.name)

    manifest: dict[str, object] = {
        "schema": "ARCANA_R6_N2C_W2_CANDIDATE_OVERLAY_V1",
        "source_package": str(source_package),
        "source_lock_sha256": source_identity["lock_sha256"],
        "source_commit_claim_from_lock": source_identity["vendored_arcana_source_commit_claim"],
        "source_locked_file_sha256": source_identity["locked_file_sha256"],
        "source_parameter_reference_sha256": source_identity["parameter_reference_sha256"],
        "source_mod_shells_sha256": SOURCE_MOD_SHA256,
        "source_shellset_main_sha256": SOURCE_MAIN_SHA256,
        "source_shells_sha256": SOURCE_SHELLS_SHA256,
        "source_makefile_sha256": SOURCE_MAKEFILE_SHA256,
        "w1_writer_sha256": SOURCE_WRITER_SHA256,
        "candidate_mod_shells_sha256": _sha256(candidate_mod),
        "candidate_shellset_main_sha256": _sha256(candidate_main),
        "candidate_shells_sha256": _sha256(candidate_shells),
        "candidate_makefile_sha256": _sha256(candidate_makefile),
        "candidate_writer_sha256": _sha256(output_root / "src" / writer.name),
        "candidate_bridge_sha256": _sha256(output_root / "src" / bridge.name),
        "candidate_source_locked_file_sha256": {
            relative_name: _sha256(output_root / relative_name)
            for relative_name in source_identity["locked_file_sha256"]
        },
        "runtime_invocation_identity": "UNKNOWN; CAPTURE_ONLY is fail-closed",
        "si1_eligibility": "BLOCKED_W1_SYNTHETIC_DIMENSION_LIMITS",
        "build_identity": "CANDIDATE_SOURCE_IDENTITY_ONLY; no build performed",
    }
    (output_root / "N2C_W2_CANDIDATE_OVERLAY.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", type=Path, default=ROOT / "external" / "ShellSet-v1.1.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = create_candidate(args.source_package, args.output)
    except (OSError, OverlayError) as exc:
        parser.error(str(exc))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
