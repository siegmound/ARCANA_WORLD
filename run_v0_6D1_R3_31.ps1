$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r331"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.31 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_31_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.31 source authority failed closed." }
Write-Host "=== R3.31 regression ==="
python -m pytest "$Root\tests\test_r331_cultural_technological_ecology.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.31 regression failed closed." }
Write-Host "=== R3.31 cultural-technological ecology ==="
python "$Root\scripts\run_v0_6D1_R3_31.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.31 integrated stage failed closed." }
Write-Host "=== R3.31 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_31_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.31 final seal failed closed." }
Write-Host "PASS_R331_INTEGRATED_AND_FINAL_SEAL_RUN"
