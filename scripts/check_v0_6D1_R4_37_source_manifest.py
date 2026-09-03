from pathlib import Path
import hashlib,json
root=Path.cwd()
m=json.loads((root/"SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_37.json").read_text(encoding="utf-8"))
failed=[]
for r in m.get("files",[]):
    p=root/r["path"]
    if not p.exists():
        failed.append({"path":r["path"],"reason":"MISSING"}); continue
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=r["sha256"]:
        failed.append({"path":r["path"],"reason":"SHA256_MISMATCH","expected":r["sha256"],"actual":h})
out={"stage":"v0.6D1-R4.37",
     "status":"PASS_R437_SOURCE_MANIFEST" if not failed else "BLOCKED_R437_SOURCE_MANIFEST",
     "checks_passed":len(m.get("files",[]))-len(failed),
     "checks_total":len(m.get("files",[])),"failed":failed}
print(json.dumps(out,indent=2))
raise SystemExit(0 if not failed else 2)
