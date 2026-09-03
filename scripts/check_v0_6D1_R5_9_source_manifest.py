from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda: f.read(1024 * 1024), b''):
            h.update(c)
    return h.hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--root', required=True); a = ap.parse_args()
    root = Path(a.root).resolve()
    m = json.loads((root / 'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_9.json').read_text(encoding='utf-8'))
    files = dict(m.get('files') or {})
    checks = {
        'stage_exact': m.get('stage') == 'v0.6D1-R5.9',
        'policy_exact': m.get('policy') == 'EXACT_SHA256_ALLOWLIST_R58_R328_AND_R59_RECONCILIATION_SOURCE',
        'file_count_exact': len(files) == int(m.get('file_count', -1)) and len(files) > 0,
    }
    for rel, expected in files.items():
        p = root / rel
        checks[f'present::{rel}'] = p.is_file()
        checks[f'sha256::{rel}'] = p.is_file() and sha(p) == expected
    failed = [k for k, v in checks.items() if not v]
    out = {
        'stage': 'v0.6D1-R5.9',
        'status': 'PASS_R59_SOURCE_MANIFEST' if not failed else 'BLOCKED_R59_SOURCE_MANIFEST',
        'checks_passed': sum(checks.values()), 'checks_total': len(checks), 'failed': failed,
    }
    print(json.dumps(out, indent=2))
    return 0 if not failed else 1

if __name__ == '__main__':
    sys.exit(main())
