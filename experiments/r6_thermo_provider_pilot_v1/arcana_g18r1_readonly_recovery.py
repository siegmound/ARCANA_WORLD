#!/usr/bin/env python3
"""G18R1 read-only recovery of the retained direct CSR campaign.
No native build or execution. Recompute diagnostics from pinned original
files and independently replay archived linear systems. Never waive missing
or contradictory native/worker coverage evidence.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import traceback
import numpy as np
from scipy.sparse.linalg import splu
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8
import arcana_g10b_consumer_resolve as b10
import arcana_g16_scale_sparse_bridge as g16
import arcana_g17_live_sparse_nonlinear as g17
import arcana_g18_direct_csr as g18

PIN='9a6fe706529ab99c7dead031b265ab8e0de685b9373dc85d826449e2089763f5'
STATUS='G18_DIRECT_CSR_NONLINEAR_BLOCKED'
BLOB='218ab8ef44c973d928225959766c0fe0913776c8'

def coverage(work,n):
    expected=list(range(1,n+1))
    log=(work/'run.log').read_text()
    records=[json.loads(x) for x in (work/'G17_WORKER.jsonl').read_text().splitlines()]
    literal=log.count('G17_SPARSE_SOLVED ')
    # Parse numbered receipts, not substring count; permit whitespace
    # differences only. Unknown/malformed or duplicated markers fail closed.
    marker_lines=[x for x in log.splitlines() if 'G17_SPARSE_SOLVED' in x]
    native_ids=[]
    malformed=[]
    for line in marker_lines:
        m=re.fullmatch(r'\s*G17_SPARSE_SOLVED\s+([0-9]+)\s*',line)
        if m: native_ids.append(int(m.group(1)))
        else: malformed.append(line)
    checks={'worker_count':len(records)==n,
            'worker_sequence':[v['iteration'] for v in records]==expected,
            'native_numbered_receipts':native_ids==expected and not malformed}
    inventory={}
    for suffix in ('_sparse_request','_sparse_response.dat','_solution.dat','_pre.dat','_post.dat'):
        files=sorted(p.name for p in work.glob('iter_*'+suffix))
        names=[f'iter_{j:03d}'+suffix for j in expected]
        missing=sorted(set(names)-set(files)); extra=sorted(set(files)-set(names))
        inventory[suffix]={'count':len(files),'missing':missing,'extra':extra}
        checks[suffix]=not missing and not extra and len(files)==n
    return {'expected_iterations':n,'worker_record_count':len(records),
        'worker_ids':[v['iteration'] for v in records],
        'original_literal_marker_count':literal,'native_numbered_marker_count':len(native_ids),
        'native_ids':native_ids,'malformed_markers':malformed,'inventory':inventory,
        'checks':checks,'screen_pass':all(checks.values())},records

def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)
        for suffix in ('_sparse_request','_sparse_response.dat','_solution.dat','_pre.dat','_post.dat'):
            for j in (1,2): (p/(f'iter_{j:03d}'+suffix)).touch()
        (p/'G17_WORKER.jsonl').write_text('{"iteration":1}\n{"iteration":2}\n')
        (p/'run.log').write_text(' G17_SPARSE_SOLVED\t1\nG17_SPARSE_SOLVED      2\n')
        r,_=coverage(p,2)
        a.need(r['screen_pass'] and r['original_literal_marker_count']==1,'WHITESPACE_FIXTURE')
        (p/'run.log').write_text('G17_SPARSE_SOLVED 1\nG17_SPARSE_SOLVED 1\n')
        a.need(not coverage(p,2)[0]['screen_pass'],'DUPLICATE_FIXTURE')
        (p/'run.log').write_text('G17_SPARSE_SOLVED 1\nG17_SPARSE_SOLVED 2\n')
        (p/'iter_002_sparse_response.dat').unlink()
        a.need(not coverage(p,2)[0]['screen_pass'],'MISSING_RESPONSE_FIXTURE')
    print('G18R1_COVERAGE_SELFTEST_PASS',flush=True)

def audit_linear(work,records,n):
    lookup={}
    for rec in records:
        i=rec['iteration']
        a.need(type(i)==int and i not in lookup,'DUPLICATE_WORKER_RECORD')
        lookup[i]=rec
    metrics=[]; failures=[]
    for j in range(1,n+1):
        prefix=f'iter_{j:03d}'
        try:
            A,b=g18.read_sparse(work/(prefix+'_post.dat'))
            ans=r1.load_vector(work/(prefix+'_sparse_response.dat'),a)
            actual=r1.load_vector(work/(prefix+'_solution.dat'),a)
            fac=splu(A,permc_spec='COLAMD'); fresh=fac.solve(b)
            rec=lookup[j]
            backward=g16.backward(A,ans,b)
            reported=float(rec['backward'])
            seconds=float(rec['seconds_including_io'])
            d=g16.relative(ans,fresh)
            result={'iteration':j,'response_readback_exact':bool(np.array_equal(ans,actual)),
                'recomputed_backward':backward,'reported_backward':reported,
                'independent_sparse_replay_relative':d,'independent_sparse_replay_exact':bool(np.array_equal(ans,fresh)),
                'nnz_match':int(rec['nnz'])==A.nnz,'lu_nnz_match':int(rec['lu_nnz'])==fac.L.nnz+fac.U.nnz}
            result['screen_pass']=bool(result['response_readback_exact'] and result['nnz_match']
                and result['lu_nnz_match'] and np.isfinite(fresh).all() and np.isfinite(seconds) and seconds>=0
                and np.isfinite(reported) and 0<=reported<=g17.LIMIT and backward<=g17.LIMIT
                and d<=g17.FIELD_LIMIT)
            metrics.append(result)
        except Exception as exc:
            failures.append({'iteration':j,'error':repr(exc)})
    return {'screen_pass':len(metrics)==n and not failures and all(x['screen_pass'] for x in metrics),
        'iterations_audited':len(metrics),'failures':failures,'iterations':metrics,
        'max_backward':max((x['recomputed_backward'] for x in metrics),default=None),
        'max_replay_relative':max((x['independent_sparse_replay_relative'] for x in metrics),default=None)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-readonly-csr-recovery',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); selftest(); g8.check_helpers()
    for name,blob in [('arcana_g18_direct_csr.py',BLOB),
        ('arcana_g17_live_sparse_nonlinear.py','b553083798713e40b8998d40e3a81fbf94c218c1'),
        ('arcana_g16_scale_sparse_bridge.py','f39258ad725847e885ba44c8af188a42d74f10ce')]:
        a.need(g7.blob(Path(__file__).with_name(name))==blob,'HELPER_PIN:'+name)
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    refs=[('g18','R6_THERMO_G18_DIRECT_CSR_NEW01',PIN,STATUS),
        ('g17','R6_THERMO_G17_LIVE_SPARSE_NONLINEAR_NEW01',g18.G17_PIN,g18.G17_STATUS),
        ('g15','R6_THERMO_G15_MIDPOINT_COUPLING_NEW01',g16.G15_PIN,g16.G15_STATUS)]
    parents={}; manifests={}
    for k,name,pin,status in refs:
        p=c10.OUT.with_name(name); parents[k]=p; manifests[k]=c.verified(p,pin,status)
        a.need(manifests[k]['source_sha']==a.SHA and all(manifests[k][key]==v for key,v in c.SCOPE.items()),'PARENT_SCOPE')
    p=parents['g18']; prev=parents['g17']; work=p/'ultra'
    old=a.read(p/'G18_REPORT.json'); prior=a.read(parents['g15']/'G15_REPORT.json')
    a.need(manifests['g18']['G17_manifest_sha256']==g18.G17_PIN and
        manifests['g18']['G16_manifest_sha256']==g18.G16_PIN and
        manifests['g17']['G16_manifest_sha256']==g18.G16_PIN and
        old['error']['error']=="RuntimeError('WORKER_COVERAGE')" and
        old['native_exit']==old['worker_exit']==0 and old['assembly_parity']['screen_pass'] and
        prior['screen_pass'] and prior['accepted_checkpoint_sha256']==g16.CP_PIN,'SOURCE_LINEAGE')
    cp=parents['g15']/prior['accepted_checkpoint']
    import arcana_g11_adaptive_pilot as g11
    g11.load(cp,g16.CP_PIN)
    for name in (*g7.DECK,'regional.in',b10.SIDE):
        a.need(a.sha(cp/name)==a.sha(work/name)==a.sha(prev/'ultra'/name),'DECK:'+name)
    build=p/'build'; pb=prev/'build'
    g8.binary(build,'solve.exe',native); g8.binary(pb,'solve.exe',native)
    a.need((build/'MOD_Shells.f90').read_text()==g18.patch((pb/'MOD_Shells.f90').read_text()) and
        (build/'SHELLS_g7.f90').read_text()==g18.patch_entry((pb/'SHELLS_g7.f90').read_text()),'NATIVE_PATCH_REPLAY')
    ids=a.read(build/'BUILD_IDENTITY.json')['source_sha256']; pi=a.read(pb/'BUILD_IDENTITY.json')['source_sha256']
    a.need(set(ids)==set(pi) and all(ids[k]==pi[k] for k in ids if k not in ('MOD_Shells.f90','SHELLS_g7.f90')),'BUILD_DRIFT')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(q) for q in (root,c10.OUT,*parents.values())),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G18_manifest':PIN,'G17_manifest':g18.G17_PIN,
        'runner_sha256':a.sha(Path(__file__)),'scope':'Read-only recovery; numbered native receipts mandatory; no waiver for absent markers.',
        'linear_limit':g17.LIMIT,'field_limit':g17.FIELD_LIMIT,**c.SCOPE})
    report={'screen_pass':False,'additional_native_solves':0,'additional_builds':0,
        'additional_time_advance_years':0,'physical_acceptance':False,**c.SCOPE}
    try:
        log=(work/'run.log').read_text()
        a.need('C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' in log and
            not (work/'G17_WORKER_FAILED').exists() and log.count('G18_CSR_ALLOC ')==1,'NATIVE_TERMINATION')
        a.need(np.array_equal(np.loadtxt(work/'G18_GRAPH_READBACK.dat',dtype=int),
            np.loadtxt(work/'G18_GRAPH.dat',dtype=int,skiprows=1)),'GRAPH_READBACK')
        # Reconstruct original sparse graph from pinned FEG, independently.
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp); shutil.copyfile(work/'regional.feg',d/'regional.feg')
            graph=g18.stage_graph(d)
            a.need(a.sha(d/'G18_GRAPH.dat')==a.sha(work/'G18_GRAPH.dat'),'GRAPH_REPLAY')
        ctl=dict(a.read(cp/'package.json')['lr_native_parameters'],maxItr=g7.MAX_ITER,okToQt=g8.ULTRA)
        g7.controls_readback(log,ctl)
        n=int((work/'C11B_FINAL_REQUEST').read_text().split()[0])
        a.need(1<=n<=g7.MAX_ITER,'ITERATION_COUNT')
        cov,records=coverage(work,n); report['coverage']=cov
        a.write(out/'COVERAGE_DIAGNOSTIC.json',cov)
        print('G18R1_COVERAGE',json.dumps({k:v for k,v in cov.items() if k not in ('worker_ids','native_ids')}),flush=True)
        lr=audit_linear(work,records,n)
        a.write(out/'LINEAR_REPLAY.json',lr)
        report['linear_replay']={k:v for k,v in lr.items() if k!='iterations'}
        print('G18R1_LINEAR_REPLAY',json.dumps(report['linear_replay']),flush=True)
        # Recompute original mechanical checks in scratch. Never call analysis
        # on the original archive: it writes C11B_FINAL_STATE.npz.
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp); w=d/'ultra'; w.mkdir()
            for file in work.iterdir():
                if file.is_file() and file.name!='C11B_FINAL_STATE.npz':
                    (w/file.name).symlink_to(file)
            (d/'reference').symlink_to(p/'reference',target_is_directory=True)
            (d/g7.C10_NAME).symlink_to(p/g7.C10_NAME,target_is_directory=True)
            r1.MAX_ITER=g7.MAX_ITER; r1.NATIVE_TOL=g8.ULTRA
            matrix=a.matrix; a.matrix=g18.dense_for_audit
            try: ar=r1.analysis(w,d/'reference',a)
            finally: a.matrix=matrix
            a.need(g8.same_npz(w/'C11B_FINAL_STATE.npz',work/'C11B_FINAL_STATE.npz'),'FINAL_STATE_REPLAY')
            shutil.copyfile(w/'C11B_FINAL_STATE.npz',out/'C11B_FINAL_STATE.npz')
        a.write(out/'MECHANICAL_ANALYSIS.json',ar)
        parity=g18.assembly_parity(work,prev/'ultra',a.matrix)
        report['assembly_parity']=parity
        a.need(parity==old['assembly_parity'],'ASSEMBLY_RECEIPT_DRIFT')
        fields={}
        with np.load(cp/'mechanical.npz') as x,np.load(out/'C11B_FINAL_STATE.npz') as y,np.load(prev/'ultra/C11B_FINAL_STATE.npz') as z:
            for f in g7.FIELDS:
                d=g16.relative(x[f],y[f]); e=g16.relative(z[f],y[f])
                fields[f]={'relative_to_DGBSV':d,'relative_to_G17':e,
                    'exact_vs_G17':bool(np.array_equal(z[f],y[f])),'screen_pass':max(d,e)<=g17.FIELD_LIMIT}
        report['fields']=fields
        report['native_mechanics']={'iterations':len(ar['iterations']),'native_scoreB':ar['native_final_scoreB'],
            'residual':ar['final_free_relative_residual'],'work_defect':ar['work_balance_relative_defect'],
            'stress_refresh':ar['stress_refresh_relative_max_component'],'power_W':ar['quadrature_power_W'],
            'max_linear_backward':max(x['linear_backward_error'] for x in ar['iterations'])}
        report['numerical_screen_pass']=bool(ar['screen_pass'] and len(ar['iterations'])==n and
            max(report['native_mechanics'][k] for k in ('residual','work_defect','stress_refresh'))<=g7.FINE_SCREEN
            and parity['screen_pass'] and parity['matched_iterations']==n and all(x['screen_pass'] for x in fields.values())
            and lr['screen_pass'])
        report['screen_pass']=bool(report['numerical_screen_pass'] and cov['screen_pass'])
    except Exception as exc:
        report['screen_pass']=False
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    for k,_,pin,_ in refs:
        a.need(c.inventory(parents[k])==manifests[k]['files'] and a.sha(parents[k]/'MANIFEST.json')==pin,'PARENT_MUTATION:'+k)
    status=('G18R1_DIRECT_CSR_NONLINEAR_PARITY_PASS__GLOBAL_INPUT_AND_GAUGE_REQUIRED' if report['screen_pass']
        else 'G18R1_DIRECT_CSR_RECOVERY_RETAINED__COVERAGE_OR_NUMERICAL_GAP')
    report.update(status=status,limitations=[
        'Original G18 status unchanged; recovery uses archived data, not a new native solve.',
        'Numbered native log receipts required; missing/duplicate/contradictory receipts are not waived.',
        'Independent linear replays are diagnostic Python solves, not new native nonlinear solves.',
        'Regional no-fault code-2 case only; global material admission, gauge and physical T1 remain open.'])
    a.write(out/'G18R1_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G18_manifest_sha256':PIN,
        'G17_manifest_sha256':g18.G17_PIN,'files':c.inventory(out),**c.SCOPE})
    # Avoid flooding the terminal with iteration inventories; keep full report.
    concise=dict(report)
    if 'coverage' in concise: concise['coverage']={k:v for k,v in cov.items() if k not in ('worker_ids','native_ids')}
    print(json.dumps(concise,indent=2,allow_nan=False),flush=True)
    print('G18R1_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True); print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
