$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH="$Root\src"
$Tmp=Join-Path $Root '.pytest_tmp\r411'
# R4.11-R1 preserves the initial blocked raw-N0 integrity evidence before rewriting current outputs.
$OldPlan=Join-Path $Root 'outputs\v0_6D1_R4_11\R4_11_REEXTRACTION_PLAN.json'
if(Test-Path $OldPlan){
  try {
    $Old=Get-Content -Raw $OldPlan | ConvertFrom-Json
    if($Old.status -eq 'BLOCKED_R411_PARENT_RETAINED_RUNTIME_OR_METRIC_REEXTRACTION_FAILURE'){
      $Hist=Join-Path $Root 'outputs\v0_6D1_R4_11\repair_history\R411_INITIAL_RAW_CONFIGURED_N0_GATE_BLOCKED'
      New-Item -ItemType Directory -Force -Path $Hist | Out-Null
      foreach($Name in @('R4_11_REEXTRACTION_PLAN.json','R4_11_RETAINED_RUNTIME_SUMMARY_INVENTORY.json','R4_11_PINNED_CDMETAPOP_SUMMARY_SEMANTICS_AUDIT.json','R4_11_INTEGRATED_AUDIT.json')){
        $Src=Join-Path $Root ('outputs\v0_6D1_R4_11\'+$Name)
        if((Test-Path $Src) -and -not (Test-Path (Join-Path $Hist $Name))){ Copy-Item $Src (Join-Path $Hist $Name) }
      }
      Write-Host 'PASS_R411_R1_INITIAL_BLOCKED_GATE_EVIDENCE_PRESERVED'
    }
  } catch { Write-Host 'R4.11-R1 preservation note: prior plan could not be parsed; continuing without deleting it.' }
}
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}
New-Item -ItemType Directory -Force -Path $Tmp|Out-Null
Write-Host '=== R4.11 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_11_source_manifest.py"
if($LASTEXITCODE -ne 0){throw 'R4.11 source authority failed closed.'}
Write-Host '=== R4.11 regression ==='
python -m pytest "$Root\tests\test_r411_cdmetapop_population_metric_repair.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'R4.11 regression failed closed.'}
Write-Host '=== R4.11 retained-runtime CDMetaPOP population-metric re-extraction + symmetric readjudication ==='
python "$Root\scripts\run_v0_6D1_R4_11.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.11 BLOCKED. Preserve outputs and paste R4_11_REEXTRACTION_PLAN.json / R4_11_INTEGRATED_AUDIT.json.';exit 3}
Write-Host '=== R4.11 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_11_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host 'R4.11 seal BLOCKED. Preserve outputs and paste audit.';exit 3}
Write-Host 'PASS_R411_INTEGRATED_AND_FINAL_SEAL_RUN'
