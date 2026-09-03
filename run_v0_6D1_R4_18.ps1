$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r418'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host '=== R4.18 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_18_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.18 source authority failed closed.'}
Write-Host '=== R4.18 regression ==='
python -m pytest "$Root\tests\test_r418_target_validation_partial_readjudication.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.18 regression failed closed.'}
Write-Host '=== R4.18 target validation + partial readjudication + P2 backlog freeze ==='
python "$Root\scripts\run_v0_6D1_R4_18.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.18 BLOCKED. Preserve outputs and paste R4_18_INTEGRATED_AUDIT.json.'; exit 3}
Write-Host '=== R4.18 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_18_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.18 seal BLOCKED. Preserve outputs and paste audit.'; exit 3}
Write-Host 'PASS_R418_INTEGRATED_AND_FINAL_SEAL_RUN'
