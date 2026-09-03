param(
    [int]$Threads = 12
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
$env:OMP_NUM_THREADS = "$Threads"
$env:MKL_NUM_THREADS = "$Threads"
$env:OPENBLAS_NUM_THREADS = "$Threads"
$env:NUMEXPR_NUM_THREADS = "$Threads"
Set-Location $root
python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/audit_v0_6D1_R3_5.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/audit_v0_6D1_R3_6A.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/audit_v0_6D1_R3_6B.py
exit $LASTEXITCODE
