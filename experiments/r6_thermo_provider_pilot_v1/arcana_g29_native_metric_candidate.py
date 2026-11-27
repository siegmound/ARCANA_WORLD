#!/usr/bin/env python3
"""G29: isolated native Fixed metric candidate, global parity and manufactured controls.
No production patch, global assembly, equilibrium solve or physical admission.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27
import arcana_g28_spherical_metric_audit as g28

PIN='0472a6ef73157b5a8be66a1128df09eb455dff26911550062a17461c658a76d0'
STATUS='G28_SPHERICAL_METRIC_HYPOTHESIS_SUPPORTED__NATIVE_PARITY_REQUIRED'
AUTH='G29_NATIVE_METRIC_CANDIDATE_ONLY_V1'
N,E,Q=g28.N,g28.E,g28.Q
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
SOURCE,SCOPE=g25.SOURCE,g25.SCOPE
TESTS=('G29_CONSTANT_PRESSURE','G29_DEPTH_PRESSURE')
def verify(p):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==PIN and m['status']==STATUS and m['source_sha']==SOURCE
         and all(m[k]==v for k,v in SCOPE.items()),'G28_PIN_SCOPE')
    need(inventory(p)==m['files'],'G28_INVENTORY')
    need(m['G23_manifest_sha256']==g25.PINS[0] and m['G26_manifest_sha256']==g27.PIN
         and m['G27_manifest_sha256']==g28.PIN,'G28_LINEAGE')
    return m
def patch_fixed(s):
    start=s.index('SUBROUTINE Fixed ('); end=s.index('END SUBROUTINE Fixed',start)
    t=s[start:end]
    old='slopey = slopey + zA * dYSP(j, m, i)'
    need(t.count(old)==1 and t.count('sinA = SIN(sita(m, i))')==1,'METRIC_ANCHOR')
    t=t.replace(old,'slopey = slopey + zA * dYSP(j, m, i) / sinA',1)
    # Correct the coordinate derivative only; do not alter other callers or Deriv.
    return s[:start]+t+s[end:]
def patch_entry(s):
    start=s.index('       CALL Fixed (alphaT, area, conduc,')
    end=s.index('     &             fBase)                    ! output',start)+len('     &             fBase)                    ! output')
    call=s[start:end]
    anchor="       print '(A)','G25_STOP_AFTER_FIXED_BEFORE_PURE'"
    need(s.count(call)==5 and s.count(anchor)==1,'ENTRY_ANCHOR')
    tail="""       doFB1 = .FALSE.
       doFB2 = .TRUE.
       doFB3 = .FALSE.
       doFB4 = .FALSE.
"""
    for label,assign in zip(TESTS,(
        '       sigZZI(:,1:numEl) = 1.0D8\n',
        '       CALL Interp (elev, mxEl, mxNode, nodes, numEl, sigZZI)\n'
        '       sigZZI(:,1:numEl) = 3300.0D0*gMean* &\n'
        '            (zMoho(:,1:numEl)+tLInt(:,1:numEl)-sigZZI(:,1:numEl))\n')):
        tail+=assign+call+'\n'
        tail+=f"""       open(76,file='{label}.dat',status='new',action='write')
       do i=1,numNod
         write(76,'(I8,2(1X,ES26.17E3))') i,fBase(2*i-1),fBase(2*i)
       end do
       close(76)
       print '(A)','{label}_READY'
"""
    s=s.replace(anchor,tail+anchor,1)
    need(len(re.findall(r'(?im)^\s*call\s+fixed\s*\(',s))==7,'FIXED_CALL_COUNT')
    need(not re.search(r'(?im)^\s*call\s+(pure|fem|solver|viscos|buildk|dgbsv)\b',s),'SOLVE_REACHABLE')
    return s
def build(old,new):
    meta=read(old/'BUILD_IDENTITY.json'); argv=meta['argv']
    need(argv[-2:]==['-o','assembly_only.exe'] and all(k in argv for k in ('-O0','-Mbounds','-Kieee')),'BUILD_FLAGS')
    need(sha(Path(argv[0]))==meta['compiler_sha256'],'COMPILER_DRIFT')
    libs=[Path(x[2:]) for x in argv if x.startswith('-L')]
    need(len(libs)==1,'LIB_PATH')
    for n,pin in meta['library_sha256'].items(): need(sha(libs[0]/n)==pin,'LIB_DRIFT:'+n)
    new.mkdir()
    for n,pin in meta['source_sha256'].items():
        need(Path(n).name==n and sha(old/n)==pin,'SOURCE_DRIFT:'+n)
        shutil.copyfile(old/n,new/n)
    for n,fn in [('MOD_Shells.f90',patch_fixed),('SHELLS_g7.f90',patch_entry)]:
        p=new/n; p.write_text(fn(p.read_text()))
    changes=[n for n,pin in meta['source_sha256'].items() if sha(new/n)!=pin]
    need(set(changes)=={'MOD_Shells.f90','SHELLS_g7.f90'},'SOURCE_CHANGE_SCOPE')
    with (new/'build.log').open('x') as f:
        subprocess.run(argv,cwd=new,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/'assembly_only.exe'
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']},'changed_sources':changes})
    return exe
def compare(work,p,q,r,t):
    with np.load(p/'native_diorite2/GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d:
        G=d['rotation_candidates']; xyz=d['native_xyz']; rhs=d['rhs']
    with np.load(q/'FIXED_COMPONENTS.npz',allow_pickle=False) as d:
        need(list(d['labels'])==list(g25.LABELS),'LABELS')
        old=d['components']; fullold=d['full']
    with np.load(t/'G28_DIAGNOSTIC_LOADS.npz',allow_pickle=False) as d:
        expected=d['diagnostic_metric_FB2']; independent=d['independent_cartesian_FB2']
        need(np.array_equal(d['native_FB2'],old[1]) or g28.rel(d['native_FB2'],old[1])<1e-12,'G28_FB2_PARENT')
    need(G.shape==(2*N,3) and xyz.shape==(N,3) and old.shape==(4,2*N)
         and np.array_equal(fullold,rhs),'PARENT_FIELDS')
    terms=np.stack([g25.vector(work/(k+'.dat')) for k in g25.LABELS])
    full=g25.vector(work/'FIXED_FULL.dat')
    need(np.array_equal(terms[0],old[0]) and np.array_equal(terms[2:],old[2:]) and np.all(terms[2:]==0),'UNCHANGED_TERMS')
    err=g28.rel(terms[1],expected); indep=g28.rel(terms[1],independent)
    fullerr=g28.rel(full,rhs-old[1]+expected); sumerr=g28.rel(terms.sum(axis=0),full)
    need(max(err,indep,fullerr,sumerr)<1e-12,'ACTUAL_PARITY')
    f=np.fromfile(r/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    s=np.fromfile(r/'pressure_audit/SQUEEZ_PRESSURE.bin',dtype=g26.PD)
    need(len(f)==len(s)==Q and np.array_equal(f['ids'][:,2:],s['ids'])
         and np.array_equal(f['v'][:,4:7],s['v'][:,:3]),'QUADRATURE_JOIN')
    nodes=f['ids'][:,2:].astype(np.int64)-1
    need(nodes.min()>=0 and nodes.max()<N,'NODE_RANGE')
    v=f['v']; w=s['v']
    pos=np.einsum('qj,qji->qi',w[:,:3],xyz[nodes])
    st=np.hypot(pos[:,0],pos[:,1])/np.linalg.norm(pos,axis=1)
    need(np.all(st>0),'POLE_QUADRATURE')
    phi=v[:,7:].reshape(Q,3,2,2).transpose(0,1,3,2)
    coeff=-v[:,0,None,None]*np.einsum('qnab,qb->qna',phi,np.column_stack((v[:,2],v[:,3]/st)))
    z=w[:,4]-w[:,3]
    reporttests={}
    for label,pressure in zip(TESTS,(np.full(Q,1e8),3300*w[:,5]*z)):
        tmp=np.zeros((N,2))
        np.add.at(tmp,nodes.ravel(),(coeff*pressure[:,None,None]).reshape(-1,2))
        native=g25.vector(work/(label+'.dat'))
        parity=g28.rel(native,tmp.ravel())
        metric=g25.metric(native,G)
        need(parity<1e-11 and max(metric['rotation_relative'])<1e-10,'MANUFACTURED_PARITY:'+label)
        reporttests[label]={'relative_inf_vs_retained_python':parity,'native':metric}
    radius=float(read(p/'native_diorite2/CONDITIONAL_CONTROLS.json')['radius'])
    np.savez_compressed(work.parent/'G29_CANDIDATE_FIXED_COMPONENTS.npz',full=full,components=terms,labels=np.array(g25.LABELS))
    return {'native_FB2_vs_G28_metric_relative_inf':err,'native_FB2_vs_cartesian_relative_inf':indep,
            'full_candidate_vs_G28_prediction_relative_inf':fullerr,'decomposition_relative_inf':sumerr,
            'FB1_FB3_FB4_exact_unchanged':True,'manufactured_tests':reporttests,
            'native_candidate_FB2':g25.metric(terms[1],G),'native_candidate_full':g25.metric(full,G),
            'candidate_full_torque_reference_radius_Nm':(radius*(G.T@full)).tolist(),
            'candidate_full_relative_change_l2':float(np.linalg.norm(full-rhs)/np.linalg.norm(rhs)),
            'regional_regression_complete':False,'physical_torque_closure_complete':False}
def main():
    ap=argparse.ArgumentParser()
    for k in ('g23','g25','g26','g27','g28','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-native-metric-candidate-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,r,s,t,out=(x.resolve() for x in (a.g23,a.g25,a.g26,a.g27,a.g28,a.output))
    parents=((p,lambda x:g25.verify(x,0)),(q,g26.verify),(r,g27.verify),(s,g28.verify),(t,verify))
    before=[fn(x) for x,fn in parents]
    need(not out.exists() and not any(out.is_relative_to(x) for x in (p,q,r,s,t,root)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G25_manifest_sha256':g26.PIN,
            'G26_manifest_sha256':g27.PIN,'G27_manifest_sha256':g28.PIN,'G28_manifest_sha256':PIN,
            'additional_builds':0,'additional_fixed_load_runs':0,'additional_native_assemblies':0,
            'additional_native_solves':0,'additional_time_advance_years':0,'material_assignments':0,
            'active_source_modified':False,'load_modified':False,'candidate_load_generated':False,
            'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        print('G29_BUILD_ISOLATED_METRIC_CANDIDATE',flush=True)
        exe=build(q/'build',out/'build'); report['additional_builds']=1
        work=out/'metric_candidate'; work.mkdir(); prev=q/'fixed_decomposition'
        for n in g25.DECK: shutil.copyfile(prev/n,work/n)
        print('G29_NATIVE_FIXED_AND_MANUFACTURED_TESTS',flush=True)
        report['additional_fixed_load_runs']=1
        with (work/'run.log').open('x') as f:
            rc=subprocess.run(['/usr/bin/time','-v','-o','run.time',str(exe)],cwd=work,
                stdout=f,stderr=subprocess.STDOUT,timeout=1200,preexec_fn=g25.limit).returncode
        log=(work/'run.log').read_text(); report['native_exit']=rc
        need(rc==0 and 'G25_STOP_AFTER_FIXED_BEFORE_PURE' in log and 'G18_CSR_ALLOC' not in log
             and all(k+'_READY' in log for k in TESTS) and not (work/'FatalError.txt').exists(),'NATIVE_STOP')
        need(all(sha(work/n)==sha(prev/n) for n in g25.DECK),'DECK_MUTATION')
        need(sha(work/'G23_NATIVE_GEOMETRY.dat')==sha(prev/'G23_NATIVE_GEOMETRY.dat'),'GEOMETRY_REPLAY')
        report['audit']=compare(work,p,q,r,t)
        report.update(screen_pass=True,candidate_load_generated=True,
            status='G29_NATIVE_GLOBAL_METRIC_PARITY_PASS__REGIONAL_AND_TORQUE_REVIEW_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G29_NATIVE_METRIC_CANDIDATE_BLOCKED',
                      error=repr(e),traceback=traceback.format_exc())
    need([fn(x) for x,fn in parents]==before,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G29_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
        'G28_manifest_sha256':PIN,'G25_manifest_sha256':g26.PIN,'runner_sha256':sha(Path(__file__)),
        'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G29_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
