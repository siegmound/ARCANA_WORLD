$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r50"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

Write-Host "=== R5.0 source + immutable parent authority ==="
python "$Root\scripts\check_v0_6D1_R5_0_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R5.0 source authority failed closed." }

Write-Host "=== R5.0 query/resolver regression ==="
python -m pytest "$Root\tests\test_r50_arbitrary_age_state_query.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R5.0 regression failed closed." }

Write-Host "=== R5.0 strict post-R4.56 authority + 20 ka / 17.5 ka end-to-end ==="
python "$Root\scripts\run_v0_6D1_R5_0.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.0 integrated query stage failed closed." }

Write-Host "=== R5.0 final scientific seal ==="
python "$Root\scripts\seal_v0_6D1_R5_0.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.0 final seal failed closed." }

Write-Host "PASS_R50_INTEGRATED_AND_FINAL_SEAL_RUN"
