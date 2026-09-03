from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines.r37c_validation import analyze_r37c_selection_evidence

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('raw_results_zip',type=Path); ap.add_argument('--out',type=Path,default=None); a=ap.parse_args()
    out=analyze_r37c_selection_evidence(a.raw_results_zip)
    dst=a.out or a.raw_results_zip.with_name('R3_7C_SELECTION_EVIDENCE_ANALYSIS.json')
    dst.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'stage':out['stage'],'verdict':out['verdict'],'observation_count':out['observation_count'],'K_eff':out['K_eff']},indent=2))
    return 0 if out['verdict'].startswith('PASS_') else 2
if __name__=='__main__': raise SystemExit(main())
