param(
  [string]$CondaEnv = "arcana-slim52",
  [int]$ParallelJobs = 4,
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
  throw "R5.6 requires a Windows drive path for WSL execution: $full"
}

Write-Host '=== R5.6 source + immutable R5.5/R5.4/R5.3/R5.2/R5.1/J14 candidate authority ==='
python scripts/check_v0_6D1_R5_6_source_manifest.py --root $Root
if($LASTEXITCODE -ne 0){ throw 'R5.6 source manifest failed closed.' }
$parentArgs=@('scripts/check_v0_6D1_R5_6_parent_authority.py','--root',$Root)
if($AllowNonScientificDevParent){ $parentArgs += '--allow-non-scientific-dev' }
python @parentArgs
if($LASTEXITCODE -ne 0){ throw 'R5.6 parent candidate authority failed closed.' }

Write-Host '=== R5.6 ancestry/admixture regression (project-local pytest basetemp) ==='
$PytestBase=Join-Path $Root '.pytest_tmp\r56'
if(Test-Path $PytestBase){ Remove-Item -Recurse -Force $PytestBase }
New-Item -ItemType Directory -Force -Path $PytestBase | Out-Null
python -m pytest tests/test_r56_slim_ancestry.py -q --basetemp $PytestBase
if($LASTEXITCODE -ne 0){ throw 'R5.6 regression failed closed.' }

$Out=Join-Path $Root 'outputs\v0_6D1_R5_6'
if(-not $Resume){
  if(Test-Path $Out){
    $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $dst=Join-Path $Root "outputs\v0_6D1_R5_6_attempt_$stamp"
    Move-Item $Out $dst; Write-Host "Preserved prior R5.6 attempt: $dst"
  }
  New-Item -ItemType Directory -Force -Path $Out | Out-Null
} elseif(-not (Test-Path $Out)) {
  throw 'R5.6 -Resume requested but outputs\v0_6D1_R5_6 does not exist.'
}

Write-Host '=== R5.6 fresh Windows -> WSL -> Conda -> SLiM 5.2 + tskit 1.0.3 binding ==='
$WslExe=(Get-Command wsl.exe -ErrorAction Stop).Source
$CondaPath = if($env:ARCANA_CONDA_EXE){ $env:ARCANA_CONDA_EXE } else { '/home/jose/miniforge3/bin/conda' }
& $WslExe -e /usr/bin/test -x $CondaPath
if($LASTEXITCODE -ne 0){ throw "R5.6 governed Conda executable unavailable: $CondaPath" }
$PkgJson=(& $WslExe -e $CondaPath list -n $CondaEnv --json 2>$null | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PkgJson)){ throw "R5.6 could not query Conda package identity in env $CondaEnv" }
try { $PkgRows=@($PkgJson | ConvertFrom-Json) } catch { throw "R5.6 could not parse Conda package identity: $($_.Exception.Message)" }
function Require-ExactPackage([string]$name,[string]$version){
  $rows=@($PkgRows | Where-Object { $_.name -eq $name -and $_.version -eq $version })
  if($rows.Count -ne 1){ throw "R5.6 requires exactly one $name=$version package in Conda env $CondaEnv; found $($rows.Count)." }
  return $rows[0]
}
$SlimPkg=Require-ExactPackage 'slim' '5.2'
$TskitPkg=Require-ExactPackage 'tskit' '1.0.3'
$MsprimeRows=@($PkgRows | Where-Object { $_.name -eq 'msprime' })
$PyslimRows=@($PkgRows | Where-Object { $_.name -eq 'pyslim' })
$MsprimeVersionObserved=if($MsprimeRows.Count -gt 0){ [string]$MsprimeRows[0].version } else { $null }
$PyslimVersionObserved=if($PyslimRows.Count -gt 0){ [string]$PyslimRows[0].version } else { $null }
$SlimExe=(& $WslExe -e $CondaPath run -n $CondaEnv /usr/bin/which slim 2>$null | Select-Object -Last 1).Trim()
if($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($SlimExe)){ throw "R5.6 slim unavailable in Conda env $CondaEnv" }
$VersionText=(& $WslExe -e $CondaPath run -n $CondaEnv slim -v 2>&1 | Out-String).Trim()
if($LASTEXITCODE -ne 0 -or $VersionText -notmatch 'SLiM version 5\.2'){ throw "R5.6 SLiM runtime version mismatch: $VersionText" }
$HashLine=(& $WslExe -e /usr/bin/sha256sum $SlimExe | Select-Object -First 1).Trim()
if($LASTEXITCODE -ne 0 -or $HashLine -notmatch '^([0-9a-fA-F]{64})\s+'){ throw 'R5.6 could not hash resolved SLiM executable.' }
$SlimHash=$Matches[1].ToLowerInvariant()
$Runtime=[ordered]@{
  stage='v0.6D1-R5.6';status='PASS_R56_SLIM_5_2_PINNED_RUNTIME_IDENTITY';slim_version='5.2';slim_executable=$SlimExe;slim_executable_sha256=$SlimHash;
  slim_package_version=[string]$SlimPkg.version;slim_package_build=[string]$SlimPkg.build_string;slim_package_channel=[string]$SlimPkg.channel;
  tskit_version=[string]$TskitPkg.version;msprime_version_observed=$MsprimeVersionObserved;pyslim_version_observed=$PyslimVersionObserved;
  conda_executable=$CondaPath;conda_env_name=$CondaEnv;wsl_executable=$WslExe;
  selection_semantics='EXACT_SLIM_5_2_PLUS_EXACT_TSKIT_1_0_3_REQUIRED; MSPRIME_AND_PYSLIM_RECORDED_IF_PRESENT_BUT_NOT_REQUIRED_FOR_R56_EXECUTION';version_probe=$VersionText
}
$Runtime | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 (Join-Path $Out 'R5_6_SLIM_RUNTIME_IDENTITY.json')
$Runtime | ConvertTo-Json -Depth 8

if(-not $Resume){
  Write-Host '=== R5.6 prepare R5.5-derived binary contact schedules + standardized SLiM ancestry challenges ==='
  $prep=@('scripts/prepare_v0_6D1_R5_6.py','--root',$Root)
  if($AllowNonScientificDevParent){ $prep += '--allow-non-scientific-dev-parent' }
  python @prep
  if($LASTEXITCODE -ne 0){ throw 'R5.6 challenge preparation failed closed.' }
} else {
  if(-not (Test-Path (Join-Path $Out 'R5_6_SLIM_EXECUTION_PLAN.json'))){ throw 'R5.6 resume requires preserved execution plan.' }
  Write-Host '=== R5.6 resume preserved execution plan ==='
}

$Plan=Get-Content -Raw (Join-Path $Out 'R5_6_SLIM_EXECUTION_PLAN.json') | ConvertFrom-Json
$StreamRunnerWin=(Resolve-Path 'benchmarks\r56\run_slim_r56_stream.sh').Path
$StreamRunnerWsl=Convert-ArcanaWindowsPathToWsl $StreamRunnerWin
$CollectorWin=(Resolve-Path 'benchmarks\r56\slim_collect_r56.py').Path
$CollectorWsl=Convert-ArcanaWindowsPathToWsl $CollectorWin

if(-not $Resume){
  Write-Host '=== R5.6 SLiM pilot: first contact schedule NO_FLOW + LOW + HIGH, one seed ==='
  $FirstSchedule=[string](($Plan.schedules | Sort-Object schedule_id | Select-Object -First 1).schedule_id)
  $pilot=@($Plan.streams | Where-Object { $_.schedule_id -eq $FirstSchedule -and $_.seed -eq 560601 } | Sort-Object variant)
  if($pilot.Count -ne 3){ throw "R5.6 expected 3 pilot streams, got $($pilot.Count)" }
  foreach($s in $pilot){
    $wdWin=Join-Path $Root (($s.work_dir) -replace '/','\'); $wdWsl=Convert-ArcanaWindowsPathToWsl $wdWin
    & $WslExe -e bash $StreamRunnerWsl $wdWsl $CondaPath $CondaEnv ([string]$s.seed) ([string]$s.variant) $CollectorWsl
    if($LASTEXITCODE -ne 0){ throw "R5.6 SLiM pilot $($s.variant) failed closed before full corpus." }
  }
  python scripts/check_v0_6D1_R5_6_pilot.py --root $Root
  if($LASTEXITCODE -ne 0){ throw 'R5.6 SLiM pilot evidence failed closed.' }
}

Write-Host "=== R5.6 SLiM targeted execution: $($Plan.schedule_class_count) schedule classes / $($Plan.planned_stream_count) streams ==="
$SuiteWin=(Resolve-Path 'benchmarks\r56\run_slim_r56_suite.sh').Path; $SuiteWsl=Convert-ArcanaWindowsPathToWsl $SuiteWin
$OutWsl=Convert-ArcanaWindowsPathToWsl $Out
& $WslExe -e bash $SuiteWsl $OutWsl $CondaPath $CondaEnv $StreamRunnerWsl $CollectorWsl ([string]$ParallelJobs)
if($LASTEXITCODE -ne 0){ throw 'R5.6 SLiM full targeted execution failed closed.' }
python scripts/build_v0_6D1_R5_6_execution_bridge.py --root $Root
if($LASTEXITCODE -ne 0){ throw 'R5.6 execution bridge integrity failed closed.' }

Write-Host '=== R5.6 governed true-local-ancestry / admixture challenge analysis ==='
$ana=@('scripts/analyze_v0_6D1_R5_6.py','--root',$Root)
if($AllowNonScientificDevParent){ $ana += '--allow-non-scientific-dev-parent' }
python @ana
if($LASTEXITCODE -ne 0){ throw 'R5.6 governed ancestry evidence analysis failed closed.' }
Write-Host 'PASS_R56_TARGETED_ANCESTRY_AND_ADMIXTURE_CHALLENGE_EVIDENCE_CANDIDATE_RUN'
Write-Host 'PASS_R56_INTEGRATED_SLIM_ANCESTRY_EVIDENCE_CANDIDATE_RUN'
Write-Host 'R5.6 remains CANDIDATE by design; next step is one large R5.3-R5.6 block audit/seal, not a micro-seal.'
