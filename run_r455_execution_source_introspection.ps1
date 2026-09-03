param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path

Write-Host "=== R4.55 prebuild exact local execution-source introspection ==="
& $Python ".\scripts\r455_execution_source_introspection.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host ""
Write-Host "PASS_R455_PREBUILD_EXECUTION_SOURCE_INTROSPECTION_HELPER"
Write-Host "No external engine was executed; this output is not scientific evidence."
