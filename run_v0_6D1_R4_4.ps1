$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r44"
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}; New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R4.4 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_4_source_manifest.py"
if($LASTEXITCODE -ne 0){throw "R4.4 source authority failed closed."}
Write-Host "=== R4.4 regression ==="
python -m pytest "$Root\tests\test_r44_discordance_adjudication.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw "R4.4 regression failed closed."}
Write-Host "=== R4.4 cross-engine/domain scientific adjudication ==="
python "$Root\scripts\run_v0_6D1_R4_4.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host "R4.4 BLOCKED. Preserve evidence and paste the integrated audit."; exit 3}
Write-Host "=== R4.4 final fail-closed seal ==="
python "$Root\scripts\audit_v0_6D1_R4_4_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host "R4.4 seal BLOCKED. Paste output."; exit 3}
Write-Host "PASS_R44_INTEGRATED_AND_FINAL_SEAL_RUN"
