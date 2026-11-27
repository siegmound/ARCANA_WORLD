#!/usr/bin/env python3
"""G10R1: minimax C1 residual and post-load native sampling on G9 year2, no solve.

Keep validated PRE base, add a mandatory, versioned sidecar. At each layer
boundary correction and its derivative vanish. Preserve base density and
sensible energy moments to first order and check exact nonlinear moments.
Native point evaluator AND analytic temperature integral consume sidecar.
No change to rheological laws, weighted mixing or Squeez quadrature.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import shutil
import traceback
import numpy as np
from scipy.optimize import linprog
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4
import arcana_g5_column_heat as g5
import arcana_g7_paired_resolve as g7
import arcana_g8_staggered_restart as g8

G10_PIN='54e677cc57173b4fec36b6bdbeffeec39b127a3ae0bc02a017d7392f9c188292'
G10_STATUS='G10_THERMAL_CONSUMER_BLOCKED'
G9_PIN='d900b3aa3dcc38241f298ee30182c068cb089bd7e104aebacb57ed3902b8cfb0'
G9_STATUS='G9_COUPLING_STEP_HALVING_SCREEN_PASS__THERMAL_CONSUMER_UPGRADE_REQUIRED'
CP_PIN='df6d932f19f1159dad1f42bb8365cdac940ecc398bfe513fed8ecac3bcaeba30'
N=64
KNOTS=np.r_[0.,(np.arange(N)+.5)/N,1.]
MAGIC='ARCANA_G10_C1_RESIDUAL_V1'
SIDE='regional_thermal_correction.dat'
TOL={'density_relative':1e-12,'energy_over_signal':1e-5,
     'cell_error_reduction_factor':0.25,'native_temperature_K':1e-10,
     'native_mean_density_kg_m3':1e-8,'zero_probe_relative':1e-13}
# Gauss quadrature on each half-cell, aligned with all correction knots.
x,w=np.polynomial.legendre.leggauss(4)
Q=((np.arange(2*N)[:,None]+(x+1)/2)/(2*N)).ravel()
W=np.tile(w/(4*N),2*N)
def basis(s):
    s=np.asarray(s); i=np.clip(np.searchsorted(KNOTS,s,side='right')-1,0,N)
    u=(s-KNOTS[i])/(KNOTS[i+1]-KNOTS[i])
    b=np.zeros(s.shape+(N+2,))
    flat=b.reshape(-1,N+2); j=np.arange(s.size); f=(u*u*(3-2*u)).ravel()
    flat[j,i.ravel()]=1-f; flat[j,i.ravel()+1]=f
    return b[...,1:-1]
B=basis(Q)
P=Q[:,None]**np.arange(4)
def fit(base,initial,alpha,target):
    t=P@base; t0=P@initial
    weights=(1-alpha*t0)*W
    def cells(y): return (y*weights).reshape(N,8).sum(axis=1)/weights.reshape(N,8).sum(axis=1)
    A=(B*weights[:,None]).reshape(N,8,N).sum(axis=1)/weights.reshape(N,8).sum(axis=1)[:,None]
    residual=target-cells(P@(base-initial))
    # Preserve integral T (density) and integral (1-alpha*T)*T (energy).
    C=np.vstack((W@B,(W*(1-2*alpha*t))@B))
    C=C/np.linalg.norm(C,axis=1)[:,None]
    _,sv,Vh=np.linalg.svd(C,full_matrices=True)
    a.need(sv[-1]>1e-8,'MOMENT_CONSTRAINT_RANK')
    Z=Vh[2:].T
    ls=Z@np.linalg.lstsq(A@Z,residual,rcond=None)[0]
    scale=float(np.max(abs(residual)))
    if scale==0:
        v=np.zeros(N); optimum=0.
    else:
        # Optimize dimensionless variables so the micokelvin signal is
        # not smaller than the LP's feasibility tolerance.
        M=A@Z
        mat=np.vstack((np.column_stack((M,-np.ones(N))),
                       np.column_stack((-M,-np.ones(N)))))
        res=linprog(np.r_[np.zeros(Z.shape[1]),1.],A_ub=mat,
            b_ub=np.r_[residual/scale,-residual/scale],
            bounds=[(None,None)]*Z.shape[1]+[(0,None)],method='highs',
            options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        a.need(res.success,'MINIMAX_OPTIMIZATION:'+str(res.message))
        v=scale*(Z@res.x[:-1]); optimum=float(res.fun*scale)
        a.need(float(np.max(abs(A@v-residual)))<=optimum+scale*1e-8,'LP_FEASIBILITY')
        a.need(float(np.max(abs(A@v-residual)))<=float(np.max(abs(A@ls-residual)))+scale*1e-8,'MINIMAX_VS_L2')
    corr=B@v
    density=1-alpha*(W@t)
    density_change=-alpha*(W@corr)
    energy_change=W@((1-2*alpha*t)*corr-alpha*corr*corr)
    mean_change=(energy_change-(W@((1-alpha*t)*t)/density)*density_change)/(density+density_change)
    return v,{'base_error_K':float(np.max(abs(residual))),
        'corrected_error_K':float(np.max(abs(A@v-residual))),
        'max_correction_K':float(np.max(abs(v))),
        'l2_fit_max_error_K':float(np.max(abs(A@ls-residual))),
        'minimax_objective_K':optimum,
        'density_relative_change':float(abs(density_change)/density),
        'mass_specific_temperature_change_K':float(mean_change)}

def selftest():
    v=np.sin(np.arange(N)/N*2*np.pi)*1e-5
    a.need(np.all(basis(np.array([0.,1.]))==0),'ENDPOINT_BASIS')
    a.need(np.array_equal(basis(KNOTS[1:-1]),np.eye(N)),'KNOT_BASIS')
    t=np.array([280.,500.,-10.,2.])
    z,r=fit(t,t,3e-5,np.zeros(N))
    a.need(np.all(z==0),'ZERO_PROFILE')
    z,r=fit(t,t,3e-5,np.sin(np.arange(N)/N*2*np.pi)*1e-5)
    a.need(r['density_relative_change']<1e-13 and abs(r['mass_specific_temperature_change_K'])<1e-12,'MOMENT_FIXTURE')
    print('G10_RECONSTRUCTION_SELFTEST_PASS',flush=True)

def project(cp):
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
    s=g4.unseal(cp/'initial.json'); z=g4.unseal(cp/'geometry.json')
    t=np.asarray(s['transport_triangles_zero_based']).ravel()
    init=np.asarray(s['normalized_depth_temperature_coefficients_K']).reshape(384,2,4)
    with np.load(cp/'thermal.npz') as th:
        cap=th['heat_capacity_J_K']; E=th['two_half_energy_increment_J']
        a.need(cap.shape==E.shape==(384,2,N) and np.isfinite(E).all(),'THERMAL_SHAPE')
        a.need(np.array_equal(th['parcel_node_local_ids'].ravel()-1,t),'PARCEL_BINDING')
    lines=(cp/'regional_PRE.dat').read_text().splitlines()[1:]
    vals=[]; results=[]; rows=[]
    for i,line in enumerate(lines):
        row=dict(zip(FIELDS,map(float,line.split()),strict=True))
        a.need(row['node_id']==i+1,'NODE_ORDER')
        idx=np.flatnonzero(t==i)
        target=E[idx].sum(axis=0)/cap[idx].sum(axis=0)
        for j,role in enumerate(('crust','mantle')):
            pre=f'layer{j+1}_'; h=row[pre+'z1_m']-row[pre+'z0_m']
            base=np.array([row[pre+k]*h**p for p,k in enumerate(('c0_k','c1_k_m','c2_k_m2','c3_k_m3'))])
            v,r=fit(base,init[idx[0],j],row[role+'_expansivity_k_1'],target[j])
            a.need(np.isfinite(v).all() and np.all(init[idx,j]==init[idx[0],j]),'PROFILE_FINITE')
            vals.append(v); results.append(dict(r,node=i+1,layer=j+1))
            rows.append((i+1,j+1,h,base,row[role+'_density_kg_m3'],row[role+'_expansivity_k_1']))
    a.need(len(vals)==162,'PROFILE_COUNT')
    return np.array(vals).reshape(81,2,N),results,rows

def sidecar(v):
    return MAGIC+' 81 64\n'+''.join(
        f'{i+1} {j+1} '+' '.join(format(x,'.17e') for x in v[i,j])+'\n'
        for i in range(81) for j in range(2))

def loader(source):
    source=a.replace1(source,'  PUBLIC :: ArcanaRuntimeRead, ArcanaRuntimeGet, ArcanaRuntimeRelease',
        '''  REAL(8), SAVE :: corr(0:65,2,ARCANA_NODE_COUNT)
  LOGICAL, SAVE :: corr_loaded=.FALSE.
  PUBLIC :: ArcanaRuntimeRead, ArcanaRuntimeGet, ArcanaRuntimeRelease''')
    source=a.replace1(source,'    branch_count = 0','    corr_loaded=.FALSE.\n    branch_count = 0')
    source=a.replace1(source,'    RETURN\n\n900 CONTINUE',
        '''    CALL ReadCorrection(ios)
    IF (ios /= 0) THEN
       message='ARCANA_G10_CORRECTION_INVALID'
       GOTO 900
    END IF
    RETURN

900 CONTINUE''')
    source=a.replace1(source,'  SUBROUTINE ArcanaRuntimeRelease()\n',
        '  SUBROUTINE ArcanaRuntimeRelease()\n    corr_loaded=.FALSE.\n')
    for j in (1,2):
        key=f'            v(I_L{j}_C1),v(I_L{j}_C0),x)'
        source=a.replace1(source,key,key+f'''
       IF (.NOT. corr_loaded) THEN
          ierr=1
          RETURN
       END IF
       temperature_k=temperature_k+CorrectionValue(node_id,{j},x/(v(I_L{j}_Z1)-v(I_L{j}_Z0)))''')
        key=f'            v(I_L{j}_C3),v(I_L{j}_C2),v(I_L{j}_C1),v(I_L{j}_C0),x0)'
        source=a.replace1(source,key,key+f'''
       integral=integral+CorrectionIntegral(node_id,{j},x0,x1,v(I_L{j}_Z1)-v(I_L{j}_Z0))''')
    code='''
  SUBROUTINE ReadCorrection(ierr)
    INTEGER, INTENT(OUT) :: ierr
    INTEGER :: u,ios,i,j,k,n,nn,count
    CHARACTER(LEN=4096) :: line
    CHARACTER(LEN=128) :: tokens(67)
    LOGICAL :: overflow
    ierr=1
    corr_loaded=.FALSE.
    corr=0d0
    OPEN(NEWUNIT=u,file='regional_thermal_correction.dat',status='old',action='read',iostat=ios)
    IF(ios/=0) RETURN
    READ(u,'(A)',iostat=ios) line
    IF(ios/=0) GOTO 800
    CALL Tokenize(line,tokens,count,overflow)
    IF(overflow .OR. count/=3) GOTO 800
    IF(TRIM(tokens(1))/='ARCANA_G10_C1_RESIDUAL_V1' .OR. &
       TRIM(tokens(2))/='81' .OR. TRIM(tokens(3))/='64') GOTO 800
    DO i=1,ARCANA_NODE_COUNT
       DO j=1,2
          READ(u,'(A)',iostat=ios) line
          IF(ios/=0) GOTO 800
          CALL Tokenize(line,tokens,count,overflow)
          IF(overflow .OR. count/=66) GOTO 800
          DO k=1,66
             IF(.NOT.IsNumericToken(TRIM(tokens(k)))) GOTO 800
          END DO
          READ(line,*,iostat=ios) n,nn,corr(1:64,j,i)
          IF(ios/=0 .OR. n/=i .OR. nn/=j) GOTO 800
          IF(.NOT.ALL(IEEE_IS_FINITE(corr(:,j,i)))) GOTO 800
          IF(MAXVAL(ABS(corr(:,j,i)))>1d-2) GOTO 800
       END DO
    END DO
    READ(u,'(A)',iostat=ios) line
    IF(ios>=0) GOTO 800
    corr_loaded=.TRUE.
    ierr=0
800 CLOSE(u)
  END SUBROUTINE ReadCorrection

  REAL(8) FUNCTION Knot(k)
    INTEGER, INTENT(IN) :: k
    Knot=MAX(0d0,MIN(1d0,(DBLE(k)-0.5d0)/64d0))
  END FUNCTION Knot

  REAL(8) FUNCTION CorrectionValue(node,layer,s)
    INTEGER, INTENT(IN) :: node,layer
    REAL(8), INTENT(IN) :: s
    REAL(8) :: x,u,f
    INTEGER :: i
    x=MAX(0d0,MIN(1d0,s))
    i=MAX(0,MIN(64,INT(64d0*x+0.5d0)))
    u=(x-Knot(i))/(Knot(i+1)-Knot(i))
    f=u*u*(3d0-2d0*u)
    CorrectionValue=(1d0-f)*corr(i,layer,node)+f*corr(i+1,layer,node)
  END FUNCTION CorrectionValue

  REAL(8) FUNCTION CorrectionIntegral(node,layer,x0,x1,h)
    INTEGER, INTENT(IN) :: node,layer
    REAL(8), INTENT(IN) :: x0,x1,h
    REAL(8) :: lo,hi,l,r,u,v,d,w0,w1
    INTEGER :: i,first,last
    lo=MAX(0d0,MIN(1d0,x0/h))
    hi=MAX(0d0,MIN(1d0,x1/h))
    first=MAX(0,MIN(64,INT(64d0*lo+0.5d0)))
    last=MAX(0,MIN(64,INT(64d0*hi+0.5d0)))
    CorrectionIntegral=0d0
    DO i=first,last
       l=Knot(i)
       r=Knot(i+1)
       d=r-l
       u=(MAX(lo,l)-l)/d
       v=(MIN(hi,r)-l)/d
       IF(v<=u) CYCLE
       w1=(v**3-0.5d0*v**4)-(u**3-0.5d0*u**4)
       w0=v-u-w1
       CorrectionIntegral=CorrectionIntegral+h*d*(w0*corr(i,layer,node)+w1*corr(i+1,layer,node))
    END DO
  END FUNCTION CorrectionIntegral

'''
    return a.replace1(source,'  SUBROUTINE Tokenize(',code+'  SUBROUTINE Tokenize(')

def entry_with_samples(source):
    # The FEG inspector only opens unit 17. Runtime data are not loaded
    # until Shells_v5p0 calls ArcanaShellsLoadRuntime.
    key='       CALL ArcanaShellsLoadRuntime(numNod,ThID)\n       IF (ArcanaShellsFailed()) RETURN'
    source=a.replace1(source,key,key+'\n       CALL G10SampleLoadedRuntime()')
    routine='''
subroutine G10SampleLoadedRuntime()
  use ArcanaRuntime, only: ArcanaRuntimeGet, ArcanaRuntimeEvaluateNode, &
       ArcanaRuntimeMeanEffectiveDensity, ARCANA_FIELD_COUNT, ARCANA_PROPERTY_COUNT
  implicit none
  integer :: ni,li,gi,ier,phase
  real(8) :: row(ARCANA_FIELD_COUNT),props(ARCANA_PROPERTY_COUNT),z0,h,z,t,rho,s0,s1
  real(8) :: weight(1)
  integer :: node(1)
  open(77,file='g10_native_samples.dat',status='new')
  weight=1d0
  do ni=1,81
    node=ni
    call ArcanaRuntimeGet(ni,row,ier)
    if(ier/=0) stop 94
    do li=1,2
      z0=0d0
      h=row(16)
      if(li==2) then
        z0=row(16)
        h=row(17)
      end if
      do gi=0,127
        z=z0+h*(dble(gi)+0.5d0)/128d0
        call ArcanaRuntimeEvaluateNode(ni,z,t,props,phase,ier)
        if(ier/=0.or.phase/=li) stop 95
        write(77,'(3I6,2(1X,ES26.17E3))') ni,li,gi,z,t
      end do
      do gi=0,3
        s0=dble(gi)/4d0
        s1=s0+0.25d0
        call ArcanaRuntimeMeanEffectiveDensity(node,weight,1,z0+h*s0,z0+h*s1,rho,ier)
        if(ier/=0) stop 96
        write(77,'(3I6,2(1X,ES26.17E3))') ni,li,128+gi,z0+h*s0,rho
      end do
    end do
  end do
  close(77)
  print '(A)','G10R1_POST_LOAD_SAMPLES_COMPLETE'
end subroutine G10SampleLoadedRuntime

'''
    return a.replace1(source,'end module SHELLS',routine+'end module SHELLS')

def sample_check(path,values,rows):
    data=np.loadtxt(path)
    a.need(data.shape==(162*132,5) and np.isfinite(data).all(),'NATIVE_SAMPLE_SHAPE')
    data=data.reshape(162,132,5)
    te=0.; de=0.
    for idx,(i,j,h,base,rho,alpha) in enumerate(rows):
        v=values[i-1,j-1]
        r=data[idx]
        a.need(np.all(r[:,0]==i) and np.all(r[:,1]==j) and
            np.array_equal(r[:,2],np.arange(132)),'NATIVE_SAMPLE_ID')
        s=(np.arange(128)+.5)/128
        expected=s[:,None]**np.arange(4)@base+basis(s)@v
        te=max(te,float(np.max(abs(r[:128,4]-expected))))
        temp=P@base+B@v
        # Quadrature splits at all correction knots and quarter boundaries.
        for k in range(4):
            sl=slice(k*128,(k+1)*128)
            density=rho*(1-alpha*float(4*(W[sl]@temp[sl])))
            de=max(de,abs(r[128+k,4]-density))
    return {'temperature_max_absolute_error_K':te,'density_max_absolute_error_kg_m3':de,
        'screen_pass':bool(te<=TOL['native_temperature_K'] and de<=TOL['native_mean_density_kg_m3'])}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-thermal-consumer-test',choices=[a.SCENARIO],required=True)
    args=ap.parse_args(); selftest(); g8.check_helpers()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
        not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    parent=c10.OUT.with_name('R6_THERMO_G9_COUPLING_HALVING_NEW01')
    prior=c10.OUT.with_name('R6_THERMO_G8_STAGGERED_RESTART_NEW01')
    failed=c10.OUT.with_name('R6_THERMO_G10_THERMAL_CONSUMER_NEW01')
    fm=c.verified(failed,G10_PIN,G10_STATUS)
    fr=a.read(failed/'G10_REPORT.json')
    a.need(not fr['screen_pass'] and not fr['projection']['screen_pass'] and fr['additional_native_solves']==0,'G10_PARENT_STATUS')
    pm=c.verified(parent,G9_PIN,G9_STATUS)
    a.need(pm['source_sha']==a.SHA and all(pm[k]==v for k,v in c.SCOPE.items()),'G9_SCOPE')
    pr=a.read(parent/'G9_REPORT.json')
    a.need(pr['screen_pass'] and pr['refined_checkpoint_sha256']==CP_PIN,'G9_SCREEN')
    cp=parent/'checkpoint_year2_refined'; g8.open_checkpoint(cp,CP_PIN)
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in (root,parent,prior,failed,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G9_manifest':G9_PIN,'G10_failed_manifest':G10_PIN,'checkpoint':CP_PIN,'runner_sha256':a.sha(Path(__file__)),
       'tolerances':TOL,'correction':'C1 smoothstep between layer-normalized cell centers, zero at boundaries; two linear moment constraints per layer; minimax cell residual in scaled units.',
       'scope':'Fixed G9 native deck and material identities. Native pre-solve only. No new rheology or physical acceptance.',**c.SCOPE})
    report={'screen_pass':False,'additional_native_solves':0,**c.SCOPE}
    try:
        v,budgets,rows=project(cp)
        a.write(out/'PROFILE_BUDGETS.json',budgets)
        np.savez(out/'CORRECTIONS.npz',values_K=v,knots=KNOTS)
        base=max(x['base_error_K'] for x in budgets)
        ls=max(x['l2_fit_max_error_K'] for x in budgets)
        a.need(abs(base-fr['projection']['base_cell_max_error_K'])<=1e-12 and abs(ls-fr['projection']['corrected_cell_max_error_K'])<=1e-12,'G10_L2_REPRODUCTION')
        corrected=max(x['corrected_error_K'] for x in budgets)
        den=max(x['density_relative_change'] for x in budgets)
        en=max(abs(x['mass_specific_temperature_change_K']) for x in budgets)
        # Compare added projection error to the existing nodal mean signal,
        # retaining G6's integrated energy accuracy requirement.
        signal=pr['second_half']['projection']['max_cumulative_mean_signal_K']
        fitrep={'base_cell_max_error_K':base,'corrected_cell_max_error_K':corrected,
            'error_ratio':corrected/base,'retained_l2_error_K':ls,'max_relative_density_change':den,
            'max_added_energy_error_over_mean_signal':en/signal,
            'max_abs_correction_K':float(np.max(abs(v)))}
        fitrep['screen_pass']=bool(corrected<=TOL['cell_error_reduction_factor']*base and
            den<=TOL['density_relative'] and en/signal<=TOL['energy_over_signal'])
        report['projection']=fitrep
        print('G10_PROFILE',json.dumps(fitrep),flush=True)
        # Use original native probe path, with only runtime evaluator and
        # extra independent sampling in the driver changed.
        build=out/'build'; build.mkdir()
        src=root/native.VENDOR
        for n in native.STOCK: shutil.copyfile(src/n,build/n)
        (build/'MOD_Shells.f90').write_text(a.replace1((build/'MOD_Shells.f90').read_text(),
           'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )','STOP 93 ! G10 solve forbidden'))
        (build/'MOD_ArcanaRuntime.f90').write_text(loader((c10.OUT/'MOD_ArcanaRuntime.regional.f90').read_text()))
        (build/'SHELLS_probe.f90').write_text(entry_with_samples(native.generated_source((src/'SHELLS_v5.0.f90').read_text())))
        shutil.copyfile(Path(native.__file__).with_name('c10_pre_solve_driver.f90'),build/'driver.f90')
        names=(native.STOCK[0],'MOD_ArcanaRuntime.f90',*native.STOCK[1:],'SHELLS_probe.f90','driver.f90')
        cmd=[str(native.COMPILER),'-O0','-Mbackslash','-Kieee','-Mbounds',*names,
             '-L'+str(native.LIB),'-Wl,-rpath,'+str(native.LIB),'-llapack','-lblas','-o','probe.exe']
        env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        print('G10_BUILD',flush=True)
        with (build/'build.log').open('x') as log:
            subprocess.run(cmd,cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        exe=build/'probe.exe'
        a.write(build/'BUILD_IDENTITY.json',{'argv':cmd,'exe_sha256':a.sha(exe),
           'compiler_sha256':a.sha(native.COMPILER),'source_sha256':{n:a.sha(build/n) for n in names},
           'library_sha256':{n:a.sha(native.LIB/n) for n in ('liblapack.so','libblas.so')}})
        probes={}; parsed={}
        for key,values in [('zero',np.zeros_like(v)),('corrected',v),('missing',None),('bad',v)]:
            print('G10_PROBE',key,flush=True)
            work=out/key; work.mkdir()
            for n in (*g7.DECK,'regional.in'): shutil.copyfile(cp/n,work/n)
            if values is not None:
                body=sidecar(values)
                if key=='bad': body=body.replace(MAGIC,'BAD_MAGIC',1)
                (work/SIDE).write_text(body)
            rc,log=g7.run(exe,work,env)
            fatal=work/'FatalError.txt'
            fatal_text=fatal.read_text(errors='replace') if fatal.exists() else ''
            fatal_text+='\n'.join(p.read_text(errors='replace') for p in sorted((work/'Error').glob('FatalError_*.txt')))
            probes[key]={'exit_code':rc,'log_tail':log[-2000:],'fatal_tail':fatal_text[-2000:]}
            report['probe_progress']=probes
            if key in ('missing','bad'):
                probes[key]['rejected']=bool(rc!=0 and 'C10_STOP_AFTER_FIXED_BEFORE_PURE' not in log and 'G10R1_POST_LOAD_SAMPLES_COMPLETE' not in log and 'ARCANA_G10_CORRECTION_INVALID' in (log+fatal_text))
                continue
            a.need(rc==0 and 'C10_STOP_AFTER_FIXED_BEFORE_PURE' in log and not (work/'FatalError.txt').exists() and 'G10R1_POST_LOAD_SAMPLES_COMPLETE' in log,'NATIVE_STOP:'+key+':'+str(rc))
            probes[key].update(sample_check(work/'g10_native_samples.dat',values,rows))
            parsed[key]=native.parse_probe(work/'native_pre_solve.txt')
        old=native.parse_probe(parent/'refined_mechanics/probe_reference/native_pre_solve/hydrostatic/native_pre_solve.txt')
        zero=parsed['zero']; new=parsed['corrected']
        a.need(zero['SIZE']==old['SIZE']==new['SIZE'],'NATIVE_SIZE')
        zeros={k:g4.relative(np.array(zero[k]),np.array(old[k])) for k in ('NODE','IP','BC')}
        nd=np.array(new['NODE']); nd0=np.array(zero['NODE'])
        ip=np.array(new['IP']); ip0=np.array(zero['IP'])
        a.need(np.array_equal(nd[:,:5],nd0[:,:5]) and np.array_equal(new['BC'],zero['BC']) and
            np.all(ip[:,-3:]==0),'NATIVE_GEOMETRY_OR_BASAL_DRIFT')
        report['native']={'cases':probes,'zero_sidecar_vs_original_relative':zeros,
            'max_sigZZ_change_Pa':float(np.max(abs(nd[:,5]-nd0[:,5]))),
            'max_tauZZ_change_N_m':float(np.max(abs(nd[:,6]-nd0[:,6]))),
            'max_fixed_load_change_N':float(np.max(abs(nd[:,7:]-nd0[:,7:])))}
        report['screen_pass']=bool(fitrep['screen_pass'] and probes['zero']['screen_pass'] and
            probes['corrected']['screen_pass'] and probes['missing']['rejected'] and probes['bad']['rejected'] and
            max(zeros.values())<=TOL['zero_probe_relative'])
    except Exception as exc:
        report['error']={'error':repr(exc),'traceback':traceback.format_exc()}
    a.need(c.inventory(parent)==pm['files'] and a.sha(parent/'MANIFEST.json')==G9_PIN,'PARENT_MUTATION')
    a.need(c.inventory(failed)==fm['files'] and a.sha(failed/'MANIFEST.json')==G10_PIN,'G10_PARENT_MUTATION')
    status='G10R1_C1_THERMAL_CONSUMER_SCREEN_PASS__RESOLVE_SENSITIVITY_REQUIRED' if report['screen_pass'] else 'G10R1_THERMAL_CONSUMER_BLOCKED'
    report.update(status=status,physical_acceptance=False,limitations=[
        'C1 correction of cubic base on retained G9 checkpoint only; no forward evolution or full native solve.',
        'Cell average errors measured in lumped nodal measure, not exact parcel or pointwise temperature reconstruction.',
        'Moment constraints preserve base density and energy to first order; exact residual measured.',
        'No change to native Squeez vertical quadrature, weighted phase mixing, natural exterior or thermodynamic closure.',
        'Experimental sidecar hard-required in regional generated loader; not a global schema migration.'])
    a.write(out/'G10R1_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G9_manifest_sha256':G9_PIN,
        'G10_manifest_sha256':G10_PIN,'additional_native_solves':0,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G10R1_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
