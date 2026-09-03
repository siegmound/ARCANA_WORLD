from __future__ import annotations
import json, shutil, subprocess, sys, traceback
from pathlib import Path

contract=Path(sys.argv[1]); out=Path(sys.argv[2]); work=Path(sys.argv[3])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)
try:
    import tskit
    c=json.loads(contract.read_text(encoding='utf-8-sig')); d=c['engine_input']['drivers']; gens=int(c['engine_input']['representative_runtime']['steps'])
    mig=max(0.001,min(0.10,float(d['engine_gene_flow_rate']))); sel=max(0.0,min(0.05,float(d['engine_selection_strength']))); reps=[]
    for spec in c['engine_input']['replicates']:
        ri=int(spec['replicate_index']); seed=int(spec['seed']); rw=work/f'rep_{ri:03d}'
        if rw.exists(): shutil.rmtree(rw)
        rw.mkdir(parents=True); endgen=gens+1
        script=f'''initialize() {{\n initializeTreeSeq();\n initializeMutationRate(1e-7);\n initializeMutationType("m1", 0.5, "f", 0.0);\n initializeMutationType("m2", 0.5, "f", {sel:.10f});\n initializeGenomicElementType("g1", c(m1,m2), c(0.99,0.01));\n initializeGenomicElement(g1, 0, 19999);\n initializeRecombinationRate(1e-8);\n}}\n1 early() {{\n sim.addSubpop("p1", 200); sim.addSubpop("p2", 200);\n p1.setMigrationRates(p2, {mig:.10f}); p2.setMigrationRates(p1, {mig:.10f});\n}}\n{endgen} late() {{\n sim.treeSeqOutput("r421.trees"); sim.simulationFinished();\n}}\n'''
        (rw/'r421.slim').write_text(script,encoding='utf-8')
        proc=subprocess.run(['slim','-s',str(seed),'r421.slim'],cwd=rw,text=True,capture_output=True,check=False,timeout=900)
        tp=rw/'r421.trees'; metrics={}; status='FAIL'
        if proc.returncode==0 and tp.exists():
            ts=tskit.load(str(tp)); alive_nodes=[]
            for ind in ts.individuals():
                nodes=[int(n) for n in ind.nodes if int(n)>=0]
                if nodes and min(float(ts.node(n).time) for n in nodes)==0.0:
                    alive_nodes.extend(n for n in nodes if float(ts.node(n).time)==0.0)
            by_pop={}
            for n in alive_nodes: by_pop.setdefault(int(ts.node(n).population),[]).append(n)
            sample_sets=[v for _,v in sorted(by_pop.items()) if len(v)>=2]
            global_div=float(ts.diversity(sample_sets=[alive_nodes])[0]) if len(alive_nodes)>=2 else 0.0
            per_pop=[float(ts.diversity(sample_sets=[s])[0]) for s in sample_sets]
            fst=None
            if len(sample_sets)>=2:
                try: fst=float(ts.Fst(sample_sets=sample_sets))
                except Exception: fst=None
            metrics={'current_sample_nodes':len(alive_nodes),'population_sample_set_count':len(sample_sets),'global_diversity_per_site':global_div,'per_population_diversity_per_site':per_pop,'fst_between_current_population_samples':fst,'sequence_length':float(ts.sequence_length),'tree_nodes':int(ts.num_nodes),'tree_edges':int(ts.num_edges),'tree_mutations':int(ts.num_mutations),'migration_rate_input':mig,'selection_strength_input':sel,'metric_semantics':{'global_diversity_per_site':'DIVERSITY_NOT_ANCESTRY_CONTRIBUTION','fst_between_current_population_samples':'DIFFERENTIATION_NOT_MIGRATION_RATE'}}
            status='PASS' if len(alive_nodes)>=2 else 'FAIL'
        reps.append({'replicate_index':ri,'seed':seed,'status':status,'returncode':proc.returncode,'metrics':metrics,'stdout_tail':proc.stdout[-4000:],'stderr_tail':proc.stderr[-4000:]})
    result={'stage':'v0.6D1-R4.21','job_id':c['frozen_parent_job']['job_id'],'engine':'SLiM','adapter_status':'PASS' if all(r['status']=='PASS' for r in reps) else 'ENGINE_EXECUTION_FAILURE','driver_application':'FROZEN_R42_GENE_FLOW_SELECTION_AND_RUNTIME','semantic_guards':['diversity != ancestry','FST != migration_rate'],'replicates':reps,'canonical_write':False,'comparison_target_used':False}
except Exception as exc:
    result={'stage':'v0.6D1-R4.21','engine':'SLiM','adapter_status':'ADAPTER_FAILURE','replicates':[],'error':repr(exc),'traceback':traceback.format_exc()[-12000:],'canonical_write':False,'comparison_target_used':False}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
raise SystemExit(0 if result['adapter_status']=='PASS' else 1)
