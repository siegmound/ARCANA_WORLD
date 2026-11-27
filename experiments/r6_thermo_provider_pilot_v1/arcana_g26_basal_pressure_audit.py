#!/usr/bin/env python3
"""G26: instrument retained Fixed/Squeez, replay FB2 and split pressure provenance.
Counterfactual shared reference is a sensitivity only; never applied to the model.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25

PIN='ff8e3298f73e429649eb78015785b41385228403f651d6500c4271e332cf4917'
STATUS='G25_FIXED_LOAD_DECOMPOSITION_PASS__PHYSICAL_TORQUE_AUTHORITY_REQUIRED'
AUTH='G26_BASAL_PRESSURE_PROVENANCE_ONLY_V1'
N=g25.N
E=128880
Q=7*E
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
SCOPE=g25.SCOPE
SOURCE=g25.SOURCE
FD=np.dtype([('ids','<i4',(5,)),('v','<f8',(19,))])
PD=np.dtype([('ids','<i4',(3,)),('v','<f8',(12,))])

def replace(s,a,b):
    need(s.count(a)==1,'ANCHOR:'+a[:100])
    return s.replace(a,b,1)

def patch_fixed(s):
    a=s.index('SUBROUTINE Fixed ('); b=s.index('END SUBROUTINE Fixed',a)
    t=s[a:b]
    t=replace(t,'INTEGER arcana_node_ids(3), arcana_ierr',
              'INTEGER arcana_node_ids(3), arcana_ierr, g26_unit\nLOGICAL g26_dump')
    t=replace(t,'IF (doFB1.OR.doFB2) THEN',"""g26_dump=doFB2 .and. .not.doFB1 .and. .not.doFB3 .and. .not.doFB4
IF (g26_dump) OPEN(newunit=g26_unit,file='FB2_QUADRATURE.bin', &
   access='stream',form='unformatted',status='new',action='write')
IF (doFB1.OR.doFB2) THEN""")
    t=replace(t,'20                 CONTINUE',"""20                 CONTINUE
              IF (g26_dump) WRITE(g26_unit) i,m,nodes(:,i),dArea,sigZZI(m,i), &
                   slopex,slopey,points(:,m),fPSfer(:,:,:,m,i)""")
    t=replace(t,'END IF ! (doFB1.OR.doFB2)',"""END IF ! (doFB1.OR.doFB2)
IF (g26_dump) CLOSE(g26_unit)""")
    return s[:a]+t+s[b:]

def patch_runtime(s):
    a=s.index('  SUBROUTINE ArcanaRuntimeSqueez('); b=s.index('  END SUBROUTINE ArcanaRuntimeSqueez',a)
    t=s[a:b]
    t=replace(t,'    INTEGER :: i,n_step,last_dr,n1,n2,phase(3),sample_ierr',
              '    INTEGER :: i,n_step,last_dr,n1,n2,phase(3),sample_ierr\n    INTEGER, SAVE :: g26_unit=0')
    t=replace(t,'    ierr = 0\n',"""    IF (node_ids(1)/=node_ids(2) .AND. node_ids(1)/=node_ids(3) .AND. node_ids(2)/=node_ids(3)) THEN
       IF (g26_unit==0) OPEN(newunit=g26_unit,file='SQUEEZ_PRESSURE.bin', &
            access='stream',form='unformatted',status='new',action='write')
       WRITE(g26_unit) node_ids,weights,elevat,z_stop,g_mean,one_km, &
            rho_water,rho_asth,rhotop,pr,sig_zzb
    END IF
    ierr = 0
""")
    return s[:a]+t+s[b:]

def verify(p):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==PIN and m['status']==STATUS and m['source_sha']==SOURCE
         and all(m[k]==v for k,v in SCOPE.items()),'G25_PIN_SCOPE')
    need(inventory(p)==m['files'],'G25_INVENTORY')
    need(m['G23_manifest_sha256']==g25.PINS[0] and m['G24_manifest_sha256']==g25.PINS[1],'LINEAGE')
    return m

def build(old,new):
    meta=read(old/'BUILD_IDENTITY.json'); argv=meta['argv']
    need(argv[-2:]==['-o','assembly_only.exe'] and '-O0' in argv and '-Mbounds' in argv
         and '-Kieee' in argv,'BUILD_FLAGS')
    need(sha(Path(argv[0]))==meta['compiler_sha256'],'COMPILER_DRIFT')
    libs=[Path(x[2:]) for x in argv if x.startswith('-L')]
    need(len(libs)==1,'LIB_PATH')
    for n,pin in meta['library_sha256'].items(): need(sha(libs[0]/n)==pin,'LIB_DRIFT:'+n)
    new.mkdir()
    for n,pin in meta['source_sha256'].items():
        need(Path(n).name==n and sha(old/n)==pin,'SOURCE_DRIFT:'+n)
        shutil.copyfile(old/n,new/n)
    for n,fn in [('MOD_Shells.f90',patch_fixed),('MOD_ArcanaRuntime.f90',patch_runtime)]:
        p=new/n; p.write_text(fn(p.read_text()))
    with (new/'build.log').open('x') as f:
        subprocess.run(argv,cwd=new,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/'assembly_only.exe'
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']}})
    return exe

def pressure(z,g,km,r):
    # Exact native reference layers: piecewise constant density at 1-km intervals.
    w,a,t=r.T
    thickness=np.clip(z[:,None]/km[:,None]-np.arange(8)[None,:],0.,1.)
    rho=np.column_stack((w,w,.7*w+.3*t,t,t,t,t,.7*t+.3*a))
    return g*km*(np.sum(thickness*rho,axis=1)+np.maximum(z/km-8.,0.)*a)

def audit(work,p,old,G,out):
    f=np.fromfile(work/'FB2_QUADRATURE.bin',dtype=FD)
    s=np.fromfile(work/'SQUEEZ_PRESSURE.bin',dtype=PD)
    need(len(f)==len(s)==Q,'QUADRATURE_COUNT:'+str((len(f),len(s))))
    ids=f['ids']; v=f['v']; w=s['v']
    need(np.array_equal(ids[:,0],np.tile(np.arange(1,E+1),7))
         and np.array_equal(ids[:,1],np.repeat(np.arange(1,8),E)),'IP_ORDER')
    need(np.array_equal(ids[:,2:],s['ids']) and np.array_equal(v[:,4:7],w[:,:3]),'IP_JOIN')
    need(np.isfinite(v).all() and np.isfinite(w).all() and np.array_equal(v[:,1],w[:,11]),'PRESSURE_JOIN')
    nodes=ids[:,2:].astype(np.int64)-1
    need(np.min(nodes)>=0 and np.max(nodes)<N,'NODE_RANGE')
    da,sig,sx,sy=v[:,:4].T
    elev,stop,g,km,rw,ra,rt,pr,sig2=w[:,3:].T
    z=stop-elev
    need(np.all(da>0) and np.all(g>0) and np.all(km>0) and np.all(z>=0)
         and np.all(z/km<300),'QUADRATURE_SUPPORT')
    rho=np.column_stack((rw,ra,rt))
    replay=pressure(z,g,km,rho)
    referr=float(np.max(abs(replay-pr))/max(float(np.max(abs(pr))),1.))
    pactual=pr-sig # derived from native anomaly, not an independent column integration
    # fPSfer Fortran memory order: (test component, direction, local node).
    phi=v[:,7:].reshape(Q,3,2,2).transpose(0,1,3,2)
    slopes=np.column_stack((sx,sy))
    coeff=-da[:,None,None]*np.einsum('qnab,qb->qna',phi,slopes)
    def assemble(pres):
        local=coeff*pres[:,None,None]
        arr=np.zeros((N,2))
        np.add.at(arr,nodes.ravel(),local.reshape(-1,2))
        return arr.ravel(),local
    actual,local=assemble(sig)
    scale=max(float(np.max(abs(old))),1.)
    err=float(np.max(abs(actual-old))/scale)
    ref,_=assemble(pr); lith,_=assemble(-pactual)
    mean=np.average(rho,axis=0,weights=da)
    common=pressure(z,g,km,np.broadcast_to(mean,rho.shape))
    common_load,_=assemble(common-pactual)
    delta,_=assemble(common-pr)
    torque=np.einsum('qna,qnac->qc',local,G.reshape(N,2,3)[nodes])
    et=torque.reshape(7,E,3).sum(axis=0)
    top=[{'axis':a,'element_id':int(j+1),'projection':float(et[j,a]),
          'node_ids':ids[j,2:].tolist()} for a in range(3)
         for j in np.argsort(abs(et[:,a]))[-20:][::-1]]
    write(out/'FB2_ELEMENT_LOCALIZATION.json',{'top_elements':top})
    np.savez_compressed(out/'FB2_PRESSURE_PROVENANCE.npz',element_projection=et,
                         native_reference_load=ref,derived_column_load=lith,
                         diagnostic_common_reference_load=common_load)
    m=lambda x:g25.metric(x,G)
    return {'quadrature_points':Q,'reference_profile_replay_relative_inf':referr,
        'FB2_reconstruction_relative_inf':err,
        'reference_plus_column_relative_inf':float(np.max(abs(ref+lith-actual))/scale),
        'element_projection_sum':et.sum(axis=0).tolist(),
        'depth_range_m':[float(z.min()),float(z.max())],
        'reference_density_ranges_kg_m3':np.column_stack((rho.min(axis=0),rho.max(axis=0))).tolist(),
        'native_FB2':m(old),'replayed_FB2':m(actual),'reference_pressure_component':m(ref),
        'derived_negative_column_pressure_component':m(lith),
        'diagnostic_common_reference':{'area_weighted_density_kg_m3':mean.tolist(),
            'FB2':m(common_load),'difference_from_native':m(delta),
            'physical_authority':False,'applied_to_model':False},
        'pressure_column_independently_integrated':False,
        'screen_pass':bool(referr<=1e-12 and err<=1e-12 and
                           np.max(abs(ref+lith-actual))/scale<=1e-12)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--g23',type=Path,required=True); ap.add_argument('--g25',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-pressure-diagnostic-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,out=(x.resolve() for x in (a.g23,a.g25,a.output))
    pm=g25.verify(p,0); qm=verify(q)
    need(not out.exists() and not any(out.is_relative_to(x) for x in (p,q,root)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G25_manifest_sha256':PIN,
            'additional_builds':0,'additional_fixed_load_runs':0,'additional_native_assemblies':0,
            'additional_native_solves':0,'additional_time_advance_years':0,'material_assignments':0,
            'load_modified':False,'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        with np.load(p/'native_diorite2/GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d: G=d['rotation_candidates']
        with np.load(q/'FIXED_COMPONENTS.npz',allow_pickle=False) as d:
            need(list(d['labels'])==list(g25.LABELS),'COMPONENT_LABELS'); old=d['components'][1]
        need(G.shape==(2*N,3) and old.shape==(2*N,),'FIELD_SHAPE')
        print('G26_BUILD_INSTRUMENTED_FIXED_ONLY',flush=True)
        exe=build(q/'build',out/'build'); report['additional_builds']=1
        work=out/'pressure_audit'; work.mkdir()
        prev=q/'fixed_decomposition'
        for n in g25.DECK: shutil.copyfile(prev/n,work/n)
        print('G26_NATIVE_PRESSURE_AUDIT',flush=True)
        report['additional_fixed_load_runs']=1
        with (work/'run.log').open('x') as f:
            rc=subprocess.run(['/usr/bin/time','-v','-o','run.time',str(exe)],cwd=work,
                stdout=f,stderr=subprocess.STDOUT,timeout=1200,preexec_fn=g25.limit).returncode
        log=(work/'run.log').read_text(); report['native_exit']=rc
        need(rc==0 and 'G25_STOP_AFTER_FIXED_BEFORE_PURE' in log and 'G18_CSR_ALLOC' not in log
             and not (work/'FatalError.txt').exists(),'NATIVE_STOP')
        need(all(sha(work/n)==sha(prev/n) for n in g25.DECK),'DECK_MUTATION')
        for n in ('FIXED_FULL',*g25.LABELS,'G23_NATIVE_GEOMETRY'):
            need(sha(work/(n+'.dat'))==sha(prev/(n+'.dat')),'INSTRUMENTATION_REPLAY:'+n)
        print('G26_NATIVE_FORCE_REPLAY_EXACT',flush=True)
        report['audit']=audit(work,p,old,G,out)
        report['screen_pass']=report['audit']['screen_pass']
        report['status']=('G26_BASAL_PRESSURE_PROVENANCE_PASS__TORQUE_CLOSURE_AUTHORITY_REQUIRED'
                          if report['screen_pass'] else 'G26_BASAL_PRESSURE_RECONSTRUCTION_UNRESOLVED')
    except Exception as e:
        report.update(screen_pass=False,status='G26_BASAL_PRESSURE_AUDIT_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    need(g25.verify(p,0)==pm and verify(q)==qm,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G26_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],
         'G25_manifest_sha256':PIN,'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G26_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
