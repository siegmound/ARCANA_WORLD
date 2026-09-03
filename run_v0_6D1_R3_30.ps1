$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r330"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.30 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_30_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.30 source authority failed closed." }
Write-Host "=== R3.30 regression ==="
python -m pytest "$Root\tests\test_r330_census_group_abm.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.30 regression failed closed." }
Write-Host "=== R3.30 census calibration + weighted group ABM ==="
python "$Root\scripts\run_v0_6D1_R3_30.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.30 integrated stage failed closed." }
Write-Host "=== R3.30 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_30_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.30 final seal failed closed." }
Write-Host "PASS_R330_INTEGRATED_AND_FINAL_SEAL_RUN"
