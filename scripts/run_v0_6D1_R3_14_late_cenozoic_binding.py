from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
if str(ROOT / "src") not in sys.path: sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines import r314_late_cenozoic_binding as r314

p=argparse.ArgumentParser()
p.add_argument('--root', default=str(ROOT))
p.add_argument('--search-root', action='append', default=[])
a=p.parse_args()
root=Path(a.root).resolve()
search=[Path(x).resolve() for x in a.search_root]
if not search:
    # Current package root, ArcanaWorld folder, and one level above it.
    search=[root, root.parent]
    if root.parent.parent != root.parent: search.append(root.parent.parent)
res=r314.run_binding(root, search)
print(json.dumps({
    'stage':res['stage'],'verdict':res['verdict'],'biology_advanced':res.get('biology_advanced',res.get('governance',{}).get('biology_advanced')),
    'discovery':None if 'discovery' not in res else {'kind':res['discovery'].get('kind'),'source':res['discovery'].get('source'),'rehydrated_to':res['discovery'].get('rehydrated_to')},
    'binding_30ma':res.get('binding_30ma'),
    'adaptive_clock':res.get('adaptive_clock'),
    'summary':res.get('summary_path'),'blocker_report':res.get('blocker_report')
},indent=2))
if res['verdict'].startswith('BLOCKED_'):
    sys.exit(2)
