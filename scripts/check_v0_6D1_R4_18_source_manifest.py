from pathlib import Path
import json
root=Path('.'); m=root/'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_18.json'; d=json.loads(m.read_text(encoding='utf-8-sig')); failed=[r for r in d['required_paths'] if not (root/r).exists()]; o={'stage':'v0.6D1-R4.18','status':'PASS_R418_SOURCE_MANIFEST' if not failed else 'BLOCKED_R418_SOURCE_MANIFEST','checks_passed':len(d['required_paths'])-len(failed),'checks_total':len(d['required_paths']),'failed':failed};print(json.dumps(o,indent=2));raise SystemExit(0 if not failed else 1)
