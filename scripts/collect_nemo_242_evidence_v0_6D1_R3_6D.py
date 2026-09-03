from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines.nemo242_r36d import collect_nemo242_evidence
from arcana_worldsim.scientific_engines.serialization import save_evidence


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('suite',type=Path); args=ap.parse_args(); root=args.suite
    suite_summary_path=root/'R3_6D_EXECUTABLE_SUITE_SUMMARY.json'
    suite_summary=json.loads(suite_summary_path.read_text()) if suite_summary_path.exists() else {}
    jobs=[]
    for jp in sorted(root.rglob('R3_6D_JOB.json')):
        j=json.loads(jp.read_text()); wd=jp.parent
        rcfile=wd/'engine.returncode.txt'; out=wd/'engine.stdout.txt'; err=wd/'engine.stderr.txt'
        if not rcfile.exists():
            jobs.append({**{k:j.get(k) for k in ('job_sha256','pair','variant','population_size','replicate','axis')},'status':'NOT_EXECUTED'}); continue
        rc=int(rcfile.read_text().strip()); stdout=out.read_text(errors='replace') if out.exists() else ''; stderr=err.read_text(errors='replace') if err.exists() else ''
        ev=collect_nemo242_evidence(experiment_sha256=j['experiment_sha256'],run_id=j['job_sha256'],workdir=wd,arcana_effect_a=j['effect_a'],execution_returncode=rc,stdout=stdout,stderr=stderr)
        save_evidence(ev,wd/'evidence')
        rec={**{k:j.get(k) for k in ('job_sha256','pair','variant','population_size','replicate','axis')},'status':ev.status,'evidence_sha256':ev.semantic_sha256}
        if 'additive_variance' in ev.arrays:
            rec['final_mean_va']=float(np.mean(ev.arrays['additive_variance'][-1])); rec['final_max_va']=float(np.max(ev.arrays['additive_variance'][-1])); rec['final_trait_spread']=float(np.max(ev.arrays['trait_mean'][-1])-np.min(ev.arrays['trait_mean'][-1]))
        jobs.append(rec)
    # Paired FLOW - MATCHED_NO_FLOW summaries.
    paired=[]
    keys=sorted({(r.get('pair'),r.get('population_size'),r.get('replicate'),r.get('axis')) for r in jobs if r.get('pair') and r.get('status')=='ENGINE_COMPLETED_QFREQ_PARSED'})
    for key in keys:
        pair,N,rep,axis=key; subset=[r for r in jobs if (r.get('pair'),r.get('population_size'),r.get('replicate'),r.get('axis'))==key]
        by={r['variant']:r for r in subset}
        if 'FLOW' in by and 'MATCHED_NO_FLOW' in by:
            paired.append({'pair':pair,'population_size':N,'replicate':rep,'axis':axis,'delta_final_mean_va_flow_minus_control':by['FLOW']['final_mean_va']-by['MATCHED_NO_FLOW']['final_mean_va'],'delta_final_max_va_flow_minus_control':by['FLOW']['final_max_va']-by['MATCHED_NO_FLOW']['final_max_va'],'flow_evidence_sha256':by['FLOW']['evidence_sha256'],'control_evidence_sha256':by['MATCHED_NO_FLOW']['evidence_sha256']})
    # Build the actual three-way review table. NEMO's primary protocol has no
    # mutation or selection, so its paired FLOW-control delta is compared to
    # ARCANA's admixture-only probes, not directly to the full Riccati runtime.
    refs={(r.get('pair'),r.get('population_size')):r for r in suite_summary.get('arcana_references',[])}
    aggregates=[]
    for pair_name in sorted({r['pair'] for r in paired}):
        for N in sorted({r['population_size'] for r in paired if r['pair']==pair_name}):
            for axis in sorted({r['axis'] for r in paired if r['pair']==pair_name and r['population_size']==N}):
                vals=np.asarray([r['delta_final_mean_va_flow_minus_control'] for r in paired if r['pair']==pair_name and r['population_size']==N and r['axis']==axis],dtype=float)
                if vals.size==0: continue
                rr=refs.get((pair_name,N),{})
                def arc_delta(flow_key,ctrl_key):
                    if flow_key not in rr or ctrl_key not in rr: return None
                    f=np.asarray(rr[flow_key]['final_additive_variance'],dtype=float)
                    c=np.asarray(rr[ctrl_key]['final_additive_variance'],dtype=float)
                    return float(np.mean(f[:,int(axis)]-c[:,int(axis)]))
                d125=arc_delta('arcana_admixture_only_125k_flow','arcana_admixture_only_125k_control')
                d25=arc_delta('arcana_admixture_only_5x25k_flow','arcana_admixture_only_5x25k_control')
                mean=float(np.mean(vals)); sd=float(np.std(vals,ddof=1)) if vals.size>1 else 0.0
                ci=float(1.96*sd/np.sqrt(vals.size)) if vals.size>1 else None
                aggregates.append({
                    'pair':pair_name,'population_size':N,'axis':axis,'replicates':int(vals.size),
                    'nemo_delta_va_mean':mean,'nemo_delta_va_sd':sd,'nemo_delta_va_ci95_halfwidth':ci,
                    'arcana_admixture_only_1x125k_delta_va':d125,
                    'arcana_admixture_only_5x25k_delta_va':d25,
                    'nemo_minus_arcana_1x125k':None if d125 is None else mean-d125,
                    'nemo_minus_arcana_5x25k':None if d25 is None else mean-d25,
                    'inference_authority':'REVIEW_ONLY_NO_AUTOMATIC_CALIBRATION',
                })
    n_sensitivity=[]
    for pair_name in sorted({a['pair'] for a in aggregates}):
        for axis in sorted({a['axis'] for a in aggregates if a['pair']==pair_name}):
            xs=[a for a in aggregates if a['pair']==pair_name and a['axis']==axis]
            if len(xs)>=2:
                vals=[a['nemo_delta_va_mean'] for a in xs]
                n_sensitivity.append({'pair':pair_name,'axis':axis,'population_sizes':[a['population_size'] for a in xs],'delta_va_range_across_N':float(max(vals)-min(vals)),'converged':False,'note':'R3.6D reports N sensitivity; convergence thresholds are not authorially inferred.'})
    executed=sum(r['status']!='NOT_EXECUTED' for r in jobs); completed=sum(r['status']=='ENGINE_COMPLETED_QFREQ_PARSED' for r in jobs)
    all_done=bool(jobs) and completed==len(jobs)
    summary={'schema':'ARCANA_R36D_NEMO_EVIDENCE_SUMMARY_V2','stage':'v0.6D1-R3.6D','status':'NEMO_EVIDENCE_COMPLETE_REVIEW_REQUIRED' if all_done else ('PARTIAL_NEMO_EVIDENCE' if executed else 'NEMO_RUNS_PENDING'),'job_count':len(jobs),'executed_count':executed,'parsed_complete_count':completed,'jobs':jobs,'paired_admixture_excess':paired,'three_way_admixture_only_comparison':aggregates,'population_size_sensitivity':n_sensitivity,'inference_scope':'NEMO paired admixture/recombination/drift delta versus ARCANA admixture-only 1x125k and 5x25k moment mixing','full_r3_5_calibration_authorized':False,'canonical_write_allowed':False,'automatic_calibration_allowed':False}
    (root/'R3_6D_NEMO_EVIDENCE_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps({k:summary[k] for k in ('stage','status','job_count','executed_count','parsed_complete_count')},indent=2)); return 0 if executed==0 or completed==executed else 2
if __name__=='__main__': raise SystemExit(main())
