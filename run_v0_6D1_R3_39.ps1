$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r339"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.39 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_39_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.39 source authority failed closed." }
Write-Host "=== R3.39 regression ==="
python -m pytest "$Root\tests\test_r339_symbolic_memory_language_identity.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.39 regression failed closed." }
Write-Host "=== R3.39 symbolic memory + language preconditions + interlineage identity ==="
python "$Root\scripts\run_v0_6D1_R3_39.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.39 integrated stage failed closed." }
Write-Host "=== R3.39 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_39_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.39 final seal failed closed." }
Write-Host "PASS_R339_INTEGRATED_AND_FINAL_SEAL_RUN"
