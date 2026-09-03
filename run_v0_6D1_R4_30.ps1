param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$RepairHistoryR1 = Join-Path $Root "outputs\v0_6D1_R4_30\repair_history\R430_R1_SOURCE_BINDING_AUTHORITY_SCOPE_BLOCKED"
$CurrentAudit = Join-Path $Root "outputs\v0_6D1_R4_30\R4_30_INTEGRATED_AUDIT.json"
if (Test-Path $CurrentAudit) {
  try {
    $Current = Get-Content $CurrentAudit -Raw | ConvertFrom-Json
    if ($Current.status -eq "BLOCKED_R430_PARENT_TARGET_MATERIALIZATION_SELECTOR_GAP_OR_J14_EXECUTION_FAILURE") {
      New-Item -ItemType Directory -Force -Path $RepairHistoryR1 | Out-Null
      $Preserve = @(
        "R4_30_INTEGRATED_AUDIT.json",
        "R4_30_AUTHORIZED_TARGET_MATERIALIZATION_REGISTRY.json",
        "R4_30_SELECTOR_GAP_CLOSURE_REGISTRY.json",
        "R4_30_SEMANTIC_REPAIR_PRIMARY_MAPPING_REVIEW.json",
        "R4_30_R431_EXECUTION_PLAN.json"
      )
      foreach ($Name in $Preserve) {
        $Src = Join-Path $Root "outputs\v0_6D1_R4_30\$Name"
        if (Test-Path $Src) { Copy-Item -Force $Src (Join-Path $RepairHistoryR1 $Name) }
      }
      $AuthDir = Join-Path $Root "outputs\v0_6D1_R4_30\authority"
      if (Test-Path $AuthDir) { Copy-Item -Recurse -Force $AuthDir (Join-Path $RepairHistoryR1 "authority") }
      Write-Host "PASS_R430_R2_R1_BLOCKED_GATE_EVIDENCE_PRESERVED"
    }
  } catch { }
}
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_30\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null
Write-Host "=== R4.30 source authority ==="
& $Python scripts\check_v0_6D1_R4_30_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.30-R2 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r430_target_materialization_selector_gap_j14_execution.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.30 authorized target materialization + selector gap closure + J14 authority execution ==="
& $Python scripts\run_v0_6D1_R4_30.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.30 BLOCKED."; exit $LASTEXITCODE }
Write-Host "=== R4.30 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_30_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.30 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }
Write-Host "PASS_R430_INTEGRATED_AND_FINAL_SEAL_RUN"
