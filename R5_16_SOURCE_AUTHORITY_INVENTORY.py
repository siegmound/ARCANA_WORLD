from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


OUTPUT_PATH = "R5_16_SOURCE_AUTHORITY_INVENTORY.json"

EXPECTED_BRANCH = "main"
STAGES = tuple(range(8, 16))

SUPPORTING_AUTHORITIES = (
    "ARCANA_WORLD_CURRENT_STATE.md",
    "R5_16_INTEGRATED_END_OF_LEGACY_SEAL_REVIEW_CONTRACT.md",
)


def git_bytes(*args: str) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"git {' '.join(args)} failed:\n"
            f"{proc.stderr.decode('utf-8', errors='replace')}"
        )
    return proc.stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8", errors="replace").strip()


def repo_root() -> Path:
    return Path(git_text("rev-parse", "--show-toplevel")).resolve()


def tracked_entries() -> list[dict]:
    """
    Return committed/index Git entries without reading artifact contents.

    git_blob_oid is the repository-bound blob identity, so even large
    artifacts do not have to be loaded or re-hashed by this inventory step.
    """
    raw = git_bytes("ls-files", "-s", "-z")

    entries: list[dict] = []

    for record in raw.split(b"\0"):
        if not record:
            continue

        try:
            meta, raw_path = record.split(b"\t", 1)
            mode, oid, index_stage = meta.split()
        except ValueError as exc:
            raise SystemExit(
                f"Unexpected git ls-files record: {record!r}"
            ) from exc

        path = raw_path.decode("utf-8", errors="surrogateescape")
        fs_path = Path(path)

        entries.append(
            {
                "path": path,
                "git_mode": mode.decode("ascii"),
                "git_blob_oid": oid.decode("ascii"),
                "git_index_stage": int(index_stage),
                "size_bytes": fs_path.stat().st_size if fs_path.exists() else None,
            }
        )

    entries.sort(key=lambda item: item["path"])
    return entries


def stage_pattern(stage_number: int) -> re.Pattern[str]:
    # Accept normal repository variants such as:
    # R5_8
    # R5-8
    # R5.8
    # R5_08
    return re.compile(
        rf"R5[_\-.]0?{stage_number}(?=[_\-./]|$)",
        flags=re.IGNORECASE,
    )


def main() -> None:
    root = repo_root()
    os.chdir(root)

    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise SystemExit(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    # Ignore untracked files so this script/output may exist locally,
    # but reject modifications to already tracked evidence.
    tracked_dirty = git_text(
        "status",
        "--porcelain",
        "--untracked-files=no",
    )

    if tracked_dirty:
        raise SystemExit(
            "Tracked working tree is not clean.\n"
            "Commit/stash tracked modifications before generating the inventory:\n"
            f"{tracked_dirty}"
        )

    source_commit = git_text("rev-parse", "HEAD")
    entries = tracked_entries()

    by_path = {entry["path"]: entry for entry in entries}

    stage_files: dict[str, list[dict]] = {}

    for number in STAGES:
        canonical_stage = f"v0.6D1-R5.{number}"
        pattern = stage_pattern(number)

        matches = [
            entry
            for entry in entries
            if pattern.search(entry["path"])
        ]

        stage_files[canonical_stage] = matches

    supporting_authorities = []

    for path in SUPPORTING_AUTHORITIES:
        entry = by_path.get(path)

        supporting_authorities.append(
            {
                "path": path,
                "tracked": entry is not None,
                "git_blob_oid": (
                    entry["git_blob_oid"] if entry is not None else None
                ),
                "size_bytes": (
                    entry["size_bytes"] if entry is not None else None
                ),
            }
        )

    missing_stage_file_groups = [
        stage
        for stage, files in stage_files.items()
        if not files
    ]

    result = {
        "schema": "ARCANA_R5_16_SOURCE_AUTHORITY_INVENTORY_V1",
        "stage": "v0.6D1-R5.16",
        "subphase": "R5.16-A1",
        "purpose": "repository-bound source-authority inventory only",
        "repository": "siegmound/ARCANA_WORLD",
        "branch": branch,
        "source_commit": source_commit,
        "scope": {
            "first_stage": "v0.6D1-R5.8",
            "last_stage": "v0.6D1-R5.15",
            "stage_count": len(STAGES),
        },
        "method": {
            "source": "git ls-files -s",
            "identity": "git_blob_oid",
            "file_content_interpretation": False,
            "scientific_adjudication": False,
            "provenance_adjudication": False,
            "automatic_repair": False,
            "canonical_mutation": False,
            "seal_action": False,
        },
        "supporting_authorities": supporting_authorities,
        "stage_file_counts": {
            stage: len(files)
            for stage, files in stage_files.items()
        },
        "stage_files": stage_files,
        "missing_stage_file_groups": missing_stage_file_groups,
        "status": "INVENTORY_ONLY_NO_ADJUDICATION",
    }

    Path(OUTPUT_PATH).write_text(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"WROTE {OUTPUT_PATH}")
    print(f"SOURCE_COMMIT = {source_commit}")

    for stage, files in stage_files.items():
        print(f"{stage}: {len(files)} tracked files")

    if missing_stage_file_groups:
        print(
            "WARNING: no stage-named tracked files found for: "
            + ", ".join(missing_stage_file_groups)
        )

    print("STATUS = INVENTORY_ONLY_NO_ADJUDICATION")


if __name__ == "__main__":
    main()