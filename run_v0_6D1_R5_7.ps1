$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r57"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

$Out = Join-Path $Root "outputs\v0_6D1_R5_7"
if (Test-Path $Out) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $archive = Join-Path $Root "outputs\v0_6D1_R5_7_attempt_$stamp"
    Move-Item -Path $Out -Destination $archive
    Write-Host "Preserved prior R5.7 attempt: $archive"
}

Write-Host "=== R5.7 source authority for one large R5.3-R5.6 closure ==="
python "$Root\scripts\check_v0_6D1_R5_7_source_manifest.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.7 source authority failed closed." }

Write-Host "=== R5.7 integrated-block closure regression (project-local pytest basetemp) ==="
python -m pytest "$Root\tests\test_r57_integrated_block_closure.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R5.7 closure regression failed closed." }

Write-Host "=== R5.7 live R5.3-R5.6 provenance / raw-evidence / non-circularity audit ==="
python "$Root\scripts\audit_v0_6D1_R5_7.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.7 integrated block audit failed closed." }

Write-Host "=== R5.7 single final scientific block seal ==="
python "$Root\scripts\seal_v0_6D1_R5_7.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R5.7 final block seal failed closed." }

Write-Host "PASS_R57_R53_R56_LARGE_BLOCK_FINAL_SEAL_RUN"
Write-Host "R5.3-R5.6 are now sealed once as a single governed scientific block; no retrospective micro-seals were created."
