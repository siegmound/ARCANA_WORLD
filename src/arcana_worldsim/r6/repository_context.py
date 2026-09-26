"""Platform-neutral Git repository provenance and baseline checks for R6."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess


@dataclass(frozen=True)
class RepositoryContext:
    root: str
    branch: str | None
    detached: bool
    head: str
    refs: dict[str, str | None]

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "origin_main": self.refs.get("origin/main"),
        }


def _git(root: Path, *args: str, allow_missing: bool = False) -> str | None:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode:
        if allow_missing:
            return None
        raise RuntimeError(
            f"git {' '.join(args)} failed in {root}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def repository_context(
    repository_root: str | Path,
    *,
    refs: tuple[str, ...] = ("origin/main",),
) -> RepositoryContext:
    """Return repository identity; branch is provenance, never scientific authority."""
    root = Path(repository_root).resolve()
    top = _git(root, "rev-parse", "--show-toplevel")
    if top is None or Path(top).resolve() != root:
        raise RuntimeError(f"execution is not rooted at the intended repository: {root}")
    head = _git(root, "rev-parse", "HEAD")
    if head is None:
        raise RuntimeError(f"cannot resolve repository HEAD: {root}")
    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD", allow_missing=True)
    resolved_refs = {
        ref: _git(root, "rev-parse", "--verify", ref, allow_missing=True)
        for ref in refs
    }
    return RepositoryContext(
        root=str(root), branch=branch, detached=branch is None, head=head,
        refs=resolved_refs,
    )


def require_repository_context(
    repository_root: str | Path,
    *,
    expected_head: str | None = None,
    expected_refs: dict[str, str] | None = None,
    required_ancestor: str | None = None,
    refs: tuple[str, ...] = ("origin/main",),
) -> RepositoryContext:
    """Validate repository/root and optional commit ancestry, not branch names."""
    names = tuple(dict.fromkeys((*refs, *(expected_refs or {}).keys())))
    context = repository_context(repository_root, refs=names)
    if expected_head is not None and context.head != expected_head:
        raise RuntimeError(
            f"unexpected HEAD: expected {expected_head}, found {context.head}"
        )
    for ref, expected in (expected_refs or {}).items():
        actual = context.refs.get(ref)
        if actual != expected:
            raise RuntimeError(
                f"unexpected {ref}: expected {expected}, found {actual}"
            )
    if required_ancestor is not None:
        root = Path(context.root)
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", required_ancestor, "HEAD"],
            cwd=root, text=True, capture_output=True, check=False,
        )
        if result.returncode:
            raise RuntimeError(
                f"required base is not an ancestor of HEAD: {required_ancestor}"
            )
    return context


def repository_provenance(repository_root: str | Path) -> dict[str, object]:
    """Serialize actual Git context, including detached-HEAD provenance."""
    context = repository_context(repository_root)
    return context.to_dict()


def canonical_text_sha256(path: str | Path) -> str:
    """Hash UTF-8 text after the declared CRLF/CR-to-LF canonicalization."""
    data = Path(path).read_bytes()
    text = data.decode("utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def external_root(repository_root: str | Path) -> Path:
    """Resolve externally stored payloads without assuming a workstation path."""
    import os

    configured = os.environ.get("ARCANA_EXTERNAL_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(repository_root).resolve().parent / "_ARCANA_EXTERNAL_SOURCES"


def resolve_external_payload_path(repository_root: str | Path, stored_path: str) -> Path:
    """Resolve logical or legacy workstation payload paths portably."""
    root = Path(repository_root).resolve()
    normalized = str(stored_path).replace("\\", "/")
    marker = "_ARCANA_EXTERNAL_SOURCES/"
    if marker in normalized:
        logical = normalized.split(marker, 1)[1]
        return external_root(root).joinpath(*PurePosixPath(logical).parts)
    candidate = Path(stored_path).expanduser()
    if candidate.is_absolute():
        return candidate
    if re.match(r"^[A-Za-z]:/", normalized):
        raise ValueError(f"absolute external path has no recognized payload-root marker: {stored_path}")
    if normalized.startswith("r6/"):
        return external_root(root).joinpath(*PurePosixPath(normalized).parts)
    return (root / candidate).resolve()


def verify_protected_staged_blobs(
    repository_root: str | Path, expected_blobs: dict[str, str]
) -> dict[str, str | None]:
    """Verify protected blob identities only when those paths are staged.

    A clean checkout has no staged replacement to protect. In a dirty checkout,
    any staged version must match the recorded protected blob exactly.
    """
    root = Path(repository_root).resolve()
    verified: dict[str, str | None] = {}
    for path, expected in expected_blobs.items():
        staged_change = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", path],
            cwd=root, text=True, capture_output=True, check=False,
        )
        if staged_change.returncode == 0:
            verified[path] = None
            continue
        if staged_change.returncode != 1:
            raise RuntimeError(f"cannot inspect staged state for protected path {path}")
        actual = _git(root, "rev-parse", f":{path}")
        if actual != expected:
            raise RuntimeError(
                f"protected staged blob changed for {path}: expected {expected}, found {actual}"
            )
        verified[path] = actual
    return verified
