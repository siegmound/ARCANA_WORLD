param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$History = Join-Path $Root "outputs\v0_6D1_R4_28\repair_history\R428_INITIAL_ALL_44_EXACT_SELECTOR_INVENTORY_GATE_BLOCKED"
$PriorAudit = Join-Path $Root "outputs\v0_6D1_R4_28\R4_28_INTEGRATED_AUDIT.json"
if (Test-Path $PriorAudit) {
  try {
    $Prior = Get-Content -Raw $PriorAudit | ConvertFrom-Json
    if ([string]$Prior.status -like "BLOCKED_R428*") {
      New-Item -ItemType Directory -Force -Path $History | Out-Null
      $Preserve = @(
        "R4_28_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT.json",
        "R4_28_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_REGISTRY.json",
        "R4_28_SEMANTIC_REPAIR_IMPLEMENTATION_PREFLIGHT.json",
        "R4_28_GEONOMICS_J14_SPATIAL_REPLAY_AUTHORITY_PREFLIGHT.json",
        "R4_28_R429_EXECUTION_PLAN.json",
        "R4_28_INTEGRATED_AUDIT.json"
      )
      foreach ($Name in $Preserve) {
        $Src = Join-Path $Root "outputs\v0_6D1_R4_28\$Name"
        if (Test-Path $Src) { Copy-Item -Force $Src (Join-Path $History $Name) }
      }
      $PriorSeal = Join-Path $Root "outputs\v0_6D1_R4_28_SEAL\R4_28_FINAL_SEAL_AUDIT.json"
      if (Test-Path $PriorSeal) { Copy-Item -Force $PriorSeal (Join-Path $History "R4_28_FINAL_SEAL_AUDIT.json") }
      Write-Host "PASS_R428_R1_INITIAL_BLOCKED_GATE_EVIDENCE_PRESERVED"
    }
  } catch {
    Write-Host "R4.28-R1 warning: prior blocked audit could not be parsed; no history mutation performed."
  }
}
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_28\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null
Write-Host "=== R4.28 source authority ==="
& $Python scripts\check_v0_6D1_R4_28_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.28-R1 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r428_target_selector_design_authority_j14_preflight.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.28-R1 selector/design authority + J14 spatial replay preflight ==="
& $Python scripts\run_v0_6D1_R4_28.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.28 BLOCKED."; exit $LASTEXITCODE }
Write-Host "=== R4.28 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_28_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.28 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }
Write-Host "PASS_R428_INTEGRATED_AND_FINAL_SEAL_RUN"
