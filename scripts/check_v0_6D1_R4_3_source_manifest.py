from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
manifest_path = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_3.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
failed = []
for row in manifest["files"]:
    p = root / row["path"]
    if not p.exists():
        failed.append({"path": row["path"], "error": "MISSING"})
        continue
    observed = hashlib.sha256(p.read_bytes()).hexdigest()
    if observed != row["sha256"]:
        failed.append({"path": row["path"], "error": "SHA256_MISMATCH", "expected": row["sha256"], "observed": observed})
out = {
    "stage": "v0.6D1-R4.3",
    "status": "PASS_R43_SOURCE_MANIFEST" if not failed else "FAIL_R43_SOURCE_MANIFEST",
    "checks_passed": len(manifest["files"]) - len(failed),
    "checks_total": len(manifest["files"]),
    "failed": failed,
}
print(json.dumps(out, indent=2))
raise SystemExit(0 if not failed else 2)
