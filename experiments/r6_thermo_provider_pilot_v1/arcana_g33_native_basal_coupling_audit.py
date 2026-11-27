#!/usr/bin/env python3
"""G33: native OneBar/THOnB constitutive audit and bounded rigid-mode sensitivity.
Two retained global decks, no active mantle field, CSR assembly or equilibrium solve.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import traceback
import numpy as np
import arcana_g32_corrected_global_operator as g32
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27

PIN='3a673638676ff21502c3e7275ef3ecd8e217f010ed49e48c25283a833d208a1e'
STATUS='G32_CORRECTED_GLOBAL_OPERATOR_PASS__PHYSICAL_CLOSURE_REQUIRED'
AUTH='G33_NATIVE_BASAL_CONSTITUTIVE_DIAGNOSTIC_ONLY_V1'
SOURCE,SCOPE=g25.SOURCE,g25.SCOPE
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
N,E,Q=g26.N,g26.E,g26.Q
YEAR=g27.YEAR
CAPS=(1e5,1e6,1e7)
SPEEDS=(.01,.1,1.,10.,100.)
TEST_CAP=1e6
TEST_ETA=1e17
DT=np.dtype([('ids','<i4',(2,)),('v','<f8',(8,))])
MODELS=('native_diorite2','native_legacy')

def patch_entry(s):
    decl='       INTEGER, DIMENSION(8) :: dateTimeNumber'
    cut='       dv = 0d0\n       dVLast = 0d0'
    need(s.count(decl)==1 and s.count(cut)==1,'ENTRY_ANCHORS')
    s=s.replace(decl,decl+'\n       INTEGER :: g33_m, g33_u',1)
    # Preserve all original pre-Pure guards, Fixed and geometry receipts.
    # Scratch arrays below are used only by this manufactured THOnB call.
    s=s.split(cut)[0]+"""       pulled = .TRUE.
       oVB(1,:,:) = 0.03D0 / 31557600.0D0
       oVB(2,:,:) = 0.04D0 / 31557600.0D0
       CALL THOnB (basal, continuum_LRi, &
     &              1.0D17, fPSfer, glue, iConve, &
     &              LRn, LR_set_eCreep, mxEl, mxNode, nodes, numEl, &
     &              oVB, pulled, 1.0D6, v, eta, sigHB, outVec)
       open(newunit=g33_u,file='G33_NATIVE_BASAL.bin',status='new', &
     &      access='stream',form='unformatted',action='write')
       do g33_m=1,7
         do i=1,numEl
           write(g33_u) i,g33_m,glue(g33_m,i),LR_set_eCreep(continuum_LRi(i)), &
     &        zMoho(g33_m,i),tLInt(g33_m,i),eta(g33_m,i), &
     &        sigHB(:,g33_m,i),zBAsth
         end do
       end do
       close(g33_u)
       print '(A)','G33_STOP_AFTER_THONB_BEFORE_PURE'
       stop 0
end subroutine Shells_v5p0
end module SHELLS
"""
    need(len(re.findall(r'(?im)^\s*call\s+thonb\s*\(',s))==1
         and not re.search(r'(?im)^\s*call\s+(pure|fem|solver|viscos|buildk|dgbsv)\b',s),'SOLVE_REACHABLE')
    return s

def build(old,new):
    meta=read(old/'BUILD_IDENTITY.json'); argv=meta['argv']
    need(argv[-2:]==['-o','assembly_only.exe'] and all(x in argv for x in ('-O0','-Mbounds','-Kieee')),'BUILD_FLAGS')
    need(sha(Path(argv[0]))==meta['compiler_sha256'] and sha(old/'assembly_only.exe')==meta['exe_sha256'],'COMPILER_OR_EXE')
    libs=[Path(x[2:]) for x in argv if x.startswith('-L')]
    need(len(libs)==1,'LIB_PATH')
    for n,pin in meta['library_sha256'].items(): need(sha(libs[0]/n)==pin,'LIB_DRIFT:'+n)
    new.mkdir()
    for n,pin in meta['source_sha256'].items():
        need(Path(n).name==n and sha(old/n)==pin,'SOURCE_DRIFT:'+n)
        shutil.copyfile(old/n,new/n)
    p=new/'SHELLS_g7.f90'; p.write_text(patch_entry(p.read_text()))
    need([n for n,pin in meta['source_sha256'].items() if sha(new/n)!=pin]==['SHELLS_g7.f90'],'PATCH_SCOPE')
    with (new/'build.log').open('x') as f:
        subprocess.run(argv,cwd=new,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/'assembly_only.exe'
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']}})
    return exe

def rel(x,y):
    return float(np.max(abs(x-y))/max(float(np.max(abs(y))),1e-300))

def distribution(x,w):
    j=np.argsort(x); c=np.cumsum(w[j])
    return {'min':float(x.min()),'max':float(x.max()),
            'area_weighted_quantiles':{str(k):float(x[j[min(np.searchsorted(c,k*c[-1]),len(j)-1)]])
                                       for k in (.01,.05,.5,.95,.99)}}

def geometry(p,q):
    with np.load(p/'native_diorite2/GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d:
        G=d['rotation_candidates']; b=d['rhs']; xyz=d['native_xyz']
    R=float(read(p/'native_diorite2/CONDITIONAL_CONTROLS.json')['radius'])
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    need(len(f)==Q and np.isfinite(f['v']).all(),'QUADRATURE')
    ids=f['ids']; v=f['v']
    need(np.array_equal(ids[:,0],np.tile(np.arange(1,E+1),7))
         and np.array_equal(ids[:,1],np.repeat(np.arange(1,8),E)),'IP_ORDER')
    nodes=ids[:,2:].astype(np.int64)-1
    need(nodes.min()>=0 and nodes.max()<N,'NODE_RANGE')
    w=v[:,0]*R
    need(np.all(w>0) and abs(w.sum()/(4*np.pi*R**2)-1)<1e-8,'AREA')
    phi=v[:,7:].reshape(Q,3,2,2).transpose(0,1,3,2)
    H=np.einsum('qnab,qnac->qbc',phi,G.reshape(N,2,3)[nodes])
    target=G.T@b
    need(np.linalg.norm(target)>0,'ZERO_TARGET')
    return ids[:,:2].copy(),w,H,target,R

def audit(work,old,geo):
    ids,w,H,target,R=geo
    ctl=read(old/'CONDITIONAL_CONTROLS.json')
    data=np.fromfile(work/'G33_NATIVE_BASAL.bin',dtype=DT)
    need(len(data)==Q and np.array_equal(data['ids'],ids) and np.isfinite(data['v']).all(),'NATIVE_QUADRATURE')
    glue,e,zc,zm,eta,tx,ty,zbase=data['v'].T
    need(np.all(glue>0) and np.all(e>0) and np.all(zc>0) and np.all(zm>=0) and np.all(zbase>0),'CONSTITUTIVE_SUPPORT')
    need(np.all(e==e[0]) and abs(float(e[0])-float(ctl['eCreep']))<1e-14,'EXPONENT_READBACK')
    need(np.all(zbase==zbase[0]) and abs(float(zbase[0])-float(ctl['zBAsth']))<1e-8,'DEPTH_READBACK')
    test=np.array([.03,.04])/YEAR
    vmag=np.linalg.norm(test)
    expected=np.minimum(np.minimum(glue*vmag**e,TEST_CAP),TEST_ETA*vmag)/vmag
    errors={'eta_relative_inf':rel(eta,expected),'south_traction_relative_inf':rel(tx,expected*test[0]),
            'east_traction_relative_inf':rel(ty,expected*test[1])}
    need(max(errors.values())<1e-12,'NATIVE_THONB_PARITY')
    mean_thick=float(np.average(zc+zm,weights=w))
    ref=float(ctl['refStr']); ok=float(ctl['okDelV'])
    need(ref>0 and ok>0,'LIMIT_CONTROLS')
    # Native Limits numerical cap, NOT an independently measured mantle viscosity.
    eta_base=ref*mean_thick/(R*ok)
    axis=target/np.linalg.norm(target)
    h=np.einsum('qba,a->qb',H,axis); hmag=np.linalg.norm(h,axis=1)
    scenarios=[]
    for cap in CAPS:
        cap_eta=min(eta_base,cap/ok)
        for speed in SPEEDS:
            vel=h*(speed*.01/YEAR); vmag=hmag*(speed*.01/YEAR)
            terms=np.stack((glue*vmag**e,np.full(Q,cap),cap_eta*vmag))
            active=np.argmin(terms,axis=0)
            mag=np.min(terms,axis=0)
            shear=-vel*np.divide(mag,vmag,out=np.zeros(Q),where=vmag>0)[:,None]
            torque=np.einsum('q,qba,qb->a',w,H,shear)
            diss=float(-np.einsum('q,qb,qb->',w,shear,vel))
            conj=float(-torque@axis*speed*.01/YEAR)
            frac=float(-torque@axis/np.linalg.norm(target))
            need(diss>0 and abs(diss-conj)/diss<1e-12,'DISSIPATION')
            scenarios.append({'traction_cap_Pa':cap,'native_limits_eta_cap_Pa_s_per_m':cap_eta,
                'rigid_equatorial_speed_cm_yr':speed,
                'opposing_torque_fraction_along_target':frac,
                'remaining_torque_relative_l2':float(np.linalg.norm(target+torque)/np.linalg.norm(target)),
                'transverse_torque_relative_l2':float(np.linalg.norm(torque-(torque@axis)*axis)/np.linalg.norm(target)),
                'area_fraction_active_limits':{k:float(w[active==i].sum()/w.sum()) for i,k in enumerate(('creep','traction_cap','eta_cap'))},
                'shear_traction_Pa':g27.qstats(shear,w),'dissipation_W':diss,
                'work_relative_error':abs(diss-conj)/diss})
    # Above/below LAB issue is part of the physical review, not an automatic rejection.
    return {'quadrature_points':Q,'native_exponent':float(e[0]),'native_zBAsth_m':float(zbase[0]),
        'glue_native_units_distribution':distribution(glue,w),
        'mean_lithosphere_thickness_m':mean_thick,
        'area_fraction_LAB_deeper_than_zBAsth':float(w[zc+zm>zbase].sum()/w.sum()),
        'native_manufactured_THOnB_parity':errors,'manufactured_speed_cm_yr':5.,
        'manufactured_cap_Pa':TEST_CAP,'manufactured_eta_cap_Pa_s_per_m':TEST_ETA,
        'native_limits_uncapped_eta_Pa_s_per_m':eta_base,'conditional_directional_scenarios':scenarios,
        'directional_scan_only':True,'mantle_velocity_provider_qualified':False,'physical_traction_authorized':False}

def main():
    ap=argparse.ArgumentParser()
    for k in ('g23','g26','g32','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-native-basal-diagnostic-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,r,out=(x.resolve() for x in (a.g23,a.g26,a.g32,a.output))
    parents=((p,lambda x:g25.verify(x,0)),(q,g27.verify),(r,lambda x:g32.verify(x,PIN,STATUS)))
    before=[fn(x) for x,fn in parents]
    need(before[2]['G23_manifest_sha256']==g25.PINS[0] and before[2]['G26_manifest_sha256']==g27.PIN,'LINEAGE')
    need(read(r/'G32_REPORT.json')['screen_pass'],'G32_SCREEN')
    need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,q,r)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':g27.PIN,
        'G32_manifest_sha256':PIN,'additional_builds':0,'native_constitutive_runs_attempted':0,
        'additional_native_assemblies':0,'additional_global_solves':0,'additional_time_advance_years':0,
        'material_assignments':0,'active_source_modified':False,'global_solve_authorized':False,
        'physical_acceptance':False,**SCOPE}
    try:
        print('G33_BUILD_NATIVE_CONSTITUTIVE_ONLY',flush=True)
        exe=build(r/'build',out/'build'); report['additional_builds']=1
        env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        for k in MODELS:
            work=out/k; work.mkdir()
            for n in g32.DECK: shutil.copyfile(p/k/n,work/n)
            need(read(work/'CONDITIONAL_CONTROLS.json')['iConve']==0,'ICONVE')
        print('G33_NATIVE_TWO_INDEPENDENT_CASES',flush=True)
        report['native_constitutive_runs_attempted']=2
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures={k:pool.submit(g32.g23.run,exe,out/k,env) for k in MODELS}
            exits={k:f.result() for k,f in futures.items()}
        report['native_exits']=exits
        geo=geometry(r,q); report['cases']={}
        for k in MODELS:
            work=out/k; old=p/k; log=(work/'run.log').read_text()
            need(exits[k]==0 and 'G33_STOP_AFTER_THONB_BEFORE_PURE' in log
                 and 'G18_CSR_ALLOC' not in log and not (work/'FatalError.txt').exists(),'NATIVE_STOP:'+k)
            need(all(sha(work/n)==sha(old/n) for n in g32.DECK),'DECK_MUTATION:'+k)
            need(sha(work/'G23_NATIVE_GEOMETRY.dat')==sha(old/'G23_NATIVE_GEOMETRY.dat'),'GEOMETRY:'+k)
            report['cases'][k]=audit(work,old,geo)
        report.update(screen_pass=True,status='G33_NATIVE_BASAL_CONSTITUTIVE_PASS__MANTLE_PROVIDER_AUTHORITY_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G33_NATIVE_BASAL_CONSTITUTIVE_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    need([fn(x) for x,fn in parents]==before,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G33_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
        'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':PIN,
        'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G33_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
