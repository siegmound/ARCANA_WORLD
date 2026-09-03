$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$ROOT\src"
python -m pytest "$ROOT\tests\test_r322_functional_phenotype_spec.py" -q
if ($LASTEXITCODE -ne 0) { throw "R3.22 candidate unit checks failed closed." }
python "$ROOT\scripts\audit_v0_6D1_R3_22_candidate.py"
if ($LASTEXITCODE -ne 0) { throw "R3.22 static candidate audit failed closed." }
Write-Host "PASS_R322_CANDIDATE_CHECKS"
