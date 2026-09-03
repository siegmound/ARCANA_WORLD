from pathlib import Path
import json
from arcana_worldsim.scientific_engines import r40_multi_engine_orchestrator as r

def cfg():
 p=Path(__file__).resolve().parents[1]/'configs/world1_r40_multi_engine_revalidation_v0_6D1_R4_0.json'
 return json.loads(p.read_text())

def test_engine_pins_exact():
 c=cfg()['engines']; assert c['NEMO']['version']=='2.4.2'; assert c['Geonomics']['version']=='1.4.9'; assert c['Madingley']['version']=='MadingleyR-1.0.6__CPP-2.02'; assert c['RangeShifter']['version']=='3.0.1'; assert c['CDMetaPOP']['version']=='3.08'; assert c['SLiM']['version']=='5.2'
def test_arcana_owns_canon(): assert cfg()['canonical_state_owner']=='ARCANA_WorldSim' and cfg()['external_engine_direct_canonical_write'] is False
def test_deep_off(): assert cfg()['deep_biological_coupling'] is False
def test_six_required_engines(): assert len(cfg()['required_engines_for_r40_seal'])==6
def test_seven_frozen_windows(): assert len(cfg()['frozen_revalidation_windows'])==7
def test_no_result_conditioned_window_selection(): assert all('result' not in json.dumps(x).lower() for x in cfg()['frozen_revalidation_windows'])
def test_h0_window_present(): assert cfg()['frozen_revalidation_windows'][0]['age_start_ma']==210.0
def test_cha1_not_ordinary_global_step(): assert any(x['id']=='H0_PRE_CHA1' for x in cfg()['frozen_revalidation_windows']) and any(x['id']=='H0_POST_CHA1_RECOVERY' for x in cfg()['frozen_revalidation_windows'])
def test_sapient_revalidation_uses_three_spatial_genetic_oracles():
 x=next(x for x in cfg()['frozen_revalidation_windows'] if x['id']=='SAPIENT_200KA_TO_0'); assert {'Geonomics','SLiM','CDMetaPOP'} <= set(x['engines'])
def test_producer_revalidation_present(): assert any(x['id']=='PRODUCER_20KA_TO_0' for x in cfg()['frozen_revalidation_windows'])
def test_no_auto_promotion(): assert cfg()['decision_policy']['no_auto_promotion'] is True
def test_preserve_old_seals(): assert cfg()['decision_policy']['preserve_superseded_seals_as_provenance'] is True
def test_version_parser(): assert r._version_tuple('v5.2')==(5,2) and r._v_ge('1.4.1','1.4.1') and r._v_ge('1.4.2','1.4.1')
def test_probe_status_dataclass(): assert r.ProbeResult('x','1','MISSING',None,None,'x').to_dict()['status']=='MISSING'
def test_matrix_is_preresult(): assert all(x['selection_based_on_result'] is False for x in r.build_matrix(cfg())['windows'])
def test_comparison_domains_include_ecology_and_genetics():
 d=set(cfg()['comparison_domains']); assert {'biomass','trophic_opportunity','gene_flow','additive_variance','ancestry'} <= d
def test_slim_minimums(): assert cfg()['engines']['SLiM']['python_minimums']=={'tskit':'1.0.2','msprime':'1.4.1','pyslim':'1.1.1'}
def test_nemo_bad_versions_not_pinned(): assert cfg()['engines']['NEMO']['version'] not in {'2.4.0','2.4.1'}
def test_r40_seal_status_distinct_from_candidate(): assert r.R40_SEALED != r.R40_CANDIDATE != r.R40_READY
def test_runtime_probe_enum_contract(): assert {'READY','MISSING','VERSION_MISMATCH','PROBE_FAILED'}=={'READY','MISSING','VERSION_MISMATCH','PROBE_FAILED'}

def test_governed_wsl_env_names_frozen():
    e=cfg()['engines']
    assert e['NEMO']['provisioning']['conda_env']=='arcana-nemo242'
    assert e['Geonomics']['provisioning']['conda_env']=='arcana-geonomics-149'
    assert e['Madingley']['provisioning']['conda_env']=='arcana-r40-r'
    assert e['RangeShifter']['provisioning']['conda_env']=='arcana-r40-r'
    assert e['CDMetaPOP']['provisioning']['conda_env']=='arcana-cdmetapop-308'
    assert e['SLiM']['provisioning']['conda_env']=='arcana-slim52'

def test_cdmetapop_308_source_commit_frozen():
    assert cfg()['engines']['CDMetaPOP']['provisioning']['source_commit']=='3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'

def test_wsl_conda_fallback_contract_present():
    x=r._wsl_conda_prefix()
    assert 'miniconda3/bin/conda' in x and 'miniforge3/bin/conda' in x


def test_provisioning_wsl_discovery_is_null_safe_and_no_wslpath_dependency():
    root=Path(__file__).resolve().parents[1]
    text=(root/'provision_v0_6D1_R4_0_engines.ps1').read_text(encoding='utf-8')
    assert 'Invoke-WslCaptureFirstLine' in text
    assert '$lines = @(& wsl.exe bash -lc $Command' in text
    assert '(& wsl.exe bash -lc $FindConda).Trim()' not in text
    assert 'wsl.exe wslpath' not in text
    assert 'find "$base" -maxdepth 6' in text

def test_provisioning_conda_env_detection_uses_runnable_probe_not_text_parsing():
    root=Path(__file__).resolve().parents[1]
    text=(root/'provision_v0_6D1_R4_0_engines.ps1').read_text(encoding='utf-8')
    assert "run -n '$EnvName' /bin/true" in text
    assert "env list | awk" not in text
    assert 'function Test-CondaRun' in text


def test_provisioning_is_incremental_for_installed_scientific_packages():
    root=Path(__file__).resolve().parents[1]
    text=(root/'provision_v0_6D1_R4_0_engines.ps1').read_text(encoding='utf-8')
    assert 'Geonomics 1.4.9 already present; skipping pip reinstall' in text
    assert 'MadingleyR 1.0.6 already present; skipping reinstall' in text
    assert 'RangeShiftR 3.0.1 already present; skipping reinstall' in text
    assert "pak::pak('RangeShifter/RangeShiftR-pkg/RangeShiftR@d01f1b6')" in text


def test_r_runtime_provisioning_exports_conda_libs_for_madingley_child_binary():
    root=Path(__file__).resolve().parents[1]
    text=(root/'provision_v0_6D1_R4_0_engines.ps1').read_text(encoding='utf-8')
    assert 'R runtime library path:' in text
    assert 'libgomp.so.1' in text
    assert "env LD_LIBRARY_PATH='$RLibPath'" in text
    assert 'r-codetools' in text

def test_r40_wsl_r_probe_exports_conda_prefix_lib():
    import inspect
    text=inspect.getsource(r._r_probe)
    assert 'LD_LIBRARY_PATH' in text
    assert 'CONDA_PREFIX/lib' in text
    assert 'Rscript+runtime-libs' in text


def test_provisioning_inline_probe_commands_use_here_strings_not_nested_powershell_quotes():
    root=Path(__file__).resolve().parents[1]
    text=(root/'provision_v0_6D1_R4_0_engines.ps1').read_text(encoding='utf-8')
    assert '$GeonomicsVersionProbe = @\'' in text
    assert '$GeonomicsVersionPrint = @\'' in text
    assert '$MadingleyVersionProbe = @\'' in text
    assert '$RangeShiftRVersionProbe = @\'' in text
    assert 'Test-CondaRun $REnv "Rscript -e "' not in text
    assert 'm.version("geonomics")' not in text


def test_r_prefix_probe_uses_conda_run_env_without_nested_printf_quoting():
    root=Path(__file__).resolve().parents[1]
    text=(root/'provision_v0_6D1_R4_0_engines.ps1').read_text(encoding='utf-8')
    assert "Invoke-WslCaptureFirstLine \"'$CondaPath' run -n '$REnv' env\"" in text
    assert "Where-Object { $_ -like 'CONDA_PREFIX=*' }" in text
    assert "Substring('CONDA_PREFIX='.Length)" in text
    assert "printf \\\"%s\\\\n\\\"" not in text


def test_rangeshiftr_301_source_ref_frozen():
    x=cfg()['engines']['RangeShifter']; assert x['version']=='3.0.1'; assert x['provisioning']['install_ref']=='d01f1b6'; assert x['provisioning']['required_package_version']=='3.0.1'


def test_wsl_exe_prefers_explicit_binding(monkeypatch,tmp_path):
    fake=tmp_path/'wsl.exe'; fake.write_text('stub')
    monkeypatch.setenv('ARCANA_WSL_EXE',str(fake))
    assert r._wsl_exe()==str(fake)

def test_wsl_conda_prefix_prefers_explicit_binding(monkeypatch):
    monkeypatch.setenv('ARCANA_WSL_CONDA','/home/test/miniforge3/bin/conda')
    x=r._wsl_conda_prefix()
    assert 'CONDA_EXE=/home/test/miniforge3/bin/conda' in x

def test_run_script_autoloads_governed_local_engine_bindings():
    root=Path(__file__).resolve().parents[1]
    text=(root/'run_v0_6D1_R4_0.ps1').read_text(encoding='utf-8')
    assert 'set_r40_engine_env.local.ps1' in text
    assert '. $LocalEngineBindings' in text

def test_provisioner_persists_wsl_and_conda_bindings():
    root=Path(__file__).resolve().parents[1]
    text=(root/'provision_v0_6D1_R4_0_engines.ps1').read_text(encoding='utf-8')
    assert 'Get-Command wsl.exe' in text
    assert '`$env:ARCANA_WSL_EXE' in text
    assert '`$env:ARCANA_WSL_CONDA' in text


def test_run_script_bridges_powershell_wsl_path_into_python():
    root=Path(__file__).resolve().parents[1]
    text=(root/'run_v0_6D1_R4_0.ps1').read_text(encoding='utf-8')
    assert 'Get-Command wsl.exe' in text
    assert '$env:ARCANA_WSL_EXE = $WslCommand.Source' in text

def test_host_runtime_evidence_bridge_file_is_governed_source():
    root=Path(__file__).resolve().parents[1]
    text=(root/'capture_v0_6D1_R4_0_runtime_evidence.ps1').read_text(encoding='utf-8')
    assert 'HOST_RUNTIME_IDENTITY_EVIDENCE' in text
    assert 'Invoke-WslScript' in text
    assert 'RedirectStandardInput = $true' in text
    assert 'Ready engines:' in text

def test_runner_generates_fresh_host_runtime_evidence_before_inventory():
    root=Path(__file__).resolve().parents[1]
    text=(root/'run_v0_6D1_R4_0.ps1').read_text(encoding='utf-8')
    assert 'capture_v0_6D1_R4_0_runtime_evidence.ps1' in text
    assert 'ARCANA_R40_HOST_RUNTIME_EVIDENCE' in text
    assert text.index('fresh host runtime evidence bridge') < text.index('multi-engine runtime inventory')

def test_host_runtime_evidence_can_authorize_exact_pins(monkeypatch,tmp_path):
    c=cfg()
    rows=[]
    for engine in c['required_engines_for_r40_seal']:
        expected=c['engines'][engine]['version']
        rows.append({'engine':engine,'expected_version':expected,'confirmed_version':expected,'status':'READY','invocation':'test','returncode':0,'stdout':'ok','stderr':''})
    ev={'stage':r.STAGE,'evidence_type':'HOST_RUNTIME_IDENTITY_EVIDENCE','generated_by':'capture_v0_6D1_R4_0_runtime_evidence.ps1','root':str(tmp_path),'engines':rows}
    p=tmp_path/'evidence.json'; p.write_text(json.dumps(ev))
    monkeypatch.setenv('ARCANA_R40_HOST_RUNTIME_EVIDENCE',str(p))
    probes=r.probe_all(tmp_path,c)
    assert len(probes)==6 and all(x.status=='READY' for x in probes)

def test_host_runtime_evidence_rejects_version_drift(monkeypatch,tmp_path):
    c=cfg(); rows=[]
    for engine in c['required_engines_for_r40_seal']:
        expected=c['engines'][engine]['version']
        if engine=='RangeShifter': expected='3.0.0'
        rows.append({'engine':engine,'expected_version':expected,'confirmed_version':expected,'status':'READY','invocation':'test','returncode':0,'stdout':'ok','stderr':''})
    ev={'stage':r.STAGE,'evidence_type':'HOST_RUNTIME_IDENTITY_EVIDENCE','generated_by':'capture_v0_6D1_R4_0_runtime_evidence.ps1','root':str(tmp_path),'engines':rows}
    p=tmp_path/'evidence.json'; p.write_text(json.dumps(ev))
    monkeypatch.setenv('ARCANA_R40_HOST_RUNTIME_EVIDENCE',str(p))
    probes={x.engine:x for x in r.probe_all(tmp_path,c)}
    assert probes['RangeShifter'].status=='VERSION_MISMATCH'


def test_runner_deletes_stale_runtime_evidence_before_capture():
    root=Path(__file__).resolve().parents[1]
    text=(root/'run_v0_6D1_R4_0.ps1').read_text(encoding='utf-8')
    assert 'Remove-Item -Force $RuntimeEvidence' in text
    assert 'produced no fresh evidence file' in text

def test_inventory_console_exposes_probe_diagnostics():
    root=Path(__file__).resolve().parents[1]
    text=(root/'scripts/run_v0_6D1_R4_0.py').read_text(encoding='utf-8')
    assert "'engine_probes'" in text and "'returncode'" in text and "'invocation'" in text


def test_host_runtime_bridge_resolves_absolute_conda_without_login_shell():
    root=Path(__file__).resolve().parents[1]
    text=(root/'capture_v0_6D1_R4_0_runtime_evidence.ps1').read_text(encoding='utf-8')
    assert '$HOME/miniforge3/bin/conda' in text
    assert 'bash -s' in text
    assert 'could not resolve Conda inside WSL' in text
