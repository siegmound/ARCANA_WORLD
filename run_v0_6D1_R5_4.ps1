param(
  [string]$CondaEnv = "arcana-nemo242",
  [int]$ParallelJobs = 6,
  [switch]$Resume,
  [switch]$AllowNonScientificDevParent
)
$ErrorActionPreference='Stop'
$Root=(Get-Location).Path
$env:PYTHONPATH=Join-Path $Root 'src'

function Convert-ArcanaWindowsPathToWsl {
  param([Parameter(Mandatory=$true)][string]$Path)
  $full=[System.IO.Path]::GetFullPath($Path)
  if($full -match '^([A-Za-z]):\\(.*)$'){
    $drive=$Matches[1].ToLowerInvariant(); $rest=$Matches[2] -replace '\\','/'
    return "/mnt/$drive/$rest"
  }
  throw "R5.4 requires a Windows drive path for WSL execution: $full"
}

Write-Host '=== R5.4 source + immutable R5.3/R5.2/R5.1/J14 authority ==='
python scripts/check_v0_6D1_R5_4_source_manifest.py --root $Root
if($LASTEXITCODE -ne 0){ throw 'R5.4 source manifest failed closed.' }
$parentArgs=@('scripts/check_v0_6D1_R5_4_parent_authority.py','--root',$Root)
if($AllowNonScientificDevParent){ $parentArgs += '--allow-non-scientific-dev' }
python @parentArgs
if($LASTEXITCODE -ne 0){ throw 'R5.4 parent authority failed closed.' }

Write-Host '=== R5.4 genetic-robustness regression (project-local pytest basetemp) ==='
$PytestBase=Join-Path $Root '.pytest_tmp\r54'
if(Test-Path $PytestBase){ Remove-Item -Recurse -Force $PytestBase }
New-Item -ItemType Directory -Force -Path $PytestBase | Out-Null
python -m pytest tests/test_r54_nemo_genetic_robustness.py -q --basetemp $PytestBase
if($LASTEXITCODE -ne 0){ throw 'R5.4 regression failed closed.' }

$Out=Join-Path $Root 'outputs\v0_6D1_R5_4'
if(-not $Resume){
  if(Test-Path $Out){
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $dst=Join-Path $Root "outputs\v0_6D1_R5_4_attempt_$stamp"
    Move-Item $Out $dst; Write-Host "Preserved prior R5.4 attempt: $dst"
  }
  New-Item -ItemType Directory -Force -Path $Out | Out-Null
} elseif(-not (Test-Path $Out)) {
  throw 'R5.4 -Resume requested but outputs\v0_6D1_R5_4 does not exist.'
}

Write-Host '=== R5.4 fresh Windows -> WSL -> Conda -> NEMO 2.4.2 binding ==='
$WslExe=(Get-Command wsl.exe -ErrorAction Stop).Source
$CondaPath = if($env:ARCANA_CONDA_EXE){ $env:ARCANA_CONDA_EXE } else { '/home/jose/miniforge3/bin/conda' }
& $WslExe -e /usr/bin/test -x $CondaPath
if($LASTEXITCODE -ne 0){ throw "R5.4 governed Conda executable unavailable: $CondaPath" }
$PkgJson=(& $WslExe -e $CondaPath list -n $CondaEnv --json nemo 2>$null | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PkgJson)){ throw "R5.4 could not query NEMO Conda package identity in env $CondaEnv" }
try { $PkgRows=@($PkgJson | ConvertFrom-Json) } catch { throw "R5.4 could not parse NEMO Conda package identity: $($_.Exception.Message)" }
$NemoPkg=@($PkgRows | Where-Object { $_.name -eq 'nemo' -and $_.version -eq '2.4.2' })
if($NemoPkg.Count -ne 1){ throw "R5.4 requires exactly one nemo=2.4.2 package in Conda env $CondaEnv; found $($NemoPkg.Count)." }
$NemoExe=(& $WslExe -e $CondaPath run -n $CondaEnv /usr/bin/which nemo2.4.2 2>$null | Select-Object -Last 1).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($NemoExe)){ throw "R5.4 nemo2.4.2 unavailable in Conda env $CondaEnv" }
$HashLine=(& $WslExe -e /usr/bin/sha256sum $NemoExe | Select-Object -First 1).Trim()
if($LASTEXITCODE -ne 0 -or $HashLine -notmatch '^([0-9a-fA-F]{64})\s+'){ throw 'R5.4 could not hash resolved NEMO executable.' }
$NemoHash=$Matches[1].ToLowerInvariant()
$Runtime=[ordered]@{stage='v0.6D1-R5.4';status='PASS_R54_NEMO_2_4_2_PINNED_RUNTIME_IDENTITY';nemo_version='2.4.2';nemo_executable_name='nemo2.4.2';nemo_executable=$NemoExe;nemo_executable_sha256=$NemoHash;conda_package_name=[string]$NemoPkg[0].name;conda_package_version=[string]$NemoPkg[0].version;conda_package_build=[string]$NemoPkg[0].build_string;conda_package_channel=[string]$NemoPkg[0].channel;conda_executable=$CondaPath;conda_env_name=$CondaEnv;wsl_executable=$WslExe;selection_semantics='EXACT_CONDA_PACKAGE_VERSION_PLUS_EXPLICIT_VERSION_STAMPED_EXECUTABLE_IN_GOVERNED_ENV_NO_FALLBACK_VERSION'}
$Runtime | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 (Join-Path $Out 'R5_4_NEMO_RUNTIME_IDENTITY.json')
$Runtime | ConvertTo-Json -Depth 6

if(-not $Resume){
  Write-Host '=== R5.4 prepare 12-family x 3-stress x FLOW/control NEMO challenge ==='
  $prep=@('scripts/prepare_v0_6D1_R5_4.py','--root',$Root)
  if($AllowNonScientificDevParent){ $prep += '--allow-non-scientific-dev-parent' }
  python @prep
  if($LASTEXITCODE -ne 0){ throw 'R5.4 challenge preparation failed closed.' }
} else {
  if(-not (Test-Path (Join-Path $Out 'R5_4_NEMO_EXECUTION_PLAN.json'))){ throw 'R5.4 resume requires preserved execution plan.' }
  Write-Host '=== R5.4 resume preserved execution plan ==='
}

$Plan=Get-Content -Raw (Join-Path $Out 'R5_4_NEMO_EXECUTION_PLAN.json') | ConvertFrom-Json
$StreamRunnerWin=(Resolve-Path 'benchmarks\r54\run_nemo_r54_stream.sh').Path
$StreamRunnerWsl=Convert-ArcanaWindowsPathToWsl $StreamRunnerWin

if(-not $Resume){
  Write-Host '=== R5.4 NEMO pilot: first family/stress FLOW + matched no-flow ==='
  $pilot=@($Plan.streams | Where-Object { $_.group_numeric_id -eq 1 -and $_.seed -eq 540401 } | Sort-Object variant)
  if($pilot.Count -ne 2){ throw "R5.4 expected 2 pilot streams, got $($pilot.Count)" }
  foreach($s in $pilot){
    $wdWin=Join-Path $Root (($s.work_dir) -replace '/','\'); $wdWsl=Convert-ArcanaWindowsPathToWsl $wdWin
    $seedStr=[string]$s.seed; $variantStr=[string]$s.variant
    & $WslExe -e bash $StreamRunnerWsl $wdWsl $CondaPath $CondaEnv $seedStr $variantStr
    if($LASTEXITCODE -ne 0){ throw "R5.4 NEMO pilot $($s.variant) failed closed before full corpus." }
  }
  python scripts/check_v0_6D1_R5_4_pilot.py --root $Root
  if($LASTEXITCODE -ne 0){ throw 'R5.4 NEMO pilot evidence failed closed.' }
}

Write-Host '=== R5.4 NEMO targeted execution: 36 groups / 144 streams ==='
$RunnerWin=(Resolve-Path 'benchmarks\r54\run_nemo_r54_suite.sh').Path; $RunnerWsl=Convert-ArcanaWindowsPathToWsl $RunnerWin
$OutWsl=Convert-ArcanaWindowsPathToWsl $Out
& $WslExe -e bash $RunnerWsl $OutWsl $CondaPath $CondaEnv $StreamRunnerWsl ([string]$ParallelJobs)
if($LASTEXITCODE -ne 0){ throw 'R5.4 NEMO full targeted execution failed closed.' }
python scripts/build_v0_6D1_R5_4_execution_bridge.py --root $Root
if($LASTEXITCODE -ne 0){ throw 'R5.4 execution bridge integrity failed closed.' }

Write-Host '=== R5.4 governed NEMO cross-engine genetic robustness analysis ==='
$ana=@('scripts/analyze_v0_6D1_R5_4.py','--root',$Root)
if($AllowNonScientificDevParent){ $ana += '--allow-non-scientific-dev-parent' }
python @ana
if($LASTEXITCODE -ne 0){ throw 'R5.4 governed evidence analysis failed closed.' }
Write-Host 'PASS_R54_CROSS_ENGINE_GENETIC_ROBUSTNESS_AND_GENE_FLOW_EVIDENCE_CANDIDATE_RUN'
Write-Host 'PASS_R54_INTEGRATED_NEMO_GENETIC_EVIDENCE_CANDIDATE_RUN'
Write-Host 'R5.4 remains CANDIDATE by design; no micro-seal is created at this stage.'
