$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"

Write-Host "=== ARCANA v0.6D1-R3.6A full pytest ==="
python -m pytest -q (Join-Path $Root "tests")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Parent R3.5 formal audit ==="
python (Join-Path $Root "scripts\audit_v0_6D1_R3_5.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R3.6A scientific-engine bridge audit ==="
python (Join-Path $Root "scripts\audit_v0_6D1_R3_6A.py")
exit $LASTEXITCODE
