from pathlib import Path
import hashlib
import json
import sys

root = Path.cwd()
mf = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_33.json"
data = json.loads(mf.read_text(encoding="utf-8"))
failed = []
for rec in data.get("files", []):
    p = root / rec["path"]
    if not p.exists():
        failed.append({"path": rec["path"], "reason": "MISSING"})
        continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != rec["sha256"]:
        failed.append({
            "path": rec["path"],
            "reason": "SHA256_MISMATCH",
            "expected": rec["sha256"],
            "actual": h,
        })
out = {
    "stage": "v0.6D1-R4.33",
    "status": "PASS_R433_SOURCE_MANIFEST" if not failed else "BLOCKED_R433_SOURCE_MANIFEST",
    "checks_passed": len(data.get("files", [])) - len(failed),
    "checks_total": len(data.get("files", [])),
    "failed": failed,
}
print(json.dumps(out, indent=2))
raise SystemExit(0 if not failed else 2)
