$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$Root\scripts\audit_v0_6D1_R3_23_seal.py" --root $Root
if ($LASTEXITCODE -ne 0) { throw "R3.23 final seal audit failed closed." }
Write-Host "PASS_R323_FINAL_SEAL_CHECKS"
