param(
  [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$env:ARCANA_PROJECT_ROOT = $Root
Write-Host "=== R4.32-R1C exact producer + manifest cause introspection ==="
& $Python ".\tools\r4_32_r1c_exact_producer_manifest_introspection.py"
if ($LASTEXITCODE -ne 0) {
  throw "R4.32-R1C introspection failed with exit code $LASTEXITCODE"
}
