#!/usr/bin/env python3
"""Independently integrate PRE density; never derive column pressure as pr-sigma.
Replay the frozen runtime's trapezoidal depth grid, including sea-level branches.
This is pressure provenance, not physical normal traction or mantle equilibrium.
"""
import argparse
from pathlib import Path
import subprocess
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g26_basal_pressure_audit as g26
import arcana_g27_interface_torque_budget as g27
import arcana_g33_native_basal_coupling_audit as g33
import arcana_g34_basal_depth_support as g34


def integrate_column(elev, stop, gravity, km, water, density):
    arrays=[np.asarray(v,dtype=float) for v in (elev,stop,gravity,km,water)]
    if not all(v.shape==arrays[0].shape and np.isfinite(v).all() for v in arrays):
        raise ValueError('COLUMN_SHAPE_FINITE')
    elev,stop,gravity,km,water=arrays
    if np.any(stop<0) or np.any(gravity<=0) or np.any(km<=0) or np.any(water<=0):
        raise ValueError('COLUMN_DOMAIN')
    h0=np.minimum(elev,0.)
    n=np.trunc((stop-h0)/km).astype(int)
    if np.any((stop-elev)/km>=300): raise ValueError('REFERENCE_TABLE_BOUND')
    def sample(h):
        rho=np.where(h>0,density(np.maximum(h,0.)),water)
        if not np.isfinite(rho).all() or np.any(rho<=0): raise ValueError('DENSITY')
        return rho
    prev=np.where(elev>0,density(np.zeros_like(elev)),water)
    total=np.zeros_like(elev)
    for i in range(1,int(n.max())+1):
        nxt=sample(h0+i*km)
        total+=np.where(i<=n,.5*(prev+nxt)*km,0.)
        prev=np.where(i<=n,nxt,prev)
    remainder=stop-(h0+n*km)
    total+=.5*(prev+sample(stop))*remainder
    return gravity*total


def effective_density(x,weights,h):
    # Interpolate raw rho, alpha and T separately, exactly as EvaluateWeighted.
    # In particular, this is not an interpolation of nodal effective densities.
    t=np.zeros_like(h); rho=np.zeros_like(h); alpha=np.zeros_like(h)
    for j in range(3):
        v=x[:,j,:]; crust=h<v[:,15]; lith=h<=v[:,17]
        da=h-v[:,39]; db=h-v[:,45]
        a=((v[:,41]*da+v[:,42])*da+v[:,43])*da+v[:,44]
        b=((v[:,47]*db+v[:,48])*db+v[:,49])*db+v[:,50]
        c=v[:,20]*np.exp(v[:,34]*9.82*(h-v[:,17])/v[:,36])
        w=np.maximum(weights[:,j],0.)
        t+=w*np.where(crust,a,np.where(lith,b,c))
        rho+=w*np.where(crust,v[:,27],np.where(lith,v[:,32],v[:,37]))
        alpha+=w*np.where(crust,v[:,29],v[:,34])
    return rho*(1.-alpha*t)


def manufactured_selftest():
    # Constant and linear rho: trapezoids have an independent analytic integral.
    cases=[]
    for elev in (2500.,0.,-2500.):
        for stop in (0.,5500.,6000.):
            e,s,g,k,w=(np.array([v]) for v in (elev,stop,9.82,1000.,1000.))
            for slope in (0.,.001):
                rho=lambda h: 3000.+slope*h
                p=integrate_column(e,s,g,k,w,rho)[0]
                # At h=0 submerged branch chooses water; reproduce that endpoint
                # convention explicitly rather than claiming continuous-interface exactness.
                h0=min(elev,0.); n=int((stop-h0)/1000.)
                hs=np.r_[h0+np.arange(n+1)*1000.,stop]
                vals=np.where(hs>0,rho(hs),1000.)
                if elev>0: vals[0]=3000.
                reference=9.82*np.sum(.5*(vals[:-1]+vals[1:])*np.diff(hs))
                if abs(p-reference)>1e-12*max(abs(reference),1.): raise RuntimeError('MANUFACTURED_GRID')
                if elev>0:
                    exact=9.82*(3000.*stop+slope*stop**2/2)
                    if abs(p-exact)>1e-12*max(abs(exact),1.): raise RuntimeError('MANUFACTURED_ANALYTIC')
                cases.append({'elevation_m':elev,'stop_m':stop,'rho_slope_kg_m4':slope,'pressure_Pa':p})
    return {'screen_pass':True,'cases':cases,'sea_level_density_jump_explicit':True}


def main():
    ap=argparse.ArgumentParser()
    for key in ('g26','g32','output'): ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args(); q,r,out=(p.resolve() for p in (a.g26,a.g32,a.output))
    def source_check():
        g25.need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE
             and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    source_check()
    import arcana_g32_corrected_global_operator as g32
    def parents(): return [g27.verify(q),g32.verify(r,g33.PIN,g33.STATUS)]
    before=parents()
    g25.need(not out.exists() and not any(out.is_relative_to(p) or p.is_relative_to(out) for p in (q,r,Path.cwd())),'OUTPUT')
    out.mkdir()
    g25.write(out/'MANUFACTURED.json',manufactured_selftest())
    x=g34.read_pre(r/'native_diorite2/regional_PRE.dat')
    f=np.fromfile(q/'pressure_audit/FB2_QUADRATURE.bin',dtype=g26.FD)
    s=np.fromfile(q/'pressure_audit/SQUEEZ_PRESSURE.bin',dtype=g26.PD)
    g25.need(len(f)==len(s)==g26.Q and np.array_equal(f['ids'][:,2:],s['ids'])
             and np.array_equal(f['v'][:,4:7],s['v'][:,:3]),'QUADRATURE_JOIN')
    p=s['v']; nodes=s['ids'].astype(int)-1
    columns=np.empty(g26.Q); reference=np.empty(g26.Q)
    for start in range(0,g26.Q,16384):
        sl=slice(start,min(start+16384,g26.Q)); local=p[sl]; weights=local[:,:3]
        xx=x[nodes[sl]]
        elev,stop,g,km,rw,ra,rt,pr,sig=local[:,3:].T
        columns[sl]=integrate_column(elev,stop,g,km,rw,lambda h:effective_density(xx,weights,h))
        # Independent interval-overlap sum for the eight reference layers.
        z=np.maximum(stop-elev,0.)
        rho=np.column_stack((rw,rw,.7*rw+.3*rt,rt,rt,rt,rt,.7*rt+.3*ra))
        thickness=np.clip(z[:,None]-km[:,None]*np.arange(8),0,km[:,None])
        reference[sl]=g*(np.sum(thickness*rho,axis=1)+np.maximum(z-8*km,0)*ra)
        if start%131072==0: print('G37_RECONSTRUCTED_IP',start,flush=True)
    expected_ref=p[:,10]; expected_sig=p[:,11]
    predicted_sig=reference-columns
    referr=float(np.max(abs(reference-expected_ref))/max(np.max(abs(expected_ref)),1.))
    err=float(np.max(abs(predicted_sig-expected_sig))/max(np.max(abs(expected_sig)),1.))
    np.savez_compressed(out/'INDEPENDENT_PRESSURES.npz',column_Pa=columns,reference_Pa=reference,
         predicted_anomaly_Pa=predicted_sig,native_anomaly_Pa=expected_sig,element_ip=f['ids'][:,:2])
    report={'status':'G37_COLUMN_RECONSTRUCTION_PASS__NORMAL_REACTION_AUTHORITY_REQUIRED' if max(referr,err)<1e-12 else 'G37_COLUMN_RECONSTRUCTION_BLOCKED',
        'screen_pass':bool(max(referr,err)<1e-12),'quadrature_points':g26.Q,
        'reference_relative_inf':referr,'independent_anomaly_relative_inf':err,
        'column_pressure_range_Pa':[float(columns.min()),float(columns.max())],
        'elevation_branches':{'above_sea_level':int(np.count_nonzero(p[:,3]>0)),
            'at_sea_level':int(np.count_nonzero(p[:,3]==0)),'below_sea_level':int(np.count_nonzero(p[:,3]<0))},
        'column_derived_by_subtraction':False,'thermal_density_scope':'frozen PRE reference and runtime, not EOS admission',
        'tau_zz_native_not_retained':True,'reference_table_error_paths_not_native_retested':True,
        'actual_variable_radius_surface_normal_and_radial_work_closed':False,
        'physical_normal_reaction_established':False,'additional_builds':0,'additional_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'physical_acceptance':False,**g25.SCOPE}
    g25.need(parents()==before,'PARENT_MUTATION'); source_check()
    g25.write(out/'REPORT.json',report)
    g25.write(out/'MANIFEST.json',{'files':g25.inventory(out),'runner_sha256':g25.sha(Path(__file__)),
          'source_sha':g25.SOURCE,'G26_manifest_sha256':g27.PIN,'G32_manifest_sha256':g33.PIN,**report})
    print(report,flush=True); return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
