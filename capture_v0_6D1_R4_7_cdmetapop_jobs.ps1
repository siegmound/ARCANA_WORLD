param(
  [switch]$PrepareOnly,
  [string]$JobId = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$LocalEngineBindings = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEngineBindings) { . $LocalEngineBindings }
$OutDir = Join-Path $Root "outputs\v0_6D1_R4_7"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$RuntimeEvidence = Join-Path $OutDir "R4_7_RUNTIME_IDENTITY_EVIDENCE.json"

Write-Host "=== R4.7 Phase A: fresh governed runtime identity evidence ==="
& (Join-Path $Root "capture_v0_6D1_R4_0_runtime_evidence.ps1") -OutputPath $RuntimeEvidence
if ($LASTEXITCODE -ne 0) { throw "R4.7 runtime identity probe failed closed." }
$Runtime = Get-Content -Raw $RuntimeEvidence | ConvertFrom-Json
$CdRow = @($Runtime.engines | Where-Object { $_.engine -eq 'CDMetaPOP' -or $_.name -eq 'CDMetaPOP' })
if ($Runtime.all_required_engines_ready -ne $true) { throw "R4.7 requires governed runtime inventory READY before scientific reexecution." }

Write-Host "=== R4.7 Phase A: forcing-parity repair plan ==="
python "$Root\scripts\prepare_v0_6D1_R4_7.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R4.7 repair-plan preparation failed closed." }
if ($PrepareOnly) { Write-Host "PASS_R47_PHASE_A_REPAIR_PLAN_READY"; exit 0 }

$WslExe = [string]$Runtime.wsl_executable
$CondaPath = [string]$Runtime.conda_binding
if ([string]::IsNullOrWhiteSpace($WslExe) -or -not (Test-Path $WslExe)) { throw "Invalid R4.7 WSL executable binding: $WslExe" }
if ([string]::IsNullOrWhiteSpace($CondaPath)) { throw "Invalid R4.7 Conda binding." }
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
  param([Parameter(Mandatory=$true)][string]$Script,[Parameter(Mandatory=$true)][string]$Label,[int]$TimeoutSeconds=900,[int]$HeartbeatSeconds=30)
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
  if($timedOut){return [pscustomobject]@{ExitCode=124;Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3)}}
  return [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3)}
}
function Write-FallbackRawEvidence {
  param([string]$Path,[string]$Job,[object]$Exec)
  if(Test-Path $Path){return}
  $obj=[ordered]@{stage='v0.6D1-R4.7';job_id=$Job;engine='CDMetaPOP';adapter_status='ENGINE_EXECUTION_FAILURE';replicates=@();bridge_returncode=[int]$Exec.ExitCode;error='Adapter produced no RAW_EVIDENCE.json';canonical_write=$false}
  $obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $Path
}

$CondaQ=Assert-ShellSafeValue $CondaPath 'CondaPath'
$RootWsl=Convert-ArcanaWindowsPathToWsl $Root; $RootQ=Assert-ShellSafeValue $RootWsl 'RootWsl'
$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{'arcana-cdmetapop-308'}
$CdRootWindows=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root '.arcana_engines\CDMetaPOP-3.08'}
$CdRootWsl=Convert-ArcanaWindowsPathToWsl $CdRootWindows; $CdRootQ=Assert-ShellSafeValue $CdRootWsl 'CDMetaPOPRoot'
$Plan = Get-Content -Raw (Join-Path $OutDir 'R4_7_REPAIR_PLAN.json') | ConvertFrom-Json
$Jobs=@($Plan.jobs)
if(-not [string]::IsNullOrWhiteSpace($JobId)){
  $Jobs=@($Jobs | Where-Object {$_.job_id -eq $JobId})
  if($Jobs.Count -ne 1){throw "Unknown R4.7 CDMetaPOP JobId: $JobId"}
}
Write-Host "=== R4.7 Phase B: symmetric CDMetaPOP reexecution with dynamic forcing ==="
$idx=0
foreach($Job in $Jobs){
  $idx++; $jid=[string]$Job.job_id
  Write-Host ("[{0}/{1}] {2} / CDMetaPOP" -f $idx,$Jobs.Count,$jid)
  $JobDir=Join-Path $OutDir ("jobs\"+$jid); $Contract=Join-Path $Root ("outputs\v0_6D1_R4_3\jobs\"+$jid+"\JOB_CONTRACT.json"); $Profile=Join-Path $JobDir 'REPAIR_PROFILE.json'; $Raw=Join-Path $JobDir 'RAW_EVIDENCE.json'; $Work=Join-Path $JobDir 'runtime_work'
  foreach($name in @('RAW_EVIDENCE.json','NORMALIZED_EVIDENCE.json','JOB_AUDIT.json','STDOUT.log','STDERR.log')){ $p=Join-Path $JobDir $name; if(Test-Path $p){Remove-Item -Force $p} }
  if(Test-Path $Work){Remove-Item -Recurse -Force $Work}; New-Item -ItemType Directory -Force -Path $Work | Out-Null
  $ContractQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Contract) 'Contract'; $ProfileQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Profile) 'Profile'; $RawQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Raw) 'Raw'; $WorkQ=Assert-ShellSafeValue (Convert-ArcanaWindowsPathToWsl $Work) 'Work'
  $script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
"`$CONDA_EXE" run -n '$CdEnv' python $RootQ/benchmarks/r47/cdmetapop_r47.py $ContractQ $ProfileQ $RawQ $WorkQ $CdRootQ
"@
  $exec=Invoke-WslScript $script $jid 900 30
  [string]$exec.Stdout | Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDOUT.log')
  [string]$exec.Stderr | Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDERR.log')
  Write-FallbackRawEvidence $Raw $jid $exec
  Write-Host ("  returncode={0} elapsed={1}s" -f $exec.ExitCode,$exec.ElapsedSeconds)
}
if(-not [string]::IsNullOrWhiteSpace($JobId)){ Write-Host "R4.7 single-job reexecution completed; run full R4.7 to collect/readjudicate all five."; exit 0 }
Write-Host "=== R4.7 Phase C: normalize + targeted readjudication ==="
python "$Root\scripts\collect_v0_6D1_R4_7.py" --root "$Root"
if($LASTEXITCODE -ne 0){ Write-Host "R4.7 BLOCKED. Preserve outputs and paste R4_7_INTEGRATED_AUDIT.json."; exit 3 }
exit 0
