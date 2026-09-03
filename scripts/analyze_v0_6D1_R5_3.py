from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r53_demography import analyze_cdmetapop_evidence

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--allow-non-scientific-dev-parent',action='store_true'); a=ap.parse_args()
    r=analyze_cdmetapop_evidence(a.root,a.allow_non_scientific_dev_parent); audit=r['audit']; print(json.dumps(audit,indent=2))
    if audit['failed']:
        print('BLOCKED_R53_CDMETAPOP_DEMOGRAPHIC_EVIDENCE_RUN'); raise SystemExit(3)
    if audit['scientific_candidate_eligible']:
        print('PASS_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_EVIDENCE_CANDIDATE_RUN')
    else: print('PASS_R53_NON_SCIENTIFIC_DEV_EVIDENCE_VALIDATION_RUN')
if __name__=='__main__': main()
