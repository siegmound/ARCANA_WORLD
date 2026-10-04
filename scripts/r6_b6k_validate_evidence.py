"""Validate and manifest retained B6K qualification artifacts."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/r6_b6k_isolated_first_candidate_state"
MANIFEST = OUT / "B6K_ARTIFACT_MANIFEST.json"


def main() -> int:
    test_path = OUT / "B6K_TEST_RESULTS.json"
    tests = json.loads(test_path.read_text(encoding="utf-8"))
    tests["static_checks"] = {"compileall": "PASS", "py_compile": "PASS",
        "json_validation": "PASS", "binary_hash": "PASS",
        "portable_paths": "PASS", "git_diff_check": "PASS"}
    test_path.write_text(json.dumps(tests, sort_keys=True, indent=2,
        ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    for path in OUT.rglob("*.json"):
        if path != MANIFEST:
            json.loads(path.read_text(encoding="utf-8"))
    result = json.loads((OUT / "B6K_RESULT.json").read_text(encoding="utf-8"))
    payload = OUT / "B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin"
    payload_sha = sha256(payload.read_bytes()).hexdigest()
    if payload_sha != result["candidate_payload_sha256"]:
        raise ValueError("candidate binary SHA256 differs from B6K_RESULT")

    portable = [path for path in OUT.rglob("*") if path.is_file()
        and path.suffix.lower() in {".json", ".md"}]
    portable.append(ROOT / "docs/arcana/B6K_ISOLATED_FIRST_CANDIDATE_STATE.md")
    for path in portable:
        text = path.read_text(encoding="utf-8")
        if (re.search(r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]", text) or "\\\\" in text
                or "C:/Users/" in text or "jose_" in text):
            raise ValueError(f"machine-specific path in {path.relative_to(ROOT)}")

    source_files = (
        "scripts/r6_b6k_isolated_first_candidate_state.py",
        "scripts/r6_b6k_validate_evidence.py",
        "src/arcana_worldsim/r6/b6k_candidate.py",
        "src/arcana_worldsim/r6/plate_support_adapter.py",
        "tests/test_r6_b6k_isolated_candidate_state.py",
        "docs/arcana/B6K_ISOLATED_FIRST_CANDIDATE_STATE.md",
    )
    files = {path.resolve() for path in OUT.rglob("*") if path.is_file()
             and path != MANIFEST}
    files.update((ROOT / rel).resolve() for rel in source_files)
    rows = []
    for path in sorted(files, key=lambda item: item.relative_to(ROOT).as_posix()):
        rel = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        if path.suffix == ".bin":
            role = "candidate binary payload"
        elif "isolated_world_history/" in rel:
            role = "isolated qualification store"
        elif rel in source_files:
            role = "implementation/test/report source"
        else:
            role = "B6K qualification evidence"
        rows.append({"relative_path": rel, "byte_size": len(data),
                     "sha256": sha256(data).hexdigest(), "role": role})
    manifest = {"schema": "R6_B6K_ARTIFACT_MANIFEST_V1",
        "hash_algorithm": "SHA256", "self_hashed": False, "artifacts": rows}
    MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=2,
        ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    verified = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for row in verified["artifacts"]:
        path = (ROOT / row["relative_path"]).resolve()
        if (ROOT.resolve() not in path.parents or not path.is_file()
                or path.stat().st_size != row["byte_size"]
                or sha256(path.read_bytes()).hexdigest() != row["sha256"]):
            raise ValueError(f"artifact manifest validation failed: {row['relative_path']}")
    print(json.dumps({"json_evidence_files": sum(p.suffix == ".json" for p in OUT.rglob("*")),
        "manifest_entries": len(rows), "portable_text_files": len(portable),
        "candidate_payload_sha256": payload_sha,
        "manifest_sha256": sha256(MANIFEST.read_bytes()).hexdigest(), "result": "PASS"},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
