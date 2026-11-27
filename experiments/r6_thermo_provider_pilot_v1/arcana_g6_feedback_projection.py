#!/usr/bin/env python3
"""G6: conservative nodal PRE/FEG projection of the G4/G5 experimental state.
Native input probe only; no new factorization or time advance.
Full parcel thermal state remains authoritative; nodal cubics are a lossy
mechanics-consumer view, not a replacement for the thermal archive.
"""
import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import numpy as np
import arcana_c11a_assembly as a
import arcana_c11c_sensitivity as c
import arcana_g4_controlled_transport as g4

G5_PIN='48fbfb6d452840c0086517d557acb6d1cc76850d500c4225aae007f75aeeec14'
G5_STATUS='G5_CONTROLLED_COLUMN_HEAT_UPDATE_PASS__THERMOMECHANICAL_FEEDBACK_PENDING'
G4_PIN='9207eefd69425a013a32e117a8f515b40682a269a0cf5495b238a87898af3747'
G4_STATUS='G4_CONTROLLED_MOVING_COLUMN_TRANSPORT_PASS__PHYSICAL_ACCEPTANCE_PENDING'
TOL={'mass_relative':1e-12,'heat_increment_relative':1e-5,
     'projection_cell_max_K':1e-5,'moho_flux_W_m2':2e-12,
     'moho_temperature_K':2e-7,'native_geometry_m':1e-6,'native_bc_m_s':2e-22}

def moments(coeff,alpha):
    x,w=np.polynomial.legendre.leggauss(4)
    B=((x+1)/2)[:,None]**np.arange(4)
    t=coeff@B.T
    den=np.sum((1-alpha[:,None]*t)*w/2,axis=1)
    mean=np.sum((1-alpha[:,None]*t)*t*w/2,axis=1)/den
    return B,w/2,t,den,mean

def incremental(d,alpha,B,w,t,den,mean):
    p=d@B.T
    newden=den-alpha*(p@w)
    delta=((1-2*alpha[:,None]*t+alpha[:,None]*mean[:,None])*p-
            alpha[:,None]*p*p)@w/newden
    return newden,delta

def fit(coeff,alpha,rho,k,cp,mass,area,target_cell,target_mean):
    """Two cubics, 6 constraints: surface/LAB temperature, Moho T and q,
    layer mass-specific sensible heat increments. Least-squares remaining DOF.
    Use small perturbations directly to avoid cancellation of absolute T.
    """
    B,w,t,den,mean=moments(coeff,alpha)
    n=target_cell.shape[1]
    x,wc=np.polynomial.legendre.leggauss(4)
    bx=((np.arange(n)[:,None]+(x+1)/2)/n)[:,:,None]**np.arange(4)
    tc=np.einsum('lk,jgk->ljg',coeff,bx)
    wc=wc/2
    basis=np.einsum('ljg,jgk,g->ljk',1-alpha[:,None,None]*tc,bx,wc)/np.einsum(
        'ljg,g->lj',1-alpha[:,None,None]*tc,wc)[:,:,None]
    A=np.zeros((2*n,8)); A[:n,:4]=basis[0]; A[n:,4:]=basis[1]
    target=target_cell.ravel()
    jac=(np.einsum('lg,gk,g->lk',1-2*alpha[:,None]*t+alpha[:,None]*mean[:,None],B,w)
         /den[:,None])
    d=np.zeros((2,4))
    for _ in range(8):
        nd,dm=incremental(d,alpha,B,w,t,den,mean)
        h=mass/(area*rho*nd)
        factor=k/h; ratio=factor[1]/factor[0]
        C=np.zeros((6,8)); C[0,0]=1.; C[1,4:]=1.
        C[2,:4]=1.; C[2,4]=-1.
        C[3,1:4]=[1,2,3]; C[3,5]=-ratio
        C[4,:4]=jac[0]; C[5,4:]=jac[1]
        rhs=np.array([0.,0.,coeff[1,0]-coeff[0].sum(),
            ratio*coeff[1,1]-coeff[0]@np.array([0,1,2,3]),
            target_mean[0]-dm[0]+jac[0]@d[0],
            target_mean[1]-dm[1]+jac[1]@d[1]])
        particular=np.linalg.lstsq(C,rhs,rcond=None)[0]
        _,sv,Vh=np.linalg.svd(C,full_matrices=True)
        a.need(sv[-1]>1e-6,'PROJECTION_CONSTRAINT_RANK')
        null=Vh[6:].T
        d=(particular+null@np.linalg.lstsq(A@null,target-A@particular,rcond=None)[0]).reshape(2,4)
    nd,dm=incremental(d,alpha,B,w,t,den,mean)
    h=mass/(area*rho*nd)
    evolved=coeff+d
    # Verify the serialized absolute polynomial as well as the small-increment fit.
    actual=evolved-coeff
    nd,dm=incremental(actual,alpha,B,w,t,den,mean)
    h=mass/(area*rho*nd)
    qmoho=k/h*np.array([evolved[0]@np.array([0,1,2,3]),evolved[1,1]])
    err=float(np.max(abs((A@actual.ravel())-target)))
    return evolved,h,dm,err,float(abs(qmoho[0]-qmoho[1]))

def selftest():
    coeff=np.array([[280.,500.,0.,0.],[780.,500.,0.,0.]])
    alpha=np.array([3e-5,3e-5]); rho=np.array([2800.,3300.])
    k=np.array([2.5,2.5]); cp=np.array([1000.,1200.])
    _,_,_,den,_=moments(coeff,alpha)
    mass=1e8*rho*den*30000
    p,h,dm,err,gap=fit(coeff,alpha,rho,k,cp,mass,1e8,np.zeros((2,16)),np.zeros(2))
    a.need(np.array_equal(p,coeff) and np.allclose(h,30000,rtol=1e-14) and gap<1e-12,'ZERO_UPDATE_TEST')
    p,h,dm,err,gap=fit(coeff,alpha,rho,k,cp,mass,1e8,np.full((2,16),1e-6),np.full(2,1e-6))
    a.need(np.max(abs(dm-1e-6))<1e-12 and gap<1e-12 and np.all(h>0),'HEAT_PROJECTION_TEST')
    print('G6_PROJECTION_SELFTEST_PASS',flush=True)

def project(s,z,thermal,package,original):
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS,RuntimeNode
    from arcana_worldsim.r6.shellset_mesh.coordinates import rotation_matrices
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg,write_feg
    t=np.asarray(s['transport_triangles_zero_based']).ravel()
    areas=np.repeat(np.asarray(z['area_m2'])/3,3)
    h4=np.asarray(z['thickness_m']).reshape(384,2)
    old_mass=np.asarray(s['layer_mass_kg']).reshape(384,2)
    coeff=np.asarray(s['normalized_depth_temperature_coefficients_K']).reshape(384,2,4)
    cap=thermal['heat_capacity_J_K']; dE=thermal['two_half_energy_increment_J']
    a.need(cap.shape==dE.shape==(384,2,64) and np.isfinite(dE).all()
        and np.array_equal(thermal['parcel_node_local_ids'].ravel()-1,t)
        and np.array_equal(thermal['element_parent_ids'],s['element_parent_ids']),'G5_PARCEL_BINDING')
    a.need(np.allclose(thermal['mass_kg'].sum(axis=-1),old_mass,rtol=1e-12,atol=0),'G5_MASS')
    mesh=parse_feg(original,mode='SHELLS_READY')
    forward,_=rotation_matrices()
    p=np.asarray(z['canonical_unit_xyz'])@forward.T
    lat=np.rad2deg(np.arcsin(np.clip(p[:,2],-1,1)))
    lon=np.rad2deg(np.arctan2(p[:,1],p[:,0]))
    rows=[]; nodes=[]; budgets=[]
    for i,tokens in enumerate(s['original_PRE_rows_tokens']):
        row=dict(zip(FIELDS,map(float,tokens),strict=True))
        a.need(row['node_id']==i+1 and row['runtime_branch_code']==1,'CONTINENTAL_ONLY')
        idx=np.flatnonzero(t==i)
        a.need(len(idx)>0 and np.all(coeff[idx]==coeff[idx[0]]),'NODAL_OWNER_PROFILE')
        area=float(areas[idx].sum()); mass=old_mass[idx].sum(axis=0)
        cellcap=cap[idx].sum(axis=0); cellenergy=dE[idx].sum(axis=0)
        target=cellenergy/cellcap
        targetmean=cellenergy.sum(axis=1)/cellcap.sum(axis=1)
        alpha,rho,k,cp=[np.array([row[role+'_'+key] for role in ('crust','mantle')]) for key in
            ('expansivity_k_1','density_kg_m3','conductivity_w_m_k','cp_j_kg_k')]
        co=coeff[idx[0]]
        fitco,h,dm,err,qgap=fit(co,alpha,rho,k,cp,mass,area,target,targetmean)
        hgeom=np.sum(areas[idx,None]*h4[idx],axis=0)/area
        # G4 volume projection before thermal expansion must already conserve mass.
        _,_,_,d0,_=moments(co,alpha)
        a.need(np.allclose(area*hgeom*rho*d0,mass,rtol=1e-12,atol=0),'GEOMETRIC_NODAL_MASS')
        _,_,_,den,_=moments(fitco,alpha)
        massnew=area*h*rho*den
        energynew=mass*cp*dm
        energywant=cellenergy.sum(axis=1)
        row.update(crust_thickness_m=float(h[0]),mantle_lithosphere_thickness_m=float(h[1]),
                   lab_depth_m=float(h.sum()),surface_temperature_k=float(fitco[0,0]),
                   surface_heat_flow_w_m2=float(k[0]/h[0]*fitco[0,1]),
                   moho_temperature_k=float(fitco[0].sum()),
                   moho_flux_w_m2=float(k[0]/h[0]*(fitco[0]@np.array([0,1,2,3]))),
                   lab_temperature_k=float(fitco[1].sum()),
                   lab_flux_w_m2=float(k[1]/h[1]*(fitco[1]@np.array([0,1,2,3]))))
        for j in range(2):
            row[f'layer{j+1}_z0_m']=float(h[:j].sum())
            row[f'layer{j+1}_z1_m']=float(h[:j+1].sum())
            for power,key in enumerate(('c0_k','c1_k_m','c2_k_m2','c3_k_m3')):
                row[f'layer{j+1}_{key}']=float(fitco[j,power]/h[j]**power)
        # Transient rate is T0 metadata required by legacy PRE branch schema;
        # not a recalculated physical derivative. Native reader has no consumer.
        rows.append(RuntimeNode(tuple(row[f] for f in FIELDS)).line())
        nodes.append(replace(mesh.nodes[i],latitude_deg=float(lat[i]),longitude_deg=float(lon[i]),
            crustal_thickness_m=float(h[0]),mantle_lithosphere_thickness_m=float(h[1]),
            heat_flow_w_m2=row['surface_heat_flow_w_m2']))
        budgets.append({'node_local_id':i+1,'parent_id':s['node_parent_ids'][i],
            'mass_kg':mass.tolist(),'projected_mass_kg':massnew.tolist(),
            'target_increment_J':energywant.tolist(),'projected_increment_J':energynew.tolist(),
            'heat_capacity_J_K':(mass*cp).tolist(),'max_cell_projection_error_K':err,
            'moho_flux_gap_W_m2':qgap,'moho_temperature_gap_K':float(abs(fitco[0].sum()-fitco[1,0])),
            'thermal_thickness_change_m':(h-hgeom).tolist()})
    newmesh=replace(mesh,nodes=tuple(nodes))
    # FEG round-trip and preserve original topology and elevation.
    body=write_feg(newmesh); restored=parse_feg(body,mode='SHELLS_READY')
    a.need(restored==newmesh and restored.elements==mesh.elements and restored.faults==mesh.faults,'FEG_ROUNDTRIP')
    return rows,body,budgets

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--authorize-controlled-feedback-projection',choices=[a.SCENARIO],required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    selftest()
    from experiments.r6_thermo_provider_pilot_v1 import run_c10_controlled_region as c10,c10_native as native
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    a.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.SHA
        and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'C10_CHECKOUT')
    g=c10.OUT.with_name('R6_THERMO_G4_CONTROLLED_TRANSPORT_NEW01')
    heat=c10.OUT.with_name('R6_THERMO_G5_COLUMN_HEAT_NEW01')
    gm=c.verified(g,G4_PIN,G4_STATUS); hm=c.verified(heat,G5_PIN,G5_STATUS)
    a.need(hm['G4_manifest_sha256']==G4_PIN and hm['source_sha']==a.SHA and
        all(hm[k]==v for k,v in c.SCOPE.items()),'G5_LINEAGE')
    a.need(a.read(heat/'G5_THERMAL_REPORT.json')['screen_pass'],'G5_SCREEN')
    cm=a.read(c10.OUT/'MANIFEST.json')
    a.need(a.sha(c10.OUT/'MANIFEST.json')==a.PIN,'C10_PIN')
    inv=c10.c09.c08.c07.c06.inventory(c10.OUT); inv.pop('MANIFEST.json')
    a.need(inv==cm['files'],'C10_INVENTORY')
    s=g4.unseal(g/'INITIAL_CHECKPOINT.json'); z=g4.unseal(g/'TWO_HALF_STEPS_CHECKPOINT.json')
    a.need(s['elapsed_years']==0 and z['elapsed_years']==1 and s['node_parent_ids']==z['node_parent_ids'],'G4_STATE')
    out=args.output.resolve()
    a.need(not out.exists() and not any(out.is_relative_to(p) for p in (root,g,heat,c10.OUT)),'OUTPUT_NOT_FRESH')
    out.mkdir()
    a.write(out/'POLICY.json',{'G4_manifest':G4_PIN,'G5_manifest':G5_PIN,'tolerances':TOL,
        'runner_sha256':a.sha(Path(__file__)),'projection':'Nodal mass lumping by original owner, constrained cubic perturbation; fixed reference material and cp; density from rho0(1-alpha*T).',
        'boundary':'Original local imposed south/east velocity components and elevation frozen; no natural exterior or isostasy.',
        'rate_metadata':'Original PRE transient rate retained only for compatibility, not an evolved derivative.',**c.SCOPE})
    with np.load(heat/'columns_64.npz') as thermal:
        rows,feg,budgets=project(s,z,thermal,a.read(c10.OUT/'COMPLETE_CANDIDATE_INPUT_PACKAGE.json'),
                                  (c10.OUT/'regional.feg').read_text())
    original=(c10.OUT/'regional_PRE.dat').read_text().splitlines()
    (out/'regional_PRE.dat').write_text('\n'.join([original[0],*rows])+'\n')
    (out/'regional.feg').write_text(feg)
    a.write(out/'NODAL_PROJECTION_BUDGETS.json',budgets)
    m=np.array([x['mass_kg'] for x in budgets]); mn=np.array([x['projected_mass_kg'] for x in budgets])
    E=np.array([x['target_increment_J'] for x in budgets]); En=np.array([x['projected_increment_J'] for x in budgets])
    capacity=np.array([x['heat_capacity_J_K'] for x in budgets])
    signal=float(np.max(abs(E/capacity)))
    projection={'mass_relative':float(np.max(abs(mn-m)/m)),
        'heat_increment_relative':float(np.max(abs(En-E)/capacity))/max(signal,1e-300),
        'heat_increment_target_J':E.sum(axis=0).tolist(),'heat_increment_projected_J':En.sum(axis=0).tolist(),
        'max_cell_projection_error_K':max(x['max_cell_projection_error_K'] for x in budgets),
        'max_moho_flux_gap_W_m2':max(x['moho_flux_gap_W_m2'] for x in budgets),
        'max_moho_temperature_gap_K':max(x['moho_temperature_gap_K'] for x in budgets),
        'max_thermal_thickness_change_m':float(np.max(abs(np.array([x['thermal_thickness_change_m'] for x in budgets])))),
        'max_nodal_mean_temperature_signal_K':signal}
    projection['screen_pass']=bool(projection['mass_relative']<=TOL['mass_relative'] and
        projection['heat_increment_relative']<=TOL['heat_increment_relative'] and
        projection['max_cell_projection_error_K']<=TOL['projection_cell_max_K'] and
        projection['max_moho_flux_gap_W_m2']<=TOL['moho_flux_W_m2'] and
        projection['max_moho_temperature_gap_K']<=TOL['moho_temperature_K'])
    a.write(out/'PROJECTION_REPORT.json',projection)
    print('G6_PROJECTION',json.dumps(projection),flush=True)
    probe={'status':'NOT_RUN'}
    if projection['screen_pass']:
        try:
            for n in ('controlled.bcs','runtime.control','regional_reporting_plates.dat','regional.in'):
                shutil.copyfile(c10.OUT/n,out/n)
            src=root/native.VENDOR
            for n in native.STOCK: shutil.copyfile(src/n,out/n)
            # Hard stop before Pure, stock native reader and S1B stress precompute.
            sub=(out/'MOD_Shells.f90').read_text()
            (out/'MOD_Shells.f90').write_text(a.replace1(sub,
                'CALL dgbsv ( n, kl, ku, nrhs, ab, ldab, ipiv, b, ldb, info )','STOP 93 ! G6 solve forbidden'))
            (out/'SHELLS_pre_solve.f90').write_text(native.generated_source((src/'SHELLS_v5.0.f90').read_text()))
            shutil.copyfile(c10.OUT/'MOD_ArcanaRuntime.regional.f90',out/'MOD_ArcanaRuntime.f90')
            shutil.copyfile(Path(native.__file__).with_name('c10_pre_solve_driver.f90'),out/'driver.f90')
            sources=(native.STOCK[0],'MOD_ArcanaRuntime.f90',*native.STOCK[1:],'SHELLS_pre_solve.f90','driver.f90')
            cmd=[str(native.COMPILER),'-O0','-Mbackslash','-Kieee','-Mbounds',*sources,
                '-L'+str(native.LIB),'-Wl,-rpath,'+str(native.LIB),'-llapack','-lblas','-o','probe.exe']
            env=os.environ.copy(); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
            print('G6_NATIVE_BUILD',flush=True)
            with (out/'build.log').open('x') as log:
                subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
            a.write(out/'BUILD_IDENTITY.json',{'argv':cmd,'source_sha256':{n:a.sha(out/n) for n in sources},
                 'compiler_sha256':a.sha(native.COMPILER),'exe_sha256':a.sha(out/'probe.exe'),
                 'library_sha256':{n:a.sha(native.LIB/n) for n in ('liblapack.so','libblas.so')}})
            print('G6_NATIVE_PRESOLVE',flush=True)
            with (out/'run.log').open('x') as log:
                subprocess.run(['/usr/bin/time','-v','-o','run.time',str(out/'probe.exe')],
                    cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,preexec_fn=a.limit)
            a.need('C10_STOP_AFTER_FIXED_BEFORE_PURE' in (out/'run.log').read_text()
                and not (out/'FatalError.txt').exists(),'NATIVE_HARD_STOP')
            data=native.parse_probe(out/'native_pre_solve.txt')
            base=native.parse_probe(c10.OUT/'native_pre_solve/hydrostatic/native_pre_solve.txt')
            from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
            pre=np.array([[float(x) for x in row.split()] for row in rows])
            expected=pre[:,[FIELDS.index('crust_thickness_m'),FIELDS.index('mantle_lithosphere_thickness_m')]]
            nd=np.array(data['NODE']); old=np.array(base['NODE'])
            ip=np.array(data['IP']); oi=np.array(base['IP'])
            # NODE: id, reporting slot, elevation, crust, mantle, sigZZ, tauZZ, fixed S,E.
            geom=float(np.max(abs(nd[:,3:5]-expected)))
            bc=float(np.max(abs(np.array(data['BC'])[:,3:]-np.array(base['BC'])[:,3:])))
            a.need(data['SIZE']==base['SIZE'] and np.array_equal(nd[:,:3],old[:,:3]) and
                geom<=TOL['native_geometry_m'] and bc<=TOL['native_bc_m_s'] and
                np.all(ip[:,-3:]==0),'NATIVE_READBACK')
            probe={'status':'PASS','max_nodal_thickness_readback_error_m':geom,'max_bc_difference_m_s':bc,
                'max_nodal_sigZZ_change_Pa':float(np.max(abs(nd[:,5]-old[:,5]))),
                'max_nodal_tauZZ_change_N_m':float(np.max(abs(nd[:,6]-old[:,6]))),
                'max_IP_sigZZ_change_Pa':float(np.max(abs(ip[:,4]-oi[:,4]))),
                'max_IP_tauZZ_change_N_m':float(np.max(abs(ip[:,5]-oi[:,5]))),
                'max_fixed_load_change_N':float(np.max(abs(nd[:,7:]-old[:,7:]))),
                'native_solves':0}
        except Exception as e:
            import traceback
            probe={'status':'BLOCKED','error':repr(e),'traceback':traceback.format_exc()}
    ok=projection['screen_pass'] and probe['status']=='PASS'
    status='G6_CONSERVATIVE_NODAL_FEEDBACK_PROJECTION_PASS__CONTROLLED_RESOLVE_REQUIRED' if ok else 'G6_FEEDBACK_PROJECTION_BLOCKED'
    report={'status':status,'projection':projection,'native_probe':probe,'additional_native_solves':0,
        'physical_acceptance':False,'limitations':['Nodal lumped thin-shell mass and sensible heat; loss of intra-node parcel variability.',
          'Cubic compression measured, not exact thermal field reconstruction. Full G5 cell state retained.',
          'Frozen elevation and local BC components; no isostasy, pressure work, natural exterior or mineralogy.',
          'No mechanical re-solve, no canonical T1.'],**c.SCOPE}
    a.write(out/'G6_REPORT.json',report)
    a.write(out/'MANIFEST.json',{'status':status,'source_sha':a.SHA,'G4_manifest_sha256':G4_PIN,
        'G5_manifest_sha256':G5_PIN,'additional_native_solves':0,'files':c.inventory(out),**c.SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G6_MANIFEST_SHA256',a.sha(out/'MANIFEST.json'),flush=True)
    print(status,flush=True)
    return 0 if ok else 2

if __name__=='__main__':
    raise SystemExit(main())
