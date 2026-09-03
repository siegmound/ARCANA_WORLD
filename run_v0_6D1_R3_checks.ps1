param([int]$Threads = 12)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
if ($Threads -gt 0) {
  $env:OMP_NUM_THREADS = "$Threads"
  $env:MKL_NUM_THREADS = "$Threads"
  $env:OPENBLAS_NUM_THREADS = "$Threads"
  $env:NUMEXPR_NUM_THREADS = "$Threads"
}
python -m pytest -q (Join-Path $Root "tests")
if ($LASTEXITCODE -ne 0) { throw "R3 tests failed" }
python (Join-Path $Root "scripts\audit_v0_6D1_R3.py")
if ($LASTEXITCODE -ne 0) { throw "R3 formal audit failed" }
Write-Host "PASS: v0.6D1-R3 checks completed"
