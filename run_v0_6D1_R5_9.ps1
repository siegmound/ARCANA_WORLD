$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r59"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

$Out = Join-Path $Root "outputs\v0_6D1_R5_9"
if (Test-Path $Out) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $archive = Join-Path $Root "outputs\v0_6D1_R5_9_attempt_$stamp"
    Move-Item -Path $Out -Destination $archive
    Write-Host "Preserved prior R5.9 attempt: $archive"
}

Write-Host "=== R5.9 source + R5.8 candidate / sealed R3.28 authority ==="
python "$Root\scripts\check_v0_6D1_R5_9_source_manifest.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.9 source authority failed closed." }

Write-Host "=== R5.9 reconciliation regression (project-local pytest basetemp) ==="
python -m pytest "$Root\tests\test_r59_recent_human_history_reconciliation.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R5.9 regression failed closed." }

Write-Host "=== R5.9 runtime utility review + sealed R3.28 200 ka -> 0 reconciliation ==="
python "$Root\scripts\run_v0_6D1_R5_9.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.9 scientific reconciliation failed closed." }

Write-Host "PASS_R59_R58_TO_R328_200KA_0KA_HIGH_RESOLUTION_RECONCILIATION_CANDIDATE_RUN"
Write-Host "R5.9 remains CANDIDATE; R3.28 was not rerun and no external engine was executed. Downstream R3.29 is not auto-authorized."
