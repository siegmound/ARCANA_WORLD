from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r52_corridors import prepare_corridor_inputs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); args=ap.parse_args()
    r=prepare_corridor_inputs(args.root,args.allow_non_scientific_dev_parent)
    p=r['plan']
    summary={
      "stage":p['stage'],"status":p['status'],"scientific_parent_mode":p['scientific_parent_mode'],
      "robust_family_count":p['robust_family_count'],"group_count":p['group_count'],
      "executable_group_count":p['executable_group_count'],"nonexecutable_group_count":p['nonexecutable_group_count'],
      "planned_stream_count":p['planned_stream_count'],"habitat_profiles":p['habitat_profiles'],
      "movement_profiles":p['movement_profiles'],"seeds":p['seeds'],"plan_sha256":r['plan_sha256']
    }
    print(json.dumps(summary,indent=2))
    print('PASS_R52_TARGETED_CORRIDOR_EXECUTION_PLAN_PREPARED')
if __name__=='__main__': main()
