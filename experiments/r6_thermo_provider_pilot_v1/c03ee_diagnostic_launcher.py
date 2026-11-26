"""Bounded C03EE diagnostic launcher; separate from immutable zero-PT launcher."""
import json
import os
import resource
import selectors
import signal
import subprocess
import time

def launch_dialogue(command,work,limits,*,protocol_factory):
    def set_limits():
        resource.setrlimit(resource.RLIMIT_AS,(limits["address_space_limit_bytes"],)*2)
        resource.setrlimit(resource.RLIMIT_FSIZE,(limits["file_size_limit_bytes"],)*2)
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))

    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1",
             BLIS_NUM_THREADS="1",LC_ALL="C",GFORTRAN_UNBUFFERED_ALL="1")
    start=time.monotonic()
    deadline=start+limits["walltime_s"]
    protocol=protocol_factory()
    raw=bytearray()
    proc=None
    error=None
    timeout=False
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        with (work/"RUN_STDOUT.log").open("xb") as out, (work/"DIALOGUE_STDIN.log").open("xb") as sent:
            proc=subprocess.Popen([str(x) for x in command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,cwd=work,env=env,start_new_session=True,preexec_fn=set_limits)
            with selectors.DefaultSelector() as sel:
                sel.register(proc.stdout,selectors.EVENT_READ)
                while True:
                    left=deadline-time.monotonic()
                    if left<=0 or not sel.select(left):
                        timeout=True
                        raise TimeoutError("C03D_DIALOGUE_TIMEOUT:"+protocol.state)
                    chunk=os.read(proc.stdout.fileno(),65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    out.flush()
                    raw.extend(chunk)
                    if len(raw)>limits["file_size_limit_bytes"]:
                        raise ValueError("C03D_DIALOGUE_STDOUT_LIMIT")
                    while True:
                        response=protocol.next_response(bytes(raw))
                        if response is None:
                            break
                        proc.stdin.write(response)
                        proc.stdin.flush()
                        sent.write(response)
                        sent.flush()
                        if protocol.state=="SENTINEL_SENT":
                            proc.stdin.close()
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    timeout=True
                    raise TimeoutError("C03D_DIALOGUE_EXIT_TIMEOUT")
                status=proc.wait(timeout=remaining)
                if status!=0 or protocol.state!="SENTINEL_SENT" or len(protocol.completed)!=len(protocol.points):
                    raise ValueError("C03D_DIALOGUE_INCOMPLETE:"+protocol.state+":"+str(status))
    except BaseException as exc:
        error=type(exc).__name__+": "+str(exc)
        timeout=timeout or isinstance(exc,(TimeoutError,subprocess.TimeoutExpired))
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
        raise
    finally:
        if proc is not None:
            if proc.stdin is not None and not proc.stdin.closed:
                proc.stdin.close()
            if proc.stdout is not None:
                proc.stdout.close()
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        telemetry={"pid":proc.pid if proc else None,"exit_code":proc.returncode if proc else None,
                   "timeout":timeout,"wall_s":time.monotonic()-start,"error":error,
                   "children_cumulative_maxrss_KiB":after.ru_maxrss,
                   "child_user_cpu_s":after.ru_utime-before.ru_utime,
                   "child_system_cpu_s":after.ru_stime-before.ru_stime,
                   "address_space_limit_bytes":limits["address_space_limit_bytes"],
                   "individual_file_size_limit_bytes":limits["file_size_limit_bytes"]}
        for name,obj in (("LAUNCH.json",telemetry),("DIALOGUE.json",{
            "policy":protocol.policy,"state":protocol.state,"events":protocol.events,
            "acknowledged_warning_codes":protocol.acknowledged,"requested_equilibrium_points":len(protocol.requested),
            "completed_equilibrium_points":len(protocol.completed),
            "requested_ids":protocol.requested,"completed_ids":[x["id"] for x in protocol.completed],
            "scientific_warning_acceptance":False,"error":error})):
            with (work/name).open("x") as f:
                json.dump(obj,f,indent=2,allow_nan=False)
                f.write("\n")
    return telemetry
