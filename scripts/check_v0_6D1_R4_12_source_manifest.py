from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];doc=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_12.json').read_text(encoding='utf-8'));failed=[]
for row in doc['files']:
 p=root/row['path'];ok=p.exists()
 if ok and row.get('sha256'):ok=hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
 if not ok:failed.append(row['path'])
out={'stage':'v0.6D1-R4.12','status':'PASS_R412_SOURCE_MANIFEST' if not failed else 'BLOCKED_R412_SOURCE_MANIFEST','checks_passed':len(doc['files'])-len(failed),'checks_total':len(doc['files']),'failed':failed};print(json.dumps(out,indent=2));raise SystemExit(0 if not failed else 3)
