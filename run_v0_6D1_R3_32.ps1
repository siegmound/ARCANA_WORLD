$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r332"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.32 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_32_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.32 source authority failed closed." }
Write-Host "=== R3.32 regression ==="
python -m pytest "$Root\tests\test_r332_subsistence_regional_transitions.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.32 regression failed closed." }
Write-Host "=== R3.32 subsistence intensification + regional transitions ==="
python "$Root\scripts\run_v0_6D1_R3_32.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.32 integrated stage failed closed." }
Write-Host "=== R3.32 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_32_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.32 final seal failed closed." }
Write-Host "PASS_R332_INTEGRATED_AND_FINAL_SEAL_RUN"
