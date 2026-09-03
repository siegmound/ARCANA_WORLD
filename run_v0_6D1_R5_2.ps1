param(
  [switch]$Resume,
  [switch]$ProbeOnly,
  [switch]$SealOnly,
  [int]$GroupTimeoutSeconds = 7200
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r52"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

Write-Host "=== R5.2-R1 source-initialisation repair + immutable R5.1/J14/provider authority ==="
python "$Root\scripts\check_v0_6D1_R5_2_source_manifest.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.2 source/parent authority failed closed." }

Write-Host "=== R5.2 targeted-corridor + final-seal regression ==="
python -m pytest "$Root\tests\test_r52_targeted_corridors.py" "$Root\tests\test_r52_final_seal.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R5.2 regression failed closed." }

if($SealOnly){
  Write-Host "=== R5.2 seal-only: recompute readout from preserved raw corpus + final scientific seal ==="
  python "$Root\scripts\seal_v0_6D1_R5_2.py" --root "$Root"
  if ($LASTEXITCODE -ne 0) { throw "R5.2 seal-only final scientific seal failed closed." }
  Write-Host "PASS_R52_SEAL_ONLY_RUN"
  Write-Host "PASS_R52_INTEGRATED_AND_FINAL_SEAL_RUN"
  exit 0
}

$OutDir = Join-Path $Root "outputs\v0_6D1_R5_2"
# R5.2-R1 repair-history guard: pre-R1 summaries lack the explicit source-
# initialisation provenance column and must never be resumed, overwritten or
# reinterpreted as corridor evidence. Preserve them under a repair-history path.
if (Test-Path $OutDir) {
  $preR1 = $false
  $summaries = @(Get-ChildItem -Path $OutDir -Recurse -Filter "STREAM_SUMMARY.tsv" -ErrorAction SilentlyContinue)
  foreach($sf in $summaries){
    $first = Get-Content -Path $sf.FullName -TotalCount 1
    if($first -and $first -notmatch "initialization_mode"){ $preR1 = $true; break }
  }
  if($preR1){
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $archive = Join-Path $Root "outputs\v0_6D1_R5_2_BLOCKED_PRE_R1_FREE_INIT_$stamp"
    Move-Item $OutDir $archive
    [ordered]@{
      stage='v0.6D1-R5.2';
      status='REJECTED_R52_PRE_R1_FREE_INITIALISATION_EVIDENCE_PRESERVED';
      reason='SpDistFile source.asc was supplied but Initialise InitType=0 selected free initialisation rather than source-distribution initialisation';
      scientific_use_forbidden=$true;
      rerun_required=$true;
      repair='R5.2-R1 uses InitType=1 SpType=0 InitDens=1 and an exact source-binding preflight before full execution'
    } | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $archive 'R5_2_PRE_R1_REJECTION.json')
    Write-Host "R5.2-R1 preserved blocked pre-repair free-initialisation corpus: $archive"
    $Resume = $false
  }
}
if ((Test-Path $OutDir) -and -not $Resume) {
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $archive = Join-Path $Root "outputs\v0_6D1_R5_2_attempt_$stamp"
  Move-Item $OutDir $archive
  Write-Host "Preserved prior R5.2 evidence attempt: $archive"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$RuntimeBindingPath = Join-Path $Root "outputs\v0_6D1_R4_1\R4_1_RUNTIME_IDENTITY_EVIDENCE.json"
if (-not (Test-Path $RuntimeBindingPath)) { throw "R5.2 runtime path discovery requires historical governed R4.1 runtime identity evidence: $RuntimeBindingPath" }
$Binding = Get-Content -Raw $RuntimeBindingPath | ConvertFrom-Json
$WslExe = [string]$Binding.wsl_executable
$CondaPath = [string]$Binding.conda_binding
if ([string]::IsNullOrWhiteSpace($WslExe) -or -not (Test-Path $WslExe)) { throw "R5.2 invalid WSL binding: $WslExe" }
if ([string]::IsNullOrWhiteSpace($CondaPath)) { throw "R5.2 invalid Conda binding." }
$REnv = if($env:ARCANA_R40_R_CONDA_ENV){$env:ARCANA_R40_R_CONDA_ENV}else{'arcana-r40-r'}

function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  $full=[System.IO.Path]::GetFullPath($Path)
  if($full -match '^([A-Za-z]):\\(.*)$'){
    $drive=$Matches[1].ToLowerInvariant(); $rest=$Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "Unsupported ARCANA Windows path for WSL bridge: $full"
}
function ShellQuote {
  param([Parameter(Mandatory=$true)][string]$Value)
  if($Value.Contains("'")){ throw "R5.2 governed WSL bridge refuses path/value containing single quote: $Value" }
  return "'$Value'"
}
function Invoke-WslScript {
  param(
    [Parameter(Mandatory=$true)][string]$Script,
    [Parameter(Mandatory=$true)][string]$Label,
    [int]$TimeoutSeconds=7200,
    [int]$HeartbeatSeconds=60
  )
  $psi=[System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$WslExe; $psi.Arguments="bash -s"; $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.CreateNoWindow=$true
  $p=[System.Diagnostics.Process]::new(); $p.StartInfo=$psi
  if(-not $p.Start()){ throw "Could not start governed WSL bridge for $Label" }
  $stdoutTask=$p.StandardOutput.ReadToEndAsync(); $stderrTask=$p.StandardError.ReadToEndAsync()
  $p.StandardInput.Write($Script); $p.StandardInput.Close()
  $sw=[System.Diagnostics.Stopwatch]::StartNew(); $next=[double]$HeartbeatSeconds; $timedOut=$false
  while(-not $p.WaitForExit(1000)){
    if($sw.Elapsed.TotalSeconds -ge $TimeoutSeconds){
      $timedOut=$true; try{$p.Kill($true)}catch{try{$p.Kill()}catch{}}; break
    }
    if($sw.Elapsed.TotalSeconds -ge $next){
      Write-Host ("  {0}: still running ({1:n0}s elapsed)" -f $Label,$sw.Elapsed.TotalSeconds)
      $next += [double]$HeartbeatSeconds
    }
  }
  if($timedOut){$p.WaitForExit()}
  $stdout=$stdoutTask.GetAwaiter().GetResult(); $stderr=$stderrTask.GetAwaiter().GetResult(); $sw.Stop()
  [pscustomobject]@{ExitCode=if($timedOut){124}else{$p.ExitCode};Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3);TimedOut=$timedOut}
}
function Get-Tail([string]$Text,[int]$N=4000){ if([string]::IsNullOrEmpty($Text)){return ''}; if($Text.Length -le $N){return $Text}; return $Text.Substring($Text.Length-$N) }

$RootWsl = Convert-ArcanaWindowsPathToWsl $Root
$OutWsl = Convert-ArcanaWindowsPathToWsl $OutDir
$RootQ=ShellQuote $RootWsl; $OutQ=ShellQuote $OutWsl; $CondaQ=ShellQuote $CondaPath

Write-Host "=== R5.2 fresh RangeShiftR 3.0.1 runtime identity ==="
$runtimeScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
OUT=$OutQ
"`$CONDA_EXE" run -n '$REnv' bash "`$ROOT/benchmarks/r41/run_r_with_conda_libs.sh" "`$ROOT/benchmarks/r52/check_rangeshiftr_r52.R" "`$OUT/R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json"
"@
$runtimeExec=Invoke-WslScript $runtimeScript "RangeShiftR runtime identity" 900 30
if($runtimeExec.ExitCode -ne 0){
  Write-Host (Get-Tail $runtimeExec.Stdout); Write-Host (Get-Tail $runtimeExec.Stderr)
  throw "R5.2 fresh RangeShiftR runtime identity failed closed."
}
Get-Content -Raw (Join-Path $OutDir "R5_2_RANGESHIFTER_RUNTIME_IDENTITY.json") | Write-Host

Write-Host "=== R5.2 prepare 12-family targeted dynamic-landscape corridor challenge ==="
python "$Root\scripts\prepare_v0_6D1_R5_2.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.2 corridor execution plan preparation failed closed." }

$PlanPath = Join-Path $OutDir "R5_2_RANGE_EXECUTION_PLAN.json"
$Plan = Get-Content -Raw $PlanPath | ConvertFrom-Json
$Groups = @($Plan.groups | Where-Object { $_.executable -eq $true })
if($Groups.Count -lt 1){ throw "R5.2-R1 source binding probe requires at least one executable group." }

Write-Host "=== R5.2-R1 RangeShiftR source-binding preflight (1 engine year, before full corpus) ==="
$ProbeDir = Join-Path $OutDir "source_binding_probe"
if(Test-Path $ProbeDir){ Remove-Item -Recurse -Force $ProbeDir }
$ProbeInputs=Join-Path $ProbeDir "Inputs"; $ProbeEvidence=Join-Path $ProbeDir "Evidence"
New-Item -ItemType Directory -Force -Path $ProbeInputs,$ProbeEvidence | Out-Null
$FirstGroup=$Groups[0]
$FirstInputDir=Join-Path $Root ([string]$FirstGroup.input_dir)
Copy-Item (Join-Path $FirstInputDir "habitat_000.asc") (Join-Path $ProbeInputs "habitat_000.asc")
Copy-Item (Join-Path $FirstInputDir "source.asc") (Join-Path $ProbeInputs "source.asc")
$ProbeWsl=Convert-ArcanaWindowsPathToWsl $ProbeDir; $ProbeQ=ShellQuote $ProbeWsl
$probeScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
PROBE=$ProbeQ
"`$CONDA_EXE" run -n '$REnv' bash "`$ROOT/benchmarks/r41/run_r_with_conda_libs.sh" "`$ROOT/benchmarks/r52/probe_rangeshiftr_r52_source_binding.R" "`$PROBE"
"@
$probeExec=Invoke-WslScript $probeScript "R5.2-R1 source binding probe" 900 30
if($probeExec.ExitCode -ne 0){
  Write-Host (Get-Tail $probeExec.Stdout); Write-Host (Get-Tail $probeExec.Stderr)
  throw "R5.2-R1 RangeShiftR source binding probe execution failed closed before full corpus."
}
python "$Root\scripts\check_v0_6D1_R5_2_source_binding_probe.py" --root "$Root"
if($LASTEXITCODE -ne 0){ throw "R5.2-R1 source binding probe failed closed before full 80-stream corpus." }
if($ProbeOnly){
  Write-Host "PASS_R52_R1_SOURCE_BINDING_PREFLIGHT_ONLY"
  exit 0
}

Write-Host ("=== R5.2 RangeShiftR targeted execution: {0} groups / {1} streams ===" -f $Groups.Count,[int]$Plan.planned_stream_count)
$bridge=@()
$idx=0
foreach($g in $Groups){
  $idx++
  $gid=[string]$g.group_id
  $GroupDir = Split-Path -Parent (Join-Path $Root ([string]$g.input_dir))
  $EvidenceDir = Join-Path $GroupDir "Evidence"
  $SummaryPath = Join-Path $EvidenceDir "STREAM_SUMMARY.tsv"
  $resumeComplete=$false
  if($Resume -and (Test-Path $SummaryPath)){
    $lines=@(Get-Content $SummaryPath)
    $passLines=@($lines | Select-Object -Skip 1 | Where-Object { $_ -match "\tPASS\t" })
    $occ=@(Get-ChildItem -Path $EvidenceDir -Filter "occupancy_*.tsv.gz" -ErrorAction SilentlyContinue)
    $headerOk = $lines.Count -ge 1 -and $lines[0] -match "initialization_mode"
    $initRows=@($lines | Select-Object -Skip 1 | Where-Object { $_ -match "\tSPDIST_INITTYPE1_SPTYPE0\t" })
    if($lines.Count -eq 5 -and $passLines.Count -eq 4 -and $occ.Count -eq 4 -and $headerOk -and $initRows.Count -eq 4){ $resumeComplete=$true }
  }
  if($resumeComplete){
    Write-Host ("[{0}/{1}] {2}: RESUME existing complete evidence" -f $idx,$Groups.Count,$gid)
    $bridge += [ordered]@{group_id=$gid;mode='RESUMED_EXISTING_COMPLETE_EVIDENCE';exit_code=0;elapsed_seconds=0;timed_out=$false;stdout_tail='';stderr_tail=''}
    continue
  }
  foreach($sub in @("Outputs","Output_Maps","Evidence")){
    $p=Join-Path $GroupDir $sub
    if(Test-Path $p){Remove-Item -Recurse -Force $p}
  }
  New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
  $GroupWsl=Convert-ArcanaWindowsPathToWsl $GroupDir; $GroupQ=ShellQuote $GroupWsl
  Write-Host ("[{0}/{1}] {2}" -f $idx,$Groups.Count,$gid)
  $script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
GROUP=$GroupQ
"`$CONDA_EXE" run -n '$REnv' bash "`$ROOT/benchmarks/r41/run_r_with_conda_libs.sh" "`$ROOT/benchmarks/r52/rangeshiftr_r52_group.R" "`$GROUP" '$([int]$g.group_numeric_id)' '$gid'
"@
  $ex=Invoke-WslScript $script $gid $GroupTimeoutSeconds 60
  $bridge += [ordered]@{group_id=$gid;mode='LIVE_EXECUTION';exit_code=[int]$ex.ExitCode;elapsed_seconds=[double]$ex.ElapsedSeconds;timed_out=[bool]$ex.TimedOut;stdout_tail=(Get-Tail ([string]$ex.Stdout));stderr_tail=(Get-Tail ([string]$ex.Stderr))}
  if($ex.ExitCode -eq 0){Write-Host "  PASS"}else{Write-Host "  BLOCKED/FAILED (preserved; continuing remaining groups)"}
}
$BridgePath=Join-Path $OutDir "R5_2_RANGE_EXECUTION_BRIDGE.json"
[ordered]@{stage='v0.6D1-R5.2';status='R52_POWERSHELL_WSL_RANGESHIFTER_EXECUTION_BRIDGE';group_count=$Groups.Count;records=$bridge} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $BridgePath

Write-Host "=== R5.2 governed RangeShiftR corridor evidence analysis ==="
python "$Root\scripts\analyze_v0_6D1_R5_2.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.2 targeted RangeShiftR evidence analysis failed closed. Raw evidence has been preserved." }
Write-Host "PASS_R52_INTEGRATED_TARGETED_RANGESHIFTER_CORRIDOR_EVIDENCE_CANDIDATE_RUN"
Write-Host "=== R5.2 descriptive evidence structure + final scientific seal ==="
python "$Root\scripts\seal_v0_6D1_R5_2.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.2 final scientific seal failed closed." }
Write-Host "PASS_R52_INTEGRATED_AND_FINAL_SEAL_RUN"
