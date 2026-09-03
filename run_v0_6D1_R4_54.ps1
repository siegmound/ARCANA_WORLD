param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r454"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.54 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_54_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 regression ==="
& $Python -m pytest -q ".\tests\test_r454_non_geonomics_exact_seed_readout_dry_run_authorization.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

$Runtime=Join-Path $Root "outputs\v0_6D1_R4_54\R4_54_RUNTIME_IDENTITY_EVIDENCE.json"
if(Test-Path $Runtime){Remove-Item -Force $Runtime}
Write-Host "=== R4.54 fresh exact runtime identity evidence ==="
& ".\capture_v0_6D1_R4_0_runtime_evidence.ps1" -OutputPath $Runtime
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

$Dry=Join-Path $Root "outputs\v0_6D1_R4_54\R4_54_HOST_DRY_RUN_EVIDENCE.json"
if(Test-Path $Dry){Remove-Item -Force $Dry}
Write-Host "=== R4.54 real five-engine disposable seed/readout dry-runs ==="
& ".\capture_v0_6D1_R4_54_dry_runs.ps1" -RuntimeIdentityEvidence $Runtime -OutputPath $Dry
$DryExit=$LASTEXITCODE
if(-not (Test-Path $Dry)){throw "R4.54 dry-run bridge produced no evidence"}
if($DryExit -ne 0){
  Write-Host "R4.54: one or more dry-runs failed; integrated audit will preserve diagnostics."
}

Write-Host "=== R4.54 dry-run schema validation + 80-stream authorization ==="
& $Python ".\scripts\run_v0_6D1_R4_54.py"
$RunExit=$LASTEXITCODE
if($RunExit -ne 0){
  Write-Host "R4.54 BLOCKED. No historical scientific stream is authorized."
  exit $RunExit
}

Write-Host "=== R4.54 final fail-closed authorization seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_54_seal.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R454_INTEGRATED_AND_FINAL_SEAL_RUN"
