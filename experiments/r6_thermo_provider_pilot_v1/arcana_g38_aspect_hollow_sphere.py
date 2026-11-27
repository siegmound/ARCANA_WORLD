#!/usr/bin/env python3
"""G38: existing ASPECT HollowSphere analytic 3D Stokes refinement pair.
Synthetic, t=0, prescribed analytic velocities, not free-slip or ARCANA mantle.
Use only previously inventoried release plugin and executable. No installation/build.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import traceback
import math
import arcana_g25_fixed_load_decomposition as g25
import arcana_g32_corrected_global_operator as g32
import arcana_aspect_recovery_preflight as ar

AUTH='G38_SYNTHETIC_HOLLOW_SPHERE_RANK1_ONLY_V1'
P37B='20687dfd1bc63cf497e3feeec983fda77890cf16b696015da1817200203c88bf'
S37B='G37B_NORMAL_GEOMETRY_TRANSFER_PASS__PHYSICAL_REACTION_AND_REAL_MESH_AUTHORITY_REQUIRED'
PREC='2157bac10d69c9faba1f79a922fc2cc3ad05bef47acffad0ac18ab95e059678d'
PINV='d736c02b5115fb6ad0799245d27b894b298dd3b03d5774898eb669b3716e41fd'
LEVELS=(2,3)
LABELS=('u_L1','p_L1','u_L2','p_L2','topo_L2')
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
PATTERN=r'Errors u_L1, p_L1, u_L2, p_L2 topo_L2:\s*([^\r\n]+)'

def verified_bundle(p,pin):
    m=read(p/'MANIFEST.json')
    need(sha(p/'MANIFEST.json')==pin and inventory(p)==m['files'],'BUNDLE:'+p.name)
    return m

def inputs(base,rec,inv):
    tools=base/'ARCANA_ASPECT_TOOLS'; state=tools/'udocker-state'
    container=(state/'containers/arcana-aspect-v310').resolve()
    root=container/'ROOT'; src=root/'home/dealii/aspect'
    hs=src/'benchmarks/hollow_sphere'
    identity=read(rec/'IDENTITY.json')
    need(read(rec/'REPORT.json')['screen_pass'] and identity['source_sha']==ar.ASPECT_SHA,'RUNTIME_SCOPE')
    for p,pin in identity['sha256'].items(): need(sha(Path(p))==pin,'RUNTIME_DRIFT:'+p)
    need(subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()==ar.ASPECT_SHA,'ASPECT_SHA')
    h=read(inv/'HOLLOW_SPHERE_SOURCE_INVENTORY.json')
    need(h['source_commit']==ar.ASPECT_SHA and h['proposed_not_executed'],'BENCHMARK_SCOPE')
    actual={str(p.relative_to(hs)):sha(p) for p in sorted(hs.rglob('*')) if p.is_file()}
    need(actual==h['files'],'BENCHMARK_INVENTORY_DRIFT')
    prm=hs/'hollow_sphere.prm'; cc=hs/'hollow_sphere.cc'
    for p in (prm,cc,hs/'CMakeLists.txt'):
        blob=subprocess.check_output(['git','-C',str(src),'show',ar.ASPECT_SHA+':'+str(p.relative_to(src))])
        need(p.read_bytes()==blob,'UPSTREAM_SOURCE_DRIFT:'+p.name)
    libs=sorted(hs.rglob('libhollow_sphere.release.so'))
    need(libs and len({sha(p) for p in libs})==1,'RELEASE_PLUGIN_UNRESOLVED')
    lib=libs[0]
    need(str(lib.relative_to(hs)) in actual,'PLUGIN_INVENTORY')
    txt=prm.read_text()
    for key,val in {'Dimension':'3','Start time':'0','End time':'0','Use years instead of seconds':'false',
        'Additional shared libraries':'./libhollow_sphere.so','Output directory':'output',
        'Pressure normalization':'surface','Inner radius':'0.5','Outer radius':'1.0',
        'Viscosity parameter':'3','Initial global refinement':'4','Initial adaptive refinement':'0',
        'Linear solver tolerance':'1e-6','Nonlinear solver scheme':'no Advection, iterated Stokes'}.items():
        need(re.findall(r'(?m)^\s*set\s+'+re.escape(key)+r'\s*=\s*([^\r\n]+)',txt)==[val],'PRM_CONTRACT:'+key)
    need('bottom : HollowSphereBoundary' in txt and 'top : HollowSphereBoundary' in txt
         and 'HollowSpherePostprocessor' in txt and 'dynamic topography' in txt,'BOUNDARIES_POSTPROCESS')
    need('Errors u_L1, p_L1, u_L2, p_L2 topo_L2:' in cc.read_text(),'POSTPROCESSOR_IDENTITY')
    return state,container,root,src,hs,prm,lib,identity

def candidate(txt,level):
    need(level in LEVELS,'LEVEL')
    pattern=r'(?m)^(\s*set\s+Initial global refinement\s*=\s*)4(\s*)$'
    new,n=re.subn(pattern,lambda m:m[1]+str(level)+m[2],txt)
    need(n==1,'REFINEMENT_PATCH')
    back,n=re.subn(r'(?m)^(\s*set\s+Initial global refinement\s*=\s*)'+str(level)+r'(\s*)$',
        lambda m:m[1]+'4'+m[2],new)
    need(n==1 and back==txt,'PATCH_SCOPE')
    return new

def errors(text):
    rows=re.findall(PATTERN,text)
    need(len(rows)==1,'NATIVE_ERROR_ROW_COUNT:'+str(len(rows)))
    vals=[float(v.strip()) for v in rows[0].split(',')]
    need(len(vals)==5 and all(math.isfinite(v) and v>0 for v in vals),'NATIVE_ERROR_VALUES')
    return dict(zip(LABELS,vals))

def statistics(path):
    cols={}; rows=[]
    for line in path.read_text().splitlines():
        m=re.match(r'^#\s*(\d+):\s*(.+)$',line)
        if m: cols[m[2].strip()]=int(m[1])-1
        elif line.strip() and not line.startswith('#'): rows.append(line.split())
    step=[v for k,v in cols.items() if k.lower()=='time step number']
    time=[v for k,v in cols.items() if re.match(r'^time \((seconds|s)\)$',k,re.I)]
    cells=[v for k,v in cols.items() if k.lower()=='number of mesh cells']
    need(len(step)==len(time)==len(cells)==1 and len(rows)==1,'STATISTICS_SCHEMA_OR_STEPS')
    row=rows[0]
    need(float(row[step[0]])==0 and float(row[time[0]])==0,'ZERO_TIME')
    nc=int(row[cells[0]]); need(nc>0,'CELL_COUNT')
    return {'cells':nc,'step':0,'time_s':0.}

def limits():
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024**3,1024**3))

def run_case(out,level,prm,lib,state,root):
    case=out/('level_'+str(level)); case.mkdir()
    (case/'input.prm').write_text(candidate(prm.read_text(),level))
    shutil.copyfile(lib,case/lib.name)
    need(sha(case/lib.name)==sha(lib),'PLUGIN_COPY')
    # Same native rank-1 executable, isolated cwd and all output in bound /tmp.
    # Singleton MPI initialization, not a host MPI invocation.
    cmd=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev',
         '-b',str(case)+':/tmp','-w','/tmp',
         '/home/dealii/aspect/bin/aspect-release','input.prm']
    env=dict(os.environ,HOME='/home/dealii',USER='dealii',PATH='/usr/bin:/bin',
        OMPI_MCA_btl='^vader',HWLOC_HIDE_ERRORS='2',OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',TMPDIR='/tmp',
        PYTHONDONTWRITEBYTECODE='1')
    write(case/'COMMAND.json',{'argv':cmd,'input_sha256':sha(case/'input.prm'),
        'plugin_sha256':sha(case/lib.name),'rank_policy':'singleton MPI','timeout_s':600,
        'address_space_limit_bytes_per_process':8*1024**3,'file_size_limit_bytes':1024**3,
        'environment_overrides':{k:env[k] for k in ('HOME','USER','PATH','OMPI_MCA_btl','HWLOC_HIDE_ERRORS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','TMPDIR')}})
    with (case/'STDOUT.txt').open('x') as stdout,(case/'STDERR.txt').open('x') as stderr:
        proc=subprocess.Popen(['/usr/bin/time','-v','-o',str(case/'TIME.txt'),*cmd],
            env=env,stdout=stdout,stderr=stderr,cwd=case,start_new_session=True,preexec_fn=limits)
        try: rc=proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL); proc.wait(); rc=124
    (case/'EXIT_CODE.txt').write_text(str(rc)+'\n')
    text=(case/'STDOUT.txt').read_text()
    need(rc==0,'NATIVE_EXIT:'+str(rc))
    need('OPTIMIZED' in text and '3.2.0-pre' in text and '30eb77ee5' in text,'NATIVE_VERSION')
    need(re.search(r'(?:\b1\s+MPI\s+process(?:es)?\b|Number of MPI processes\s*:\s*1\b)',text,re.I),'RANK_COUNT')
    need(sha(case/lib.name)==sha(lib) and (case/'input.prm').read_text()==candidate(prm.read_text(),level),'INPUT_MUTATION')
    data=statistics(case/'output/statistics')
    need(data['cells']==12*8**level,'UNIFORM_REFINEMENT_CELL_COUNT')
    report={'level':level,'native_exit':rc,'errors':errors(text),**data}
    write(case/'CASE_REPORT.json',report)
    print('G38_CASE',json.dumps(report),flush=True)
    return report

def selftest():
    txt='set Initial global refinement = 4\nset End time = 0\n'
    need(candidate(txt,2)=='set Initial global refinement = 2\nset End time = 0\n','SELFTEST_PATCH')
    need(errors('Errors u_L1, p_L1, u_L2, p_L2 topo_L2: 1e-3, 2e-3, 3e-3, 4e-3, 5e-3\n')['topo_L2']==.005,'SELFTEST_PARSE')
    for bad in ('', 'Errors u_L1, p_L1, u_L2, p_L2 topo_L2: nan, 1, 1, 1, 1'):
        try: errors(bad)
        except RuntimeError: pass
        else: raise RuntimeError('BAD_ERROR_ROW_ACCEPTED')
    return True

def main():
    ap=argparse.ArgumentParser()
    for k in ('base','recovery','inventory','g37b','output'): ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-synthetic-hollow-sphere-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    base,rec,inv,g37b,out=(x.resolve() for x in (a.base,a.recovery,a.inventory,a.g37b,a.output))
    source=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def source_check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and
            not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'FROZEN_SOURCE')
    def parents(): return [verified_bundle(rec,PREC),verified_bundle(inv,PINV),g32.verify(g37b,P37B,S37B)]
    source_check(); before=parents()
    need(not out.exists() and not any(out.is_relative_to(p) or p.is_relative_to(out)
        for p in (source,rec,inv,g37b,base/'ARCANA_ASPECT_TOOLS')),'OUTPUT')
    out.mkdir()
    report={'source_sha':g25.SOURCE,'ASPECT_source_sha':ar.ASPECT_SHA,'G37B_manifest_sha256':P37B,
        'runtime_recovery_manifest_sha256':PREC,'provider_inventory_manifest_sha256':PINV,
        'installations':0,'builds':0,'synthetic_solves_attempted':0,'ARCANA_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'physical_acceptance':False,
        'global_solve_authorized':False,'mantle_provider_qualified':False,'free_slip_qualified':False,**g25.SCOPE}
    snapshot=None
    try:
        need(selftest(),'SELFTEST')
        state,container,root,src,hs,prm,lib,identity=inputs(base,rec,inv)
        snapshot=ar.tree_metadata(container)
        write(out/'UPSTREAM_IDENTITY.json',{'prm_sha256':sha(prm),'plugin_path':str(lib),
            'plugin_sha256':sha(lib),'source_cc_sha256':sha(hs/'hollow_sphere.cc'),
            'release_exe_sha256':sha(src/'bin/aspect-release'),'upstream_refinement':4,
            'modified_diagnostic_levels':list(LEVELS),'only_prm_change':'Initial global refinement'})
        shutil.copyfile(prm,out/'UPSTREAM_UNMODIFIED.prm')
        report['cases']=[]
        for level in LEVELS:
            report['synthetic_solves_attempted']+=1
            report['cases'].append(run_case(out,level,prm,lib,state,root))
        x,y=report['cases']
        ratios={k:y['errors'][k]/x['errors'][k] for k in LABELS}
        report['fine_to_coarse_error_ratio']=ratios
        report['observed_pair_order']={k:-math.log2(v) for k,v in ratios.items()}
        need(y['cells']==8*x['cells'] and all(0<v<1 for v in ratios.values()),'REFINEMENT_SCREEN')
        report.update(screen_pass=True,status='G38_ASPECT_HOLLOW_SPHERE_REFINEMENT_PASS__FREE_SLIP_AND_MANTLE_STATE_REQUIRED')
    except Exception as e:
        report.update(screen_pass=False,status='G38_ASPECT_HOLLOW_SPHERE_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        need(parents()==before,'PARENT_MUTATION'); source_check()
        if snapshot is not None:
            need(ar.tree_metadata(container)==snapshot,'CONTAINER_METADATA_DRIFT')
            inputs(base,rec,inv)
            report['historical_container_targeted_bytes_and_metadata_unchanged']=True
        report['source_and_parents_unchanged']=True
    except Exception as e:
        report.update(screen_pass=False,status='G38_ASPECT_HOLLOW_SPHERE_BLOCKED',postcheck_error=repr(e))
    report['limitations']=['Synthetic analytic Dirichlet velocity on both boundaries, not free-slip.',
        'Two modified mesh levels measure a refinement trend, not formal asymptotic convergence.',
        'Native velocity/pressure/topography errors only; independent boundary traction and work integrals pending.',
        'Targeted container content and metadata checked, not full container content rehash.']
    write(out/'REPORT.json',report)
    write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G38_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
