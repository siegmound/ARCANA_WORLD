$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ROOT\scripts\audit_v0_6D1_R3_22_seal.py" --root "$ROOT"
if ($LASTEXITCODE -ne 0) { throw "R3.22 final seal audit failed closed." }
Write-Host "PASS_R322_FINAL_SEAL_CHECKS"
