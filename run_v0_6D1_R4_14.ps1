$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r414'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp|Out-Null
Write-Host '=== R4.14 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_14_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.14 source authority failed closed.'}
Write-Host '=== R4.14 regression ==='
python -m pytest "$Root\tests\test_r414_evidence_gap_closure.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.14 regression failed closed.'}
Write-Host '=== R4.14 multi-engine evidence-gap census + targeted adapter enhancement freeze ==='
python "$Root\scripts\run_v0_6D1_R4_14.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.14 BLOCKED. Preserve outputs and paste R4_14_INTEGRATED_AUDIT.json.';exit 3}
Write-Host '=== R4.14 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_14_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.14 seal BLOCKED. Preserve outputs and paste audit.';exit 3}
Write-Host 'PASS_R414_INTEGRATED_AND_FINAL_SEAL_RUN'
