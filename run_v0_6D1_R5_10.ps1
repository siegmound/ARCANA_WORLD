$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r510"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

$Out = Join-Path $Root "outputs\v0_6D1_R5_10"
if (Test-Path $Out) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $archive = Join-Path $Root "outputs\v0_6D1_R5_10_attempt_$stamp"
    Move-Item -Path $Out -Destination $archive
    Write-Host "Preserved prior R5.10 attempt: $archive"
}

Write-Host "=== R5.10 source + R5.9 candidate / sealed R3.29 authority ==="
python "$Root\scripts\check_v0_6D1_R5_10_source_manifest.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.10 source authority failed closed." }

Write-Host "=== R5.10 R3.29 reconciliation regression (project-local pytest basetemp) ==="
python -m pytest "$Root\tests\test_r510_r329_settlement_cultural_reconciliation.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R5.10 regression failed closed." }

Write-Host "=== R5.10 runtime utility review + sealed R3.29 settlement/cultural-precondition reconciliation ==="
python "$Root\scripts\run_v0_6D1_R5_10.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.10 scientific reconciliation failed closed." }

Write-Host "PASS_R510_R59_TO_R329_POPULATION_SETTLEMENT_CULTURAL_PRECONDITION_RECONCILIATION_CANDIDATE_RUN"
Write-Host "R5.10 remains CANDIDATE; R3.29 was not rerun and no external engine was executed. Downstream R3.30 is not auto-authorized."
