from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[1]
manifest_path = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_0.json"
m = json.loads(manifest_path.read_text(encoding="utf-8"))
failed = []
checks_total = 0
checks_passed = 0

for group in ("files", "immutable_parent_artifacts"):
    for rel, meta in m[group].items():
        checks_total += 1
        p = root / rel
        if not p.is_file():
            failed.append([group, rel, "missing"])
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if p.stat().st_size != int(meta["bytes"]) or h != meta["sha256"]:
            failed.append([group, rel, "mismatch", h])
            continue
        checks_passed += 1

print(json.dumps({
    "stage": m["stage"],
    "status": "PASS_R50_SOURCE_AND_PARENT_MANIFEST" if not failed else "FAIL_R50_SOURCE_AND_PARENT_MANIFEST",
    "checks_passed": checks_passed,
    "checks_total": checks_total,
    "failed": failed,
    "r456_runtime_authority": m["r456_runtime_authority"],
}, indent=2))
sys.exit(1 if failed else 0)
