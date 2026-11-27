#!/usr/bin/env python3
"""C11C-R2: recover a split native CAP record from literal archived tokens.
Never rerun a solver, infer missing values, or change the retained archives.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_c11cr1_recover as rec

R1_REC_PIN='e3e16a4ea9a994e36420101122dcb5b68ebe8785821ff1c36891a8d1f8938611'
R1_REC_STATUS='C11CR1_RECOVERY_RETAINED__DIAGNOSTIC_GAPS'
R1_REC_BLOB='72432979632b92a8ec2b0a73e5137016907f540e'
WARN='Warning: ieee_inexact is signaling'
STATUS_OK='C11CR2_CAP_RECORDS_RECOVERED__PHYSICAL_REVIEW_REQUIRED'
STATUS_BAD='C11CR2_RETAINED__CAP_RECORD_GAPS'

def blob(p):
    x=p.read_bytes()
    return hashlib.sha1(('blob '+str(len(x))+'\0').encode()+x).hexdigest()

def repair(log):
    lines=log.splitlines()
    repairs=[]
    for i,line in enumerate(lines):
        if not line.startswith('C11CAP ') or WARN not in line:
            continue
        prefix,sep,suffix=line.partition(WARN)
        a.need(sep and prefix.count('Warning:')==0 and not suffix.strip(),
               'UNEXPECTED_WARNING_FORM')
        tokens=prefix.split()[1:]
        a.need(3<=len(tokens)<8 and all(rec.NUM.fullmatch(t) for t in tokens)
               and all(rec.INT.fullmatch(t) for t in tokens[3:]),'CAP_PREFIX')
        j=i+1
        continuation=[]
        while len(tokens)<8:
            a.need(j<len(lines),'CAP_CONTINUATION_EOF')
            extra=lines[j].split()
            a.need(extra and all(rec.INT.fullmatch(t) for t in extra)
                   and len(tokens)+len(extra)<=8,'CAP_CONTINUATION_NOT_LITERAL_INTEGERS')
            tokens.extend(extra)
            continuation.append(lines[j])
            j+=1
        a.need(len(tokens)==8,'CAP_REPAIRED_WIDTH')
        a.need(j<len(lines) and lines[j].startswith('C11CAP '),'CAP_NEXT_RECORD_BOUNDARY')
        normalized='C11CAP '+' '.join(tokens)
        repairs.append({'first_line':i+1,'last_line':j,'original':[line]+continuation,
                        'normalized':normalized,'warning':WARN})
        lines[i]=normalized
        for k in range(i+1,j): lines[k]=''
    return '\n'.join(lines),repairs

def selftest():
    row='C11CAP 28000 52000 0 0 0 0'
    nextrow='C11CAP 0 28000 16000 1 0 0 0 51'
    for tail in ('    0  51','    0\n   51'):
        log=row+' '+WARN+'\n'+tail+'\n'+nextrow
        normalized,fix=repair(log)
        rows,bad,_=rec.parse_records(normalized)
        a.need(len(fix)==1 and len(rows['C11CAP'])==2 and not bad['C11CAP']
               and rows['C11CAP'][0][-2:]==['0','51'],'REPAIR_FIXTURE')
    try: repair(row+' '+WARN+'\n    0\n'+nextrow)
    except RuntimeError: pass
    else: raise RuntimeError('MISSING_TOKEN_ACCEPTED')
    try: repair(row+' '+WARN+'\n    0 51 7\n'+nextrow)
    except RuntimeError: pass
    else: raise RuntimeError('EXTRA_TOKEN_ACCEPTED')
    print('C11CR2_PARSER_SELFTEST_PASS',flush=True)

def main():
    selftest()
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    here=Path(__file__).resolve().parent
    for n,pin in [('arcana_c11a_assembly.py',r1.A_SCRIPT_PIN),
                  ('arcana_c11b_first_solve.py',r1.B_SCRIPT_PIN),
                  ('arcana_c11br1_convergence.py',c.R1_SCRIPT)]:
        a.need(a.sha(here/n)==pin,'RUNNER_HASH:'+n)
    a.need(blob(here/'arcana_c11c_sensitivity.py')==rec.C_BLOB and
           blob(here/'arcana_c11cr1_recover.py')==R1_REC_BLOB,'RECOVERY_RUNNER_PIN')
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA
           and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    retained=c10.OUT.with_name('R6_THERMO_C11C_SENSITIVITY_NEW01')
    prior=c10.OUT.with_name('R6_THERMO_C11CR1_RECOVERY_NEW01')
    baseline=c10.OUT.with_name('R6_THERMO_C11BR1_CONVERGENCE_NEW01')
    cm=c.verified(retained,rec.C_PIN,rec.C_STATUS)
    pm=c.verified(prior,R1_REC_PIN,R1_REC_STATUS)
    a.need(pm['source_sha']==a.SHA and pm['C11C_manifest_sha256']==rec.C_PIN
           and pm['C11BR1_manifest_sha256']==c.R1_PIN and pm['additional_native_solves']==0
           and all(pm[k]==v for k,v in c.SCOPE.items()),'RECOVERY_LINEAGE')
    p=a.read(prior/'C11CR1_CAMPAIGN_REPORT.json')
    a.need(set(p['cases'])==set(c.CASES) and all(
        v['mechanical_analysis']=='PASS' and v['control_readback']=='PASS' and
        v['cap_analysis']=='BLOCKED' and v['iterations']==rec.COUNTS[k]
        for k,v in p['cases'].items()),'PRIOR_MECHANICAL_RESULTS')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(x) for x in
          (root,retained,prior,baseline,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'RECOVERY_POLICY.json',{'parent_manifest':R1_REC_PIN,'native_campaign_manifest':rec.C_PIN,
        'runner_sha256':a.sha(Path(__file__)),'additional_native_solves':0,
        'policy':'Only reconstruct split records using literal adjacent integer tokens. No inferred numbers. Numerical screen unchanged.',**c.SCOPE})
    reports={}
    for case in c.CASES:
        print('C11CR2_CASE',case,flush=True)
        work=out/case; work.mkdir()
        old=p['cases'][case]
        report={k:v for k,v in old.items() if k not in ('parser','cap_error','caps','cap_analysis')}
        report['mechanical_source_sha256']=a.sha(prior/case/'MECHANICAL_ANALYSIS.json')
        report['cap_analysis']='BLOCKED'
        try:
            log=(retained/case/'run.log').read_text()
            rows,bad,_=rec.parse_records(log)
            a.need(len(rows['C11CAP'])==1791 and len(bad['C11CAP'])==1
                   and not bad['C11ZERO'] and len(rows['C11ZERO'])==0,'ORIGINAL_CAP_GAP')
            fixed,fixes=repair(log)
            a.need(len(fixes)==1 and fixes[0]['first_line']==bad['C11CAP'][0]['line'],
                   'REPAIR_PROVENANCE')
            a.write(work/'REPAIRED_RECORD_RECEIPT.json',{'source_log_sha256':a.sha(retained/case/'run.log'),
                'repairs':fixes})
            rows,bad,_=rec.parse_records(fixed)
            a.need(len(rows['C11CAP'])==1792 and not bad['C11CAP'],'COMPLETE_CAP_INVENTORY')
            cap=rec.caps_from_records(rows,bad)
            a.write(work/'CAP_ANALYSIS.json',cap)
            report['cap_analysis']='PASS'; report['caps']=cap
        except Exception as exc:
            report['cap_error']=rec.err(exc)
        reports[case]=report
        print(json.dumps({case:report},allow_nan=False),flush=True)
    status=STATUS_OK if all(r['cap_analysis']=='PASS' for r in reports.values()) else STATUS_BAD
    a.need(c.inventory(prior)==pm['files'] and a.sha(prior/'MANIFEST.json')==R1_REC_PIN
           and c.inventory(retained)==cm['files'] and a.sha(retained/'MANIFEST.json')==rec.C_PIN,
           'ARCHIVE_MUTATED')
    a.write(out/'C11CR2_CAMPAIGN_REPORT.json',{'status':status,'cases':reports,
        'physical_acceptance':False,'additional_native_solves':0,**c.SCOPE})
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'C11CR1_manifest_sha256':R1_REC_PIN,
        'C11C_manifest_sha256':rec.C_PIN,'additional_native_solves':0,'files':c.inventory(out),**c.SCOPE})
    print('C11CR2_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if status==STATUS_OK else 2

if __name__=='__main__':
    raise SystemExit(main())
