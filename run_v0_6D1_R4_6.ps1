$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r46"
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}; New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R4.6 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_6_source_manifest.py"
if($LASTEXITCODE -ne 0){throw "R4.6 source authority failed closed."}
Write-Host "=== R4.6 regression ==="
python -m pytest "$Root\tests\test_r46_targeted_causal_counterfactual.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw "R4.6 regression failed closed."}
$BlockedAudit = Join-Path $Root "outputs\v0_6D1_R4_6\R4_6_INTEGRATED_AUDIT.json"
if(Test-Path $BlockedAudit){
  $Hist = Join-Path $Root "outputs\v0_6D1_R4_6\repair_history\R46_INITIAL_SCOPE_MISMATCH_BLOCKED"
  New-Item -ItemType Directory -Force -Path $Hist | Out-Null
  Copy-Item $BlockedAudit (Join-Path $Hist "R4_6_INTEGRATED_AUDIT_PRE_R1.json") -Force
}
Write-Host "=== R4.6-R1 targeted R3.11 causal counterfactual + R4.3 CDMetaPOP forcing-parity audit ==="
python -u "$Root\scripts\run_v0_6D1_R4_6.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host "R4.6 BLOCKED. Preserve outputs and paste the integrated audit."; exit 3}
Write-Host "=== R4.6 final fail-closed seal ==="
python "$Root\scripts\audit_v0_6D1_R4_6_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host "R4.6 seal BLOCKED. Paste output."; exit 3}
Write-Host "PASS_R46_INTEGRATED_AND_FINAL_SEAL_RUN"
