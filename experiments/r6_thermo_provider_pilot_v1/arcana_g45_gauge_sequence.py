#!/usr/bin/env python3
"""Predeclared G45R1 gauge control; original nonlinear failures are immutable."""
import argparse
from pathlib import Path
import sys
import traceback
import numpy as np
import arcana_g45_distributed_amr_cbf as c
sys.path.insert(0,str(c.CODE));import audit


def main():
    p=argparse.ArgumentParser();p.add_argument('--plugin',type=Path,required=True);a=p.parse_args();c.check()
    plan=c.read(c.CODE/'gauge_diagnostic_contract_v1.json');rows=[];refs={};parities=[];locations={}
    for design in plan['cases']:
        spec=design['original_case'];variant=design['gauge_variant'];label=('G45R1_'+spec['name']+'_unremoved_NEW01') if variant=='unremoved' else spec['name']+'_NEW01';case=c.ROOT/label
        if not case.exists():c.case(spec,label,a.plugin,gauge_variant=variant if variant=='unremoved' else None)
        execution=c.read(case/'EXECUTION_REPORT.json');c.need(execution['screen_pass'] and not execution['execution']['remaining'],'GAUGE_EXECUTION_FAILURE')
        convergence=c.native_convergence(case)
        convergence_file=case/'NATIVE_CONVERGENCE_ADJUDICATION.json'
        if not convergence_file.exists():c.write(convergence_file,convergence)
        c.need(convergence['screen_pass'],'NATIVE_NONLINEAR_CONVERGENCE:'+label)
        reportfile=case/'G45R1_AUDIT_REPORT.json'
        if reportfile.exists():row=c.read(reportfile);fields=c.read(case/'G45R1_FIELDS.json')
        else:
            try:
                row,fields=audit.evaluate(case);row.update(gauge_variant=variant,native_convergence=convergence)
                c.need(row['cells']==execution['statistics']['cells'],'GLOBAL_CELL_COVERAGE')
                if spec['family']=='analytic':row['analytic_errors']=c.old.g38.errors((case/'STDOUT.txt').read_text())
                else:
                    stats=c.g39.parse_stats(case/'output/statistics');row['rotation_statistics']={k:stats[k] for k in ('rotation','surface_rotation','angular_momentum','rms','dissipation')}
                c.write(reportfile,row);c.write(case/'G45R1_FIELDS.json',fields)
            except Exception as e:
                c.write(case/'G45R1_AUDIT_FAILURE.json',{'error':repr(e),'traceback':traceback.format_exc()});raise
        audit.enforce(row);rows.append(row);locations[(spec['family'],spec['base_refinement'],spec['ranks'])]=case
        key=(spec['family'],spec['base_refinement'])
        if spec['ranks']==1:refs[key]=(row,fields)
        else:
            ref,old=refs[key];c.need(row['mesh_sha256']==ref['mesh_sha256'] and fields['keys']==old['keys'],'GAUGE_RANK_MESH_IDENTITY')
            actual=np.array(fields['values']);prior=np.array(old['values']);delta=[np.linalg.norm(actual[:,k]-prior[:,k])/max(np.linalg.norm(prior[:,k]),1.) for k in range(actual.shape[1])]
            c.need(max(delta)<=audit.T['same_mesh_rank_relative'],'GAUGE_RANK_PARITY');parities.append({'case':label,'relative_fields':delta,'screen_pass':True})
        print('G45R1_PASS',label,'cells',row['cells'],'hanging',row['boundary_hanging_nodes'],'CG',row['trace_CG_residual'],flush=True)
    gauges=[]
    for (family,l,n),case in locations.items():
        if family=='datum' and ('forced',l,n) in locations:gauges.append({'case':case.name,**audit.datum(locations[('forced',l,n)],case)})
    analytic=[]
    for n in (1,4):
        coarse=next(r for r in rows if r['spec']['family']=='analytic' and r['spec']['base_refinement']==2 and r['spec']['ranks']==n)
        fine=next(r for r in rows if r['spec']['family']=='analytic' and r['spec']['base_refinement']==3 and r['spec']['ranks']==n)
        ratios={k:fine['analytic_errors'][k]/coarse['analytic_errors'][k] for k in coarse['analytic_errors']};c.need(all(v<1 for v in ratios.values()),'AMR_ANALYTIC_REFINEMENT');analytic.append({'ranks':n,'fine_over_coarse':ratios})
    c.write(c.ROOT/'GAUGE_R1_PHASE_REPORT.json',{'screen_pass':True,'cases':rows,'rank_parity':parities,'datum':gauges,'analytic_convergence':analytic,
        'scope':'AMR CBF conditional on predeclared unremoved-gauge variant for forced/datum; original net-rotation nonlinear path remains blocked',
        'contract_sha256':c.sha(c.CODE/'gauge_diagnostic_contract_v1.json'),**c.SCOPE})
    print('G45R1_PHASE_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
