param([switch]$PrepareOnly)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$OutDir=Join-Path $Root 'outputs\v0_6D1_R4_8';New-Item -ItemType Directory -Force -Path $OutDir|Out-Null
$RuntimeEvidence=Join-Path $OutDir 'R4_8_RUNTIME_IDENTITY_EVIDENCE.json'
Write-Host '=== R4.8 Phase A: fresh governed runtime identity evidence ==='
& (Join-Path $Root 'capture_v0_6D1_R4_0_runtime_evidence.ps1') -OutputPath $RuntimeEvidence
if($LASTEXITCODE -ne 0){throw 'R4.8 runtime identity probe failed closed.'}
$Runtime=Get-Content -Raw $RuntimeEvidence|ConvertFrom-Json
if($Runtime.all_required_engines_ready -ne $true){throw 'R4.8 requires governed runtime inventory READY.'}
Write-Host '=== R4.8 Phase A: matched neutral-control plan ==='
python "$Root\scripts\prepare_v0_6D1_R4_8.py" --root "$Root"
if($LASTEXITCODE -ne 0){throw 'R4.8 control-plan preparation failed closed.'}
if($PrepareOnly){Write-Host 'PASS_R48_PHASE_A_MATCHED_CONTROL_PLAN_READY';exit 0}
$WslExe=[string]$Runtime.wsl_executable;$CondaPath=[string]$Runtime.conda_binding
function Q([string]$v){if($v.Contains("'")){throw 'Unsupported quote in shell path'};return "'$v'"}
function WslPath([string]$p){$f=[IO.Path]::GetFullPath($p);if($f -match '^([A-Za-z]):\\(.*)$'){return '/mnt/'+$Matches[1].ToLowerInvariant()+'/'+($Matches[2]-replace '\\','/')};throw "Unsupported path: $f"}
function InvokeWsl([string]$script,[string]$label,[int]$timeout=900){$psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$WslExe;$psi.Arguments='bash -s';$psi.UseShellExecute=$false;$psi.RedirectStandardInput=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true;$p=[Diagnostics.Process]::new();$p.StartInfo=$psi;if(-not $p.Start()){throw "Cannot start WSL for $label"};$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();$p.StandardInput.Write($script);$p.StandardInput.Close();$sw=[Diagnostics.Stopwatch]::StartNew();$next=30;while(-not $p.WaitForExit(1000)){if($sw.Elapsed.TotalSeconds -ge $timeout){try{$p.Kill($true)}catch{};return [pscustomobject]@{ExitCode=124;Stdout=$ot.GetAwaiter().GetResult();Stderr=$et.GetAwaiter().GetResult();Elapsed=$sw.Elapsed.TotalSeconds}};if($sw.Elapsed.TotalSeconds -ge $next){Write-Host ("  {0}: still running ({1:n0}s elapsed)" -f $label,$sw.Elapsed.TotalSeconds);$next+=30}};$sw.Stop();return [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$ot.GetAwaiter().GetResult();Stderr=$et.GetAwaiter().GetResult();Elapsed=[math]::Round($sw.Elapsed.TotalSeconds,3)}}
$jid='R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP';$JobDir=Join-Path $OutDir ('jobs\'+$jid);New-Item -ItemType Directory -Force -Path $JobDir|Out-Null
$Contract=Join-Path $Root ('outputs\v0_6D1_R4_3\jobs\'+$jid+'\JOB_CONTRACT.json');$Control=Join-Path $JobDir 'NEUTRAL_CONTROL_PROFILE.json';$Raw=Join-Path $JobDir 'RAW_NEUTRAL_CONTROL_EVIDENCE.json';$Work=Join-Path $JobDir 'runtime_work_neutral'
foreach($p in @($Raw,(Join-Path $JobDir 'STDOUT.log'),(Join-Path $JobDir 'STDERR.log'))){if(Test-Path $p){Remove-Item -Force $p}};if(Test-Path $Work){Remove-Item -Recurse -Force $Work};New-Item -ItemType Directory -Force -Path $Work|Out-Null
$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{'arcana-cdmetapop-308'};$CdRoot=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root '.arcana_engines\CDMetaPOP-3.08'}
$script="set -euo pipefail`nCONDA_EXE=$(Q $CondaPath)`n`"`$CONDA_EXE`" run -n '$CdEnv' python $(Q (WslPath (Join-Path $Root 'benchmarks\r48\cdmetapop_r48_neutral.py'))) $(Q (WslPath $Contract)) $(Q (WslPath $Control)) $(Q (WslPath $Raw)) $(Q (WslPath $Work)) $(Q (WslPath $CdRoot))`n"
Write-Host '=== R4.8 Phase B: J09 matched neutral-forcing CDMetaPOP control ===';$e=InvokeWsl $script $jid 900;[string]$e.Stdout|Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDOUT.log');[string]$e.Stderr|Set-Content -Encoding UTF8 (Join-Path $JobDir 'STDERR.log');Write-Host ("  returncode={0} elapsed={1}s" -f $e.ExitCode,$e.Elapsed)
if(-not(Test-Path $Raw)){[ordered]@{stage='v0.6D1-R4.8';job_id=$jid;engine='CDMetaPOP';adapter_status='ENGINE_EXECUTION_FAILURE';diagnostic_control='MATCHED_NEUTRAL_FORCING';replicates=@();canonical_write=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $Raw}
Write-Host '=== R4.8 Phase C: paired causal-effect diagnosis ===';python "$Root\scripts\collect_v0_6D1_R4_8.py" --root "$Root";if($LASTEXITCODE -ne 0){exit 3}
