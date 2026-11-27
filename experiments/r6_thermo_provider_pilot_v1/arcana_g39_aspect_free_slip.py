#!/usr/bin/env python3
"""G39: synthetic free-slip spherical shell, native rotation gauges and pressure datum.
No ARCANA mantle state, new build, physical traction, or history advance.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import traceback
import arcana_g38_aspect_hollow_sphere as g38
import arcana_aspect_recovery_preflight as ar
import arcana_g25_fixed_load_decomposition as g25
import arcana_g32_corrected_global_operator as g32

PIN='7bccfd5b38d7e078315b94ba85aa72efc49aa91a41825ece88866241fe4c4f82'
STATUS='G38_ASPECT_HOLLOW_SPHERE_REFINEMENT_PASS__FREE_SLIP_AND_MANTLE_STATE_REQUIRED'
AUTH='G39_SYNTHETIC_FREE_SLIP_GAUGE_ONLY_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
CASES=(('hydro_2',2,False,'net rotation',0),
       ('hydro_3',3,False,'net rotation',0),
       ('forced_volume_3',3,True,'net rotation',0),
       ('forced_surface_3',3,True,'net surface rotation',0),
       ('forced_datum_3',3,True,'net rotation',10))
COLS={'rms':'RMS velocity (m/s)','max':'Max. velocity (m/s)',
      'pmin':'Minimal pressure (Pa)','pmean':'Average pressure (Pa)','pmax':'Maximal pressure (Pa)',
      'rotation':'Angular velocity (1/s)','surface_rotation':'Surface angular velocity (1/s)',
      'angular_momentum':'Angular momentum (kg*m^2/s)','dissipation':'Viscous dissipation (W)',
      'Ixx':'Moment of inertia_xx (kg*m^2)','Iyy':'Moment of inertia_yy (kg*m^2)',
      'Izz':'Moment of inertia_zz (kg*m^2)','Ixy':'Moment of inertia_xy (kg*m^2)',
      'Ixz':'Moment of inertia_xz (kg*m^2)','Iyz':'Moment of inertia_yz (kg*m^2)'}
FILES=('source/simulator/parameters.cc','source/simulator/nullspace.cc',
       'source/material_model/simple.cc','source/material_model/equation_of_state/linearized_incompressible.cc',
       'source/boundary_velocity/interface.cc','source/postprocess/rotation_statistics.cc',
       'source/postprocess/pressure_statistics.cc','source/postprocess/viscous_dissipation_statistics.cc',
       'source/postprocess/velocity_statistics.cc','source/geometry_model/spherical_shell.cc')
PRM="""set Dimension = 3
set Start time = 0
set End time = 0
set Use years instead of seconds = false
set Nonlinear solver scheme = no Advection, iterated Stokes
set Nonlinear solver tolerance = 1e-6
set Output directory = output
set Pressure normalization = surface
set Surface pressure = {datum}
subsection Geometry model
  set Model name = spherical shell
  subsection Spherical shell
    set Inner radius = 0.5
    set Outer radius = 1.0
    set Cells along circumference = 12
  end
end
subsection Boundary velocity model
  set Tangential velocity boundary indicators = bottom, top
end
subsection Nullspace removal
  set Remove nullspace = {gauge}
end
subsection Material model
  set Model name = simple
  subsection Simple model
    set Reference density = 1000
    set Reference temperature = 1000
    set Thermal expansion coefficient = 0.001
    set Viscosity = 1
    set Thermal viscosity exponent = 0
  end
end
subsection Gravity model
  set Model name = radial constant
  subsection Radial constant
    set Magnitude = 1
  end
end
subsection Initial temperature model
  set List of model names = function
  subsection Function
    set Coordinate system = cartesian
    set Function expression = {temperature}
  end
end
subsection Mesh refinement
  set Initial adaptive refinement = 0
  set Initial global refinement = {level}
end
subsection Postprocess
  set List of postprocessors = visualization, velocity statistics, pressure statistics, rotation statistics, viscous dissipation statistics
  subsection Rotation statistics
    set Use constant density of one = true
    set Output full moment of inertia tensor = true
  end
end
subsection Solver parameters
  subsection Stokes solver parameters
    set Linear solver tolerance = 1e-7
    set Number of cheap Stokes solver steps = 0
  end
end
"""
def make_prm(case):
    name,level,forced,gauge,datum=case
    need(case in CASES,'CASE_AUTHORITY')
    return PRM.format(level=level,gauge=gauge,datum=datum,
        temperature='1000+100*(x*y+0.3*z)' if forced else '1000')
def parse_stats(p):
    basic=g38.statistics(p)
    cols={}; rows=[]
    for line in p.read_text().splitlines():
        m=re.match(r'^#\s*(\d+):\s*(.+)$',line)
        if m: cols[m[2].strip()]=int(m[1])-1
        elif line.strip() and not line.startswith('#'): rows.append(line.split())
    need(len(rows)==1,'STATISTICS_ROWS')
    missing=[v for v in COLS.values() if v not in cols]
    need(not missing,'STATISTICS_MISSING:'+str(missing))
    d={k:float(rows[0][cols[v]]) for k,v in COLS.items()}
    need(all(math.isfinite(v) for v in d.values()),'NONFINITE_STATISTICS')
    need(all(d[k]>=0 for k in ('rms','max','rotation','surface_rotation','angular_momentum','dissipation'))
        and d['pmin']<=d['pmean']<=d['pmax'],'STATISTICS_DOMAIN')
    return {**basic,**d}
def native_sources(src):
    rows={}
    for name in FILES:
        p=src/name
        need(p.read_bytes()==subprocess.check_output(['git','-C',str(src),'show',ar.ASPECT_SHA+':'+name]),'SOURCE_DRIFT:'+name)
        rows[name]=sha(p)
    return rows
def run_case(out,case,state,root):
    name,level,forced,gauge,datum=case
    work=out/name; work.mkdir()
    prm=work/'input.prm'; prm.write_text(make_prm(case))
    cmd=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev',
         '-b',str(work)+':/tmp','-w','/tmp','/home/dealii/aspect/bin/aspect-release','input.prm']
    env=dict(os.environ,HOME='/home/dealii',USER='dealii',PATH='/usr/bin:/bin',
        OMPI_MCA_btl='^vader',HWLOC_HIDE_ERRORS='2',OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',TMPDIR='/tmp',PYTHONDONTWRITEBYTECODE='1')
    write(work/'COMMAND.json',{'argv':cmd,'input_sha256':sha(prm),'timeout_s':600,
        'rank_policy':'singleton MPI','address_space_limit_bytes_per_process':8*1024**3,
        'file_size_limit_bytes':1024**3,'environment_overrides':{k:env[k] for k in
        ('HOME','USER','PATH','OMPI_MCA_btl','HWLOC_HIDE_ERRORS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','TMPDIR')}})
    with (work/'STDOUT.txt').open('x') as stdout,(work/'STDERR.txt').open('x') as stderr:
        proc=subprocess.Popen(['/usr/bin/time','-v','-o',str(work/'TIME.txt'),*cmd],
            cwd=work,env=env,stdout=stdout,stderr=stderr,start_new_session=True,preexec_fn=g38.limits)
        try: rc=proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL); proc.wait(); rc=124
    (work/'EXIT_CODE.txt').write_text(str(rc)+'\n')
    need(rc==0,'NATIVE_EXIT:'+name+':'+str(rc))
    text=(work/'STDOUT.txt').read_text()
    need(all(x in text for x in ('OPTIMIZED','3.2.0-pre','30eb77ee5','running with 1 MPI process')),'RUNTIME_IDENTITY')
    need(prm.read_text()==make_prm(case),'INPUT_MUTATION')
    residuals=re.findall(r'Relative nonlinear residual \(Stokes system\) after nonlinear iteration \d+:\s*([0-9.eE+-]+)',text)
    d=parse_stats(work/'output/statistics')
    # A truly zero initial residual may be reported without an iteration;
    # retain the observed marker count rather than inventing a residual.
    residual=float(residuals[-1]) if residuals else None
    need(d['cells']==12*8**level,'CELL_COUNT')
    report={'name':name,'level':level,'forced':forced,'gauge':gauge,'datum_Pa':datum,
        'native_exit':rc,'last_nonlinear_residual':residual,'residual_markers':len(residuals),**d}
    write(work/'CASE_REPORT.json',report)
    print('G39_CASE',json.dumps(report,allow_nan=False),flush=True)
    return report
def evaluate(rows):
    import numpy as np
    h2,h3,v,s,p=rows
    # Hydrostatic p=1000*(1-r); mean over a shell with uniform volume measure.
    mean=1000*(1-.75*(1-.5**4)/(1-.5**3))
    I=8*math.pi/15*(1-.5**5)  # constant unit density, each diagonal
    checks={}
    for d in rows:
        tag=d['name']
        checks[tag+'_inertia']=max(abs(d[k]-I)/I for k in ('Ixx','Iyy','Izz'))<1e-3 and max(abs(d[k])/I for k in ('Ixy','Ixz','Iyz'))<1e-3
        target=d['surface_rotation'] if d['gauge']=='net surface rotation' else d['rotation']
        checks[tag+'_selected_gauge']=target<1e-9*max(1.,d['rms'])
        checks[tag+'_nonlinear_residual']=d['last_nonlinear_residual'] is not None and 0<=d['last_nonlinear_residual']<=1e-6
    hydro_errors=[abs(d['pmean']-mean)/mean for d in (h2,h3)]
    checks['hydrostatic_mean']=max(hydro_errors)<1e-2
    checks['hydrostatic_velocity_small']=v['rms']>0 and h3['rms']<.05*v['rms']
    checks['hydrostatic_dissipation_small']=v['dissipation']>0 and h3['dissipation']<.01*v['dissipation']
    checks['nonzero_forced_flow']=min(d['rms'] for d in (v,s,p))>1e-6 and min(d['dissipation'] for d in (v,s,p))>1e-8
    def relative(a,b): return abs(a-b)/max(abs(a),abs(b),1e-300)
    gauge_diss=relative(v['dissipation'],s['dissipation'])
    gauge_pressure=max(abs(v[k]-s[k])/max(abs(v[k]),abs(s[k]),1.) for k in ('pmin','pmean','pmax'))
    datum_velocity=relative(v['rms'],p['rms'])
    datum_diss=relative(v['dissipation'],p['dissipation'])
    datum_error=max(abs(p[k]-v[k]-10.) for k in ('pmin','pmean','pmax'))
    checks['gauge_dissipation_invariance']=gauge_diss<1e-4
    checks['gauge_pressure_invariance']=gauge_pressure<1e-4
    checks['datum_velocity_invariance']=datum_velocity<1e-4
    checks['datum_dissipation_invariance']=datum_diss<1e-4
    checks['datum_pressure_shift']=datum_error<1e-2
    return {'checks':checks,'screen_pass':all(checks.values()),
        'hydrostatic_mean_analytic_Pa':mean,'hydrostatic_mean_relative_errors':hydro_errors,
        'hydrostatic_rms_m_s':[h2['rms'],h3['rms']],
        'unit_density_inertia_diagonal_analytic':I,'gauge_dissipation_relative':gauge_diss,
        'gauge_pressure_relative':gauge_pressure,'datum_velocity_relative':datum_velocity,
        'datum_dissipation_relative':datum_diss,'datum_shift_max_error_Pa':datum_error,
        'analytic_body_torque':'zero pointwise because radial gravity; not independently integrated from native fields',
        'nullspace_rank_proven':False,'independent_boundary_work_qualified':False}
def main():
    ap=argparse.ArgumentParser()
    for k in ('base','recovery','inventory','g37b','g38','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-synthetic-free-slip-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    base,rec,inv,b,p,out=(x.resolve() for x in (a.base,a.recovery,a.inventory,a.g37b,a.g38,a.output))
    source=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def source_check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'FROZEN_SOURCE')
    def parents(): return [g38.verified_bundle(rec,g38.PREC),g38.verified_bundle(inv,g38.PINV),
        g32.verify(b,g38.P37B,g38.S37B),g32.verify(p,PIN,STATUS)]
    source_check(); before=parents()
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in
        (source,rec,inv,b,p,base/'ARCANA_ASPECT_TOOLS')),'OUTPUT')
    out.mkdir()
    report={'source_sha':g25.SOURCE,'ASPECT_source_sha':ar.ASPECT_SHA,'G38_manifest_sha256':PIN,
        'installations':0,'builds':0,'synthetic_solves_attempted':0,'ARCANA_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'physical_acceptance':False,
        'global_solve_authorized':False,'mantle_provider_qualified':False,**g25.SCOPE}
    snapshot=None
    try:
        state,container,root,src,hs,prm,lib,identity=g38.inputs(base,rec,inv)
        snapshot=ar.tree_metadata(container)
        files=native_sources(src)
        write(out/'NATIVE_SOURCE_IDENTITY.json',files)
        report['cases']=[]
        for case in CASES:
            report['synthetic_solves_attempted']+=1
            report['cases'].append(run_case(out,case,state,root))
        report['audit']=evaluate(report['cases'])
        need(report['audit']['screen_pass'],'FREE_SLIP_GAUGE_SCREEN')
        report.update(screen_pass=True,status='G39_ASPECT_FREE_SLIP_GAUGE_SCREEN_PASS__NATIVE_TRACTION_AND_STATE_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G39_ASPECT_FREE_SLIP_GAUGE_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        source_check(); need(parents()==before,'PARENT_MUTATION')
        if snapshot is not None:
            need(ar.tree_metadata(container)==snapshot,'CONTAINER_METADATA_DRIFT')
            g38.inputs(base,rec,inv); need(native_sources(src)==files,'NATIVE_SOURCE_MUTATION')
        report['source_and_parents_unchanged']=True
    except Exception as e:
        report.update(screen_pass=False,status='G39_ASPECT_FREE_SLIP_GAUGE_BLOCKED',postcheck_error=repr(e))
    report['limitations']=['Synthetic simple incompressible material, not ARCANA mantle.',
        'Gauge checks use ASPECT native quadrature, not independent FE integration or rank proof.',
        'No applied tangential traction, normal reaction admission or physical interface work closure.',
        'Pressure shift test is numerical datum invariance, not absolute EOS pressure authority.']
    write(out/'REPORT.json',report)
    write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G39_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
