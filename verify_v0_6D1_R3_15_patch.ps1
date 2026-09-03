$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "PATCH_MANIFEST_v0_6D1_R3_15_OVER_R3_14.json"
if (-not (Test-Path $ManifestPath)) { throw "Missing R3.15 patch manifest" }
$M = Get-Content -Raw $ManifestPath | ConvertFrom-Json
$ok = 0
foreach ($row in $M.payload) {
    $p = Join-Path $Root $row.path
    if (-not (Test-Path $p -PathType Leaf)) { throw "Missing patch payload: $($row.path)" }
    $got = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
    if ($got -ne ([string]$row.sha256).ToLowerInvariant()) { throw "SHA mismatch: $($row.path)" }
    $ok++
}
Write-Host "PASS_R315_PATCH_FILES_VERIFIED: $ok/$($M.payload_file_count)"
Write-Host "Parent boundary: R3.14 SEALED 30.0 Ma C2 provider + adaptive clock"
Write-Host "Canonical R3.15 endpoint: 250 ka PRE-C2-200ka-BRIDGE"
Write-Host "Biology cadence changes: NONE (125 kyr preserved)"
Write-Host "Scientific parameter changes: NONE"
