from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    mp = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_7.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    checks = {}
    checks["stage_exact"] = m.get("stage") == "v0.6D1-R5.7"
    checks["policy_exact"] = m.get("policy") == "EXACT_SHA256_ALLOWLIST_R53_R56_BLOCK_AND_R57_CLOSURE_SOURCE"
    files = dict(m.get("files") or {})
    checks["file_count_exact"] = len(files) == int(m.get("file_count", -1)) and len(files) > 0
    for rel, expected in files.items():
        p = root / rel
        checks[f"present::{rel}"] = p.is_file()
        checks[f"sha256::{rel}"] = p.is_file() and sha256_file(p) == expected
    failed = [k for k,v in checks.items() if not v]
    out = {
        "stage": "v0.6D1-R5.7",
        "status": "PASS_R57_SOURCE_MANIFEST" if not failed else "BLOCKED_R57_SOURCE_MANIFEST",
        "checks_passed": sum(bool(v) for v in checks.values()),
        "checks_total": len(checks),
        "failed": failed,
    }
    print(json.dumps(out, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
