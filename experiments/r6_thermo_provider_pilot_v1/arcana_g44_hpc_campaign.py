#!/usr/bin/env python3
"""Synthetic FAIR HPC campaign, architecture A; no ARCANA physical evolution."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback
import arcana_g25_fixed_load_decomposition as g25
import arcana_g32_corrected_global_operator as g32
import arcana_g38_aspect_hollow_sphere as g38
import arcana_g44_hpc_mpi_preflight as g44
import arcana_g44r2_tcp_mpi_recovery as r2
import arcana_aspect_recovery_preflight as ar

BASE=Path('/home/jlpfritas/HPC-POMDP/Arcana')
EV=BASE/'ARCANA_WORLD_EVIDENCE/R6'
ROOT=EV/'R6_G44_HPC_FULL_MANTLE_20261128_NEW01'
SOURCE=BASE/'ARCANA_WORLD_R6_C11A_VERIFY.a7voPe'
PINNED=(('R6_ASPECT_RUNTIME_RECOVERY_NEW01',g38.PREC),('R6_G36R2_HANDOFF_AND_PROVIDER_INVENTORY_NEW02',g38.PINV),
 ('R6_G38_ASPECT_HOLLOW_SPHERE_NEW01',g44.P38),('R6_G43_T0_MANTLE_HANDOFF_NEW01',g44.PIN),
 ('R6_G44_HPC_MPI_PREFLIGHT_NEW01',r2.FAILED_PIN),('R6_G44R1_MPI_TRANSPORT_RECOVERY_NEW01',r2.R1_PIN))
SCOPE={'architecture':'A_FULL_MANTLE_ADAPTIVE','physical_T1':None,'D_024':'ACTIVE','D_025':'ACTIVE',
 'scientific_promotion':False,'physical_acceptance':False,'mantle_initial_state_admitted':False,
 'mantle_provider_qualified':False,'global_solve_authorized':False,'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
 'material_assignments':0,'ARCANA_solves':0,'additional_time_advance_years':0}
sha,read,write,need=g25.sha,g25.read,g25.write,g25.need

def source_check():
    need(subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()==g25.SOURCE,'FROZEN_SHA')
    need(not subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip(),'FROZEN_DIRTY')

def runtime():return g38.inputs(BASE,EV/PINNED[0][0],EV/PINNED[1][0])

def prepare():
    source_check();parents=[]
    for folder,pin in PINNED:
        p=EV/folder;m=g38.verified_bundle(p,pin)
        parents.append({'directory':folder,'manifest_sha256':pin,'status':m.get('status'),'members':len(m['files'])})
    write(ROOT/'PARENT_PREFLIGHT.json',{'parents':parents,**SCOPE})
    h=g44.host();h['numa_nodes']={str(i):{'cpulist':(Path('/sys/devices/system/node')/f'node{i}/cpulist').read_text().strip(),
       'meminfo':(Path('/sys/devices/system/node')/f'node{i}/meminfo').read_text()} for i in range(4)}
    h['loadavg']=Path('/proc/loadavg').read_text();h['meminfo']=Path('/proc/meminfo').read_text()
    write(ROOT/'HARDWARE_BEFORE.json',h)
    state,container,root,src,hs,prm,lib,identity=runtime()
    write(ROOT/'CONTAINER_METADATA_BEFORE.json',ar.tree_metadata(container))
    write(ROOT/'RUNTIME_IDENTITY.json',{'aspect':str(src/'bin/aspect-release'),'aspect_sha256':sha(src/'bin/aspect-release'),
           'plugin':str(lib),'plugin_sha256':sha(lib),'prm_sha256':sha(prm),'upstream_commit':ar.ASPECT_SHA})
    # Cleanup authorization is an exact historical tag from a pinned command.
    p1=EV/PINNED[-1][0];case=p1/'probe_legacy_btl_2';tag=sha(case/'JOB_ID.txt')
    cmd=read(case/'RUN_COMMAND.json')
    need(cmd['tag']==tag and (case/'JOB_ID.txt').read_text()==str(case.resolve())+'\n','LEGACY_TOKEN')
    birth=int(subprocess.check_output(['stat','-c','%W',str(case/'JOB_ID.txt')],text=True).strip())
    boot=int(re.search(r'^btime (\d+)$',Path('/proc/stat').read_text(),re.M)[1])
    need(birth>boot,'TAG_BIRTH_UNKNOWN')
    floor=max(0,(birth-boot-2)*os.sysconf('SC_CLK_TCK'))
    sup=Path(__file__).with_name('arcana_hpc_supervisor.py')
    done=subprocess.run(['/usr/bin/python3',str(sup),'--cleanup-tag',tag,'--key','ARCANA_G44R1_JOB',
          '--not-before-ticks',str(floor),'--output',str(ROOT/'LEGACY_CLEANUP.json')],capture_output=True,text=True)
    (ROOT/'LEGACY_CLEANUP.stdout').write_text(done.stdout);(ROOT/'LEGACY_CLEANUP.stderr').write_text(done.stderr)
    need(done.returncode==0,'LEGACY_CLEANUP_FAILED')
    write(ROOT/'LEGACY_CLEANUP_AUTHORITY.json',{'tag':tag,'job_file_birth_epoch':birth,'not_before_ticks':floor,
       'exclusion_reason':'Processes started before manifest-bound JOB_ID creation cannot inherit its initial-environment token.',
       'R2_output_exists':(EV/'R6_G44R2_TCP_MPI_RECOVERY_NEW01').exists(),**SCOPE})
    build=p1/'probe_build';ident=read(build/'IDENTITY.json')
    need(sha(build/'mpi_probe')==ident['binary_sha256'] and sha(build/'mpi_probe.c')==ident['source_sha256'],'PROBE_PIN')
    write(ROOT/'RETAINED_PROBE_IDENTITY.json',ident)
    print('PREFLIGHT_AND_LEGACY_CLEANUP_PASS',flush=True)

def cpus(n,layout):
    h=read(ROOT/'HARDWARE_BEFORE.json');groups={}
    for row in h['topology']:
        groups.setdefault((row['socket'],row['core']),[]).append(row['cpu'])
    physical=[min(v) for _,v in sorted(groups.items())]
    if layout=='spread':
        nodes={i:[] for i in range(4)}
        for cpu in physical:
            i=next(i for i in range(4) if cpu in r2.cpuset(h['numa_nodes'][str(i)]['cpulist']))
            nodes[i].append(cpu)
        physical=[v for tup in zip(*nodes.values()) for v in tup]
    logical=physical+[max(groups[(row['socket'],row['core'])]) for cpu in physical for row in h['topology'] if row['cpu']==cpu]
    need(n<=len(logical) and (n<=64 or n==128),'CPU_COUNT')
    return (physical if n<=64 else logical)[:n]

def candidate(text,level,visualization=True):
    need(level in (2,3,4,5,6),'LEVEL_NOT_AUTHORIZED')
    text,count=re.subn(r'(?m)^(\s*set Initial global refinement\s*=\s*)4\s*$',lambda m:m[1]+str(level),text)
    need(count==1,'REFINEMENT_PATCH')
    # Default retains all upstream postprocessors. A no-visualization variant is
    # separate if later needed; analytic error/topography postprocessors stay on.
    if not visualization:text=text.replace('visualization, velocity statistics','velocity statistics')
    return text

def numeric_or_text(value):
    try:return float(value)
    except ValueError:return value

def parse_case(case,n,level,selected,expected_cpus,baseline):
    s=(case/'STDOUT.txt').read_text();exit=read(case/'RUN_EXIT.json')
    need(exit['exit_code']==0 and not exit['remaining'],'NATIVE_EXIT_OR_LEFTOVERS')
    need('OPTIMIZED' in s and '3.2.0-pre' in s and '30eb77ee5' in s,'ASPECT_IDENTITY')
    need(re.search(r'\brunning with '+str(n)+r' MPI process(?:es)?\b',s,re.I),'ACTUAL_MPI_RANKS')
    marks=re.findall(r'HPC_RANK=(\d+) CPU=([0-9,-]+)',s)
    need(sorted(int(a) for a,b in marks)==list(range(n)),'RANK_MARKERS')
    need(all(r2.cpuset(b)=={expected_cpus[int(a)]} for a,b in marks),'PINNING')
    stats=g38.statistics(case/'output/statistics');need(stats['cells']==12*8**level,'CELL_PARITY')
    errors=g38.errors(s)
    delta={k:abs(errors[k]/baseline['errors'][k]-1) for k in g38.LABELS} if baseline else None
    need(delta is None or all(v<1e-4 for v in delta.values()),'NUMERICAL_PARITY')
    timings={}
    for line in s.splitlines():
        m=re.match(r'\|\s*([^|]+?)\s*\|\s*\d+\s*\|\s*([0-9.e+-]+)(ms|s|h)\s*\|',line)
        if m:timings[m[1].strip()]=float(m[2])*{'ms':.001,'s':1.,'h':3600.}[m[3]]
    total=re.search(r'Total wallclock time elapsed since start\s*\|\s*([\d.e+-]+)(ms|s|h)',s)
    dofs=re.search(r'Number of degrees of freedom:\s*([\d,]+)\s*\(([^)]+)\)',s)
    need(total and dofs,'TIMING_DOF_SCHEMA')
    stattext=(case/'output/statistics').read_text();cols={int(i)-1:k for i,k in re.findall(r'^#\s*(\d+):\s*(.+)$',stattext,re.M)}
    statrow=[l.split() for l in stattext.splitlines() if l and not l.startswith('#')][-1]
    return {**stats,'errors':errors,'relative_to_baseline':delta,'rank_affinity':marks,
       'total_dofs':int(dofs[1].replace(',','')),'dof_components':[int(x.replace(',','')) for x in dofs[2].split('+')],
       'aspect_wall_s':float(total[1])*{'ms':.001,'s':1.,'h':3600.}[total[2]],'section_times_s':timings,
       'stokes_iterations':re.findall(r'Solving Stokes system \(GMG\)\.\.\.\s*([^\n]+)',s),
       'nonlinear_residuals':[float(x) for x in re.findall(r'after nonlinear iteration \d+:\s*([\d.e+-]+)',s)],
       'statistics':{k:numeric_or_text(statrow[i]) for i,k in cols.items()},'screen_pass':True}

def execute(name,n,level,profile='tcp',layout='spread',probe=False,baseline=None,timeout=240,visualization=True,backend='proot'):
    source_check();case=ROOT/name;case.mkdir();(case/'output').mkdir()
    state,container,root,src,hs,prm,lib,identity=runtime()
    selected=cpus(n,layout);(case/'cpus.txt').write_text('\n'.join(map(str,selected))+'\n')
    wrapper='''#!/bin/bash
set -eu
mapfile -t CPUS < /tmp/cpus.txt
/usr/bin/taskset -pc "${CPUS[$OMPI_COMM_WORLD_RANK]}" $$ >/dev/null
printf 'HPC_RANK=%s CPU=%s\\n' "$OMPI_COMM_WORLD_RANK" "$(grep Cpus_allowed_list /proc/self/status | cut -f2)"
exec "$@"
'''
    if backend=='native':
        private=ROOT/'native_candidate2'
        need(read(private/'ENV_PROBE.json')['rc']==0,'NATIVE_VERSION_UNQUALIFIED')
        wrapper=wrapper.replace('/tmp/cpus.txt',str(case/'cpus.txt')).replace('/usr/bin/taskset',str(private/'bin/taskset'))
    (case/'rank.sh').write_text(wrapper)
    if probe:
        binary=EV/PINNED[-1][0]/'probe_build/mpi_probe';shutil.copy2(binary,case/'mpi_probe');need(os.access(case/'mpi_probe',os.X_OK) and sha(case/'mpi_probe')==sha(binary),'PROBE_EXECUTABLE_IDENTITY');exe=['/tmp/mpi_probe',str(n)]
    else:
        (case/'input.prm').write_text(candidate(prm.read_text(),level,visualization));shutil.copyfile(lib,case/lib.name)
        exe=['/home/dealii/aspect/bin/aspect-release','input.prm']
    env={'HOME':'/home/dealii','USER':'dealii','PATH':'/usr/bin:/bin','TMPDIR':'/tmp','HWLOC_HIDE_ERRORS':'2',
        'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1',
        'OMPI_MCA_pml':'ob1','OMPI_MCA_btl':'self,tcp' if profile=='tcp' else 'self,vader'}
    if profile=='tcp':env.update(OMPI_MCA_btl_tcp_if_include='lo',OMPI_MCA_oob_tcp_if_include='lo')
    else:env['OMPI_MCA_btl_vader_single_copy_mechanism']='none'
    argv=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev',
          '-b',str(case)+':/tmp','-w','/tmp','/usr/bin/mpirun','-np',str(n),
          '--nooversubscribe','--bind-to','none','--map-by','slot']
    if n==128:argv+=['--use-hwthread-cpus']
    argv+=['/bin/bash','/tmp/rank.sh',*exe]
    if backend=='native':
        need(not probe,'NATIVE_PROBE_NEEDS_SEPARATE_ELF_IDENTITY')
        (case/'tmp').mkdir()
        env.update(OPAL_PREFIX=str(private),
            OMPI_MCA_mca_base_component_path=str(root/'usr/lib/x86_64-linux-gnu/openmpi/lib/openmpi3'),
            PATH=str(private/'bin')+':/usr/bin:/bin',TMPDIR=str(case/'tmp'))
        argv=['/usr/bin/env','LD_LIBRARY_PATH='+str(private/'lib'),str(private/'bin/orterun'),
             '-np',str(n),'--nooversubscribe','--bind-to','none','--map-by','slot']
        if n==128:argv+=['--use-hwthread-cpus']
        argv+=[str(private/'bin/bash'),str(case/'rank.sh'),str(private/'bin/aspect-release'),'input.prm']
    tag=hashlib.sha256(str(case).encode()).hexdigest()
    config={'case':str(case),'tag':tag,'argv':argv,'environment':env,'timeout_s':timeout,
       'aggregate_pss_abort_bytes':80*1024**3,'host_available_floor_bytes':max(64*1024**3,int(read(ROOT/'HARDWARE_BEFORE.json')['memavailable_bytes']*.25)),
       'sample_interval_s':.25}
    write(case/'config.json',config)
    (case/'HOST_BEFORE.txt').write_text(Path('/proc/loadavg').read_text()+Path('/proc/meminfo').read_text())
    print('START',name,'ranks',n,'level',level,flush=True)
    with (case/'SUPERVISOR.stdout').open('x') as so,(case/'SUPERVISOR.stderr').open('x') as se:
        run=subprocess.run(['/usr/bin/python3',str(Path(__file__).with_name('arcana_hpc_supervisor.py')),'--run',str(case/'config.json')],stdout=so,stderr=se)
    row={'name':name,'ranks':n,'level':level,'transport':profile,'layout':layout,'visualization':visualization,'probe':probe,'backend':backend,'screen_pass':False,**SCOPE}
    try:
        need(run.returncode==0,'SUPERVISOR_FAILURE')
        row['execution']=read(case/'RUN_EXIT.json')
        if probe:
            txt=(case/'STDOUT.txt').read_text();stages={stage:sorted(map(int,re.findall(r'PROBE rank=(\d+) stage='+stage+r'\b',txt))) for stage in r2.STAGES}
            need(row['execution']['exit_code']==0 and all(v==list(range(n)) for v in stages.values()),'PROBE_STAGES')
            row.update(stage_ranks=stages,screen_pass=True)
        else:row.update(parse_case(case,n,level,selected,selected,baseline))
        if not probe:need(sha(case/lib.name)==sha(lib) and (case/'input.prm').read_text()==candidate(prm.read_text(),level,visualization),'INPUT_MUTATION')
    except Exception as e:row.update(error=repr(e),traceback=traceback.format_exc())
    (case/'HOST_AFTER.txt').write_text(Path('/proc/loadavg').read_text()+Path('/proc/meminfo').read_text())
    source_check();write(case/'CASE_REPORT.json',row)
    print('RESULT',name,'PASS' if row['screen_pass'] else row.get('error'),flush=True)
    need(row['screen_pass'],'CASE_FAILED:'+name)
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','case']);ap.add_argument('--name');ap.add_argument('--ranks',type=int);ap.add_argument('--level',type=int,default=2);ap.add_argument('--profile',default='tcp',choices=['tcp','vader']);ap.add_argument('--layout',default='spread',choices=['spread','compact']);ap.add_argument('--probe',action='store_true');ap.add_argument('--baseline',type=Path);ap.add_argument('--timeout',type=int,default=240);ap.add_argument('--backend',choices=['proot','native'],default='proot')
    a=ap.parse_args()
    if a.action=='prepare':prepare()
    else:execute(a.name,a.ranks,a.level,a.profile,a.layout,a.probe,read(a.baseline) if a.baseline else None,a.timeout,backend=a.backend)
if __name__=='__main__':main()
