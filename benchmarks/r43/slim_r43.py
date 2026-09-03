from __future__ import annotations
import json, shutil, subprocess, sys, traceback
from pathlib import Path

contract=Path(sys.argv[1]); out=Path(sys.argv[2]); work=Path(sys.argv[3])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)
try:
    import tskit
    c=json.loads(contract.read_text(encoding='utf-8-sig')); d=c['engine_input']['drivers']; gens=int(c['engine_input']['representative_runtime']['steps'])
    mig=max(0.001,min(0.10,float(d['engine_gene_flow_rate']))); sel=max(0.0,min(0.05,float(d['engine_selection_strength'])))
    reps=[]
    for spec in c['engine_input']['replicates']:
        ri=int(spec['replicate_index']); seed=int(spec['seed']); rw=work/f'rep_{ri:03d}'
        if rw.exists(): shutil.rmtree(rw)
        rw.mkdir(parents=True)
        endgen=gens+1
        script=f'''initialize() {{\n initializeTreeSeq();\n initializeMutationRate(1e-7);\n initializeMutationType("m1", 0.5, "f", 0.0);\n initializeMutationType("m2", 0.5, "f", {sel:.10f});\n initializeGenomicElementType("g1", c(m1,m2), c(0.99,0.01));\n initializeGenomicElement(g1, 0, 19999);\n initializeRecombinationRate(1e-8);\n}}\n1 early() {{\n sim.addSubpop("p1", 200); sim.addSubpop("p2", 200);\n p1.setMigrationRates(p2, {mig:.10f}); p2.setMigrationRates(p1, {mig:.10f});\n}}\n{endgen} late() {{\n catn("R43_P1=" + p1.individualCount); catn("R43_P2=" + p2.individualCount);\n sim.treeSeqOutput("r43.trees"); sim.simulationFinished();\n}}\n'''
        (rw/'r43.slim').write_text(script,encoding='utf-8')
        proc=subprocess.run(['slim','-s',str(seed),'r43.slim'],cwd=rw,text=True,capture_output=True,check=False,timeout=900)
        tp=rw/'r43.trees'; metrics={}; status='FAIL'
        if proc.returncode==0 and tp.exists():
            ts=tskit.load(str(tp))
            # tskit Individual rows do not carry a time column. Current SLiM individuals are
            # identified from their genome-node times instead of assuming an Individual.time API.
            alive=[]
            for ind in ts.individuals():
                inode=[int(n) for n in ind.nodes if int(n) >= 0]
                if inode and min(float(ts.node(n).time) for n in inode) == 0.0:
                    alive.append(ind)
            nodes=[]
            for ind in alive: nodes.extend(int(n) for n in ind.nodes if int(n) >= 0 and float(ts.node(int(n)).time) == 0.0)
            final_pop=len(alive)
            diversity=float(ts.diversity(sample_sets=[nodes])[0]) if len(nodes)>=2 else 0.0
            metrics={'initial_population':400,'final_population':final_pop,'sequence_length':float(ts.sequence_length),'tree_nodes':int(ts.num_nodes),'tree_edges':int(ts.num_edges),'tree_mutations':int(ts.num_mutations),'final_genetic_diversity_per_site':diversity,'migration_rate':mig,'selection_strength':sel,'generations':gens}
            status='PASS' if ts.num_nodes>0 and final_pop>0 else 'FAIL'
        reps.append({'replicate_index':ri,'seed':seed,'status':status,'returncode':proc.returncode,'metrics':metrics,'stdout_tail':proc.stdout[-4000:],'stderr_tail':proc.stderr[-4000:]})
    result={'stage':'v0.6D1-R4.3','job_id':c['frozen_parent_job']['job_id'],'engine':'SLiM','adapter_status':'PASS' if all(r['status']=='PASS' for r in reps) else 'ENGINE_EXECUTION_FAILURE','driver_application':'migration_rate_and_selection_strength','replicates':reps,'canonical_write':False}
except Exception as exc:
    result={'stage':'v0.6D1-R4.3','engine':'SLiM','adapter_status':'ADAPTER_FAILURE','replicates':[],'error':repr(exc),'traceback':traceback.format_exc()[-12000:],'canonical_write':False}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
raise SystemExit(0 if result['adapter_status']=='PASS' else 1)
