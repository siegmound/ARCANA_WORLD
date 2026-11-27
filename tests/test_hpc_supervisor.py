"""Real subprocess tests for pidfd supervision, including detached children."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import uuid
import pytest

SCRIPT=Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1/arcana_hpc_supervisor.py'
SYSTEM='/usr/bin/python3'

def run_job(tmp_path,program,timeout=1.):
    tag=hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    cfg={'case':str(tmp_path),'tag':tag,'argv':[SYSTEM,'-c',program],'environment':{},
         'timeout_s':timeout,'aggregate_pss_abort_bytes':2*1024**3,
         'host_available_floor_bytes':64*1024**3,'sample_interval_s':.05}
    p=tmp_path/'config.json';p.write_text(json.dumps(cfg))
    subprocess.run([SYSTEM,str(SCRIPT),'--run',str(p)],check=True,capture_output=True,text=True,timeout=20)
    return json.loads((tmp_path/'RUN_EXIT.json').read_text())

def test_clean_child(tmp_path):
    r=run_job(tmp_path,'print("ok")')
    assert r['exit_code']==0 and not r['remaining'] and not r['cleanup']['signals']

def test_timeout_and_detached_child(tmp_path):
    code='import subprocess,time; subprocess.Popen(["/usr/bin/python3","-c","import time;time.sleep(60)"],start_new_session=True); time.sleep(60)'
    r=run_job(tmp_path,code,.4)
    assert r['exit_code']==124 and r['cleanup']['signals'] and not r['remaining']

def test_orphan_is_not_false_success(tmp_path):
    code='import subprocess; subprocess.Popen(["/usr/bin/python3","-c","import time;time.sleep(60)"],start_new_session=True)'
    r=run_job(tmp_path,code,2.)
    assert r['exit_code']==125 and r['cleanup']['signals'] and not r['remaining']

def test_unrelated_process_is_untouched(tmp_path):
    p=subprocess.Popen([SYSTEM,'-c','import time;time.sleep(20)'])
    try:
        r=run_job(tmp_path,'import time;time.sleep(60)',.3)
        assert r['exit_code']==124 and p.poll() is None
    finally:p.terminate();p.wait()

def test_no_match_needs_no_pidfd(monkeypatch):
    spec=importlib.util.spec_from_file_location('supervisor',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'scan',lambda *args:[])
    monkeypatch.setattr(m,'capability',lambda: (_ for _ in ()).throw(AssertionError('must not probe')))
    assert m.cleanup('a'*64)['no_op']

def test_live_match_without_support_is_blocked(monkeypatch):
    spec=importlib.util.spec_from_file_location('supervisor2',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'scan',lambda *args:[{'pid':123,'starttime':456}])
    monkeypatch.setattr(m,'capability',lambda:{'self_pidfd':False})
    with pytest.raises(RuntimeError,match='PIDFD_REQUIRED'):m.cleanup('b'*64)
