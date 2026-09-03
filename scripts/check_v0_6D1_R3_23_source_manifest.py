from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_23.json'
if not P.is_file():
    print('FAIL_R323_SOURCE_MANIFEST_MISSING'); raise SystemExit(1)
data=json.loads(P.read_text(encoding='utf-8'))
failed=[]
for rel, meta in data['files'].items():
    fp=ROOT/rel
    if not fp.is_file(): failed.append((rel,'missing')); continue
    h=hashlib.sha256(fp.read_bytes()).hexdigest()
    if h != meta['sha256'] or fp.stat().st_size != meta['bytes']:
        failed.append((rel,'hash_or_size'))
if failed:
    print(json.dumps({'status':'FAIL_R323_SOURCE_MANIFEST','failed':failed}, indent=2)); raise SystemExit(1)
print(json.dumps({'status':'PASS_R323_SOURCE_MANIFEST','checks_passed':len(data['files']),'checks_total':len(data['files'])}, indent=2))
