#!/usr/bin/env python3
"""C11C-R1: read-only recovery of the retained C11C campaign.
No native executable invocation, build, physics change or extra solve.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c

C_PIN='cf174de3ba1edef2168e65cc0208e1367db5e2d516efa1887356e0b893326750'
C_STATUS='C11C_SENSITIVITY_CAMPAIGN_RETAINED__BLOCKED'
C_BLOB='822ea9f80d4c1b1a0f820f8e6c2d44b9073dd41b'
COUNTS={'S0':79,'S1':82,'S2':133,'S3':79,'S4':80,'S5':80,'S6':103}
NUM=re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?\Z')
MARK=re.compile(r'\b(C11C_CONTROLS|C11CAP|C11ZERO)\b')
INT=re.compile(r'[+-]?\d+\Z')

def parse_records(log):
    """Accept complete typed records; tolerate explicit trailing warnings only.
    Never reconstruct missing numbers or silently discard malformed records.
    """
    rows={k:[] for k in ('C11C_CONTROLS','C11CAP','C11ZERO')}
    malformed={k:[] for k in rows}
    tails=[]
    widths={'C11C_CONTROLS':5,'C11CAP':8,'C11ZERO':2}
    lines=log.splitlines()
    for i,line in enumerate(lines):
        m=MARK.search(line)
        if not m: continue
        key=m.group(1); rest=line[m.end():].split()
        n=widths[key]; tokens=rest[:n]; tail=rest[n:]
        valid=(len(tokens)==n and all(NUM.fullmatch(t) for t in tokens))
        if valid:
            ints=[0] if key=='C11C_CONTROLS' else list(range(3,8)) if key=='C11CAP' else [0,1]
            valid=all(INT.fullmatch(tokens[j]) for j in ints)
        if valid and (not tail or re.match(r'(?i)^(warning:|fortran warning:|nvfortran-warning)', ' '.join(tail))):
            rows[key].append([t.replace('D','E').replace('d','e') for t in tokens])
            if tail: tails.append({'line':i+1,'marker':key,'tail':' '.join(tail)[:300]})
        else:
            malformed[key].append({'line':i+1,'context':[x[:500] for x in lines[max(0,i-1):i+2]]})
    return rows,malformed,tails

def verify_controls(rows,bad,ctl):
    a.need(not bad['C11C_CONTROLS'] and len(rows['C11C_CONTROLS'])==1,'CONTROL_RECORD_INCOMPLETE')
    want=[250,ctl['okToQt'],ctl['okDelV'],ctl['Biot'],ctl['zBAsth']]
    a.need(np.allclose(np.array(rows['C11C_CONTROLS'][0],float),want,rtol=1e-13,atol=0),'CONTROL_READBACK_DRIFT')

def caps_from_records(rows,bad):
    a.need(not bad['C11CAP'] and not bad['C11ZERO'],'CAP_RECORD_INCOMPLETE')
    # Use the original C11C inventory and range checks unchanged.
    clean='\n'.join(k+' '+' '.join(row) for k in ('C11CAP','C11ZERO') for row in rows[k])
    return c.cap_report(clean)

def err(exc):
    return {'error':repr(exc),'traceback':traceback.format_exc()}

def main():
    from experiments.r6_thermo_provider_pilot_v1 import c10_native as native
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    here=Path(__file__).resolve().parent
    for n,pin in [('arcana_c11a_assembly.py',r1.A_SCRIPT_PIN),
                  ('arcana_c11b_first_solve.py',r1.B_SCRIPT_PIN),
                  ('arcana_c11br1_convergence.py',c.R1_SCRIPT)]:
        a.need(a.sha(here/n)==pin,'RUNNER_HASH:'+n)
    raw=(here/'arcana_c11c_sensitivity.py').read_bytes()
    a.need(hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()==C_BLOB,'C11C_BLOB')
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA
        and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    parent=c10.OUT.with_name('R6_THERMO_C11A_OPERATOR_ASSEMBLY_NEW01')
    b=c10.OUT.with_name('R6_THERMO_C11B_FIRST_CONTROLLED_SOLVE_NEW01')
    baseline=c10.OUT.with_name('R6_THERMO_C11BR1_CONVERGENCE_NEW01')
    retained=c10.OUT.with_name('R6_THERMO_C11C_SENSITIVITY_NEW01')
    c.verified(parent,r1.A_PIN,r1.A_STATUS)
    c.verified(b,r1.B_PIN,r1.B_STATUS)
    rm=c.verified(baseline,c.R1_PIN,c.R1_STATUS)
    cm=c.verified(retained,C_PIN,C_STATUS)
    a.need(cm['source_sha']==a.SHA and cm['C11BR1_manifest_sha256']==c.R1_PIN
        and all(cm[k]==v for k,v in c.SCOPE.items()),'C11C_LINEAGE')
    a.need(rm['source_sha']==a.SHA and rm['physical_solves']==1,'R1_LINEAGE')
    a.need(a.read(baseline/'C11BR1_ANALYSIS.json')['screen_pass'] is True,'R1_SCREEN')
    orig=a.read(retained/'C11C_CAMPAIGN_REPORT.json')
    a.need(set(orig['cases'])==set(COUNTS) and all(
        orig['cases'][k]['completed_linear_solves']==v and
        orig['cases'][k]['status']=='EXECUTION_OR_DIAGNOSTIC_ERROR'
        for k,v in COUNTS.items()),'RETAINED_CASE_RECEIPTS')
    m=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and all(m[k]==v for k,v in c10.SCOPE.items()),'C10_SCOPE')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==m['files'],'C10_INVENTORY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in
        (root,c10.OUT,parent,b,baseline,retained)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'RECOVERY_POLICY.json',{'C11C_manifest':C_PIN,'R1_manifest':c.R1_PIN,
        'runner_sha256':a.sha(Path(__file__)),'additional_native_solves':0,
        'additional_builds':0,'original_screens_unchanged':True,
        'parse_policy':'Strict complete numeric records, explicit trailing warning tolerated, incomplete rows blocked; original archive untouched.',
        **c.SCOPE})
    pkg=c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json'
    package_dir=out/c10.OUT.name; package_dir.mkdir()
    shutil.copyfile(pkg,package_dir/pkg.name)
    a.need(a.sha(pkg)==a.sha(retained/c10.OUT.name/pkg.name),'RETAINED_PACKAGE_DRIFT')
    controls0=a.read(pkg)['lr_native_parameters']
    fields=('velocity','strain_rate','tau_relative','reaction')
    reports={}
    with np.load(baseline/'C11B_FINAL_STATE.npz') as base:
        for case,(change,bcfile,kind) in c.CASES.items():
            print('C11CR1_RECOVER',case,flush=True)
            src=retained/case; work=out/case; work.mkdir()
            ctl=dict(controls0,maxItr=250,okToQt=5e-7); ctl.update(change)
            summary={'kind':kind,'mechanical_analysis':'NOT_RUN','cap_analysis':'NOT_RUN',
                     'additional_native_solves':0}
            try:
                a.need(a.read(src/'CASE_POLICY.json')['controls']==ctl,'CASE_CONTROL_DRIFT')
                a.need((src/'regional.in').read_bytes()==native.serialize_lr(ctl).encode(),'LR_DECK_DRIFT')
                for n in ('regional.feg','regional_PRE.dat','runtime.control','regional_reporting_plates.dat'):
                    a.need(a.sha(src/n)==a.sha(c10.OUT/n),'CASE_INPUT_DRIFT:'+n)
                a.need(a.sha(src/'controlled.bcs')==a.sha(c10.OUT/bcfile),'BC_DECK_DRIFT')
                build=a.read(src/'BUILD_IDENTITY.json')
                a.need(a.sha(src/'controlled_solve.exe')==build['exe_sha256'] and
                    all(a.sha(src/n)==h for n,h in build['source_sha256'].items()),'BUILD_IDENTITY')
                log=(src/'run.log').read_text()
                a.need('C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in log and
                    not (src/'FatalError.txt').exists() and
                    re.search(r'(?m)^\s*Exit status:\s*0\s*$',(src/'run.time').read_text()),'NATIVE_STOP_RECEIPT')
                rows,bad,tails=parse_records(log)
                diagnostics={'record_counts':{k:len(v) for k,v in rows.items()},
                    'malformed_counts':{k:len(v) for k,v in bad.items()},
                    'malformed_examples':{k:v[:3] for k,v in bad.items()},
                    'explicit_warning_suffix_count':len(tails),'warning_suffix_examples':tails[:3],
                    'standalone_warning_examples':[l[:400] for l in log.splitlines() if 'Warning:' in l][:5]}
                a.write(work/'PARSER_DIAGNOSTICS.json',diagnostics)
                summary['parser']=diagnostics
                # Mechanical analysis and cap parsing are independent, so a cap
                # logging fault cannot suppress the mechanically valid fields.
                try:
                    verify_controls(rows,bad,ctl)
                    summary['control_readback']='PASS'
                except Exception as e:
                    summary['control_readback']='BLOCKED'; summary['control_error']=err(e)
                for pattern in ('iter_*_pre.dat','iter_*_post.dat','iter_*_solution.dat'):
                    members=sorted(src.glob(pattern))
                    a.need(len(members)==COUNTS[case],'ITERATION_MEMBER_COUNT:'+pattern)
                    for p in members: shutil.copyfile(p,work/p.name)
                for n in ('final_pre.dat','final_post.dat','final_nodes.dat','final_ip.dat',
                          'prior_refresh_stress.dat','C11B_FINAL_REQUEST'):
                    shutil.copyfile(src/n,work/n)
                ref=out/('reference_'+case)
                c.reference(ref,c10.OUT,parent,case,ctl,bcfile)
                r1.NATIVE_TOL=ctl['okToQt']
                report=r1.analysis(work,ref,a)
                a.need(len(report['iterations'])==COUNTS[case],'ITERATION_REPLAY')
                comparison={}
                with np.load(work/'C11B_FINAL_STATE.npz') as state:
                    for f in fields:
                        x,y=state[f],base[f]
                        a.need(x.shape==y.shape,'FIELD_SHAPE:'+f)
                        comparison[f]={'relative_max':r1.ratio(float(np.max(abs(x-y))),max(float(np.max(abs(x))),float(np.max(abs(y))))),
                            'relative_L2':r1.ratio(float(np.linalg.norm(x-y)),max(float(np.linalg.norm(x)),float(np.linalg.norm(y)))),
                            'absolute_max':float(np.max(abs(x-y)))}
                invariant=all(v['relative_max']<=1e-10 for v in comparison.values()) if case in ('S0','S3') else None
                report['baseline_field_comparison']=comparison; report['invariance_screen']=invariant
                report['additional_native_solves']=0
                summary.update(mechanical_analysis='PASS' if report['screen_pass'] and invariant is not False else 'BLOCKED',
                    iterations=len(report['iterations']),residual=report['final_free_relative_residual'],
                    work_defect=report['work_balance_relative_defect'],stress_refresh=report['stress_refresh_relative_max_component'],
                    free_cond2=report['final_free_rank']['cond2'],max_speed_m_s=report['max_final_speed_m_s'],
                    max_strain_s_inv=report['max_strain_component_s_inv'],power_W=report['quadrature_power_W'],
                    fields=comparison,invariance_screen=invariant)
                a.write(work/'MECHANICAL_ANALYSIS.json',report)
                try:
                    cap=caps_from_records(rows,bad)
                    a.write(work/'CAP_ANALYSIS.json',cap)
                    summary['cap_analysis']='PASS'; summary['caps']=cap
                except Exception as e:
                    summary['cap_analysis']='BLOCKED'; summary['cap_error']=err(e)
            except Exception as e:
                summary['mechanical_analysis']='BLOCKED'; summary['recovery_error']=err(e)
            reports[case]=summary
            print(json.dumps({case:summary},allow_nan=False),flush=True)
    success=all(x['mechanical_analysis']=='PASS' and x.get('control_readback')=='PASS'
                and x['cap_analysis']=='PASS' for x in reports.values())
    status='C11CR1_RECOVERED_SENSITIVITY_NUMERICAL_SCREEN_PASS__PHYSICAL_REVIEW_REQUIRED' if success else 'C11CR1_RECOVERY_RETAINED__DIAGNOSTIC_GAPS'
    a.need(c.inventory(retained)==cm['files'] and a.sha(retained/'MANIFEST.json')==C_PIN,'RETAINED_ARCHIVE_MUTATED')
    a.write(out/'C11CR1_CAMPAIGN_REPORT.json',{'status':status,'cases':reports,
        'physical_acceptance':False,'additional_native_solves':0,**c.SCOPE})
    a.write(out/'MANIFEST.json',{'status':status,'C11C_manifest_sha256':C_PIN,
        'C11BR1_manifest_sha256':c.R1_PIN,'source_sha':a.SHA,'additional_native_solves':0,
        'files':c.inventory(out),**c.SCOPE})
    print('C11CR1_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if success else 2

if __name__=='__main__':
    raise SystemExit(main())
