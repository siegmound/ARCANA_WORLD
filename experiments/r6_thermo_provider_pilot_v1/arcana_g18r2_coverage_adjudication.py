#!/usr/bin/env python3
"""G18R2 explicit evidence adjudication + global-input preflight.

Keep G18/G18R1 blocked status immutable. A narrow engineering acceptance
of computational coverage is separate from native stdout completeness.
No native execution, new material admission, or physical promotion.
"""
import argparse
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g16_scale_sparse_bridge as g16
import arcana_g17_live_sparse_nonlinear as g17
import arcana_g18_direct_csr as g18
import arcana_g18r1_readonly_recovery as rec

R1_PIN='3f00ddf6e90f68149a9cac1e06cfbc7e4fc12c3cc2fa74b7cd4a97f95eb92d04'
R1_STATUS='G18R1_DIRECT_CSR_RECOVERY_RETAINED__COVERAGE_OR_NUMERICAL_GAP'
POLICY='G18R2_COMPUTATIONAL_COVERAGE_WITH_ONE_RETAINED_STDOUT_GAP_V1'

def identify_gap(cov,n):
    ids=cov['native_ids']; expect=list(range(1,n+1))
    missing=sorted(set(expect)-set(ids))
    a.need(len(missing)==1 and ids==[i for i in expect if i not in missing]
           and not cov['malformed_markers']
           and cov['native_numbered_marker_count']==n-1
           and cov['original_literal_marker_count']==n-1,'STDOUT_NOT_SINGLE_OMISSION')
    a.need(set(cov['checks'])=={'worker_count','worker_sequence','native_numbered_receipts',
        '_sparse_request','_sparse_response.dat','_solution.dat','_pre.dat','_post.dat'}
        and not cov['checks']['native_numbered_receipts']
        and all(v for k,v in cov['checks'].items() if k!='native_numbered_receipts'),'OTHER_COVERAGE_GAP')
    return missing[0]

def selftest():
    checks={k:True for k in ('worker_count','worker_sequence','_sparse_request',
        '_sparse_response.dat','_solution.dat','_pre.dat','_post.dat')}
    checks['native_numbered_receipts']=False
    v={'native_ids':[1,3],'native_numbered_marker_count':2,'original_literal_marker_count':2,
       'malformed_markers':[],'checks':checks}
    a.need(identify_gap(v,3)==2,'GAP_FIXTURE')
    for bad in ([1,1],[3,1],[1,4],[1,2,3],[]):
        try: identify_gap(dict(v,native_ids=bad),3)
        except RuntimeError: continue
        raise RuntimeError('INVALID_RECEIPT_FIXTURE')
    print('G18R2_SINGLE_GAP_SELFTEST_PASS',flush=True)

def adjudicate(p,q,r):
    w=p/'ultra'; old=q/'ultra'
    report=a.read(r/'G18R1_REPORT.json')
    retained=a.read(p/'G18_REPORT.json')
    n=report['native_mechanics']['iterations']
    a.need(n==258 and not report['screen_pass'] and report['numerical_screen_pass']
        and not report['coverage']['screen_pass'] and retained['native_exit']==retained['worker_exit']==0
        and retained['error']['error']=="RuntimeError('WORKER_COVERAGE')",'SOURCE_RESULT')
    cov,_=rec.coverage(w,n)
    a.need(cov==report['coverage']==a.read(r/'COVERAGE_DIAGNOSTIC.json'),'COVERAGE_REPLAY_DRIFT')
    j=identify_gap(cov,n)
    # G17 is the independently qualified same-input live nonlinear reference.
    base,_=rec.coverage(old,n)
    a.need(base['screen_pass'],'G17_REFERENCE_COVERAGE')
    lin=a.read(r/'LINEAR_REPLAY.json')
    a.need(lin['screen_pass'] and lin['iterations_audited']==n and not lin['failures']
        and [x['iteration'] for x in lin['iterations']]==list(range(1,n+1))
        and all(x['screen_pass'] and x['response_readback_exact'] and
            x['independent_sparse_replay_exact'] and x['recomputed_backward']<=g17.LIMIT
            for x in lin['iterations']),'REPLAY_NOT_COMPLETE')
    a.need(report['linear_replay']=={k:v for k,v in lin.items() if k!='iterations'},'REPLAY_RECEIPT_DRIFT')
    par=report['assembly_parity']
    a.need(par==retained['assembly_parity'] and par['screen_pass'] and par['matched_iterations']==n
        and par['max_matched_iteration_matrix_rhs_relative']==0
        and all(x['exact'] for x in par['cases'].values()),'ASSEMBLY_NOT_EXACT')
    a.need(all(x['screen_pass'] for x in report['fields'].values())
        and g8.same_npz(w/'C11B_FINAL_STATE.npz',r/'C11B_FINAL_STATE.npz'),'FINAL_STATE_DRIFT')
    # Source-level ordering: the request is emitted inside Solver; the
    # solution dump is emitted after Solver returns in FEM. Confirm that
    # the archived native sources contain this exact instrumentation.
    native=(p/'build/MOD_Shells.f90').read_text()
    a.need(native==g18.patch((q/'build/MOD_Shells.f90').read_text()),'PATCH_DRIFT')
    solver=native[native.index('SUBROUTINE Solver ('):native.index('END SUBROUTINE Solver')]
    anchors=["//'_sparse_request'","//'_sparse_response.dat'","g17_id,b(g17_j,1)",
        "PRINT '(A,I6)','G17_SPARSE_SOLVED ',g17_iter"]
    positions=[solver.index(x) for x in anchors]
    a.need(positions==sorted(positions),'SOLVER_RECEIPT_ORDER')
    fem=native[native.index('SUBROUTINE FEM ('):native.index('END SUBROUTINE FEM')]
    # Verify source order with case-insensitive solver call, not comment.
    import re
    calls=list(re.finditer(r'(?im)^\s*CALL\s+Solver\s*\(',fem))
    a.need(len(calls)==1 and calls[0].start()<fem.index("//'_solution.dat'"),'FEM_SOLUTION_ORDER')
    exact_g17=0
    for i in range(1,n+1):
        prefix=f'iter_{i:03d}'
        ans=r1.load_vector(w/(prefix+'_sparse_response.dat'),a)
        act=r1.load_vector(w/(prefix+'_solution.dat'),a)
        oldans=r1.load_vector(old/(prefix+'_sparse_response.dat'),a)
        oldact=r1.load_vector(old/(prefix+'_solution.dat'),a)
        a.need(np.array_equal(ans,act) and np.array_equal(oldans,oldact),'NATIVE_READBACK')
        a.need(g16.relative(ans,oldans)<=g17.FIELD_LIMIT,'REFERENCE_RESPONSE_DRIFT')
        exact_g17+=int(np.array_equal(ans,oldans))
    pref=f'iter_{j:03d}'
    files={s:a.sha(w/(pref+s)) for s in ('_sparse_request','_sparse_response.dat','_solution.dat','_pre.dat','_post.dat')}
    ar=a.read(r/'MECHANICAL_ANALYSIS.json')
    a.need(ar['screen_pass'] and len(ar['iterations'])==n and
        [x['iteration'] for x in ar['iterations']]==list(range(1,n+1)),'MECHANICAL_RECEIPT')
    return {'policy':POLICY,'computational_coverage_pass':True,'native_stdout_complete':False,
        'native_stdout_gap_retained':True,'missing_iteration':j,'missing_iteration_file_sha256':files,
        'missing_iteration_linear_receipt':lin['iterations'][j-1],
        'matched_native_response_pairs':n,'exact_responses_vs_G17':exact_g17,
        'native_stdout_receipts':n-1,'original_gate_pass':False,
        'missing_stdout_cause':'UNDETERMINED','native_stdout_reconstructed':False,
        'regional_engineering_acceptance':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-computational-coverage-adjudication',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); selftest(); g8.check_helpers()
    for name,blob in [('arcana_g18r1_readonly_recovery.py','d27f9c811627fe3b50cfcff5f1f776728d61cf7f'),
        ('arcana_g18_direct_csr.py',rec.BLOB),
        ('arcana_g17_live_sparse_nonlinear.py','b553083798713e40b8998d40e3a81fbf94c218c1')]:
        a.need(g7.blob(Path(__file__).with_name(name))==blob,'HELPER_PIN:'+name)
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native,c09_mechanical_case as c09case
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g18','R6_THERMO_G18_DIRECT_CSR_NEW01',rec.PIN,rec.STATUS),
        ('g18r1','R6_THERMO_G18R1_READONLY_RECOVERY_NEW01',R1_PIN,R1_STATUS),
        ('g17','R6_THERMO_G17_LIVE_SPARSE_NONLINEAR_NEW01',g18.G17_PIN,g18.G17_STATUS)]
    parents={}; manifests={}
    for k,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[k]=p; manifests[k]=c.verified(p,pin,status)
        a.need(manifests[k]['source_sha']==a.SHA and all(manifests[k][x]==v for x,v in c.SCOPE.items()),'SCOPE')
    a.need(manifests['g18r1']['G18_manifest_sha256']==rec.PIN and
        manifests['g18r1']['G17_manifest_sha256']==g18.G17_PIN and
        manifests['g18']['G17_manifest_sha256']==g18.G17_PIN,'LINEAGE')
    for k in ('g18','g17'): g8.binary(parents[k]/'build','solve.exe',native)
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in (root,c10.OUT,c10.c09.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'policy':POLICY,'runner_sha256':a.sha(Path(__file__)),
        'original_gate_preserved':True,'new_gate':'One missing numbered stdout receipt only; all other artifacts, exact sparse replays and independent reference comparison mandatory.',
        'stdout_cause_claimed':False,'scope':'Regional engineering only. No retrospective alteration of G18/G18R1 or global physics.',**c.SCOPE})
    report={'screen_pass':False,'regional_engineering_acceptance':False,'native_stdout_complete':False,
        'additional_native_solves':0,'additional_builds':0,'additional_time_advance_years':0,
        'physical_acceptance':False,**c.SCOPE}
    try:
        print('G18R2_ADJUDICATE',flush=True)
        decision=adjudicate(parents['g18'],parents['g17'],parents['g18r1'])
        report['decision']=decision
        report['regional_engineering_acceptance']=decision['regional_engineering_acceptance']
        a.write(out/'COMPUTATIONAL_COVERAGE_DECISION.json',decision)
        print('G18R2_MISSING_NATIVE_STDOUT_ITERATION',decision['missing_iteration'],flush=True)
        # Begin G19 with a source-backed inventory, not invented admissions.
        print('G19_GLOBAL_INPUT_PREFLIGHT',flush=True)
        files=c10.verify_c09(c10.c09.OUT)
        global_result=c09case.global_route(root)
        retained=a.read(c10.c09.OUT/'REGIONAL_GLOBAL_ROUTE_COMPARISON.json')['global']
        a.need(json.loads(json.dumps(global_result,allow_nan=False))==retained,'GLOBAL_ROUTE_REPLAY')
        a.need(c10.verify_c09(c10.c09.OUT)==files,'C09_MUTATION')
        report['global_input_preflight']={'inventory_reproduced':True,
            'nodes':global_result['node_count'],'triangles':global_result['triangle_count'],
            'known_PRE_profiles':global_result['known_PRE_profiles'],
            'owner_domain_counts':global_result['owner_domain_counts'],
            'PRE_branch_counts':global_result['PRE_branch_counts'],
            'mixed_PRE_owner_records':global_result['mixed_PRE_owner_records'],
            'D12_admitted_cells':global_result['D12_admitted_cells'],
            'D12_unadmitted_cells':global_result['D12_unadmitted_cells'],
            'D12_cells_total':global_result['D12_cells_total'],
            'global_constitutive_authority_complete':False,'global_assembly_authorized':False,
            'global_solve_authorized':False,'D12_cell_scope':global_result['D12_scope'],
            'unclosed':global_result['unclosed']}
        a.write(out/'GLOBAL_INPUT_PREFLIGHT.json',global_result)
        report['screen_pass']=True
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for k,_,pin,_ in refs:
        a.need(c.inventory(parents[k])==manifests[k]['files'] and a.sha(parents[k]/'MANIFEST.json')==pin,'PARENT_MUTATION:'+k)
    status=('G18R2_COMPUTATIONAL_PARITY_ACCEPTED__STDOUT_GAP_RETAINED__GLOBAL_ADMISSION_REQUIRED'
            if report['screen_pass'] else 'G18R2_ADJUDICATION_OR_GLOBAL_PREFLIGHT_BLOCKED')
    report.update(status=status,limitations=[
        'New explicit engineering evidence criterion; original G18/G18R1 gate remains failed.',
        'One missing stdout receipt not reconstructed; actual cause remains unknown.',
        'Global source inventory only; nodal PRE coverage is not constitutive or D12 cell admission.',
        'No global assembly, physical T1, or production history authorization.'])
    a.write(out/'G18R2_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G18_manifest_sha256':rec.PIN,
        'G18R1_manifest_sha256':R1_PIN,'G17_manifest_sha256':g18.G17_PIN,
        'C09_manifest_sha256':c10.PIN,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G18R2_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
