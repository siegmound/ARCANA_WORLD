param(
  [switch]$PrepareOnly,
  [switch]$Smoke,
  [switch]$RepairNemo,
  [string]$JobId = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$LocalEngineBindings = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEngineBindings) { . $LocalEngineBindings }

$OutDir = Join-Path $Root "outputs\v0_6D1_R4_3"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$RuntimeEvidence = Join-Path $OutDir "R4_3_RUNTIME_IDENTITY_EVIDENCE.json"

Write-Host "=== R4.3 Phase A: fresh governed runtime identity evidence ==="
& (Join-Path $Root "capture_v0_6D1_R4_0_runtime_evidence.ps1") -OutputPath $RuntimeEvidence
if ($LASTEXITCODE -ne 0) { throw "R4.3 runtime identity probe failed closed." }
$Runtime = Get-Content -Raw $RuntimeEvidence | ConvertFrom-Json
if (-not $Runtime.all_required_engines_ready) { throw "R4.3 requires all six governed external runtimes READY." }

Write-Host "=== R4.3 Phase A: frozen 23-job contract + per-job unit mappings ==="
python "$Root\scripts\prepare_v0_6D1_R4_3.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R4.3 pre-execution materialization failed closed." }
if ($PrepareOnly) {
  Write-Host "PASS_R43_PHASE_A_PREEXECUTION_READY"
  Write-Host "Inspect: $OutDir\R4_3_PREEXECUTION_AUDIT.json"
  exit 0
}

$WslExe = [string]$Runtime.wsl_executable
$CondaPath = [string]$Runtime.conda_binding
if ([string]::IsNullOrWhiteSpace($WslExe) -or -not (Test-Path $WslExe)) { throw "Invalid R4.3 WSL executable binding: $WslExe" }
if ([string]::IsNullOrWhiteSpace($CondaPath)) { throw "Invalid R4.3 Conda binding." }

# R4.3-R1: the NEMO 2.4.2 environment is an engine runtime and is not required to contain Python.
# Use the Miniforge/base control Python to drive the adapter, and invoke NEMO itself through
# `conda run -n <NEMO_ENV> nemo2.4.2`. This preserves the R4.0/R4.1 governed engine identity.
$ControlPythonPath = if ($CondaPath -match '/conda$') { $CondaPath.Substring(0,$CondaPath.Length-5) + 'python' } else { '' }
if ([string]::IsNullOrWhiteSpace($ControlPythonPath)) { throw "Could not derive governed control Python from Conda binding: $CondaPath" }

function Assert-ShellSafeValue {
  param([Parameter(Mandatory=$true)][string]$Value,[Parameter(Mandatory=$true)][string]$Name)
  if ($Value.Contains("'")) { throw "$Name contains unsupported single quote: $Value" }
  return "'$Value'"
}
function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  $full=[System.IO.Path]::GetFullPath($Path)
  if($full -match '^([A-Za-z]):\\(.*)$'){
    $drive=$Matches[1].ToLowerInvariant(); $rest=$Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "Unsupported Windows path for WSL bridge: $full"
}
function Invoke-WslScript {
  param([Parameter(Mandatory=$true)][string]$Script,[Parameter(Mandatory=$true)][string]$Label,[int]$TimeoutSeconds=3600,[int]$HeartbeatSeconds=30)
  $psi=[System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName=$WslExe; $psi.Arguments="bash -s"; $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.CreateNoWindow=$true
  $p=[System.Diagnostics.Process]::new(); $p.StartInfo=$psi
  if(-not $p.Start()){ throw "Could not start governed WSL bridge for $Label" }
  $stdoutTask=$p.StandardOutput.ReadToEndAsync(); $stderrTask=$p.StandardError.ReadToEndAsync(); $p.StandardInput.Write($Script); $p.StandardInput.Close()
  $sw=[System.Diagnostics.Stopwatch]::StartNew(); $nextHeartbeat=[double]$HeartbeatSeconds; $timedOut=$false
  while(-not $p.WaitForExit(1000)){
    if($sw.Elapsed.TotalSeconds -ge $TimeoutSeconds){ $timedOut=$true; try{$p.Kill($true)}catch{try{$p.Kill()}catch{}}; break }
    if($sw.Elapsed.TotalSeconds -ge $nextHeartbeat){ Write-Host ("  {0}: still running ({1:n0}s elapsed)" -f $Label,$sw.Elapsed.TotalSeconds); $nextHeartbeat += [double]$HeartbeatSeconds }
  }
  if($timedOut){$p.WaitForExit()}
  $stdout=$stdoutTask.GetAwaiter().GetResult(); $stderr=$stderrTask.GetAwaiter().GetResult(); $sw.Stop()
  if($timedOut){$stderr=((([string]$stderr)+"`nARCANA_R43_TIMEOUT after $TimeoutSeconds seconds ($Label)").Trim()); return [pscustomobject]@{ExitCode=124;Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3);TimedOut=$true}}
  return [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3);TimedOut=$false}
}
function Write-FallbackRawEvidence {
  param([string]$Path,[string]$Job,[string]$Engine,[object]$Exec)
  if(Test-Path $Path){return}
  $obj=[ordered]@{stage='v0.6D1-R4.3';job_id=$Job;engine=$Engine;adapter_status='ENGINE_EXECUTION_FAILURE';replicates=@();bridge_returncode=[int]$Exec.ExitCode;timed_out=[bool]$Exec.TimedOut;error='Adapter produced no RAW_EVIDENCE.json';canonical_write=$false}
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Path
}

function Backup-R43EvidenceForRepair {
  param([Parameter(Mandatory=$true)][string]$JobDir,[Parameter(Mandatory=$true)][string]$JobId,[Parameter(Mandatory=$true)][string]$HistoryRoot)
  $dest=Join-Path $HistoryRoot $JobId
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  foreach($name in @('RAW_EVIDENCE.json','NORMALIZED_EVIDENCE.json','JOB_AUDIT.json','STDOUT.log','STDERR.log')){
    $src=Join-Path $JobDir $name
    if(Test-Path $src){Copy-Item -Force $src (Join-Path $dest $name)}
  }
}

$CondaQ=Assert-ShellSafeValue $CondaPath 'CondaPath'
$ControlPythonQ=Assert-ShellSafeValue $ControlPythonPath 'ControlPythonPath'
$RootWsl=Convert-ArcanaWindowsPathToWsl $Root; $RootQ=Assert-ShellSafeValue $RootWsl 'RootWsl'
$NemoEnv=if($env:ARCANA_NEMO_CONDA_ENV){$env:ARCANA_NEMO_CONDA_ENV}else{'arcana-nemo242'}
$GeoEnv=if($env:ARCANA_GEONOMICS_CONDA_ENV){$env:ARCANA_GEONOMICS_CONDA_ENV}else{'arcana-geonomics-149'}
$REnv=if($env:ARCANA_R40_R_CONDA_ENV){$env:ARCANA_R40_R_CONDA_ENV}else{'arcana-r40-r'}
$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{'arcana-cdmetapop-308'}
$SlimEnv=if($env:ARCANA_SLIM_CONDA_ENV){$env:ARCANA_SLIM_CONDA_ENV}else{'arcana-slim52'}
$CdRootWindows=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root '.arcana_engines\CDMetaPOP-3.08'}
$CdRootWsl=Convert-ArcanaWindowsPathToWsl $CdRootWindows; $CdRootQ=Assert-ShellSafeValue $CdRootWsl 'CDMetaPOPRoot'

$Cfg = Get-Content -Raw (Join-Path $Root 'configs\world1_r43_historical_revalidation_v0_6D1_R4_3.json') | ConvertFrom-Json
$Frozen = Get-Content -Raw (Join-Path $OutDir 'R4_3_FROZEN_JOB_REGISTRY.json') | ConvertFrom-Json
$Jobs=@($Frozen.jobs)
$ModeCount = @([bool]$Smoke,[bool]$RepairNemo,[bool](-not [string]::IsNullOrWhiteSpace($JobId))) | Where-Object {$_} | Measure-Object | Select-Object -ExpandProperty Count
if($ModeCount -gt 1){ throw "Use only one of -Smoke, -RepairNemo, or -JobId." }
if($Smoke){
  # One pre-declared representative frozen job per governed engine. This is execution plumbing smoke only;
  # it is never used for result selection, scientific agreement, or R4.4 adjudication.
  $SmokeIds=@(
    'R42_J01_H0_DEEP_TIME_BACKGROUND_MADINGLEY',
    'R42_J02_H0_DEEP_TIME_BACKGROUND_RANGESHIFTER',
    'R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP',
    'R42_J10_H0_POST_CHA1_RECOVERY_NEMO',
    'R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS',
    'R42_J16_SAPIENT_3MA_TO_200KA_SLIM'
  )
  $Jobs=@($Jobs | Where-Object {$SmokeIds -contains $_.job_id})
  if($Jobs.Count -ne 6){ throw "R4.3 smoke set must resolve exactly six frozen jobs, one per engine." }
}
if($RepairNemo){
  $RepairNemoIds=@(
    'R42_J10_H0_POST_CHA1_RECOVERY_NEMO',
    'R42_J13_H0_LATE_CENOZOIC_NEMO',
    'R42_J17_SAPIENT_3MA_TO_200KA_NEMO'
  )
  $Jobs=@($Jobs | Where-Object {$RepairNemoIds -contains $_.job_id})
  if($Jobs.Count -ne 3){throw "R4.3-R1 NEMO repair set must resolve exactly the three frozen NEMO jobs."}
  $HistoryRoot=Join-Path $OutDir 'repair_history\R43_R1_NEMO_RETURN127_PRE_REPAIR'
  New-Item -ItemType Directory -Force -Path $HistoryRoot | Out-Null
  foreach($name in @('R4_3_EXECUTION_SUMMARY.json','R4_3_COMPLETENESS_AUDIT.json')){
    $src=Join-Path $OutDir $name
    if(Test-Path $src){Copy-Item -Force $src (Join-Path $HistoryRoot $name)}
  }
}
if(-not [string]::IsNullOrWhiteSpace($JobId)){
  $Jobs=@($Jobs | Where-Object {$_.job_id -eq $JobId})
  if($Jobs.Count -ne 1){throw "Unknown frozen R4.3 JobId: $JobId"}
}

Write-Host "=== R4.3 Phase B: actual frozen engine-window executions ==="
$idx=0
foreach($Job in $Jobs){
  $idx++; $jid=[string]$Job.job_id; $engine=[string]$Job.engine
  Write-Host ("[{0}/{1}] {2} / {3}" -f $idx,$Jobs.Count,$jid,$engine)
  $JobDir=Join-Path $OutDir ("jobs\"+$jid); $Contract=Join-Path $JobDir 'JOB_CONTRACT.json'; $EngineCfg=Join-Path $JobDir 'ENGINE_CONFIG.tsv'; $Raw=Join-Path $JobDir 'RAW_EVIDENCE.json'; $Work=Join-Path $JobDir 'runtime_work'
  if($RepairNemo){Backup-R43EvidenceForRepair $JobDir $jid $HistoryRoot}
  if(Test-Path $Raw){Remove-Item -Force $Raw}; if(Test-Path $Work){Remove-Item -Recurse -Force $Work}; New-Item -ItemType Directory -Force -Path $Work | Out-Null
  $ContractQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Contract) 'Contract'; $CfgQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $EngineCfg) 'EngineCfg'; $RawQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Raw) 'Raw'; $WorkQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Work) 'Work'
  $timeout=[int]$Cfg.engine_timeout_seconds.$engine
  switch($engine){
    'NEMO' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
CONTROL_PYTHON=$ControlPythonQ
test -x "`$CONTROL_PYTHON" || { echo "R4.3-R1 control Python missing: `$CONTROL_PYTHON" >&2; exit 126; }
"`$CONTROL_PYTHON" $RootQ/benchmarks/r43/nemo_r43.py $ContractQ $RawQ $WorkQ "`$CONDA_EXE" '$NemoEnv'
"@}
    'Geonomics' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$GeoEnv' python $RootQ/benchmarks/r43/geonomics_r43.py $ContractQ $RawQ $WorkQ
"@}
    'Madingley' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$REnv' bash $RootQ/benchmarks/r41/run_r_with_conda_libs.sh $RootQ/benchmarks/r43/madingley_r43.R $CfgQ $RawQ $WorkQ
"@}
    'RangeShifter' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$REnv' bash $RootQ/benchmarks/r41/run_r_with_conda_libs.sh $RootQ/benchmarks/r43/rangeshiftr_r43.R $CfgQ $RawQ $WorkQ
"@}
    'CDMetaPOP' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$CdEnv' python $RootQ/benchmarks/r43/cdmetapop_r43.py $ContractQ $RawQ $WorkQ $CdRootQ
"@}
    'SLiM' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$SlimEnv' python $RootQ/benchmarks/r43/slim_r43.py $ContractQ $RawQ $WorkQ
"@}
    default {throw "Unsupported frozen engine: $engine"}
  }
  $exec=Invoke-WslScript $script $jid $timeout 30
  [string]$exec.Stdout | Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDOUT.log')
  [string]$exec.Stderr | Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDERR.log')
  Write-FallbackRawEvidence $Raw $jid $engine $exec
  Write-Host ("  returncode={0} elapsed={1}s" -f $exec.ExitCode,$exec.ElapsedSeconds)
}

if($Smoke){
  Write-Host "PASS_R43_SIX_ENGINE_EXECUTION_PLUMBING_SMOKE"
  Write-Host "Smoke evidence is preserved but is not a completeness audit and makes no scientific conclusion."
  exit 0
}
if(-not [string]::IsNullOrWhiteSpace($JobId)){
  Write-Host "R4.3 single-job execution completed. Run -RepairNemo or the full runner after repairs/review to materialize the final completeness audit."
  exit 0
}
if($RepairNemo){Write-Host "PASS_R43_R1_THREE_NEMO_JOBS_REEXECUTED__COLLECTING_ALL_23_PRESERVED_BUNDLES"}

Write-Host "=== R4.3 Phase C: collect + normalize + completeness audit ==="
python "$Root\scripts\collect_v0_6D1_R4_3.py" --root "$Root"
$CollectExit=$LASTEXITCODE
if($CollectExit -eq 3){Write-Host "R4.3 execution evidence is BLOCKED. Preserve outputs and paste the completeness audit."; exit 3}
if($CollectExit -ne 0){throw "R4.3 collection failed closed."}
exit 0
