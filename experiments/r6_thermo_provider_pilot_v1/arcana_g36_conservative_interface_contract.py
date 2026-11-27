#!/usr/bin/env python3
"""G36: corrected pressure provenance and conservative interface algebra.
Manufactured velocities on a shared reference surface, no mantle PDE or physical closure.
"""
import argparse
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27
import arcana_g32_corrected_global_operator as g32
import arcana_g33_native_basal_coupling_audit as g33
import arcana_g34_basal_depth_support as g34
import arcana_g35_native_depth_parity as g35

PIN='a0307ab6033fd56f1473ec43ea1af4c4f23049b88b4efa1edc4c393ade195d56'
STATUS='G35_NATIVE_DEPTH_PARITY_PASS__MANTLE_PHYSICAL_AUTHORITY_REQUIRED'
AUTH='G36_CONSERVATIVE_INTERFACE_DIAGNOSTIC_ONLY_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
SOURCE,SCOPE=g25.SOURCE,g25.SCOPE
N,E,Q=g26.N,g26.E,g26.Q
DEPTHS=(250000,300000)
def verify(p):
    m=g32.verify(p,PIN,STATUS)
    need(m['G34_manifest_sha256']==g35.PIN and m['G33_manifest_sha256']==g34.PIN
         and m['G23_manifest_sha256']==g25.PINS[0] and m['G26_manifest_sha256']==g27.PIN,'G35_LINEAGE')
    need(read(p/'G35_REPORT.json')['screen_pass'],'G35_SCREEN')
    return m
def relative(a,b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))
def audit(q,r,t,out):
    with np.load(r/'native_diorite2/GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d:
        G=d['rotation_candidates']; xyz=d['native_xyz']; b=d['rhs']
        need(np.array_equal(b,d['fixed_load']),'RHS_FIXED')
    need(G.shape==(2*N,3) and xyz.shape==(N,3) and b.shape==(2*N,),'FIELDS')
    R=float(read(r/'native_diorite2/CONDITIONAL_CONTROLS.json')['radius'])
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    s=np.fromfile(q/'pressure_audit/SQUEEZ_PRESSURE.bin',dtype=g26.PD)
    need(len(f)==len(s)==Q and np.isfinite(f['v']).all() and np.isfinite(s['v']).all(),'QUADRATURE')
    ids=f['ids']; v=f['v']; p=s['v']
    need(np.array_equal(ids[:,0],np.tile(np.arange(1,E+1),7))
         and np.array_equal(ids[:,1],np.repeat(np.arange(1,8),E))
         and np.array_equal(ids[:,2:],s['ids']) and np.array_equal(v[:,4:7],p[:,:3])
         and np.array_equal(v[:,1],p[:,11]),'IP_JOIN')
    nodes=ids[:,2:].astype(np.int64)-1
    need(nodes.min()>=0 and nodes.max()<N,'NODES')
    pos=np.einsum('qj,qji->qi',p[:,:3],xyz[nodes])
    st=np.hypot(pos[:,0],pos[:,1])/np.linalg.norm(pos,axis=1)
    area=v[:,0]*R
    need(np.all(st>0) and np.all(area>0) and abs(area.sum()/(4*np.pi*R**2)-1)<1e-8,'GEOMETRY')
    phi=v[:,7:].reshape(Q,3,2,2).transpose(0,1,3,2)
    def interp(u): return np.einsum('qnab,qna->qb',phi,u.reshape(N,2)[nodes])
    def scatter(t):
        local=area[:,None,None]*np.einsum('qnab,qb->qna',phi,t)
        a=np.zeros((N,2)); np.add.at(a,nodes.ravel(),local.reshape(-1,2))
        return a.ravel()
    H=np.stack([interp(G[:,k]) for k in range(3)],axis=2)
    def projection(t): return np.einsum('q,qba,qb->a',area,H,t)
    grad=np.column_stack((v[:,2],v[:,3]/st))/R
    sig=v[:,1]; pr=p[:,10]; column=pr-sig
    ref=scatter(-pr[:,None]*grad); col=scatter(column[:,None]*grad)
    anomaly=scatter(-sig[:,None]*grad)
    pressure_split=relative(ref+col,anomaly)
    torque_match=relative(G.T@anomaly,G.T@b)
    need(pressure_split<1e-12 and torque_match<1e-10,'PRESSURE_SPLIT')
    pressure={'corrected_anomaly_projection':(G.T@anomaly).tolist(),
              'reference_component_projection':(G.T@ref).tolist(),
              'derived_negative_column_component_projection':(G.T@col).tolist(),
              'reference_radius_torque_Nm':(R*(G.T@anomaly)).tolist(),
              'split_relative_l2':pressure_split,'anomaly_vs_full_rhs_rotation_relative_l2':torque_match,
              'derived_column_independent':False,'physical_normal_reaction_established':False}
    print('G36_CORRECTED_PRESSURE_PROVENANCE_VERIFIED',flush=True)
    # Independent manufactured nodal fields; not chosen to close G32 torque.
    scale=.05/g33.YEAR
    x=xyz[:,0]; y=xyz[:,1]; z=xyz[:,2]
    ul=scale*(G@np.array([.2,-.4,.8])+np.column_stack((.3*x*z,.2*y*z)).ravel())
    um=scale*(G@np.array([-.6,.5,.1])+np.column_stack((-.2*x*y,.3*x*z)).ravel())
    common=scale*(G@np.array([.3,.2,-.4]))
    perturb=scale*(G@np.array([.7,-.2,.4])+np.column_stack((.1*y,.2*z)).ravel())
    dl=interp(ul); dm=interp(um); d=dm-dl; h=interp(perturb)
    mag=np.linalg.norm(d,axis=1)
    # Nonzero sampled speed needed for smooth uncapped tangent tests.
    need(np.all(mag>0),'ZERO_MANUFACTURED_SPEED')
    shift=interp(um+common)-interp(ul+common)
    need(relative(shift,d)<1e-12,'COMMON_ROTATION_KINEMATICS')
    rows=[]
    for model in g33.MODELS:
        ctl=read(t/'G34_REPORT.json')['audit']['cases'][model]; e=float(ctl['native_exponent'])
        need(0<e<=1,'EXPONENT')
        with np.load(t/(model+'_DEPTH_DIAGNOSTICS.npz'),allow_pickle=False) as data:
            need(np.array_equal(data['element_id'],ids[:,0]) and np.array_equal(data['ip_id'],ids[:,1])
                 and np.array_equal(data['depths_m'],g34.DEPTHS),'G34_JOIN')
            fields=data['glue_1km_step']
        for depth in DEPTHS:
            glue=fields[g34.DEPTHS.index(depth)]
            need(glue.shape==(Q,) and np.all(np.isfinite(glue)) and np.all(glue>0),'GLUE')
            def tau(delta):
                m=np.linalg.norm(delta,axis=1)
                return glue[:,None]*np.power(m,e-1)[:,None]*delta
            traction=tau(d)
            fl=scatter(traction); fm=scatter(-traction)
            diss=float(np.einsum('q,qb,qb->',area,traction,d))
            power=float(ul@fl+um@fm)
            p_err=abs(power+diss)/diss
            adj=relative(projection(traction),G.T@fl)
            action=relative(fl+fm,fl)
            common_err=relative(scatter(tau(shift)),fl)
            # Tangent of tau with respect to slip, tested against centered FD.
            jh=glue[:,None]*mag[:,None]**(e-1)*(h+(e-1)*d*(np.sum(d*h,axis=1)/mag**2)[:,None])
            analytic=scatter(jh)
            errs={}
            for eps in (1e-4,1e-5,1e-6):
                fd=scatter((tau(d+eps*h)-tau(d-eps*h))/(2*eps))
                errs[str(eps)]=relative(fd,analytic)
            work=float(perturb@analytic)
            qwork=float(np.einsum('q,qb,qb->',area,h,jh))
            tangent_work=abs(work-qwork)/max(abs(qwork),1e-300)
            # Second perturbation demonstrates symmetry on the shared trace.
            k=interp(common); jk=glue[:,None]*mag[:,None]**(e-1)*(k+(e-1)*d*(np.sum(d*k,axis=1)/mag**2)[:,None])
            ab=float(common@analytic); ba=float(perturb@scatter(jk))
            symmetry=abs(ab-ba)/max(abs(ab),abs(ba),abs(qwork),1e-300)
            need(diss>0 and qwork>0 and max(p_err,adj,action,common_err,tangent_work,symmetry)<1e-11
                 and min(errs.values())<1e-6,'INTERFACE_ALGEBRA:'+model+str(depth))
            rows.append({'model':model,'depth_m':depth,'exponent':e,'dissipation_W':diss,
                'interface_power_W':power,'power_balance_relative':p_err,'action_reaction_relative':action,
                'rotation_projection_relative':adj,'common_rotation_traction_relative':common_err,
                'tangent_centered_fd_relative':errs,'tangent_work_relative':tangent_work,
                'tangent_symmetry_relative':symmetry,'tangent_positive_on_test_direction':True,
                'combined_tangential_torque_Nm':(R*(G.T@(fl+fm))).tolist(),
                'normal_reaction_only_if_independently_authorized':True})
    # No production traction files: manufactured forces are deliberately not exported.
    contract={'status':'CANDIDATE_INTERFACE_CONTRACT_NOT_PHYSICAL_AUTHORITY',
        'trace':'shared reference-radius 2-D quadrature; not actual mantle mesh or variable-radius interface',
        'normal_load':'reference-minus-derived-column anomaly; reconcile hydrostatic reference and true normal traction before admitting reaction',
        'shear':'equal/opposite work-conjugate transfer; uncapped creep only for smooth tangent tests',
        'double_counting_guard':'OneBar integrates from surface to zBAsth; do not overlap resolved lithosphere or mantle shear dissipation with this unresolved column law',
        'gauge':'one common rotation constraint only after total load compatibility; do not remove relative rotation or project away physical torque',
        'required_provider_inputs':['mantle shell radial geometry and boundaries','3D temperature/composition or explicitly bounded reduced-state hypothesis',
          'density/buoyancy and viscosity laws with domain support','initial condition and evolution law',
          'normal traction/reference pressure convention','conservative trace transfer, frame and units','external torque authority if nonzero'],
        'available_evidence':['G32 corrected shell load and operator','G26 retained reference pressure and derived column',
          'G34 conditional column thermal extension and glue','G35 sampled native constitutive parity'],
        'missing_inputs_are_not_defaulted':True,'mantle_provider_selected':False,'global_solve_authorized':False}
    write(out/'CANDIDATE_INTERFACE_CONTRACT.json',contract)
    return {'quadrature_points':Q,'pressure':pressure,'manufactured_interface_tests':rows,
        'mantle_physical_authority':False,'physical_normal_reaction_established':False,
        'total_system_torque_closed':False,'traction_applied':False}
def main():
    ap=argparse.ArgumentParser()
    for k in ('g26','g32','g34','g35','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-conservative-interface-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    q,r,t,s,out=(x.resolve() for x in (a.g26,a.g32,a.g34,a.g35,a.output))
    parents=((q,g27.verify),(r,lambda x:g32.verify(x,g33.PIN,g33.STATUS)),(t,g35.verify),(s,verify))
    before=[fn(x) for x,fn in parents]
    need(not out.exists() and not any(out.is_relative_to(x) for x in (root,q,r,t,s)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,
        'G34_manifest_sha256':g35.PIN,'G35_manifest_sha256':PIN,'additional_builds':0,
        'additional_native_assemblies':0,'additional_global_solves':0,'additional_time_advance_years':0,
        'material_assignments':0,'active_source_modified':False,'global_solve_authorized':False,
        'physical_acceptance':False,**SCOPE}
    try:
        # Filename inventory is a discovery aid, not proof of provider absence or presence.
        tracked=subprocess.check_output(['git','ls-files'],text=True).splitlines()
        import re
        write(out/'MANTLE_PROVIDER_DISCOVERY.json',{'frozen_source':SOURCE,
            'candidate_paths':[p for p in tracked if re.search(r'mantle|astheno|convec|citcom|aspect|geodyn|stokes',p,re.I)],
            'filename_search_only':True,'provider_qualified':False})
        report['audit']=audit(q,r,t,out)
        report.update(screen_pass=True,status='G36_CONSERVATIVE_INTERFACE_ALGEBRA_PASS__MANTLE_STATE_AND_NORMAL_REACTION_AUTHORITY_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G36_CONSERVATIVE_INTERFACE_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    need([fn(x) for x,fn in parents]==before,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G36_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,
        'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,'G34_manifest_sha256':g35.PIN,
        'G35_manifest_sha256':PIN,'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G36_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
