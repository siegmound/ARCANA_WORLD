$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r415'

# R4.15-R1 preserves the initial blocked over-broad P0 recovery-gate evidence.
$OldAudit=Join-Path $Root 'outputs\v0_6D1_R4_15\R4_15_INTEGRATED_AUDIT.json'
if(Test-Path $OldAudit){
  try {
    $Old=Get-Content -Raw $OldAudit | ConvertFrom-Json
    if($Old.status -eq 'BLOCKED_R415_PARENT_RECOVERY_OR_TARGET_MATERIALIZATION_FAILURE'){
      $Hist=Join-Path $Root 'outputs\v0_6D1_R4_15\repair_history\R415_INITIAL_OVERBROAD_ALL_PRIMARY_RECOVERY_GATE_BLOCKED'
      New-Item -ItemType Directory -Force -Path $Hist | Out-Null
      foreach($Name in @('R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json','R4_15_ARCANA_TARGET_SOURCE_CANDIDATE_REGISTRY.json','R4_15_R416_PROMOTION_GATE_PLAN.json','R4_15_INTEGRATED_AUDIT.json')){
        $Src=Join-Path $Root ('outputs\v0_6D1_R4_15\'+$Name)
        if((Test-Path $Src) -and -not (Test-Path (Join-Path $Hist $Name))){ Copy-Item $Src (Join-Path $Hist $Name) }
      }
      $OldSeal=Join-Path $Root 'outputs\v0_6D1_R4_15_SEAL\R4_15_FINAL_SEAL_AUDIT.json'
      if((Test-Path $OldSeal) -and -not (Test-Path (Join-Path $Hist 'R4_15_FINAL_SEAL_AUDIT.json'))){ Copy-Item $OldSeal (Join-Path $Hist 'R4_15_FINAL_SEAL_AUDIT.json') }
      Write-Host 'PASS_R415_R1_INITIAL_BLOCKED_GATE_EVIDENCE_PRESERVED'
    }
  } catch { Write-Host 'R4.15-R1 preservation note: prior blocked audit could not be parsed; continuing without deleting it.' }
}

if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

Write-Host '=== R4.15 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_15_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.15 source authority failed closed.'}

Write-Host '=== R4.15 regression ==='
python -m pytest "$Root\tests\test_r415_retained_metric_target_semantics.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.15 regression failed closed.'}

Write-Host '=== R4.15-R1 retained P0 candidate realization + ARCANA target-source semantic audit ==='
python "$Root\scripts\run_v0_6D1_R4_15.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.15-R1 BLOCKED. Preserve outputs and paste R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json / R4_15_INTEGRATED_AUDIT.json.'; exit 3}

Write-Host '=== R4.15 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_15_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.15-R1 seal BLOCKED. Preserve outputs and paste audit.'; exit 3}

Write-Host 'PASS_R415_INTEGRATED_AND_FINAL_SEAL_RUN'
