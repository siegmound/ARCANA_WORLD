$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r51"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R5.1 immutable parent authority + engine utility review ==="
python "$Root\scripts\check_v0_6D1_R5_1_source_manifest.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.1 source/authority failed closed." }
Write-Host "=== R5.1 cradle/niche + structure-adjudication + final-seal regression ==="
python -m pytest "$Root\tests\test_r51_cradle_discovery.py" "$Root\tests\test_r51_structure_adjudication.py" "$Root\tests\test_r51_final_seal.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R5.1 regression failed closed." }
Write-Host "=== R5.1 emergent cradle opportunity discovery 3 Ma -> 200 ka ==="
python "$Root\scripts\run_v0_6D1_R5_1.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.1 integrated candidate failed closed." }
Write-Host "=== R5.1 threshold-nested region families + temporal persistence + engine adjudication ==="
python "$Root\scripts\analyze_v0_6D1_R5_1_structure.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.1 structure/engine adjudication failed closed." }
Write-Host "=== R5.1 final scientific seal ==="
python "$Root\scripts\seal_v0_6D1_R5_1.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.1 final scientific seal failed closed." }
Write-Host "PASS_R51_INTEGRATED_AND_FINAL_SEAL_RUN"
