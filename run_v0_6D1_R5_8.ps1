$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r58"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

$Out = Join-Path $Root "outputs\v0_6D1_R5_8"
if (Test-Path $Out) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $archive = Join-Path $Root "outputs\v0_6D1_R5_8_attempt_$stamp"
    Move-Item -Path $Out -Destination $archive
    Write-Host "Preserved prior R5.8 attempt: $archive"
}

Write-Host "=== R5.8 source + sealed R5.7 / sealed R3.27 / direct R3.21 authority ==="
python "$Root\scripts\check_v0_6D1_R5_8_source_manifest.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.8 source authority failed closed." }

Write-Host "=== R5.8 reconciliation regression (project-local pytest basetemp) ==="
python -m pytest "$Root\tests\test_r58_hominid_history_reconciliation.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R5.8 regression failed closed." }

Write-Host "=== R5.8 ARCANA-native 3 Ma -> 200 ka lineage / macro-replay / contact-history reconciliation ==="
python "$Root\scripts\run_v0_6D1_R5_8.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.8 scientific reconciliation failed closed." }

Write-Host "PASS_R58_3MA_200KA_HOMINID_HISTORY_RECONCILIATION_CANDIDATE_RUN"
Write-Host "R5.8 remains CANDIDATE; no new external engine was executed and no final human species identity was materialized."
