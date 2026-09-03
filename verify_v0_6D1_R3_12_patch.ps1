$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "PATCH_MANIFEST_v0_6D1_R3_12_OVER_R3_11.json"
$m = Get-Content $manifestPath -Raw | ConvertFrom-Json
$bad = @()
foreach ($f in $m.files) {
    $p = Join-Path $root ($f.path -replace '/', '\\')
    if (-not (Test-Path $p)) { $bad += "MISSING $($f.path)"; continue }
    $h = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
    if ($h -ne $f.sha256) { $bad += "HASH $($f.path)" }
}
if ($bad.Count -gt 0) {
    $bad | ForEach-Object { Write-Error $_ }
    exit 1
}
Write-Host "PASS_R312_PATCH_FILES_VERIFIED: $($m.file_count)/$($m.file_count)"
Write-Host "Then run: .\\run_v0_6D1_R3_12_diversity_recovery.ps1"
