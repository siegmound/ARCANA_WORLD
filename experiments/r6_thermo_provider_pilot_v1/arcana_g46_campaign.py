#!/usr/bin/env python3
"""Isolated G46 synthetic campaign. Parents and historical runtimes are read-only."""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
import arcana_g45_distributed_amr_cbf as prior
BASE=prior.BASE;EV=prior.EV;PARENT=prior.ROOT;ROOT=EV/'R6_G46_CONSTRAINED_GAUGE_DATUM_NEW01'
CODE=Path(__file__).with_name('g46_constrained_gauge_v1')
PIN='a4be9d965d14dca982ad1d2d3607cdc6814e196c51d2813ceeeacdaae3c5b2fd'
sha,read,write,need=prior.sha,prior.read,prior.write,prior.need
SCOPE=read(CODE/'contract.json')['scope']

def check():
 prior.old.source_check();need(sha(CODE/'contract.json')==PIN and sha(ROOT/'FROZEN_CONTRACT.json')==PIN,'G46_CONTRACT_DRIFT');need(not (ROOT/'MANIFEST.json').exists(),'G46_ALREADY_SEALED')

def preflight():
 check();parents=[]
 for name,pin in read(CODE/'contract.json')['parents'].items():
  m=prior.old.g38.verified_bundle(EV/name,pin);parents.append({'path':name,'manifest_sha256':pin,'members':len(m['files'])});print('PARENT_VERIFIED',name,flush=True)
 write(ROOT/'PARENT_PREFLIGHT.json',{'screen_pass':True,'parents':parents,**SCOPE})
 h=prior.old.g44.host();h['numa_nodes']={str(i):{'cpulist':(Path('/sys/devices/system/node')/f'node{i}/cpulist').read_text().strip()} for i in range(4)};h['loadavg']=Path('/proc/loadavg').read_text();write(ROOT/'HARDWARE_BEFORE.json',h)
 state,container,rt,src,*_=prior.old.runtime();write(ROOT/'HISTORICAL_METADATA_BEFORE.json',prior.old.ar.tree_metadata(container))
 files=['source/simulator/nullspace.cc','source/simulator/helper_functions.cc','source/simulator/core.cc','source/simulator/checkpoint_restart.cc','source/simulator/solver/stokes_matrix_free_global_coarsening.cc','source/simulator/solver/stokes_matrix_free_local_smoothing.cc','source/simulator/solver/stokes_matrix_based.cc','source/simulator/introspection.cc','source/termination_criteria/end_time.cc','source/time_stepping/interface.cc','source/time_stepping/function.cc','include/aspect/simulator_signals.h','include/aspect/simulator_access.h']
 out=ROOT/'UPSTREAM_SOURCE';out.mkdir();ident={}
 for name in files:
  p=src/name;raw=subprocess.check_output(['git','-C',str(src),'show',prior.old.ar.ASPECT_SHA+':'+name]);need(p.read_bytes()==raw,'UPSTREAM_SOURCE_DRIFT:'+name);target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);ident[name]=sha(target)
 write(ROOT/'UPSTREAM_SOURCE_IDENTITY.json',{'commit':prior.old.ar.ASPECT_SHA,'files':ident})
 # The G45 runtime is only read; no probe/build/install inside the parent.
 identity=read(PARENT/'NATIVE_RUNTIME_BUILD.json');binary={}
 for name,row in identity['binary_identity'].items():
  p=PARENT/'native_runtime/bin'/name;need(sha(p)==row['private_sha256'] and sha(Path(row['source']))==row['source_sha256'],'RUNTIME_DRIFT');binary[name]=sha(p)
 write(ROOT/'RUNTIME_READONLY_IDENTITY.json',{'root':str(PARENT/'native_runtime'),'binary_sha256':binary,'historic_unchanged':True})
 print('G46_PREFLIGHT_PASS',flush=True)


def supervise(case,argv,env,timeout=600):
 oldroot=prior.ROOT
 try:
  prior.ROOT=ROOT
  return prior.supervise(case,argv,env,timeout)
 finally:prior.ROOT=oldroot

def env(case,extra=None):
 rt=PARENT/'native_runtime';root=prior.old.runtime()[2]
 e={'HOME':'/home/dealii','USER':'dealii','PATH':str(rt/'bin')+':/usr/bin:/bin','TMPDIR':str(case/'tmp'),'OPAL_PREFIX':str(rt),'OMPI_MCA_mca_base_component_path':str(root/'usr/lib/x86_64-linux-gnu/openmpi/lib/openmpi3'),'OMPI_MCA_pml':'ob1','OMPI_MCA_btl':'self,vader','OMPI_MCA_btl_vader_single_copy_mechanism':'none','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','HWLOC_HIDE_ERRORS':'2','PYTHONDONTWRITEBYTECODE':'1'}
 e.update(extra or {});return e

def build(label):
 check();work=ROOT/label;work.mkdir()
 for name in ('arcana_g46.cc','CMakeLists.txt'):shutil.copy2(CODE/name,work/name)
 state,container,root,src,*_=prior.old.runtime()
 prefix=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev','-b',str(work)+':/tmp','-w','/tmp']
 for stage,args in [('configure',['/usr/bin/cmake','-S','/tmp','-B','/tmp/build','-DAspect_DIR=/home/dealii/aspect']),('compile',['/usr/bin/cmake','--build','/tmp/build','--target','arcana_g46.release','--parallel','1'])]:
  case=work/stage;case.mkdir();r=supervise(case,prefix+args,{'HOME':'/home/dealii','USER':'dealii','PATH':'/usr/bin:/bin','TMPDIR':'/tmp','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','HWLOC_HIDE_ERRORS':'2'});need(r['exit_code']==0,'BUILD_FAILED:'+stage)
 lib=work/'build/libarcana_g46.release.so';need(lib.exists(),'MISSING_PLUGIN');write(work/'IDENTITY.json',{'plugin_sha256':sha(lib),'cpp_sha256':sha(work/'arcana_g46.cc'),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'contract_sha256':PIN});print('G46_BUILD_PASS',lib,flush=True)

def execute(label,spec,plugin,text=None,extra_env=None,checkpoint=None):
 check();need(spec['ranks'] in (1,2,4,8),'RANK_SCOPE')
 priorcases=list(ROOT.glob('*/CASE_SPEC.json'));need(len(priorcases)<read(CODE/'contract.json')['budgets']['native_case_budget'],'CASE_BUDGET')
 case=ROOT/label;case.mkdir();(case/'output').mkdir();write(case/'CASE_SPEC.json',spec)
 for lib in [plugin,PARENT/'plugin_build_NEW02/build/libarcana_g45.release.so']:
  shutil.copy2(lib,case/lib.name)
 if spec['family']=='analytic':
  lib=prior.old.runtime()[6];shutil.copy2(lib,case/lib.name)
 if text is None:
  text=prior.prm_for(spec).replace('./libarcana_g45.so','./libarcana_g45.so, ./libarcana_g46.so').replace('arcana g45 distributed cbf','arcana g45 distributed cbf, arcana g46 operator')
  if spec.get('gauge')=='unremoved':text=text.replace('set Remove nullspace = net rotation','set Remove nullspace = ')
 (case/'input.prm').write_text(text)
 if checkpoint:
  shutil.copytree(checkpoint/'restart',case/'output/restart');write(case/'RESTART_PARENT.json',{'source_output':str(checkpoint),'checkpoint_inventory':prior.old.g25.inventory(checkpoint/'restart')})
 oldroot=prior.ROOT
 try:prior.ROOT=ROOT;cpus=prior.cpus(spec['ranks'])
 finally:prior.ROOT=oldroot
 rt=PARENT/'native_runtime';wrapper='''#!/bin/bash
set -eu
CPUS=(CPU_VALUES)
TASKSET -pc "${CPUS[$OMPI_COMM_WORLD_RANK]}" $$ >/dev/null
printf 'HPC_RANK=%s CPU=%s\\n' "$OMPI_COMM_WORLD_RANK" "$(GREP Cpus_allowed_list /proc/self/status | CUT -f2)"
exec "$@"
'''.replace('CPU_VALUES',' '.join(map(str,cpus))).replace('TASKSET',str(rt/'bin/taskset')).replace('GREP',str(rt/'bin/grep')).replace('CUT',str(rt/'bin/cut'))
 (case/'rank.sh').write_text(wrapper)
 argv=['/usr/bin/env','LD_LIBRARY_PATH='+str(rt/'lib'),str(rt/'bin/orterun'),'-np',str(spec['ranks']),'--nooversubscribe','--bind-to','none','--map-by','slot',str(rt/'bin/bash'),str(case/'rank.sh'),str(rt/'bin/aspect-release'),'input.prm']
 write(case/'G46_EXECUTED_IDENTITY.json',{'plugin_sha256':sha(plugin),'input_sha256':sha(case/'input.prm'),'G46_contract_sha256':PIN,'G46_runner_sha256':sha(Path(__file__)),'G45_plugin_sha256':sha(PARENT/'plugin_build_NEW02/build/libarcana_g45.release.so'),'cpus':cpus})
 print('G46_START',label,flush=True);r=supervise(case,argv,env(case,extra_env));conv=prior.native_convergence(case) if r['exit_code']==0 and spec.get('kind','static')=='static' else None
 row={'exit_code':r['exit_code'],'native_convergence':conv,'spec':spec,'execution':r,'screen_pass':r['exit_code']==0 and (conv is None or conv['screen_pass']),**SCOPE};write(case/'EXECUTION_REPORT.json',row);print('G46_NATIVE_EXIT',label,r['exit_code'],row['screen_pass'],flush=True);return case,row

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','build','case']);p.add_argument('--label');p.add_argument('--plugin',type=Path);p.add_argument('--family',choices=['forced','hydro','analytic'],default='forced');p.add_argument('--level',type=int,default=2);p.add_argument('--ranks',type=int,default=1);p.add_argument('--amr',type=int,default=1);p.add_argument('--gauge',choices=['original','unremoved'],default='unremoved');p.add_argument('--matrix',action='store_true');a=p.parse_args()
 if a.action=='preflight':preflight()
 elif a.action=='build':build(a.label)
 else:execute(a.label,{'name':a.label,'family':a.family,'base_refinement':a.level,'ranks':a.ranks,'adaptive_cycles':a.amr,'gauge':a.gauge,'synthetic_time':0},a.plugin,extra_env={'ARCANA_G46_MATRIX':'1'} if a.matrix else {})
