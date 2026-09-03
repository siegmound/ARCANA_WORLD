from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np


def load_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def event_signature(summary):
    rows=[]
    for e in summary.get('events',[]):
        if e.get('event') in {'speciation','deme_fission','deme_coalescence','ordinary_background_extinction'}:
            rows.append((e.get('event'), e.get('age_ma'), e.get('parent_species_id'), e.get('daughter_species_id'), e.get('parent_component_id'), e.get('daughter_component_id'), e.get('survivor_component_id')))
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run-dir', type=Path, required=True)
    ap.add_argument('--end-age-ma', type=float, default=150.0)
    args=ap.parse_args()
    tagbase=f"210_to_{str(args.end_age_ma).replace('.','p')}Ma"
    s08=load_json(args.run_dir/f'{tagbase}_q0.08_summary.json')
    s10=load_json(args.run_dir/f'{tagbase}_q0.10_summary.json')
    z08=np.load(args.run_dir/f'{tagbase}_q0.08_state.npz',allow_pickle=False)
    z10=np.load(args.run_dir/f'{tagbase}_q0.10_state.npz',allow_pickle=False)
    same_shape=z08['va'].shape==z10['va'].shape
    out={
      'status':'PASS_R3_5_DYNAMIC_SENSITIVITY_COMPARISON_COMPLETED',
      'interval':[210.0,float(args.end_age_ma)],
      'q0_08':s08['r35_headroom_summary'],
      'q0_10':s10['r35_headroom_summary'],
      'final_total_population_abs_diff':abs(float(s08['final_total_population'])-float(s10['final_total_population'])),
      'species_count':[s08['species_count'],s10['species_count']],
      'component_count':[s08['component_count'],s10['component_count']],
      'event_counts':[s08['event_counts'],s10['event_counts']],
      'species_ids_equal':s08['species_ids']==s10['species_ids'],
      'macro_event_signatures_equal':event_signature(s08)==event_signature(s10),
      'state_shapes_equal':same_shape,
      'va_max_abs_diff':float(np.max(np.abs(z08['va']-z10['va']))) if same_shape else None,
      'trait_max_abs_diff':float(np.max(np.abs(z08['trait']-z10['trait']))) if z08['trait'].shape==z10['trait'].shape else None,
      'promotion_gate': {
        'q0_10_nonbinding_full_dynamic_replay': s10['r35_headroom_summary']['steps_with_homeostasis_clipping']==0 and s10['r35_headroom_summary']['steps_with_ge_99pct_ceiling_after_homeostasis']==0,
        'q0_08_dynamic_clipping_measured': True,
        'macrohistory_stability_requires_review': True,
      }
    }
    op=args.run_dir/f'{tagbase}_dynamic_ceiling_comparison.json'
    op.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
