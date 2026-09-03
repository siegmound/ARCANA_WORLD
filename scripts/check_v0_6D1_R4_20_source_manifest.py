from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve(); mp=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_20.json'; m=json.loads(mp.read_text(encoding='utf-8-sig')); failed=[]
for rec in m['files']:
 p=root/rec['path']
 if not p.exists(): failed.append({'path':rec['path'],'reason':'MISSING'});continue
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if h!=rec['sha256']: failed.append({'path':rec['path'],'reason':'SHA256_MISMATCH','expected':rec['sha256'],'actual':h})
o={'stage':'v0.6D1-R4.20','status':'PASS_R420_SOURCE_MANIFEST' if not failed else 'BLOCKED_R420_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed};print(json.dumps(o,indent=2));raise SystemExit(0 if not failed else 1)
