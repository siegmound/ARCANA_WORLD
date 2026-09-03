$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "SEAL_PATCH_MANIFEST_v0_6D1_R3_13.json"
$M = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$Good = 0
foreach ($E in $M.files) {
    $P = Join-Path $Root ($E.path -replace '/', '\')
    if (!(Test-Path $P)) { throw "Missing seal-patch file: $($E.path)" }
    $H = (Get-FileHash $P -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($H -ne $E.sha256) { throw "Hash mismatch: $($E.path)" }
    $Good++
}
Write-Host "PASS_R313_SEAL_PATCH_FILES_VERIFIED: $Good/$($M.payload_count)"
Write-Host "Canonical boundary: 30.0 Ma POST_CHA1_36MY_LONG_TERM_REASSEMBLY"
Write-Host "Scientific changes: NONE"
