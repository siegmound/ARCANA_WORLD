#!/usr/bin/env python3
"""Recover existing ASPECT/PRoot identity, never install, build, or solve."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ASPECT_SHA='30eb77ee5da186137d436dbad35c6cb3cab64b69'

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def write(p,d):
    with p.open('x') as f: json.dump(d,f,indent=2,sort_keys=True); f.write('\n')

def tree_metadata(root):
    # Identity guard over the historical tree, including symlinks, without following them.
    rows={}
    for p in sorted(root.rglob('*')):
        st=p.lstat()
        rows[str(p.relative_to(root))]=[st.st_mode,st.st_size,st.st_mtime_ns,
                                      os.readlink(p) if p.is_symlink() else None]
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); base=a.base.resolve(); out=a.output.resolve()
    tools=base/'ARCANA_ASPECT_TOOLS'; state=tools/'udocker-state'
    container=(state/'containers/arcana-aspect-v310').resolve()
    root=container/'ROOT'; src=root/'home/dealii/aspect'
    if out.exists() or out.is_relative_to(tools): raise RuntimeError('OUTPUT')
    out.mkdir(); (out/'scratch').mkdir()
    before=tree_metadata(container)
    paths=[tools/'udocker-1.3.17/udocker/udocker',state/'bin/proot-x86_64-4_8_0',
           src/'bin/aspect',src/'bin/aspect-release',container/'container.json',
           src/'source/main.cc',tools/'udocker-1.3.17/udocker/engine/proot.py',
           tools/'udocker-1.3.17/udocker/config.py']
    identities={str(p):sha(p) for p in paths}
    source_sha=subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
    if source_sha!=ASPECT_SHA: raise RuntimeError('ASPECT_SOURCE_DRIFT')
    cfg=json.loads((container/'container.json').read_text())
    # Bypass udocker's metadata/user setup: PRoot binary and ROOT already exist.
    # This is a new explicit read-only preflight command, not a claim to recover
    # undocumented historical CLI flags. No .prm is supplied to ASPECT.
    inner='''set -eu
/home/dealii/aspect/bin/aspect --version
/home/dealii/aspect/bin/aspect-release --version
/usr/bin/mpirun --version
/usr/bin/g++ --version
/usr/bin/ldd /home/dealii/aspect/bin/aspect-release
'''
    cmd=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev',
         '-b',str(out/'scratch')+':/tmp','-w','/home/dealii/aspect',
         '/bin/bash','--noprofile','--norc','-c',inner]
    env=dict(os.environ,HOME='/home/dealii',USER='dealii',PATH='/usr/bin:/bin',
             OMPI_MCA_btl='^vader',HWLOC_HIDE_ERRORS='2',OMP_NUM_THREADS='1',
             OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    write(out/'COMMAND.json',{'argv':cmd,'source_sha':source_sha,'UDOCKER_DIR':str(state),
        'container_id':container.name,'image_workdir':cfg['config']['WorkingDir'],
        'historical_exact_cli':'UNKNOWN: original logs retain output, not argv',
        'execution':'existing PRoot P1 backend, direct read-only version probe',
        'historical_udocker_user_setup_bypassed_to_preserve_container':True})
    with (out/'STDOUT.txt').open('x') as stdout,(out/'STDERR.txt').open('x') as stderr:
        try: result=subprocess.run(cmd,env=env,stdout=stdout,stderr=stderr,timeout=60); rc=result.returncode
        except subprocess.TimeoutExpired: rc=124
    text=(out/'STDOUT.txt').read_text()
    after=tree_metadata(container)
    unchanged=before==after and identities=={str(p):sha(p) for p in paths}
    (out/'EXIT_CODE.txt').write_text(str(rc)+'\n')
    write(out/'CONTAINER_METADATA_BEFORE.json',before)
    write(out/'IDENTITY.json',{'sha256':identities,'source_sha':source_sha,
         'container_metadata_unchanged':before==after,'targeted_bytes_unchanged':unchanged,
         'full_tree_content_rehash_claimed':False})
    ok=rc==0 and unchanged and all(v in text for v in ('3.2.0-pre','30eb77ee5','deal.II 9.6.0','Trilinos 13.2.0','p4est 2.2.0','OPTIMIZED','DEBUG'))
    report={'status':'ASPECT_EXISTING_RUNTIME_RECOVERED' if ok else 'ASPECT_RUNTIME_RECOVERY_BLOCKED',
         'screen_pass':ok,'exit_code':rc,'historical_container_unchanged':unchanged,
         'builds':0,'solves':0,'installations':0,'mantle_provider_qualified':False,
         'physical_acceptance':False,'physical_T1':None,'scientific_promotion':False,
         'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}
    write(out/'REPORT.json',report)
    write(out/'MANIFEST.json',{'files':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},'report':report,'runner_sha256':sha(Path(__file__))})
    print(json.dumps(report)); return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
