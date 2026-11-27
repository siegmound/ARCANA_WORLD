#!/usr/bin/env python3
"""G25: decompose native Fixed load using its four existing switches.
Replay one pinned G23 deck; stop before Pure, CSR assembly or equilibrium solve.
No force correction, physical admission, or time advance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import traceback
import numpy as np

SOURCE='901cbb4a38916190df6a881bb561b6558dd997dd'
PINS=('ddb51be4fb3e7d5a6e56f7caaa11f3861792a25239489b532e6350d726637abc',
      '7c18c82f80b7cf65f3bb5caa1158b81a297d89781bfbae2ddee01659465536a9')
STATUSES=('G23_CONDITIONAL_GLOBAL_CSR_ASSEMBLY_PASS__OPERATOR_AND_PHYSICAL_AUTHORITY_REQUIRED',
          'G24_OPERATOR_DIAGNOSTIC_PASS__LOAD_CLOSURE_REQUIRED')
AUTH='G25_FIXED_LOAD_DECOMPOSITION_ONLY_V1'
SCOPE={'physical_T1':None,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
       'D_024':'ACTIVE','D_025':'ACTIVE','scientific_promotion':False}
N=64442
LABELS=('FB1_TOPOGRAPHIC_STRESS','FB2_NORMAL_TRACTION_ANOMALY',
        'FB3_EXTERIOR_BOUNDARY','FB4_FAULT_PLANE')
DECK=('regional.feg','regional_PRE.dat','regional.in','controlled.bcs',
      'regional_reporting_plates.dat','runtime.control')
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def read(p): return json.loads(p.read_text())
def write(p,d):
    with p.open('x') as f: json.dump(d,f,indent=2,sort_keys=True,allow_nan=False); f.write('\n')
def inventory(p):
    return {str(x.relative_to(p)):sha(x) for x in sorted(p.rglob('*'))
            if x.is_file() and x!=p/'MANIFEST.json'}
def verify(p,j):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==PINS[j] and m['status']==STATUSES[j]
         and m['source_sha']==SOURCE and all(m[k]==v for k,v in SCOPE.items()),'PARENT_PIN:'+p.name)
    need(inventory(p)==m['files'],'PARENT_INVENTORY:'+p.name)
    return m

def generate(s):
    # Reuse the already executed G23 entry, including all pre-Pure guards.
    # Fixed explicitly supports separate evaluation using these four switches.
    start=s.index('       CALL Fixed (alphaT, area, conduc,')
    end=s.index('     &             fBase)                    ! output',start)+len('     &             fBase)                    ! output')
    call=s[start:end]
    need(s.count(call)==1,'FIXED_CALL_ANCHOR')
    cut='       dv = 0d0\n       dVLast = 0d0'
    need(s.count(cut)==1 and s.index(cut)>end,'PRE_PURE_ANCHOR')
    def dump(name):
        return f"""       open(76,file='{name}.dat',status='new',action='write')
       do i=1,numNod
         write(76,'(I8,2(1X,ES26.17E3))') i,fBase(2*i-1),fBase(2*i)
       end do
       close(76)
"""
    tail=dump('FIXED_FULL')
    for k,label in enumerate(LABELS):
        tail+= ''.join(f"       doFB{j+1} = {'.TRUE.' if j==k else '.FALSE.'}\n" for j in range(4))
        tail+=call+'\n'+dump(label)
        tail+=f"       print '(A)','G25_COMPONENT_READY {label}'\n"
    result=s.split(cut)[0]+tail+"""       print '(A)','G25_STOP_AFTER_FIXED_BEFORE_PURE'
       stop 0
end subroutine Shells_v5p0
end module SHELLS
"""
    need(len(re.findall(r'(?im)^\s*call\s+fixed\s*\(',result))==5,'FIXED_CALL_COUNT')
    need(not re.search(r'(?im)^\s*call\s+(pure|fem|solver|viscos|buildk|dgbsv)\b',result),'SOLVE_REACHABLE')
    return result

def build(old,new):
    meta=read(old/'BUILD_IDENTITY.json')
    argv=meta['argv']
    need(argv[-2:]==['-o','assembly_only.exe'] and '-O0' in argv and '-Mbounds' in argv and '-Kieee' in argv,'BUILD_FLAGS')
    compiler=Path(argv[0])
    need(sha(compiler)==meta['compiler_sha256'],'COMPILER_DRIFT')
    libs=[Path(x[2:]) for x in argv if x.startswith('-L')]
    need(len(libs)==1,'LIB_PATH')
    for name,pin in meta['library_sha256'].items():
        need(sha(libs[0]/name)==pin,'LIB_DRIFT:'+name)
    new.mkdir()
    for name,pin in meta['source_sha256'].items():
        need(Path(name).name==name and sha(old/name)==pin,'BUILD_SOURCE:'+name)
        shutil.copyfile(old/name,new/name)
    entry=new/'SHELLS_g7.f90'
    entry.write_text(generate(entry.read_text()))
    with (new/'build.log').open('x') as f:
        subprocess.run(argv,cwd=new,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/'assembly_only.exe'
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']}})
    return exe

def limit(): resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
def vector(p):
    x=np.loadtxt(p)
    need(x.shape==(N,3) and np.array_equal(x[:,0],np.arange(1,N+1)) and np.isfinite(x).all(),'VECTOR:'+p.name)
    return x[:,1:].ravel()
def metric(v,G):
    den=np.sum(abs(G)*abs(v[:,None]),axis=0)
    proj=G.T@v
    return {'norm_l2':float(np.linalg.norm(v)),'max_abs':float(np.max(abs(v))),
            'rotation_projection':proj.tolist(),
            'rotation_relative':(abs(proj)/np.maximum(den,1e-300)).tolist(),
            'rotation_absolute_sum':den.tolist()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--g23',type=Path,required=True); ap.add_argument('--g24',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-fixed-decomposition-only',choices=[AUTH],required=True)
    args=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,out=(x.resolve() for x in (args.g23,args.g24,args.output))
    manifests=[verify(p,0),verify(q,1)]
    need(manifests[1]['G23_manifest_sha256']==PINS[0],'PARENT_LINEAGE')
    need(not out.exists() and not any(out.is_relative_to(x) for x in (p,q,root)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':PINS[0],'G24_manifest_sha256':PINS[1],
            'additional_builds':0,'additional_fixed_load_runs':0,'additional_native_assemblies':0,
            'additional_native_solves':0,'additional_time_advance_years':0,'material_assignments':0,
            'load_modified':False,'physical_acceptance':False,'global_solve_authorized':False,**SCOPE}
    try:
        old=p/'native_diorite2'
        with np.load(old/'GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as f:
            G=f['rotation_candidates']; fixed=f['fixed_load']; rhs=f['rhs']; xyz=f['native_xyz']
        need(G.shape==(2*N,3) and fixed.shape==rhs.shape==(2*N,) and xyz.shape==(N,3)
             and all(np.isfinite(x).all() for x in (G,fixed,rhs,xyz)) and np.array_equal(rhs,fixed),'G23_FIXED')
        print('G25_BUILD_FIXED_ONLY',flush=True)
        exe=build(p/'build',out/'build'); report['additional_builds']=1
        work=out/'fixed_decomposition'; work.mkdir()
        for name in DECK: shutil.copyfile(old/name,work/name)
        print('G25_NATIVE_FIXED_DECOMPOSITION',flush=True)
        report['additional_fixed_load_runs']=1
        with (work/'run.log').open('x') as f:
            rc=subprocess.run(['/usr/bin/time','-v','-o','run.time',str(exe)],cwd=work,
                              stdout=f,stderr=subprocess.STDOUT,timeout=1200,preexec_fn=limit).returncode
        log=(work/'run.log').read_text()
        report['native_exit']=rc
        need(rc==0 and 'G25_STOP_AFTER_FIXED_BEFORE_PURE' in log and
             all('G25_COMPONENT_READY '+k in log for k in LABELS) and
             'G18_CSR_ALLOC' not in log and not (work/'FatalError.txt').exists(),'NATIVE_STOP')
        need(all(sha(work/n)==sha(old/n) for n in DECK),'DECK_MUTATION')
        geo=np.loadtxt(work/'G23_NATIVE_GEOMETRY.dat')
        oldgeo=np.loadtxt(old/'G23_NATIVE_GEOMETRY.dat')
        need(np.array_equal(geo,oldgeo),'GEOMETRY_REPLAY')
        full=vector(work/'FIXED_FULL.dat')
        terms=np.stack([vector(work/(k+'.dat')) for k in LABELS])
        combined=terms.sum(axis=0)
        scale=max(float(np.max(abs(fixed))),1e-300)
        replay=float(np.max(abs(full-fixed))/scale)
        reconstruction=float(np.max(abs(combined-full))/scale)
        report['replay']={'full_exact':bool(np.array_equal(full,fixed)),'relative_inf':replay,
                          'component_sum_relative_inf':reconstruction,'threshold':1e-12}
        report['full']=metric(full,G)
        report['components']={k:metric(v,G) for k,v in zip(LABELS,terms)}
        report['sum_minus_full']=metric(combined-full,G)
        report['exterior_and_fault_exact_zero']=bool(np.all(terms[2:]==0))
        owners=np.loadtxt(old/'regional_reporting_plates.dat',dtype=np.int64)
        need(owners.shape==(N,2) and np.array_equal(owners[:,0],np.arange(1,N+1)),'OWNERS')
        lat=np.rad2deg(np.arcsin(np.clip(xyz[:,2],-1,1)))
        lon=np.rad2deg(np.arctan2(xyz[:,1],xyz[:,0]))
        loc={}
        for label,v in zip(LABELS,terms):
            c=(G*v[:,None]).reshape(N,2,3).sum(axis=1)
            loc[label]={'by_plate':{str(i-2):c[owners[:,1]==i].sum(axis=0).tolist() for i in range(2,14)},
                        'top_nodes':[{'axis':a,'node_id':int(j+1),'lat_deg':float(lat[j]),
                                      'lon_deg':float(lon[j]),'plate':int(owners[j,1]-2),
                                      'projection':float(c[j,a])}
                                     for a in range(3) for j in np.argsort(abs(c[:,a]))[-10:][::-1]]}
        write(out/'COMPONENT_LOCALIZATION.json',loc)
        np.savez_compressed(out/'FIXED_COMPONENTS.npz',full=full,components=terms,labels=np.array(LABELS))
        report['screen_pass']=bool(replay<=1e-12 and reconstruction<=1e-12 and report['exterior_and_fault_exact_zero'])
        report['status']=('G25_FIXED_LOAD_DECOMPOSITION_PASS__PHYSICAL_TORQUE_AUTHORITY_REQUIRED'
                          if report['screen_pass'] else 'G25_FIXED_LOAD_DECOMPOSITION_RETAINED__REPLAY_OR_BOUNDARY_REVIEW')
    except Exception as e:
        report.update(screen_pass=False,status='G25_FIXED_LOAD_DECOMPOSITION_BLOCKED',
                      error=repr(e),traceback=traceback.format_exc())
    need(all(verify(x,j)==manifests[j] for j,x in enumerate((p,q))),'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G25_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,'G23_manifest_sha256':PINS[0],
          'G24_manifest_sha256':PINS[1],'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G25_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
