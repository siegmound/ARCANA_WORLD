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

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight']);a=p.parse_args();preflight()
