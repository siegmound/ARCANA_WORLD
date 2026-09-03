from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r56_slim_ancestry import prepare_ancestry_challenges, sha256_file, OUT_REL

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); a=ap.parse_args()
    plan=prepare_ancestry_challenges(a.root.resolve(),allow_non_scientific_dev_parent=a.allow_non_scientific_dev_parent)
    p=a.root.resolve()/OUT_REL/'R5_6_SLIM_EXECUTION_PLAN.json'
    print(json.dumps({'stage':'v0.6D1-R5.6','status':plan['status'],'pair_count':plan['pair_count'],'schedule_class_count':plan['schedule_class_count'],'planned_stream_count':plan['planned_stream_count'],'variants':plan['variant_count'],'seeds':plan['seeds'],'plan_sha256':sha256_file(p)},indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
