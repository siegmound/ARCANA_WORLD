param(
  [string]$RuntimeIdentityEvidence = "",
  [string]$OutputPath = ""
)
$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$Bindings=Join-Path $Root "set_r40_engine_env.local.ps1"
if(Test-Path $Bindings){ . $Bindings }

if([string]::IsNullOrWhiteSpace($RuntimeIdentityEvidence)){
  $RuntimeIdentityEvidence=Join-Path $Root "outputs\v0_6D1_R4_54\R4_54_RUNTIME_IDENTITY_EVIDENCE.json"
}
if([string]::IsNullOrWhiteSpace($OutputPath)){
  $OutputPath=Join-Path $Root "outputs\v0_6D1_R4_54\R4_54_HOST_DRY_RUN_EVIDENCE.json"
}
if(-not (Test-Path $RuntimeIdentityEvidence)){ throw "R4.54 runtime identity evidence missing" }
$Runtime=Get-Content -Raw $RuntimeIdentityEvidence | ConvertFrom-Json
if(-not $Runtime.all_required_engines_ready){ throw "R4.54 requires fresh all-engine READY runtime evidence" }

$PlanPath=Join-Path $Root "outputs\v0_6D1_R4_52\R4_52_NON_GEONOMICS_EXECUTION_PLAN.json"
$RegPath=Join-Path $Root "outputs\v0_6D1_R4_53\R4_53_NON_GEONOMICS_EXECUTION_READOUT_AUTHORITY_REGISTRY.json"
$Plan=Get-Content -Raw $PlanPath | ConvertFrom-Json
$Registry=Get-Content -Raw $RegPath | ConvertFrom-Json
$ExpectedPlan="f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
$ExpectedReg="f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380"
if([string]$Plan.plan_sha256 -ne $ExpectedPlan){ throw "R4.54 parent plan SHA mismatch" }
if([string]$Registry.registry_sha256 -ne $ExpectedReg){ throw "R4.54 parent registry SHA mismatch" }

function Convert-Wsl([string]$Path){
  $full=[System.IO.Path]::GetFullPath($Path)
  if($full -match '^([A-Za-z]):\\(.*)$'){
    return "/mnt/$($Matches[1].ToLowerInvariant())/$($Matches[2] -replace '\\','/')"
  }
  throw "Unsupported Windows path $full"
}
function Q([string]$Value,[string]$Name){
  if($Value.Contains("'")){ throw "$Name contains unsupported single quote" }
  return "'$Value'"
}
function Invoke-WslScript([string]$Script,[string]$Label,[int]$TimeoutSeconds=3600){
  $wsl=[string]$Runtime.wsl_executable
  $psi=[System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$wsl; $psi.Arguments="bash -s"; $psi.UseShellExecute=$false
  $psi.RedirectStandardInput=$true; $psi.RedirectStandardOutput=$true
  $psi.RedirectStandardError=$true; $psi.CreateNoWindow=$true
  $p=[System.Diagnostics.Process]::new(); $p.StartInfo=$psi
  if(-not $p.Start()){ throw "Could not start WSL bridge for $Label" }
  $ot=$p.StandardOutput.ReadToEndAsync(); $et=$p.StandardError.ReadToEndAsync()
  $p.StandardInput.Write($Script); $p.StandardInput.Close()
  $sw=[System.Diagnostics.Stopwatch]::StartNew(); $timed=$false
  while(-not $p.WaitForExit(1000)){
    if($sw.Elapsed.TotalSeconds -ge $TimeoutSeconds){
      $timed=$true; try{$p.Kill($true)}catch{try{$p.Kill()}catch{}}; break
    }
  }
  if($timed){$p.WaitForExit()}
  $stdout=$ot.GetAwaiter().GetResult(); $stderr=$et.GetAwaiter().GetResult()
  [pscustomobject]@{ExitCode=if($timed){124}else{$p.ExitCode};Stdout=$stdout;Stderr=$stderr;TimedOut=$timed}
}
function Probe([string]$Engine){
  $j=@($Plan.jobs | Where-Object {$_.engine -eq $Engine} | Select-Object -First 1)
  if($j.Count -ne 1){ throw "No unique first R4.52 probe job for $Engine" }
  [pscustomobject]@{JobId=[string]$j[0].job_id;Seed=[int]$j[0].frozen_seeds[0]}
}
function Version([string]$Engine){
  $r=@($Runtime.engines | Where-Object {$_.engine -eq $Engine} | Select-Object -First 1)
  if($r.Count -ne 1){return ""}
  return [string]$r[0].confirmed_version
}
function ReadResult([string]$Path,[string]$Engine,[object]$Exec){
  if(Test-Path $Path){
    try{$x=Get-Content -Raw $Path | ConvertFrom-Json}catch{$x=$null}
  } else {$x=$null}
  if($null -eq $x){
    return [ordered]@{engine=$Engine;status="FAIL";returncode=[int]$Exec.ExitCode;metrics=@();artifact_hashes=@{};error="missing/unparseable result"}
  }
  $x | Add-Member -NotePropertyName confirmed_version -NotePropertyValue (Version $Engine) -Force
  $x | Add-Member -NotePropertyName bridge_exit_code -NotePropertyValue ([int]$Exec.ExitCode) -Force
  return $x
}

$RootW=Convert-Wsl $Root
$Out=Join-Path $Root "outputs\v0_6D1_R4_54"
$Work=Join-Path $Out "runtime_work"
$Results=Join-Path $Out "dry_runs"
if(Test-Path $Work){Remove-Item -Recurse -Force $Work}
if(Test-Path $Results){Remove-Item -Recurse -Force $Results}
New-Item -ItemType Directory -Force -Path $Work,$Results | Out-Null
$WorkW=Convert-Wsl $Work; $ResultsW=Convert-Wsl $Results
$Conda=[string]$Runtime.conda_binding
if([string]::IsNullOrWhiteSpace($Conda)){throw "missing conda binding"}
$CondaQ=Q $Conda "conda"; $RootQ=Q $RootW "root"; $WorkQ=Q $WorkW "work"; $ResultQ=Q $ResultsW "result"

$REnv=if($env:ARCANA_R40_R_CONDA_ENV){$env:ARCANA_R40_R_CONDA_ENV}else{"arcana-r40-r"}
$NemoEnv=if($env:ARCANA_NEMO_CONDA_ENV){$env:ARCANA_NEMO_CONDA_ENV}else{"arcana-nemo242"}
$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{"arcana-cdmetapop-308"}
$SlimEnv=if($env:ARCANA_SLIM_CONDA_ENV){$env:ARCANA_SLIM_CONDA_ENV}else{"arcana-slim52"}
$CdRootWindows=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root ".arcana_engines\CDMetaPOP-3.08"}
$CdRootW=Convert-Wsl $CdRootWindows
$CdRootQ=Q $CdRootW "cdroot"

$rows=@()

Write-Host "[1/5] R4.54 Madingley seed/readout dry-run"
$p=Probe "Madingley"
$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$REnv' bash "`$ROOT/benchmarks/r454/run_r_with_conda_libs.sh" "`$ROOT/benchmarks/r454/madingley_r454.R" "`$RESULT/Madingley.json" "`$WORK/Madingley" '$($p.Seed)' '$($p.JobId)'
"@
$e=Invoke-WslScript $script "Madingley"
$r=ReadResult (Join-Path $Results "Madingley.json") "Madingley" $e
# Hash at least one concrete materialized artifact or the result file itself.
$r.artifact_hashes=[ordered]@{"dry_run_result_json"=(Get-FileHash -Algorithm SHA256 (Join-Path $Results "Madingley.json")).Hash.ToLowerInvariant()}
$rows += $r

Write-Host "[2/5] R4.54 RangeShifter seed/readout dry-run"
$p=Probe "RangeShifter"
$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$REnv' bash "`$ROOT/benchmarks/r454/run_r_with_conda_libs.sh" "`$ROOT/benchmarks/r454/rangeshiftr_r454.R" "`$RESULT/RangeShifter.json" "`$WORK/RangeShifter" '$($p.Seed)' '$($p.JobId)'
"@
$e=Invoke-WslScript $script "RangeShifter"
$r=ReadResult (Join-Path $Results "RangeShifter.json") "RangeShifter" $e
$r.artifact_hashes=[ordered]@{"dry_run_result_json"=(Get-FileHash -Algorithm SHA256 (Join-Path $Results "RangeShifter.json")).Hash.ToLowerInvariant()}
$rows += $r

Write-Host "[3/5] R4.54 CDMetaPOP seed/readout dry-run"
$p=Probe "CDMetaPOP"
$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
CDROOT=$CdRootQ
"`$CONDA_EXE" run -n '$CdEnv' python "`$ROOT/benchmarks/r454/cdmetapop_r454.py" "`$RESULT/CDMetaPOP.json" "`$WORK/CDMetaPOP" "`$CDROOT" '$($p.Seed)' '$($p.JobId)'
"@
$e=Invoke-WslScript $script "CDMetaPOP"
$r=ReadResult (Join-Path $Results "CDMetaPOP.json") "CDMetaPOP" $e
$rows += $r

Write-Host "[4/5] R4.54 NEMO seed/readout dry-run"
$p=Probe "NEMO"
$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$NemoEnv' bash "`$ROOT/benchmarks/r454/run_nemo_r454.sh" "`$ROOT/benchmarks/r41/Nemo2_R41_B1.ini" "`$WORK/NEMO" "`$RESULT/NEMO.json" '$($p.Seed)' '$($p.JobId)' "`$ROOT/benchmarks/r454/nemo_collect_r454.py"
"@
$e=Invoke-WslScript $script "NEMO" 1800
$r=ReadResult (Join-Path $Results "NEMO.json") "NEMO" $e
$qf=Get-ChildItem -Path (Join-Path $Work "NEMO") -Filter "*.qfreq" -File | Select-Object -First 1
if($null -ne $qf){
  $r.artifact_hashes=[ordered]@{"NEMO_NATIVE_QFREQ_OUTPUT"=(Get-FileHash -Algorithm SHA256 $qf.FullName).Hash.ToLowerInvariant()}
}else{$r.artifact_hashes=@{}}
$rows += $r

Write-Host "[5/5] R4.54 SLiM seed/readout dry-run"
$p=Probe "SLiM"
$script=@"
set -euo pipefail
CONDA_EXE=$CondaQ
ROOT=$RootQ
WORK=$WorkQ
RESULT=$ResultQ
"`$CONDA_EXE" run -n '$SlimEnv' bash "`$ROOT/benchmarks/r454/run_slim_r454.sh" "`$ROOT/benchmarks/r454/R454_two_pop_gene_flow.slim" "`$ROOT/benchmarks/r454/slim_collect_r454.py" "`$WORK/SLiM" "`$RESULT/SLiM.json" '$($p.Seed)' '$($p.JobId)'
"@
$e=Invoke-WslScript $script "SLiM" 1800
$r=ReadResult (Join-Path $Results "SLiM.json") "SLiM" $e
$rows += $r

$pass=@($rows | Where-Object {$_.status -eq "PASS" -and $_.returncode -eq 0})
$result=[ordered]@{
 stage="v0.6D1-R4.54"
 evidence_type="NON_SCIENTIFIC_FIVE_ENGINE_SEED_AND_READOUT_DRY_RUN_EVIDENCE"
 generated_by="capture_v0_6D1_R4_54_dry_runs.ps1"
 parent_execution_plan_sha256=$ExpectedPlan
 parent_readout_registry_sha256=$ExpectedReg
 dry_run_count=$rows.Count
 passed_dry_run_count=$pass.Count
 historical_job_execution_performed=$false
 scientific_engine_execution_performed=$false
 scientific_evidence_claimed=$false
 numeric_acceptance_threshold_count=0
 automatic_scientific_pass_fail_count=0
 canonical_state_changed=$false
 dry_runs=$rows
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
$result | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $OutputPath
Write-Host "R4.54 dry-run evidence: $OutputPath"
Write-Host "Passed dry-runs: $($pass.Count)/5"
if($pass.Count -ne 5){exit 3}
exit 0
