#!/usr/bin/env python3
"""Recover interleaved stdout bytes and verify retained computational receipts.
No factorization, solve, build, time advance, or historical status mutation.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g17_live_sparse_nonlinear as g17
import arcana_g18_direct_csr as g18
import arcana_g18r1_readonly_recovery as rec

PARENTS=(
 ('17_LIVE_SPARSE_NONLINEAR','0cb0b2610ebeecc78747e2fc89235018f618d44432e3f25d893ed6e7c9f928d1'),
 ('18_DIRECT_CSR','9a6fe706529ab99c7dead031b265ab8e0de685b9373dc85d826449e2089763f5'),
 ('18R1_READONLY_RECOVERY','3f00ddf6e90f68149a9cac1e06cfbc7e4fc12c3cc2fa74b7cd4a97f95eb92d04'),
 ('18R2_COVERAGE_ADJUDICATION','a2b609ae4b1f4a093e9ab645948991522b8074c2e19e79006a32a971a4bee353'),
 ('18R3_REFERENCE_AUDIT','f294108dc146f3507cd23a919ce28fd303e97b523ccafa0c7ab5e4a9f4e213f9'),
 ('31_CORRECTED_DIRECT_CSR','28ebbee110fa1e3e96f1842e7542deef6c26277cac9ee0ec535b3a267f9ee7fb'))

def recover_markers(log,n):
    # Remove only this observed compiler stderr block, with byte offsets/context.
    # The ID must survive in the original bytes; never infer it from sequence.
    pattern=r'Warning: ieee_inexact is signaling\n[ \t]+0\n'
    blocks=[{'offset':m.start(),'removed':m.group(),'context':log[max(0,m.start()-25):m.end()+25]}
            for m in re.finditer(pattern,log)]
    clean=re.sub(pattern,'',log)
    ids=[]; malformed=[]
    for line in clean.splitlines():
        if 'G17_SPARSE_SOLV' not in line: continue
        m=re.fullmatch(r'\s*G17_SPARSE_SOLVED\s+([0-9]+)\s*',line)
        if m: ids.append(int(m.group(1)))
        else: malformed.append(line)
    return {'screen_pass':len(blocks)==1 and not malformed and ids==list(range(1,n+1)),
            'ordered_ids':ids,'stderr_blocks':blocks,'malformed':malformed,
            'raw_stdout_unchanged':True,'reconstructed_view_only':True}

def verify(p,pin):
    m=g25.read(p/'MANIFEST.json')
    g25.need(g25.sha(p/'MANIFEST.json')==pin,'PIN:'+p.name)
    g25.need(g25.inventory(p)==m['files'],'INVENTORY:'+p.name)
    return m

def audit(p,n,csr):
    work=p/'ultra'; cov,records=rec.coverage(work,n)
    g25.need(all(v for k,v in cov['checks'].items() if k!='native_numbered_receipts'),'COVERAGE')
    recovered=recover_markers((work/'run.log').read_text(),n)
    checks=[]
    reader=g18.read_sparse if csr else g17.read_sparse
    for j,record in enumerate(records,1):
        prefix=work/f'iter_{j:03d}'
        A,b=reader(Path(str(prefix)+'_post.dat'))
        # Validate the pre-BC artifact with the actual codec as well.
        pre,pb=reader(Path(str(prefix)+'_pre.dat'))
        ans=g17.r1.load_vector(Path(str(prefix)+'_sparse_response.dat'),g17.a)
        native=g17.r1.load_vector(Path(str(prefix)+'_solution.dat'),g17.a)
        backward=g17.g16.backward(A,ans,b)
        row={'iteration':j,'request_bytes':Path(str(prefix)+'_sparse_request').stat().st_size,
             'response_readback_exact':bool(np.array_equal(ans,native)),
             'nnz_match':record['nnz']==A.nnz,'backward':backward,
             'reported_backward':record['backward'],'pre_finite':bool(np.isfinite(pre.data).all() and np.isfinite(pb).all())}
        row['screen_pass']=bool(row['request_bytes']==0 and row['response_readback_exact'] and row['nnz_match']
             and row['pre_finite'] and 0<=backward<=g17.LIMIT and 0<=record['backward']<=g17.LIMIT)
        checks.append(row)
    source=(p/'build/MOD_Shells.f90').read_text()
    solver=source[source.index('SUBROUTINE Solver ('):source.index('END SUBROUTINE Solver')]
    anchors=["//'_sparse_request'","//'_sparse_response.dat'",'g17_id,b(g17_j,1)',"PRINT '(A,I6)','G17_SPARSE_SOLVED ',g17_iter"]
    offsets=[solver.index(s) for s in anchors]
    ok=recovered['screen_pass'] and offsets==sorted(offsets) and all(x['screen_pass'] for x in checks)
    return {'screen_pass':ok,'iterations':n,'coverage':cov,'recovered_markers':recovered,
            'request_response_read_print_order_verified':offsets==sorted(offsets),'checks':checks}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--evidence',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); out=a.output.resolve(); evidence=a.evidence.resolve()
    g25.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE
             and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    parents=[(evidence/('R6_THERMO_G'+name+'_NEW01'),pin) for name,pin in PARENTS]
    before=[verify(p,pin) for p,pin in parents]
    g25.need(not out.exists() and not any(out.is_relative_to(p) or p.is_relative_to(out) for p,_ in parents),'OUTPUT')
    out.mkdir()
    results={name:audit(parents[i][0],n,csr) for name,i,n,csr in (('G17',0,258,False),('G18',1,258,True),('G31',5,264,True))}
    for name,data in results.items(): g25.write(out/(name+'_DOCUMENTARY.json'),data)
    g25.need([verify(p,pin) for p,pin in parents]==before,'PARENT_MUTATION')
    g25.need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    ok=all(x['screen_pass'] for x in results.values())
    report={'status':'G18R4_DOCUMENTARY_COVERAGE_PASS__HISTORICAL_FAILURES_PRESERVED' if ok else 'G18R4_DOCUMENTARY_BLOCKED',
         'screen_pass':ok,'parent_manifest_sha256':dict(PARENTS),'historical_status_rewritten':False,
         'additional_builds':0,'additional_solves':0,'additional_time_advance_years':0,
         'physical_acceptance':False,**g25.SCOPE}
    g25.write(out/'REPORT.json',report)
    g25.write(out/'MANIFEST.json',{'files':g25.inventory(out),'source_sha':g25.SOURCE,'runner_sha256':g25.sha(Path(__file__)),**report})
    print(json.dumps(report)); return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
