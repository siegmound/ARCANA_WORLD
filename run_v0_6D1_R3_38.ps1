$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r338"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.38 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_38_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.38 source authority failed closed." }
Write-Host "=== R3.38 regression ==="
python -m pytest "$Root\tests\test_r338_exchange_technology_cultural_genealogy.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.38 regression failed closed." }
Write-Host "=== R3.38 regional exchange + concrete technology + cultural genealogies ==="
python "$Root\scripts\run_v0_6D1_R3_38.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.38 integrated stage failed closed." }
Write-Host "=== R3.38 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_38_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.38 final seal failed closed." }
Write-Host "PASS_R338_INTEGRATED_AND_FINAL_SEAL_RUN"
