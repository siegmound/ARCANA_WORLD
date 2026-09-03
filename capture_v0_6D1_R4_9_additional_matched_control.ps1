param([switch]$PrepareOnly)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$OutDir=Join-Path $Root 'outputs\v0_6D1_R4_9';New-Item -ItemType Directory -Force -Path $OutDir|Out-Null
$RuntimeEvidence=Join-Path $OutDir 'R4_9_RUNTIME_IDENTITY_EVIDENCE.json'
Write-Host '=== R4.9 Phase A: fresh governed runtime identity evidence ==='
& (Join-Path $Root 'capture_v0_6D1_R4_0_runtime_evidence.ps1') -OutputPath $RuntimeEvidence
if($LASTEXITCODE -ne 0){throw 'R4.9 runtime identity probe failed closed.'}
$Runtime=Get-Content -Raw $RuntimeEvidence|ConvertFrom-Json
if($Runtime.all_required_engines_ready -ne $true){throw 'R4.9 requires governed runtime inventory READY.'}
Write-Host '=== R4.9 Phase A: fixed additional matched-pair expansion plan ==='
python "$Root\scripts\prepare_v0_6D1_R4_9.py" --root "$Root"
if($LASTEXITCODE -ne 0){throw 'R4.9 replicate-expansion preparation failed closed.'}
if($PrepareOnly){Write-Host 'PASS_R49_PHASE_A_FIXED_REPLICATE_EXPANSION_READY';exit 0}
$WslExe=[string]$Runtime.wsl_executable;$CondaPath=[string]$Runtime.conda_binding
function Q([string]$v){if($v.Contains("'")){throw 'Unsupported quote in shell path'};return "'$v'"}
function WslPath([string]$p){$f=[IO.Path]::GetFullPath($p);if($f -match '^([A-Za-z]):\\(.*)$'){return '/mnt/'+$Matches[1].ToLowerInvariant()+'/'+($Matches[2]-replace '\\','/')};throw "Unsupported path: $f"}
function InvokeWsl([string]$script,[string]$label,[int]$timeout=2400){$psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$WslExe;$psi.Arguments='bash -s';$psi.UseShellExecute=$false;$psi.RedirectStandardInput=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true;$p=[Diagnostics.Process]::new();$p.StartInfo=$psi;if(-not $p.Start()){throw "Cannot start WSL for $label"};$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();$p.StandardInput.Write($script);$p.StandardInput.Close();$sw=[Diagnostics.Stopwatch]::StartNew();$next=30;while(-not $p.WaitForExit(1000)){if($sw.Elapsed.TotalSeconds -ge $timeout){try{$p.Kill($true)}catch{};return [pscustomobject]@{ExitCode=124;Stdout=$ot.GetAwaiter().GetResult();Stderr=$et.GetAwaiter().GetResult();Elapsed=$sw.Elapsed.TotalSeconds}};if($sw.Elapsed.TotalSeconds -ge $next){Write-Host ("  {0}: still running ({1:n0}s elapsed)" -f $label,$sw.Elapsed.TotalSeconds);$next+=30}};$sw.Stop();return [pscustomobject]@{ExitCode=$p.ExitCode;Stdout=$ot.GetAwaiter().GetResult();Stderr=$et.GetAwaiter().GetResult();Elapsed=[math]::Round($sw.Elapsed.TotalSeconds,3)}}
$jid='R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP';$JobDir=Join-Path $OutDir ('jobs\'+$jid);New-Item -ItemType Directory -Force -Path $JobDir|Out-Null
$Contract=Join-Path $Root ('outputs\v0_6D1_R4_3\jobs\'+$jid+'\JOB_CONTRACT.json')
$R47Profile=Join-Path $Root ('outputs\v0_6D1_R4_7\jobs\'+$jid+'\REPAIR_PROFILE.json')
$Expansion=Join-Path $JobDir 'ADDITIONAL_REPLICATE_PROFILE.json'
$DynamicRaw=Join-Path $JobDir 'RAW_ADDITIONAL_DYNAMIC_EVIDENCE.json';$NeutralRaw=Join-Path $JobDir 'RAW_ADDITIONAL_NEUTRAL_EVIDENCE.json'
$DynamicWork=Join-Path $JobDir 'runtime_work_additional_dynamic';$NeutralWork=Join-Path $JobDir 'runtime_work_additional_neutral'
$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{'arcana-cdmetapop-308'};$CdRoot=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root '.arcana_engines\CDMetaPOP-3.08'}
foreach($p in @($DynamicRaw,$NeutralRaw,(Join-Path $JobDir 'DYNAMIC_STDOUT.log'),(Join-Path $JobDir 'DYNAMIC_STDERR.log'),(Join-Path $JobDir 'NEUTRAL_STDOUT.log'),(Join-Path $JobDir 'NEUTRAL_STDERR.log'))){if(Test-Path $p){Remove-Item -Force $p}}
foreach($p in @($DynamicWork,$NeutralWork)){if(Test-Path $p){Remove-Item -Recurse -Force $p};New-Item -ItemType Directory -Force -Path $p|Out-Null}
$dynScript="set -euo pipefail`nCONDA_EXE=$(Q $CondaPath)`n`"`$CONDA_EXE`" run -n '$CdEnv' python $(Q (WslPath (Join-Path $Root 'benchmarks\r49\cdmetapop_r49_dynamic.py'))) $(Q (WslPath $Contract)) $(Q (WslPath $R47Profile)) $(Q (WslPath $Expansion)) $(Q (WslPath $DynamicRaw)) $(Q (WslPath $DynamicWork)) $(Q (WslPath $CdRoot))`n"
Write-Host '=== R4.9 Phase B1: 16 additional J09 dynamic-forcing replicates ===';$d=InvokeWsl $dynScript 'R49 J09 dynamic x16' 2400;[string]$d.Stdout|Set-Content -Encoding UTF8 (Join-Path $JobDir 'DYNAMIC_STDOUT.log');[string]$d.Stderr|Set-Content -Encoding UTF8 (Join-Path $JobDir 'DYNAMIC_STDERR.log');Write-Host ("  returncode={0} elapsed={1}s" -f $d.ExitCode,$d.Elapsed)
if(-not(Test-Path $DynamicRaw)){[ordered]@{stage='v0.6D1-R4.9';job_id=$jid;engine='CDMetaPOP';adapter_status='ENGINE_EXECUTION_FAILURE';diagnostic_arm='ADDITIONAL_DYNAMIC_FORCING';replicates=@();canonical_write=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $DynamicRaw}
$neuScript="set -euo pipefail`nCONDA_EXE=$(Q $CondaPath)`n`"`$CONDA_EXE`" run -n '$CdEnv' python $(Q (WslPath (Join-Path $Root 'benchmarks\r49\cdmetapop_r49_neutral.py'))) $(Q (WslPath $Contract)) $(Q (WslPath $Expansion)) $(Q (WslPath $NeutralRaw)) $(Q (WslPath $NeutralWork)) $(Q (WslPath $CdRoot))`n"
Write-Host '=== R4.9 Phase B2: 16 additional J09 matched-neutral replicates ===';$n=InvokeWsl $neuScript 'R49 J09 neutral x16' 2400;[string]$n.Stdout|Set-Content -Encoding UTF8 (Join-Path $JobDir 'NEUTRAL_STDOUT.log');[string]$n.Stderr|Set-Content -Encoding UTF8 (Join-Path $JobDir 'NEUTRAL_STDERR.log');Write-Host ("  returncode={0} elapsed={1}s" -f $n.ExitCode,$n.Elapsed)
if(-not(Test-Path $NeutralRaw)){[ordered]@{stage='v0.6D1-R4.9';job_id=$jid;engine='CDMetaPOP';adapter_status='ENGINE_EXECUTION_FAILURE';diagnostic_arm='ADDITIONAL_MATCHED_NEUTRAL_FORCING';replicates=@();canonical_write=$false}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $NeutralRaw}
Write-Host '=== R4.9 Phase C: expanded 20-pair causal direction resolution ===';python "$Root\scripts\collect_v0_6D1_R4_9.py" --root "$Root";if($LASTEXITCODE -ne 0){exit 3}
