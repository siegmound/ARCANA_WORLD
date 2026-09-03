from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from rebased_natural_control_runtime_v0_6D1_R3_5 import R35Config, run


def write_jsonl(path: Path, rows):
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, separators=(',', ':'), sort_keys=True) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--end-age-ma', type=float, default=150.0)
    ap.add_argument('--ceiling', type=float, default=0.08, choices=[0.08, 0.10])
    ap.add_argument('--out-dir', type=Path, default=ROOT / 'local_runs/v0_6D1_R3_5')
    ap.add_argument('--threads', type=int, default=0)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    common = np.load(ROOT / 'outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz', allow_pickle=False)
    a1 = np.load(ROOT / 'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz', allow_pickle=False)
    md = json.loads((ROOT / 'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8'))
    rows = md['species'] if isinstance(md, dict) and 'species' in md else md

    cfg = R35Config(end_age_ma=float(args.end_age_ma), variance_ceiling_normalized=float(args.ceiling))
    t0 = time.time()
    r = run(common, a1, rows, cfg)
    wall = time.time() - t0

    ec = {}
    for e in r['events']:
        ec[e['event']] = ec.get(e['event'], 0) + 1
    tag = f"210_to_{str(args.end_age_ma).replace('.','p')}Ma_q{args.ceiling:.2f}"
    summary_path = args.out_dir / f'{tag}_summary.json'
    state_path = args.out_dir / f'{tag}_state.npz'
    telemetry_path = args.out_dir / f'{tag}_va_telemetry.jsonl'
    telemetry_summary_path = args.out_dir / f'{tag}_va_headroom_summary.json'

    summary = {k: r[k] for k in [
        'stage','config','initial_total_population','final_total_population','species_ids',
        'events','snapshots','registry','gate_diagnostics','gene_flow_closure',
        'topology_remap_mass','barrier_history','authority'
    ]}
    summary.update({
        'species_count': len(r['species_ids']),
        'component_count': len(r['component_ids']),
        'event_counts': ec,
        'wall_seconds': wall,
        'r35_headroom_summary': r['r35_headroom_summary'],
        'telemetry_file': telemetry_path.name,
    })
    summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    write_jsonl(telemetry_path, r['r35_telemetry'])
    telemetry_summary_path.write_text(json.dumps(r['r35_headroom_summary'], indent=2), encoding='utf-8')
    np.savez_compressed(
        state_path,
        population=r['population'], trait=r['trait'], va=r['va'], generation_time=r['generation_time'],
        ri=r['ri'], clock=r['clock'], contact=r['contact'], trait_distance=r['trait_distance'],
        component_guild=r['component_guild'],
        component_ids=np.asarray(r['component_ids'], dtype='U160'),
        component_root_species=np.asarray(r['component_root_species'], dtype='U80'),
        component_species=np.asarray(r['component_species'], dtype='U80'),
    )
    print(json.dumps({
        'status': 'PASS_LOCAL_R3_5_RUN_COMPLETED', 'tag': tag,
        'ceiling_q': args.ceiling, 'wall_seconds': wall,
        'final_total_population': r['final_total_population'],
        'species_count': len(r['species_ids']), 'component_count': len(r['component_ids']),
        'event_counts': ec, 'headroom': r['r35_headroom_summary'],
        'summary': str(summary_path), 'state': str(state_path), 'telemetry': str(telemetry_path)
    }, indent=2))

if __name__ == '__main__':
    main()
