#!/usr/bin/env python3
"""G36-R2: repair the action-reaction metric, replay unchanged R1 algebra.
Manufactured velocities on a shared reference surface, no mantle PDE or physical closure.
"""
import argparse
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
from arcana_interface_metrics import force_diagnostic, balance_screen, metric_selftest
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27
import arcana_g32_corrected_global_operator as g32
import arcana_g33_native_basal_coupling_audit as g33
import arcana_g34_basal_depth_support as g34
import arcana_g35_native_depth_parity as g35

PIN='a0307ab6033fd56f1473ec43ea1af4c4f23049b88b4efa1edc4c393ade195d56'
STATUS='G35_NATIVE_DEPTH_PARITY_PASS__MANTLE_PHYSICAL_AUTHORITY_REQUIRED'
AUTH='G36R2_CONSERVATIVE_INTERFACE_DIAGNOSTIC_ONLY_V1'
R1_PIN='e984cd81bd151b0e6d5c005a54f169ee71442f2aaddcf198d5fa9d0579a7e3ae'
FAILED_PIN='beeee8ec24cb20b0211c4c1bd295653482a516fe628251858a780a30d83ac11f'
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
def compare_replay(old,new):
    """Compare every preserved R1 field except the repaired metric and gate booleans.

    Roundoff allowance: rtol=1e-12, dimensionless atol=1e-13; dimensional atol=0.
    These are replay comparisons, never replacements for scientific acceptance tolerances.
    """
    checks=[]
    skip={'action_reaction_relative','original_screen_pass','balance_screen_pass','screen_pass'}
    def visit(a,b,path):
        key=path.rsplit('/',1)[-1]
        if key in skip: return
        if isinstance(a,dict):
            for k,v in a.items():
                need(k in b,'REPLAY_MISSING:'+path+'/'+k)
                visit(v,b[k],path+'/'+k)
        elif isinstance(a,(int,float,list)) and not isinstance(a,bool):
            aa,bb=np.asarray(a),np.asarray(b)
            dimensional=any(x in path for x in ('_W','_Nm','projection','torque','slip_m_s'))
            atol=0. if dimensional else 1e-13
            ok=bool(aa.shape==bb.shape and np.isfinite(aa).all() and np.isfinite(bb).all()
                    and np.allclose(aa,bb,rtol=1e-12,atol=atol))
            checks.append({'field':path,'pass':ok,'max_abs_difference':float(np.max(abs(aa-bb))),
                           'rtol':1e-12,'atol':atol})
        else:
            checks.append({'field':path,'pass':a==b})
    visit(old,new,'')
    return {'screen_pass':bool(checks and all(x['pass'] for x in checks)),'checks':checks}

def audit(q,r,t,r1,out):
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
    write(out/'PRESSURE_DIAGNOSTIC.json',pressure)
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
    local_ratio=np.linalg.norm(h,axis=1)/mag
    weight=np.minimum(1.,1./np.maximum(local_ratio,1e-300))
    write(out/'SLIP_CONDITIONING.json',{'min_slip_m_s':float(mag.min()),'max_slip_m_s':float(mag.max()),'max_perturbation_to_slip_ratio':float(local_ratio.max()),'ratio_percentiles':np.percentile(local_ratio,[50,95,99,99.9,100]).tolist()})
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
            forces=force_diagnostic(fl,fm)
            action=forces['action_reaction_relative']
            legacy=relative(fl+fm,fl)  # retained R0/R1 expression, never an acceptance metric
            need(abs(legacy-forces['legacy_action_reaction_relative'])<1e-13,'LEGACY_REPLAY')
            np.savez_compressed(out/(model+'_'+str(depth)+'_FORCES.npz'),
                                fl=fl,fm=fm,residual=fl+fm)
            common_err=relative(scatter(tau(shift)),fl)
            # Tangent of tau with respect to slip, tested against centered FD.
            jh=glue[:,None]*mag[:,None]**(e-1)*(h+(e-1)*d*(np.sum(d*h,axis=1)/mag**2)[:,None])
            analytic=scatter(jh)
            errs={}
            for eps in (1e-4,1e-5,1e-6):
                fd=scatter((tau(d+eps*h)-tau(d-eps*h))/(2*eps))
                errs[str(eps)]=relative(fd,analytic)
            # Pointwise steps bound the relative displacement away from the singular
            # slip=0 limit. Differentiate BEFORE scatter; the derivative direction
            # is unchanged after division by the individual step.
            adaptive={}
            for eps in (1e-3,1e-4,1e-5):
                step=eps*weight
                point=(tau(d+step[:,None]*h)-tau(d-step[:,None]*h))/(2*step[:,None])
                adaptive[str(eps)]={'assembled':relative(scatter(point),analytic),'pointwise_l2':relative(point,jh)}
            # Complex-step uses the analytic extension of sqrt(delta dot delta),
            # NOT the Hermitian norm. All real base slip magnitudes are nonzero.
            step=1e-12*weight
            dc=d.astype(np.complex128)+1j*step[:,None]*h
            tc=glue[:,None]*(np.sum(dc*dc,axis=1)**((e-1)/2))[:,None]*dc
            cs=tc.imag/step[:,None]
            complex_errors={'assembled':relative(scatter(cs),analytic),'pointwise_l2':relative(cs,jh)}
            work=float(perturb@analytic)
            qwork=float(np.einsum('q,qb,qb->',area,h,jh))
            tangent_work=abs(work-qwork)/max(abs(qwork),1e-300)
            # Second perturbation demonstrates symmetry on the shared trace.
            k=interp(common); jk=glue[:,None]*mag[:,None]**(e-1)*(k+(e-1)*d*(np.sum(d*k,axis=1)/mag**2)[:,None])
            ab=float(common@analytic); ba=float(perturb@scatter(jk))
            symmetry=abs(ab-ba)/max(abs(ab),abs(ba),abs(qwork),1e-300)
            # Keep the original check and individual values as evidence.
            # Near-zero slip can invalidate a uniform FD step; independent
            # locally scaled FD and complex-step must BOTH meet the thresholds.
            balance_pass=balance_screen(diss,qwork,p_err,adj,action,common_err,tangent_work,symmetry,forces['nonzero_coupling'])
            original_pass=bool(balance_pass and min(errs.values())<1e-6)
            adaptive_pass=bool(min(max(v.values()) for v in adaptive.values())<1e-6)
            complex_pass=bool(max(complex_errors.values())<1e-10)
            rows.append({'model':model,'depth_m':depth,'exponent':e,'dissipation_W':diss,
                'force_diagnostic':forces,'legacy_action_reaction_relative':legacy,
                'interface_power_W':power,'power_balance_relative':p_err,'action_reaction_relative':action,
                'rotation_projection_relative':adj,'common_rotation_traction_relative':common_err,
                'tangent_centered_fd_relative':errs,'tangent_work_relative':tangent_work,
                'tangent_symmetry_relative':symmetry,'tangent_positive_on_test_direction':bool(qwork>0),
                'original_screen_pass':original_pass,'balance_screen_pass':balance_pass,
                'adaptive_fd_errors':adaptive,'complex_step_errors':complex_errors,
                'adaptive_screen_pass':adaptive_pass,'complex_screen_pass':complex_pass,
                'screen_pass':bool(balance_pass and adaptive_pass and complex_pass),
                'combined_tangential_torque_Nm':(R*(G.T@(fl+fm))).tolist(),
                'normal_reaction_only_if_independently_authorized':True})
            # Use the identical production predicate with a deliberately wrong reaction.
            wrong=force_diagnostic(fl,fl)
            rows[-1]['wrong_reaction_gate_rejected']=not balance_screen(
                diss,qwork,p_err,adj,wrong['action_reaction_relative'],common_err,tangent_work,symmetry)
            rows[-1]['legacy_gate_rejected']=not balance_screen(
                diss,qwork,p_err,adj,legacy,common_err,tangent_work,symmetry)
            rows[-1]['r1_replay']=compare_replay(
                read(r1/(model+'_'+str(depth)+'_DIAGNOSTIC.json')),rows[-1])
            rows[-1]['screen_pass']=bool(rows[-1]['screen_pass'] and rows[-1]['wrong_reaction_gate_rejected']
                and rows[-1]['legacy_gate_rejected'] and rows[-1]['r1_replay']['screen_pass'])
            print('G36R2_CASE',json.dumps(rows[-1],allow_nan=False),flush=True)
            write(out/(model+'_'+str(depth)+'_DIAGNOSTIC.json'),rows[-1])
    pressure_replay=compare_replay(read(r1/'PRESSURE_DIAGNOSTIC.json'),pressure)
    slip_replay=compare_replay(read(r1/'SLIP_CONDITIONING.json'),read(out/'SLIP_CONDITIONING.json'))
    write(out/'R1_REPLAY.json',{'pressure':pressure_replay,'slip':slip_replay,
        'cases':[row['r1_replay'] for row in rows]})
    need(len(rows)==4 and all(row['screen_pass'] for row in rows)
         and pressure_replay['screen_pass'] and slip_replay['screen_pass'],'G36R2_INTERFACE_CHECKS_FAILED')
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
    for k in ('g26','g32','g34','g35','failed','r1','output'):
        ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-conservative-interface-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def source_check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
             and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    source_check()
    q,r,t,s,failed,r1,out=(x.resolve() for x in (a.g26,a.g32,a.g34,a.g35,a.failed,a.r1,a.output))
    parents=((q,g27.verify),(r,lambda x:g32.verify(x,g33.PIN,g33.STATUS)),
             (t,g35.verify),(s,verify),
             (failed,lambda x:g32.verify(x,FAILED_PIN,'G36_CONSERVATIVE_INTERFACE_BLOCKED')),
             (r1,lambda x:g32.verify(x,R1_PIN,'G36R1_CONSERVATIVE_INTERFACE_BLOCKED')))
    before=[fn(x) for x,fn in parents]
    for p in (failed,r1):
        old=read(p/'G36_REPORT.json')
        need(old['screen_pass'] is False and all(old[k]==v for k,v in {
            'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,
            'G34_manifest_sha256':g35.PIN,'G35_manifest_sha256':PIN}.items()),'FAILURE_LINEAGE')
    need(read(r1/'MANIFEST.json')['failed_G36_manifest_sha256']==FAILED_PIN,'R1_LINEAGE')
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out)
         for x in (root,q,r,t,s,failed,r1)),'OUTPUT')
    out.mkdir()
    runner_dir=Path(__file__).resolve().parent
    code_files=sorted(runner_dir.glob('arcana_*.py'))
    code_before={p.name:sha(p) for p in code_files}
    report={'source_sha':SOURCE,'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,
        'G34_manifest_sha256':g35.PIN,'G35_manifest_sha256':PIN,'failed_G36_manifest_sha256':FAILED_PIN,
        'failed_G36R1_manifest_sha256':R1_PIN,'additional_builds':0,'additional_native_assemblies':0,
        'additional_global_solves':0,'additional_time_advance_years':0,'material_assignments':0,
        'active_source_modified':False,'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        write(out/'METRIC_SELFTEST.json',metric_selftest())
        report['audit']=audit(q,r,t,r1,out)
        report.update(screen_pass=True,status='G36R2_CONSERVATIVE_INTERFACE_ALGEBRA_PASS__MANTLE_STATE_AND_NORMAL_REACTION_AUTHORITY_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G36R2_CONSERVATIVE_INTERFACE_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        need([fn(x) for x,fn in parents]==before,'PARENT_MUTATION')
        source_check()
        need({p.name:sha(p) for p in sorted(runner_dir.glob('arcana_*.py'))}==code_before,'RUNNER_MUTATION')
        report['source_and_parents_unchanged']=True
    except Exception as e:
        report.update(screen_pass=False,status='G36R2_CONSERVATIVE_INTERFACE_BLOCKED',postcheck_error=repr(e))
    write(out/'RUNNER_IDENTITY.json',{'files':code_before,'r0_git_blob':'68317917241f09db0ff6fb17f05ed5848555c3dc',
        'r1_git_blob':'3ce7b6b2e4e68389cf982380c10e4bc07ae3b7f1'})
    write(out/'G36R2_REPORT.json',report)
    write(out/'MANIFEST.json',{**{k:v for k,v in report.items() if k!='audit'},
        'runner_sha256':sha(Path(__file__)),'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G36R2_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
