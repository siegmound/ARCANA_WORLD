$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$LocalEngineBindings = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEngineBindings) {
  . $LocalEngineBindings
  Write-Host "R4.1 loaded governed local engine bindings: $LocalEngineBindings"
}
$Tmp = Join-Path $Root ".pytest_tmp\r41"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

Write-Host "=== R4.1 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_1_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R4.1 source authority failed closed." }

Write-Host "=== R4.1 semantic/microbenchmark regression ==="
python -m pytest "$Root\tests\test_r41_semantic_revalidation.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R4.1 regression failed closed." }

Write-Host "=== R4.1 fresh exact runtime identity evidence ==="
$RuntimeIdentity = Join-Path $Root "outputs\v0_6D1_R4_1\R4_1_RUNTIME_IDENTITY_EVIDENCE.json"
if (Test-Path $RuntimeIdentity) { Remove-Item -Force $RuntimeIdentity }
& "$Root\capture_v0_6D1_R4_0_runtime_evidence.ps1" -OutputPath $RuntimeIdentity
if ($LASTEXITCODE -ne 0) { throw "R4.1 requires all six exact R4.0 runtime identities READY before scientific microbenchmarks." }

Write-Host "=== R4.1 controlled scientific microbenchmarks ==="
$MicroEvidence = Join-Path $Root "outputs\v0_6D1_R4_1\R4_1_HOST_MICROBENCHMARK_EVIDENCE.json"
if (Test-Path $MicroEvidence) { Remove-Item -Force $MicroEvidence }
& "$Root\capture_v0_6D1_R4_1_microbenchmarks.ps1" -RuntimeIdentityEvidence $RuntimeIdentity -OutputPath $MicroEvidence
$MicroExit = $LASTEXITCODE
if (-not (Test-Path $MicroEvidence)) { throw "R4.1 microbenchmark bridge produced no fresh evidence file." }
if ($MicroExit -ne 0) { Write-Host "R4.1: one or more controlled microbenchmarks failed; integrated audit will preserve exact diagnostics." }

Write-Host "=== R4.1 semantic authority + historical window execution gate ==="
python "$Root\scripts\run_v0_6D1_R4_1.py" --root "$Root"
$RunExit = $LASTEXITCODE

Write-Host "=== R4.1 final fail-closed seal ==="
python "$Root\scripts\audit_v0_6D1_R4_1_seal.py" --root "$Root"
$SealExit = $LASTEXITCODE
if ($RunExit -eq 3 -or $SealExit -eq 3) {
  Write-Host "R4.1 is BLOCKED by controlled microbenchmark or semantic-gate evidence. Paste this output; do not start historical windows yet."
  exit 3
}
if ($RunExit -ne 0 -or $SealExit -ne 0) { throw "R4.1 failed closed." }
Write-Host "PASS_R41_INTEGRATED_AND_FINAL_SEAL_RUN"
