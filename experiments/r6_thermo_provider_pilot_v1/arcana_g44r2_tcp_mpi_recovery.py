#!/usr/bin/env python3
"""G44-R2: reuse qualified TCP probe, retire legacy transport and qualify ASPECT.
Preserve G44 and R1; targeted pidfd cleanup only, no build or physical solve.
"""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import time
import traceback
import arcana_g44_hpc_mpi_preflight as g44
import arcana_g38_aspect_hollow_sphere as g38
import arcana_g32_corrected_global_operator as g32
import arcana_g25_fixed_load_decomposition as g25
import arcana_aspect_recovery_preflight as ar

FAILED_PIN='c75838030314bc72dd7fb197ac06e7a8f33764e45e346e71eba50f94ceba2954'
FAILED_STATUS='G44_AB_HPC_MPI_SCREEN_BLOCKED'
R1_PIN='399a7439e54365817d04905055e06bc50fd32556a5ecd8871967b2e5c21f49c8'
R1_STATUS='G44R1_MPI_RECOVERY_BLOCKED'
AUTH='G44R2_TCP_MPI_RECOVERY_ONLY_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
PROFILES={'legacy_btl':{'OMPI_MCA_btl':'^vader'},
          'tcp_loopback':{'OMPI_MCA_pml':'ob1','OMPI_MCA_btl':'self,tcp',
                          'OMPI_MCA_btl_tcp_if_include':'lo','OMPI_MCA_oob_tcp_if_include':'lo'}}
C=r'''
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
static void mark(int r,const char *s) {printf("PROBE rank=%d stage=%s\n",r,s);fflush(stdout);}
int main(int argc,char **argv) {
  int r=-1,n=0,provided=0,expected=argc>1?atoi(argv[1]):0;
  printf("PROBE preinit pid=%ld\n",(long)getpid());fflush(stdout);
  if(MPI_Init_thread(&argc,&argv,MPI_THREAD_FUNNELED,&provided)!=MPI_SUCCESS)return 2;
  MPI_Comm_rank(MPI_COMM_WORLD,&r);MPI_Comm_size(MPI_COMM_WORLD,&n);mark(r,"init");
  if(n!=expected || provided<MPI_THREAD_FUNNELED)MPI_Abort(MPI_COMM_WORLD,3);
  MPI_Barrier(MPI_COMM_WORLD);mark(r,"barrier");
  int a=r+1,b=0;
  MPI_Allreduce(&a,&b,1,MPI_INT,MPI_SUM,MPI_COMM_WORLD);
  if(b!=n*(n+1)/2)MPI_Abort(MPI_COMM_WORLD,4);
  mark(r,"allreduce");
  int *send=malloc(n*sizeof(int)),*recv=malloc(n*sizeof(int));
  if(!send || !recv)MPI_Abort(MPI_COMM_WORLD,5);
  for(int i=0;i<n;i++)send[i]=100*r+i;
  MPI_Alltoall(send,1,MPI_INT,recv,1,MPI_INT,MPI_COMM_WORLD);
  for(int i=0;i<n;i++)if(recv[i]!=100*i+r)MPI_Abort(MPI_COMM_WORLD,6);
  mark(r,"alltoall");
  const int count=262144;
  double *x=malloc(count*sizeof(double)),*y=malloc(count*sizeof(double));
  if(!x||!y)MPI_Abort(MPI_COMM_WORLD,7);
  for(int i=0;i<count;i++)x[i]=r+1.;
  MPI_Allreduce(x,y,count,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD);
  for(int i=0;i<count;i++)if(y[i]!=b)MPI_Abort(MPI_COMM_WORLD,8);
  mark(r,"large_allreduce");
  if(r==0){FILE *f=fopen("shared-marker.txt","w");if(!f)MPI_Abort(MPI_COMM_WORLD,9);
    if(fputs("G44R1\n",f)<0||fclose(f)!=0)MPI_Abort(MPI_COMM_WORLD,10);}
  MPI_Barrier(MPI_COMM_WORLD);
  FILE *f=fopen("shared-marker.txt","r");char line[32];
  if(!f||!fgets(line,sizeof(line),f)||line[0]!='G')MPI_Abort(MPI_COMM_WORLD,11);
  fclose(f);mark(r,"shared_file");
  free(x);free(y);free(send);free(recv);
  MPI_Barrier(MPI_COMM_WORLD);mark(r,"before_finalize");
  if(MPI_Finalize()!=MPI_SUCCESS)return 12;
  mark(r,"complete");return 0;
}
'''
STAGES=('init','barrier','allreduce','alltoall','large_allreduce','shared_file','before_finalize','complete')
WRAPPER='''#!/bin/bash
set -eu
printf 'G44R1_RANK=%s CPU=%s\\n' "$OMPI_COMM_WORLD_RANK" "$(grep Cpus_allowed_list /proc/self/status | cut -f2)"
exec "$@"
'''

def tagged(tag):
    key=('ARCANA_G44R1_JOB='+tag).encode()
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if p.stat().st_uid==os.getuid() and key in (p/'environ').read_bytes().split(b'\0'):
                found.append(int(p.name))
        except (OSError,PermissionError):pass
    return sorted(found)

def cleanup(tag):
    # Signal only same-UID processes carrying the exact manifest-bound tag.
    # pidfd avoids signalling a recycled PID. Never signal by process name.
    need(hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal'),'PIDFD_UNAVAILABLE')
    events=[]
    for sig in (signal.SIGTERM,signal.SIGKILL):
        for pid in tagged(tag):
            try: fd=os.pidfd_open(pid)
            except ProcessLookupError: continue
            try:
                if pid not in tagged(tag):continue
                try:
                    signal.pidfd_send_signal(fd,sig)
                    events.append({'pid':pid,'signal':sig.name})
                except ProcessLookupError:pass
            finally:os.close(fd)
        until=time.monotonic()+5
        while tagged(tag) and time.monotonic()<until:time.sleep(.1)
        if not tagged(tag):break
    return {'tag':tag,'signals':events,'remaining_tagged_pids':tagged(tag)}

def cleanup_previous(p):
    case=p/'probe_legacy_btl_2'
    cmd=read(case/'RUN_COMMAND.json')
    tag=sha(case/'JOB_ID.txt')
    need(cmd['tag']==tag and cmd['profile']=='legacy_btl' and
         (case/'JOB_ID.txt').read_text()==str(case.resolve())+'\n','LEGACY_TAG_AUTHORITY')
    old=read(case/'RUN_EXIT.json')
    need(old['exit_code']==124 and old['remaining_tagged_pids']==[1950845,1950846,1950850,1950851],
         'LEGACY_TIMEOUT_AUTHORITY')
    return cleanup(tag)

def launch(case,state,root,args,label,timeout,profile=None):
    tag=sha(case/'JOB_ID.txt') if (case/'JOB_ID.txt').exists() else None
    if tag is None:
        (case/'JOB_ID.txt').write_text(str(case.resolve())+'\n')
        tag=sha(case/'JOB_ID.txt')
    env={k:v for k,v in os.environ.items() if not k.startswith(('OMPI_','PMIX_','PMI_','OPAL_','ORTE_'))
         and k not in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','LD_PRELOAD','LD_LIBRARY_PATH')}
    env.update(HOME='/home/dealii',USER='dealii',PATH='/usr/bin:/bin',TMPDIR='/tmp',
               HWLOC_HIDE_ERRORS='2',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
               PYTHONDONTWRITEBYTECODE='1',ARCANA_G44R1_JOB=tag)
    if profile:env.update(PROFILES[profile])
    cmd=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev',
         '-b',str(case)+':/tmp','-w','/tmp',*args]
    write(case/(label+'_COMMAND.json'),{'argv':cmd,'timeout_s':timeout,'profile':profile,
        'MCA':PROFILES.get(profile,{}),'tag':tag,'per_process_AS_bytes':8*1024**3,
        'inherited_MPI_and_display_environment_removed':True})
    need(not tagged(tag),'PREEXISTING_TAGGED_PROCESS')
    start=time.monotonic()
    with (case/(label+'_STDOUT.txt')).open('x') as so,(case/(label+'_STDERR.txt')).open('x') as se:
        p=subprocess.Popen(['/usr/bin/time','-v','-o',str(case/(label+'_TIME.txt')),*cmd],
            env=env,cwd=case,stdout=so,stderr=se,start_new_session=True,preexec_fn=g38.limits)
        try:rc=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Only this launched process group; never global pkill.
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait()
            rc=124
    # mpirun children may have separate process groups; check even if the
    # outer launcher has exited. Keep all cleanup actions as evidence.
    initial=tagged(tag)
    recovery=cleanup(tag) if initial else {'tag':tag,'signals':[],'remaining_tagged_pids':[]}
    remaining=recovery['remaining_tagged_pids']
    result={'exit_code':rc,'wall_s':time.monotonic()-start,'remaining_tagged_pids':remaining,
            'initial_tagged_pids_after_exit':initial,'cleanup':recovery}
    write(case/(label+'_EXIT.json'),result)
    need(not remaining,'TAGGED_PROCESSES_REMAIN:'+str(remaining))
    # A nominal successful launcher exit with forcibly cleaned children
    # is not a clean MPI success.
    if initial and rc==0:result['exit_code']=125
    return result

def mpi(n,exe):
    return ['/usr/bin/mpirun','-np',str(n),'--nooversubscribe','--map-by','core',
            '--bind-to','core','--report-bindings','/bin/bash','/tmp/rank.sh',*exe]

def cpuset(s):
    out=set()
    for token in s.split(','):
        a=token.split('-');out.update(range(int(a[0]),int(a[-1])+1))
    return out

def affinity(text,n,h):
    marks=re.findall(r'G44R1_RANK=(\d+) CPU=([0-9,-]+)',text)
    need(sorted(int(r) for r,_ in marks)==list(range(n)),'RANK_MARKERS')
    topology={x['cpu']:(x['socket'],x['core']) for x in h['topology']}
    used=set()
    for r,s in marks:
        cp=cpuset(s);need(cp and cp<=topology.keys(),'AFFINITY_RANGE')
        core={topology[i] for i in cp}
        need(len(core)==1 and not core&used,'AFFINITY_PHYSICAL_CORE_OVERLAP')
        used|=core
    return marks

def probe(out,state,root,binary,profile,n,h):
    case=out/('probe_'+profile+'_'+str(n));case.mkdir()
    shutil.copy2(binary,case/'mpi_probe')
    (case/'rank.sh').write_text(WRAPPER)
    r=launch(case,state,root,mpi(n,['/tmp/mpi_probe',str(n)]),'RUN',45,profile)
    s=(case/'RUN_STDOUT.txt').read_text()
    r['profile']=profile;r['ranks']=n
    r['stage_ranks']={stage:sorted(int(x) for x in re.findall(r'PROBE rank=(\d+) stage='+stage+r'\b',s)) for stage in STAGES}
    try:
        r['rank_affinity']=affinity(s,n,h)
        r['screen_pass']=r['exit_code']==0 and all(v==list(range(n)) for v in r['stage_ranks'].values())
    except Exception as e:r.update(screen_pass=False,error=repr(e))
    write(case/'CASE_REPORT.json',r);print('G44R1_PROBE',json.dumps(r),flush=True)
    return r

def solve(out,state,root,prm,lib,profile,n,h,baseline):
    case=out/('aspect_'+profile+'_'+str(n));case.mkdir()
    txt=g38.candidate(prm.read_text(),2)
    (case/'input.prm').write_text(txt);shutil.copy2(lib,case/lib.name)
    (case/'rank.sh').write_text(WRAPPER)
    # Avoid the rank-zero output-directory creation path. No physical or
    # numerical parameter is changed relative to the G38/G44 input.
    (case/'output').mkdir()
    r=launch(case,state,root,mpi(n,['/home/dealii/aspect/bin/aspect-release','input.prm']),'RUN',90,profile)
    r.update(profile=profile,ranks=n,screen_pass=False)
    s=(case/'RUN_STDOUT.txt').read_text()
    try:
        need(r['exit_code']==0,'ASPECT_EXIT')
        need(all(x in s for x in ('OPTIMIZED','3.2.0-pre','30eb77ee5')) and
             re.search(r'\brunning with '+str(n)+r' MPI processes\b',s,re.I),'ASPECT_IDENTITY')
        r['rank_affinity']=affinity(s,n,h)
        r['stats']=g38.statistics(case/'output/statistics')
        need(r['stats']['cells']==baseline['cells']==768,'MESH_PARITY')
        r['errors']=g38.errors(s)
        r['relative_to_rank1']={k:abs(r['errors'][k]/baseline['errors'][k]-1) for k in g38.LABELS}
        need(all(v<1e-4 for v in r['relative_to_rank1'].values()),'NUMERICAL_PARITY')
        need((case/'input.prm').read_text()==txt and sha(case/lib.name)==sha(lib),'INPUT_MUTATION')
        r['screen_pass']=True
    except Exception as e:r['error']=repr(e)
    write(case/'CASE_REPORT.json',r);print('G44R1_ASPECT',json.dumps(r),flush=True)
    return r

def main():
    ap=argparse.ArgumentParser()
    for k in ('base','recovery','inventory','g38','g43','failed-g44','failed-r1','output'):
        ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-mpi-recovery-only',choices=[AUTH],required=True)
    a=ap.parse_args()
    base,rec,inv,p38,p43,failed,p1,out=(x.resolve() for x in (a.base,a.recovery,a.inventory,a.g38,a.g43,a.failed_g44,a.failed_r1,a.output))
    source=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    def parents():return [g38.verified_bundle(rec,g38.PREC),g38.verified_bundle(inv,g38.PINV),
        g32.verify(p38,g44.P38,g44.S38),g32.verify(p43,g44.PIN,g44.STATUS),
        g32.verify(failed,FAILED_PIN,FAILED_STATUS),g32.verify(p1,R1_PIN,R1_STATUS)]
    check();before=parents()
    need(before[-2]['screen_pass'] is False and before[-2]['cases'][0]['exit_code']==124,'FAILED_PARENT')
    need(before[-1]['screen_pass'] is False and before[-1]['synthetic_solves_attempted']==0 and
         before[-1]['probes'][0]['screen_pass'] and before[-1]['probes'][0]['profile']=='tcp_loopback','R1_PARENT')
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in
        (source,rec,inv,p38,p43,failed,p1,base/'ARCANA_ASPECT_TOOLS')),'OUTPUT')
    out.mkdir();report={'source_sha':g25.SOURCE,'G44_failed_manifest_sha256':FAILED_PIN,
        'G38_manifest_sha256':g44.P38,'G43_manifest_sha256':g44.PIN,'G44R1_failed_manifest_sha256':R1_PIN,
        'probe_builds_attempted':0,'ASPECT_builds':0,'installations':0,'synthetic_solves_attempted':0,
        'ARCANA_solves':0,'additional_time_advance_years':0,'material_assignments':0,
        'global_solve_authorized':False,'physical_acceptance':False,'MPI_multirank_qualified':False,
        'mantle_provider_qualified':False,**g25.SCOPE}
    snapshot=None
    try:
        report['legacy_cleanup']=cleanup_previous(p1)
        write(out/'LEGACY_CLEANUP.json',report['legacy_cleanup'])
        need(not report['legacy_cleanup']['remaining_tagged_pids'],'LEGACY_PROCESSES_REMAIN')
        h=g44.host();write(out/'FAIR_HARDWARE.json',h)
        need(h['affinity_physical_cores']>=4 and (h['memavailable_bytes'] or 0)>=40*1024**3,'HOST_HEADROOM')
        need(h['cgroup_cpu_quota_cores'] is None or h['cgroup_cpu_quota_cores']>=4,'CPU_QUOTA')
        need(h['cgroup_finite_memory_headroom_bytes'] is None or h['cgroup_finite_memory_headroom_bytes']>=40*1024**3,'CGROUP_HEADROOM')
        state,container,root,src,hs,prm,lib,identity=g38.inputs(base,rec,inv)
        snapshot=ar.tree_metadata(container)
        baseline=read(p38/'level_2/CASE_REPORT.json')
        need(baseline['native_exit']==0 and baseline['cells']==768,'BASELINE')
        build=p1/'probe_build'
        binary=build/'mpi_probe'
        identity_probe=read(build/'IDENTITY.json')
        need(sha(binary)==identity_probe['binary_sha256'] and
             sha(build/'mpi_probe.c')==identity_probe['source_sha256'] and
             (build/'mpi_probe.c').read_text()==C,'RETAINED_PROBE_IDENTITY')
        prior=read(p1/'probe_tcp_loopback_2/CASE_REPORT.json')
        need(prior==before[-1]['probes'][0] and prior['exit_code']==0 and
             all(prior['stage_ranks'][stage]==[0,1] for stage in STAGES) and
             not prior['remaining_tagged_pids'],'TCP_PRIOR')
        report['retained_probe_identity']=identity_probe
        report['prior_tcp_probe']=prior
        report['probes']=[];report['cases']=[]
        selected='tcp_loopback';report['selected_profile']=selected
        # Start directly with ASPECT using the already passing TCP profile.
        report['synthetic_solves_attempted']+=1
        row=solve(out,state,root,prm,lib,selected,2,h,baseline);report['cases'].append(row)
        need(row['screen_pass'],'RANK2_ASPECT')
        row=probe(out,state,root,binary,selected,4,h);report['probes'].append(row)
        need(row['screen_pass'],'RANK4_PROBE')
        report['synthetic_solves_attempted']+=1
        row=solve(out,state,root,prm,lib,selected,4,h,baseline);report['cases'].append(row)
        need(row['screen_pass'],'RANK4_ASPECT')
        report.update(screen_pass=True,MPI_multirank_qualified=True,
                      status='G44R2_SMALL_TCP_MPI_PASS__SCALING_REQUIRED')
    except Exception as e:report.update(screen_pass=False,status='G44R2_TCP_MPI_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        check();need(parents()==before,'PARENT_MUTATION')
        if snapshot is not None:
            need(ar.tree_metadata(container)==snapshot,'CONTAINER_DRIFT');g38.inputs(base,rec,inv)
        report['source_and_parents_unchanged']=True
    except Exception as e:report.update(screen_pass=False,MPI_multirank_qualified=False,status='G44R2_TCP_MPI_BLOCKED',postcheck_error=repr(e))
    report['limitations']=['Synthetic 2/4 rank only; no scaling claim.',
        'Legacy transport is deliberately not repeated. TCP success does not isolate the original component.',
        'MPI probe tests collectives and shared file visibility, not all MPI features.',
        'No aggregate memory or GPU qualification. No new physical authority.']
    write(out/'REPORT.json',report);write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G44R2_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
