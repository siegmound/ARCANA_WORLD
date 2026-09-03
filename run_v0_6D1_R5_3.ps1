param(
  [switch]$Resume,
  [switch]$PilotOnly,
  [int]$StreamTimeoutSeconds = 3600
)
$ErrorActionPreference='Stop'
$Root=(Get-Location).Path
$OutDir=Join-Path $Root 'outputs\v0_6D1_R5_3'

Write-Host '=== R5.3 source + immutable R5.2/R5.1/J14 authority ==='
python "$Root\scripts\check_v0_6D1_R5_3_source_manifest.py" --root "$Root"
if($LASTEXITCODE -ne 0){ throw 'R5.3 source manifest failed closed.' }
python "$Root\scripts\check_v0_6D1_R5_3_parent_authority.py" --root "$Root"
if($LASTEXITCODE -ne 0){ throw 'R5.3 parent authority failed closed.' }

Write-Host '=== R5.3 demographic-persistence regression (project-local pytest basetemp) ==='
$PytestBase=Join-Path $Root '.pytest_tmp\r53'
if(Test-Path $PytestBase){ Remove-Item -Recurse -Force $PytestBase }
New-Item -ItemType Directory -Force -Path $PytestBase | Out-Null
python -m pytest "$Root\tests\test_r53_corridor_conditioned_demography.py" -q --basetemp "$PytestBase"
if($LASTEXITCODE -ne 0){ throw 'R5.3 regression failed closed.' }

if((Test-Path $OutDir) -and -not $Resume){
  $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
  $archive=Join-Path $Root "outputs\v0_6D1_R5_3_attempt_$stamp"
  Move-Item $OutDir $archive
  Write-Host "Preserved prior R5.3 attempt: $archive"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host '=== R5.3 fresh Windows -> WSL -> Conda host binding ==='
$WslCommand=Get-Command wsl.exe -ErrorAction SilentlyContinue
if($null -eq $WslCommand){ throw 'R5.3 could not resolve wsl.exe from the current Windows host.' }
$WslExe=[string]$WslCommand.Source
if([string]::IsNullOrWhiteSpace($WslExe) -or -not (Test-Path $WslExe)){ throw "R5.3 invalid fresh WSL binding: $WslExe" }

$CondaOverride=[string]$env:ARCANA_CONDA_EXE
$CondaCandidates=@()
function Test-R53WslCondaCandidate {
  param([Parameter(Mandatory=$true)][string]$Candidate)
  if([string]::IsNullOrWhiteSpace($Candidate)){ return $null }
  # Direct WSL exec avoids PowerShell -> bash -lc quoting/argument parsing entirely.
  & $WslExe -e /usr/bin/test -x $Candidate 2>$null
  if($LASTEXITCODE -ne 0){ return $null }
  $probe=& $WslExe -e /usr/bin/readlink -f $Candidate 2>$null
  if($LASTEXITCODE -ne 0){ return $null }
  $resolved=(($probe | ForEach-Object { [string]$_ }) -join "`n").Trim()
  if([string]::IsNullOrWhiteSpace($resolved)){ return $null }
  return $resolved
}

if(-not [string]::IsNullOrWhiteSpace($CondaOverride)){
  $resolved=Test-R53WslCondaCandidate $CondaOverride
  if([string]::IsNullOrWhiteSpace($resolved)){
    throw "R5.3 ARCANA_CONDA_EXE is not an executable WSL conda path: $CondaOverride"
  }
  $CondaCandidates=@($resolved)
}else{
  # Governed path already established in the post-R4 runtime history for this project.
  # It is a preferred discovery candidate, not a bypass: executability is freshly rechecked.
  $KnownCandidates=@(
    '/home/jose/miniforge3/bin/conda'
  )
  foreach($candidate in $KnownCandidates){
    $resolved=Test-R53WslCondaCandidate $candidate
    if(-not [string]::IsNullOrWhiteSpace($resolved)){ $CondaCandidates += $resolved }
  }

  # Do not embed a bash discovery loop inside PowerShell: mixed quoting caused a parser
  # failure before any scientific execution. Probe only explicit governed candidates.
  # Additional installations remain available through ARCANA_CONDA_EXE, which is fail-closed.
  $CondaCandidates=@($CondaCandidates | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
}
if($CondaCandidates.Count -eq 0){ throw 'R5.3 found no executable Conda installation in WSL. Set ARCANA_CONDA_EXE=/home/jose/miniforge3/bin/conda (or another governed path) explicitly.' }
if($CondaCandidates.Count -ne 1){ throw ("R5.3 found multiple WSL Conda installations and refuses an arbitrary choice: {0}. Set ARCANA_CONDA_EXE explicitly." -f ($CondaCandidates -join ', ')) }
$CondaPath=[string]$CondaCandidates[0]

$HostBinding=[ordered]@{
  stage='v0.6D1-R5.3'
  status='PASS_R53_FRESH_HOST_RUNTIME_BINDING'
  binding_semantics='FRESH_WINDOWS_WSL_CONDA_PROCESS_BOUNDARY_BINDING_POST_R456; CDMETAPOP_VERSION_PIN_AND_ENV_VALIDATED_SEPARATELY'
  legacy_r41_runtime_identity_required=$false
  wsl_executable=$WslExe
  conda_binding=$CondaPath
  conda_override_used=(-not [string]::IsNullOrWhiteSpace($CondaOverride))
}
$HostBinding | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $OutDir 'R5_3_HOST_RUNTIME_BINDING.json')
$HostBinding | ConvertTo-Json -Depth 6 | Write-Host

function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  $full=[System.IO.Path]::GetFullPath($Path)
  if($full -match '^([A-Za-z]):\\(.*)$'){
    $drive=$Matches[1].ToLowerInvariant(); $rest=$Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "Unsupported Windows path for WSL bridge: $full"
}
function ShellQuote {
  param([Parameter(Mandatory=$true)][string]$Value)
  if($Value.Contains("'")){ throw "R5.3 WSL bridge refuses single quote in value: $Value" }
  return "'$Value'"
}
function Invoke-WslScript {
  param([Parameter(Mandatory=$true)][string]$Script,[Parameter(Mandatory=$true)][string]$Label,[int]$TimeoutSeconds=3600,[int]$HeartbeatSeconds=60)
  $psi=[System.Diagnostics.ProcessStartInfo]::new(); $psi.FileName=$WslExe; $psi.Arguments='bash -s'; $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.CreateNoWindow=$true
  $p=[System.Diagnostics.Process]::new(); $p.StartInfo=$psi
  if(-not $p.Start()){ throw "Could not start WSL bridge for $Label" }
  $stdoutTask=$p.StandardOutput.ReadToEndAsync(); $stderrTask=$p.StandardError.ReadToEndAsync(); $p.StandardInput.Write($Script); $p.StandardInput.Close()
  $sw=[System.Diagnostics.Stopwatch]::StartNew(); $next=[double]$HeartbeatSeconds; $timedOut=$false
  while(-not $p.WaitForExit(1000)){
    if($sw.Elapsed.TotalSeconds -ge $TimeoutSeconds){ $timedOut=$true; try{$p.Kill($true)}catch{try{$p.Kill()}catch{}}; break }
    if($sw.Elapsed.TotalSeconds -ge $next){ Write-Host ("  {0}: still running ({1:n0}s elapsed)" -f $Label,$sw.Elapsed.TotalSeconds); $next += [double]$HeartbeatSeconds }
  }
  if($timedOut){$p.WaitForExit()}; $stdout=$stdoutTask.GetAwaiter().GetResult(); $stderr=$stderrTask.GetAwaiter().GetResult(); $sw.Stop()
  [pscustomobject]@{ExitCode=if($timedOut){124}else{$p.ExitCode};Stdout=$stdout;Stderr=$stderr;ElapsedSeconds=[math]::Round($sw.Elapsed.TotalSeconds,3);TimedOut=$timedOut}
}
function Tail([string]$Text,[int]$N=5000){ if([string]::IsNullOrEmpty($Text)){return ''}; if($Text.Length -le $N){return $Text}; return $Text.Substring($Text.Length-$N) }

$RootWsl=Convert-ArcanaWindowsPathToWsl $Root
$OutWsl=Convert-ArcanaWindowsPathToWsl $OutDir
$EngineWsl=Convert-ArcanaWindowsPathToWsl (Join-Path $Root '.arcana_engines\CDMetaPOP-3.08')
$RootQ=ShellQuote $RootWsl; $OutQ=ShellQuote $OutWsl; $EngineQ=ShellQuote $EngineWsl; $CondaQ=ShellQuote $CondaPath
$Preferred=[string]$env:ARCANA_CDMETAPOP_CONDA_ENV
$PreferredArg=if([string]::IsNullOrWhiteSpace($Preferred)){''}else{" --preferred-env " + (ShellQuote $Preferred)}

Write-Host '=== R5.3 fresh CDMetaPOP 3.08 pinned runtime identity ==='
$runtimeScript=@"
set -euo pipefail
CONDA_EXE=$CondaQ
BASE_PY="`$(dirname "`$CONDA_EXE")/python"
"`$BASE_PY" $RootQ/benchmarks/r53/discover_cdmetapop_runtime_r53.py --conda-exe $CondaQ --engine-root $EngineQ --out $OutQ/R5_3_CDMETAPOP_RUNTIME_IDENTITY.json$PreferredArg
"@
$rx=Invoke-WslScript $runtimeScript 'CDMetaPOP runtime discovery' 900 30
if($rx.ExitCode -ne 0){ Write-Host (Tail $rx.Stdout); Write-Host (Tail $rx.Stderr); throw 'R5.3 CDMetaPOP runtime discovery failed closed.' }
Get-Content -Raw (Join-Path $OutDir 'R5_3_CDMETAPOP_RUNTIME_IDENTITY.json') | Write-Host
$Runtime=Get-Content -Raw (Join-Path $OutDir 'R5_3_CDMETAPOP_RUNTIME_IDENTITY.json') | ConvertFrom-Json
$EnvPrefix=[string]$Runtime.conda_env_prefix
if([string]::IsNullOrWhiteSpace($EnvPrefix)){ throw 'R5.3 runtime identity missing conda env prefix.' }
$EnvQ=ShellQuote $EnvPrefix

Write-Host '=== R5.3 prepare 12-family x 3-stress CDMetaPOP challenge ==='
python "$Root\scripts\prepare_v0_6D1_R5_3.py" --root "$Root"
if($LASTEXITCODE -ne 0){ throw 'R5.3 demographic challenge preparation failed closed.' }
$Plan=Get-Content -Raw (Join-Path $OutDir 'R5_3_CDMETAPOP_EXECUTION_PLAN.json') | ConvertFrom-Json
$Groups=@($Plan.groups)
if($Groups.Count -ne 36){ throw "R5.3 expected 36 groups, got $($Groups.Count)" }

function Invoke-R53Stream($g,[int]$seed,[bool]$AllowResume){
  $gid=[string]$g.group_id
  $EvDir=Join-Path $Root ([string]$g.evidence_dir)
  $SeedDir=Join-Path $EvDir ("seed_{0}" -f $seed)
  $Summary=Join-Path $SeedDir 'summary_popAllTime.csv'; $Meta=Join-Path $SeedDir 'STREAM_RUNTIME.json'
  if($AllowResume -and (Test-Path $Summary) -and (Test-Path $Meta)){
    try{ $m=Get-Content -Raw $Meta | ConvertFrom-Json; if([int]$m.seed -eq $seed -and [string]$m.status -eq 'PASS_R53_CDMETAPOP_STREAM' -and [string]$m.cdmetapop_commit -eq '3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'){ return [pscustomobject]@{Mode='RESUMED';ExitCode=0;ElapsedSeconds=0;TimedOut=$false;Stdout='';Stderr=''} } }catch{}
  }
  if(Test-Path $SeedDir){Remove-Item -Recurse -Force $SeedDir}; New-Item -ItemType Directory -Force -Path $SeedDir | Out-Null
  $InputDir=Join-Path $Root ([string]$g.input_dir)
  $InputWsl=Convert-ArcanaWindowsPathToWsl $InputDir; $EvWsl=Convert-ArcanaWindowsPathToWsl $SeedDir
  $InputQ=ShellQuote $InputWsl; $EvQ=ShellQuote $EvWsl
  $prefix="r53_$($g.group_numeric_id)_$seed`_"
  $PrefixQ=ShellQuote $prefix
  $script=@"
set -euo pipefail
$CondaQ run -p $EnvQ python $RootQ/benchmarks/r53/cdmetapop_r53_seeded_launcher.py --engine-root $EngineQ --data-dir $InputQ --runvars RunVars_R53.csv --output-prefix $PrefixQ --seed $seed --evidence-dir $EvQ
"@
  $ex=Invoke-WslScript $script "$gid seed=$seed" $StreamTimeoutSeconds 60
  return [pscustomobject]@{Mode='LIVE_EXECUTION';ExitCode=$ex.ExitCode;ElapsedSeconds=$ex.ElapsedSeconds;TimedOut=$ex.TimedOut;Stdout=$ex.Stdout;Stderr=$ex.Stderr}
}

Write-Host '=== R5.3 CDMetaPOP pilot: first family/stress/seed before full corpus ==='
$First=$Groups[0]; $FirstSeed=530301
$px=Invoke-R53Stream $First $FirstSeed $Resume
if($px.ExitCode -ne 0){Write-Host (Tail $px.Stdout); Write-Host (Tail $px.Stderr); throw 'R5.3 CDMetaPOP pilot execution failed closed before full corpus.'}
python "$Root\scripts\check_v0_6D1_R5_3_pilot.py" --root "$Root"
if($LASTEXITCODE -ne 0){ throw 'R5.3 CDMetaPOP pilot evidence failed closed before full corpus.' }
if($PilotOnly){ Write-Host 'PASS_R53_CDMETAPOP_PILOT_ONLY'; exit 0 }

Write-Host ("=== R5.3 CDMetaPOP targeted execution: {0} groups / {1} streams ===" -f $Groups.Count,[int]$Plan.planned_stream_count)
$bridge=@(); $streamIndex=0
foreach($g in $Groups){
  foreach($seed in @(530301,530302)){
    $streamIndex++; $gid=[string]$g.group_id
    Write-Host ("[{0}/{1}] {2} seed={3}" -f $streamIndex,[int]$Plan.planned_stream_count,$gid,$seed)
    $ex=Invoke-R53Stream $g $seed $true
    $bridge += [ordered]@{group_id=$gid;seed=$seed;mode=$ex.Mode;exit_code=[int]$ex.ExitCode;elapsed_seconds=[double]$ex.ElapsedSeconds;timed_out=[bool]$ex.TimedOut;stdout_tail=(Tail ([string]$ex.Stdout));stderr_tail=(Tail ([string]$ex.Stderr))}
    if($ex.ExitCode -eq 0){ Write-Host ("  {0}" -f $(if($ex.Mode -eq 'RESUMED'){'RESUME'}else{'PASS'})) } else { Write-Host '  BLOCKED/FAILED (preserved; continuing)' }
  }
}
[ordered]@{stage='v0.6D1-R5.3';status='R53_POWERSHELL_WSL_CDMETAPOP_EXECUTION_BRIDGE';stream_count=$bridge.Count;records=$bridge} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $OutDir 'R5_3_CDMETAPOP_EXECUTION_BRIDGE.json')

Write-Host '=== R5.3 governed CDMetaPOP demographic persistence/bottleneck analysis ==='
python "$Root\scripts\analyze_v0_6D1_R5_3.py" --root "$Root"
if($LASTEXITCODE -ne 0){ throw 'R5.3 CDMetaPOP evidence analysis failed closed. Raw evidence has been preserved.' }
Write-Host 'PASS_R53_INTEGRATED_CDMETAPOP_DEMOGRAPHIC_EVIDENCE_CANDIDATE_RUN'
Write-Host 'R5.3 remains CANDIDATE by design; no micro-seal is created at this stage.'
