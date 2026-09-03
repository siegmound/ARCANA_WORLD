$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = (Join-Path $Root "src")
python -m pytest -q (Join-Path $Root "tests\test_r39_precha1_continuation.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_9.py")
exit $LASTEXITCODE
