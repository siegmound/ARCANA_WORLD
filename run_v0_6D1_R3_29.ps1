$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r329"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.29 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_29_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.29 source authority failed closed." }
Write-Host "=== R3.29 regression ==="
python -m pytest "$Root\tests\test_r329_population_settlement_culture.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.29 regression failed closed." }
Write-Host "=== R3.29 population + settlement + cultural preconditions ==="
python "$Root\scripts\run_v0_6D1_R3_29.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.29 integrated replay failed closed." }
Write-Host "=== R3.29 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_29_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.29 final seal failed closed." }
Write-Host "PASS_R329_INTEGRATED_AND_FINAL_SEAL_RUN"
