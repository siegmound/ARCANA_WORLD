#!/usr/bin/env python3
"""Resumable frozen G45 matrix. Reuse executions, never rewrite their verdicts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback
import numpy as np
import arcana_g45_distributed_amr_cbf as c
sys.path.insert(0,str(c.CODE));import audit


def needs_retry(case):
    if not c.read(case/'EXECUTION_REPORT.json')['screen_pass']:return True
    failed=case/'AUDIT_V2_FAILURE.json'
    if failed.exists():
        c.need('NO_BOUNDARY_HANGING_NODES' in c.read(failed)['error'],'UNRESOLVED_AUDIT_FAILURE:'+case.name)
        return True
    return False

def execute(spec,plugin):
    label=spec['name']+'_NEW01';case=c.ROOT/label
    if case.exists() and needs_retry(case):
        failed=c.read(case/'RUN_EXIT.json');c.need(not failed['remaining'],'UNSAFE_RETRY')
        retry=2
        while (c.ROOT/(label+'_RETRY'+str(retry))).exists():
            candidate=c.ROOT/(label+'_RETRY'+str(retry))
            if not needs_retry(candidate):break
            c.need(not c.read(candidate/'RUN_EXIT.json')['remaining'],'UNSAFE_RETRY');retry+=1
        label=label+'_RETRY'+str(retry);case=c.ROOT/label
    if not case.exists():c.case(spec,label,plugin)
    execution=c.read(case/'EXECUTION_REPORT.json');c.need(execution['screen_pass'],'REUSE_FAILED_EXECUTION:'+label)
    c.need(execution['case_spec']==spec and execution['plugin_sha256']==c.sha(plugin),'REUSE_IDENTITY')
    report=case/'AUDIT_V2_REPORT.json'
    if report.exists():return c.read(report),c.read(case/'STABLE_FIELDS_V2.json'),case
    c.write(case/'AUDIT_V2_CODE_IDENTITY.json',{'audit_sha256':c.sha(Path(audit.__file__)),'contract_sha256':c.CONTRACT_PIN})
    try:
        row,fields=audit.evaluate(case)
        c.need(row['cells']==execution['statistics']['cells'],'GLOBAL_CELL_COVERAGE')
        if spec['family']=='analytic':row['analytic_errors']=c.old.g38.errors((case/'STDOUT.txt').read_text())
        if spec['family']!='analytic' and spec['adaptive_cycles']==0 and spec['base_refinement'] in (2,3):
            oldname=('hydro_3' if spec['family']=='hydro' else 'forced_datum_3' if spec['family']=='datum' else 'forced_volume_'+str(spec['base_refinement']))
            old=c.EV/'R6_G41_NATIVE_QUADRATURE_NEW01'/oldname/'CASE_REPORT.json'
            if old.exists():
                reference=c.read(old)['native'];stats=c.g39.parse_stats(case/'output/statistics')
                row['G41_archive_replay_relative']={k:abs(stats[k]-reference[k])/max(abs(reference[k]),1.) for k in ('rms','dissipation','pmean')}
                c.need(max(row['G41_archive_replay_relative'].values())<1e-6,'G41_REPLAY')
        c.write(report,row);c.write(case/'STABLE_FIELDS_V2.json',fields)
        if not row['screen_pass']:print('G45_RETAINED_EQUILIBRIUM_FAILURE',spec['name'],flush=True)
        else:print('G45_AUDIT_PASS',spec['name'],'hanging',row['boundary_hanging_nodes'],'offdiag',row['trace_offdiagonal_nnz'],flush=True)
        return row,fields,case
    except Exception as e:
        c.write(case/'AUDIT_V2_FAILURE.json',{'error':repr(e),'traceback':traceback.format_exc()});raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['uniform','amr'],required=True);p.add_argument('--plugin',type=Path,required=True);a=p.parse_args();c.check()
    if a.phase=='amr':
        uniform=c.read(c.ROOT/'UNIFORM_PHASE_REPORT.json');c.need(uniform['execution_and_algebra_pass'] and uniform['equilibrium_pass'],'UNIFORM_GATE_REQUIRED')
    plan=c.read(c.CODE/'contract.json')['cases'];rows=[];refs={};parities=[];cases={}
    for spec in plan:
        if bool(spec['adaptive_cycles'])!=(a.phase=='amr'):continue
        row,fields,case=execute(spec,a.plugin);rows.append(row);cases[(spec['family'],spec['base_refinement'],spec['adaptive_cycles'],spec['ranks'])]=case
        key=(spec['family'],spec['base_refinement'],spec['adaptive_cycles'])
        if spec['ranks']==1:refs[key]=(row,fields)
        else:
            ref,old=refs[key];c.need(row['mesh_sha256']==ref['mesh_sha256'] and fields['keys']==old['keys'],'RANK_MESH_OR_SUPPORT_IDENTITY')
            actual=np.array(fields['values']);prior=np.array(old['values']);delta=[np.linalg.norm(actual[:,k]-prior[:,k])/max(np.linalg.norm(prior[:,k]),1.) for k in range(actual.shape[1])]
            c.need(max(delta)<=audit.T['same_mesh_rank_relative'],'RANK_NUMERICAL_PARITY')
            parities.append({'case':spec['name'],'field_relative':delta,'screen_pass':True})
    gauges=[]
    for (family,l,amr,n),case in cases.items():
        if family=='datum' and ('forced',l,amr,n) in cases:
            result=audit.datum(cases[('forced',l,amr,n)],case);gauges.append({'case':case.name,**result})
    analytic=[]
    for n in (1,4):
        coarse=next((r for r in rows if r['spec']['family']=='analytic' and r['spec']['base_refinement']==2 and r['spec']['ranks']==n),None)
        fine=next((r for r in rows if r['spec']['family']=='analytic' and r['spec']['base_refinement']==3 and r['spec']['ranks']==n),None)
        if coarse and fine:
            ratios={k:fine['analytic_errors'][k]/coarse['analytic_errors'][k] for k in coarse['analytic_errors']};c.need(all(v<1 for v in ratios.values()),'ANALYTIC_REFINEMENT')
            analytic.append({'ranks':n,'fine_over_coarse':ratios,'screen_pass':True})
    result={'phase':a.phase,'execution_and_algebra_pass':True,'equilibrium_pass':all(r['screen_pass'] for r in rows),'cases':rows,'rank_parity':parities,'datum':gauges,'analytic_convergence':analytic,'contract_sha256':c.CONTRACT_PIN,**c.SCOPE}
    c.write(c.ROOT/(a.phase.upper()+'_PHASE_REPORT.json'),result);print('G45_PHASE_COMPLETE',a.phase,'cases',len(rows),'equilibrium',result['equilibrium_pass'],flush=True)
if __name__=='__main__':main()
