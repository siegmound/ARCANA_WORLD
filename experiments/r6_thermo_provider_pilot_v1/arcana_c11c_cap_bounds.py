#!/usr/bin/env python3
"""C11C bounded cap audit: preserve measured partial records; no solver calls."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_c11cr1_recover as rec
import arcana_c11cr2_cap_repair as r2

R2_PIN='74935f7de08a9bd111d796dc29b1ae364dd781d76f9ef0b83e75db4410d507a0'
R2_BLOB='6b72021c2f93cfdb556d5588bf33e33100805b7d'

def bounds(log):
    rows,bad,_=rec.parse_records(log)
    a.need(len(rows['C11CAP'])==1791 and len(bad['C11CAP'])==1 and
           not bad['C11ZERO'] and not rows['C11ZERO'],'CAP_INVENTORY')
    i=bad['C11CAP'][0]['line']-1
    lines=log.splitlines()
    prefix,sep,suffix=lines[i].partition(r2.WARN)
    t=prefix.split()
    a.need(sep and not suffix.strip() and len(t)==7 and t[0]=='C11CAP' and
           all(rec.NUM.fullmatch(x) for x in t[1:4]) and
           all(rec.INT.fullmatch(x) for x in t[4:]),'PARTIAL_RECORD_SCHEMA')
    partial=np.array([float(x.replace('D','E')) for x in t[1:]])
    a.need(np.isfinite(partial).all() and partial[0]>0 and partial[1]>0
           and partial[2]==0 and np.array_equal(partial[3:],np.zeros(3)),
           'PARTIAL_RECORD_NOT_EXPECTED_MANTLE')
    x=np.array(rows['C11CAP'],dtype=float)
    a.need(x.shape==(1791,8) and np.isfinite(x).all() and
           np.all(x[:,0]>=0) and np.all(x[:,1]>0) and
           np.all((x[:,2]>=0)&(x[:,2]<=x[:,1])) and
           np.all(x[:,3:]>=0) and np.all(x[:,3:]==np.floor(x[:,3:])) and
           np.all(x[:,3]<=9) and np.all(x[:,4]<=x[:,7]) and
           np.all(x[:,5:7]<=1) and np.all(x[:,7]<=51),'COMPLETE_RECORD_RANGE')
    # No exact completion asserted: the last two counters are unobserved.
    # Diamnd has at most 51 creep trial samples and one region V flag per call.
    result={}
    for name,y,missing in [('crust',x[x[:,0]==0],0),('mantle',x[x[:,0]>0],1)]:
        a.need(len(y)+missing==896,'LAYER_INVENTORY:'+name)
        v={'dCreep_transition_trial_hits':(int(y[:,3].sum()),0),
           'dCreep_transition_layer_calls_with_hits':(int(np.count_nonzero(y[:,3])),0),
           'dCreep_creep_quadrature_hits':(int(y[:,4].sum()),0),
           'dCreep_creep_layer_calls_with_hits':(int(np.count_nonzero(y[:,4])),0),
           'visMax_mean_creep_clamped_layer_calls':(int(y[:,5].sum()),0),
           'visMax_brittle_region_V_layer_calls':(int(y[:,6].sum()),missing),
           'creep_trial_samples':(int(y[:,7].sum()),51*missing)}
        result[name]={'complete_records':len(y),'partial_records':missing,
            'counter_intervals':{k:{'lower':n,'upper':n+d} for k,(n,d) in v.items()}}
    return {'complete_records':1791,'partial_records':1,'zero_strain_IP':0,
            'layers':result,'partial_prefix_tokens':t[1:],
            'unobserved_fields':['brittle_region_V_flag','creep_trial_samples'],
            'raw_context': [{'line':j+1,'text':lines[j]} for j in range(max(0,i-3),min(len(lines),i+9))],
            'exact_full_inventory':False,
            'limitations':'Intervals are conservative bounds on unobserved tokens, not reconstructed records or depth fractions. Other visMax-dependent stiffness terms remain outside these counters.'}

def main():
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    here=Path(__file__).resolve().parent
    for n,pin in [('arcana_c11a_assembly.py',r1.A_SCRIPT_PIN),
                  ('arcana_c11b_first_solve.py',r1.B_SCRIPT_PIN),
                  ('arcana_c11br1_convergence.py',c.R1_SCRIPT)]:
        a.need(a.sha(here/n)==pin,'RUNNER_HASH:'+n)
    for n,pin in [('arcana_c11c_sensitivity.py',rec.C_BLOB),
                  ('arcana_c11cr1_recover.py',r2.R1_REC_BLOB),
                  ('arcana_c11cr2_cap_repair.py',R2_BLOB)]:
        a.need(r2.blob(here/n)==pin,'RUNNER_BLOB:'+n)
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
           not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    native=c10.OUT.with_name('R6_THERMO_C11C_SENSITIVITY_NEW01')
    prev=c10.OUT.with_name('R6_THERMO_C11CR1_RECOVERY_NEW01')
    latest=c10.OUT.with_name('R6_THERMO_C11CR2_CAP_RECOVERY_NEW01')
    m=c.verified(native,rec.C_PIN,rec.C_STATUS)
    p=c.verified(prev,r2.R1_REC_PIN,r2.R1_REC_STATUS)
    q=c.verified(latest,R2_PIN,r2.STATUS_BAD)
    a.need(q['C11CR1_manifest_sha256']==r2.R1_REC_PIN and
           q['C11C_manifest_sha256']==rec.C_PIN and q['additional_native_solves']==0 and
           q['source_sha']==a.SHA and all(q[k]==v for k,v in c.SCOPE.items()),'R2_LINEAGE')
    old=a.read(latest/'C11CR2_CAMPAIGN_REPORT.json')['cases']
    a.need(set(old)==set(c.CASES),'CASE_INVENTORY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(z) for z in
           (root,native,prev,latest,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    reports={}
    for k,v in old.items():
        a.need(v['mechanical_analysis']=='PASS' and v['control_readback']=='PASS'
               and v['cap_analysis']=='BLOCKED' and v['iterations']==rec.COUNTS[k]
               and a.sha(prev/k/'MECHANICAL_ANALYSIS.json')==v['mechanical_source_sha256'],
               'MECHANICAL_PROVENANCE:'+k)
        report={z:t for z,t in v.items() if z!='cap_error'}
        try:
            cap=bounds((native/k/'run.log').read_text())
            cap['source_log_sha256']=a.sha(native/k/'run.log')
            report['cap_analysis']='BOUNDED_NOT_EXACT'
            report['caps']=cap
        except Exception as e:
            report['cap_analysis']='BLOCKED'
            report['cap_error']=rec.err(e)
        reports[k]=report
        print(json.dumps({k:{'cap_analysis':report['cap_analysis'],
             'caps':report.get('caps'),'error':report.get('cap_error')}},allow_nan=False),flush=True)
    status=('C11C_CAP_DIAGNOSTICS_BOUNDED__PHYSICAL_REVIEW_REQUIRED'
            if all(v['cap_analysis']=='BOUNDED_NOT_EXACT' for v in reports.values())
            else 'C11C_CAP_DIAGNOSTIC_BOUNDS_BLOCKED')
    for archive,manifest in [(native,m),(prev,p),(latest,q)]:
        a.need(c.inventory(archive)==manifest['files'],'SOURCE_ARCHIVE_MUTATION')
    a.write(out/'CAP_BOUNDS_REPORT.json',{'status':status,'cases':reports,
        'physical_acceptance':False,'additional_native_solves':0,'full_cap_inventory':False,**c.SCOPE})
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,
        'C11C_manifest_sha256':rec.C_PIN,'C11CR1_manifest_sha256':r2.R1_REC_PIN,
        'C11CR2_manifest_sha256':R2_PIN,'runner_sha256':a.sha(Path(__file__)),
        'additional_native_solves':0,'files':c.inventory(out),**c.SCOPE})
    print('C11C_CAP_BOUNDS_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if status.endswith('PHYSICAL_REVIEW_REQUIRED') else 2

if __name__=='__main__':
    raise SystemExit(main())
