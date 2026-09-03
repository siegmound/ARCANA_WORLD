$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r419'
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host '=== R4.19 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_19_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.19 source authority failed closed.'}
Write-Host '=== R4.19 regression ==='
python -m pytest "$Root\tests\test_r419_p2_target_design_execution_plan.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.19 regression failed closed.'}
Write-Host '=== R4.19 P2 adapter + target-design execution-plan freeze ==='
python "$Root\scripts\run_v0_6D1_R4_19.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.19 BLOCKED. Preserve outputs and paste R4_19_INTEGRATED_AUDIT.json.'; exit 3}
Write-Host '=== R4.19 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_19_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.19 seal BLOCKED. Preserve outputs and paste audit.'; exit 3}
Write-Host 'PASS_R419_INTEGRATED_AND_FINAL_SEAL_RUN'
