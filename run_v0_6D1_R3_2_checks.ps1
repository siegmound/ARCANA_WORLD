$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
python -m pytest -q (Join-Path $Root "tests")
if ($LASTEXITCODE -ne 0) { throw "R3.2 pytest failed" }
python (Join-Path $Root "scripts\audit_v0_6D1_R3_2.py")
if ($LASTEXITCODE -ne 0) { throw "R3.2 formal audit failed" }
