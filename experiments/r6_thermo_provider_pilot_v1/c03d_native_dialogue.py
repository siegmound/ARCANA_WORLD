"""Bounded, prompt-driven MEEMUM initialization; never request a nonzero PT.
Only two explicitly identified HP02 O2 EoS warnings may be acknowledged.
No global warning override. Raw stdout and actual stdin are retained.
"""
from __future__ import annotations
import json
import os
import re
import resource
import selectors
import signal
import subprocess
import time

PROJECT=b"Enter the project name (the name assigned in BUILD) [default = my_project]:"
WARNING=b"Continue execution despite this warning (Y/N)?"
BULK=b"Interactively enter bulk compositions (y/n)?"
PT=b"Enter (T = 0 to quit)"
PROMPTS=(PROJECT,WARNING,BULK,PT)
POLICY="HP02_O2_VER966_AND_CONDITIONAL_VER968_INITIALIZATION_ONLY"


class Dialogue:
    def __init__(self):
        self.state="PROJECT"
        self.cursor=0
        self.acknowledged=[]
        self.events=[]

    def next_response(self,raw):
        """Consume exactly one observed prompt; never guess the next one."""
        tail=raw[self.cursor:]
        fatal=re.search(rb"\*\*error ver\d+\*\*[^\n]*",tail,re.I)
        if fatal:
            raise ValueError("C03D_NATIVE_FATAL:"+fatal.group().decode("ascii",errors="replace"))
        hits=[(tail.find(p),p) for p in PROMPTS if p in tail]
        if not hits:
            return None
        pos,prompt=min(hits,key=lambda x:x[0])
        context=tail[:pos]
        if prompt==PROJECT and self.state=="PROJECT":
            response=b"c03d\n"
            self.state="INITIALIZING"
            kind="PROJECT"
        elif prompt==WARNING and self.state=="INITIALIZING":
            marks=list(re.finditer(rb"\*\*warning ver(\d+)\*\*",context,re.I))
            block=context[marks[-1].start():] if marks else b""
            flat=b" ".join(block.split())
            code=marks[-1][1].decode("ascii") if marks else ""
            valid966=(code=="966" and not self.acknowledged
                and b"EoS code 1 for O2 in data file hp02ver.dat requires" in flat
                and b"volumetric data" in flat and b"automatically be set to 0" in flat)
            valid968=(code=="968" and self.acknowledged==["966"]
                and b"O2 is a name reserved for fluid" in flat
                and b"hp02ver.dat" in flat and b"G(Pr,T)" in flat
                and b"activity or fugacity of O2" in flat)
            if not (valid966 or valid968):
                raise ValueError("C03D_UNAPPROVED_INTERACTIVE_WARNING:"+flat[-500:].decode("ascii",errors="replace"))
            self.acknowledged.append(code)
            response=b"y\n"
            kind="HP02_O2_VER"+code
        elif prompt==BULK and self.state=="INITIALIZING":
            response=b"n\n"
            self.state="AWAIT_PT"
            kind="FIXED_BULK"
        elif prompt==PT and self.state=="AWAIT_PT":
            response=b"0 0\n"
            self.state="SENTINEL_SENT"
            kind="ZERO_PT_SENTINEL"
        else:
            raise ValueError("C03D_UNEXPECTED_PROMPT:"+self.state+":"+prompt.decode())
        self.cursor+=pos+len(prompt)
        self.events.append({"prompt":kind,"response":response.decode().strip(),
                            "stdout_byte_offset_after_prompt":self.cursor})
        return response


def launch_dialogue(command,work,limits):
    def set_limits():
        resource.setrlimit(resource.RLIMIT_AS,(limits["address_space_limit_bytes"],)*2)
        resource.setrlimit(resource.RLIMIT_FSIZE,(limits["file_size_limit_bytes"],)*2)
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))

    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1",
             BLIS_NUM_THREADS="1",LC_ALL="C",GFORTRAN_UNBUFFERED_ALL="1")
    start=time.monotonic()
    deadline=start+limits["walltime_s"]
    protocol=Dialogue()
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
                if status!=0 or protocol.state!="SENTINEL_SENT":
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
            "policy":POLICY,"state":protocol.state,"events":protocol.events,
            "acknowledged_warning_codes":protocol.acknowledged,"requested_equilibrium_points":0,
            "scientific_warning_acceptance":False,"error":error})):
            with (work/name).open("x") as f:
                json.dump(obj,f,indent=2,allow_nan=False)
                f.write("\n")
    return telemetry
