#!/usr/bin/env python3
"""G37-B: variable-radius basal graph and conservative common-quadrature transfer.
The retained candidate LAB geometry is real input; both volume supports and
velocities are manufactured diagnostics, NOT an admitted mantle or SHELLS trace.
No physical reaction, RHS correction, global solve, or evolution is authorized.
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
import arcana_g28_spherical_metric_audit as g28
import arcana_g32_corrected_global_operator as g32
import arcana_g33_native_basal_coupling_audit as g33

P36='4de04df65012846fb1b6319be08085d16b8e344f4c489f5cbfb461ae46280576'
S36='G36R2_CONSERVATIVE_INTERFACE_ALGEBRA_PASS__MANTLE_STATE_AND_NORMAL_REACTION_AUTHORITY_REQUIRED'
P37='5b324066945358dea2eeccc404d67b583b8ce5743aabee8f7fab6da00a350794'
S37='G37_COLUMN_RECONSTRUCTION_PASS__NORMAL_REACTION_AUTHORITY_REQUIRED'
AUTH='G37B_NORMAL_TRANSFER_DIAGNOSTIC_ONLY_V1'
N,E,Q=g26.N,g26.E,g26.Q
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
TOL=1e-11

def norm(a): return float(np.linalg.norm(a))
def rel(a,b): return norm(a-b)/max(norm(b),1e-300)
def dot(a,b): return np.einsum('qi,qi->q',a,b)
def sumabs(a): return float(np.sum(np.abs(a)))
def errwork(a,b,scale): return abs(a-b)/max(scale,1e-300)

def frame(raw):
    length=np.linalg.norm(raw,axis=1)
    need(np.all(length>0),'RADIAL_DIRECTION')
    er=raw/length[:,None]
    st=np.hypot(er[:,0],er[:,1])
    need(np.all(st>0),'POLE_IP')
    cp,sp=er[:,0]/st,er[:,1]/st
    et=np.column_stack((er[:,2]*cp,er[:,2]*sp,-st))
    ep=np.column_stack((-sp,cp,np.zeros_like(st)))
    need(np.max(abs(np.cross(et,ep)-er))<1e-12,'FRAME_ORIENTATION')
    return length,er,et,ep

def surface(R,z,gx,gy,raw,area):
    length,er,et,ep=frame(raw)
    r=R-z
    need(np.all(r>0) and np.all(area>0),'RADIUS_AREA')
    x=r[:,None]*er
    grad=gx[:,None]*et+gy[:,None]*ep
    # Oriented area per reference area for x=(R-z) er.
    av=(r/R)[:,None]**2*(er+grad/r[:,None])
    cross=np.cross(r[:,None]*et-gx[:,None]*er,r[:,None]*ep-gy[:,None]*er)/R**2
    need(rel(av,cross)<TOL and np.all(dot(av,er)>0),'NORMAL_GEOMETRY')
    jac=np.linalg.norm(av,axis=1)
    normal=av/jac[:,None]
    return x,normal,area*jac,av,er,length

def trace_weights(w,raw_scale,lo,hi,split=None):
    need(w.ndim==2 and w.shape[1]==3 and np.isfinite(w).all()
        and np.min(w)>=-1e-14 and np.max(abs(w.sum(axis=1)-1))<1e-12,'WEIGHT_COVERAGE')
    need(hi>lo>0 and np.isfinite(raw_scale).all(),'RADIAL_SUPPORT')
    t=(raw_scale-lo)/(hi-lo)
    need(np.min(t)>=-1e-14 and np.max(t)<=1+1e-14,'RADIAL_COVERAGE')
    if split is not None:
        split=np.asarray(split)
        need(split.shape==(3,) and np.all(split>0) and abs(split.sum()-1)<1e-14,'SPLIT')
        c=np.min(w/split,axis=1)
        w=np.column_stack((w-c[:,None]*split,c))
    W=np.concatenate((w*(1-t[:,None]),w*t[:,None]),axis=1)
    need(np.min(W)>=-1e-13 and np.max(abs(W.sum(axis=1)-1))<1e-12,'PARTITION')
    return W

def interpolate(values,ids,W):
    return np.einsum('qj,qjk->qk',W,values[ids])
def scatter(load,ids,W,count):
    out=np.zeros((count,3))
    for j in range(W.shape[1]): np.add.at(out,ids[:,j],W[:,j,None]*load)
    return out

def support(xyz,node,ids,w,r,length,x):
    # Two independent piecewise-linear volume traces through a shared radial
    # bracket. M adds an off-centre element vertex: not a real ASPECT mesh.
    # Chord positions at each radial level (including the off-centre vertex)
    # guarantee exact affine reproduction of the curved quadrature positions.
    raw_scale=r/length
    lo=float(raw_scale.min()-1000.); hi=float(raw_scale.max()+1000.)
    split=np.array([.2,.3,.5])
    mid=np.einsum('j,ejk->ek',split,xyz[node])
    lm=xyz
    mm=np.vstack((xyz,mid))
    li=ids[:,2:]-1
    mi=np.column_stack((li,N+ids[:,0]-1))
    result=[]
    for label,points,idx,sub in (('L',lm,li,None),('M',mm,mi,split)):
        coords=np.vstack((lo*points,hi*points))
        ix=np.concatenate((idx,idx+len(points)),axis=1)
        W=trace_weights(w,raw_scale,lo,hi,sub)
        pos=interpolate(coords,ix,W)
        need(np.max(np.linalg.norm(pos-x,axis=1))/lo<TOL,'AFFINE_POSITION:'+label)
        result.append((coords,ix,W))
    return result,{'radial_bracket_m':[lo,hi],'L_nodes':len(result[0][0]),'M_nodes':len(result[1][0]),
        'M_interior_split':split.tolist(),'actual_provider_meshes':False}

def transfer(load,x,supports,R):
    scale=float(np.linalg.norm(load,axis=1).sum())
    need(scale>0,'ZERO_TEST_LOAD')
    F=load.sum(axis=0); T=np.cross(x,load).sum(axis=0)
    forces=[]; results={}
    omega=np.array([.2,-.4,.7])/R*1e-9
    translation=np.array([.3,-.6,.5])*1e-9
    for label,(coords,ix,W),sign in zip(('L','M'),supports,(1.,-1.)):
        local=sign*load
        f=scatter(local,ix,W,len(coords)); forces.append(f)
        rigid=translation+np.cross(omega,coords)
        rigid_q=translation+np.cross(omega,x)
        rigid_err=rel(interpolate(rigid,ix,W),rigid_q)
        u=rigid+1e-9*np.column_stack((coords[:,0]*coords[:,2]/R**2,coords[:,1]**2/R**2,coords[:,2]/R))
        uq=interpolate(u,ix,W)
        work=float(np.sum(u*f)); qw=float(np.sum(uq*local))
        ferr=norm(f.sum(axis=0)-sign*F)/scale
        terr=norm(np.cross(coords,f).sum(axis=0)-sign*T)/(R*scale)
        workerr=errwork(work,qw,sumabs(uq*local))
        need(max(ferr,terr,workerr,rigid_err)<TOL,'TRANSFER:'+label)
        # Wrong-sign transfer must be rejected by comparison with the
        # nonzero distributed load, even if its total resultant is zero.
        # Actual target vector is not forced to cancel nodal-by-nodal.
        wrong=norm(-f-f)/max(norm(f),1e-300)
        need(wrong>1.,'NEGATIVE_SIGN_CONTROL')
        results[label]={'force_relative':ferr,'moment_relative':terr,
            'adjoint_work_relative':workerr,'rigid_velocity_relative':rigid_err,
            'wrong_sign_relative':wrong,'work_W':work,'quadrature_work_W':qw}
    fl,fm=forces
    c0,c1=supports[0][0],supports[1][0]
    combined_force=norm(fl.sum(axis=0)+fm.sum(axis=0))/scale
    combined_moment=norm(np.cross(c0,fl).sum(axis=0)+np.cross(c1,fm).sum(axis=0))/(R*scale)
    need(max(combined_force,combined_moment)<TOL,'COMBINED_RESULTANTS')
    return {'sides':results,'combined_force_relative':combined_force,'combined_moment_relative':combined_moment}

def selftest():
    R=10.; z=np.array([2.,1.]); raw=np.array([[1.,0.,0.],[0.,1.,0.]])
    a=np.array([3.,4.]); gx=np.array([0.,2.]); gy=np.array([0.,3.])
    x,n,A,av,er,l=surface(R,z,gx,gy,raw,a)
    need(np.allclose(n[0],er[0]) and abs(A[0]-3*.8**2)<1e-14,'FLAT_RADIAL')
    need(np.all(dot(n,er)>0),'OUTWARD')
    w=np.array([[.2,.3,.5],[.4,.1,.5]])
    for split in (None,[.2,.3,.5]):
        W=trace_weights(w,np.array([9.,10.]),8.,11.,split)
        need(np.allclose(W.sum(axis=1),1),'SELFTEST_PARTITION')
    negatives=[]
    for name,fn in (
        ('negative_weight',lambda:trace_weights(np.array([[-.1,.5,.6]]),np.array([9.]),8.,11.)),
        ('uncovered_radius',lambda:trace_weights(w,np.array([7.,9.]),8.,11.)),
        ('inverted_bracket',lambda:trace_weights(w,np.array([9.,10.]),11.,8.)),
        ('inverted_radius',lambda:surface(R,np.array([11.,1.]),gx,gy,raw,a)),
        ('negative_area',lambda:surface(R,z,gx,gy,raw,-a)),
        ('invalid_split',lambda:trace_weights(w,np.array([9.,10.]),8.,11.,[0.,.5,.5]))):
        try: fn()
        except RuntimeError: negatives.append(name)
        else: raise RuntimeError('NEGATIVE_ACCEPTED:'+name)
    return {'screen_pass':True,'negative_cases_rejected':negatives}

def audit(q,r,p,out):
    with np.load(r/'native_diorite2/GLOBAL_PRE_BC_FIELDS.npz',allow_pickle=False) as d:
        xyz=d['native_xyz']; G=d['rotation_candidates']; b=d['rhs']
    need(xyz.shape==(N,3) and G.shape==(2*N,3) and b.shape==(2*N,),'G32_FIELDS')
    need(np.max(abs(np.linalg.norm(xyz,axis=1)-1))<1e-10,'UNIT_NODES')
    R=float(read(r/'native_diorite2/CONDITIONAL_CONTROLS.json')['radius'])
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    s=np.fromfile(q/'pressure_audit/SQUEEZ_PRESSURE.bin',dtype=g26.PD)
    need(len(f)==len(s)==Q and np.isfinite(f['v']).all() and np.isfinite(s['v']).all(),'QUADRATURE')
    ids=f['ids']; v=f['v']; pv=s['v']; w=pv[:,:3]
    need(np.array_equal(ids[:,0],np.tile(np.arange(1,E+1),7)) and
        np.array_equal(ids[:,1],np.repeat(np.arange(1,8),E)) and
        np.array_equal(ids[:,2:],s['ids']) and np.array_equal(v[:,4:7],w) and
        np.array_equal(v[:,1],pv[:,11]),'IP_JOIN')
    node=ids[:E,2:].astype(np.int64)-1
    need(node.min()>=0 and node.max()<N and np.array_equal(ids[:,2:].reshape(7,E,3),
        np.broadcast_to(node+1,(7,E,3))),'NODE_ORDER')
    W=w.reshape(7,E,3)[:,0,:].copy()
    need(np.array_equal(w.reshape(7,E,3),np.broadcast_to(W[:,None,:],(7,E,3))) and np.linalg.matrix_rank(W)==3,'WEIGHTS')
    z=pv[:,4]-pv[:,3]
    ze=np.linalg.lstsq(W,z.reshape(7,E),rcond=None)[0].T
    need(g28.rel((W@ze.T).ravel(),z)<1e-11,'DEPTH_FIT')
    low=np.full(N,np.inf); high=np.full(N,-np.inf)
    np.minimum.at(low,node.ravel(),ze.ravel()); np.maximum.at(high,node.ravel(),ze.ravel())
    need(np.isfinite(low).all() and np.isfinite(high).all() and np.max(high-low)/np.max(abs(ze))<1e-10,'SHARED_DEPTH')
    gx,gy,st=g28.gradients(xyz[node],ze,W)
    need(max(g28.rel(gx,v[:,2]),g28.rel(gy,v[:,3]/st))<1e-7,'METRIC_PARITY')
    area=v[:,0]*R
    need(np.all(area>0) and abs(area.sum()/(4*np.pi*R**2)-1)<1e-8,'REFERENCE_AREA')
    raw=np.einsum('qj,qjk->qk',w,xyz[ids[:,2:]-1])
    x,n,A,av,er,length=surface(R,z,gx,gy,raw,area)
    with np.load(p/'INDEPENDENT_PRESSURES.npz',allow_pickle=False) as d:
        need(np.array_equal(d['element_ip'],ids[:,:2]) and np.array_equal(d['native_anomaly_Pa'],v[:,1]),'G37_JOIN')
        ref=d['reference_Pa']; column=d['column_Pa']; sig=d['predicted_anomaly_Pa']
    need(all(a.shape==(Q,) and np.isfinite(a).all() for a in (ref,column,sig)) and
        np.array_equal(ref-column,sig) and g28.rel(sig,v[:,1])<1e-12,'G37_PRESSURE')
    # Preserve the G32 thin-shell baseline; compare it separately from
    # physical-radius graph resultants, which include radial force.
    phi=v[:,7:].reshape(Q,3,2,2).transpose(0,1,3,2)
    local=-area[:,None,None]*sig[:,None,None]*np.einsum('qnab,qb->qna',phi,np.column_stack((gx,gy))/R)
    thin=np.zeros((N,2)); np.add.at(thin,(ids[:,2:]-1).ravel(),local.reshape(-1,2))
    thin_t=R*(G.T@thin.ravel()); baseline=R*(G.T@b)
    need(rel(thin_t,baseline)<1e-10,'G32_ROTATION_REPLAY')
    del phi,local,thin
    geom={'radius_range_m':[float((R-z).min()),float((R-z).max())],
          'area_m2':float(A.sum()),'area_to_reference':float(A.sum()/area.sum()),
          'normal_radial_cosine_range':[float(dot(n,er).min()),float(dot(n,er).max())],
          'thin_shell_torque_Nm':thin_t.tolist(),'G32_torque_Nm':baseline.tolist(),
          'thin_shell_torque_relative_error':rel(thin_t,baseline)}
    write(out/'GEOMETRY_DIAGNOSTIC.json',geom)
    print('G37B_VARIABLE_RADIUS_GEOMETRY_PASS',flush=True)
    # Unit pressure on a closed graph: report integration error independently.
    unit=A[:,None]*n
    closure={'force_relative':norm(unit.sum(axis=0))/A.sum(),
             'moment_relative':norm(np.cross(x,unit).sum(axis=0))/(R*A.sum())}
    # This is a bounded quadrature screen, not proof of convergence.
    need(max(closure.values())<1e-6,'CONSTANT_PRESSURE_CLOSED_SURFACE')
    load=-sig[:,None]*unit
    ref_load=-ref[:,None]*unit; col_load=column[:,None]*unit
    need(rel(ref_load+col_load,load)<TOL,'PRESSURE_DECOMPOSITION')
    radial=dot(load,er)[:,None]*er; tangential=load-radial
    radial_u=1e-9*(1+.2*er[:,2])[:,None]*er
    tangent_u=1e-9*np.cross(np.array([.3,-.2,.6]),er)
    pressure={}
    for label,L in (('reference',ref_load),('negative_column',col_load),('anomaly',load)):
        pressure[label]={'force_N':L.sum(axis=0).tolist(),'torque_Nm':np.cross(x,L).sum(axis=0).tolist(),
            'radial_work_W':float(np.sum(L*radial_u)),'tangential_work_W':float(np.sum(L*tangent_u))}
    need(norm(np.cross(x,radial).sum(axis=0))/(R*np.linalg.norm(load,axis=1).sum())<TOL,'RADIAL_TORQUE')
    pressure['anomaly']['radial_fraction_l2']=norm(radial)/norm(load)
    pressure['anomaly']['tangential_fraction_l2']=norm(tangential)/norm(load)
    write(out/'PRESSURE_RESULTANTS.json',pressure)
    supports,identity=support(xyz,node,ids,w,R-z,length,x)
    results=transfer(load,x,supports,R)
    write(out/'TRANSFER_DIAGNOSTIC.json',results)
    print('G37B_DISTINCT_SUPPORT_TRANSFER_PASS',flush=True)
    return {'quadrature_points':Q,'geometry':geom,'constant_pressure_closure':closure,'pressure':pressure,
        'support_identity':identity,'transfer':results,
        'normal_sign':'outward from mantle; lithosphere anomaly diagnostic -sigma*n',
        'geometry_scope':'retained candidate LAB radial graph with reference quadrature, not physical boundary admission',
        'pressure_scope':'runtime datum anomaly, not absolute EOS or dynamic traction',
        'limitations':['Both traces are manufactured chord-prism supports; real SHELLS/ASPECT trace mapping is unqualified.',
           'No physically admitted normal reaction, radial velocity or traction imposed.',
           'No hydrostatic/dynamic pressure partition or unresolved-layer selection.',
           'Constant-pressure closure is one quadrature screen, not mesh convergence.'],
        'physical_normal_reaction_established':False,'mantle_provider_qualified':False,'traction_applied':False}

def main():
    ap=argparse.ArgumentParser()
    for k in ('g26','g32','g36r2','g37','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-normal-transfer-diagnostic-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    q,r,s,p,out=(x.resolve() for x in (a.g26,a.g32,a.g36r2,a.g37,a.output))
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def source_check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and
            not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    source_check()
    def parents():
        m=[g27.verify(q),g32.verify(r,g33.PIN,g33.STATUS),g32.verify(s,P36,S36),g32.verify(p,P37,S37)]
        need(all(x['G26_manifest_sha256']==g27.PIN and x['G32_manifest_sha256']==g33.PIN for x in m[2:]),'LINEAGE')
        need(m[2]['screen_pass'] and m[3]['screen_pass'],'PARENT_SCREEN')
        return m
    before=parents()
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in (root,q,r,s,p)),'OUTPUT')
    out.mkdir()
    report={'source_sha':g25.SOURCE,'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,
        'G36R2_manifest_sha256':P36,'G37_manifest_sha256':P37,'additional_builds':0,'additional_native_assemblies':0,
        'additional_global_solves':0,'additional_time_advance_years':0,'material_assignments':0,
        'physical_acceptance':False,'global_solve_authorized':False,**g25.SCOPE}
    try:
        write(out/'SELFTEST.json',selftest())
        report['audit']=audit(q,r,p,out)
        report.update(screen_pass=True,status='G37B_NORMAL_GEOMETRY_TRANSFER_PASS__PHYSICAL_REACTION_AND_REAL_MESH_AUTHORITY_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G37B_NORMAL_GEOMETRY_TRANSFER_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        need(parents()==before,'PARENT_MUTATION'); source_check()
        report['source_and_parents_unchanged']=True
    except Exception as e:
        report.update(screen_pass=False,status='G37B_NORMAL_GEOMETRY_TRANSFER_BLOCKED',postcheck_error=repr(e))
    write(out/'REPORT.json',report)
    write(out/'MANIFEST.json',{**{k:v for k,v in report.items() if k!='audit'},
        'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G37B_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
