#!/usr/bin/python3
"""Linux pidfd job supervisor. Run with system Python; no unsafe PID fallback.
Only same-UID processes with an exact initial-environment job token are owned.
"""
import argparse
import ctypes
import errno
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import time

KEY='ARCANA_HPC_JOB'
SCAN_FLOOR_TICKS=0
DESCENDANT_ROOT=None
HELD_PIDFDS={}

def held_exited(pid,starttime,wait_ms=0):
    """Kernel-confirmed termination, independent of proc exit/dumpability races."""
    for identity,fd in HELD_PIDFDS.items():
        if identity[:2]!=(pid,starttime):continue
        poll=select.poll();poll.register(fd,select.POLLIN)
        return any(events & select.POLLIN for _,events in poll.poll(wait_ms))
    return False

def write(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')

def proc_read(reader):
    """Retry transient Linux exit/exec dumpability transitions; persistent denial blocks."""
    for attempt in range(20):
        try:return reader()
        except PermissionError:
            if attempt==19:raise
            time.sleep(.01)

def scan(tag,key=KEY):
    if not re.fullmatch(r'[a-f0-9]{64}',tag):raise ValueError('INVALID_JOB_TOKEN')
    marker=(key+'='+tag).encode();found=[];errors=[]
    parent_map={}
    if DESCENDANT_ROOT is not None:
        for item in Path('/proc').iterdir():
            if not item.name.isdigit():continue
            try:
                raw=(item/'stat').read_text();fields=raw[raw.rfind(')')+2:].split()
                parent_map[int(item.name)]=int(fields[1])
            except OSError:continue
    def in_job(pid):
        if DESCENDANT_ROOT is None:return True
        seen=set()
        while pid>1 and pid not in seen:
            if pid==DESCENDANT_ROOT:return True
            seen.add(pid);pid=parent_map.get(pid,0)
        return False
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or not in_job(int(p.name)):continue
        known_start=None
        try:
            if p.stat().st_uid!=os.getuid():continue
            text=(p/'stat').read_text();fields=text[text.rfind(')')+2:].split()
            known_start=int(fields[19])
            if int(fields[19])<SCAN_FLOOR_TICKS:continue
            if fields[0] in ('Z','X'):continue
            if marker not in proc_read((p/'environ').read_bytes).split(b'\0'):continue
            found.append({'pid':int(p.name),'starttime':int(fields[19]),'state':fields[0]})
        except OSError as e:
            if e.errno not in (errno.ENOENT,errno.ESRCH):
                # Linux can revoke environ access during the exit transition.
                # Recheck disappearance/zombie state; persistent live denial blocks.
                try:
                    now=(p/'stat').read_text();state=now[now.rfind(')')+2:].split()[0]
                    if state in ('Z','X'):continue
                except OSError as gone:
                    if gone.errno in (errno.ENOENT,errno.ESRCH):continue
                # A retained pidfd can prove death even before proc has reached
                # its final zombie/disappearance state. Never infer from EACCES.
                if e.errno==errno.EACCES and known_start is not None and held_exited(int(p.name),known_start,500):continue
                errors.append({'pid':int(p.name),'errno':e.errno})
    if errors:raise RuntimeError('UNRELIABLE_PROC_SCAN:'+json.dumps(errors))
    return found

def open_owned(row,tag,key=KEY):
    # A held pidfd cannot follow a recycled pid. Reconfirm starttime, UID and tag
    # after opening before any signal; a raced new process is never signalled.
    fd=os.pidfd_open(row['pid'])
    try:
        p=Path('/proc')/str(row['pid'])
        raw=proc_read((p/'stat').read_text);fields=raw[raw.rfind(')')+2:].split()
        owned=(p.stat().st_uid==os.getuid() and int(fields[19])==row['starttime']
               and fields[0] not in ('Z','X')
               and (key+'='+tag).encode() in proc_read((p/'environ').read_bytes).split(b'\0'))
        if not owned:
            os.close(fd);return None
        return fd
    except OSError as e:
        os.close(fd)
        if e.errno in (errno.ENOENT,errno.ESRCH):return None
        raise
    except BaseException:
        os.close(fd);raise

def held_fd(row,tag,key=KEY):
    identity=(row['pid'],row['starttime'],key,tag)
    if identity not in HELD_PIDFDS:
        fd=open_owned(row,tag,key)
        if fd is not None:HELD_PIDFDS[identity]=fd
    return HELD_PIDFDS.get(identity)

def close_held():
    for fd in HELD_PIDFDS.values():os.close(fd)
    HELD_PIDFDS.clear()

def capability():
    result={'python':os.sys.executable,'pidfd_open':hasattr(os,'pidfd_open'),
            'pidfd_send_signal':hasattr(signal,'pidfd_send_signal')}
    if all(result[x] for x in ('pidfd_open','pidfd_send_signal')):
        fd=os.pidfd_open(os.getpid());os.close(fd);result['self_pidfd']=True
    return result

def cleanup(tag,key=KEY,grace=3.):
    initial=scan(tag,key)
    if not initial:return {'no_op':True,'initial':[],'signals':[],'remaining':[]}
    cap=capability()
    if not cap.get('self_pidfd'):raise RuntimeError('PIDFD_REQUIRED_FOR_LIVE_MATCHES')
    events=[]
    for sig in (signal.SIGTERM,signal.SIGKILL):
        for row in scan(tag,key):
            try:fd=held_fd(row,tag,key)
            except ProcessLookupError:continue
            if fd is None:continue
            try:
                signal.pidfd_send_signal(fd,sig)
                events.append({**row,'signal':sig.name})
            except ProcessLookupError:pass
        until=time.monotonic()+grace
        while scan(tag,key) and time.monotonic()<until:time.sleep(.05)
        if not scan(tag,key):break
    return {'no_op':False,'initial':initial,'signals':events,'remaining':scan(tag,key)}

def subreaper():
    # Resolve the Linux constant from the installed ABI header, not syscall numbers.
    header=Path('/usr/include/linux/prctl.h').read_text()
    match=re.search(r'^#define\s+PR_SET_CHILD_SUBREAPER\s+(\d+)',header,re.M)
    if not match:raise RuntimeError('SUBREAPER_ABI_UNKNOWN')
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(int(match[1]),1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'prctl')

def metrics(rows):
    rss=pss=swap=readb=writeb=0;cpu=0.;details=[]
    for row in rows:
        pid=row['pid'];p=Path('/proc')/str(pid)
        try:
            st=(p/'stat').read_text();parts=st[st.rfind(')')+2:].split()
            if int(parts[19])!=row['starttime']:continue
            sm=proc_read((p/'smaps_rollup').read_text)
            vals={k:int(v)*1024 for k,v in re.findall(r'^(Rss|Pss|Swap):\s+(\d+) kB$',sm,re.M)}
            io={k:int(v) for k,v in re.findall(r'^(read_bytes|write_bytes):\s+(\d+)',proc_read((p/'io').read_text),re.M)}
            cmd=proc_read((p/'cmdline').read_bytes).replace(b'\0',b' ').decode(errors='replace')
            status=(p/'status').read_text()
            numa=(p/'numa_maps').read_text()
            pages={int(k):sum(int(n) for kk,n in re.findall(r'\bN(\d+)=(\d+)',numa) if kk==k) for k in set(re.findall(r'\bN(\d+)=',numa))}
            d={**row,**vals,'cpu_s':(int(parts[11])+int(parts[12]))/os.sysconf('SC_CLK_TCK'),
               'cpu_user_s':int(parts[11])/os.sysconf('SC_CLK_TCK'),
               'cpu_system_s':int(parts[12])/os.sysconf('SC_CLK_TCK'),
               'threads':int(re.search(r'^Threads:\s*(\d+)',status,re.M)[1]),
               'read_bytes':io.get('read_bytes',0),'write_bytes':io.get('write_bytes',0),
               'cpu_allowed':re.search(r'^Cpus_allowed_list:\s*(.+)$',status,re.M)[1],
               'numa_resident_pages':pages,'role':'rank' if Path(proc_read(lambda:os.readlink(p/'exe'))).name=='aspect-release' else 'launcher_or_trace'}
            details.append(d);rss+=vals.get('Rss',0);pss+=vals.get('Pss',0);swap+=vals.get('Swap',0)
            readb+=d['read_bytes'];writeb+=d['write_bytes'];cpu+=d['cpu_s']
        except OSError as e:
            if e.errno not in (errno.ENOENT,errno.ESRCH):raise
        except (TypeError,IndexError):continue
    return {'rss_bytes':rss,'pss_bytes':pss,'swap_bytes':swap,'cpu_s_observed':cpu,
            'read_bytes':readb,'write_bytes':writeb,'processes':details}

def run(config):
    global SCAN_FLOOR_TICKS,DESCENDANT_ROOT
    DESCENDANT_ROOT=os.getpid()
    case=Path(config['case']);tag=config['tag']
    # Tokens are assigned to children launched after this dedicated supervisor.
    st=Path('/proc/self/stat').read_text();SCAN_FLOOR_TICKS=int(st[st.rfind(')')+2:].split()[19])
    if scan(tag):raise RuntimeError('PREEXISTING_JOB_TOKEN')
    if not capability().get('self_pidfd'):raise RuntimeError('SAFE_TIMEOUT_UNAVAILABLE')
    subreaper()
    env={k:v for k,v in os.environ.items() if not k.startswith(('OMPI_','PMIX_','PMI_','OPAL_','ORTE_'))
         and k not in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','LD_PRELOAD','LD_LIBRARY_PATH','PYTHONPATH')}
    env.update(config['environment']);env[KEY]=tag
    write(case/'SUPERVISOR_COMMAND.json',config)
    start=time.monotonic();timedout=False;resource_abort=None;peak_rss=peak_pss=peak_swap=0;peak_by_pid={};sample_count=0
    with (case/'STDOUT.txt').open('x') as so,(case/'STDERR.txt').open('x') as se,(case/'PROCESS_SAMPLES.jsonl').open('x') as samples:
        proc=subprocess.Popen(['/usr/bin/time','-v','-o',str(case/'TIME.txt'),*config['argv']],
                    cwd=case,env=env,stdout=so,stderr=se,start_new_session=True)
        while True:
            rc=proc.poll();rows=scan(tag)
            for row in rows:
                try:held_fd(row,tag)
                except ProcessLookupError:continue
                except FileNotFoundError:continue
            m=metrics(rows)
            m['elapsed_s']=time.monotonic()-start;samples.write(json.dumps(m)+'\n');samples.flush();sample_count+=1
            peak_rss=max(peak_rss,m['rss_bytes']);peak_pss=max(peak_pss,m['pss_bytes']);peak_swap=max(peak_swap,m['swap_bytes'])
            for d in m['processes']:
                old=peak_by_pid.get(str(d['pid']))
                if old is None or d.get('Pss',0)>old.get('Pss',0):peak_by_pid[str(d['pid'])]=d
            if rc is not None:break
            if m['pss_bytes']>config['aggregate_pss_abort_bytes']:resource_abort='PSS_BUDGET';break
            if m['swap_bytes']>64*1024**2:resource_abort='JOB_SWAP';break
            avail=int(re.search(r'^MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text(),re.M)[1])*1024
            if avail<config['host_available_floor_bytes']:resource_abort='HOST_HEADROOM';break
            if time.monotonic()-start>config['timeout_s']:timedout=True;break
            time.sleep(config.get('sample_interval_s',.25))
        leftovers=scan(tag)
        recovery=cleanup(tag) if leftovers else {'no_op':True,'initial':[],'signals':[],'remaining':[]}
        native_rc=proc.wait(timeout=10)
    # Reap orphaned descendants adopted by this dedicated supervisor.
    reaped=[]
    while True:
        try:
            pid,status=os.waitpid(-1,os.WNOHANG)
            if pid==0:break
            reaped.append({'pid':pid,'status':status})
        except ChildProcessError:break
    remaining=scan(tag)
    rc=124 if timedout else 126 if resource_abort else 125 if recovery['signals'] and native_rc==0 else native_rc
    result={'exit_code':rc,'launcher_exit_code':native_rc,'timeout':timedout,'resource_abort':resource_abort,
            'wall_s':time.monotonic()-start,'cleanup':recovery,'remaining':remaining,'reaped':reaped,
            'sample_interval_s':config.get('sample_interval_s',.25),'sample_count':sample_count,
            'peak_aggregate_rss_observed_bytes':peak_rss,'peak_aggregate_pss_observed_bytes':peak_pss,
            'peak_aggregate_swap_observed_bytes':peak_swap,'per_process_peak_pss_samples':peak_by_pid,
            'memory_metric':'sampled PSS sum, not a cgroup limit; short peaks may be missed; RSS double-counts shared pages',
            'supervisor_capability':capability()}
    result['retained_pidfd_count']=len(HELD_PIDFDS)
    result['pidfd_lifetime']='first reliable observation through final cleanup; descriptors closed at supervisor exit'
    write(case/'RUN_EXIT.json',result)
    if remaining:raise RuntimeError('JOB_REMAINS_LIVE')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path);ap.add_argument('--cleanup-tag');ap.add_argument('--key',default=KEY);ap.add_argument('--output',type=Path)
    ap.add_argument('--not-before-ticks',type=int,default=0)
    a=ap.parse_args()
    global SCAN_FLOOR_TICKS
    SCAN_FLOOR_TICKS=a.not_before_ticks
    if a.run:
        config=json.loads(a.run.read_text())
        try:result=run(config)
        except BaseException as error:
            # A monitor/parser failure must never abandon its launched descendants.
            recovery=cleanup(config['tag'])
            write(Path(config['case'])/'SUPERVISOR_FAILURE.json',{'error':repr(error),'cleanup':recovery})
            raise
    else:
        result=cleanup(a.cleanup_tag,a.key)
        if a.output:write(a.output,result)
    print(json.dumps(result));return 0 if not result.get('remaining') else 2
if __name__=='__main__':
    try:raise SystemExit(main())
    finally:close_held()
