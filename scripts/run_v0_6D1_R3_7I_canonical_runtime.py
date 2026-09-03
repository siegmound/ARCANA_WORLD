from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r37i_production_runtime import R37IProductionConfig, run_canonical_production


def load_inputs():
    common=np.load(ROOT/'outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz',allow_pickle=False)
    a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
    md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8'))
    rows=md['species'] if isinstance(md,dict) and 'species' in md else md
    return common,a1,rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seal',type=Path,default=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json')
    ap.add_argument('--end-age-ma',type=float,default=150.0)
    ap.add_argument('--diagnostic-smoke',action='store_true')
    ap.add_argument('--out-dir',type=Path,default=ROOT/'local_runs/v0_6D1_R3_7I')
    args=ap.parse_args()
    cfg=R37IProductionConfig(end_age_ma=args.end_age_ma,diagnostic_smoke=args.diagnostic_smoke)
    common,a1,rows=load_inputs()
    t0=time.time(); out=run_canonical_production(common,a1,rows,cfg,args.seal); out['wall_seconds']=time.time()-t0
    args.out_dir.mkdir(parents=True,exist_ok=True)
    p=args.out_dir/f"210_to_{str(args.end_age_ma).replace('.','p')}Ma_R3_7I_canonical.json"
    p.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps({
        'stage':out['stage'],'canonical_runtime_binding':out['canonical_runtime_binding'],
        'biology_steps':out['biology_steps'],'peak_q':out['peak_q'],'clipping_contacts':out['clipping_contacts'],
        'final_total_population':out['final_total_population'],'species_count':out['species_count'],
        'component_count':out['component_count'],'event_counts':out['event_counts'],
        'wall_seconds':out['wall_seconds'],'result':str(p),
    },indent=2))

if __name__=='__main__': main()
