"""Offline, source-derived resource arithmetic for the SI1 engineering case.

This module validates named-array formulas only. It does not estimate or
certify process RSS, runtime overhead, or Fair-enforced resource limits.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping


OFFLINE_VALIDATOR_PASS = "OFFLINE_VALIDATOR_PASS"
ARITHMETIC_VERIFIED = "ARITHMETIC_VERIFIED"
INVALID_INPUT = "INVALID_INPUT"
INSUFFICIENT_RESOURCE_AUTHORITY = "INSUFFICIENT_RESOURCE_AUTHORITY"
PENDING_HPC_MEASUREMENT = "PENDING_HPC_MEASUREMENT"
IDENTITY_DECLARED_ONLY = "IDENTITY_DECLARED_ONLY"
SOURCE_IDENTITY_VERIFIED = "SOURCE_IDENTITY_VERIFIED"

D3A_REPORT_SHA256 = "ca2ff09491bbdcb995fc79fb9e4cf66b461c519a2fc67f652e09099c70884989"
F2AV_RECOVERY_MANIFEST_SHA256 = "3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f"
D3A_AUDIT_SOURCE_COMMIT = "9adb986f510d81d220ab39b69a2df71704aac606"
ENGINEERING_CASE_SHA256 = "c5062a1d831e44ff787e66d2a88e50f570b9d716dfe2b5b19aba0751d2ee529d"
CASE_ID = "ARCANA_SHELLS_GLOBAL_CONTINUUM_ENGINEERING_V0"
REQUIRED_ARRAY_FAMILIES = frozenset(
    {
        "matrix_stiff",
        "element_real",
        "node_real",
        "node_integer_logical",
        "dof_real_integer",
        "boundary",
        "element_integer_logical",
        "plates",
        "list",
        "runtime_nodes",
        "region_lr",
    }
)

# JSON documents are parsed from immutable in-memory snapshots. The caps are
# defensive parser limits, not claims about the total evidence-tree size.
MAX_CASE_JSON_BYTES = 1 * 1024 * 1024
MAX_D3A_REPORT_BYTES = 8 * 1024 * 1024
MAX_RECOVERY_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_RECOVERY_RESULT_BYTES = 32 * 1024 * 1024
MAX_STREAMED_MEMBER_BYTES = 2 * 1024 * 1024 * 1024


class _InvalidInput(Exception):
    pass


def sha256_file(path: str | Path) -> str:
    """Return the byte SHA256 of a local configuration/evidence file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open_confined_no_follow(candidate: Path, root: Path, relative: Path) -> int:
    """Open a confined path, walking via directory descriptors where available."""
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    if os.open in getattr(os, "supports_dir_fd", set()) and nofollow and directory:
        current = os.open(root, flags | directory | nofollow)
        try:
            for part in relative.parts[:-1]:
                following = os.open(part, flags | directory | nofollow, dir_fd=current)
                os.close(current)
                current = following
            return os.open(relative.parts[-1], flags | nofollow, dir_fd=current)
        finally:
            os.close(current)
    return os.open(candidate, flags | nofollow)


def _is_link_like(path: Path) -> bool:
    junction_check = getattr(path, "is_junction", None)
    return path.is_symlink() or (callable(junction_check) and junction_check())


def _read_snapshot(path: Path, *, root: Path, expected_sha256: str,
                   expected_size: int | None, max_bytes: int) -> bytes:
    """Read one confined regular file once and authenticate those exact bytes.

    Path checks and pre/post stat comparisons detect ordinary replacement and
    symlink races. Windows does not provide the same portable dir-fd/O_NOFOLLOW
    guarantees as POSIX, so this attests the bytes read, not future path
    stability or an atomic filesystem snapshot against a privileged racer.
    """
    root_abs = Path(os.path.abspath(root))
    candidate = Path(os.path.abspath(path))
    try:
        relative = candidate.relative_to(root_abs)
    except ValueError as exc:
        raise _InvalidInput("evidence path escapes the authorized evidence root") from exc
    if not relative.parts or any(part in (".", "..") for part in relative.parts):
        raise _InvalidInput("evidence path has an unsafe component")
    if _is_link_like(root_abs):
        raise _InvalidInput("evidence root may not be a symlink")
    cursor = root_abs
    for part in relative.parts:
        cursor = cursor / part
        if _is_link_like(cursor):
            raise _InvalidInput("evidence path may not traverse a symlink")
    try:
        before = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise _InvalidInput(f"evidence file is unavailable: {candidate}") from exc
    import stat
    if not stat.S_ISREG(before.st_mode):
        raise _InvalidInput("evidence path is not a regular file")
    if before.st_size < 0 or before.st_size > max_bytes:
        raise _InvalidInput("evidence file exceeds its declared snapshot size limit")
    if expected_size is not None and before.st_size != expected_size:
        raise _InvalidInput("evidence file size does not match the authenticated declaration")

    try:
        fd = _open_confined_no_follow(candidate, root_abs, relative)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise _InvalidInput("opened evidence handle is not a regular file")
            if (opened.st_dev, opened.st_ino, opened.st_size) != (before.st_dev, before.st_ino, before.st_size):
                raise _InvalidInput("evidence path identity changed before opening")
            content = stream.read(max_bytes + 1)
            after_fd = os.fstat(stream.fileno())
        after_path = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise _InvalidInput(f"cannot securely acquire evidence snapshot: {exc}") from exc
    if len(content) > max_bytes:
        raise _InvalidInput("evidence file exceeds its declared snapshot size limit")
    if len(content) != before.st_size or (after_fd.st_dev, after_fd.st_ino, after_fd.st_size) != (
            opened.st_dev, opened.st_ino, opened.st_size):
        raise _InvalidInput("evidence file changed while its snapshot was read")
    if (after_path.st_dev, after_path.st_ino, after_path.st_size) != (
            opened.st_dev, opened.st_ino, opened.st_size):
        raise _InvalidInput("evidence path was replaced during snapshot acquisition")
    if hashlib.sha256(content).hexdigest() != expected_sha256.lower():
        raise _InvalidInput("evidence snapshot SHA256 mismatch")
    return content


def _verify_streamed_member(path: Path, *, root: Path, expected_sha256: str,
                            expected_size: int) -> None:
    """Verify a non-JSON manifest member from one opened handle, bounded in size."""
    root_abs = Path(os.path.abspath(root))
    candidate = Path(os.path.abspath(path))
    try:
        relative = candidate.relative_to(root_abs)
    except ValueError as exc:
        raise _InvalidInput("manifest member escapes the authorized evidence root") from exc
    if not relative.parts or any(part in (".", "..") for part in relative.parts):
        raise _InvalidInput("manifest member has an unsafe path component")
    cursor = root_abs
    for part in relative.parts:
        cursor = cursor / part
        if _is_link_like(cursor):
            raise _InvalidInput("manifest member may not traverse a symlink")
    import stat
    try:
        before = candidate.stat(follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_size != expected_size:
            raise _InvalidInput("manifest member type or size mismatch")
        if expected_size > MAX_STREAMED_MEMBER_BYTES:
            raise _InvalidInput("manifest member exceeds streaming verification limit")
        fd = _open_confined_no_follow(candidate, root_abs, relative)
        digest = hashlib.sha256()
        total = 0
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino, opened.st_size) != (
                    before.st_dev, before.st_ino, before.st_size):
                raise _InvalidInput("manifest member changed before opening")
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > expected_size or total > MAX_STREAMED_MEMBER_BYTES:
                    raise _InvalidInput("manifest member exceeded declared size while streaming")
                digest.update(chunk)
            after_fd = os.fstat(stream.fileno())
        after_path = candidate.stat(follow_symlinks=False)
    except OSError as exc:
        raise _InvalidInput(f"cannot verify manifest member: {exc}") from exc
    if total != expected_size or digest.hexdigest() != expected_sha256.lower():
        raise _InvalidInput("manifest member size or SHA256 mismatch")
    if (after_fd.st_dev, after_fd.st_ino, after_fd.st_size) != (opened.st_dev, opened.st_ino, opened.st_size) or (
            after_path.st_dev, after_path.st_ino, after_path.st_size) != (
            opened.st_dev, opened.st_ino, opened.st_size):
        raise _InvalidInput("manifest member changed during verification")


def load_case_json(path: str | Path) -> tuple[dict[str, Any], str]:
    """Load JSON and return parsed case plus the hash of the exact source bytes."""
    source = Path(path).read_bytes()
    value = json.loads(source.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("engineering case JSON must be an object")
    return value, hashlib.sha256(source).hexdigest()


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise _InvalidInput(f"{name} must be an integer >= {minimum}")
    return value


def _checked_add(a: int, b: int, max_value: int, label: str) -> int:
    result = a + b
    if result > max_value:
        raise _InvalidInput(f"{label} overflows the declared byte-count format")
    return result


def _checked_mul(a: int, b: int, max_value: int, label: str) -> int:
    if a and b > max_value // a:
        raise _InvalidInput(f"{label} overflows the declared byte-count format")
    return a * b


def _valid_sha(value: Any, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
        raise _InvalidInput(f"{name} must be a declared 64-hex SHA256")
    return value.lower()


def _validate_identity(identity: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(identity, Mapping):
        raise _InvalidInput("identity must be a mapping")
    case_id = identity.get("case_id")
    if case_id != CASE_ID:
        raise _InvalidInput("case_id does not identify the governed SI1 engineering case")
    source_commit = identity.get("source_commit")
    if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", source_commit):
        raise _InvalidInput("source_commit must be a declared 40-hex commit identity")
    if source_commit.lower() != D3A_AUDIT_SOURCE_COMMIT:
        raise _InvalidInput("source_commit does not match the D3A audited source baseline")
    config_sha = _valid_sha(identity.get("configuration_sha256"), "configuration_sha256")
    if config_sha != ENGINEERING_CASE_SHA256:
        raise _InvalidInput("configuration identity is not the audited SI1 engineering-case byte hash")
    return {
        "case_id": case_id,
        "source_commit": source_commit.lower(),
        "configuration_sha256": config_sha,
        "allocation_inventory_sha256": _valid_sha(
            identity.get("allocation_inventory_sha256"), "allocation_inventory_sha256"
        ),
        "band_dimension_evidence_sha256": _valid_sha(
            identity.get("band_dimension_evidence_sha256"), "band_dimension_evidence_sha256"
        ),
    }


def _verified_evidence(case: Mapping[str, Any], identity: Mapping[str, str], paths: Mapping[str, Any]) -> dict[str, Any]:
    """Verify supplied source artifact bytes, manifest membership, and consumed dimensions."""
    required = {"engineering_case", "d3a_report", "f2av_recovery_manifest"}
    if not isinstance(paths, Mapping) or set(paths) != required:
        raise _InvalidInput(f"evidence_paths must contain exactly {sorted(required)}")
    repo_root = Path(__file__).resolve().parents[1]

    def confined_path(value: Any, root: Path, *, regular_file: bool) -> Path:
        if not isinstance(value, (str, Path)):
            raise _InvalidInput("evidence paths must be filesystem paths")
        raw_candidate = Path(value)
        if ".." in raw_candidate.parts:
            raise _InvalidInput("evidence path may not contain parent traversal")
        candidate = Path(os.path.abspath(raw_candidate))
        root = Path(os.path.abspath(root))
        try:
            relative = candidate.relative_to(root)
        except ValueError as exc:
            raise _InvalidInput("evidence path escapes the authorized evidence root") from exc
        cursor = root
        if _is_link_like(cursor):
            raise _InvalidInput("evidence root may not be a symlink")
        for part in relative.parts:
            cursor = cursor / part
            if _is_link_like(cursor):
                raise _InvalidInput("evidence path may not traverse a symlink")
        if not candidate.exists():
            raise _InvalidInput(f"evidence file is missing: {candidate}")
        if regular_file and not candidate.is_file():
            raise _InvalidInput("evidence path is not a regular file")
        return candidate

    case_path = confined_path(paths["engineering_case"], repo_root, regular_file=True)
    report_path = confined_path(paths["d3a_report"], repo_root, regular_file=True)
    manifest_path = confined_path(paths["f2av_recovery_manifest"], repo_root, regular_file=True)
    case_bytes = _read_snapshot(case_path, root=repo_root,
                                expected_sha256=identity["configuration_sha256"],
                                expected_size=None, max_bytes=MAX_CASE_JSON_BYTES)
    report_bytes = _read_snapshot(report_path, root=repo_root,
                                  expected_sha256=identity["allocation_inventory_sha256"],
                                  expected_size=None, max_bytes=MAX_D3A_REPORT_BYTES)
    manifest_bytes = _read_snapshot(
        manifest_path, root=repo_root,
        expected_sha256=identity["band_dimension_evidence_sha256"],
        expected_size=None, max_bytes=MAX_RECOVERY_MANIFEST_BYTES,
    )

    source_case = json.loads(case_bytes.decode("utf-8"))
    for key in ("schema", "case_id", "feg", "solver"):
        if case.get(key) != source_case.get(key):
            raise _InvalidInput(f"consumed case field {key} disagrees with verified configuration bytes")

    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if (not isinstance(manifest, dict)
            or manifest.get("schema") != "arcana_worldsim.r6.si1_f2av_offline_recovery_manifest.v1"
            or manifest.get("membership") != "all regular files except this manifest"):
        raise _InvalidInput("unexpected F2A-V recovery manifest contract")
    entries = manifest.get("artifacts") if isinstance(manifest, dict) else None
    if not isinstance(entries, list):
        raise _InvalidInput("F2A-V manifest lacks an artifacts list")
    evidence_root = manifest_path.parent
    expected_members: set[str] = set()
    verified_member_hashes: dict[str, str] = {}
    result_bytes: bytes | None = None
    result_relpath = "F2AV_RECOVERY_RESULT.json"
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"bytes", "path", "sha256"}:
            raise _InvalidInput("malformed F2A-V manifest entry")
        rel = entry["path"]
        rel_path = Path(rel) if isinstance(rel, str) else None
        if (not isinstance(rel, str) or not rel or rel_path is None or rel_path.is_absolute()
                or rel_path.drive or ".." in rel_path.parts or "\x00" in rel):
            raise _InvalidInput("unsafe F2A-V manifest member path")
        normalized_rel = rel.replace("\\", "/")
        if normalized_rel in expected_members:
            raise _InvalidInput("duplicate manifest member path")
        member = confined_path(evidence_root / rel, evidence_root, regular_file=True)
        member_size = _integer(entry["bytes"], "manifest bytes")
        member_sha = _valid_sha(entry["sha256"], "manifest sha256")
        if normalized_rel == result_relpath:
            result_bytes = _read_snapshot(
                member, root=evidence_root, expected_sha256=member_sha,
                expected_size=member_size, max_bytes=MAX_RECOVERY_RESULT_BYTES,
            )
        else:
            _verify_streamed_member(member, root=evidence_root,
                                    expected_sha256=member_sha, expected_size=member_size)
        verified_member_hashes[normalized_rel] = member_sha
        expected_members.add(normalized_rel)
    actual_members: set[str] = set()
    for p in evidence_root.rglob("*"):
        if _is_link_like(p):
            raise _InvalidInput("evidence directory contains a symlink")
        if p.is_file() and p != manifest_path:
            actual_members.add(p.relative_to(evidence_root).as_posix())
    if actual_members != expected_members:
        raise _InvalidInput("F2A-V manifest membership does not match evidence directory")
    if result_bytes is None:
        raise _InvalidInput("F2A-V manifest does not contain the required recovery result")
    result = json.loads(result_bytes.decode("utf-8"))
    stage = result.get("diagnostics", {}).get("stage", {})
    dimensions = case.get("band_dimensions", {})
    actual = {
        "nRank": stage.get("nRank"), "kl": stage.get("kl"),
        "ku": stage.get("ku"), "LDAB": stage.get("nKRows"),
    }
    consumed = {key: str(dimensions.get(key)) for key in ("kl", "ku", "LDAB")}
    consumed["nRank"] = str(case.get("derived_n_rank"))
    if consumed != actual:
        raise _InvalidInput("consumed band dimensions disagree with verified F2A-V result")
    return {
        "evidence_artifact_identity": SOURCE_IDENTITY_VERIFIED,
        "verified_paths": {
            "engineering_case": case_path.relative_to(repo_root).as_posix(),
            "d3a_report": report_path.relative_to(repo_root).as_posix(),
            "f2av_recovery_manifest": manifest_path.relative_to(repo_root).as_posix(),
        },
        "source_commit_identity": "DECLARED_ONLY_GIT_OBJECT_NOT_VERIFIED_BY_THIS_VALIDATOR",
        "manifest_member_count": len(actual_members),
        "snapshot_sha256": {
            "engineering_case": hashlib.sha256(case_bytes).hexdigest(),
            "d3a_report": hashlib.sha256(report_bytes).hexdigest(),
            "f2av_recovery_manifest": hashlib.sha256(manifest_bytes).hexdigest(),
            "manifest_members": dict(sorted(verified_member_hashes.items())),
        },
    }


def _allocation_formulas(
    *, n_nodes: int, n_elements: int, n_rank: int, ldab: int, lr_n: int,
    abi: Mapping[str, int], max_bytes: int,
) -> dict[str, int]:
    r8 = abi["real64_bytes"]
    integer = abi["integer_bytes"]
    logical = abi["logical_bytes"]
    char = abi["character_bytes"]

    def mul(count: int, width: int, label: str) -> int:
        return _checked_mul(count, width, max_bytes, label)

    def add(values: list[int], label: str) -> int:
        total = 0
        for value in values:
            total = _checked_add(total, value, max_bytes, label)
        return total

    matrix_entries = mul(ldab, n_rank, "matrix element count")
    matrix = mul(matrix_entries, r8, "matrix bytes")
    families = {
        "matrix_stiff": matrix,
        "element_real": mul(mul(603, n_elements, "element REAL count"), r8, "element REAL bytes"),
        "node_real": mul(mul(20, n_nodes, "node REAL count"), r8, "node REAL bytes"),
        "node_integer_logical": add(
            [mul(mul(3, n_nodes, "node INTEGER count"), integer, "node INTEGER bytes"),
             mul(n_nodes, logical, "node LOGICAL bytes")], "node integer/logical bytes"
        ),
        "dof_real_integer": add(
            [mul(mul(8, n_rank, "DOF REAL count"), r8, "DOF REAL bytes"),
             mul(n_rank, integer, "DOF INTEGER bytes")], "DOF bytes"
        ),
        "boundary": add(
            [mul(mul(5, n_nodes, "boundary REAL count"), r8, "boundary REAL bytes"),
             mul(mul(3, n_nodes, "boundary INTEGER count"), integer, "boundary INTEGER bytes"),
             mul(mul(2, n_nodes, "boundary CHARACTER count"), char, "boundary CHARACTER bytes")],
            "boundary bytes",
        ),
        "element_integer_logical": add(
            [mul(mul(4, n_elements, "element INTEGER count"), integer, "element INTEGER bytes"),
             mul(mul(18, n_elements, "element LOGICAL count"), logical, "element LOGICAL bytes")],
            "element integer/logical bytes",
        ),
        "plates": add(
            [mul(mul(mul(2, 12, "plate outline count"), 1250, "plate outline points"), r8,
                  "plate REAL bytes"), mul(12, integer, "plate INTEGER bytes")],
            "plate bytes",
        ),
        "list": mul(20, integer, "list bytes"),
        "runtime_nodes": mul(mul(51, n_nodes, "runtime REAL count"), r8, "runtime bytes"),
        "region_lr": mul(
            add([mul(13, r8, "LR REAL bytes"), mul(2, logical, "LR LOGICAL bytes")], "LR bytes per row"),
            lr_n + 1,
            "LR array bytes",
        ),
    }
    # Audit the independent family inventory rather than trusting an aggregate constant.
    if frozenset(families) != REQUIRED_ARRAY_FAMILIES:
        raise _InvalidInput("named allocation-family set is incomplete or duplicated")
    return families


def validate_resource_budget(
    case: Mapping[str, Any],
    *,
    lr_n: int,
    abi: Mapping[str, Any],
    identity: Mapping[str, Any],
    allocation_families: list[str] | tuple[str, ...],
    byte_count_bits: int = 64,
    scenario: str = "NO_PRESERVATION",
    require_complete_budget: bool = False,
    evidence_paths: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate SI1 named-array formulas; never claim total memory sufficiency.

    ``identity`` declares (but does not cryptographically authenticate) the
    configuration/source/inventory identities. Callers that load files should
    calculate their hashes from those exact file bytes first.
    """
    try:
        ident = _validate_identity(identity)
        if not isinstance(case, Mapping) or case.get("schema") != "arcana_worldsim.r6.shells_si1_engineering_case.v1":
            raise _InvalidInput("case schema is missing or unexpected")
        if case.get("case_id") != CASE_ID:
            raise _InvalidInput("case JSON does not match SI1 case identity")
        feg, solver = case.get("feg"), case.get("solver")
        if not isinstance(feg, Mapping) or not isinstance(solver, Mapping):
            raise _InvalidInput("case requires feg and solver objects")
        n_nodes = _integer(feg.get("nodes"), "feg.nodes", minimum=1)
        n_elements = _integer(feg.get("triangles"), "feg.triangles", minimum=1)
        n_faults = _integer(feg.get("fault_elements"), "feg.fault_elements")
        if (n_nodes, n_elements, n_faults) != (64_442, 128_880, 0):
            raise _InvalidInput("case cardinalities do not match the audited SI1 engineering case")
        models = _integer(solver.get("models"), "solver.models", minimum=1)
        mpi_ranks = _integer(solver.get("mpi_ranks"), "solver.mpi_ranks", minimum=2)
        if models != 1:
            raise _InvalidInput("SI1 resource inventory is scoped to one model")
        if mpi_ranks != 2:
            raise _InvalidInput("case rank count does not match the audited SI1 configuration")
        rank = _integer(case.get("derived_n_rank"), "nRank", minimum=1)
        dimensions = case.get("band_dimensions")
        if not isinstance(dimensions, Mapping):
            raise _InvalidInput("band_dimensions must be declared from dimension evidence")
        kl = _integer(dimensions.get("kl"), "kl")
        ku = _integer(dimensions.get("ku"), "ku")
        ldab = _integer(dimensions.get("LDAB"), "LDAB", minimum=1)
        if ident["band_dimension_evidence_sha256"] != F2AV_RECOVERY_MANIFEST_SHA256:
            raise _InvalidInput("band dimensions are not anchored to the declared F2A-V recovery manifest")
        expected_rank = _checked_mul(2, n_nodes, (1 << 63) - 1, "nRank")
        if rank != expected_rank:
            raise _InvalidInput("nRank must equal two DOFs per node")
        expected_ldab = _checked_add(
            _checked_add(_checked_mul(2, kl, (1 << 63) - 1, "2*kl"), ku, (1 << 63) - 1, "2*kl+ku"),
            1, (1 << 63) - 1, "LDAB",
        )
        if ldab != expected_ldab or kl >= rank or ku >= rank:
            raise _InvalidInput("LDAB/band dimensions are inconsistent")
        if kl != ku:
            raise _InvalidInput("SI1 ShellSet inventory requires the attested symmetric KSize half-bandwidth")
        lr_n = _integer(lr_n, "LRn")
        if byte_count_bits not in (32, 64, 128):
            raise _InvalidInput("byte_count_bits must be explicitly selected from 32, 64, 128")
        max_bytes = (1 << byte_count_bits) - 1

        required_abi = {"real64_bytes": 8, "integer_bytes": 4, "logical_bytes": 4, "character_bytes": 1}
        if not isinstance(abi, Mapping) or set(abi) != set(required_abi):
            raise _InvalidInput("all four ABI sizes must be explicitly declared")
        for key, expected in required_abi.items():
            if _integer(abi[key], f"abi.{key}", minimum=1) != expected:
                raise _InvalidInput(f"unsupported/unverified SI1 ABI assumption: {key}")
        integer_max = (1 << (required_abi["integer_bytes"] * 8 - 1)) - 1
        fortran_n_rank = 2 * n_nodes
        fortran_n_krows = 3 * kl + 1
        if fortran_n_rank > integer_max or fortran_n_krows > integer_max:
            raise _InvalidInput("a derived SI1 dimension exceeds the declared signed Fortran INTEGER range")
        if rank != fortran_n_rank or ldab != fortran_n_krows:
            raise _InvalidInput("derived Fortran nRank/nKRows dimensions are inconsistent")
        # LRn+1 is evaluated in the source Fortran integer kind; reject overflow there.
        if lr_n >= integer_max:
            raise _InvalidInput("LRn+1 is not representable in the declared signed Fortran INTEGER ABI")
        for name, value in {"nNodes": n_nodes, "nRank": rank, "kl": kl, "ku": ku, "LDAB": ldab,
                            "nElements": n_elements, "nFaults": n_faults, "models": models,
                            "mpiRanks": mpi_ranks, "LRn+1": lr_n + 1}.items():
            if value > integer_max:
                raise _InvalidInput(f"{name} exceeds the declared signed Fortran INTEGER range")
        if not isinstance(require_complete_budget, bool):
            raise _InvalidInput("require_complete_budget must be a boolean")

        if not isinstance(allocation_families, (list, tuple)):
            raise _InvalidInput("allocation_families must enumerate the independent source inventory")
        if len(allocation_families) != len(set(allocation_families)):
            raise _InvalidInput("duplicate allocation family")
        if frozenset(allocation_families) != REQUIRED_ARRAY_FAMILIES:
            raise _InvalidInput("allocation inventory is incomplete or contains unknown families")
        if ident["allocation_inventory_sha256"] != D3A_REPORT_SHA256:
            raise _InvalidInput("allocation inventory identity is not the D3A report identity")
        provenance = ({"evidence_artifact_identity": IDENTITY_DECLARED_ONLY,
                       "source_commit_identity": "DECLARED_ONLY_GIT_OBJECT_NOT_VERIFIED_BY_THIS_VALIDATOR"}
                      if evidence_paths is None else _verified_evidence(case, ident, evidence_paths))

        families = _allocation_formulas(
            n_nodes=n_nodes, n_elements=n_elements, n_rank=rank, ldab=ldab, lr_n=lr_n,
            abi=abi, max_bytes=max_bytes,
        )
        subtotal = 0
        for name in allocation_families:
            subtotal = _checked_add(subtotal, families[name], max_bytes, "explicit array subtotal")
        matrix_bytes = families["matrix_stiff"]
        rhs_bytes = _checked_mul(rank, abi["real64_bytes"], max_bytes, "RHS copy bytes")
        if scenario == "NO_PRESERVATION":
            preserved_increment = 0
        elif scenario == "COPY_A0_B0":
            preserved_increment = _checked_add(matrix_bytes, rhs_bytes, max_bytes, "A0/b0 copy increment")
        elif scenario == "REPLAYABLE_MATVEC":
            raise _InvalidInput("replayable matvec storage has no governed byte inventory")
        else:
            raise _InvalidInput("unknown preservation scenario")
        calculated = _checked_add(subtotal, preserved_increment, max_bytes, "calculated named-array bytes")
        resource_status = INSUFFICIENT_RESOURCE_AUTHORITY if require_complete_budget else OFFLINE_VALIDATOR_PASS
        return {
            "status": resource_status,
            "arithmetic_status": ARITHMETIC_VERIFIED,
            "source_identity_status": provenance["evidence_artifact_identity"],
            "hpc_status": PENDING_HPC_MEASUREMENT,
            "solver_acceptance": "THRESHOLD_UNJUSTIFIED",
            "validation_scope": "NAMED_ARRAY_FORMULA_VALIDATION_ONLY",
            "identity": ident,
            "provenance": provenance,
            "dimensions": {"nodes": n_nodes, "triangles": n_elements, "fault_elements": n_faults,
                           "nRank": rank, "kl": kl, "ku": ku, "LDAB": ldab, "LRn": lr_n},
            "LRn_authority": "DECLARED_ARGUMENT_NOT_REDERIVED_FROM_FEG_IN_THIS_VALIDATOR",
            "abi_assumptions_bytes": dict(abi),
            "abi_authority": "EXPLICIT_ASSUMPTION_NOT_COMPILER_ATTESTATION",
            "array_family_bytes": {name: families[name] for name in sorted(families)},
            "matrix_bytes": matrix_bytes,
            "named_array_subtotal_bytes": subtotal,
            "lr_term_bytes": families["region_lr"],
            "preservation_scenario": scenario,
            "preservation_increment_bytes": preserved_increment,
            "calculated_named_array_bytes": calculated,
            "overhead_not_accounted": [
                "allocation descriptors and allocator overhead", "compiler temporaries and stack",
                "MPI/NVHPC/LAPACK runtime and library allocations", "OS page accounting and fragmentation",
            ],
            "real_process_or_job_memory": "UNKNOWN",
            "fair_enforced_limits": PENDING_HPC_MEASUREMENT,
            "is_upper_bound_on_rss": False,
            "complete_budget_authority": "INSUFFICIENT_RESOURCE_AUTHORITY",
            "note": "A passing arithmetic check does not establish memory sufficiency or an RSS bound.",
        }
    except (_InvalidInput, OverflowError, TypeError, ValueError, KeyError, OSError, UnicodeError) as exc:
        return {"status": INVALID_INPUT, "reason": str(exc)}


__all__ = [
    "D3A_REPORT_SHA256", "INSUFFICIENT_RESOURCE_AUTHORITY", "INVALID_INPUT",
    "ARITHMETIC_VERIFIED", "OFFLINE_VALIDATOR_PASS", "PENDING_HPC_MEASUREMENT", "IDENTITY_DECLARED_ONLY",
    "SOURCE_IDENTITY_VERIFIED", "load_case_json",
    "sha256_file", "validate_resource_budget",
]
