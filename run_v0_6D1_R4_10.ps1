$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r410'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp|Out-Null
Write-Host '=== R4.10 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_10_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.10 source authority failed closed.'}
Write-Host '=== R4.10 regression ==='
python -m pytest "$Root\tests\test_r410_precision_alternate_evidence_closure.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.10 regression failed closed.'}
Write-Host '=== R4.10 precision + alternate-evidence + CDMetaPOP population-metric integrity audit ==='
python "$Root\scripts\run_v0_6D1_R4_10.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.10 integrated audit BLOCKED. Preserve outputs and paste audit.';exit 3}
Write-Host '=== R4.10 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_10_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.10 seal BLOCKED. Preserve outputs and paste audit.';exit 3}
Write-Host 'PASS_R410_INTEGRATED_AND_FINAL_SEAL_RUN'
