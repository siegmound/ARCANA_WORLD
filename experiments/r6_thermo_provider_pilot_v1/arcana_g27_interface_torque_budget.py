#!/usr/bin/env python3
"""G27: retained-quadrature interface torque budget and conditional viscous drag pilot.
No native execution, no global equilibrium solve, no changes to active loads.
The 3x3 drag calculation is a manufactured rigid-mode restriction, not mantle authority.
"""
import argparse
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26

PIN='533c72073d26606ed981a1845da5119432e3ee13114fcd7076788869b3d8a602'
STATUS='G26_BASAL_PRESSURE_PROVENANCE_PASS__TORQUE_CLOSURE_AUTHORITY_REQUIRED'
AUTH='G27_INTERFACE_TORQUE_BUDGET_DIAGNOSTIC_ONLY_V1'
N,E,Q=g26.N,g26.E,g26.Q
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
SOURCE,SCOPE=g25.SOURCE,g25.SCOPE
YEAR=365.25*86400
KAPPAS=(1e13,1e14,1e15,1e16,1e17)
def verify(p):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==PIN and m['status']==STATUS and m['source_sha']==SOURCE
         and all(m[k]==v for k,v in SCOPE.items()),'G26_PIN_SCOPE')
    need(inventory(p)==m['files'],'G26_INVENTORY')
    need(m['G23_manifest_sha256']==g25.PINS[0] and m['G25_manifest_sha256']==g26.PIN,'G26_LINEAGE')
    return m

def qstats(x,w):
    n=np.linalg.norm(x,axis=1)
    order=np.argsort(n); c=np.cumsum(w[order]); k=np.searchsorted(c,.95*c[-1])
    return {'max':float(n.max()),'area_weighted_rms':float(np.sqrt(np.average(n*n,weights=w))),
            'area_weighted_p95':float(n[order[min(k,len(n)-1)]])}
def run(p,q,out):
    d=p/'native_diorite2'
    with np.load(d/'GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as f:
        G=f['rotation_candidates']; b=f['rhs']; xyz=f['native_xyz']; fixed=f['fixed_load']
    need(G.shape==(2*N,3) and b.shape==fixed.shape==(2*N,) and xyz.shape==(N,3)
         and np.array_equal(b,fixed),'G23_FIELDS')
    ctl=read(d/'CONDITIONAL_CONTROLS.json')
    radius=float(ctl['radius'])
    need(np.isfinite(radius) and radius>0 and ctl['iConve']==0 and ctl['trHMax']==0,'CONTROL')
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    s=np.fromfile(q/'pressure_audit/SQUEEZ_PRESSURE.bin',dtype=g26.PD)
    need(len(f)==len(s)==Q,'IP_COUNT')
    ids=f['ids']; v=f['v']
    need(np.array_equal(ids[:,0],np.tile(np.arange(1,E+1),7))
         and np.array_equal(ids[:,1],np.repeat(np.arange(1,8),E))
         and np.array_equal(ids[:,2:],s['ids'])
         and np.array_equal(v[:,4:7],s['v'][:,:3])
         and np.array_equal(v[:,1],s['v'][:,11]),'IP_JOIN')
    need(np.isfinite(v).all() and np.isfinite(s['v']).all(),'NONFINITE')
    nodes=ids[:,2:].astype(np.int64)-1
    need(nodes.min()>=0 and nodes.max()<N,'NODE_RANGE')
    da,sig,sx,sy=v[:,:4].T
    w=da*radius
    need(np.all(w>0),'AREA_WEIGHT')
    area=float(w.sum()); sphere_area=4*np.pi*radius**2
    area_ratio=area/sphere_area
    need(abs(area_ratio-1)<.01,'NATIVE_AREA_SCALE')
    phi=v[:,7:].reshape(Q,3,2,2).transpose(0,1,3,2)
    # Work-conjugate interpolation of the three native rigid rotations at IPs.
    H=np.einsum('qnab,qnac->qbc',phi,G.reshape(N,2,3)[nodes])
    def assemble(t):
        loc=w[:,None,None]*np.einsum('qnab,qb->qna',phi,t)
        result=np.zeros((N,2))
        np.add.at(result,nodes.ravel(),loc.reshape(-1,2))
        return result.ravel()
    def projection(t): return np.einsum('q,qba,qb->a',w,H,t)
    normal=-sig[:,None]*np.column_stack((sx,sy))/radius
    normal_load=assemble(normal)
    old=vector_from_g25_projection(q)
    scale=max(float(np.max(abs(old))),1.)
    replay=float(np.max(abs(normal_load-old))/scale)
    tnormal=projection(normal)
    target=G.T@b
    need(replay<=1e-12,'FB2_REPLAY')
    need(np.linalg.norm(tnormal-G.T@normal_load)<=1e-12*np.linalg.norm(target),'VIRTUAL_WORK')
    # Constant pressure and depth-only pressure have zero continuum torque
    # on a closed sphere; measure their residual in the same discretization.
    z=s['v'][:,4]-s['v'][:,3]
    grad=np.column_stack((sx,sy))/radius
    manufactured={}
    for label,pres in [('constant',np.full(Q,1e8)),
                       ('linear_depth',3300.*s['v'][:,5]*z)]:
        t=-pres[:,None]*grad
        load=assemble(t)
        manufactured[label]=g25.metric(load,G)
    # Unit-uniform drag law tau=-kappa H u. u is rigid-mode relative
    # speed at reference radius, not a complete mantle or plate velocity.
    K=np.einsum('q,qba,qbc->ac',w,H,H)
    K=(K+K.T)*.5
    ev=np.linalg.eigvalsh(K)
    need(ev[0]>0 and ev[-1]/ev[0]<1e3,'DRAG_GRAM')
    c=np.linalg.solve(K,target)
    shear=-np.einsum('qba,a->qb',H,c)
    shear_load=assemble(shear)
    tshear=projection(shear)
    residual=G.T@(b+shear_load)
    rel=float(np.linalg.norm(residual)/np.linalg.norm(target))
    workerr=float(np.linalg.norm(tshear-G.T@shear_load)/np.linalg.norm(target))
    reaction=-(normal+shear)
    mantle=projection(reaction)
    scenarios=[]
    for kap in KAPPAS:
        u=c/kap
        ip=np.einsum('qba,a->qb',H,u)
        diss=float(np.einsum('q,qb,qb->',w,ip,ip)*kap)
        conjugate=float(-u@tshear)
        scenarios.append({'kappa_Pa_s_per_m':kap,'equivalent_viscosity_for_100km_Pa_s':kap*1e5,
                          'relative_rigid_speed_coeff_m_s':u.tolist(),
                          'relative_angular_speed_rad_s':(u/radius).tolist(),
                          'relative_speed_cm_yr':qstats(ip*YEAR*100,w),
                          'dissipation_W':diss,'conjugate_work_W':conjugate,
                          'work_relative_error':abs(diss-conjugate)/max(diss,1e-300)})
    need(rel<1e-12 and workerr<1e-12 and all(x['work_relative_error']<1e-12 and x['dissipation_W']>0 for x in scenarios),
         'CONDITIONAL_DRAG_ALGEBRA')
    # A diagnostic result only. Do not export a replacement production RHS.
    np.savez_compressed(out/'INTERFACE_DIAGNOSTIC_FIELDS.npz',element_id=ids[:,0],
        ip_id=ids[:,1],normal_equivalent_traction_Pa=normal,conditional_shear_Pa=shear,
        quadrature_area_m2=w,conditional_shear_nodal_load=shear_load)
    return {'quadrature_points':Q,'radius_m':radius,'quadrature_area_m2':area,'sphere_area_ratio':area_ratio,
        'native_FB2_replay_relative_inf':replay,'native_rotation_projection':target.tolist(),
        'FB2_projection':tnormal.tolist(),'FB2_torque_reference_radius_Nm':(radius*tnormal).tolist(),
        'manufactured_pressure_tests':manufactured,
        'drag_gram_eigenvalues_m2':ev.tolist(),'drag_gram_condition':float(ev[-1]/ev[0]),
        'conditional_shear_traction_Pa':qstats(shear,w),'native_normal_equivalent_traction_Pa':qstats(normal,w),
        'conditional_shear_load':g25.metric(shear_load,G),
        'conditional_residual_projection':residual.tolist(),'conditional_residual_relative_l2':rel,
        'quadrature_virtual_work_relative_error':workerr,
        'interface_action_reaction_projection_residual':(tnormal+tshear+mantle).tolist(),
        'mantle_reaction_projection_normal_plus_shear':mantle.tolist(),
        'conditional_drag_scenarios':scenarios,'three_by_three_diagnostic_systems':1,
        'physical_mantle_provider_available_or_qualified':False,
        'physical_traction_authorized':False,'physical_gauge_authorized':False,
        'uniform_drag_and_reference_radius_are_assumptions':True,
        'excluded_D12_nodes_still_present':True,
        'limitations':['Rigid-mode restriction only; actual deformation changes basal drag.',
                       'Opposite traction is bookkeeping action-reaction on same thin-shell interface, not mantle PDE.',
                       'No selected viscosity, shear depth, mantle flow, or physical torque authority.',
                       'Manufactured pressure tests are diagnostics, not additional physical scenarios.']}

def vector_from_g25_projection(q):
    # G26 retains original native force files with exact G25 replay.
    return g25.vector(q/'pressure_audit'/('FB2_NORMAL_TRACTION_ANOMALY.dat'))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--g23',type=Path,required=True); ap.add_argument('--g26',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-interface-diagnostic-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,out=(x.resolve() for x in (a.g23,a.g26,a.output))
    pm=g25.verify(p,0); qm=verify(q)
    need(not out.exists() and not any(out.is_relative_to(x) for x in (p,q,root)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':PIN,
            'additional_builds':0,'additional_native_assemblies':0,'additional_native_solves':0,
            'additional_time_advance_years':0,'material_assignments':0,'load_modified':False,
            'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        print('G27_PARENT_VERIFIED',flush=True)
        report['audit']=run(p,q,out)
        report.update(screen_pass=True,status='G27_INTERFACE_TORQUE_BUDGET_PASS__MANTLE_COUPLING_AUTHORITY_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G27_INTERFACE_TORQUE_BUDGET_BLOCKED',
                      error=repr(e),traceback=traceback.format_exc())
    need(g25.verify(p,0)==pm and verify(q)==qm,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G27_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
        'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':PIN,
        'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G27_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
