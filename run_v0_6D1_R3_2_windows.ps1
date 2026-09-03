param(
  [double]$EndAgeMa = 150.0,
  [int]$Threads = 12,
  [switch]$FissionOff
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
if ($Threads -gt 0) {
  $env:OMP_NUM_THREADS = "$Threads"
  $env:MKL_NUM_THREADS = "$Threads"
  $env:OPENBLAS_NUM_THREADS = "$Threads"
  $env:NUMEXPR_NUM_THREADS = "$Threads"
}
$Args = @(
  (Join-Path $Root "scripts\run_v0_6D1_R3_2_local.py"),
  "--end-age-ma", "$EndAgeMa",
  "--threads", "$Threads"
)
if ($FissionOff) { $Args += "--fission-off" }
python @Args
if ($LASTEXITCODE -ne 0) { throw "v0.6D1-R3.2 local run failed with exit code $LASTEXITCODE" }
