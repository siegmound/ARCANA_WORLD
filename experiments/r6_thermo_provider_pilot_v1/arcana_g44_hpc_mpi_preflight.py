#!/usr/bin/env python3
"""G44-A/B: author-selected full-mantle architecture; FAIR inventory and bounded
synthetic MPI portability screen. No physical mantle parameters or production solve.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
import traceback
import arcana_g25_fixed_load_decomposition as g25
import arcana_g32_corrected_global_operator as g32
import arcana_g38_aspect_hollow_sphere as g38
import arcana_aspect_recovery_preflight as ar

PIN='44bac8b010a6fbdcf31ba1bcb1ab4dd7cada7148d0f7960b4a8135a561d43a62'
STATUS='G43_T0_THERMAL_HANDOFF_PASS__PHYSICAL_MANTLE_INITIALIZER_BLOCKED'
P38='7bccfd5b38d7e078315b94ba85aa72efc49aa91a41825ece88866241fe4c4f82'
S38='G38_ASPECT_HOLLOW_SPHERE_REFINEMENT_PASS__FREE_SLIP_AND_MANTLE_STATE_REQUIRED'
AUTH='G44_FULL_MANTLE_HPC_SYNTHETIC_MPI_SCREEN_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
GIB=1024**3
ARCHITECTURE={
    'authorial_selection':'A_FULL_MANTLE_ADAPTIVE',
    'authorial_basis':'Author explicitly selected A following full-mantle versus truncated-shell comparison.',
    'B_role':'optional comparison, not production default',
    'use_FAIR_resources':'maximize useful throughput within actual allocation, benchmark first',
    'CMB_radius_m':None,'physical_EOS':None,'physical_rheology':None,'physical_initial_state':None,
    'ASPECT_role':'candidate full-mantle provider; physical admission pending',
    'GPU_backend_qualified':False,'physical_authority_granted':False,
    'G15_corrected_trajectory_pending':True,**g25.SCOPE}

def capture(argv,timeout=20):
    try:
        p=subprocess.run(argv,text=True,capture_output=True,timeout=timeout)
        return {'argv':argv,'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except (OSError,subprocess.TimeoutExpired) as e:
        return {'argv':argv,'rc':None,'error':str(e)}

def host():
    cpus=sorted(os.sched_getaffinity(0))
    topo=[]
    for i in cpus:
        p=Path('/sys/devices/system/cpu')/('cpu'+str(i))/'topology'
        topo.append({'cpu':i,'socket':int((p/'physical_package_id').read_text()),
            'core':int((p/'core_id').read_text())})
    cores=len({(x['socket'],x['core']) for x in topo})
    mem={k:int(v)*1024 for k,v in re.findall(r'(?m)^(\w+):\s+(\d+)\s+kB$',Path('/proc/meminfo').read_text())}
    groups=Path('/proc/self/cgroup').read_text()
    # cgroup v2 only: retain unknown for other layouts rather than assuming unlimited.
    entries=[l.split(':',2)[2] for l in groups.splitlines() if l.startswith('0::')]
    cg=[]
    if len(entries)==1:
        root=Path('/sys/fs/cgroup')
        p=(root/entries[0].lstrip('/')).resolve()
        if p.is_relative_to(root) and p.is_dir():
            while True:
                values={}
                for name in ('memory.max','memory.current','cpu.max','cpuset.cpus.effective','cpuset.mems.effective'):
                    q=p/name
                    if q.is_file():values[name]=q.read_text().strip()
                cg.append({'path':str(p),'values':values})
                if p==root:break
                p=p.parent
    limits=[]
    for row in cg:
        v=row['values']
        if v.get('memory.max','max').isdigit() and v.get('memory.current','').isdigit():
            limits.append(max(0,int(v['memory.max'])-int(v['memory.current'])))
    quotas=[]
    for row in cg:
        v=row['values'].get('cpu.max','max 100000').split()
        if len(v)==2 and v[0].isdigit() and v[1].isdigit() and int(v[1])>0:
            quotas.append(int(v[0])/int(v[1]))
    return {'affinity_cpus':cpus,'affinity_physical_cores':cores,'topology':topo,
        'memtotal_bytes':mem.get('MemTotal'),'memavailable_bytes':mem.get('MemAvailable'),
        'cgroup_raw':groups,'cgroup_v2_hierarchy':cg,'cgroup_finite_memory_headroom_bytes':min(limits) if limits else None,
        'cgroup_cpu_quota_cores':min(quotas) if quotas else None,
        'scheduler_environment':{k:os.environ[k] for k in ('SLURM_JOB_ID','SLURM_CPUS_PER_TASK','SLURM_NTASKS','PBS_JOBID','CUDA_VISIBLE_DEVICES') if k in os.environ},
        'commands':{name:capture(argv) for name,argv in (
            ('lscpu',['lscpu']),('numa',['numactl','--hardware']),('storage',['df','-hT','.']),
            ('gpu',['nvidia-smi','--query-gpu=index,name,memory.total,memory.free,driver_version','--format=csv']),
            ('gpu_topology',['nvidia-smi','topo','-m']),('gpu_p2p',['nvidia-smi','topo','-p2p','r']))},
        'allocation_caveat':'Affinity and cgroup observations are not a reservation of shared resources.'}

def run(out,state,root,prm,lib,n,baseline):
    case=out/('ranks_'+str(n));case.mkdir()
    text=g38.candidate(prm.read_text(),2)
    (case/'input.prm').write_text(text)
    shutil.copyfile(lib,case/lib.name)
    need(sha(case/lib.name)==sha(lib),'PLUGIN_COPY')
    wrapper='''#!/bin/bash
set -eu
printf 'G44_RANK=%s LOCAL_RANK=%s CPU=%s\\n' "$OMPI_COMM_WORLD_RANK" "$OMPI_COMM_WORLD_LOCAL_RANK" "$(grep Cpus_allowed_list /proc/self/status | cut -f2)"
exec /home/dealii/aspect/bin/aspect-release input.prm
'''
    (case/'rank.sh').write_text(wrapper)
    cmd=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev',
        '-b',str(case)+':/tmp','-w','/tmp','/usr/bin/mpirun','-np',str(n),
        '--nooversubscribe','--map-by','core','--bind-to','core','--report-bindings',
        '/bin/bash','/tmp/rank.sh']
    env=dict(os.environ,HOME='/home/dealii',USER='dealii',PATH='/usr/bin:/bin',
        OMPI_MCA_btl='^vader',HWLOC_HIDE_ERRORS='2',OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',TMPDIR='/tmp',PYTHONDONTWRITEBYTECODE='1')
    write(case/'COMMAND.json',{'argv':cmd,'input_sha256':sha(case/'input.prm'),
        'plugin_sha256':sha(case/lib.name),'wrapper_sha256':sha(case/'rank.sh'),
        'timeout_s':180,'address_space_limit_per_process_bytes':8*GIB,
        'environment_overrides':{k:env[k] for k in ('HOME','USER','PATH','OMPI_MCA_btl','HWLOC_HIDE_ERRORS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','TMPDIR')}})
    start=time.monotonic()
    with (case/'STDOUT.txt').open('x') as so,(case/'STDERR.txt').open('x') as se:
        p=subprocess.Popen(['/usr/bin/time','-v','-o',str(case/'TIME.txt'),*cmd],
            env=env,cwd=case,stdout=so,stderr=se,start_new_session=True,preexec_fn=g38.limits)
        try:rc=p.wait(timeout=180)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.wait();rc=124
    wall=time.monotonic()-start
    (case/'EXIT_CODE.txt').write_text(str(rc)+'\n')
    row={'ranks':n,'exit_code':rc,'wall_s':wall,'screen_pass':False}
    try:
        need(rc==0,'MPI_NATIVE_EXIT')
        s=(case/'STDOUT.txt').read_text()
        need(all(t in s for t in ('OPTIMIZED','3.2.0-pre','30eb77ee5')),'VERSION')
        need(re.search(r'\brunning with '+str(n)+r' MPI processes\b',s,re.I),'MPI_RANK_COUNT')
        markers=re.findall(r'G44_RANK=(\d+) LOCAL_RANK=(\d+) CPU=([0-9,-]+)',s)
        need(sorted(int(a) for a,b,c in markers)==list(range(n)) and sorted(int(b) for a,b,c in markers)==list(range(n)),'RANK_MARKERS')
        stats=g38.statistics(case/'output/statistics')
        need(stats['cells']==baseline['cells']==768,'MESH_PARITY')
        errors=g38.errors(s)
        delta={k:abs(errors[k]/baseline['errors'][k]-1) for k in g38.LABELS}
        need((case/'input.prm').read_text()==text and sha(case/lib.name)==sha(lib),'INPUT_MUTATION')
        row.update(stats=stats,errors=errors,relative_to_rank1=delta,rank_affinity=markers,
            numerical_parity=all(v<1e-4 for v in delta.values()))
        need(row['numerical_parity'],'MPI_NUMERICAL_PARITY')
        row['screen_pass']=True
    except Exception as e:row['error']=repr(e)
    write(case/'CASE_REPORT.json',row)
    print('G44_MPI_CASE',json.dumps(row),flush=True)
    return row

def main():
    ap=argparse.ArgumentParser()
    for k in ('base','recovery','inventory','g38','g43','output'):ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-full-mantle-hpc-screen',choices=[AUTH],required=True)
    a=ap.parse_args()
    base,rec,inv,p38,p43,out=(x.resolve() for x in (a.base,a.recovery,a.inventory,a.g38,a.g43,a.output))
    source=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    def parents():return [g38.verified_bundle(rec,g38.PREC),g38.verified_bundle(inv,g38.PINV),g32.verify(p38,P38,S38),g32.verify(p43,PIN,STATUS)]
    check();before=parents()
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in (source,rec,inv,p38,p43,base/'ARCANA_ASPECT_TOOLS')),'OUTPUT')
    out.mkdir();report={'source_sha':g25.SOURCE,'G43_manifest_sha256':PIN,'G38_manifest_sha256':P38,
        'builds':0,'installations':0,'synthetic_solves_attempted':0,'ARCANA_solves':0,
        'additional_time_advance_years':0,'material_assignments':0,'global_solve_authorized':False,
        'physical_acceptance':False,'mantle_provider_qualified':False,'MPI_multirank_qualified':False,**g25.SCOPE}
    snapshot=None
    try:
        write(out/'ARCHITECTURE_DECISION.json',ARCHITECTURE)
        h=host();write(out/'FAIR_HARDWARE.json',h)
        report['hardware_inventory_complete']=True
        report['affinity_physical_cores']=h['affinity_physical_cores']
        report['affinity_logical_cpus']=len(h['affinity_cpus'])
        report['memavailable_bytes']=h['memavailable_bytes']
        print('G44_HARDWARE',json.dumps({k:report[k] for k in ('affinity_physical_cores','affinity_logical_cpus','memavailable_bytes')}),flush=True)
        need(h['affinity_physical_cores']>=4 and (h['memavailable_bytes'] or 0)>=40*GIB,'HOST_HEADROOM')
        need(h['cgroup_cpu_quota_cores'] is None or h['cgroup_cpu_quota_cores']>=4,'CPU_QUOTA')
        need(h['cgroup_finite_memory_headroom_bytes'] is None or h['cgroup_finite_memory_headroom_bytes']>=40*GIB,'CGROUP_HEADROOM')
        state,container,root,src,hs,prm,lib,identity=g38.inputs(base,rec,inv)
        snapshot=ar.tree_metadata(container)
        baseline=read(p38/'level_2/CASE_REPORT.json')
        need(baseline['level']==2 and baseline['native_exit']==0 and baseline['cells']==768,'BASELINE')
        report['cases']=[]
        for n in (2,4):
            report['synthetic_solves_attempted']+=1
            row=run(out,state,root,prm,lib,n,baseline);report['cases'].append(row)
            need(row['screen_pass'],'MPI_SCREEN:'+str(n))
        report.update(screen_pass=True,MPI_multirank_qualified=True,
            status='G44_AB_HPC_INVENTORY_AND_SMALL_MPI_PASS__SCALING_REQUIRED')
    except Exception as e:report.update(screen_pass=False,status='G44_AB_HPC_MPI_SCREEN_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        check();need(parents()==before,'PARENT_MUTATION')
        if snapshot is not None:
            need(ar.tree_metadata(container)==snapshot,'CONTAINER_DRIFT');g38.inputs(base,rec,inv)
        report['source_and_parents_unchanged']=True
    except Exception as e:report.update(screen_pass=False,MPI_multirank_qualified=False,status='G44_AB_HPC_MPI_SCREEN_BLOCKED',postcheck_error=repr(e))
    report['limitations']=['2/4 rank synthetic uniform level-2 only, not scalability or production admission.',
        'Per-process address-space cap, not an aggregate memory cap; time -v RSS is not summed rank memory.',
        'No GPU compute, adaptive mesh MPI, physical CBF MPI or high-rank claim.',
        'Missing or unknown cgroup layout is not proof of unrestricted allocation.']
    write(out/'REPORT.json',report);write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G44_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
