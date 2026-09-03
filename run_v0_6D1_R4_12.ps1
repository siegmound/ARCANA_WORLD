$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r412'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp|Out-Null
Write-Host '=== R4.12 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_12_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.12 source authority failed closed.'}
Write-Host '=== R4.12 regression ==='
python -m pytest "$Root\tests\test_r412_cdmetapop_precision_comparability_diagnosis.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.12 regression failed closed.'}
Write-Host '=== R4.12 metric-repaired precision + absolute-response comparability diagnosis ==='
python "$Root\scripts\run_v0_6D1_R4_12.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.12 BLOCKED. Preserve outputs and paste R4_12_INTEGRATED_AUDIT.json.';exit 3}
Write-Host '=== R4.12 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_12_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.12 seal BLOCKED. Preserve outputs and paste audit.';exit 3}
Write-Host 'PASS_R412_INTEGRATED_AND_FINAL_SEAL_RUN'
