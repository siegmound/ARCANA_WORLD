#!/usr/bin/env python3
"""G28 retained spherical scalar-gradient audit; no change to native physics.
Compare coordinate derivatives with an independent Cartesian planar-triangle
construction and test the orthonormal east metric factor on retained loads.
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

PIN='ea8c8810d65ecce94b53ed6a571061ac17d32a2cad9053b8e2f8448708e674cf'
STATUS='G27_INTERFACE_TORQUE_BUDGET_PASS__MANTLE_COUPLING_AUTHORITY_REQUIRED'
AUTH='G28_SPHERICAL_METRIC_DIAGNOSTIC_ONLY_V1'
N,E,Q=g26.N,g26.E,g26.Q
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
SOURCE,SCOPE=g25.SOURCE,g25.SCOPE
def verify(p):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==PIN and m['status']==STATUS and m['source_sha']==SOURCE
         and all(m[k]==v for k,v in SCOPE.items()),'G27_PIN_SCOPE')
    need(inventory(p)==m['files'],'G27_INVENTORY')
    need(m['G23_manifest_sha256']==g25.PINS[0] and m['G26_manifest_sha256']==g27.PIN,'G27_LINEAGE')
    return m
def rel(x,y):
    return float(np.max(abs(x-y))/max(float(np.max(abs(y))),1e-300))
def gradients(x,z,W):
    # x: unit-vector vertices (E,3,3); z: scalar vertex data (E,3).
    # The native scalar shape functions are planar barycentric functions
    # evaluated at the intersection of the radial ray with the triangle.
    a=x[:,1]-x[:,0]; b=x[:,2]-x[:,0]
    normal=np.cross(a,b)
    norm2=np.einsum('ei,ei->e',normal,normal)
    need(np.all(norm2>0),'DEGENERATE_TRIANGLE')
    normal/=np.sqrt(norm2)[:,None]
    aa=np.einsum('ei,ei->e',a,a); bb=np.einsum('ei,ei->e',b,b)
    ab=np.einsum('ei,ei->e',a,b)
    da=z[:,1]-z[:,0]; db=z[:,2]-z[:,0]
    grad=((bb*da-ab*db)/norm2)[:,None]*a+((aa*db-ab*da)/norm2)[:,None]*b
    south=[]; east=[]; sin=[]
    for w in W:
        raw=np.einsum('j,eji->ei',w,x)
        p=np.linalg.norm(raw,axis=1)
        r=raw/p[:,None]
        st=np.hypot(r[:,0],r[:,1])
        need(np.all(st>0),'POLE_QUADRATURE')
        cp=r[:,0]/st; sp=r[:,1]/st
        et=np.column_stack((r[:,2]*cp,r[:,2]*sp,-st))
        ep=np.column_stack((-sp,cp,np.zeros(E)))
        nr=np.einsum('ei,ei->e',normal,r)
        gr=np.einsum('ei,ei->e',grad,r)
        need(np.all(abs(nr)>.9),'RADIAL_INTERSECTION')
        def deriv(t):
            return p*(np.einsum('ei,ei->e',grad,t)-gr*np.einsum('ei,ei->e',normal,t)/nr)
        south.append(deriv(et)); east.append(deriv(ep)); sin.append(st)
    return np.concatenate(south),np.concatenate(east),np.concatenate(sin)

def run(p,q,r,out):
    d=p/'native_diorite2'
    with np.load(d/'GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as data:
        G=data['rotation_candidates']; xyz=data['native_xyz']; rhs=data['rhs']
    need(G.shape==(2*N,3) and xyz.shape==(N,3) and rhs.shape==(2*N,),'G23_FIELDS')
    R=float(read(d/'CONDITIONAL_CONTROLS.json')['radius'])
    need(R>0,'RADIUS')
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    s=np.fromfile(q/'pressure_audit/SQUEEZ_PRESSURE.bin',dtype=g26.PD)
    need(len(f)==len(s)==Q,'IP_COUNT')
    ids=f['ids']; v=f['v']; w=s['v']
    need(np.array_equal(ids[:,0],np.tile(np.arange(1,E+1),7))
         and np.array_equal(ids[:,1],np.repeat(np.arange(1,8),E))
         and np.array_equal(ids[:,2:],s['ids'])
         and np.array_equal(v[:,4:7],w[:,:3])
         and np.array_equal(v[:,1],w[:,11]),'IP_JOIN')
    need(np.isfinite(v).all() and np.isfinite(w).all(),'NONFINITE')
    node=ids[:E,2:].astype(np.int64)-1
    need(node.min()>=0 and node.max()<N and
         np.array_equal(ids[:,2:].reshape(7,E,3),np.broadcast_to(node+1,(7,E,3))),'NODE_ORDER')
    W=w[:,:3].reshape(7,E,3)[:,0,:].copy()
    need(np.array_equal(w[:,:3].reshape(7,E,3),np.broadcast_to(W[:,None,:],(7,E,3)))
         and np.max(abs(W.sum(axis=1)-1))<1e-12 and np.linalg.matrix_rank(W)==3,'IP_WEIGHTS')
    # Depth at quadrature is zMoho+tLInt-elevation, linear in planar barycentric weights.
    z=w[:,4]-w[:,3]
    ze=np.linalg.lstsq(W,z.reshape(7,E),rcond=None)[0].T
    zfit=rel((W@ze.T).ravel(),z)
    lo=np.full(N,np.inf); hi=np.full(N,-np.inf)
    np.minimum.at(lo,node.ravel(),ze.ravel()); np.maximum.at(hi,node.ravel(),ze.ravel())
    need(np.isfinite(lo).all() and np.isfinite(hi).all(),'NODE_COVERAGE')
    shared=float(np.max(hi-lo)/max(float(np.max(abs(ze))),1.))
    need(zfit<1e-11 and shared<1e-10,'DEPTH_RECONSTRUCTION')
    gx,gy,st=gradients(xyz[node],ze,W)
    da,sig,sx,sy=v[:,:4].T
    warea=da*R
    need(np.all(warea>0) and abs(warea.sum()/(4*np.pi*R**2)-1)<1e-8,'AREA')
    xerr=rel(gx,sx); yerr=rel(gy*st,sy); ortherr=rel(gy,sy/st)
    need(max(xerr,yerr,ortherr)<1e-7,'INDEPENDENT_GRADIENT_REPLAY')
    phi=v[:,7:].reshape(Q,3,2,2).transpose(0,1,3,2)
    nodes=ids[:,2:].astype(np.int64)-1
    native=np.column_stack((sx,sy))/R
    metric=np.column_stack((sx,sy/st))/R
    independent=np.column_stack((gx,gy))/R
    def assemble(pres,grad):
        local=-warea[:,None,None]*pres[:,None,None]*np.einsum('qnab,qb->qna',phi,grad)
        load=np.zeros((N,2))
        np.add.at(load,nodes.ravel(),local.reshape(-1,2))
        return load.ravel()
    old=g27.vector_from_g25_projection(q)
    original=assemble(sig,native); replay=rel(original,old)
    need(replay<1e-12,'FB2_NATIVE_REPLAY')
    with np.load(r/'INTERFACE_DIAGNOSTIC_FIELDS.npz',allow_pickle=False) as d27:
        need(np.array_equal(d27['element_id'],ids[:,0]) and np.array_equal(d27['ip_id'],ids[:,1])
             and np.array_equal(d27['quadrature_area_m2'],warea),'G27_QUADRATURE_REPLAY')
        need(rel(d27['normal_equivalent_traction_Pa'],-sig[:,None]*native)<1e-12,'G27_TRACTION_REPLAY')
    g=w[:,5]
    need(np.max(abs(g-g[0]))<1e-12*abs(g[0]),'GRAVITY_NOT_CONSTANT')
    fields={'constant':np.full(Q,1e8),'linear_depth':3300*g*z,'native_pressure_anomaly':sig}
    results={}; saved={}
    for name,pres in fields.items():
        a=assemble(pres,native); b=assemble(pres,metric); c=assemble(pres,independent)
        results[name]={'native':g25.metric(a,G),'metric_candidate':g25.metric(b,G),
                       'independent_cartesian':g25.metric(c,G),
                       'metric_vs_cartesian_relative_inf':rel(b,c),
                       'metric_minus_native_relative_l2':float(np.linalg.norm(b-a)/np.linalg.norm(a)),
                       'native_torque_reference_radius_Nm':(R*(G.T@a)).tolist(),
                       'metric_torque_reference_radius_Nm':(R*(G.T@b)).tolist()}
        need(results[name]['metric_vs_cartesian_relative_inf']<1e-7,'CARTESIAN_LOAD_REPLAY:'+name)
        if name=='native_pressure_anomaly':
            saved={'native_FB2':a,'diagnostic_metric_FB2':b,'independent_cartesian_FB2':c}
    def worst(row,key): return max(row[key]['rotation_relative'])
    checks={k:bool(worst(results[k],'metric_candidate')<1e-6 and
                   worst(results[k],'metric_candidate')<worst(results[k],'native')/100)
            for k in ('constant','linear_depth')}
    corrected=saved['diagnostic_metric_FB2']
    total=rhs-old+corrected
    np.savez_compressed(out/'G28_DIAGNOSTIC_LOADS.npz',**saved)
    return {'quadrature_points':Q,'depth_reconstruction_relative_inf':zfit,
            'shared_vertex_depth_relative_spread':shared,'sin_colatitude_range':[float(st.min()),float(st.max())],
            'south_derivative_relative_inf':xerr,'longitude_coordinate_derivative_relative_inf':yerr,
            'east_orthonormal_derivative_relative_inf':ortherr,
            'native_FB2_replay_relative_inf':replay,'tests':results,'manufactured_metric_screen':checks,
            'candidate_total_rhs_projection':(G.T@total).tolist(),
            'candidate_total_rhs_rotation_relative':g25.metric(total,G)['rotation_relative'],
            'candidate_total_rhs_relative_change_l2':float(np.linalg.norm(total-rhs)/np.linalg.norm(rhs)),
            'metric_hypothesis_supported':all(checks.values()),
            'physical_load_correction_authorized':False,'native_code_changed':False,
            'limitations':['Retained quadrature only; native source and regional parity remain untested.',
                           'Independent Cartesian gradient uses depth reconstructed from native IP samples.',
                           'Manufactured tests are on one mesh, not a convergence study.',
                           'Remaining native pressure torque is not automatically physical.']}

def main():
    ap=argparse.ArgumentParser()
    for k in ('g23','g26','g27','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-metric-diagnostic-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==SOURCE
         and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    p,q,r,out=(x.resolve() for x in (a.g23,a.g26,a.g27,a.output))
    pm=g25.verify(p,0); qm=g27.verify(q); rm=verify(r)
    need(not out.exists() and not any(out.is_relative_to(x) for x in (p,q,r,root)),'OUTPUT')
    out.mkdir()
    report={'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],'G26_manifest_sha256':g27.PIN,
            'G27_manifest_sha256':PIN,'additional_builds':0,'additional_native_assemblies':0,
            'additional_native_solves':0,'additional_time_advance_years':0,'material_assignments':0,
            'load_modified':False,'global_solve_authorized':False,'physical_acceptance':False,**SCOPE}
    try:
        print('G28_PARENTS_VERIFIED',flush=True)
        report['audit']=run(p,q,r,out)
        report['screen_pass']=report['audit']['metric_hypothesis_supported']
        report['status']=('G28_SPHERICAL_METRIC_HYPOTHESIS_SUPPORTED__NATIVE_PARITY_REQUIRED'
                          if report['screen_pass'] else 'G28_SPHERICAL_METRIC_DIAGNOSTIC_RETAINED__HYPOTHESIS_UNRESOLVED')
    except Exception as e:
        report.update(screen_pass=False,status='G28_SPHERICAL_METRIC_AUDIT_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    need(g25.verify(p,0)==pm and g27.verify(q)==qm and verify(r)==rm,'PARENT_MUTATION')
    need(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE_MUTATION')
    write(out/'G28_REPORT.json',report)
    write(out/'MANIFEST.json',{'status':report['status'],'source_sha':SOURCE,'G23_manifest_sha256':g25.PINS[0],
         'G26_manifest_sha256':g27.PIN,'G27_manifest_sha256':PIN,'runner_sha256':sha(Path(__file__)),
         'files':inventory(out),**SCOPE})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G28_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    print(report['status'],flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
