"""HR2-P1-D2 v1: explicit frozen-V1 spatial diagnostics; never revises V1."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import traceback


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def table(path, rows):
    with Path(path).open('x', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--expected-contract-sha256', required=True)
    parser.add_argument('--execute-frozen-v1-spatial-diagnostic', action='store_true')
    args = parser.parse_args()
    if not args.execute_frozen_v1_spatial_diagnostic:
        parser.error('Explicit diagnostic opt-in required')
    repo = Path(__file__).resolve().parents[1]
    identity = json.loads(Path(args.identity).read_text())
    def pins():
        assert all(sha(repo / k) == v for k, v in identity['pins'].items()), 'SOURCE_CHANGED'
        assert sha(repo / 'experiments/hr2_p1/SOURCE_CONTRACT.json') == args.expected_contract_sha256 == identity['source_contract_sha256']
    pins()
    out = Path(args.output)
    out.mkdir()  # Must not exist; no overwrite or automatic retry.
    started = time.perf_counter()
    usage0 = resource.getrusage(resource.RUSAGE_SELF)
    put(out / 'INVOCATION.json', {'argv': sys.argv, 'driver_sha256': sha(__file__),
        'identity_sha256': sha(args.identity), 'source_contract_sha256': args.expected_contract_sha256,
        'scope': 'Only original two spatial modes, five grids, main/half dt and T0 flux probe; no full Q1 or correction',
        'roundoff_diagnostic_budget': '64*eps*incident absolute rate for EW+NS grouping;256*eps*(analytic incident rate + continuum rate + kappa*A/R2*H0) for analytic face closure; not a modified solver acceptance',
        'scientific_authority': False, 'production_authority': False})
    try:
        import numpy as np
        sys.path.insert(0, str(repo / 'experiments'))
        from hr2_p1.manufactured import (new_case, continuum_heights, errors,
            SPATIAL_MESHES, SPATIAL_END_YEAR, KAPPA_M2_YEAR, RADIUS_M, MEAN_HEIGHT_M)
        from hr2_p1.model import finite_volume_step
        assert tuple(SPATIAL_MESHES) == ((16,8),(32,16),(64,32),(128,64),(256,128))
        assert SPATIAL_END_YEAR == .0001 and KAPPA_M2_YEAR == 405896410000. and RADIUS_M == 6371000.
        put(out / 'RUNTIME.json', {'python': sys.version, 'numpy': np.__version__,
            'executable': sys.executable, 'thread_environment': {k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}})
        qroot = Path(args.identity).resolve().parent.parent / 'HR2_P1_Q1_20261031_01/qualification'
        global_rows, bands, case_results = [], [], []
        for mode in ['latitude', 'longitude']:
            historical = json.loads((qroot / ('SPATIAL_CONVERGENCE_'+mode+'.json')).read_text())['rows']
            for index, (width, height) in enumerate(SPATIAL_MESHES):
                t0 = time.perf_counter(); u0 = resource.getrusage(resource.RUSAGE_SELF)
                folder = out / f'{mode}_{width}x{height}'; folder.mkdir()
                catalog = {}
                def save(name, array, unit):
                    a = np.ascontiguousarray(array)
                    p = folder / (name+'.npy')
                    with p.open('xb') as f:
                        np.save(f, a, allow_pickle=False)
                    catalog[name] = {'path':p.name, 'shape':list(a.shape), 'dtype':a.dtype.str,
                        'unit':unit, 'bytes':p.stat().st_size, 'sha256':sha(p),
                        'raw_C_sha256':hashlib.sha256(a.tobytes(order='C')).hexdigest()}
                case = new_case(width, height, SPATIAL_END_YEAR, mode)
                mesh = case.mesh; n = width*height; ne = n; kappa = KAPPA_M2_YEAR
                area = mesh.areas; dtang = math.pi/height
                row = np.repeat(np.arange(height, dtype='<i8'), width)
                col = np.tile(np.arange(width, dtype='<i8'), height)
                lat = -math.pi/2+(row+.5)*dtang
                lon = -math.pi+(col+.5)*dtang
                save('row', row, 'native SOUTH_TO_NORTH row'); save('column', col, 'periodic column')
                save('latitude_center_deg', np.degrees(lat), 'degree_north')
                save('longitude_center_deg', np.degrees(lon), 'degree_east')
                for name, a, unit in [('area',area,'m2'),('face_first',mesh.first,'cell_id'),('face_second',mesh.second,'cell_id'),('face_length',mesh.lengths,'m'),('center_distance',mesh.distances,'m'),('face_axis',np.r_[np.zeros(ne,dtype='u1'),np.ones(len(mesh.first)-ne,dtype='u1')],'0=EW;1=NS')]:
                    save(name,a,unit)
                initial_h = continuum_heights(width,height,0,mode)
                initial_v = case.volumes.copy()
                save('initial_analytic_h',initial_h,'m');save('initial_v',initial_v,'m3')
                reference = continuum_heights(width,height,SPATIAL_END_YEAR,mode)
                save('final_analytic_h',reference,'m')
                case.start_window(SPATIAL_END_YEAR); count=case.window['substeps'];dt=SPATIAL_END_YEAR/count
                # Probe one original old-state step on detached initial volumes only.
                pstart=time.perf_counter()
                probe_updated,probe_diag,transfer=finite_volume_step(mesh,initial_v,kappa,dt)
                probe_wall=time.perf_counter()-pstart
                h = initial_v/area
                rate = mesh.conductance(kappa)*(h[mesh.first]-h[mesh.second])
                assert np.array_equal(transfer,rate*dt), 'PROBE_TRANSFER_MISMATCH'
                def gather(face_values, start=0, stop=None):
                    sl=slice(start,stop)
                    return np.bincount(mesh.second[sl],weights=face_values[sl],minlength=n)-np.bincount(mesh.first[sl],weights=face_values[sl],minlength=n)
                ew=gather(rate,0,ne);ns=gather(rate,ne,None);total=gather(rate)
                incident=np.bincount(mesh.first,weights=np.abs(rate),minlength=n)+np.bincount(mesh.second,weights=np.abs(rate),minlength=n)
                eps=np.finfo(float).eps
                split_bound=64*eps*incident
                split_residual=ew+ns-total
                assert np.all(np.abs(split_residual)<=split_bound), 'DIRECTIONAL_GROUPING_ROUNDOFF'
                assert np.array_equal(initial_v+gather(transfer),probe_updated), 'FROZEN_STEP_RECONSTRUCTION_MISMATCH'
                # Exact continuum integrated face rates, oriented first -> second.
                edge_lam=-math.pi+(col+1)*dtang
                if mode=='latitude':
                    exact_ew=np.zeros(ne)
                else:
                    exact_ew=kappa*dtang*np.sin(edge_lam)
                nr=row[:width*(height-1)];nc=col[:width*(height-1)]
                phi_edge=-math.pi/2+(nr+1)*dtang
                lam_w=-math.pi+nc*dtang;lam_e=lam_w+dtang
                if mode=='latitude':exact_ns=-kappa*dtang*np.cos(phi_edge)**2
                else:exact_ns=kappa*np.cos(phi_edge)*np.sin(phi_edge)*(np.sin(lam_e)-np.sin(lam_w))
                exact_rate=np.r_[exact_ew,exact_ns]
                continuum_rate=(-2*kappa/RADIUS_M**2)*area*(initial_h-MEAN_HEIGHT_M)
                exact_total=gather(exact_rate)
                exact_incident=np.bincount(mesh.first,weights=np.abs(exact_rate),minlength=n)+np.bincount(mesh.second,weights=np.abs(exact_rate),minlength=n)
                closure_bound=256*eps*(exact_incident+np.abs(continuum_rate)+kappa*area/RADIUS_M**2*MEAN_HEIGHT_M)
                assert np.all(np.abs(exact_total-continuum_rate)<=closure_bound), 'ANALYTIC_FACE_CLOSURE'
                defect=total-continuum_rate
                defect_ew=ew-gather(exact_rate,0,ne);defect_ns=ns-gather(exact_rate,ne,None)
                for name,a,unit in [('T0_face_rate',rate,'m3/year first->second'),('T0_face_transfer',transfer,'m3 over probe dt'),('T0_exact_face_rate',exact_rate,'m3/year first->second'),('T0_volume_rate_EW',ew,'m3/year'),('T0_volume_rate_NS',ns,'m3/year'),('T0_volume_rate_total',total,'m3/year'),('T0_exact_continuum_volume_rate',continuum_rate,'m3/year'),('T0_exact_face_divergence',exact_total,'m3/year'),('T0_defect',defect,'m3/year'),('T0_defect_EW',defect_ew,'m3/year'),('T0_defect_NS',defect_ns,'m3/year'),('T0_grouping_residual',split_residual,'m3/year'),('T0_grouping_roundoff_bound',split_bound,'m3/year'),('T0_analytic_face_closure_bound',closure_bound,'m3/year'),('T0_probe_updated_v',probe_updated,'m3')]:save(name,a,unit)
                t=time.perf_counter();case.finish_window();main_wall=time.perf_counter()-t
                save('final_main_v',case.volumes,'m3');save('final_main_h',case.heights(),'m')
                half=new_case(width,height,SPATIAL_END_YEAR,mode)
                half.start_window(SPATIAL_END_YEAR,substeps=2*count)
                t=time.perf_counter();half.finish_window();half_wall=time.perf_counter()-t
                save('final_half_v',half.volumes,'m3');save('final_half_h',half.heights(),'m')
                # All reported errors/subsets derive from persisted arrays.
                final=np.load(folder/'final_main_h.npy',allow_pickle=False)
                ref=np.load(folder/'final_analytic_h.npy',allow_pickle=False)
                half_h=np.load(folder/'final_half_h.npy',allow_pickle=False)
                A=np.load(folder/'area.npy',allow_pickle=False)
                error=final-ref
                save('final_signed_error_h',error,'m')
                save('final_half_signed_error_h',half_h-ref,'m')
                norm=errors(final,ref,A);time_diff=errors(final,half_h,A)['L2_m']
                orig=historical[index]
                equal={key:norm[key]==orig[key] for key in ['L1_m','L2_m','Linf_m']}
                equal['half_dt_L2_difference_m']=time_diff==orig['half_dt_L2_difference_m']
                equal['accepted_steps']=count==orig['accepted_steps']
                equal['dt_histogram']=case.dt_histogram==orig['dt_histogram_hex_years']
                maximum=int(np.argmax(np.abs(error)))
                global_energy=math.fsum(map(float,A*error**2));global_area=math.fsum(map(float,A))
                def subset(label,mask):
                    ids=np.flatnonzero(mask);size=len(ids)
                    rr={'mode':mode,'width':width,'height':height,'selection':label,'cells':size,'native_rows':','.join(map(str,np.unique(row[ids]))),'status':'MEASURED' if size else 'EMPTY_SELECTION','area_m2':math.fsum(map(float,A[ids]))}
                    keys=['L1_m','L2_m','Linf_m','signed_mean_error_m','fraction_global_L2_squared','L2_squared_contribution_m2','defect_height_rate_L2_m_per_year','defect_EW_height_rate_L2_m_per_year','defect_NS_height_rate_L2_m_per_year','defect_cross_term_global_m2_per_year2']
                    if not size:rr.update({k:None for k in keys})
                    else:
                        rr.update(errors(final[ids],ref[ids],A[ids]))
                        rr['signed_mean_error_m']=math.fsum(map(float,A[ids]*error[ids]))/rr['area_m2']
                        energy=math.fsum(map(float,A[ids]*error[ids]**2))
                        rr['fraction_global_L2_squared']=energy/global_energy if global_energy else None
                        rr['L2_squared_contribution_m2']=energy/global_area
                        for name,values in [('defect_height_rate_L2_m_per_year',defect),('defect_EW_height_rate_L2_m_per_year',defect_ew),('defect_NS_height_rate_L2_m_per_year',defect_ns)]:
                            rr[name]=math.sqrt(math.fsum(map(float,A[ids]*(values[ids]/A[ids])**2))/rr['area_m2'])
                        rr['defect_cross_term_global_m2_per_year2']=2*math.fsum(map(float,defect_ew[ids]*defect_ns[ids]/A[ids]))/global_area
                    bands.append(rr)
                subset('global',np.ones(n,dtype=bool))
                for low in range(-90,90,10):subset(f'lat_band_{low}_{low+10}',(np.degrees(lat)>=low)&(np.degrees(lat)<low+10))
                for j in range(height):subset(f'native_row_{j}',row==j)
                for pole,base in [('south',row),('north',height-1-row)]:
                    for j in range(4):subset(f'{pole}_polar_row_{j}',base==j)
                    for k in [1,2,4]:subset(f'{pole}_first_{k}_rows',base<k)
                for k in [1,2,4]:
                    subset(f'exclude_{k}_rows_each_pole',(row>=k)&(row<height-k))
                    subset(f'both_first_{k}_polar_rows',(row<k)|(row>=height-k))
                for limit in [60,75,85]:subset(f'abs_lat_le_{limit}',np.abs(np.degrees(lat))<=limit)
                subset('seam_adjacent_columns',(col==0)|(col==width-1))
                subset('interior_columns',(col!=0)&(col!=width-1))
                u=resource.getrusage(resource.RUSAGE_SELF)
                result={'mode':mode,'width':width,'height':height,'end_year':case.year,**norm,
                    'half_dt_L2_difference_m':time_diff,'Q1_exact_scalar_matches':equal,
                    'maximum_error_cell_id':maximum,'maximum_error_latitude_deg':float(np.degrees(lat[maximum])),
                    'maximum_error_longitude_deg':float(np.degrees(lon[maximum])),'maximum_error_signed_m':float(error[maximum]),
                    'main_dt_histogram':case.dt_histogram,'half_dt_histogram':half.dt_histogram,
                    'main_accepted_steps':count,'half_accepted_steps':2*count,'T0_probe_dt_year':dt,
                    'T0_probe_wall_s':probe_wall,'main_kernel_wall_s_including_checks':main_wall,
                    'half_kernel_wall_s_including_checks':half_wall,
                    'main_face_evaluations_per_s_including_checks':len(mesh.first)*count/main_wall,
                    'max_grouping_residual_m3_per_year':float(np.max(np.abs(split_residual))),
                    'max_analytic_face_closure_residual_m3_per_year':float(np.max(np.abs(exact_total-continuum_rate))),
                    'case_wall_s_before_receipt':time.perf_counter()-t0,'case_cpu_user_s':u.ru_utime-u0.ru_utime,'case_cpu_system_s':u.ru_stime-u0.ru_stime,'process_cumulative_peak_rss_kib':u.ru_maxrss,
                    'initial_volume_m3':case.initial_volume,'final_volume_residual_m3':math.fsum(map(float,case.volumes))-case.initial_volume,
                    'cumulative_roundoff_bound_m3':case.cumulative_roundoff_bound,'arrays':catalog}
                put(folder/'RESULT.json',result);case_results.append(result)
                global_rows.append({k:result[k] for k in ['mode','width','height','L1_m','L2_m','Linf_m','maximum_error_cell_id','maximum_error_latitude_deg','maximum_error_longitude_deg','maximum_error_signed_m','half_dt_L2_difference_m','main_accepted_steps','main_kernel_wall_s_including_checks','half_kernel_wall_s_including_checks','case_cpu_user_s','case_cpu_system_s','process_cumulative_peak_rss_kib']})
                assert all(equal.values()), 'UNDOCUMENTED_Q1_GLOBAL_DEVIATION'
                print(f'{mode} {width}x{height}: Q1 exact, L2={norm["L2_m"]:.12g}',flush=True)
        table(out/'GLOBAL_METRICS.csv',global_rows);table(out/'LATITUDE_ERROR_BANDS.csv',bands)
        pins()
        u=resource.getrusage(resource.RUSAGE_SELF)
        result={'marker':'HR2_P1_D2=PASS_MEASURED_POLAR_ERROR_AND_FLUX_ATTRIBUTION',
            'cases':len(case_results),'arrays':sum(len(c['arrays']) for c in case_results),
            'all_Q1_global_scalars_exact':True,'wall_s_before_receipt':time.perf_counter()-started,
            'cpu_user_s':u.ru_utime-usage0.ru_utime,'cpu_system_s':u.ru_stime-usage0.ru_stime,'peak_rss_kib':u.ru_maxrss,
            'scope':'Diagnostic localization only; Q1 and D1 remain historically BLOCKED; no corrected convergence or scientific/production authority'}
        put(out/'SUMMARY.json',result)
        print(json.dumps(result),flush=True)
        return 0
    except Exception:
        put(out/'FAILURE.json',{'marker':'HR2_P1_D2=BLOCKED_DIAGNOSTIC_ASSERTION_OR_RUNTIME','traceback':traceback.format_exc(),'no_retry':True})
        traceback.print_exc()
        return 2


if __name__=='__main__':
    raise SystemExit(main())
