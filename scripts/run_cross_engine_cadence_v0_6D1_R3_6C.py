from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
from dataclasses import replace

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines import (  # noqa:E402
    canonical_r36b_scenarios, build_three_way_reference_plan,
    simulate_arcana_cadence_probe, write_three_way_plan,
    embeddable_reference_exchange_from_edge_targets,
)
from arcana_worldsim.scientific_engines.nemo_benchmarks import ExchangePhase  # noqa:E402


def run_one(s, root, macrosteps):
    sr=root/s.name; sr.mkdir(parents=True,exist_ok=True)
    plan=build_three_way_reference_plan(s); write_three_way_plan(plan,sr/'three_way_plan.json')
    r125=simulate_arcana_cadence_probe(s,macrosteps=macrosteps,substeps_per_macrostep=1)
    r25=simulate_arcana_cadence_probe(s,macrosteps=macrosteps,substeps_per_macrostep=5,rate_normalize_exchange=True)
    raw=simulate_arcana_cadence_probe(s,macrosteps=macrosteps,substeps_per_macrostep=5,rate_normalize_exchange=False)
    for name,p in [('arcana_125k.json',r125),('arcana_5x25k_rate_normalized.json',r25),('arcana_5x25k_raw_repeat_DIAGNOSTIC_ONLY.json',raw)]:
        (sr/name).write_text(json.dumps(p,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    m=np.asarray(plan['nemo_per_generation_stochastic_matrix']); off=m-np.diag(np.diag(m))
    return {
        'scenario':s.name,'status':'PASS_CADENCE_NORMALIZED_PLAN',
        'q_125k':r125['final_max_q'],'q_5x25k_rate_normalized':r25['final_max_q'],
        'q_5x25k_raw_repeat':raw['final_max_q'],
        'abs_q_delta_125k_vs_5x25k':abs(r125['final_max_q']-r25['final_max_q']),
        'nemo_per_generation_max_offdiag':float(np.max(off)),
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('outdir',type=Path); ap.add_argument('--macrosteps',type=int,default=40)
    args=ap.parse_args(); args.outdir.mkdir(parents=True,exist_ok=True)
    suite=canonical_r36b_scenarios(n_individuals=2000); records=[]
    for s in (suite[0],suite[1]): records.append(run_one(s,args.outdir,args.macrosteps))

    # Preserve R3.6B B3 as historical diagnostic and explicitly record why it
    # cannot be an exact per-generation NEMO cadence reference.
    b3=suite[3]
    try:
        records.append(run_one(b3,args.outdir,args.macrosteps))
    except ValueError as e:
        records.append({'scenario':b3.name,'status':'REJECTED_NON_EMBEDDABLE_FOR_EXACT_PER_GENERATION_REFERENCE','reason':str(e)})

    # Build a new R3.6C-only embeddable stress reference from the same symmetric
    # edge targets. This never replaces B3 or any ARCANA production exchange.
    g2=embeddable_reference_exchange_from_edge_targets(b3.phases[0].exchange_matrix,125000.0)
    c3=replace(b3,name='C3_EMBEDDABLE_HIGH_ADMIXTURE_STRESS',phases=(ExchangePhase('EMBEDDABLE_HIGH_EXCHANGE',0,b3.generations,g2),),notes=b3.notes+('R3.6C-only CTMC-embeddable cross-engine reference; never canonical production exchange',))
    records.append(run_one(c3,args.outdir,args.macrosteps))

    summary={
        'schema':'ARCANA_R36C_THREE_WAY_PRE_NEMO_SUMMARY_V1','stage':'v0.6D1-R3.6C',
        'status':'PASS_INTERNAL_CADENCE_AND_NEMO_NORMALIZATION_PREVALIDATION',
        'nemo_actual_engine_runs':'PENDING_EXTERNAL_NEMO_2_4_2_EXECUTION',
        'canonical_write_allowed':False,'automatic_calibration_allowed':False,
        'r36b_b3_preserved_not_rewritten':True,'records':records,
    }
    (args.outdir/'R3_6C_PRE_NEMO_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
