param([switch]$PrepareOnly)
$ErrorActionPreference='Stop';$Root=Split-Path -Parent $MyInvocation.MyCommand.Path;$env:PYTHONPATH="$Root\src";$Tmp=Join-Path $Root '.pytest_tmp\r48';if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp};New-Item -ItemType Directory -Force -Path $Tmp|Out-Null
Write-Host '=== R4.8 source authority ===';python "$Root\scripts\check_v0_6D1_R4_8_source_manifest.py";if($LASTEXITCODE -ne 0){throw 'R4.8 source authority failed closed.'}
Write-Host '=== R4.8 regression ===';python -m pytest "$Root\tests\test_r48_post_cdmetapop_structural_diagnosis.py" -q --basetemp "$Tmp" -p no:cacheprovider;if($LASTEXITCODE -ne 0){throw 'R4.8 regression failed closed.'}
Write-Host '=== R4.8 matched neutral-control causal diagnosis ===';& "$Root\capture_v0_6D1_R4_8_matched_control.ps1" -PrepareOnly:$PrepareOnly;if($LASTEXITCODE -ne 0){exit $LASTEXITCODE};if($PrepareOnly){exit 0}
Write-Host '=== R4.8 final fail-closed seal ===';python "$Root\scripts\audit_v0_6D1_R4_8_seal.py" --root "$Root";if($LASTEXITCODE -ne 0){Write-Host 'R4.8 seal BLOCKED. Preserve outputs and paste audit.';exit 3};Write-Host 'PASS_R48_INTEGRATED_AND_FINAL_SEAL_RUN'
