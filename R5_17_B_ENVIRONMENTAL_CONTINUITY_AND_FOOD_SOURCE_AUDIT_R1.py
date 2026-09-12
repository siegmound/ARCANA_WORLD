#!/usr/bin/env python3
"""R5.17 environmental continuity audit R1.

Narrow runtime-binding repair for
R5_17_B_ENVIRONMENTAL_CONTINUITY_AND_FOOD_SOURCE_AUDIT.py.

The original audit correctly requires catalogue-backed exact hashes for B3 parents,
R3.33 and R3.34. The sealed R3.14 paleoclimate spatial snapshot, however, is a
local binding already used by R5.17-B5/B6 and is not currently represented in the
default SIMULATION_RESULTS/MANIFEST catalogue.

R1 changes no scientific semantics. It only allows the exact R3.14 SHA256 to be
resolved from the authenticated local binding when the catalogue has no matching
record. Every other SHA continues to use the original exact-one-catalogue-record
rule.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ORIGINAL = "R5_17_B_ENVIRONMENTAL_CONTINUITY_AND_FOOD_SOURCE_AUDIT.py"
R314_SHA = "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd"
R314_FILENAME = "paleoclimate_spatial_snapshots.npz"
R314_PREFERRED_RELATIVE = Path(
    "local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL/outputs/hybrid1/"
    "paleoclimate_v0_6_1/paleoclimate_spatial_snapshots.npz"
)


def load_original(repo: Path):
    path = repo / ORIGINAL
    if not path.is_file():
        raise FileNotFoundError(f"Original audit runner missing: {path}")
    spec = importlib.util.spec_from_file_location("arcana_r517_environmental_audit_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import original audit runner: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_exact_r314_local_binding(module: Any, repo: Path) -> dict[str, Any]:
    preferred = repo / R314_PREFERRED_RELATIVE
    checked: list[dict[str, Any]] = []

    def inspect(path: Path) -> dict[str, Any] | None:
        if not path.is_file():
            checked.append({"path": str(path), "exists": False, "sha256": None})
            return None
        digest = module.sha256_file(path)
        checked.append({"path": str(path.resolve()), "exists": True, "sha256": digest})
        if digest.lower() == R314_SHA:
            return {
                "path": str(path.resolve()),
                "sha256": digest,
                "filename": path.name,
                "stage": "v0_6D1_R3_14",
                "authority_status": "EXACT_LOCAL_BINDING_HASH_VERIFIED",
                "semantic_status": "SEALED_R314_SPATIAL_SNAPSHOT_BINDING",
                "semantic_class": "PALEOCLIMATE_SPATIAL_SNAPSHOTS",
                "primary_use": "R5.17 exact paleoclimate/NPP temporal modulation source binding",
                "forbidden_interpretations": (
                    "not physical human population; not K(x,t); not direct human food support"
                ),
                "binding_source": "LOCAL_BINDINGS_FALLBACK_EXACT_SHA256",
                "catalogue_record_present": False,
                "preferred_path": True,
                "checked_candidates": checked,
            }
        return None

    exact = inspect(preferred)
    if exact is not None:
        return exact

    candidates: list[Path] = []
    for path in repo.rglob(R314_FILENAME):
        text = str(path).lower()
        if any(token in text for token in (".pytest_tmp", "__pycache__")):
            continue
        if path.resolve() == preferred.resolve():
            continue
        candidates.append(path)

    matches: list[dict[str, Any]] = []
    for path in sorted(candidates):
        if not path.is_file():
            continue
        digest = module.sha256_file(path)
        checked.append({"path": str(path.resolve()), "exists": True, "sha256": digest})
        if digest.lower() == R314_SHA:
            matches.append({
                "path": str(path.resolve()),
                "sha256": digest,
                "filename": path.name,
                "stage": "v0_6D1_R3_14",
                "authority_status": "EXACT_LOCAL_BINDING_HASH_VERIFIED",
                "semantic_status": "SEALED_R314_SPATIAL_SNAPSHOT_BINDING",
                "semantic_class": "PALEOCLIMATE_SPATIAL_SNAPSHOTS",
                "primary_use": "R5.17 exact paleoclimate/NPP temporal modulation source binding",
                "forbidden_interpretations": (
                    "not physical human population; not K(x,t); not direct human food support"
                ),
                "binding_source": "LOCAL_BINDINGS_FALLBACK_EXACT_SHA256",
                "catalogue_record_present": False,
                "preferred_path": False,
            })

    if len(matches) != 1:
        raise RuntimeError(
            "R3.14 catalogue record absent and exact local-binding resolution did not "
            f"produce exactly one fallback match; matches={len(matches)}; checked={checked}"
        )

    matches[0]["checked_candidates"] = checked
    return matches[0]


def main() -> int:
    # The base runner's argparse handles --repo/--output. Resolve repo here only for
    # the narrow fallback binding. This deliberately mirrors its default semantics.
    repo = Path.cwd().resolve()
    if "--repo" in sys.argv:
        idx = sys.argv.index("--repo")
        if idx + 1 >= len(sys.argv):
            raise RuntimeError("--repo supplied without a value")
        repo = Path(sys.argv[idx + 1]).resolve()

    module = load_original(repo)
    original_find = module.find_unique_by_sha
    original_verify = module.verify_manifest_record

    def patched_find(records: list[dict[str, Any]], digest: str) -> dict[str, Any]:
        matches = [
            record
            for record in records
            if str(record.get("SHA256", "")).lower() == digest.lower()
        ]

        # Preserve the original exact-one rule whenever the catalogue actually has
        # a record, including for R3.14 if it is catalogued in a future revision.
        if len(matches) == 1:
            return matches[0]

        if digest.lower() == R314_SHA and len(matches) == 0:
            return {
                "__arcana_direct_r314_binding__": True,
                "SHA256": R314_SHA,
                "FileName": R314_FILENAME,
            }

        # All non-R3.14 cases retain the original strict behaviour.
        return original_find(records, digest)

    def patched_verify(repo_arg: Path, record: dict[str, Any]) -> dict[str, Any]:
        if record.get("__arcana_direct_r314_binding__"):
            return find_exact_r314_local_binding(module, repo_arg)
        return original_verify(repo_arg, record)

    module.find_unique_by_sha = patched_find
    module.verify_manifest_record = patched_verify

    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
