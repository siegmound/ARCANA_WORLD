#!/usr/bin/env python3
"""C11-B-R1: tighter native convergence, same physical scenario.
Preserve C11-B and require explicit operator authorization. No T1 or canon.
"""
import argparse, json, os, shutil, subprocess, sys, re, signal
from pathlib import Path
import numpy as np

A_SCRIPT_PIN='af9afbd8d337f00e8d23c2681c25b2542a788b10302d0c3cafef0c888845780c'
A_PIN='58914c9318b2ac342bf13fef89fc6e2c7a4d3b1cc54e057b9abe549a513de5a3'
A_STATUS='C11A_FIRST_LINEARIZATION_RANK_SCREEN_PASS__SOLVE_NOT_AUTHORIZED'
B_PIN='c667fdbfde09fe1e15cd157ac8ed5be259db7dde5f54566666c4faebecd67b40'
B_STATUS='C11B_NATIVE_CONVERGED__BLOCKED_DIAGNOSTIC_SCREEN'
B_SCRIPT_PIN='7b17dc4f7371a436b24f94672a58ee82797132b0f3a6eecf6925652afde9cc2b'
MAX_ITER=250
NATIVE_TOL=5e-7
STRESS_REFRESH_SCREEN=1e-3

# Prospective engineering screens, not a physical acceptance budget.
LINEAR_LIMIT=1e-12
BC_REL_LIMIT=1e-12
NONLINEAR_SCREEN=1e-3
POWER_SCREEN=1e-3
QUADRATURE_SCREEN=1e-9


def native_sources(entry, subs, a, native):
    # Keep the proven C11A entry and use the real native Pure/FEM/Solver.
    e=a.gen_entry(entry,native).replace('stop 79 ! FEM must stop, never return',
        'stop 79 ! native iteration ended without final diagnostic stop')
    # FEM: save native matrices every iteration and final same-state reassembly.
    start=subs.index('SUBROUTINE FEM ('); end=subs.index('END SUBROUTINE FEM',start)
    f=subs[start:end]
    f=a.replace1(f,'INTEGER i, j\nREAL*8 bDenom', '''INTEGER i, j, c11m
INTEGER, SAVE :: c11iter=0
LOGICAL c11final
CHARACTER(40) c11prefix
DOUBLE PRECISION c11weight(7)
COMMON / WgtVec / c11weight
REAL*8 bDenom''')
    f=a.replace1(f,'CALL BuildF (area, detJ, dXS, dYS, eta,', '''INQUIRE(file='C11B_FINAL_REQUEST',exist=c11final)
IF (c11final) THEN
  c11prefix='final'
ELSE
  c11iter=c11iter+1
  WRITE(c11prefix,'(A,I3.3)') 'iter_',c11iter
END IF
CALL BuildF (area, detJ, dXS, dYS, eta,''')
    def dump(u,suffix):
        return f'''OPEN({u},file=trim(c11prefix)//'{suffix}',status='new',action='write')
WRITE({u},*) nRank,nKRows,iDiagonal,nLB,nUB,nDOF
DO j=1,nRank
  WRITE({u},'(I6,*(1X,ES26.17E3))') j,f(j,1),k(:,j)
END DO
CLOSE({u})
'''
    f=a.replace1(f,'CALL VBCs (iCond, mxBn, mxDOF,',dump(72,'_pre.dat')+'CALL VBCs (iCond, mxBn, mxDOF,')
    f=a.replace1(f,'CALL Solver (iUnitT,',dump(73,'_post.dat')+'''IF (c11final) THEN
  CALL TauDef(alpha,eRate,mxEl,numEl,tOfset,tauMat)
  OPEN(74,file='final_nodes.dat',status='new',action='write')
  DO i=1,numNod
    WRITE(74,'(I6,4(1X,ES26.17E3))') i,v(:,i),fBase(2*i-1),fBase(2*i)
  END DO
  CLOSE(74)
  OPEN(75,file='final_ip.dat',status='new',action='write')
  DO i=1,numEl
    DO c11m=1,7
      WRITE(75,'(2I6,*(1X,ES26.17E3))') i,c11m, &
        area(i)*c11weight(c11m)*detJ(c11m,i), &
        eRate(:,c11m,i),tauMat(:,c11m,i),tOfset(:,c11m,i),eta(c11m,i)
    END DO
  END DO
  CLOSE(75)
  PRINT '(A)','C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER'
  STOP 0
END IF
CALL Solver (iUnitT,''')
    f=a.replace1(f,'!  After this CALL, new solution is in "f", and old one in "v".', '''OPEN(76,file=trim(c11prefix)//'_solution.dat',status='new',action='write')
DO j=1,nRank
  WRITE(76,'(I6,1X,ES26.17E3)') j,f(j,1)
END DO
CLOSE(76)
!  After this CALL, new solution is in "f", and old one in "v".''')
    s=subs[:start]+f+subs[end:]
    # At native convergence, reevaluate actual THOnB/Viscos/Mohr and assemble
    # with the unchanged final velocity; FEM hard-stops before any extra solve.
    p0=s.index('SUBROUTINE Pure ('); p1=s.index('END SUBROUTINE Pure',p0)
    p=s[p0:p1]
    updates=a.section(p,'\tCALL THOnB (basal, continuum_LRi, etaMax,','\tIF (iter > 1) THEN')
    fem=a.section(p,'\tCALL FEM (alpha, area, constr, detJ,','\tvRMS = 0.0D0')
    c0=p.index('IF (scoreB <= okToQt) THEN'); c1=p.index('!           Check whether iteration permit still exists:',c0)
    block=p[c0:c1]
    block=a.replace1(block,'\t\t RETURN', '''         OPEN(78,file='prior_refresh_stress.dat',status='new',action='write')
         DO i=1,numEl
           DO m=1,7
             WRITE(78,'(2I6,3(1X,ES26.17E3))') i,m,tauMat(:,m,i)
           END DO
         END DO
         CLOSE(78)
         OPEN(77,file='C11B_FINAL_REQUEST',status='new',action='write')
         WRITE(77,*) iter,scoreA,scoreB
         CLOSE(77)
'''+updates+fem+'''         STOP 78 ! final FEM must not return
''')
    p=p[:c0]+block+p[c1:]; s=s[:p0]+p+s[p1:]
    # Preserve actual LAPACK call; fail hard if it reports an error.
    s=a.replace1(s,'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )',
        'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )\nIF (info /= 0) STOP 83')
    return e,s


def load_vector(p,a):
    z=np.loadtxt(p); a.need(z.shape==(162,2) and np.array_equal(z[:,0],np.arange(1,163)) and np.isfinite(z).all(),'SOLUTION_INVENTORY'); return z[:,1]

def inf(x): return float(np.linalg.norm(x,ord=np.inf))
def ratio(x,y): return float(x/max(y,np.finfo(float).tiny))
def backerror(A,b,x): return ratio(inf(A@x-b),inf(A)*inf(x)+inf(b))
def relative(a,b): return ratio(inf(a-b),max(inf(a),inf(b)))

def analysis(work, parent, a):
    old=np.load(parent/'C11_MATRICES.npz'); held=old['held']; free=old['free']; target=old['target']
    iters=sorted(work.glob('iter_*_solution.dat')); a.need(1<=len(iters)<=MAX_ITER,'ITERATION_INVENTORY')
    a.need(len(list(work.glob('iter_*_pre.dat')))==len(iters)==len(list(work.glob('iter_*_post.dat'))),'ITERATION_MATRIX_INVENTORY')
    records=[]; prev=np.zeros(162)
    for j,p in enumerate(iters,1):
        prefix=f'iter_{j:03d}'; a.need(p.name==prefix+'_solution.dat','ITERATION_ORDER')
        A,b=a.matrix(work/(prefix+'_pre.dat')); B,c=a.matrix(work/(prefix+'_post.dat')); x=load_vector(p,a)
        if j==1:
            for v,k in ((A,'A_pre'),(b,'b_pre'),(B,'A_post'),(c,'b_post')): a.need(relative(v,old[k])<1e-12,'C11A_FIRST_MATRIX_DRIFT:'+k)
        top=float(np.diag(A).max()); a.need(top>0,'VBC_SCALE')
        expected=A.copy(); expected[held,:]=0; expected[held,held]=top
        rhs=b.copy(); rhs[held]=target*top
        a.need(np.array_equal(B,expected) and relative(c,rhs)<1e-14,'VBC_DRIFT')
        rr=a.svd_report(A[np.ix_(free,free)]); post=a.svd_report(B)
        bcerr=ratio(inf(x[held]-target),inf(target))
        delta=np.linalg.norm((x-prev).reshape(-1,2),axis=1).sum()
        scale=max(np.linalg.norm(x.reshape(-1,2),axis=1).sum(),np.linalg.norm(prev.reshape(-1,2),axis=1).sum())
        records.append({'iteration':j,'linear_backward_error':backerror(B,c,x),'held_relative_error':bcerr,
            'native_scoreB_reconstructed':ratio(delta,scale),'free_rank':rr['rank'],'free_cond2':rr['cond2'],
            'post_rank':post['rank'],'post_cond2':post['cond2'],'max_speed_m_s':float(np.linalg.norm(x.reshape(-1,2),axis=1).max())})
        prev=x
    A,b=a.matrix(work/'final_pre.dat'); B,c=a.matrix(work/'final_post.dat')
    nodes=np.loadtxt(work/'final_nodes.dat'); ip=np.loadtxt(work/'final_ip.dat')
    a.need(nodes.shape==(81,5) and ip.shape==(896,13) and np.isfinite(nodes).all() and np.isfinite(ip).all(),'FINAL_OUTPUT_INVENTORY')
    a.need(np.array_equal(nodes[:,0],np.arange(1,82)) and np.array_equal(ip[:,:2],np.array([(i,m) for i in range(1,129) for m in range(1,8)])),'FINAL_ID_ORDER')
    x=nodes[:,1:3].ravel(); base=nodes[:,3:5].ravel(); a.need(np.array_equal(x,prev),'FINAL_VELOCITY_MUTATED')
    a.need(np.array_equal(ip[:,-1],np.zeros(896)),'BASAL_ETA_NONZERO')
    top=float(np.diag(A).max()); a.need(top>0,'FINAL_VBC_SCALE')
    expected=A.copy(); expected[held,:]=0; expected[held,held]=top
    rhs=b.copy(); rhs[held]=target*top
    a.need(np.array_equal(B,expected) and relative(c,rhs)<1e-14,'FINAL_VBC_DRIFT')
    raw=(work/'C11B_FINAL_REQUEST').read_text().split(); a.need(len(raw)==3 and int(raw[0])==len(records),'NATIVE_CONVERGENCE_RECEIPT')
    score=float(raw[2]); a.need(abs(score-records[-1]['native_scoreB_reconstructed'])<1e-12 and score<=NATIVE_TOL,'NATIVE_SCORE_DRIFT')
    prior=np.loadtxt(work/'prior_refresh_stress.dat')
    a.need(prior.shape==(896,5) and np.isfinite(prior).all() and np.array_equal(prior[:,:2],ip[:,:2]),'PRIOR_STRESS_INVENTORY')
    old_stress=prior[:,2:5]; new_stress=ip[:,6:9]
    stress_scale=max(float(np.max(abs(old_stress))),float(np.max(abs(new_stress))))
    stress_refresh=ratio(float(np.max(abs(new_stress-old_stress))),stress_scale)
    # Original unconstrained residual. External Dirichlet reaction on modeled sheet = residual on held DOFs.
    internal=A@x+(base-b); residual=internal-base
    reaction=np.zeros(162); reaction[held]=residual[held]
    free_res=ratio(inf(residual[free]),max(inf(internal[free]),inf(base[free]),inf(reaction)))
    # Independent native quadrature of integrated relative stress : strain rate.
    w=ip[:,2]; strain=ip[:,3:6]; stress=ip[:,6:9]; a.need(np.all(w>0),'QUADRATURE_AREA')
    power_density=stress[:,0]*strain[:,0]+stress[:,1]*strain[:,1]+2*stress[:,2]*strain[:,2]
    qpower=float(w@power_density); alg=float(x@internal); gpe=float(x@base); boundary=float(x@reaction)
    power_scale=max(abs(qpower),abs(alg),abs(gpe)+abs(boundary),float(w@abs(power_density)))
    qerr=ratio(abs(qpower-alg),power_scale); werr=ratio(abs(qpower-gpe-boundary),power_scale)
    # Tangent vectors and torques in runtime frame; a proper rotation preserves norms.
    package=a.read(parent.parent/'R6_THERMO_C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_NEW01/COMPLETE_CANDIDATE_INPUT_PACKAGE.json')
    ll=np.deg2rad(np.array([r['runtime_lat_lon_deg'] for r in package['G4_mapping']['nodes']]))
    lat,lon=ll.T; pos=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
    south=np.column_stack((np.sin(lat)*np.cos(lon),np.sin(lat)*np.sin(lon),-np.cos(lat)))
    east=np.column_stack((-np.sin(lon),np.cos(lon),np.zeros(81)))
    def xyz(y):
        z=y.reshape(81,2); return z[:,0,None]*south+z[:,1,None]*east
    radius=float(package['lr_native_parameters']['radius'])
    fxyz=xyz(base+reaction); ixyz=xyz(internal); dxyz=ixyz-fxyz
    force_scale=float(np.linalg.norm(ixyz,axis=1).sum()+np.linalg.norm(fxyz,axis=1).sum())
    torque_scale=radius*force_scale
    ff=float(np.linalg.norm(dxyz.sum(axis=0))); tt=float(np.linalg.norm(np.cross(radius*pos,dxyz).sum(axis=0)))
    final_rank=a.svd_report(A[np.ix_(free,free)]); final_post=a.svd_report(B)
    screen=all(r['linear_backward_error']<=LINEAR_LIMIT and r['held_relative_error']<=BC_REL_LIMIT and r['free_rank']==98 and r['post_rank']==162 for r in records)
    screen=bool(screen and final_rank['rank']==98 and final_post['rank']==162 and free_res<=NONLINEAR_SCREEN and werr<=POWER_SCREEN and qerr<=QUADRATURE_SCREEN and stress_refresh<=STRESS_REFRESH_SCREEN)
    np.savez(work/'C11B_FINAL_STATE.npz',velocity=x.reshape(81,2),strain_rate=strain.reshape(128,7,3),tau_relative=stress.reshape(128,7,3),quadrature_area=w.reshape(128,7),reaction=reaction.reshape(81,2),free_residual=residual[free],A_pre=A,b_pre=b,A_post=B,b_post=c,held=held,free=free)
    return {'native_convergence':True,'iterations':records,'native_final_scoreB':score,'first_linearization_reproduced':True,
        'final_free_rank':final_rank,'final_post_rank':final_post,'stress_refresh_relative_max_component':stress_refresh,'stress_refresh_max_N_per_m':float(np.max(abs(new_stress-old_stress))),'final_free_relative_residual':free_res,
        'final_free_residual_max_N':inf(residual[free]),'quadrature_power_W':qpower,'algebraic_internal_power_W':alg,
        'native_fixed_load_power_W':gpe,'Dirichlet_reaction_power_W':boundary,'quadrature_power_relative_defect':qerr,
        'work_balance_relative_defect':werr,'minimum_relative_stress_power_density_W_m2':float(power_density.min()),
        'negative_power_density_count':int(np.count_nonzero(power_density<0)),
        'force_balance_weak_form_defect_N':ff,'force_balance_weak_form_relative_defect':ratio(ff,force_scale),
        'torque_balance_weak_form_defect_N_m':tt,'torque_balance_weak_form_relative_defect':ratio(tt,torque_scale),
        'max_final_speed_m_s':float(np.linalg.norm(x.reshape(81,2),axis=1).max()),'max_strain_component_s_inv':float(np.max(abs(strain))),
        'basal_tangential_eta_zero':True,'screen_pass':screen,
        'screen_limits':{'linear_backward':LINEAR_LIMIT,'held_relative':BC_REL_LIMIT,'free_residual':NONLINEAR_SCREEN,'work':POWER_SCREEN,'quadrature':QUADRATURE_SCREEN,'stress_refresh':STRESS_REFRESH_SCREEN,'native_scoreB':NATIVE_TOL},
        'limitations':['Final reassembly is one constitutive refresh; measured stress change is a fixed-point screen, not a proof of full stress convergence.', 'Force and torque defects use assembled nodal terms, not independent exterior traction quadrature.', 'Relative stress power is not an independently validated thermodynamic dissipation budget.', 'Cap activation and sensitivity, natural exterior, G4, and physical acceptance remain open.'],
        'physical_solves':1,'physical_T1':None,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}


def main():
    import hashlib
    helper=Path(__file__).with_name('arcana_c11a_assembly.py')
    if hashlib.sha256(helper.read_bytes()).hexdigest()!=A_SCRIPT_PIN: raise RuntimeError('C11A_HELPER_HASH')
    import arcana_c11a_assembly as a
    from experiments.r6_thermo_provider_pilot_v1 import c10_native as native
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    ap=argparse.ArgumentParser(); ap.add_argument('--authorize-controlled-solve',choices=[a.SCENARIO],required=True); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==a.SHA,'HEAD_MISMATCH')
    a.need(not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip(),'DIRTY_CHECKOUT')
    parent=c10.OUT.with_name('R6_THERMO_C11A_OPERATOR_ASSEMBLY_NEW01'); m=a.read(parent/'MANIFEST.json')
    a.need(a.sha(parent/'MANIFEST.json')==A_PIN and m['status']==A_STATUS and m['physical_solves']==0 and m['C10_manifest_sha256']==a.PIN,'C11A_MANIFEST')
    inventory={str(p.relative_to(parent)):a.sha(p) for p in sorted(parent.rglob('*')) if p.is_file() and p!=parent/'MANIFEST.json'}
    a.need(inventory==m['files'],'C11A_INVENTORY')
    c=a.read(c10.OUT/'MANIFEST.json'); a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and all(c[k]==v for k,v in c10.SCOPE.items()),'C10_SCOPE')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json'); a.need(inv==c['files'],'C10_INVENTORY')
    prior_b=c10.OUT.with_name('R6_THERMO_C11B_FIRST_CONTROLLED_SOLVE_NEW01')
    bm=a.read(prior_b/'MANIFEST.json')
    a.need(a.sha(prior_b/'MANIFEST.json')==B_PIN and bm['status']==B_STATUS and bm['source_sha']==a.SHA and bm['C11A_manifest_sha256']==A_PIN and bm['physical_solves']==1 and bm['physical_T1'] is None and bm['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False,'C11B_PARENT_MANIFEST')
    b_inventory={str(p.relative_to(prior_b)):a.sha(p) for p in sorted(prior_b.rglob('*')) if p.is_file() and p!=prior_b/'MANIFEST.json'}
    a.need(b_inventory==bm['files'],'C11B_PARENT_INVENTORY')
    old_result=a.read(prior_b/'C11B_ANALYSIS.json')
    a.need(old_result['native_convergence'] is True and old_result['screen_pass'] is False and len(old_result['iterations'])==22,'C11B_PARENT_RESULT')
    a.need(old_result['screen_limits']=={'linear_backward':LINEAR_LIMIT,'held_relative':BC_REL_LIMIT,'free_residual':NONLINEAR_SCREEN,'work':POWER_SCREEN,'quadrature':QUADRATURE_SCREEN},'C11B_SCREEN_DRIFT')
    a.need(a.sha(Path(__file__).with_name('arcana_c11b_first_solve.py'))==B_SCRIPT_PIN,'C11B_SCRIPT_HASH')
    work=args.output.resolve(); a.need(not work.exists() and not work.is_relative_to(root) and not work.is_relative_to(parent) and not work.is_relative_to(c10.OUT) and not work.is_relative_to(prior_b),'OUTPUT_NOT_FRESH')
    work.mkdir(); a.write(work/'AUTHORIZATION_RECEIPT.json',{'scenario':args.authorize_controlled_solve,'operator_CLI_authorized_controlled_solve':True,'C11A_manifest':A_PIN,'C10_manifest':a.PIN,'source_sha':a.SHA,'C11B_manifest':B_PIN,'scope':'one serial numerical convergence retry, same native hydrostatic smooth trace free slip; no physical model changes, no T1, no canon','D_024':'ACTIVE','D_025':'ACTIVE','physical_T1':None,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False})
    for k in ('regional.feg','regional_PRE.dat','controlled.bcs','regional.in','runtime.control','regional_reporting_plates.dat'): shutil.copyfile(c10.OUT/k,work/k)
    # Change ONLY two LR numerical controls using the actual native serializer.
    baseline=a.read(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json')['lr_native_parameters']
    a.need(baseline['maxItr']==50 and baseline['okToQt']==5e-4,'LR_ORIGINAL_CONTROL_DRIFT')
    original=native.serialize_lr(baseline)
    a.need(original.encode()==(c10.OUT/'regional.in').read_bytes(),'LR_BASELINE_REPLAY')
    updated=dict(baseline,maxItr=MAX_ITER,okToQt=NATIVE_TOL)
    new_deck=native.serialize_lr(updated)
    a.need([i for i,(x,y) in enumerate(zip(original.splitlines(),new_deck.splitlines(),strict=True)) if x!=y]==[native.LR_FIELDS.index('maxItr')+1,native.LR_FIELDS.index('okToQt')+1],'LR_NONNUMERICAL_MUTATION')
    (work/'regional.in').write_text(new_deck)
    a.write(work/'NUMERICAL_RETRY_POLICY.json',{'C11B_manifest':B_PIN,'original_maxItr':50,'maxItr':MAX_ITER,'original_okToQt':5e-4,'okToQt':NATIVE_TOL,'unchanged_screens':old_result['screen_limits'],'additional_stress_refresh_screen':STRESS_REFRESH_SCREEN,'physics_changed':False,'baseline_comparison':{k:old_result[k] for k in ('native_final_scoreB','final_free_relative_residual','work_balance_relative_defect','max_final_speed_m_s','max_strain_component_s_inv')}})
    src=root/native.VENDOR
    e,s=native_sources((src/'SHELLS_v5.0.f90').read_text(),(src/'MOD_Shells.f90').read_text(),a,native)
    for k in native.STOCK: shutil.copyfile(src/k,work/k)
    (work/'MOD_Shells.f90').write_text(s); (work/'SHELLS_solve.f90').write_text(e)
    shutil.copyfile(c10.OUT/'MOD_ArcanaRuntime.regional.f90',work/'MOD_ArcanaRuntime.f90')
    driver=Path(native.__file__).with_name('c10_pre_solve_driver.f90').read_text()
    anchor='  if (Biot/=1d0 .and. Biot/=0d0) stop 16'
    driver=a.replace1(driver,anchor,anchor+"\n  if (maxItr/=250 .or. abs(okToQt-5d-7)>1d-18) stop 84\n  print '(A,I6,1X,ES26.17E3)','C11BR1_NATIVE_CONTROLS ',maxItr,okToQt")
    (work/'driver.f90').write_text(driver)
    compiler=native.COMPILER; lib=native.LIB; sources=(native.STOCK[0],'MOD_ArcanaRuntime.f90',*native.STOCK[1:],'SHELLS_solve.f90','driver.f90')
    cmd=[str(compiler),'-O0','-Mbackslash','-Kieee','-Mbounds',*sources,'-L'+str(lib),'-Wl,-rpath,'+str(lib),'-llapack','-lblas','-o','controlled_solve.exe']
    env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    print('C11BR1_BUILD',flush=True)
    with (work/'build.log').open('x') as log: subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    exe=work/'controlled_solve.exe'; a.write(work/'BUILD_IDENTITY.json',{'compiler_sha256':a.sha(compiler),'exe_sha256':a.sha(exe),'argv':cmd,'source_sha256':{x:a.sha(work/x) for x in sources},'lapack_blas_sha256':{x:a.sha(lib/x) for x in ('liblapack.so','libblas.so')}})
    print('C11BR1_RUN',flush=True)
    with (work/'run.log').open('x') as log:
        proc=subprocess.Popen(['/usr/bin/time','-v','-o','run.time',str(exe)],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=a.limit,start_new_session=True)
        try:
            rc=proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
            rc=124
    log_text=(work/'run.log').read_text()
    control_lines=[l for l in log_text.splitlines() if l.startswith('C11BR1_NATIVE_CONTROLS ')]
    if rc==0:
        a.need(len(control_lines)==1,'NATIVE_CONTROL_READBACK')
        parsed=control_lines[0].split()
        a.need(len(parsed)==3 and int(parsed[1])==MAX_ITER and abs(float(parsed[2])-NATIVE_TOL)<1e-18,'NATIVE_CONTROL_READBACK_DRIFT')
    if rc!=0 or 'C11B_FINAL_REASSEMBLY_STOP_BEFORE_EXTRA_SOLVER' not in (work/'run.log').read_text() or (work/'FatalError.txt').exists():
        status='C11BR1_BLOCKED_NATIVE_STOP_OR_NONCONVERGENCE'
        completed=len(list(work.glob('iter_*_solution.dat')))
        a.write(work/'FAILURE_RECEIPT.json',{'native_exit':rc,'completed_linear_solves':completed,'native_convergence_verified':False,'physical_T1':None})
        a.write(work/'MANIFEST.json',{'status':status,'C11B_manifest_sha256':B_PIN,'C11A_manifest_sha256':A_PIN,'C10_manifest_sha256':a.PIN,'source_sha':a.SHA,'physical_T1':None,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,'files':{str(p.relative_to(work)):a.sha(p) for p in sorted(work.rglob('*')) if p.is_file()}})
        print('C11BR1_MANIFEST_SHA256',a.sha(work/'MANIFEST.json')); print('NATIVE_EXIT',rc,'COMPLETED_LINEAR_SOLVES',completed); print(status); return 3
    r=analysis(work,parent,a)
    r['previous_C11B_manifest']=B_PIN
    r['comparison_to_C11B']={k:{'previous':old_result[k],'current':r[k]} for k in ('native_final_scoreB','final_free_relative_residual','work_balance_relative_defect','max_final_speed_m_s','max_strain_component_s_inv')}
    a.write(work/'C11BR1_ANALYSIS.json',r)
    status='C11BR1_CONTROLLED_SOLVE_NUMERICAL_SCREEN_PASS__SENSITIVITY_REQUIRED' if r['screen_pass'] else 'C11BR1_NATIVE_CONVERGED__BLOCKED_DIAGNOSTIC_SCREEN'
    a.write(work/'MANIFEST.json',{'status':status,'C11B_manifest_sha256':B_PIN,'C11A_manifest_sha256':A_PIN,'C10_manifest_sha256':a.PIN,'source_sha':a.SHA,'physical_solves':1,'physical_T1':None,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,'files':{str(p.relative_to(work)):a.sha(p) for p in sorted(work.rglob('*')) if p.is_file()}})
    print('C11BR1_MANIFEST_SHA256',a.sha(work/'MANIFEST.json')); print(json.dumps({k:v for k,v in r.items() if k not in ('iterations','final_free_rank','final_post_rank')},indent=2)); print('ITERATIONS',len(r['iterations'])); print('MAX_LINEAR_BACKWARD',max(x['linear_backward_error'] for x in r['iterations'])); print('FINAL_FREE_COND2',r['final_free_rank']['cond2']); print(status)
    return 0 if r['screen_pass'] else 2

if __name__=='__main__': raise SystemExit(main())
