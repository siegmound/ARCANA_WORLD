from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r53_demography import prepare_demographic_challenges

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); a=ap.parse_args()
    r=prepare_demographic_challenges(a.root,a.allow_non_scientific_dev_parent)
    p=r['plan']; print(json.dumps({'stage':p['stage'],'status':p['status'],'scientific_parent_mode':p['scientific_parent_mode'],'robust_family_count':p['robust_family_count'],'group_count':p['group_count'],'planned_stream_count':p['planned_stream_count'],'stress_profiles':list(p['stress_profiles']),'seeds':p['seeds'],'plan_sha256':r['plan_sha256']},indent=2))
    print('PASS_R53_CDMETAPOP_DEMOGRAPHIC_CHALLENGE_PLAN_PREPARED')
if __name__=='__main__': main()
