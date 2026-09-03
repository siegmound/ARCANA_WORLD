from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines.r37b_validation import analyze_r37a_b2_neutral_closure

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('raw_zip',type=Path)
    ap.add_argument('output_json',type=Path)
    a=ap.parse_args()
    out=analyze_r37a_b2_neutral_closure(a.raw_zip)
    a.output_json.parent.mkdir(parents=True,exist_ok=True)
    a.output_json.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:out[k] for k in ('stage','verdict','phase_observation_count','S_observed_over_predicted','VA_fractional_error')},indent=2))
    return 0 if out['verdict'].startswith('PASS_') else 2
if __name__=='__main__': raise SystemExit(main())
