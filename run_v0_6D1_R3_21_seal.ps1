$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ROOT\scripts\audit_v0_6D1_R3_21_seal.py" --root "$ROOT"
if ($LASTEXITCODE -ne 0) { throw "R3.21 final seal audit failed closed." }
Write-Host "PASS_R321_FINAL_SEAL_CHECKS"
