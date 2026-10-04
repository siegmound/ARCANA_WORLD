"""Validate and hash retained B6L qualification artifacts."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/r6_b6l_candidate_query_publication_readiness"
MANIFEST = OUT / "B6L_ARTIFACT_MANIFEST.json"


def main() -> int:
    for path in sorted(OUT.rglob("*.json")):
        if path != MANIFEST:
            json.loads(path.read_text(encoding="utf-8"))
    result = json.loads((OUT / "B6L_RESULT.json").read_text(encoding="utf-8"))
    if result["reproduced_candidate_payload_sha256"] != \
            "9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a":
        raise ValueError("replayed candidate payload SHA differs from B6K")
    rows = []
    selected = {path.resolve() for path in OUT.rglob("*") if path.is_file()
                and path != MANIFEST}
    selected.update((ROOT / item).resolve() for item in (
        "scripts/r6_b6l_candidate_query_publication_readiness.py",
        "scripts/r6_b6l_validate_evidence.py",
        "src/arcana_worldsim/r6/b6l_readiness.py",
        "tests/test_r6_b6l_candidate_query_publication_readiness.py",
        "docs/arcana/B6L_CANDIDATE_QUERY_PUBLICATION_READINESS.md",
    ))
    selected.update((ROOT / item).resolve() for item in (
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_RESULT.json",
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_ARTIFACT_MANIFEST.json",
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_CANDIDATE_PLATE_LOCAL_COORDINATES.bin",
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_BOUNDARY_CANDIDATE.json",
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_JUNCTION_CANDIDATE.json",
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_STATE_TRANSFER.json",
        "outputs/r6_b6k_isolated_first_candidate_state/B6K_ASYNC_DOMAIN_STATE.json",
        "outputs/r6_b6d_authorial_mvp_model_freeze/B6D_RESULT.json",
        "outputs/r6_b6i_first_segment_topology_model_extension/B6I_TOPOLOGY_PROCESS_REGISTRY.json",
        "outputs/r6_b6j_first_dt_adjudication/B6J_DT_SELECTION.json",
        "outputs/r6_b6j_first_dt_adjudication/B6J_ENDPOINT_POLICY.json",
    ))
    portable_paths = []
    for path in sorted(selected, key=lambda item: item.relative_to(ROOT).as_posix()):
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"missing or unsafe B6L artifact: {path}")
        data = path.read_bytes()
        if path.suffix.lower() in {".json", ".md"}:
            text = data.decode("utf-8")
            if (re.search(r"(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]", text)
                    or "C:/Users/" in text or "jose_" in text):
                raise ValueError(f"machine-specific path in {path.relative_to(ROOT)}")
            portable_paths.append(path)
        rows.append({"relative_path": path.relative_to(ROOT).as_posix(),
            "byte_size": len(data), "sha256": sha256(data).hexdigest(),
            "role": "B6L qualification artifact or immutable B6K/B6D/B6I/B6J input"})
    body = {"schema": "R6_B6L_ARTIFACT_MANIFEST_V1", "hash_algorithm": "SHA256",
        "self_hashed": False, "artifacts": rows}
    MANIFEST.write_text(json.dumps(body, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    verified = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for row in verified["artifacts"]:
        path = (ROOT / row["relative_path"]).resolve()
        data = path.read_bytes()
        if len(data) != row["byte_size"] or sha256(data).hexdigest() != row["sha256"]:
            raise ValueError(f"B6L artifact manifest mismatch: {row['relative_path']}")
    print(json.dumps({"result": "PASS", "manifest_entries": len(rows),
        "portable_text_files": len(portable_paths),
        "manifest_sha256": sha256(MANIFEST.read_bytes()).hexdigest()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
