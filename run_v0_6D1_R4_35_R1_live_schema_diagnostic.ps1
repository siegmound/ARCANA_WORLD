param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$env:ARCANA_PROJECT_ROOT = $Root

Write-Host "=== R4.35-R1 live seed + spatial schema diagnostic ==="
& $Python ".\tools\r4_35_r1_live_seed_spatial_schema_diagnostic.py"
if ($LASTEXITCODE -ne 0) {
    throw "R4.35-R1 diagnostic failed with exit code $LASTEXITCODE"
}
