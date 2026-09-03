param([string]$Python="python",[string]$RuntimeIdentityEvidence="",[switch]$NoResume)
$ErrorActionPreference="Stop";$Root=(Get-Location).Path;$env:PYTHONPATH=(Join-Path $Root "src")
if([string]::IsNullOrWhiteSpace($RuntimeIdentityEvidence)){$RuntimeIdentityEvidence=Join-Path $Root "outputs\v0_6D1_R4_55\R4_55_RUNTIME_IDENTITY_EVIDENCE.json"}
$Manifest=Get-Content -Raw (Join-Path $Root "outputs\v0_6D1_R4_55\R4_55_EXECUTION_MANIFEST.json")|ConvertFrom-Json
$Runtime=Get-Content -Raw $RuntimeIdentityEvidence|ConvertFrom-Json
if(-not $Runtime.all_required_engines_ready){throw "R4.55 requires fresh READY runtime evidence"}
$WslExe=[string]$Runtime.wsl_executable;$CondaPath=[string]$Runtime.conda_binding
if([string]::IsNullOrWhiteSpace($WslExe)-or -not(Test-Path $WslExe)){throw "invalid WSL binding"}
$CondaBasePython=$CondaPath -replace '/bin/conda$','/bin/python'
if($CondaBasePython -eq $CondaPath){throw "cannot derive governed Conda base Python"}
function CW([string]$Path){$f=[IO.Path]::GetFullPath($Path);if($f -match '^([A-Za-z]):\\(.*)$'){return "/mnt/$($Matches[1].ToLowerInvariant())/$($Matches[2]-replace '\\','/')}throw "unsupported path $f"}
function Q([string]$v,[string]$n){if($v.Contains("'")){throw "$n unsafe"};return "'$v'"}
function IWS([string]$s,[string]$label,[int]$timeout=3600){$psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$WslExe;$psi.Arguments="bash -s";$psi.UseShellExecute=$false;$psi.RedirectStandardInput=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true;$p=[Diagnostics.Process]::new();$p.StartInfo=$psi;if(-not$p.Start()){throw "WSL start failed"};$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();$p.StandardInput.Write($s);$p.StandardInput.Close();$sw=[Diagnostics.Stopwatch]::StartNew();$timed=$false;while(-not$p.WaitForExit(1000)){if($sw.Elapsed.TotalSeconds-ge$timeout){$timed=$true;try{$p.Kill($true)}catch{try{$p.Kill()}catch{}};break}};if($timed){$p.WaitForExit()};[pscustomobject]@{ExitCode=if($timed){124}else{$p.ExitCode};Stdout=$ot.GetAwaiter().GetResult();Stderr=$et.GetAwaiter().GetResult();TimedOut=$timed}}
function ArchivePartial([string]$jid,[string]$jd){if(-not (Test-Path $jd)){return};$h=Join-Path $Root "outputs\v0_6D1_R4_55\repair_history";New-Item -ItemType Directory -Force -Path $h|Out-Null;$n=0;do{$dst=Join-Path $h ("PARTIAL_"+$jid+"_"+("{0:D3}"-f$n));$n++}while(Test-Path $dst);Move-Item -Force -Path $jd $dst;Write-Host "Archived partial: $dst"}
function BridgeFailure([string]$raw,[object]$job,[object]$e){$o=[ordered]@{stage="v0.6D1-R4.55";job_id=[string]$job.job_id;engine=[string]$job.engine;adapter_status="ENGINE_EXECUTION_FAILURE";replicates=@();bridge_returncode=[int]$e.ExitCode;timed_out=[bool]$e.TimedOut;stdout_tail=[string]$e.Stdout;stderr_tail=[string]$e.Stderr;error="Authorized adapter produced no RAW_ENGINE_EVIDENCE.json";canonical_write=$false};$o|ConvertTo-Json -Depth 20|Set-Content -Encoding UTF8 -Path $raw}
$RootQ=Q (CW $Root) "root";$CondaQ=Q $CondaPath "conda";$BasePyQ=Q $CondaBasePython "basepy"
$REnv=if($env:ARCANA_R40_R_CONDA_ENV){$env:ARCANA_R40_R_CONDA_ENV}else{"arcana-r40-r"};$NemoEnv=if($env:ARCANA_NEMO_CONDA_ENV){$env:ARCANA_NEMO_CONDA_ENV}else{"arcana-nemo242"};$CdEnv=if($env:ARCANA_CDMETAPOP_CONDA_ENV){$env:ARCANA_CDMETAPOP_CONDA_ENV}else{"arcana-cdmetapop-308"};$SlimEnv=if($env:ARCANA_SLIM_CONDA_ENV){$env:ARCANA_SLIM_CONDA_ENV}else{"arcana-slim52"}
$CdRoot=if($env:ARCANA_CDMETAPOP_ROOT){$env:ARCANA_CDMETAPOP_ROOT}else{Join-Path $Root ".arcana_engines\CDMetaPOP-3.08"};$CdRootQ=Q (CW $CdRoot) "cdroot"
$jobs=@($Manifest.jobs);$i=0
foreach($j in $jobs){$i++;$jid=[string]$j.job_id;$eng=[string]$j.engine;$jd=Join-Path $Root ("outputs\v0_6D1_R4_55\jobs\"+$jid)
 if(-not$NoResume){&$Python ".\scripts\check_v0_6D1_R4_55_job_resume.py" --job-id $jid|Out-Null;$rs=$LASTEXITCODE;if($rs-eq0){Write-Host("[$i/$($jobs.Count)] $jid / $eng -- RESUME VALID, SKIP");continue}elseif($rs-eq11){ArchivePartial $jid $jd}elseif($rs-eq12){Write-Host"R4.55 BLOCKED: completed evidence exists but fails resume integrity for $jid";exit 12}}elseif(Test-Path $jd){ArchivePartial $jid $jd}
 New-Item -ItemType Directory -Force -Path $jd|Out-Null;$raw=Join-Path $jd"RAW_ENGINE_EVIDENCE.json";$so=Join-Path $jd"STDOUT.log";$se=Join-Path $jd"STDERR.log";$work=Join-Path $jd"runtime_work";New-Item -ItemType Directory -Force -Path $work|Out-Null
 $cq=Q(CW(Join-Path $Root([string]$j.contract_path)))"contract";$rq=Q(CW$raw)"raw";$wq=Q(CW$work)"work";Write-Host("[$i/$($jobs.Count)] $jid / $eng -- SCIENTIFIC EXECUTION")
 switch($eng){
  "Madingley"{$cfgq=Q(CW(Join-Path $Root([string]$j.engine_config_path)))"cfg";$script="set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$REnv' bash $RootQ/benchmarks/r41/run_r_with_conda_libs.sh $RootQ/benchmarks/r43/madingley_r43.R $cfgq $rq $wq";$to=3600}
  "RangeShifter"{$cfgq=Q(CW(Join-Path $Root([string]$j.engine_config_path)))"cfg";$script="set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$REnv' bash $RootQ/benchmarks/r41/run_r_with_conda_libs.sh $RootQ/benchmarks/r43/rangeshiftr_r43.R $cfgq $rq $wq";$to=3600}
  "NEMO"{$script="set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$NemoEnv' $BasePyQ $RootQ/benchmarks/r421/nemo_r421.py $cq $rq $wq";$to=3600}
  "SLiM"{$script="set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$SlimEnv' python $RootQ/benchmarks/r421/slim_r421.py $cq $rq $wq";$to=3600}
  "CDMetaPOP"{$pq=Q(CW(Join-Path $Root([string]$j.repair_profile_path)))"profile";$script="set -euo pipefail`nCONDA_EXE=$CondaQ`n`"`$CONDA_EXE`" run -n '$CdEnv' python $RootQ/benchmarks/r421/cdmetapop_r421_matched.py $cq $pq $rq $wq $CdRootQ";$to=5400}
  default{throw"unauthorized engine"}
 }
 $e=IWS $script $jid $to;Set-Content -Encoding UTF8 -Path $so ([string]$e.Stdout);Set-Content -Encoding UTF8 -Path $se ([string]$e.Stderr);if(-not (Test-Path $raw)){BridgeFailure $raw $j $e};if($e.ExitCode-ne0){Write-Host"R4.55 BLOCKED: $jid rc=$($e.ExitCode). Prior jobs remain resumable.";exit $e.ExitCode}
 if($eng-eq"SLiM"){$sx="set -euo pipefail`nCONDA_EXE=$CondaQ`ncd $RootQ`nPYTHONPATH=$RootQ/src `"`$CONDA_EXE`" run -n '$SlimEnv' python $RootQ/scripts/extract_v0_6D1_R4_55_job.py --job-id '$jid' --slim";$x=IWS $sx ($jid+"_extract") 1800;Add-Content -Encoding UTF8 -Path $so ([string]$x.Stdout);Add-Content -Encoding UTF8 -Path $se ([string]$x.Stderr);if($x.ExitCode-ne0){exit $x.ExitCode}}
 else{&$Python ".\scripts\extract_v0_6D1_R4_55_job.py" --job-id $jid;if($LASTEXITCODE-ne0){exit $LASTEXITCODE}}
}
Write-Host "PASS_R455_ALL_20_JOBS_80_STREAMS_EXECUTION_AND_JOB_EVIDENCE_CAPTURE"
