$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r416'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

Write-Host '=== R4.16 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_16_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.16 source authority failed closed.'}

Write-Host '=== R4.16 regression ==='
python -m pytest "$Root\tests\test_r416_recovered_metric_target_protocol.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.16 regression failed closed.'}

Write-Host '=== R4.16 recovered metric promotion gate + ARCANA target semantic protocol ==='
python "$Root\scripts\run_v0_6D1_R4_16.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.16 BLOCKED. Preserve outputs and paste R4_16_INTEGRATED_AUDIT.json.'; exit 3}

Write-Host '=== R4.16 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_16_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.16 seal BLOCKED. Preserve outputs and paste audit.'; exit 3}

Write-Host 'PASS_R416_INTEGRATED_AND_FINAL_SEAL_RUN'
