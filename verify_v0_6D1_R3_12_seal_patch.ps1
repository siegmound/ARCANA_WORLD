$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest = Get-Content (Join-Path $Root "SEAL_PATCH_MANIFEST_v0_6D1_R3_12.json") -Raw | ConvertFrom-Json
$Ok = 0
foreach ($F in $Manifest.files) {
    $P = Join-Path $Root ($F.path -replace '/', '\')
    if (-not (Test-Path $P)) { throw "Missing: $($F.path)" }
    $H = (Get-FileHash -Algorithm SHA256 $P).Hash.ToLowerInvariant()
    if ($H -ne $F.sha256.ToLowerInvariant()) { throw "SHA256 mismatch: $($F.path)" }
    $Ok++
}
Write-Host "PASS_R312_SEAL_PATCH_FILES_VERIFIED: $Ok/$($Manifest.payload_file_count)"
Write-Host "Canonical boundary: 46.0 Ma POST_CHA1_20MY_DIVERSITY_RECOVERY"
