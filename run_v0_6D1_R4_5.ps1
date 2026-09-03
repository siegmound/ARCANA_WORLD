$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r45"
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}; New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R4.5 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_5_source_manifest.py"
if($LASTEXITCODE -ne 0){throw "R4.5 source authority failed closed."}
Write-Host "=== R4.5 regression ==="
python -m pytest "$Root\tests\test_r45_causal_diagnosis.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw "R4.5 regression failed closed."}
Write-Host "=== R4.5 earliest-authority causal diagnosis + robustness gate ==="
python "$Root\scripts\run_v0_6D1_R4_5.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host "R4.5 BLOCKED. Preserve R4.4 evidence and paste the integrated audit."; exit 3}
Write-Host "=== R4.5 final fail-closed seal ==="
python "$Root\scripts\audit_v0_6D1_R4_5_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host "R4.5 seal BLOCKED. Paste output."; exit 3}
Write-Host "PASS_R45_INTEGRATED_AND_FINAL_SEAL_RUN"
