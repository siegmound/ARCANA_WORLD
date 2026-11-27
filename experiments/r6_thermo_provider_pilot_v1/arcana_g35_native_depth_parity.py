#!/usr/bin/env python3
"""G35: sampled native OneBar depth parity and THOnB branch coverage.
Standalone driver, retained PRE, no Shells_v5p0 call or equilibrium assembly.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import traceback
import numpy as np
import arcana_g34_basal_depth_support as g34
import arcana_g33_native_basal_coupling_audit as g33
import arcana_g32_corrected_global_operator as g32
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27

PIN='45dfb5b8c088b09c6f06da4b0b07ae0c4b9234f3c933dd43ad8dacf4a483f1ef'
STATUS='G34_BASAL_DEPTH_SUPPORT_PASS__PHYSICAL_DEPTH_AND_MANTLE_AUTHORITY_REQUIRED'
AUTH='G35_NATIVE_DEPTH_PARITY_DIAGNOSTIC_ONLY_V1'
SOURCE,SCOPE=g33.SOURCE,g33.SCOPE
need,sha,read,write,inventory=g33.need,g33.sha,g33.read,g33.write,g33.inventory
N,E,Q=g33.N,g33.E,g33.Q
DEPTHS=(1000,200000,250000,300000)
CASES=('creep','traction_cap','eta_cap','zero_speed','not_pulled')
DRIVER="""program g35_native_depth_only
  use ShellsSubs, only: OneBar, THOnB
  use ShellSetSubs, only: ArcanaShellsInspectFEG, ArcanaShellsLoadRuntime, ArcanaShellsModeActive
  use SharedVars, only: ThID
  implicit none
  integer,parameter :: nn=64442
  integer :: ne,i,j,m,k,d,ic,uid,oid
  integer,allocatable :: nodes(:,:), ids(:), lr(:)
  real(8) :: points(3,7), ac(2,0:0),bc(2,0:0),cc(2,0:0),ec(0:0)
  real(8) :: depth,cap,etamax
  common /S1S2S3/ points
  real(8),allocatable :: moho(:,:),gc(:,:,:),gm(:,:,:),glue(:,:),phi(:,:,:,:,:)
  real(8),allocatable :: basal(:,:),v(:,:),ovb(:,:,:),eta(:,:),sig(:,:,:),outv(:,:,:)
  logical,allocatable :: pulled(:,:)
  integer,parameter :: depths(4)=(/1000,200000,250000,300000/)
  ThID=0
  open(1,file='regional.feg',status='old',action='read')
  call ArcanaShellsInspectFEG(1,'regional_PRE.dat',1)
  call ArcanaShellsLoadRuntime(nn,1)
  if (.not.ArcanaShellsModeActive()) stop 21
  close(1)
  open(newunit=uid,file='sample_input.dat',status='old',action='read')
  read(uid,*) ne
  if (ne<1.or.ne>2048) stop 22
  allocate(nodes(3,ne),ids(ne),lr(ne),moho(7,ne),gc(4,7,ne),gm(4,7,ne),glue(7,ne))
  allocate(phi(2,2,3,7,ne),basal(2,nn),v(2,nn),ovb(2,7,ne),eta(7,ne),sig(2,7,ne),outv(2,7,ne),pulled(7,ne))
  read(uid,*) ac(:,0),bc(:,0),cc(:,0),ec(0)
  do m=1,7
    read(uid,*) points(:,m)
  end do
  do i=1,ne
    read(uid,*) ids(i),nodes(:,i),moho(:,i)
  end do
  close(uid)
  if (minval(nodes)<1.or.maxval(nodes)>nn) stop 23
  lr=0
  gc=0d0
  gm=0d0
  phi=0d0
  basal=0d0
  v=0d0
  open(newunit=oid,file='G35_NATIVE.dat',status='new',action='write')
  do d=1,4
    depth=real(depths(d),8)
    ! Legacy geotherm/adiabat inputs are unused in active ARCANA mode.
    call OneBar(lr,gc,gm,0d0,0,ac,bc,cc,ec,ne,nodes,ne,1000d0,0d0,depth,moho,glue)
    do ic=1,5
      cap=1d30
      etamax=1d30
      pulled=.true.
      ovb(1,:,:)=0.03d0/31557600d0
      ovb(2,:,:)=0.04d0/31557600d0
      if (ic==2) cap=1d0
      if (ic==3) etamax=1d8
      if (ic==4) ovb=0d0
      if (ic==5) pulled=.false.
      ! Zero lithosphere velocity and zero shape functions give exact zero Flow.
      ! This deliberately tests the constitutive law, not interpolation.
      call THOnB(basal,lr,etamax,phi,glue,0,0,ec,ne,nn,nodes,ne,ovb,pulled,cap,v,eta,sig,outv)
      do m=1,7
        do i=1,ne
          write(oid,'(4I10,4(1X,ES26.17E3))') depths(d),ic,m,ids(i),glue(m,i),eta(m,i),sig(:,m,i)
        end do
      end do
    end do
  end do
  close(oid)
  print '(A)','G35_NATIVE_CONSTITUTIVE_ONLY_STOP'
end program g35_native_depth_only
"""
def verify(p):
    m=g32.verify(p,PIN,STATUS)
    need(m['G33_manifest_sha256']==g34.PIN and m['G32_manifest_sha256']==g33.PIN
         and m['G23_manifest_sha256']==g25.PINS[0] and m['G26_manifest_sha256']==g27.PIN,'G34_LINEAGE')
    need(read(p/'G34_REPORT.json')['screen_pass'],'G34_SCREEN')
    return m

def build(old,new):
    meta=read(old/'BUILD_IDENTITY.json'); argv=list(meta['argv'])
    need(argv[-2:]==['-o','assembly_only.exe'] and argv.count('driver.f90')==1
         and argv.count('SHELLS_g7.f90')==1 and all(k in argv for k in ('-O0','-Mbounds','-Kieee')),'BUILD_FLAGS')
    need(sha(Path(argv[0]))==meta['compiler_sha256'] and sha(old/'assembly_only.exe')==meta['exe_sha256'],'BUILD_IDENTITY')
    libs=[Path(x[2:]) for x in argv if x.startswith('-L')]
    need(len(libs)==1,'LIB_PATH')
    for n,pin in meta['library_sha256'].items(): need(sha(libs[0]/n)==pin,'LIB_DRIFT:'+n)
    new.mkdir()
    for n,pin in meta['source_sha256'].items():
        need(Path(n).name==n and sha(old/n)==pin,'SOURCE_DRIFT:'+n)
        shutil.copyfile(old/n,new/n)
    # Do not link the full SHELLS entry routine at all.
    argv.remove('SHELLS_g7.f90')
    (new/'driver.f90').write_text(DRIVER)
    need([n for n,pin in meta['source_sha256'].items() if sha(new/n)!=pin]==['driver.f90'],'SOURCE_SCOPE')
    argv[-1]='constitutive_only.exe'
    with (new/'build.log').open('x') as log:
        subprocess.run(argv,cwd=new,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=new/argv[-1]
    write(new/'BUILD_IDENTITY.json',{'argv':argv,'compiler_sha256':meta['compiler_sha256'],
        'library_sha256':meta['library_sha256'],'exe_sha256':sha(exe),
        'source_sha256':{n:sha(new/n) for n in meta['source_sha256']}})
    return exe

def samples(q,s,t):
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    need(len(f)==Q and np.array_equal(f['ids'][:,0],np.tile(np.arange(1,E+1),7))
         and np.array_equal(f['ids'][:,1],np.repeat(np.arange(1,8),E)),'QUADRATURE')
    ids=f['ids']; pts=f['v'][:,4:7].reshape(7,E,3)
    W=pts[:,0,:].copy()
    need(np.array_equal(pts,np.broadcast_to(W[:,None,:],pts.shape)),'WEIGHTS')
    nodes=ids[:E,2:].copy()
    need(np.array_equal(ids[:,2:].reshape(7,E,3),np.broadcast_to(nodes,(7,E,3))),'NODE_ORDER')
    native=np.fromfile(s/'native_diorite2/G33_NATIVE_BASAL.bin',dtype=g33.DT)
    need(len(native)==Q and np.array_equal(native['ids'],ids[:,:2]),'G33_JOIN')
    zc=native['v'][:,2].reshape(7,E).copy()
    lab=(native['v'][:,2]+native['v'][:,3])
    selected=set(np.linspace(0,E-1,96,dtype=int).tolist())
    def pick(x):
        order=np.argsort(x,kind='stable')
        for p in (0,.01,.05,.25,.5,.75,.95,.99,1):
            j=int(order[round(p*(len(order)-1))]); selected.add(j%E)
    pick(lab)
    refs={}
    for k in g33.MODELS:
        with np.load(t/(k+'_DEPTH_DIAGNOSTICS.npz'),allow_pickle=False) as d:
            need(np.array_equal(d['element_id'],ids[:,0]) and np.array_equal(d['ip_id'],ids[:,1])
                 and np.array_equal(d['depths_m'],g34.DEPTHS),'G34_JOIN')
            a=d['glue_1km_step']
            need(a.shape==(len(g34.DEPTHS),Q) and np.isfinite(a).all() and np.all(a>0),'G34_GLUE')
            for depth in DEPTHS: pick(a[g34.DEPTHS.index(depth)])
            refs[k]=a
    el=np.array(sorted(selected),dtype=int)
    idx=(np.arange(7)[:,None]*E+el[None,:]).ravel()
    return el,nodes[el],W,zc[:,el],{k:v[[g34.DEPTHS.index(d) for d in DEPTHS]][:,idx] for k,v in refs.items()}

def run_case(exe,work,parent,el,nodes,W,zc,ref):
    work.mkdir()
    for name in ('regional.feg','regional_PRE.dat'): shutil.copyfile(parent/name,work/name)
    ctl=read(parent/'CONDITIONAL_CONTROLS.json')
    co=[*ctl['aCreep'],*ctl['bCreep'],*ctl['cCreep'],ctl['eCreep']]
    with (work/'sample_input.dat').open('x') as f:
        f.write(str(len(el))+'\n'+' '.join(format(float(x),'.17g') for x in co)+'\n')
        np.savetxt(f,W,fmt='%.17g')
        for i,j in enumerate(el):
            f.write(' '.join(map(str,[j+1,*nodes[i].tolist()]))+' '+' '.join(format(x,'.17g') for x in zc[:,i])+'\n')
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    with (work/'run.log').open('x') as f:
        rc=subprocess.run(['/usr/bin/time','-v','-o','run.time',str(exe)],cwd=work,
            env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120,preexec_fn=g25.limit).returncode
    need(rc==0 and 'G35_NATIVE_CONSTITUTIVE_ONLY_STOP' in (work/'run.log').read_text()
         and not (work/'FatalError.txt').exists(),'NATIVE_STOP')
    need(all(sha(work/n)==sha(parent/n) for n in ('regional.feg','regional_PRE.dat')),'DECK_MUTATION')
    raw=np.loadtxt(work/'G35_NATIVE.dat'); n=7*len(el)
    need(raw.shape==(len(DEPTHS)*len(CASES)*n,8) and np.isfinite(raw).all(),'NATIVE_ROWS')
    raw=raw.reshape(len(DEPTHS),len(CASES),n,8)
    speed=np.array([.03,.04])/g33.YEAR; mag=np.linalg.norm(speed)
    rows=[]
    for i,depth in enumerate(DEPTHS):
        tests={}
        for j,name in enumerate(CASES):
            a=raw[i,j];glue=a[:,4]; eta=a[:,5]; sig=a[:,6:8]
            need(np.all(a[:,0]==depth) and np.all(a[:,1]==j+1)
                and np.array_equal(a[:,2],np.repeat(np.arange(1,8),len(el)))
                and np.array_equal(a[:,3],np.tile(el+1,7)),'ROW_ORDER')
            err=g33.rel(glue,ref[i]); need(err<1e-11,'ONEBAR_PARITY')
            creep=glue*mag**ctl['eCreep']
            if j==0:
                tau=creep; need(np.max(tau)<min(1e30,1e30*mag),'CREEP_BRANCH')
            elif j==1:
                tau=np.ones(n); need(np.min(creep)>1 and 1e30*mag>1,'TRACTION_BRANCH')
            elif j==2:
                tau=np.full(n,1e8*mag); need(np.min(creep)>tau[0] and tau[0]<1e30,'ETA_BRANCH')
            else: tau=np.zeros(n)
            ee=tau/mag
            errs={'glue_relative_inf':err,'eta_relative_inf':g33.rel(eta,ee),
                  'traction_relative_inf':g33.rel(sig,ee[:,None]*speed)}
            need(max(errs.values())<1e-11,'THONB_PARITY:'+name)
            tests[name]=errs
        rows.append({'depth_m':depth,'tests':tests})
    return {'sample_elements':len(el),'sample_quadrature_points':n,'native_records':len(raw.ravel())//8,
            'depths':rows,'native_exit':rc}
def main():
    ap=argparse.ArgumentParser()
    for k in ('g23','g26','g33','g34','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-native-depth-parity-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,s,t,out=(x.resolve() for x in (a.g23,a.g26,a.g33,a.g34,a.output))
    parents=((p,lambda x:g25.verify(x,0)),(q,g27.verify),(s,g34.verify),(t,verify))
    before=[fn(x) for x,fn in parents]
    need(not out.exists() and not any(out.is_relative_to(x) for x in (root,p,q,s,t)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':g27.PIN,
        'G33_manifest_sha256':g34.PIN,'G34_manifest_sha256':PIN,'additional_builds':0,
        'native_constitutive_runs_attempted':0,'additional_native_assemblies':0,'additional_global_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'active_source_modified':False,
        'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        el,nodes,W,zc,refs=samples(q,s,t)
        print('G35_SAMPLE_ELEMENTS',len(el),flush=True)
        write(out/'SAMPLE_IDENTITY.json',{'element_ids':(el+1).tolist(),
            'selection':'96 evenly spaced element IDs plus order-statistic extrema/quantiles of LAB and each retained glue field; not a statistical random sample'})
        exe=build(s/'build',out/'build');report['additional_builds']=1
        report['cases']={}
        for k in g33.MODELS:
            print('G35_NATIVE_CASE',k,flush=True);report['native_constitutive_runs_attempted']+=1
            report['cases'][k]=run_case(exe,out/k,p/k,el,nodes,W,zc,refs[k])
        report.update(screen_pass=True,status='G35_NATIVE_DEPTH_PARITY_PASS__MANTLE_PHYSICAL_AUTHORITY_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G35_NATIVE_DEPTH_PARITY_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    need([fn(x) for x,fn in parents]==before,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G35_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
        'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':g27.PIN,'G33_manifest_sha256':g34.PIN,
        'G34_manifest_sha256':PIN,'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(__import__('json').dumps(report,indent=2,allow_nan=False),flush=True)
    print('G35_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
