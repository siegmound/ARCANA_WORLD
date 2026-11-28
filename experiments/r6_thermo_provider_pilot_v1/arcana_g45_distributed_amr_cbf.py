#!/usr/bin/env python3
"""Write-once G45 synthetic runner. Never write into G44 or historical runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import arcana_g44_hpc_campaign as old
import arcana_g39_aspect_free_slip as g39

BASE=old.BASE;EV=old.EV;ROOT=EV/'R6_G45_DISTRIBUTED_AMR_CBF_20261128_NEW01'
CODE=Path(__file__).with_name('g45_distributed_cbf_v1')
SCOPE=old.SCOPE
sha,read,write,need=old.sha,old.read,old.write,old.need
CONTRACT_PIN='9b3214d51e986e7317b04c57ccf3ecdc1bf6729861c3e1dfb00472d65ca548c7'

def check():
    old.source_check();need(not (ROOT/'MANIFEST.json').exists(),'G45_ROOT_ALREADY_SEALED')
    need(sha(CODE/'contract.json')==CONTRACT_PIN and sha(ROOT/'FROZEN_CONTRACT.json')==CONTRACT_PIN,'CONTRACT_CHANGED')
    need(read(ROOT/'PARENT_PREFLIGHT.json')['screen_pass'],'PREFLIGHT')

def cpus(n):
    h=read(ROOT/'HARDWARE_BEFORE.json');groups={}
    for row in h['topology']:groups.setdefault((row['socket'],row['core']),[]).append(row['cpu'])
    physical=[min(v) for _,v in sorted(groups.items())];nodes={i:[] for i in range(4)}
    for cpu in physical:
        node=next(i for i in range(4) if cpu in old.r2.cpuset(h['numa_nodes'][str(i)]['cpulist']));nodes[node].append(cpu)
    ordered=[cpu for group in zip(*nodes.values()) for cpu in group]
    need(n in (1,2,4,8) and set(ordered[:n])<=os.sched_getaffinity(0),'CPU_SCOPE_OR_ALLOCATION')
    return ordered[:n]

def environment(case):
    rt=ROOT/'native_runtime';root=old.runtime()[2]
    return {'HOME':'/home/dealii','USER':'dealii','PATH':str(rt/'bin')+':/usr/bin:/bin','TMPDIR':str(case/'tmp'),
        'OPAL_PREFIX':str(rt),'OMPI_MCA_mca_base_component_path':str(root/'usr/lib/x86_64-linux-gnu/openmpi/lib/openmpi3'),
        'OMPI_MCA_pml':'ob1','OMPI_MCA_btl':'self,vader','OMPI_MCA_btl_vader_single_copy_mechanism':'none',
        'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','HWLOC_HIDE_ERRORS':'2','PYTHONDONTWRITEBYTECODE':'1'}

def supervise(case,argv,env,timeout=600):
    (case/'tmp').mkdir(exist_ok=True)
    config={'case':str(case),'tag':hashlib.sha256(str(case).encode()).hexdigest(),'argv':argv,'environment':env,
        'timeout_s':timeout,'aggregate_pss_abort_bytes':16*2**30,
        'host_available_floor_bytes':max(64*2**30,int(read(ROOT/'HARDWARE_BEFORE.json')['memavailable_bytes']*.25)),
        'sample_interval_s':.5}
    supervisor=Path(__file__).with_name('arcana_hpc_supervisor.py')
    write(case/'config.json',config);write(case/'CODE_IDENTITY.json',{'runner_sha256':sha(Path(__file__)),'supervisor_sha256':sha(supervisor),'contract_sha256':CONTRACT_PIN,
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()})
    (case/'HOST_BEFORE.txt').write_text(Path('/proc/loadavg').read_text()+Path('/proc/meminfo').read_text())
    with (case/'SUPERVISOR.stdout').open('x') as so,(case/'SUPERVISOR.stderr').open('x') as se:
        proc=subprocess.run(['/usr/bin/python3',str(supervisor),'--run',str(case/'config.json')],stdout=so,stderr=se)
    (case/'HOST_AFTER.txt').write_text(Path('/proc/loadavg').read_text()+Path('/proc/meminfo').read_text())
    need(proc.returncode==0,'SUPERVISOR_FAILED:'+case.name)
    result=read(case/'RUN_EXIT.json');need(not result['remaining'],'CLEANUP_UNSAFE')
    return result

def build(label):
    check();work=ROOT/label;work.mkdir()
    for name in ('arcana_g45.cc','CMakeLists.txt'):shutil.copy2(CODE/name,work/name)
    state,container,root,src,hs,*_=old.runtime()
    configset=set()
    for p in (EV/'R6_G42_CONSISTENT_BOUNDARY_FLUX_NEW01/plugin').rglob('CMakeCache.txt'):
        configset.update(re.findall(r'^Aspect_DIR:PATH=(.+)$',p.read_text(),re.M))
    need(len(configset)==1,'EXACT_ASPECT_CMAKE_CONFIG')
    prefix=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev','-b',str(work)+':/tmp','-w','/tmp']
    for stage,args in (('configure',['/usr/bin/cmake','-S','/tmp','-B','/tmp/build','-DAspect_DIR='+next(iter(configset))]),
                       ('compile',['/usr/bin/cmake','--build','/tmp/build','--target','arcana_g45.release','--parallel','1'])):
        case=work/stage;case.mkdir();result=supervise(case,prefix+args,{'HOME':'/home/dealii','USER':'dealii','PATH':'/usr/bin:/bin','TMPDIR':'/tmp','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','HWLOC_HIDE_ERRORS':'2'})
        need(result['exit_code']==0,'BUILD_STAGE_FAILED:'+stage)
    lib=work/'build/libarcana_g45.release.so';need(lib.is_file(),'PLUGIN_NOT_BUILT')
    write(work/'PLUGIN_IDENTITY.json',{'plugin':str(lib),'plugin_sha256':sha(lib),'cpp_sha256':sha(work/'arcana_g45.cc'),
        'cmake_sha256':sha(work/'CMakeLists.txt'),'ASPECT_source_sha':old.ar.ASPECT_SHA,'contract_sha256':CONTRACT_PIN})
    print('G45_BUILD_PASS',lib,flush=True)

def prm_for(spec):
    family=spec['family'];level=spec['base_refinement'];amr=spec['adaptive_cycles']
    if family=='analytic':
        raw=old.runtime()[5].read_text();text=old.candidate(raw,level)
        text=text.replace('./libhollow_sphere.so','./libhollow_sphere.so, ./libarcana_g45.so')
        text=re.sub(r'(set List of postprocessors\s*=)([^\n]+)',lambda m:m[1]+' '+', '.join(dict.fromkeys([x.strip() for x in m[2].split(',')]+['dynamic topography','arcana g45 distributed cbf'])),text)
    else:
        text='set Additional shared libraries = ./libarcana_g45.so\n'+g39.PRM.format(level=level,gauge='net rotation',datum=10 if family=='datum' else 0,
             temperature='1000' if family=='hydro' else '1000+100*(x*y+0.3*z)')
        text=text.replace('viscous dissipation statistics','viscous dissipation statistics, dynamic topography, arcana g45 distributed cbf')
    text,count=re.subn(r'(set Initial adaptive refinement\s*=\s*)0\b',lambda m:m[1]+str(amr),text);need(count==1,'ADAPTIVE_PRM')
    return refinement_settings(text)

def refinement_settings(text):
    def patch(m):
        body=re.sub(r'(?m)^\s*set (?:Strategy|Refinement fraction|Coarsening fraction|Run postprocessors on initial refinement)\s*=.*$', '',m[2])
        return m[1]+body+'\n  set Strategy = arcana g45 deterministic\n  set Refinement fraction = 0\n  set Coarsening fraction = 0\n  set Run postprocessors on initial refinement = false'+m[3]
    text,count=re.subn(r'(subsection Mesh refinement\n)(.*?)(\nend)',patch,text,flags=re.S)
    need(count==1,'MESH_SUBSECTION_SCOPE')
    return text

def case(spec,label,plugin,extra_prm=''):
    check();need(spec in read(CODE/'contract.json')['cases'],'CASE_NOT_FROZEN')
    work=ROOT/label;work.mkdir();(work/'output').mkdir();n=spec['ranks'];selected=cpus(n);rt=ROOT/'native_runtime'
    write(work/'CASE_SPEC.json',spec);shutil.copy2(plugin,work/plugin.name);(work/'input.prm').write_text(prm_for(spec)+extra_prm)
    if spec['family']=='analytic':lib=old.runtime()[6];shutil.copy2(lib,work/lib.name)
    wrapper='''#!/bin/bash
set -eu
CPUS=(CPU_VALUES)
TASKSET -pc "${CPUS[$OMPI_COMM_WORLD_RANK]}" $$ >/dev/null
printf 'HPC_RANK=%s CPU=%s\\n' "$OMPI_COMM_WORLD_RANK" "$(GREP Cpus_allowed_list /proc/self/status | CUT -f2)"
exec "$@"
'''.replace('CPU_VALUES',' '.join(map(str,selected))).replace('TASKSET',str(rt/'bin/taskset')).replace('GREP',str(rt/'bin/grep')).replace('CUT',str(rt/'bin/cut'))
    (work/'rank.sh').write_text(wrapper)
    argv=['/usr/bin/env','LD_LIBRARY_PATH='+str(rt/'lib'),str(rt/'bin/orterun'),'-np',str(n),'--nooversubscribe','--bind-to','none','--map-by','slot',str(rt/'bin/bash'),str(work/'rank.sh'),str(rt/'bin/aspect-release'),'input.prm']
    print('G45_START',label,flush=True);result=supervise(work,argv,environment(work));text=(work/'STDOUT.txt').read_text()
    row={'screen_pass':False,'case_spec':spec,'plugin_sha256':sha(plugin),'input_sha256':sha(work/'input.prm'),'execution':result,**SCOPE}
    if result['exit_code']==0:
        need('30eb77ee5' in text and 'OPTIMIZED' in text and re.search(r'running with '+str(n)+r' MPI process',text,re.I),'RUNTIME_IDENTITY')
        marks=re.findall(r'HPC_RANK=(\d+) CPU=([\d,-]+)',text);need(len(marks)==n and all(old.r2.cpuset(cpu)=={selected[int(rank)]} for rank,cpu in marks),'RANK_AFFINITY')
        need(len(list((work/'output').glob('G45_s0_r*_SUMMARY.dat')))==n,'SHARD_COUNT')
        row.update(screen_pass=True,rank_affinity=marks,statistics=old.g38.statistics(work/'output/statistics'))
    write(work/'EXECUTION_REPORT.json',row);print('G45_NATIVE_EXIT',label,result['exit_code'],flush=True)
    return row

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','case','version']);p.add_argument('--label',required=True);p.add_argument('--spec');p.add_argument('--plugin',type=Path)
    a=p.parse_args()
    if a.action=='build':build(a.label)
    elif a.action=='case':
        spec=next(x for x in read(CODE/'contract.json')['cases'] if x['name']==a.spec);r=case(spec,a.label,a.plugin);need(r['screen_pass'],'NATIVE_CASE_FAILED')
    else:
        check();work=ROOT/a.label;work.mkdir();rt=ROOT/'native_runtime';r=supervise(work,['/usr/bin/env','LD_LIBRARY_PATH='+str(rt/'lib'),str(rt/'bin/aspect-release'),'--version'],environment(work),60);need(r['exit_code']==0 and '30eb77ee5' in (work/'STDOUT.txt').read_text(),'NATIVE_VERSION')
if __name__=='__main__':main()
