param(
  [string]$Python = "python",
  [double]$EndAgeMa = 150.0,
  [switch]$DiagnosticSmoke
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$outDir = Join-Path $root "local_runs\v0_6D1_R3_7H"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$jobs = @()
foreach ($branch in @("K_LOW","K_CENTER","K_HIGH")) {
  $args = @("scripts\run_v0_6D1_R3_7H_closed_loop_validation.py","--branch",$branch,"--end-age-ma",$EndAgeMa,"--out-dir",$outDir)
  if ($DiagnosticSmoke) { $args += "--diagnostic-smoke" }
  $jobs += Start-Process -FilePath $Python -ArgumentList $args -WorkingDirectory $root -PassThru -NoNewWindow
}
$failed = $false
foreach ($job in $jobs) {
  $job.WaitForExit()
  if ($job.ExitCode -ne 0) { $failed = $true }
}
if ($failed) { throw "At least one R3.7H closed-loop branch failed" }
$agg = @("scripts\run_v0_6D1_R3_7H_closed_loop_validation.py","--aggregate-only","--end-age-ma",$EndAgeMa,"--out-dir",$outDir)
if ($DiagnosticSmoke) { $agg += "--diagnostic-smoke" }
& $Python @agg
if ($LASTEXITCODE -ne 0) { throw "R3.7H aggregate gate failed" }
