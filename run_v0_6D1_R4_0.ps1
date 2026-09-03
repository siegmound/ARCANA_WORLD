$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$LocalEngineBindings = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEngineBindings) {
  . $LocalEngineBindings
  Write-Host "R4.0 loaded governed local engine bindings: $LocalEngineBindings"
}
if ([string]::IsNullOrWhiteSpace($env:ARCANA_WSL_EXE)) {
  $WslCommand = Get-Command wsl.exe -ErrorAction SilentlyContinue
  if ($null -ne $WslCommand) {
    $env:ARCANA_WSL_EXE = $WslCommand.Source
    Write-Host "R4.0 bridged PowerShell WSL binding into Python: $($env:ARCANA_WSL_EXE)"
  }
}
$Tmp = Join-Path $Root ".pytest_tmp\r40"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R4.0 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_0_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R4.0 source authority failed closed." }
Write-Host "=== R4.0 orchestrator regression ==="
python -m pytest "$Root\tests\test_r40_multi_engine_orchestrator.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R4.0 regression failed closed." }
Write-Host "=== R4.0 fresh host runtime evidence bridge ==="
$RuntimeEvidence = Join-Path $Root "outputs\v0_6D1_R4_0\R4_0_HOST_RUNTIME_EVIDENCE.json"
if (Test-Path $RuntimeEvidence) { Remove-Item -Force $RuntimeEvidence }
& "$Root\capture_v0_6D1_R4_0_runtime_evidence.ps1" -OutputPath $RuntimeEvidence
$RuntimeEvidenceExit = $LASTEXITCODE
if (-not (Test-Path $RuntimeEvidence)) { throw "R4.0 host runtime evidence bridge produced no fresh evidence file." }
if ($RuntimeEvidenceExit -ne 0) {
  Write-Host "R4.0 host runtime evidence bridge did not confirm all six runtimes; inventory will report exact probe failures."
}
$env:ARCANA_R40_HOST_RUNTIME_EVIDENCE = $RuntimeEvidence
Write-Host "=== R4.0 multi-engine runtime inventory + frozen revalidation matrix ==="
python "$Root\scripts\run_v0_6D1_R4_0.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R4.0 inventory failed closed." }
Write-Host "=== R4.0 final fail-closed runtime-governance seal ==="
python "$Root\scripts\audit_v0_6D1_R4_0_seal.py" --root "$Root"
if ($LASTEXITCODE -eq 3) {
  Write-Host "R4.0 architecture is valid, but final seal is BLOCKED until all required external runtimes are provisioned."
  Write-Host "Paste the R4.0 output here; we will provision the missing engines without creating a micro-stage."
  exit 3
}
if ($LASTEXITCODE -ne 0) { throw "R4.0 final seal failed closed." }
Write-Host "PASS_R40_INTEGRATED_AND_FINAL_SEAL_RUN"
