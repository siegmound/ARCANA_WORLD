from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from hashlib import sha256
import json, os, platform, re, shutil, subprocess, sys, shlex
from typing import Any

STAGE = "v0.6D1-R4.0"
R339_FINAL = "PASS_R339_CULTURAL_SYMBOLIC_MEMORY_DIRECT_CHA2_EVENT_MEMORY_LANGUAGE_DIVERGENCE_PRECONDITIONS_AND_INTERLINEAGE_IDENTITY_DYNAMICS_SEALED"
R40_CANDIDATE = "PASS_R40_MULTI_ENGINE_ORCHESTRATOR_CONSOLIDATION_AND_REVALIDATION_MATRIX_CANDIDATE"
R40_READY = "PASS_R40_MULTI_ENGINE_RUNTIME_READINESS"
R40_SEALED = "PASS_R40_ARCANA_MULTI_ENGINE_SCIENTIFIC_REVALIDATION_ORCHESTRATOR_AND_RUNTIME_GOVERNANCE_SEALED"


def load_json(p: str | Path) -> Any:
    return json.loads(Path(p).read_text(encoding="utf-8"))

def write_json(p: str | Path, obj: Any) -> None:
    q=Path(p); q.parent.mkdir(parents=True,exist_ok=True); q.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def sha256_file(p: str | Path) -> str:
    h=sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def _run(cmd:list[str], timeout:float=25.0, env:dict[str,str]|None=None)->dict[str,Any]:
    try:
        p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout,check=False,env=env)
        return {"returncode":p.returncode,"stdout":p.stdout[-8000:],"stderr":p.stderr[-8000:]}
    except FileNotFoundError as e:
        return {"returncode":127,"stdout":"","stderr":str(e)}
    except subprocess.TimeoutExpired as e:
        return {"returncode":124,"stdout":str(e.stdout or "")[-8000:],"stderr":"TIMEOUT "+str(e.stderr or "")[-8000:]}
    except Exception as e:
        return {"returncode":125,"stdout":"","stderr":repr(e)}

def _version_tuple(s:str)->tuple[int,...]:
    m=re.search(r"(\d+(?:\.\d+){1,3})",s)
    return tuple(map(int,m.group(1).split('.'))) if m else ()

def _v_ge(found:str, minimum:str)->bool:
    a=_version_tuple(found); b=_version_tuple(minimum)
    if not a or not b: return False
    n=max(len(a),len(b)); return a+(0,)*(n-len(a)) >= b+(0,)*(n-len(b))

@dataclass
class ProbeResult:
    engine:str; expected_version:str; status:str; confirmed_version:str|None; invocation:str|None
    details:str; returncode:int|None=None
    def to_dict(self): return asdict(self)

def _python_probe(python_exe:str, package:str)->dict[str,Any]:
    code=("import importlib,importlib.metadata as m; "
          f"x=importlib.import_module('{package}'); "
          f"print(m.version('{package}'))")
    return _run([python_exe,"-c",code])

def _wsl_exe()->str|None:
    # Prefer an explicit binding written by the R4.0 provisioner.  On some
    # Windows Python installations shutil.which('wsl.exe') can fail even when
    # PowerShell can invoke WSL successfully, so do not make runtime discovery
    # depend on PATH semantics alone.
    override=os.environ.get('ARCANA_WSL_EXE')
    if override:
        q=Path(os.path.expandvars(override))
        if q.exists(): return str(q)
        # Also permit a command-style override such as `wsl.exe`.
        found=shutil.which(override)
        if found: return found
    for name in ('wsl.exe','wsl'):
        found=shutil.which(name)
        if found: return found
    if os.name=='nt':
        windir=os.environ.get('WINDIR') or os.environ.get('SystemRoot') or r'C:\\Windows'
        for rel in (('System32','wsl.exe'),('Sysnative','wsl.exe')):
            q=Path(windir).joinpath(*rel)
            if q.exists(): return str(q)
        q=Path(r'C:\\Windows\\System32\\wsl.exe')
        if q.exists(): return str(q)
    return None

def _wsl_run(script:str, timeout:float=60.0)->dict[str,Any]:
    exe=_wsl_exe()
    if not exe: return {"returncode":127,"stdout":"","stderr":"WSL not found"}
    return _run([exe,'bash','-lc',script],timeout=timeout)

def _wsl_conda_prefix()->str:
    override=os.environ.get('ARCANA_WSL_CONDA')
    if override:
        q=shlex.quote(override)
        return f'''CONDA_EXE={q}; if ! command -v "$CONDA_EXE" >/dev/null 2>&1 && [ ! -x "$CONDA_EXE" ]; then exit 127; fi;'''
    return r'''CONDA_EXE="$(command -v conda 2>/dev/null || true)"; if [ -z "$CONDA_EXE" ]; then for p in "$HOME/miniforge3/bin/conda" "$HOME/mambaforge/bin/conda" "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda"; do if [ -x "$p" ]; then CONDA_EXE="$p"; break; fi; done; fi; [ -n "$CONDA_EXE" ] || exit 127;'''

def _wsl_conda_run(env_name:str,args:list[str],timeout:float=60.0)->dict[str,Any]:
    cmd=' '.join(shlex.quote(x) for x in args)
    script=_wsl_conda_prefix()+f' "$CONDA_EXE" run -n {shlex.quote(env_name)} {cmd}'
    return _wsl_run(script,timeout=timeout)

def probe_nemo()->ProbeResult:
    override=os.environ.get("ARCANA_NEMO_EXECUTABLE")
    if override:
        r=_run([override,"--version"]); txt=(r['stdout']+'\n'+r['stderr']); ok='2.4.2' in txt
        return ProbeResult('NEMO','2.4.2','READY' if ok else 'VERSION_MISMATCH',_version_text(txt),override,txt.strip(),r['returncode'])
    if _wsl_exe():
        names=[]
        if os.environ.get('ARCANA_NEMO_CONDA_ENV'): names.append(os.environ['ARCANA_NEMO_CONDA_ENV'])
        names += ['arcana-nemo242','nemo']
        for env_name in dict.fromkeys(names):
            r=_wsl_conda_run(env_name,['nemo2.4.2'],timeout=30); txt=r['stdout']+'\n'+r['stderr']
            if '2.4.2' in txt:
                return ProbeResult('NEMO','2.4.2','READY','2.4.2',f'WSL conda:{env_name}/nemo2.4.2',txt.strip(),r['returncode'])
        script="command -v nemo2.4.2 >/dev/null 2>&1 || exit 127; nemo2.4.2 2>&1 | head -n 12"
        r=_wsl_run(script,timeout=30); txt=r['stdout']+'\n'+r['stderr']; ok='2.4.2' in txt
        if ok: return ProbeResult('NEMO','2.4.2','READY','2.4.2','WSL PATH:nemo2.4.2',txt.strip(),r['returncode'])
    for name in ('nemo2.4.2','nemo2','nemo'):
        if shutil.which(name):
            r=_run([name]); txt=r['stdout']+'\n'+r['stderr']; ok='2.4.2' in txt
            return ProbeResult('NEMO','2.4.2','READY' if ok else 'VERSION_MISMATCH',_version_text(txt),name,txt.strip(),r['returncode'])
    return ProbeResult('NEMO','2.4.2','MISSING',None,None,'NEMO 2.4.2 not found; checked native PATH and WSL conda envs arcana-nemo242/nemo')

def _version_text(txt:str)->str|None:
    m=re.search(r"\b(\d+(?:\.\d+){1,3})\b",txt)
    return m.group(1) if m else None

def probe_geonomics(root:Path)->ProbeResult:
    candidates=[]
    if os.environ.get('ARCANA_GEONOMICS_PYTHON'): candidates.append(os.environ['ARCANA_GEONOMICS_PYTHON'])
    candidates += [str(root/'.arcana_engines/geonomics-1.4.9/.venv/Scripts/python.exe'), str(root/'.arcana_engines/geonomics-1.4.9/.venv/bin/python'), sys.executable]
    for py in candidates:
        if py==sys.executable or Path(py).exists():
            r=_python_probe(py,'geonomics')
            if r['returncode']==0:
                v=r['stdout'].strip().splitlines()[-1]; ok=v=='1.4.9'
                return ProbeResult('Geonomics','1.4.9','READY' if ok else 'VERSION_MISMATCH',v,py,(r['stdout']+'\n'+r['stderr']).strip(),r['returncode'])
    if _wsl_exe():
        env_name=os.environ.get('ARCANA_GEONOMICS_CONDA_ENV','arcana-geonomics-149')
        code="import importlib.metadata as m, geonomics; print(m.version('geonomics'))"
        r=_wsl_conda_run(env_name,['python','-c',code],timeout=45)
        if r['returncode']==0:
            v=r['stdout'].strip().splitlines()[-1]; ok=v=='1.4.9'
            return ProbeResult('Geonomics','1.4.9','READY' if ok else 'VERSION_MISMATCH',v,f'WSL conda:{env_name}/python',(r['stdout']+'\n'+r['stderr']).strip(),r['returncode'])
    return ProbeResult('Geonomics','1.4.9','MISSING',None,None,'geonomics==1.4.9 not importable in native or governed WSL environment')

def _rscript()->str|None:
    return os.environ.get('ARCANA_RSCRIPT') or shutil.which('Rscript.exe') or shutil.which('Rscript')

def _r_probe(code:str,timeout:float=90.0)->tuple[dict[str,Any],str]:
    rs=_rscript()
    if rs:
        return _run([rs,'-e',code],timeout=timeout),rs
    if _wsl_exe():
        env_name=os.environ.get('ARCANA_R40_R_CONDA_ENV','arcana-r40-r')
        # R packages such as MadingleyR launch bundled C++ executables.  Under
        # WSL `conda run` those child executables may not see the environment's
        # runtime libraries (notably libgomp.so.1).  Execute R through a tiny
        # governed shell wrapper that exports CONDA_PREFIX/lib explicitly.
        shell_code=(
            'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; '
            f'exec Rscript -e {shlex.quote(code)}'
        )
        return _wsl_conda_run(env_name,['bash','-lc',shell_code],timeout=timeout),f'WSL conda:{env_name}/Rscript+runtime-libs'
    return {"returncode":127,"stdout":"","stderr":"Rscript not found"},'Rscript'

def probe_madingley()->ProbeResult:
    code="if(!requireNamespace('MadingleyR',quietly=TRUE)) quit(status=12); library(MadingleyR); v<-capture.output(madingley_version()); cat(as.character(utils::packageVersion('MadingleyR')),'|',paste(v,collapse=' '),'\\n')"
    r,inv=_r_probe(code,timeout=120); txt=r['stdout']+'\n'+r['stderr']
    ok=r['returncode']==0 and '1.0.6' in txt and '2.02' in txt.replace(' ','')
    return ProbeResult('Madingley','MadingleyR-1.0.6__CPP-2.02','READY' if ok else ('MISSING' if r['returncode'] in {12,127} else 'VERSION_MISMATCH'),_version_text(txt),inv,txt.strip(),r['returncode'])

def probe_rangeshifter()->ProbeResult:
    code="if(!requireNamespace('RangeShiftR',quietly=TRUE)) quit(status=12); cat(as.character(utils::packageVersion('RangeShiftR')),'\\n')"
    r,inv=_r_probe(code,timeout=120); txt=r['stdout']+'\n'+r['stderr']; v=_version_text(txt); ok=r['returncode']==0 and v == '3.0.1'
    return ProbeResult('RangeShifter','3.0.1','READY' if ok else ('MISSING' if r['returncode'] in {12,127} else 'VERSION_MISMATCH'),v,inv,txt.strip(),r['returncode'])

def probe_cdmetapop(root:Path)->ProbeResult:
    repo=os.environ.get('ARCANA_CDMETAPOP_ROOT')
    cands=[]
    if repo: cands.append(Path(repo))
    cands += [root/'.arcana_engines/CDMetaPOP-3.08', root/'.arcana_engines/CDMetaPOP']
    source=None
    for p in cands:
        if p.exists():
            hits=list(p.rglob('CDMetaPOP.py'))+list(p.rglob('CDMetaPOP_Modules.py'))
            version_text=''
            for vf in [p/'README.md',p/'README.txt',p/'doc/README.txt',p/'doc/CDmetaPOPhistory.txt']:
                if vf.exists(): version_text += vf.read_text(encoding='utf-8',errors='ignore')[:20000]
            ok=('3.08' in version_text) or any('3.08' in str(x) for x in p.rglob('*3.08*'))
            if hits and ok: source=p; break
            if hits: return ProbeResult('CDMetaPOP','3.08','VERSION_MISMATCH',_version_text(version_text),str(p),'Source found but 3.08 identity not confirmed',0)
    if source is None:
        return ProbeResult('CDMetaPOP','3.08','MISSING',None,None,'CDMetaPOP 3.08 source not found; expected .arcana_engines/CDMetaPOP-3.08')
    runtime_ok=False; runtime_detail=''; runtime_inv=''
    py=os.environ.get('ARCANA_CDMETAPOP_PYTHON')
    if py and Path(py).exists():
        r=_run([py,'-c',"import sys,numpy,scipy; print(sys.version.split()[0])"]); runtime_detail=(r['stdout']+'\n'+r['stderr']).strip(); runtime_ok=r['returncode']==0 and runtime_detail.startswith('3.8'); runtime_inv=py
    elif _wsl_exe():
        env_name=os.environ.get('ARCANA_CDMETAPOP_CONDA_ENV','arcana-cdmetapop-308')
        r=_wsl_conda_run(env_name,['python','-c',"import sys,numpy,scipy; print(sys.version.split()[0])"],timeout=45); runtime_detail=(r['stdout']+'\n'+r['stderr']).strip(); runtime_ok=r['returncode']==0 and any(x.startswith('3.8') for x in r['stdout'].splitlines()); runtime_inv=f'WSL conda:{env_name}/python'
    status='READY' if runtime_ok else 'MISSING'
    return ProbeResult('CDMetaPOP','3.08',status,'3.08' if runtime_ok else None,f'{source} + {runtime_inv or "runtime missing"}',f'source={source}; runtime={runtime_detail}',0 if runtime_ok else 127)

def probe_slim(root:Path)->ProbeResult:
    slim=os.environ.get('ARCANA_SLIM_EXECUTABLE') or shutil.which('slim.exe') or shutil.which('slim')
    py=os.environ.get('ARCANA_SLIM_PYTHON') or sys.executable
    if slim:
        r=_run([slim,'-v']); txt=r['stdout']+'\n'+r['stderr']; v=_version_text(txt)
        pkg_code="import importlib.metadata as m; print('tskit='+m.version('tskit')); print('msprime='+m.version('msprime')); print('pyslim='+m.version('pyslim'))"
        pr=_run([py,'-c',pkg_code]); ptxt=pr['stdout']+'\n'+pr['stderr']
        versions={k:v for k,v in re.findall(r'(tskit|msprime|pyslim)=([0-9.]+)',ptxt)}
        deps=(pr['returncode']==0 and _v_ge(versions.get('tskit',''),'1.0.2') and _v_ge(versions.get('msprime',''),'1.4.1') and _v_ge(versions.get('pyslim',''),'1.1.1'))
        ok=(v is not None and v.startswith('5.2') and deps)
        return ProbeResult('SLiM','5.2','READY' if ok else 'VERSION_MISMATCH',v,slim,(txt+'\n'+ptxt).strip(),r['returncode'])
    if _wsl_exe():
        env_name=os.environ.get('ARCANA_SLIM_CONDA_ENV','arcana-slim52')
        r=_wsl_conda_run(env_name,['slim','-v'],timeout=30); txt=r['stdout']+'\n'+r['stderr']; v=_version_text(txt)
        pkg_code="import importlib.metadata as m; print('tskit='+m.version('tskit')); print('msprime='+m.version('msprime')); print('pyslim='+m.version('pyslim'))"
        pr=_wsl_conda_run(env_name,['python','-c',pkg_code],timeout=30); ptxt=pr['stdout']+'\n'+pr['stderr']
        versions={k:v for k,v in re.findall(r'(tskit|msprime|pyslim)=([0-9.]+)',ptxt)}
        deps=(pr['returncode']==0 and _v_ge(versions.get('tskit',''),'1.0.2') and _v_ge(versions.get('msprime',''),'1.4.1') and _v_ge(versions.get('pyslim',''),'1.1.1'))
        ok=(v is not None and v.startswith('5.2') and deps)
        status='READY' if ok else ('MISSING' if r['returncode']==127 else 'VERSION_MISMATCH')
        return ProbeResult('SLiM','5.2',status,v,f'WSL conda:{env_name}/slim',(txt+'\n'+ptxt).strip(),r['returncode'])
    return ProbeResult('SLiM','5.2','MISSING',None,None,'SLiM 5.2 executable/toolchain not found')

def validate_parents(root:Path)->dict[str,Any]:
    bridge=root/'configs/world1_scientific_engine_bridge_v0_6D1_R3_6A.json'
    if not bridge.exists(): raise FileNotFoundError(bridge)
    b=load_json(bridge)
    if b.get('canonical_state_owner')!='ARCANA_WorldSim' or b.get('external_engine_direct_canonical_write') is not False:
        raise ValueError('R3.6A scientific-engine governance mismatch')
    seal=root/'outputs/v0_6D1_R3_39_SEAL/R3_39_FINAL_SEAL_AUDIT.json'
    if not seal.exists(): raise FileNotFoundError(seal)
    s=load_json(seal)
    if s.get('status')!=R339_FINAL or s.get('verdict')!='SEALED': raise ValueError('R3.39 final seal mismatch')
    return {'r36a_bridge':bridge,'r36a':b,'r339_seal':seal,'r339':s}

def _host_runtime_evidence_path(root:Path)->Path:
    override=os.environ.get("ARCANA_R40_HOST_RUNTIME_EVIDENCE")
    return Path(override) if override else root/"outputs/v0_6D1_R4_0/R4_0_HOST_RUNTIME_EVIDENCE.json"

def _probes_from_host_runtime_evidence(root:Path,cfg:dict[str,Any])->list[ProbeResult]|None:
    p=_host_runtime_evidence_path(root)
    if not p.exists(): return None
    try:
        evidence=load_json(p)
    except Exception:
        return None
    if evidence.get("stage")!=STAGE or evidence.get("evidence_type")!="HOST_RUNTIME_IDENTITY_EVIDENCE" or evidence.get("generated_by")!="capture_v0_6D1_R4_0_runtime_evidence.ps1":
        return None
    try:
        if Path(evidence.get("root","")).resolve()!=root.resolve(): return None
    except Exception:
        return None
    rows=evidence.get("engines")
    if not isinstance(rows,list): return None
    by_engine={x.get("engine"):x for x in rows if isinstance(x,dict) and x.get("engine")}
    out=[]
    for engine in cfg["required_engines_for_r40_seal"]:
        expected=cfg["engines"][engine]["version"]
        x=by_engine.get(engine)
        if not x:
            out.append(ProbeResult(engine,expected,"MISSING",None,None,f"Fresh host runtime evidence missing engine {engine}",127)); continue
        confirmed=x.get("confirmed_version")
        status=x.get("status")
        exact_ok=(status=="READY" and x.get("expected_version")==expected and confirmed==expected)
        if engine=="Madingley": exact_ok=(status=="READY" and confirmed=="MadingleyR-1.0.6__CPP-2.02" and expected==confirmed)
        normalized="READY" if exact_ok else ("VERSION_MISMATCH" if status=="READY" else "PROBE_FAILED")
        detail=(str(x.get("stdout") or "")+"\n"+str(x.get("stderr") or "")).strip()
        out.append(ProbeResult(engine,expected,normalized,confirmed if exact_ok else confirmed,x.get("invocation"),detail,x.get("returncode")))
    return out

def probe_all(root:Path,cfg:dict[str,Any]|None=None)->list[ProbeResult]:
    if cfg is not None:
        bridged=_probes_from_host_runtime_evidence(root,cfg)
        if bridged is not None:
            return bridged
    return [probe_nemo(),probe_geonomics(root),probe_madingley(),probe_rangeshifter(),probe_cdmetapop(root),probe_slim(root)]

def build_matrix(cfg:dict[str,Any])->dict[str,Any]:
    windows=[]
    for w in cfg['frozen_revalidation_windows']:
        windows.append({**w,'status':'FROZEN_PRE_RESULT','selection_based_on_result':False})
    return {'stage':STAGE,'status':'R40_FROZEN_REVALIDATION_MATRIX','window_count':len(windows),'windows':windows,'comparison_domains':cfg['comparison_domains'],'decision_policy':cfg['decision_policy']}

def provisioning_actions(probes:list[ProbeResult])->list[dict[str,str]]:
    out=[]
    for p in probes:
        if p.status=='READY': continue
        if p.engine=='NEMO': action='Provision/check WSL conda env `arcana-nemo242` with NEMO 2.4.2; R4.0 now probes it directly.'
        elif p.engine=='Geonomics': action='Provision WSL conda env `arcana-geonomics-149` (or native isolated Python) with geonomics==1.4.9.'
        elif p.engine=='Madingley': action='Provision governed R runtime `arcana-r40-r` with MadingleyR 1.0.6 / C++ 2.02 (native Rscript also supported).'
        elif p.engine=='RangeShifter': action='Provision governed R runtime `arcana-r40-r` with RangeShiftR 3.0.1 @ d01f1b6 (native Rscript also supported).'
        elif p.engine=='CDMetaPOP': action='Provision CDMetaPOP 3.08 source pinned to commit 3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118 plus WSL Python 3.8 env `arcana-cdmetapop-308`.'
        else: action='Provision WSL conda env `arcana-slim52` with SLiM 5.2 + tskit>=1.0.2 + msprime>=1.4.1 + pyslim>=1.1.1 (native runtime also supported).'
        out.append({'engine':p.engine,'status':p.status,'action':action})
    return out

def run_inventory(root:Path,cfg:dict[str,Any])->dict[str,Any]:
    parents=validate_parents(root); probes=probe_all(root,cfg); matrix=build_matrix(cfg)
    required=set(cfg['required_engines_for_r40_seal']); ready={p.engine for p in probes if p.status=='READY'}
    all_ready=required <= ready
    return {
        'stage':STAGE,'status':R40_READY if all_ready else R40_CANDIDATE,
        'canonical_state_owner':'ARCANA_WorldSim','external_engine_direct_canonical_write':False,
        'parent_hashes':{'r36a_bridge_sha256':sha256_file(parents['r36a_bridge']),'r339_final_seal_sha256':sha256_file(parents['r339_seal'])},
        'host':{'platform':platform.platform(),'python':sys.version.split()[0],'machine':platform.machine()},
        'required_engines':sorted(required),'ready_engines':sorted(ready),'all_required_ready':all_ready,
        'engine_probes':[p.to_dict() for p in probes],'provisioning_actions':provisioning_actions(probes),
        'revalidation_matrix':matrix,
        'baseline_semantics':'R3.19-R3.39 preserved as ARCANA_REDUCED_ORDER_BASELINE_A; no result promoted by this inventory',
        'deep_biological_coupling':False,
    }

def integrated_checks(report:dict[str,Any],cfg:dict[str,Any])->list[dict[str,Any]]:
    probes={p['engine']:p for p in report['engine_probes']}; checks=[]
    def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
    ck('canonical_owner_arcana',report['canonical_state_owner']=='ARCANA_WorldSim')
    ck('no_external_direct_write',report['external_engine_direct_canonical_write'] is False)
    ck('deep_off',report['deep_biological_coupling'] is False)
    ck('engine_count_6',len(probes)==6)
    ck('nemo_pin',probes['NEMO']['expected_version']=='2.4.2')
    ck('geonomics_pin',probes['Geonomics']['expected_version']=='1.4.9')
    ck('madingley_pin',probes['Madingley']['expected_version']=='MadingleyR-1.0.6__CPP-2.02')
    ck('rangeshifter_pin',probes['RangeShifter']['expected_version']=='3.0.1')
    ck('cdmetapop_pin',probes['CDMetaPOP']['expected_version']=='3.08')
    ck('slim_pin',probes['SLiM']['expected_version']=='5.2')
    ck('window_count_7',report['revalidation_matrix']['window_count']==7)
    ck('windows_pre_result',all(w['selection_based_on_result'] is False for w in report['revalidation_matrix']['windows']))
    ck('comparison_domains_frozen',report['revalidation_matrix']['comparison_domains']==cfg['comparison_domains'])
    ck('no_auto_promotion',cfg['decision_policy']['no_auto_promotion'] is True)
    ck('preserve_old_seals',cfg['decision_policy']['preserve_superseded_seals_as_provenance'] is True)
    ck('parent_hashes_present',all(len(v)==64 for v in report['parent_hashes'].values()))
    ck('runtime_status_enum',all(p['status'] in {'READY','MISSING','VERSION_MISMATCH','PROBE_FAILED'} for p in probes.values()))
    return checks
