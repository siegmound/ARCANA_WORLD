"""Isolated measured complete assembly and full-step service, no long horizon."""
import argparse,json,time,resource,hashlib
from pathlib import Path
import numpy as np
from hr2_p1_explore.model import sphere
from .study import load_case,T
from .compact import CompactOperator
from .compensated import advance

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--assembly',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    if a.assembly:
        start=time.perf_counter();m=sphere(256,128);op=CompactOperator(m);before=resource.getrusage(resource.RUSAGE_SELF)
        hashes={k:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest() for k,x in [('data',op.G.data),('indices',op.G.indices),('indptr',op.G.indptr)]}
        with np.load(a.archive/'attempt04/256x128/operator.npz',allow_pickle=False) as z:expected={k:hashlib.sha256(np.ascontiguousarray(z[k]).tobytes()).hexdigest() for k in hashes}
        assert hashes==expected
        result={'assembly_s':op.assembly_s,'build_peak_rss_kib':before.ru_maxrss,'cpu_user_before_audit_s':before.ru_utime,
          'cpu_system_before_audit_s':before.ru_stime,'archived_CSR_bitwise_equal':True,'hashes':hashes,'full_service_wall_s_including_hash_audit':time.perf_counter()-start}
    else:
        op,src=load_case(a.archive,256)
        with np.load(src/'x.npz',allow_pickle=False) as z:V0=op.mesh.areas*z['initial_h']
        real_high=op.high;high_times=[]
        def wrapped(h):
            timer=time.perf_counter();out=real_high(h);high_times.append(time.perf_counter()-timer);return out
        op.high=wrapped;rows=[]
        for trial in range(3):
            for label in (['original','compensated'] if trial%2==0 else ['compensated','original']):
                high_times.clear();timer=time.perf_counter()
                if label=='original':V,d=op.advance(V0,T,minimum_steps=64)
                else:V,c,d=advance(op,V0,64)
                wall=time.perf_counter()-timer
                rows.append({'method':label,'trial':trial,'steps':64,'step_service_s':wall,'high_flux_G_s':sum(high_times),
                  'remaining_step_service_s':wall-sum(high_times),'limited_faces_total':d['limited_faces_total']})
        A=op.mesh.areas;C=np.bincount(op.mesh.first,weights=op.c,minlength=len(A))+np.bincount(op.mesh.second,weights=op.c,minlength=len(A));limits=.5*A/C
        result={'rows':rows,'cfl_year':op.cfl,'minimum_steps_for_T':int(np.ceil(T/op.cfl)),
          'minimum_steps_for_one_year_arithmetic_only':int(np.ceil(1/op.cfl)),
          'latitude_row_CFL_year':limits.reshape(128,256).min(axis=1).tolist(),
          'equatorial_vs_polar_CFL_ratio':float(limits.reshape(128,256)[64,0]/op.cfl),
          'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (a.output/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
