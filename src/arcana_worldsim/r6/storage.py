"""Explicit, deterministic logical storage accounting for WORLD_HISTORY."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping
import os


class StorageCategory(str, Enum):
    CANONICAL_METADATA = "CANONICAL_METADATA"
    CANONICAL_PAYLOAD = "CANONICAL_PAYLOAD"
    INDEX = "INDEX"
    SCRATCH = "SCRATCH"
    PROVIDER_CACHE = "PROVIDER_CACHE"
    REFINEMENT_CACHE = "REFINEMENT_CACHE"
    QUALIFICATION_EVIDENCE = "QUALIFICATION_EVIDENCE"
    OPERATIONAL_METADATA = "OPERATIONAL_METADATA"


CANONICAL_HARD_CAP_BYTES = 500_000_000_000


@dataclass(frozen=True, slots=True)
class AccountingRoot:
    path: Path | str
    category: StorageCategory
    required: bool = True
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if not self.label:
            object.__setattr__(self, "label", self.category.value)


@dataclass(frozen=True, slots=True)
class AccountingScope:
    roots: tuple[AccountingRoot, ...]
    external_payloads: tuple[Path | str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "roots", tuple(self.roots))
        object.__setattr__(self, "external_payloads", tuple(Path(p) for p in self.external_payloads))


@dataclass(frozen=True, slots=True)
class CategoryMeasurement:
    file_count: int = 0
    logical_bytes: int = 0


@dataclass(frozen=True, slots=True)
class StorageReport:
    categories: Mapping[str, CategoryMeasurement]
    canonical_persistent_bytes: int
    hard_cap_bytes: int
    within_hard_cap: bool
    missing_optional_roots: tuple[str, ...]
    symlinks_excluded: tuple[str, ...]
    files: tuple[tuple[str, str, int], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "categories": {key: {"file_count": value.file_count,
                                 "logical_bytes": value.logical_bytes}
                           for key, value in sorted(self.categories.items())},
            "canonical_persistent_bytes": self.canonical_persistent_bytes,
            "hard_cap_bytes": self.hard_cap_bytes,
            "within_hard_cap": self.within_hard_cap,
            "missing_optional_roots": list(self.missing_optional_roots),
            "symlinks_excluded": list(self.symlinks_excluded),
            "files": [{"category": category, "path": path, "logical_bytes": size}
                      for category, path, size in self.files],
            "identity_effect": "NONE_OPERATIONAL_MEASUREMENT_ONLY",
        }


class StorageAccountingError(ValueError):
    pass


def _is_reparse_or_symlink(path: Path, st: os.stat_result | None = None) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(st, "st_file_attributes", 0) if st is not None else 0
    reparse = getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse)


def _path_key(path: Path, st: os.stat_result) -> tuple[object, ...]:
    # Device/inode deduplicates hard links where the filesystem provides it;
    # normalized resolved path is the portable fallback.
    if getattr(st, "st_ino", 0):
        return ("inode", st.st_dev, st.st_ino)
    return ("path", os.path.normcase(str(path.resolve(strict=True))))


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def account_storage(scope: AccountingScope, *, hard_cap_bytes: int = CANONICAL_HARD_CAP_BYTES
                    ) -> StorageReport:
    if hard_cap_bytes < 0:
        raise ValueError("hard cap must be non-negative")
    roots = [(root.path.expanduser().absolute(), root) for root in scope.roots]
    # Explicit directory scopes cannot overlap; this prevents hidden category
    # duplication and accidental measurement outside declared roots.
    directories = sorted((path.resolve(strict=False), root) for path, root in roots)
    for index, (path, _) in enumerate(directories):
        for other, _other_root in directories[index + 1:]:
            if _inside(path, other) or _inside(other, path):
                raise StorageAccountingError("overlapping accounting roots")

    totals = {category.value: [0, 0] for category in StorageCategory}
    missing: list[str] = []
    symlinks: list[str] = []
    accepted: dict[tuple[object, ...], tuple[str, str, int]] = {}

    def consider(path: Path, category: StorageCategory, label: str, *, strict: bool) -> None:
        try:
            lst = path.lstat()
        except FileNotFoundError:
            if strict:
                raise StorageAccountingError(f"required accounting path is missing: {label}")
            missing.append(label)
            return
        if _is_reparse_or_symlink(path, lst):
            symlinks.append(path.as_posix())
            return
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = []
            for current, dirnames, filenames in os.walk(path, topdown=True, followlinks=False):
                current_path = Path(current)
                kept_dirs = []
                for name in sorted(dirnames):
                    child = current_path / name
                    try:
                        child_stat = child.lstat()
                    except OSError:
                        continue
                    if _is_reparse_or_symlink(child, child_stat):
                        symlinks.append(child.as_posix())
                    else:
                        kept_dirs.append(name)
                dirnames[:] = kept_dirs
                for name in sorted(filenames):
                    candidates.append(current_path / name)
        else:
            raise StorageAccountingError(f"accounting path is not a regular file or directory: {label}")
        for candidate in candidates:
            try:
                st = candidate.lstat()
            except OSError as exc:
                raise StorageAccountingError(f"cannot inspect accounting file: {candidate}") from exc
            if _is_reparse_or_symlink(candidate, st):
                symlinks.append(candidate.as_posix())
                continue
            if not candidate.is_file():
                continue
            key = _path_key(candidate, st)
            relative = candidate.resolve(strict=True).as_posix()
            entry = (category.value, relative, st.st_size)
            previous = accepted.get(key)
            if previous:
                if previous[0] != category.value:
                    pair = {previous[0], category.value}
                    if pair == {StorageCategory.CANONICAL_METADATA.value,
                                StorageCategory.OPERATIONAL_METADATA.value}:
                        # Transaction journals hard-link staged records to
                        # their publication target. Count that inode once as
                        # canonical metadata; journal manifests/markers remain
                        # operational metadata.
                        if category is StorageCategory.CANONICAL_METADATA:
                            accepted[key] = entry
                        continue
                    raise StorageAccountingError("same physical file assigned to multiple categories")
                continue
            accepted[key] = entry

    for path, root in roots:
        consider(path, root.category, root.label, strict=root.required)
    for index, payload in enumerate(scope.external_payloads):
        consider(payload.expanduser().absolute(), StorageCategory.CANONICAL_PAYLOAD,
                 f"external_payload[{index}]", strict=True)

    rows = tuple(sorted(accepted.values(), key=lambda row: (row[0], row[1])))
    for category, _path, byte_count in rows:
        totals[category][0] += 1
        totals[category][1] += byte_count
    measurements = {key: CategoryMeasurement(values[0], values[1])
                    for key, values in sorted(totals.items())}
    canonical = sum(measurements[name].logical_bytes for name in
                    (StorageCategory.CANONICAL_METADATA.value,
                     StorageCategory.CANONICAL_PAYLOAD.value))
    return StorageReport(measurements, canonical, hard_cap_bytes, canonical < hard_cap_bytes,
                         tuple(sorted(missing)), tuple(sorted(set(symlinks))), rows)


def history_store_scope(store: object, *, external_payloads: Iterable[Path | str] = ()) -> AccountingScope:
    """Classify the current store's manifest/records and journals explicitly."""
    root = Path(getattr(store, "root"))
    record_buckets = ("states", "provenance", "events", "checkpoints", "temporal",
                      "refinement_branches", "refinement_recipes", "forcings", "replay_recipes")
    roots = [AccountingRoot(root / "metadata", StorageCategory.CANONICAL_METADATA,
                            required=True, label="store metadata")]
    roots.extend(AccountingRoot(root / bucket, StorageCategory.CANONICAL_METADATA,
                                required=False, label=f"store {bucket}") for bucket in record_buckets)
    roots.append(AccountingRoot(root / ".history_transactions", StorageCategory.OPERATIONAL_METADATA,
                                required=False, label="transaction journals"))
    return AccountingScope(tuple(roots), tuple(external_payloads))
