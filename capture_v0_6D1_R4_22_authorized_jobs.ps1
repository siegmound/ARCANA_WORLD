param(
  [switch]$PrepareOnly,
  [switch]$CollectOnly,
  [string]$JobId = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$LocalEngineBindings = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEngineBindings) { . $LocalEngineBindings }
$OutDir = Join-Path $Root "outputs\v0_6D1_R4_22"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$RuntimeEvidence = Join-Path $OutDir "R4_22_RUNTIME_IDENTITY_EVIDENCE.json"

if($CollectOnly){
  Write-Host "=== R4.22 collect-only: audit retained authorized execution evidence ==="
  python "$Root\scripts\collect_v0_6D1_R4_22.py" --root "$Root"
  exit $LASTEXITCODE
}

Write-Host "=== R4.22 Phase A: fresh governed runtime identity evidence ==="
& (Join-Path $Root "capture_v0_6D1_R4_0_runtime_evidence.ps1") -OutputPath $RuntimeEvidence
if ($LASTEXITCODE -ne 0) { throw "R4.22 runtime identity probe failed closed." }
$Runtime = Get-Content -Raw $RuntimeEvidence | ConvertFrom-Json
if ($Runtime.all_required_engines_ready -ne $true) { throw "R4.22 requires governed runtime inventory READY before authorized reexecution." }

Write-Host "=== R4.22 Phase A: exact R4.21-authorized execution plan + deferred Geonomics audit ==="
python "$Root\scripts\prepare_v0_6D1_R4_22.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R4.22 preexecution materialization failed closed." }
if ($PrepareOnly) { Write-Host "PASS_R422_PHASE_A_PREEXECUTION_READY"; exit 0 }

$WslExe = [string]$Runtime.wsl_executable
$CondaPath = [string]$Runtime.conda_binding
if ([string]::IsNullOrWhiteSpace($WslExe) -or -not (Test-Path $WslExe)) { throw "Invalid R4.22 WSL executable binding: $WslExe" }
if ([string]::IsNullOrWhiteSpace($CondaPath)) { throw "Invalid R4.22 Conda binding." }

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
  if($timedOut){return [pscustomobject]@{ExitCode=124;Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3);TimedOut=$true}}
  return [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3);TimedOut=$false}
}
function Write-FallbackRawEvidence {
  param([string]$Path,[string]$Job,[string]$Engine,[object]$Exec)
  if(Test-Path $Path){return}
  $obj=[ordered]@{stage='v0.6D1-R4.22';job_id=$Job;engine=$Engine;adapter_status='ENGINE_EXECUTION_FAILURE';replicates=@();bridge_returncode=[int]$Exec.ExitCode;timed_out=[bool]$Exec.TimedOut;error='Authorized adapter produced no RAW_EVIDENCE.json';comparison_target_used=$false;canonical_write=$false}
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Path
}

function Preserve-R422R1InitialNemoFailureEvidence {
  param([Parameter(Mandatory=$true)][string]$OutDir)
  $Hist = Join-Path $OutDir 'repair_history\R422_INITIAL_NEMO_CONDA_PYTHON_BINDING_FAILURE'
  $Marker = Join-Path $Hist 'PRESERVED.json'
  if(Test-Path $Marker){ return }
  $FailedIds = @(
    'R42_J10_H0_POST_CHA1_RECOVERY_NEMO',
    'R42_J13_H0_LATE_CENOZOIC_NEMO',
    'R42_J17_SAPIENT_3MA_TO_200KA_NEMO'
  )
  $Records = @()
  foreach($jid in $FailedIds){
    $JobDir = Join-Path $OutDir ('jobs\' + $jid)
    $Raw = Join-Path $JobDir 'RAW_EVIDENCE.json'
    if(-not (Test-Path $Raw)){ continue }
    try { $Obj = Get-Content -Raw $Raw | ConvertFrom-Json } catch { continue }
    if(([string]$Obj.adapter_status -ne 'ENGINE_EXECUTION_FAILURE') -or ([int]$Obj.bridge_returncode -ne 127)){ continue }
    $Dst = Join-Path $Hist $jid
    New-Item -ItemType Directory -Force -Path $Dst | Out-Null
    foreach($name in @('RAW_EVIDENCE.json','JOB_AUDIT.json','STDOUT.log','STDERR.log')){
      $p = Join-Path $JobDir $name
      if(Test-Path $p){ Copy-Item -Force $p (Join-Path $Dst $name) }
    }
    $Records += [ordered]@{job_id=$jid;adapter_status=[string]$Obj.adapter_status;bridge_returncode=[int]$Obj.bridge_returncode}
  }
  if($Records.Count -gt 0){
    foreach($name in @('R4_22_INTEGRATED_AUDIT.json','R4_22_PREEXECUTION_AUDIT.json')){
      $p = Join-Path $OutDir $name
      if(Test-Path $p){ New-Item -ItemType Directory -Force -Path $Hist | Out-Null; Copy-Item -Force $p (Join-Path $Hist $name) }
    }
    $Meta = [ordered]@{
      stage='v0.6D1-R4.22-R1'
      finding='R422_NEMO_CONDA_ENV_PYTHON_BINDING_FAILURE_CONFIRMED'
      repair_scope='HOST_WSL_EXECUTION_BRIDGE_ONLY'
      adapter_source_modified=$false
      authorized_adapter_hash_preserved=$true
      failed_jobs=$Records
    }
    $Meta | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Marker
    Write-Host 'PASS_R422_R1_INITIAL_NEMO_EXECUTION_FAILURE_EVIDENCE_PRESERVED'
  }
}

$CondaQ=Assert-ShellSafeValue $CondaPath 'CondaPath'
$CondaBasePython = $CondaPath -replace '/bin/conda$','/bin/python'
if($CondaBasePython -eq $CondaPath){ throw "Cannot derive governed base Python from Conda binding: $CondaPath" }
$CondaBasePythonQ=Assert-ShellSafeValue $CondaBasePython 'CondaBasePython'
$RootWsl=Convert-ArcanaWindowsPathToWsl $Root; $RootQ=Assert-ShellSafeValue $RootWsl 'RootWsl'
$NemoEnv=if($env:ARCANA_NEMO_CONDA_ENV){$env:ARCANA_NEMO_CONDA_ENV}else{'arcana-nemo242'}
$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{'arcana-cdmetapop-308'}
$SlimEnv=if($env:ARCANA_SLIM_CONDA_ENV){$env:ARCANA_SLIM_CONDA_ENV}else{'arcana-slim52'}
$CdRootWindows=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root '.arcana_engines\CDMetaPOP-3.08'}
$CdRootWsl=Convert-ArcanaWindowsPathToWsl $CdRootWindows; $CdRootQ=Assert-ShellSafeValue $CdRootWsl 'CDMetaPOPRoot'

$Plan = Get-Content -Raw (Join-Path $OutDir 'R4_22_PREEXECUTION_PLAN.json') | ConvertFrom-Json
Preserve-R422R1InitialNemoFailureEvidence -OutDir $OutDir
$Jobs=@($Plan.jobs)
if(-not [string]::IsNullOrWhiteSpace($JobId)){
  $Jobs=@($Jobs | Where-Object {$_.job_id -eq $JobId})
  if($Jobs.Count -ne 1){throw "Unknown R4.22 authorized JobId: $JobId"}
}
Write-Host "=== R4.22 Phase B: exact authorized symmetric reexecution ==="
$idx=0
foreach($Job in $Jobs){
  $idx++; $jid=[string]$Job.job_id; $engine=[string]$Job.engine
  Write-Host ("[{0}/{1}] {2} / {3}" -f $idx,$Jobs.Count,$jid,$engine)
  $JobDir=Join-Path $OutDir ("jobs\"+$jid); New-Item -ItemType Directory -Force -Path $JobDir | Out-Null
  $Contract=Join-Path $Root ([string]$Job.contract_path); $Raw=Join-Path $JobDir 'RAW_EVIDENCE.json'; $Work=Join-Path $JobDir 'runtime_work'
  foreach($name in @('RAW_EVIDENCE.json','JOB_AUDIT.json','STDOUT.log','STDERR.log')){ $p=Join-Path $JobDir $name; if(Test-Path $p){Remove-Item -Force $p} }
  if(Test-Path $Work){Remove-Item -Recurse -Force $Work}; New-Item -ItemType Directory -Force -Path $Work | Out-Null
  $ContractQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Contract) 'Contract'; $RawQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Raw) 'Raw'; $WorkQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Work) 'Work'
  switch($engine){
    'NEMO' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
# R4.22-R1: the native NEMO env is authoritative for nemo2.4.2 but need not carry Python.
# Execute the unchanged/hash-authorized Python adapter with governed Miniforge base Python
# inside the NEMO conda execution context, so nemo2.4.2 remains resolved from arcana-nemo242.
"`$CONDA_EXE" run -n '$NemoEnv' $CondaBasePythonQ $RootQ/benchmarks/r421/nemo_r421.py $ContractQ $RawQ $WorkQ
"@}
    'SLiM' {$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$SlimEnv' python $RootQ/benchmarks/r421/slim_r421.py $ContractQ $RawQ $WorkQ
"@}
    'CDMetaPOP' {
      $Profile=Join-Path $Root ([string]$Job.repair_profile_path); $ProfileQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Profile) 'Profile'
      $script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$CdEnv' python $RootQ/benchmarks/r421/cdmetapop_r421_matched.py $ContractQ $ProfileQ $RawQ $WorkQ $CdRootQ
"@
    }
    default { throw "Engine not authorized by R4.21 for R4.22 execution: $engine" }
  }
  $exec=Invoke-WslScript $script $jid 3600 30
  [string]$exec.Stdout | Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDOUT.log')
  [string]$exec.Stderr | Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDERR.log')
  Write-FallbackRawEvidence $Raw $jid $engine $exec
  Write-Host ("  returncode={0} elapsed={1}s" -f $exec.ExitCode,$exec.ElapsedSeconds)
}
if(-not [string]::IsNullOrWhiteSpace($JobId)){ Write-Host "R4.22 single authorized job execution completed; run full R4.22 for exact 11-job completeness audit."; exit 0 }

Write-Host "=== R4.22 Phase C: evidence integrity + completeness audit ==="
python "$Root\scripts\collect_v0_6D1_R4_22.py" --root "$Root"
if($LASTEXITCODE -ne 0){ Write-Host "R4.22 BLOCKED. Preserve outputs and rerun only failed authorized jobs if needed."; exit 3 }
exit 0
