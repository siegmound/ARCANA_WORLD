from pathlib import Path
import hashlib,json
root=Path.cwd()
m=json.loads((root/"SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_54.json").read_text())
failed=[]
for rec in m["files"]:
 p=root/rec["path"]
 if not p.exists():
  failed.append({"path":rec["path"],"reason":"MISSING"}); continue
 a=hashlib.sha256(p.read_bytes()).hexdigest()
 if a!=rec["sha256"]:
  failed.append({"path":rec["path"],"reason":"SHA256_MISMATCH","expected":rec["sha256"],"actual":a})
out={"stage":"v0.6D1-R4.54","status":"PASS_R454_SOURCE_MANIFEST" if not failed else "BLOCKED_R454_SOURCE_MANIFEST","checks_passed":len(m["files"])-len(failed),"checks_total":len(m["files"]),"failed":failed}
print(json.dumps(out,indent=2))
raise SystemExit(0 if not failed else 2)
