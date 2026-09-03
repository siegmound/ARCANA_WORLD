$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r413'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp|Out-Null
Write-Host '=== R4.13 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_13_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.13 source authority failed closed.'}
Write-Host '=== R4.13 regression ==='
python -m pytest "$Root\tests\test_r413_cdmetapop_comparability_downgrade.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.13 regression failed closed.'}
Write-Host '=== R4.13 CDMetaPOP absolute-response comparability downgrade + symmetric readjudication ==='
python "$Root\scripts\run_v0_6D1_R4_13.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.13 BLOCKED. Preserve outputs and paste R4_13_INTEGRATED_AUDIT.json.';exit 3}
Write-Host '=== R4.13 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_13_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.13 seal BLOCKED. Preserve outputs and paste audit.';exit 3}
Write-Host 'PASS_R413_INTEGRATED_AND_FINAL_SEAL_RUN'
