$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r417'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host '=== R4.17 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_17_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.17 source authority failed closed.'}
Write-Host '=== R4.17 regression ==='
python -m pytest "$Root\tests\test_r417_target_extractor_promotion_closure.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.17 regression failed closed.'}
Write-Host '=== R4.17 ARCANA target extraction + recovered metric promotion closure ==='
python "$Root\scripts\run_v0_6D1_R4_17.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.17 BLOCKED. Preserve outputs and paste R4_17_INTEGRATED_AUDIT.json.'; exit 3}
Write-Host '=== R4.17 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_17_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.17 seal BLOCKED. Preserve outputs and paste audit.'; exit 3}
Write-Host 'PASS_R417_INTEGRATED_AND_FINAL_SEAL_RUN'
