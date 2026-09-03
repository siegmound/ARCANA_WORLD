param(
  [string]$RuntimeIdentityEvidence = "",
  [string]$OutputPath = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocalEngineBindings = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEngineBindings) { . $LocalEngineBindings }
if ([string]::IsNullOrWhiteSpace($RuntimeIdentityEvidence)) {
  $RuntimeIdentityEvidence = Join-Path $Root "outputs\v0_6D1_R4_1\R4_1_RUNTIME_IDENTITY_EVIDENCE.json"
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
  $OutputPath = Join-Path $Root "outputs\v0_6D1_R4_1\R4_1_HOST_MICROBENCHMARK_EVIDENCE.json"
}
if (-not (Test-Path $RuntimeIdentityEvidence)) { throw "R4.1 runtime identity evidence missing: $RuntimeIdentityEvidence" }
$RuntimeEvidence = Get-Content -Raw $RuntimeIdentityEvidence | ConvertFrom-Json
if (-not $RuntimeEvidence.all_required_engines_ready) { throw "R4.1 refuses microbenchmarks unless all six R4.0 runtime identities are freshly READY." }
$WslExe = [string]$RuntimeEvidence.wsl_executable
$CondaPath = [string]$RuntimeEvidence.conda_binding
if ([string]::IsNullOrWhiteSpace($WslExe) -or -not (Test-Path $WslExe)) { throw "R4.1 invalid WSL binding in runtime evidence: $WslExe" }
if ([string]::IsNullOrWhiteSpace($CondaPath)) { throw "R4.1 invalid Conda binding in runtime evidence." }

function Assert-ShellSafeValue {
  param([Parameter(Mandatory=$true)][string]$Value,[Parameter(Mandatory=$true)][string]$Name)
  if ($Value.Contains("'")) { throw "$Name contains an unsupported single quote for governed WSL bridge: $Value" }
  return "'$Value'"
}
function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  $full=[System.IO.Path]::GetFullPath($Path)
  if($full -match '^([A-Za-z]):\\(.*)$'){
    $drive=$Matches[1].ToLowerInvariant(); $rest=$Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "Unsupported ARCANA Windows path for WSL bridge: $full"
}
function Invoke-WslScript {
  param(
    [Parameter(Mandatory=$true)][string]$Script,
    [Parameter(Mandatory=$true)][string]$Label,
    [int]$TimeoutSeconds=3600,
    [int]$HeartbeatSeconds=30
  )
  $psi=[System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$WslExe; $psi.Arguments="bash -s"; $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.CreateNoWindow=$true
  $p=[System.Diagnostics.Process]::new(); $p.StartInfo=$psi
  if(-not $p.Start()){ throw "Could not start governed WSL R4.1 microbenchmark bridge for $Label" }

  # Drain stdout and stderr concurrently. Reading one redirected stream to EOF before
  # the other can deadlock when a verbose engine fills the other pipe buffer.
  $stdoutTask=$p.StandardOutput.ReadToEndAsync()
  $stderrTask=$p.StandardError.ReadToEndAsync()
  $p.StandardInput.Write($Script); $p.StandardInput.Close()

  $sw=[System.Diagnostics.Stopwatch]::StartNew()
  $nextHeartbeat=[double]$HeartbeatSeconds
  $timedOut=$false
  while(-not $p.WaitForExit(1000)){
    if($sw.Elapsed.TotalSeconds -ge $TimeoutSeconds){
      $timedOut=$true
      try { $p.Kill($true) } catch { try { $p.Kill() } catch {} }
      break
    }
    if($sw.Elapsed.TotalSeconds -ge $nextHeartbeat){
      Write-Host ("  {0}: still running ({1:n0}s elapsed)" -f $Label,$sw.Elapsed.TotalSeconds)
      $nextHeartbeat += [double]$HeartbeatSeconds
    }
  }
  if($timedOut){ $p.WaitForExit() }
  $stdout=$stdoutTask.GetAwaiter().GetResult()
  $stderr=$stderrTask.GetAwaiter().GetResult()
  $sw.Stop()
  if($timedOut){
    $stderr = (([string]$stderr) + "`nARCANA_R41_TIMEOUT after $TimeoutSeconds seconds ($Label)").Trim()
    return [pscustomobject]@{ ExitCode=124; Stdout=$stdout; Stderr=$stderr; ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3); TimedOut=$true }
  }
  [pscustomobject]@{ ExitCode=$p.ExitCode; Stdout=$stdout; Stderr=$stderr; ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3); TimedOut=$false }
}
function Get-RuntimeVersion([string]$Engine){
  $row=@($RuntimeEvidence.engines | Where-Object { $_.engine -eq $Engine } | Select-Object -First 1)
  if($row.Count -eq 0){ return $null }
  return [string]$row[0].confirmed_version
}
function Get-TailText([string]$Text,[int]$MaxChars=6000){
  if([string]::IsNullOrEmpty($Text)){ return '' }
  if($Text.Length -le $MaxChars){ return $Text }
  return $Text.Substring($Text.Length-$MaxChars)
}
function Read-BenchmarkResult([string]$Path,[string]$Engine,[string]$BenchmarkId,[object]$Exec){
  $status='FAIL'; $returncode=[int]$Exec.ExitCode; $metrics=@{}; $error=$null
  $resultStdoutTail=''; $resultStderrTail=''; $engineLogTail=''
  if(Test-Path $Path){
    try {
      $raw=Get-Content -Raw $Path | ConvertFrom-Json
      $status=[string]$raw.status
      if($null -ne $raw.returncode){ $returncode=[int]$raw.returncode }
      if($null -ne $raw.metrics){ $metrics=$raw.metrics }
      if($null -ne $raw.error){ $error=[string]$raw.error }
      if($null -ne $raw.stdout_tail){ $resultStdoutTail=Get-TailText ([string]$raw.stdout_tail) }
      if($null -ne $raw.stderr_tail){ $resultStderrTail=Get-TailText ([string]$raw.stderr_tail) }
      if($null -ne $raw.engine_log_tail){ $engineLogTail=Get-TailText ([string]$raw.engine_log_tail) 12000 }
    } catch { $error="Could not parse benchmark result JSON: $($_.Exception.Message)" }
  } else { $error="Benchmark produced no result JSON: $Path" }
  [ordered]@{
    benchmark_id=$BenchmarkId
    engine=$Engine
    confirmed_version=(Get-RuntimeVersion $Engine)
    status=$status
    returncode=$returncode
    elapsed_seconds=if($null -ne $Exec.ElapsedSeconds){[double]$Exec.ElapsedSeconds}else{$null}
    timed_out=if($null -ne $Exec.TimedOut){[bool]$Exec.TimedOut}else{$false}
    metrics=$metrics
    result_file=$Path
    stdout_tail=(Get-TailText ([string]$Exec.Stdout))
    stderr_tail=(Get-TailText ([string]$Exec.Stderr))
    result_stdout_tail=$resultStdoutTail
    result_stderr_tail=$resultStderrTail
    engine_log_tail=$engineLogTail
    error=$error
  }
}

$RootWsl=Convert-ArcanaWindowsPathToWsl $Root
$OutDir=Join-Path $Root "outputs\v0_6D1_R4_1"
$WorkDir=Join-Path $OutDir "runtime_work"
$ResultDir=Join-Path $OutDir "microbenchmarks"
if(Test-Path $WorkDir){ Remove-Item -Recurse -Force $WorkDir }
if(Test-Path $ResultDir){ Remove-Item -Recurse -Force $ResultDir }
New-Item -ItemType Directory -Force -Path $WorkDir,$ResultDir | Out-Null
$WorkWsl=Convert-ArcanaWindowsPathToWsl $WorkDir
$ResultWsl=Convert-ArcanaWindowsPathToWsl $ResultDir
$CondaQ=Assert-ShellSafeValue $CondaPath 'CondaPath'
$RootQ=Assert-ShellSafeValue $RootWsl 'RootWsl'
$WorkQ=Assert-ShellSafeValue $WorkWsl 'WorkWsl'
$ResultQ=Assert-ShellSafeValue $ResultWsl 'ResultWsl'

$NemoEnv=if($env:ARCANA_NEMO_CONDA_ENV){$env:ARCANA_NEMO_CONDA_ENV}else{'arcana-nemo242'}
$GeoEnv=if($env:ARCANA_GEONOMICS_CONDA_ENV){$env:ARCANA_GEONOMICS_CONDA_ENV}else{'arcana-geonomics-149'}
$REnv=if($env:ARCANA_R40_R_CONDA_ENV){$env:ARCANA_R40_R_CONDA_ENV}else{'arcana-r40-r'}
$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{'arcana-cdmetapop-308'}
$SlimEnv=if($env:ARCANA_SLIM_CONDA_ENV){$env:ARCANA_SLIM_CONDA_ENV}else{'arcana-slim52'}
$CdRootWindows=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root '.arcana_engines\CDMetaPOP-3.08'}
$CdRootWsl=Convert-ArcanaWindowsPathToWsl $CdRootWindows

$benchmarks=@()
Write-Host "=== R4.1 controlled multi-engine microbenchmarks ==="

# NEMO
Write-Host "[1/6] NEMO controlled admixture convergence"
$nemoScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$NemoEnv' bash "`$ROOT/benchmarks/r41/run_nemo_r41.sh" "`$ROOT/benchmarks/r41/Nemo2_R41_B1.ini" "`$WORK/NEMO" "`$RESULT/NEMO.json"
"@
$nemoExec=Invoke-WslScript $nemoScript "NEMO" 1800 30
$benchmarks += Read-BenchmarkResult (Join-Path $ResultDir 'NEMO.json') 'NEMO' 'R41_NEMO_B1_ADMIXTURE_CONVERGENCE' $nemoExec
Write-Host "NEMO microbenchmark: $($benchmarks[-1].status)"

# Geonomics
Write-Host "[2/6] Geonomics default spatial demography"
$geoScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$GeoEnv' python "`$ROOT/benchmarks/r41/geonomics_r41.py" "`$RESULT/Geonomics.json" "`$WORK/Geonomics"
"@
$geoExec=Invoke-WslScript $geoScript "Geonomics" 3600 30
$benchmarks += Read-BenchmarkResult (Join-Path $ResultDir 'Geonomics.json') 'Geonomics' 'R41_GEONOMICS_DEFAULT_SPATIAL_DEMOGRAPHY' $geoExec
Write-Host "Geonomics microbenchmark: $($benchmarks[-1].status)"

# Madingley
Write-Host "[3/6] Madingley one-year ecosystem"
$madScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$REnv' bash "`$ROOT/benchmarks/r41/run_r_with_conda_libs.sh" "`$ROOT/benchmarks/r41/madingley_r41.R" "`$RESULT/Madingley.json" "`$WORK/Madingley"
"@
$madExec=Invoke-WslScript $madScript "Madingley" 3600 30
$benchmarks += Read-BenchmarkResult (Join-Path $ResultDir 'Madingley.json') 'Madingley' 'R41_MADINGLEY_ONE_YEAR_ECOSYSTEM' $madExec
Write-Host "Madingley microbenchmark: $($benchmarks[-1].status)"

# RangeShiftR
Write-Host "[4/6] RangeShiftR default range dynamics"
$rangeScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$REnv' bash "`$ROOT/benchmarks/r41/run_r_with_conda_libs.sh" "`$ROOT/benchmarks/r41/rangeshiftr_r41.R" "`$RESULT/RangeShifter.json" "`$WORK/RangeShifter"
"@
$rangeExec=Invoke-WslScript $rangeScript "RangeShiftR" 3600 30
$benchmarks += Read-BenchmarkResult (Join-Path $ResultDir 'RangeShifter.json') 'RangeShifter' 'R41_RANGESHIFTR_DEFAULT_RANGE_DYNAMICS' $rangeExec
Write-Host "RangeShiftR microbenchmark: $($benchmarks[-1].status)"

# CDMetaPOP
Write-Host "[5/6] CDMetaPOP pinned bundled 5-generation example"
$cdRootQ=Assert-ShellSafeValue $CdRootWsl 'CDMetaPOPRoot'
$cdScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
CDROOT=$cdRootQ
"`$CONDA_EXE" run -n '$CdEnv' python "`$ROOT/benchmarks/r41/cdmetapop_r41.py" "`$RESULT/CDMetaPOP.json" "`$WORK/CDMetaPOP" "`$CDROOT"
"@
$cdExec=Invoke-WslScript $cdScript "CDMetaPOP" 3600 30
$benchmarks += Read-BenchmarkResult (Join-Path $ResultDir 'CDMetaPOP.json') 'CDMetaPOP' 'R41_CDMETAPOP_BUNDLED_5GEN_EXAMPLE' $cdExec
Write-Host "CDMetaPOP microbenchmark: $($benchmarks[-1].status)"

# SLiM
Write-Host "[6/6] SLiM two-population tree-sequence gene flow"
$slimScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$SlimEnv' bash "`$ROOT/benchmarks/r41/run_slim_r41.sh" "`$ROOT/benchmarks/r41/R41_two_pop_gene_flow.slim" "`$ROOT/benchmarks/r41/slim_collect_r41.py" "`$WORK/SLiM" "`$RESULT/SLiM.json"
"@
$slimExec=Invoke-WslScript $slimScript "SLiM" 1800 30
$benchmarks += Read-BenchmarkResult (Join-Path $ResultDir 'SLiM.json') 'SLiM' 'R41_SLIM_TWO_POP_TREESEQ_GENE_FLOW' $slimExec
Write-Host "SLiM microbenchmark: $($benchmarks[-1].status)"

$passes=@($benchmarks | Where-Object {$_.status -eq 'PASS'})
$result=[ordered]@{
  stage='v0.6D1-R4.1'
  evidence_type='CONTROLLED_MULTI_ENGINE_MICROBENCHMARK_EVIDENCE'
  generated_by='capture_v0_6D1_R4_1_microbenchmarks.ps1'
  generated_at_utc=[DateTime]::UtcNow.ToString('o')
  canonical_state_changed=$false
  parent_runtime_identity_evidence=$RuntimeIdentityEvidence
  parent_runtime_identity_sha256=(Get-FileHash -Algorithm SHA256 $RuntimeIdentityEvidence).Hash.ToLowerInvariant()
  benchmark_count=$benchmarks.Count
  passed_benchmarks=$passes.Count
  benchmarks=$benchmarks
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $OutputPath
Write-Host "R4.1 microbenchmark evidence: $OutputPath"
Write-Host "Passed benchmarks: $($passes.Count)/6"
if($passes.Count -ne 6){ exit 3 }
exit 0
