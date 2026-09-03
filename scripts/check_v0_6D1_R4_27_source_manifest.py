from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
manifest=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_27.json'
if not manifest.exists():
    print(json.dumps({'stage':'v0.6D1-R4.27','status':'BLOCKED_R427_SOURCE_MANIFEST_MISSING','checks_passed':0,'checks_total':0,'failed':['manifest missing']},indent=2)); raise SystemExit(3)
o=json.loads(manifest.read_text(encoding='utf-8-sig'))
failed=[]
for rec in o.get('files',[]):
    p=root/rec['path']
    if not p.exists(): failed.append({'path':rec['path'],'reason':'MISSING'}); continue
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=rec.get('sha256') or p.stat().st_size!=rec.get('bytes'):
        failed.append({'path':rec['path'],'reason':'HASH_OR_SIZE_MISMATCH','expected_sha256':rec.get('sha256'),'observed_sha256':h,'expected_bytes':rec.get('bytes'),'observed_bytes':p.stat().st_size})
status='PASS_R427_SOURCE_MANIFEST' if not failed else 'BLOCKED_R427_SOURCE_MANIFEST_DRIFT'
print(json.dumps({'stage':'v0.6D1-R4.27','status':status,'checks_passed':len(o.get('files',[]))-len(failed),'checks_total':len(o.get('files',[])),'failed':failed},indent=2))
raise SystemExit(0 if not failed else 3)
