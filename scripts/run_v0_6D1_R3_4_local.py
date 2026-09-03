from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rebased_natural_control_runtime_v0_6D1_R3_4 import R34Config, run

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--end-age-ma',type=float,default=150.0); ap.add_argument('--out-dir',type=Path,default=ROOT/'local_runs/v0_6D1_R3_4'); ap.add_argument('--threads',type=int,default=0)
    args=ap.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    common=np.load(ROOT/'outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz',allow_pickle=False)
    a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
    md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); rows=md['species'] if isinstance(md,dict) and 'species' in md else md
    cfg=R34Config(end_age_ma=float(args.end_age_ma))
    t=time.time(); r=run(common,a1,rows,cfg); wall=time.time()-t
    ec={}
    for e in r['events']: ec[e['event']]=ec.get(e['event'],0)+1
    tag=f"210_to_{str(args.end_age_ma).replace('.','p')}Ma"
    summary={k:r[k] for k in ['stage','config','initial_total_population','final_total_population','species_ids','events','snapshots','registry','gate_diagnostics','gene_flow_closure','topology_remap_mass','barrier_history','authority']}
    summary.update({'species_count':len(r['species_ids']),'component_count':len(r['component_ids']),'event_counts':ec,'wall_seconds':wall})
    (args.out_dir/f'{tag}_summary.json').write_text(json.dumps(summary,indent=2))
    np.savez_compressed(args.out_dir/f'{tag}_state.npz',population=r['population'],trait=r['trait'],va=r['va'],generation_time=r['generation_time'],ri=r['ri'],clock=r['clock'],contact=r['contact'],trait_distance=r['trait_distance'],component_guild=r['component_guild'],component_ids=np.asarray(r['component_ids'],dtype='U160'),component_root_species=np.asarray(r['component_root_species'],dtype='U80'),component_species=np.asarray(r['component_species'],dtype='U80'))
    print(json.dumps({'status':'PASS_LOCAL_R3_4_RUN_COMPLETED','tag':tag,'wall_seconds':wall,'final_total_population':r['final_total_population'],'species_count':len(r['species_ids']),'component_count':len(r['component_ids']),'event_counts':ec,'summary':str(args.out_dir/f'{tag}_summary.json'),'state':str(args.out_dir/f'{tag}_state.npz')},indent=2))
if __name__=='__main__': main()
