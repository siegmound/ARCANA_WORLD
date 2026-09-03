$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r337"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.37 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_37_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.37 source authority failed closed." }
Write-Host "=== R3.37 regression ==="
python -m pytest "$Root\tests\test_r337_managed_forager_economy.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.37 regression failed closed." }
Write-Host "=== R3.37 intensive managed-forager demography + settlement + exchange economy ==="
python "$Root\scripts\run_v0_6D1_R3_37.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.37 integrated stage failed closed." }
Write-Host "=== R3.37 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_37_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.37 final seal failed closed." }
Write-Host "PASS_R337_INTEGRATED_AND_FINAL_SEAL_RUN"
