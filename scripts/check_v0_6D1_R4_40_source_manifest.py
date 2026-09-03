from pathlib import Path
import hashlib
import json

root = Path.cwd()
manifest = json.loads(
    (root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_40.json").read_text(
        encoding="utf-8"
    )
)
failed = []
for rec in manifest["files"]:
    p = root / rec["path"]
    if not p.exists():
        failed.append({"path": rec["path"], "reason": "MISSING"})
        continue
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != rec["sha256"]:
        failed.append({
            "path": rec["path"],
            "reason": "SHA256_MISMATCH",
            "expected": rec["sha256"],
            "actual": actual,
        })

out = {
    "stage": "v0.6D1-R4.40",
    "status":
        "PASS_R440_SOURCE_MANIFEST"
        if not failed else "BLOCKED_R440_SOURCE_MANIFEST",
    "checks_passed": len(manifest["files"]) - len(failed),
    "checks_total": len(manifest["files"]),
    "failed": failed,
}
print(json.dumps(out, indent=2))
raise SystemExit(0 if not failed else 2)
