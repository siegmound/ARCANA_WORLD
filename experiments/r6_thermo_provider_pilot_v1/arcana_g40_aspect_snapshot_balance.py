#!/usr/bin/env python3
"""G40: independent Q1 volume/boundary reconstruction of retained G39 VTU.
This is an export-resolution audit, not native FE traction or physical authority.
No ASPECT executions, no new material or history advance.
"""
import argparse
import itertools
import json
from pathlib import Path
import subprocess
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g32_corrected_global_operator as g32
import arcana_g39_aspect_free_slip as g39
from arcana_worldsim.r6.adapters.aspect_snapshot_reader import AspectSnapshotSeries, ReaderLimits

PIN='07ba543a44e841fb5d0397cef86154c3eed818a3473160cb8d529068d4d1399b'
STATUS='G39_ASPECT_FREE_SLIP_GAUGE_SCREEN_PASS__NATIVE_TRACTION_AND_STATE_REQUIRED'
AUTH='G40_RETAINED_SNAPSHOT_BALANCE_ONLY_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
# VTK_HEXAHEDRON ordering, reference coordinates [-1,1]^3.
S=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
            [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],dtype=float)
I=np.eye(3)
def shape(q):
    a=1+S*np.asarray(q)
    N=np.prod(a,axis=1)/8
    d=np.column_stack([S[:,i]*np.prod(a[:,[j for j in range(3) if j!=i]],axis=1)/8 for i in range(3)])
    return N,d
def interpolate(x,u,p,t,q):
    N,d=shape(q)
    xx=np.einsum('j,cji->ci',N,x); vv=np.einsum('j,cji->ci',N,u)
    J=np.einsum('cji,jk->cik',x,d)
    det=np.linalg.det(J)
    need(np.isfinite(det).all() and np.all(det>0),'INVERTED_EXPORT_CELL')
    inv=np.linalg.inv(J)
    grad=np.einsum('cji,jk,ckl->cil',u,d,inv)
    div=np.trace(grad,axis1=1,axis2=2)
    strain=(grad+grad.transpose(0,2,1))/2-div[:,None,None]*I/3
    pp=p@N; tt=t@N
    return xx,vv,pp,tt,J,det,inv,div,strain
def dot(a,b): return np.einsum('ci,ci->c',a,b)
def mag(a): return np.linalg.norm(a,axis=1)
def rel(a,b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))
def integrate(coords,u,p,t,cells,datum,order=3):
    x=coords[cells]; v=u[cells]; pp=p[cells]; tt=t[cells]
    points,weights=np.polynomial.legendre.leggauss(order)
    vals={k:0. for k in ('volume','u2','p_integral','dissipation','body_work','hydro_body_work',
        'dynamic_body_work','pressure_div_work','div2','density_integral','dynamic_p2')}
    force=np.zeros(3); torque=np.zeros(3); angular=np.zeros(3); inertia=np.zeros((3,3))
    for ids in itertools.product(range(order),repeat=3):
        q=points[list(ids)]; w=float(np.prod(weights[list(ids)]))
        xx,vv,pq,tq,J,det,inv,div,eps=interpolate(x,v,pp,tt,q)
        dv=w*det; rr=mag(xx); need(np.min(rr)>0,'RADIUS')
        er=xx/rr[:,None]; rho=1000*(1-.001*(tq-1000))
        need(np.all(rho>0),'DENSITY')
        body=-rho[:,None]*er; hyd=-1000*er; dyn=body-hyd
        pd=pq-1000*(1-rr)-datum
        add={'volume':np.ones(len(dv)),'u2':dot(vv,vv),'p_integral':pq,
             'dissipation':2*np.sum(eps*eps,axis=(1,2)),'body_work':dot(body,vv),
             'hydro_body_work':dot(hyd,vv),'dynamic_body_work':dot(dyn,vv),
             'pressure_div_work':pq*div,'div2':div*div,'density_integral':rho,'dynamic_p2':pd*pd}
        for k,a in add.items(): vals[k]+=float(dv@a)
        force+=dv@body; torque+=dv@np.cross(xx,body); angular+=dv@np.cross(xx,vv)
        inertia+=np.einsum('c,cij->ij',dv,rr[:,None,None]**2*I-xx[:,:,None]*xx[:,None,:])
    vals.update(rms=float(np.sqrt(vals['u2']/vals['volume'])),
        pmean=vals['p_integral']/vals['volume'],div_rms=float(np.sqrt(vals['div2']/vals['volume'])),
        dynamic_pressure_rms=float(np.sqrt(vals['dynamic_p2']/vals['volume'])),
        body_force=force.tolist(),body_torque=torque.tolist(),
        volumetric_rotation=np.linalg.solve(inertia,angular).tolist(),inertia=inertia.tolist())
    # Select boundary faces by radial node membership; no coordinate merging
    # or averaging across discontinuous exported cells. Check full shell area.
    radii=np.linalg.norm(x,axis=2)
    faces={k:{'count':0,'area':0.,'force':np.zeros(3),'torque':np.zeros(3),
              'work':0.,'normal_velocity2':0.,'tangential_traction2':0.,
              'dynamic_force':np.zeros(3),'dynamic_torque':np.zeros(3),
              'dynamic_work':0.,'abs_load':0.} for k in ('inner','outer')}
    for ax in range(3):
        rem=[i for i in range(3) if i!=ax]
        for sign in (-1,1):
            face=S[:,ax]==sign
            for label,r0 in (('inner',.5),('outer',1.)):
                mask=np.max(abs(radii[:,face]-r0),axis=1)<.002
                if not np.any(mask): continue
                f=faces[label]; f['count']+=int(mask.sum())
                for i,j in itertools.product(range(order),repeat=2):
                    q=np.zeros(3); q[ax]=sign; q[rem]=points[[i,j]]
                    xx,vv,pq,tq,J,det,inv,div,eps=interpolate(x[mask],v[mask],pp[mask],tt[mask],q)
                    av=sign*det[:,None]*inv[:,ax,:]
                    an=mag(av); n=av/an[:,None]
                    da=an*weights[i]*weights[j]
                    er=xx/mag(xx)[:,None]
                    need(np.min(dot(n,er)*(1 if label=='outer' else -1))>.9,'FACE_ORIENTATION')
                    stress=2*eps-pq[:,None,None]*I
                    tr=np.einsum('cij,cj->ci',stress,n)
                    pd=pq-1000*(1-mag(xx))-datum
                    td=np.einsum('cij,cj->ci',2*eps-pd[:,None,None]*I,n)
                    f['area']+=float(da.sum()); f['force']+=da@tr; f['torque']+=da@np.cross(xx,tr)
                    f['work']+=float(da@dot(tr,vv)); f['normal_velocity2']+=float(da@(dot(vv,n)**2))
                    f['tangential_traction2']+=float(da@dot(tr-dot(tr,n)[:,None]*n,tr-dot(tr,n)[:,None]*n))
                    f['dynamic_force']+=da@td; f['dynamic_torque']+=da@np.cross(xx,td)
                    f['dynamic_work']+=float(da@dot(td,vv)); f['abs_load']+=float(da@mag(tr))
    for label,f in faces.items():
        need(f['count']>0 and f['area']>0,'MISSING_BOUNDARY:'+label)
        f['normal_velocity_rms']=float(np.sqrt(f['normal_velocity2']/f['area']))
        f['tangential_traction_rms']=float(np.sqrt(f['tangential_traction2']/f['area']))
        for k in ('force','torque','dynamic_force','dynamic_torque'): f[k]=f[k].tolist()
    vals['boundaries']=faces
    bw=sum(f['work'] for f in faces.values())
    vals['boundary_work']=bw
    vals['energy_residual_W']=vals['dissipation']-vals['body_work']-bw-vals['pressure_div_work']
    vals['resultant_force_residual_N']=(force+sum(np.array(f['force']) for f in faces.values())).tolist()
    vals['resultant_torque_residual_Nm']=(torque+sum(np.array(f['torque']) for f in faces.values())).tolist()
    return vals

def load_case(p,name):
    work=p/name
    case=read(work/'CASE_REPORT.json')
    need(case['name']==name and case['native_exit']==0 and case['time_s']==0,'CASE_AUTHORITY')
    pvd=work/'output/solution.pvd'
    series=AspectSnapshotSeries(pvd,run_id='G40_'+name,mpi_rank_count=1,time_unit='s',
        time_unit_source='G39 verified input.prm and statistics',solver_completed_time=0,
        limits=ReaderLimits(max_points=500000,max_cells=500000,max_materialized_values=8000000,
                            max_estimated_python_bytes=320000000))
    need(series.times()==(0.,),'SNAPSHOT_TIME')
    s=series.read_snapshot(0); m=s.mesh
    need(set(m.cell_types)=={12},'EXPORT_NOT_LINEAR_HEXAHEDRA')
    need(np.array_equal(m.offsets,np.arange(1,m.cell_count+1)*8),'CONNECTIVITY')
    need(m.cell_count==8*case['cells'],'EXPECTED_Q2_VISUALIZATION_SUBDIVISIONS')
    x=np.asarray(m.coordinates,dtype=float).reshape(-1,3)
    cells=np.asarray(m.connectivity,dtype=np.int64).reshape(-1,8)
    def field(key,n):
        a=s.fields[key]; need(a.metadata.components==n and a.metadata.tuples==len(x),'FIELD_SHAPE:'+key)
        return np.asarray(a.values,dtype=float).reshape(-1,n)
    u=field('point:velocity',3); pp=field('point:p',1).ravel(); t=field('point:T',1).ravel()
    exact=1000+100*(x[:,0]*x[:,1]+.3*x[:,2]) if case['forced'] else np.full(len(x),1000.)
    need(np.max(abs(t-exact))<1.,'TEMPERATURE_EXPORT_IDENTITY')
    return case,s.record,x,u,pp,t,cells

def selftest():
    # Exact affine gradient on the standard VTK unit cube.
    x=(S+1)[None,:,:]/2
    M=np.array([[1.,2.,3.],[-2.,4.,.5],[.3,-.5,-1.]])
    u=x@M.T
    z=np.zeros((1,8))
    xx,v,p,t,J,det,inv,div,eps=interpolate(x,u,z,z,[.2,-.3,.1])
    target=(M+M.T)/2-np.trace(M)*I/3
    need(np.max(abs(eps[0]-target))<1e-14 and abs(det[0]-.125)<1e-14 and abs(div[0]-np.trace(M))<1e-14,'AFFINE_SELFTEST')
    rot=np.cross(np.array([.2,-.4,.7]),x)
    need(np.max(abs(interpolate(x,rot,z,z,[.2,-.3,.1])[-1]))<1e-14,'RIGID_SELFTEST')
    try: interpolate(x[:,:,::-1],u,z,z,[0,0,0])
    except RuntimeError: pass
    else: raise RuntimeError('INVERTED_SELFTEST')
    return True

def audit(p,out):
    rows={}; fields={}
    for name,*_ in g39.CASES:
        case,record,x,u,pp,t,cells=load_case(p,name)
        # Two quadrature rules on the same exported Q1 mesh, not FE convergence.
        d2=integrate(x,u,pp,t,cells,case['datum_Pa'],2)
        d=integrate(x,u,pp,t,cells,case['datum_Pa'],3)
        checks={'volume_geometry':abs(d['volume']/(4*np.pi/3*(1-.5**3))-1)<.02,
            'inner_area':abs(d['boundaries']['inner']['area']/np.pi-1)<.02,
            'outer_area':abs(d['boundaries']['outer']['area']/(4*np.pi)-1)<.02,
            'quadrature_volume':abs(d2['volume']/d['volume']-1)<1e-10,
            'quadrature_dissipation':abs(d2['dissipation']/max(d['dissipation'],1e-300)-1)<.03}
        if case['forced']:
            checks.update(rms_export_parity=abs(d['rms']/case['rms']-1)<.05,
                dissipation_export_parity=abs(d['dissipation']/case['dissipation']-1)<.15,
                energy_screen=abs(d['energy_residual_W'])/case['dissipation']<.25,
                radial_body_torque=float(np.linalg.norm(d['body_torque']))<1e-10,
                pressure_mean=abs(d['pmean']-case['pmean'])<1.)
            fields[name]=(x,u,pp,cells)
        row={'case':name,'native':case,'snapshot_id':record.snapshot_id,
             'mesh_fingerprint':record.mesh_fingerprint,'precision_types':list(record.precision_types),
             'export_cells':len(cells),'quadrature2':d2,'quadrature3':d,'checks':checks,'screen_pass':all(checks.values())}
        write(out/(name+'_BALANCE.json'),row); rows[name]=row
        print('G40_CASE',name,json.dumps({'checks':checks,'rms':d['rms'],'dissipation':d['dissipation'],
             'body_work':d['body_work'],'boundary_work':d['boundary_work'],'pressure_div_work':d['pressure_div_work'],
             'energy_residual_W':d['energy_residual_W']},allow_nan=False),flush=True)
    x,u,pp,c=fields['forced_volume_3']; comparisons={}
    for name in ('forced_surface_3','forced_datum_3'):
        y,v,p1,c1=fields[name]
        need(np.array_equal(x,y) and np.array_equal(c,c1),'FORCED_MESH_IDENTITY')
        shift=10. if name=='forced_datum_3' else 0.
        comparisons[name]={'velocity_l2_relative':rel(v,u),
            'pressure_shift_max_error_Pa':float(np.max(abs(p1-pp-shift)))}
    pair_pass=all(v['velocity_l2_relative']<1e-5 and v['pressure_shift_max_error_Pa']<1e-3 for v in comparisons.values())
    return {'cases':{k:{'checks':v['checks'],'screen_pass':v['screen_pass']} for k,v in rows.items()},
        'pointwise_gauge_and_datum':comparisons,'pointwise_screen_pass':pair_pass,
        'screen_pass':pair_pass and all(v['screen_pass'] for v in rows.values()),
        'native_FE_traction_qualified':False,'native_FE_rank_proven':False}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--g39',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--authorize-retained-snapshot-balance-only',choices=[AUTH],required=True)
    a=ap.parse_args(); p=a.g39.resolve(); out=a.output.resolve()
    source=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def source_check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'FROZEN_SOURCE')
    source_check(); before=g32.verify(p,PIN,STATUS)
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in (source,p)),'OUTPUT')
    out.mkdir()
    report={'source_sha':g25.SOURCE,'G39_manifest_sha256':PIN,'additional_builds':0,'additional_native_solves':0,
            'additional_time_advance_years':0,'material_assignments':0,'global_solve_authorized':False,
            'physical_acceptance':False,'mantle_provider_qualified':False,**g25.SCOPE}
    try:
        need(selftest(),'SELFTEST')
        report['audit']=audit(p,out)
        need(report['audit']['screen_pass'],'EXPORT_BALANCE_SCREEN')
        report.update(screen_pass=True,status='G40_ASPECT_EXPORTED_BALANCE_PASS__NATIVE_TRACTION_AND_STATE_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G40_ASPECT_EXPORTED_BALANCE_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        source_check(); need(g32.verify(p,PIN,STATUS)==before,'PARENT_MUTATION')
        report['source_and_parent_unchanged']=True
    except Exception as e:
        report.update(screen_pass=False,status='G40_ASPECT_EXPORTED_BALANCE_BLOCKED',postcheck_error=repr(e))
    report['limitations']=['Q1 interpolated VTU subcells, not native Q2 Stokes FE quadrature.',
        'Boundary faces classified by radius and area; export stress is diagnostic only.',
        'Resultants and boundary tractions reported, not admitted or used to correct any RHS.',
        'Hydrostatic/dynamic split uses synthetic G39 density, not ARCANA EOS.']
    write(out/'REPORT.json',report); write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G40_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
