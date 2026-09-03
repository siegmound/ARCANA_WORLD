from pathlib import Path
import argparse, hashlib, json
p=argparse.ArgumentParser(); p.add_argument('root',nargs='?',default='.'); a=p.parse_args(); root=Path(a.root).resolve()
m=json.loads((root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_26.json').read_text(encoding='utf-8-sig')); failed=[]
for r in m['files']:
    f=root/r['path']
    if not f.exists(): failed.append({'path':r['path'],'reason':'missing'}); continue
    h=hashlib.sha256(f.read_bytes()).hexdigest()
    if h!=r['sha256']: failed.append({'path':r['path'],'reason':'sha256','expected':r['sha256'],'observed':h})
out={'stage':'v0.6D1-R4.26','status':'PASS_R426_SOURCE_MANIFEST' if not failed else 'BLOCKED_R426_SOURCE_MANIFEST','checks_passed':len(m['files'])-len(failed),'checks_total':len(m['files']),'failed':failed}
print(json.dumps(out,indent=2)); raise SystemExit(0 if not failed else 2)
