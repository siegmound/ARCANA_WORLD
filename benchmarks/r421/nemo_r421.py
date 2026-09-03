from __future__ import annotations
import json, math, shutil, subprocess, sys, traceback
from pathlib import Path

contract=Path(sys.argv[1]); out=Path(sys.argv[2]); work=Path(sys.argv[3])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)

def load(p:Path): return json.loads(p.read_text(encoding='utf-8-sig'))

def parse_qfreq(path:Path):
    vals={}
    lines=path.read_text(encoding='utf-8',errors='replace').splitlines()
    for line in lines[1:]:
        tok=line.split()
        if len(tok)<5: continue
        try: pop=int(float(tok[0])); locus=int(float(tok[2])); freq=float(tok[4])
        except Exception: continue
        vals.setdefault(pop,{})[locus]=freq
    pops=sorted(vals)
    common=sorted(set.intersection(*(set(vals[p]) for p in pops))) if pops else []
    if not common: return {'loci':0,'population_count':len(pops)}
    gaps=[]; het=[]
    for li in common:
        fs=[vals[p][li] for p in pops]
        if len(fs)>=2: gaps.append(max(fs)-min(fs))
        het.extend(2.0*f*(1.0-f) for f in fs)
    return {
        'loci':len(common),'population_count':len(pops),
        'mean_population_frequency_range':sum(gaps)/len(gaps) if gaps else 0.0,
        'mean_expected_heterozygosity':sum(het)/len(het) if het else 0.0,
        'metric_semantics':{
            'mean_population_frequency_range':'RAW_ALLELE_FREQUENCY_DIFFERENTIATION_NOT_GENE_FLOW_RATE',
            'mean_expected_heterozygosity':'RAW_EXPECTED_HETEROZYGOSITY_NOT_ADDITIVE_GENETIC_VARIANCE'
        }
    }

try:
    c=load(contract); d=c['engine_input']['drivers']; gens=int(c['engine_input']['representative_runtime']['steps'])
    mig=max(0.001,min(0.10,float(d['engine_gene_flow_rate'])))
    div=max(0.05,min(0.95,float(d['normalized_initial_genetic_diversity'])))
    initial_gap=max(0.18,min(0.70,0.70-0.45*div)); reps=[]
    for spec in c['engine_input']['replicates']:
        ri=int(spec['replicate_index']); seed=int(spec['seed']); rw=work/f'rep_{ri:03d}'
        if rw.exists(): shutil.rmtree(rw)
        rw.mkdir(parents=True)
        f1=[]; f2=[]
        for li in range(8):
            jitter=(li-3.5)*0.01
            f1.append(max(0.02,min(0.48,0.5-initial_gap/2+jitter)))
            f2.append(max(0.52,min(0.98,0.5+initial_gap/2-jitter)))
        mat=f"{{{{{1-mig:.8f}, {mig:.8f}}}\n                         {{{mig:.8f}, {1-mig:.8f}}}}}"
        ini=f'''## ARCANA R4.21 symmetric NEMO P2 candidate {c["frozen_parent_job"]["job_id"]}\nlogfile r421_nemo.log\nrun_mode overwrite\nrandom_seed {seed}\nroot_dir .\nfilename r421_nemo\nreplicates 1\ngenerations {gens}\npatch_number 2\npatch_nbfem {{{{500, 500}}}}\npatch_nbmal 0\nquanti_init 1\nbreed_disperse 2\nsave_stats 3\nsave_files 4\nmating_system 6\nmating_isWrightFisher\nbreed_disperse_matrix {mat}\nquanti_traits 1\nquanti_loci 8\nquanti_allele_model diallelic\nquanti_diallele_datatype byte\nquanti_allele_value {{{{0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05}}}}\nquanti_init_freq {{{{{', '.join(f'{x:.6f}' for x in f1)}}}\n                         {{{', '.join(f'{x:.6f}' for x in f2)}}}}}\nquanti_mutation_rate 0\nquanti_recombination_rate 0.5\nstat adlt.demography adlt.quanti\nstat_log_time {gens}\nquanti_freq_output 1\nquanti_freq_logtime {gens}\nquanti_dir .\n'''
        (rw/'R421.ini').write_text(ini,encoding='utf-8')
        proc=subprocess.run(['nemo2.4.2','R421.ini'],cwd=rw,text=True,capture_output=True,check=False,timeout=900)
        q=rw/'r421_nemo_1.qfreq'; metrics={}; status='FAIL'
        if proc.returncode==0 and q.exists() and q.stat().st_size>0:
            metrics=parse_qfreq(q); metrics.update({'generations':gens,'migration_rate':mig,'initial_frequency_gap_parameter':initial_gap})
            status='PASS' if metrics.get('loci',0)>=8 else 'FAIL'
        reps.append({'replicate_index':ri,'seed':seed,'status':status,'returncode':proc.returncode,'metrics':metrics,'stdout_tail':proc.stdout[-4000:],'stderr_tail':proc.stderr[-4000:]})
    result={'stage':'v0.6D1-R4.21','job_id':c['frozen_parent_job']['job_id'],'engine':'NEMO','adapter_status':'PASS' if all(r['status']=='PASS' for r in reps) else 'ENGINE_EXECUTION_FAILURE','driver_application':'FROZEN_R42_START_STATE_AND_GENE_FLOW_ONLY','semantic_guards':['heterozygosity != additive_variance','allele_frequency_differentiation != gene_flow_rate'],'replicates':reps,'canonical_write':False,'comparison_target_used':False}
except Exception as exc:
    result={'stage':'v0.6D1-R4.21','engine':'NEMO','adapter_status':'ADAPTER_FAILURE','replicates':[],'error':repr(exc),'traceback':traceback.format_exc()[-12000:],'canonical_write':False,'comparison_target_used':False}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
raise SystemExit(0 if result['adapter_status']=='PASS' else 1)
