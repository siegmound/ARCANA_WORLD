#!/usr/bin/env python3
"""C11D native Balanc cross-check of the archived S0 state, no solve or time advance.
Balanc independently integrates stresses over triangles; exterior reactions are
inferred in its weak form, not an independently reconstructed side stress trace.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11br1_convergence as r1
import arcana_c11c_sensitivity as c

CAP_PIN='d44d4893bd82f391a610938cd5c7be31474e60860444002ff58d88f754d5fa30'
CAP_STATUS='C11C_CAP_DIAGNOSTICS_BOUNDED__PHYSICAL_REVIEW_REQUIRED'
REC_PIN='e3e16a4ea9a994e36420101122dcb5b68ebe8785821ff1c36891a8d1f8938611'
REC_STATUS='C11CR1_RECOVERY_RETAINED__DIAGNOSTIC_GAPS'
# Cross-implementation agreement at identical state, not a physical error budget.
AGREEMENT=1e-9

def sources(stock,subs,native):
    e=native.generated_source(stock).split('       v(1,:) = 2d-9')[0]
    bal=a.section(stock,'       CALL Balanc (alphaT, area, conduc, constr,','!   Output the solution:')
    edge=a.section(stock,'       CALL Fixed (alphaT, area, conduc,','!  -Create and solve a thin-plate')
    e+='''
       open(71,file='archived_nodes.dat',status='old',action='read')
       do i=1,numNod
         read(71,*,iostat=ios) n,v(:,i)
         if (ios/=0 .or. n/=i) stop 90
       end do
       close(71)
       open(71,file='archived_ip.dat',status='old',action='read')
       do i=1,numEl
         do j=1,7
           read(71,*,iostat=ios) n,LRi,tauMat(:,j,i)
           if (ios/=0 .or. n/=i .or. LRi/=j) stop 91
         end do
       end do
       close(71)
       call EDot(dXS,dYS,fPSfer,mxEl,mxNode,nodes,numEl,radius,sita,v,eRate)
       eta=0d0
       sigHB=0d0
       fC=0d0
       fTStar=0d0
       fIMuDZ=0d0
       open(72,file='fixed_total.dat',status='new')
       do i=1,nDOF
         write(72,'(I6,1X,ES26.17E3)') i,fBase(i)
       end do
       close(72)
'''+bal+'''
       open(73,file='balance_components.dat',status='new')
       do i=1,nDOF
         write(73,'(I6,6(1X,ES26.17E3))') i,comp(:,i)
       end do
       close(73)
       if (any(sigHB/=0d0)) stop 92
       doFB1=.false.
       doFB2=.false.
       doFB3=.true.
       doFB4=.false.
'''+edge+'''
       open(74,file='fixed_side_only.dat',status='new')
       do i=1,nDOF
         write(74,'(I6,1X,ES26.17E3)') i,fBase(i)
       end do
       close(74)
       open(75,file='balance_ip.dat',status='new')
       do i=1,numEl
         do j=1,7
           write(75,'(2I6,7(1X,ES26.17E3))') i,j,eRate(:,j,i),tauMat(:,j,i),tauZZI(j,i)
         end do
       end do
       close(75)
       print '(A)','C11D_BALANC_NO_SOLVER_STOP'
       stop 0
end subroutine Shells_v5p0
end module SHELLS
'''
    a.need(not __import__('re').search(r'(?im)^\s*call\s+(pure|fem|solver)\b',e),'SOLVER_ENTRY_REACHABLE')
    # Extra guard: any accidental call to LAPACK stops before factorization.
    subs=a.replace1(subs,'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )','STOP 93 ! C11D solve forbidden')
    return e,subs

def vector(path,ncol):
    z=np.loadtxt(path)
    a.need(z.shape==(162,ncol+1) and np.array_equal(z[:,0],np.arange(1,163))
           and np.isfinite(z).all(),'BALANCE_VECTOR:'+path.name)
    return z[:,1:] if ncol>1 else z[:,1]

def geometry(package,x,strain):
    from experiments.shellset_regional_explore_v1.solution_mapping import bind_solution
    mapping=package['G4_mapping']
    mapped=bind_solution(mapping,{i+1:v for i,v in enumerate(x.reshape(81,2))},
                         {i+1:v for i,v in enumerate(strain)})
    ll=np.deg2rad(np.array([n['runtime_lat_lon_deg'] for n in mapping['nodes']]))
    lat,lon=ll.T
    pos=np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
    south=np.column_stack((np.sin(lat)*np.cos(lon),np.sin(lat)*np.sin(lon),-np.cos(lat)))
    east=np.column_stack((-np.sin(lon),np.cos(lon),np.zeros(81)))
    radius=float(package['lr_native_parameters']['radius'])
    pids={row['parent_id']:i for i,row in enumerate(mapping['nodes'])}
    tris=np.array([[pids[k] for k in row['parent_node_ids']] for row in mapping['elements']])
    edges=sorted({tuple(sorted((int(tri[i]),int(tri[(i+1)%3])))) for tri in tris for i in range(3)})
    u=np.array([v[0] for v in edges]); w=np.array([v[1] for v in edges])
    length=radius*np.arctan2(np.linalg.norm(np.cross(pos[u],pos[w]),axis=1),np.sum(pos[u]*pos[w],axis=1))
    vel=x.reshape(81,2); xyz=vel[:,0,None]*south+vel[:,1,None]*east
    year=365.25*86400
    maxspeed=float(np.linalg.norm(xyz,axis=1).max())
    div=strain[:,:,0]+strain[:,:,1]
    return mapped,{'min_edge_m':float(length.min()),'max_speed_m_s':maxspeed,
        'one_year_max_displacement_m':maxspeed*year,
        'one_year_displacement_over_min_edge':maxspeed*year/float(length.min()),
        'one_year_max_abs_horizontal_trace_times_dt':float(np.max(abs(div))*year),
        'geometry_change_fraction_provisional':1e-4,
        'scope':'Kinematic timestep readiness only, not a mesh update or a material flux budget.'},pos,south,east,radius

def analyse(work,state,package):
    x=state['velocity'].ravel(); held=state['held']; free=state['free']
    A=state['A_pre']; b=state['b_pre']
    fixed=vector(work/'fixed_total.dat',1)
    side=vector(work/'fixed_side_only.dat',1)
    comp=vector(work/'balance_components.dat',6)
    ip=np.loadtxt(work/'balance_ip.dat')
    strain=state['strain_rate']; stress=state['tau_relative']; weights=state['quadrature_area']
    a.need(ip.shape==(896,9) and np.isfinite(ip).all() and
           np.array_equal(ip[:,:2],np.array([(i,j) for i in range(1,129) for j in range(1,8)])),'IP_INVENTORY')
    stress_error=r1.relative(ip[:,5:8].ravel(),stress.ravel())
    strain_error=r1.relative(ip[:,2:5].ravel(),strain.ravel())
    a.need(stress_error<=AGREEMENT and strain_error<=AGREEMENT,'ARCHIVED_FIELD_READBACK')
    a.need(np.all(comp[:,1:3]==0) and np.all(comp[:,4]==0),'FAULT_OR_BASAL_TANGENTIAL')
    # Fixed = negative volumetric tauZZ contribution + basal normal + side.
    # Balanc uses total stress tauMat + tauZZ*I. Its Bounds includes the
    # side pressure anomaly, so subtract this exactly once for Dirichlet load.
    residual=A@x-b
    direct=comp[:,5]-side
    balance_error=r1.relative(direct,residual)
    held_reaction=np.zeros(162); held_reaction[held]=direct[held]
    reaction_error=r1.relative(held_reaction,state['reaction'].ravel())
    scale=max(r1.inf(comp[:,0]),r1.inf(comp[:,3]),r1.inf(side),r1.inf(held_reaction))
    free_defect=r1.ratio(r1.inf(direct[free]),scale)
    q=float(np.sum(weights*(stress[:,:,0]*strain[:,:,0]+stress[:,:,1]*strain[:,:,1]+2*stress[:,:,2]*strain[:,:,2])))
    qzz=float(np.sum(weights*ip[:,8].reshape(128,7)*(strain[:,:,0]+strain[:,:,1])))
    full_work=float(x@comp[:,0])
    full_work_error=r1.ratio(abs(full_work-q-qzz),max(abs(full_work),abs(q)+abs(qzz)))
    fixed_reconstructed=comp[:,3]+side-(comp[:,0]-(A@x+fixed-b))
    fixed_error=r1.relative(fixed_reconstructed,fixed)
    mapped,dt,pos,south,east,radius=geometry(package,x,strain)
    def xyz(y):
        u=y.reshape(81,2); return u[:,0,None]*south+u[:,1,None]*east
    groups={'total_stress_weak_form':comp[:,0],'basal_normal':comp[:,3],
            'native_side_pressure':side,'Dirichlet_reaction':held_reaction}
    sums={}
    for k,f in groups.items():
        vec=xyz(f); tor=np.cross(radius*pos,vec)
        sums[k]={'force_xyz_N':vec.sum(axis=0).tolist(),'torque_xyz_N_m':tor.sum(axis=0).tolist(),
                 'sum_force_norm_N':float(np.linalg.norm(vec,axis=1).sum()),
                 'sum_torque_norm_N_m':float(np.linalg.norm(tor,axis=1).sum()),'power_W':float(x@f)}
    net=xyz(comp[:,0]-comp[:,3]-side-held_reaction)
    force=float(np.linalg.norm(net.sum(axis=0))); torque=float(np.linalg.norm(np.cross(radius*pos,net).sum(axis=0)))
    den=sum(t['sum_force_norm_N'] for t in sums.values())
    den_t=sum(t['sum_torque_norm_N_m'] for t in sums.values())
    errors={'archived_stress_readback':stress_error,'archived_strain_readback':strain_error,
       'weak_form_residual_agreement':balance_error,'held_reaction_agreement':reaction_error,
       'total_stress_work_quadrature_agreement':full_work_error,'fixed_load_decomposition_agreement':fixed_error}
    screen=all(v<=AGREEMENT for v in errors.values()) and free_defect<=1e-3
    a.write(work/'G4_PARENT_BOUND_FIELDS.json',mapped)
    return {'screen_pass':screen,'cross_implementation_agreement_limit':AGREEMENT,'errors':errors,
       'free_relative_defect':free_defect,'force_balance_relative_defect':r1.ratio(force,den),
       'torque_balance_relative_defect':r1.ratio(torque,den_t),'components':sums,
       'relative_stress_power_W':q,'vertical_reference_stress_power_W':qzz,
       'kinematic_readiness':dt,'native_fault_and_basal_tangential_terms_exact_zero':True,
       'limitations':['Balanc is an independent native volume weak-form stress integration, not direct exterior stress traction quadrature.',
          'Fixed side pressure integrated separately; Dirichlet reaction is still inferred from weak form.',
          'No physical acceptance, natural exterior, material transport or thermodynamic dissipation closure.'],**c.SCOPE}

def main():
    from experiments.r6_thermo_provider_pilot_v1 import c10_native as native
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    here=Path(__file__).resolve().parent
    for n,pin in [('arcana_c11a_assembly.py',r1.A_SCRIPT_PIN),
                  ('arcana_c11br1_convergence.py',c.R1_SCRIPT)]:
        a.need(a.sha(here/n)==pin,'RUNNER_HASH:'+n)
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA and
           not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    caps=c10.OUT.with_name('R6_THERMO_C11C_CAP_BOUNDS_NEW01')
    rec=c10.OUT.with_name('R6_THERMO_C11CR1_RECOVERY_NEW01')
    base=c10.OUT.with_name('R6_THERMO_C11BR1_CONVERGENCE_NEW01')
    c.verified(caps,CAP_PIN,CAP_STATUS); c.verified(rec,REC_PIN,REC_STATUS)
    c.verified(base,c.R1_PIN,c.R1_STATUS)
    audit=a.read(caps/'CAP_BOUNDS_REPORT.json')
    a.need(set(audit['cases'])==set(c.CASES) and all(v['mechanical_analysis']=='PASS' and
          v['cap_analysis']=='BOUNDED_NOT_EXACT' for v in audit['cases'].values()),'C11C_RECEIPTS')
    m=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN and all(m[k]==v for k,v in c10.SCOPE.items()),'C10_SCOPE')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==m['files'],'C10_INVENTORY')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in
         (root,c10.OUT,caps,rec,base)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'cap_manifest':CAP_PIN,'recovery_manifest':REC_PIN,'R1_manifest':c.R1_PIN,
        'runner_sha256':a.sha(Path(__file__)),'additional_native_solves':0,
        'native_volume_balance_only':True,'cross_implementation_limit':AGREEMENT,**c.SCOPE})
    with np.load(base/'C11B_FINAL_STATE.npz') as state:
        with np.load(rec/'S0/C11B_FINAL_STATE.npz') as replay:
            for n in ('velocity','strain_rate','tau_relative','reaction'):
                a.need(np.array_equal(state[n],replay[n]),'S0_DRIFT:'+n)
        np.savetxt(out/'archived_nodes.dat',np.column_stack((np.arange(1,82),state['velocity'])),fmt=['%d','%.17e','%.17e'])
        ids=np.array([(i,j) for i in range(1,129) for j in range(1,8)])
        np.savetxt(out/'archived_ip.dat',np.column_stack((ids,state['tau_relative'].reshape(896,3))),
                   fmt=['%d','%d','%.17e','%.17e','%.17e'])
        for n in ('regional.feg','regional_PRE.dat','controlled.bcs','runtime.control','regional_reporting_plates.dat'):
            shutil.copyfile(c10.OUT/n,out/n)
        shutil.copyfile(base/'regional.in',out/'regional.in')
        src=root/native.VENDOR
        for n in native.STOCK: shutil.copyfile(src/n,out/n)
        entry,subs=sources((src/'SHELLS_v5.0.f90').read_text(),(src/'MOD_Shells.f90').read_text(),native)
        (out/'MOD_Shells.f90').write_text(subs); (out/'SHELLS_balance.f90').write_text(entry)
        shutil.copyfile(c10.OUT/'MOD_ArcanaRuntime.regional.f90',out/'MOD_ArcanaRuntime.f90')
        shutil.copyfile(Path(native.__file__).with_name('c10_pre_solve_driver.f90'),out/'driver.f90')
        sources_list=(native.STOCK[0],'MOD_ArcanaRuntime.f90',*native.STOCK[1:],'SHELLS_balance.f90','driver.f90')
        compiler=native.COMPILER; lib=native.LIB
        cmd=[str(compiler),'-O0','-Mbackslash','-Kieee','-Mbounds',*sources_list,'-L'+str(lib),
             '-Wl,-rpath,'+str(lib),'-llapack','-lblas','-o','balance_only.exe']
        env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        print('C11D_BUILD',flush=True)
        with (out/'build.log').open('x') as log:
            subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        exe=out/'balance_only.exe'
        a.write(out/'BUILD_IDENTITY.json',{'argv':cmd,'compiler_sha256':a.sha(compiler),'exe_sha256':a.sha(exe),
            'source_sha256':{n:a.sha(out/n) for n in sources_list},
            'lapack_blas_sha256':{n:a.sha(lib/n) for n in ('liblapack.so','libblas.so')}})
        print('C11D_BALANCE_ONLY_RUN',flush=True)
        with (out/'run.log').open('x') as log:
            subprocess.run(['/usr/bin/time','-v','-o','run.time',str(exe)],cwd=out,env=env,
                           stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,preexec_fn=a.limit)
        a.need('C11D_BALANC_NO_SOLVER_STOP' in (out/'run.log').read_text() and not (out/'FatalError.txt').exists(),'HARD_STOP')
        report=analyse(out,state,a.read(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json'))
    status='C11D_NATIVE_WEAK_FORM_CROSSCHECK_PASS__EXTERIOR_AND_TRANSPORT_PENDING' if report['screen_pass'] else 'C11D_BALANCE_DIAGNOSTIC_BLOCKED'
    a.write(out/'C11D_ANALYSIS.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'cap_manifest_sha256':CAP_PIN,
        'R1_manifest_sha256':c.R1_PIN,'additional_native_solves':0,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('C11D_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if report['screen_pass'] else 2

if __name__=='__main__':
    raise SystemExit(main())
