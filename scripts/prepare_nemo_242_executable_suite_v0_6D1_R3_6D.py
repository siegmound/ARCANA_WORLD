from __future__ import annotations
import argparse, json, sys
from hashlib import sha256
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines.nemo_qtl_ensemble import NemoQTLArchitectureSpec, build_qtl_realization, write_qtl_realization
from arcana_worldsim.scientific_engines.nemo242_r36d import (
    Nemo242ExecutableReferenceSpec, canonical_r36d_scenarios, matched_no_flow_scenario,
    render_nemo242_axis_ini, simulate_arcana_admixture_only_probe,
)
from arcana_worldsim.scientific_engines.cadence_validation import simulate_arcana_cadence_probe


def semhash(obj): return sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description='Prepare R3.6D executable NEMO 2.4.2 paired-reference suite.')
    ap.add_argument('outdir',type=Path)
    ap.add_argument('--replicates',type=int,default=2)
    ap.add_argument('--seed',type=int,default=36062026)
    ap.add_argument('--loci-per-trait',type=int,default=64)
    ap.add_argument('--population-sizes',type=int,nargs='+',default=[500,2000])
    ap.add_argument('--macro-intervals',type=int,default=1)
    args=ap.parse_args()
    if args.replicates<1 or args.loci_per_trait<4 or any(n<20 for n in args.population_sizes): raise ValueError('invalid suite dimensions')
    root=args.outdir; root.mkdir(parents=True,exist_ok=True)
    records=[]; comparisons=[]
    spec=Nemo242ExecutableReferenceSpec(macro_intervals=args.macro_intervals)

    for N in args.population_sizes:
        b0,b1,c3=canonical_r36d_scenarios(n_individuals=N)
        flow_bases=(b1,c3)
        # Internal ARCANA references for the exact same start states.
        for flow in flow_bases:
            ctrl=matched_no_flow_scenario(flow)
            comparisons.append({
                'population_size':N,'pair':flow.name,
                'arcana_admixture_only_125k_flow':simulate_arcana_admixture_only_probe(flow,macro_intervals=args.macro_intervals,substeps_per_interval=1),
                'arcana_admixture_only_125k_control':simulate_arcana_admixture_only_probe(ctrl,macro_intervals=args.macro_intervals,substeps_per_interval=1),
                'arcana_admixture_only_5x25k_flow':simulate_arcana_admixture_only_probe(flow,macro_intervals=args.macro_intervals,substeps_per_interval=5),
                'arcana_admixture_only_5x25k_control':simulate_arcana_admixture_only_probe(ctrl,macro_intervals=args.macro_intervals,substeps_per_interval=5),
                'arcana_full_r36c_125k_flow':simulate_arcana_cadence_probe(flow,macrosteps=args.macro_intervals,substeps_per_macrostep=1),
                'arcana_full_r36c_5x25k_flow':simulate_arcana_cadence_probe(flow,macrosteps=args.macro_intervals,substeps_per_macrostep=5,rate_normalize_exchange=True),
            })

        # B0 engine sanity plus paired B1/C3 flow/no-flow controls.
        variants=[('B0_SANITY',b0,None)]
        for flow in flow_bases:
            variants += [('FLOW',flow,flow.name),('MATCHED_NO_FLOW',matched_no_flow_scenario(flow),flow.name)]

        for vi,(variant,scenario,pair_name) in enumerate(variants):
            for rep in range(args.replicates):
                qspec=NemoQTLArchitectureSpec(loci_per_trait=args.loci_per_trait,individual_sample_size=N)
                # Paired FLOW/control jobs must share both the same QTL realization
                # and the same engine RNG seed. This is a controlled common-random-
                # numbers design: only the migration operator changes.
                genetic_key=pair_name or scenario.name
                pair_code=(sum((i+1)*ord(c) for i,c in enumerate(genetic_key))%100000)
                gseed=int(args.seed + N*1000 + pair_code*10 + rep)
                seed=int(args.seed + 50_000_000 + N*1000 + pair_code*10 + rep)
                base_for_qtl=scenario
                realization=build_qtl_realization(base_for_qtl.normalized_trait_means,base_for_qtl.normalized_additive_variance,trait_axes=(0,1),seed=gseed,spec=qspec,individuals_per_patch=base_for_qtl.population_individuals)
                rroot=root/f'N_{N}'/(pair_name or scenario.name)/f'rep_{rep:03d}'/variant
                qtlroot=rroot/'qtl'; write_qtl_realization(realization,qtlroot,[f'P{i:03d}' for i in range(len(scenario.population_individuals))])
                for ti in range(2):
                    jroot=rroot/f'axis_{ti}'
                    bind=render_nemo242_axis_ini(scenario,realization,trait_local_index=ti,seed=seed+ti,output_dir=jroot,spec=spec)
                    job={
                        'schema':'ARCANA_R36D_NEMO_JOB_V1','stage':'v0.6D1-R3.6D','population_size':N,
                        'pair':pair_name,'variant':variant,'scenario':scenario.name,'replicate':rep,'axis':ti,
                        'arcana_trait_axis':int(realization.trait_axes[ti]),'engine_seed':seed+ti,'genetic_seed':gseed,
                        'qtl_realization_sha256':realization.semantic_sha256,
                        'effect_a':realization.effect_sizes[ti].tolist(),
                        'target_means':realization.target_means[:,ti].tolist(),
                        'target_va':realization.target_variances[:,ti].tolist(),
                        'binding_manifest_sha256':semhash(bind),
                        'experiment_sha256':sha256((realization.semantic_sha256+'|'+scenario.name+'|'+variant+'|'+str(ti)+'|'+str(N)+'|'+str(rep)).encode()).hexdigest(),
                        'canonical_write_allowed':False,'automatic_calibration_allowed':False,
                    }
                    job['job_sha256']=semhash(job)
                    (jroot/'R3_6D_JOB.json').write_text(json.dumps(job,indent=2,sort_keys=True)+'\n',encoding='utf-8')
                    records.append({k:job[k] for k in ('job_sha256','population_size','pair','variant','scenario','replicate','axis','experiment_sha256')})

    summary={'schema':'ARCANA_R36D_NEMO_EXECUTABLE_SUITE_V1','stage':'v0.6D1-R3.6D','status':'PREPARED_NEMO_2_4_2_EXECUTABLE_REFERENCE_SUITE','nemo_required':'2.4.2','protocol':'ADMIXTURE_RECOMBINATION_DRIFT_ONLY','selection_enabled':False,'mutation_rate':0.0,'q_star_initial':0.045,'population_sizes':args.population_sizes,'replicates':args.replicates,'macro_intervals':args.macro_intervals,'job_count':len(records),'records':records,'arcana_references':comparisons,'canonical_write_allowed':False,'automatic_calibration_allowed':False}
    (root/'R3_6D_EXECUTABLE_SUITE_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('stage','status','nemo_required','job_count','population_sizes','replicates')},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
