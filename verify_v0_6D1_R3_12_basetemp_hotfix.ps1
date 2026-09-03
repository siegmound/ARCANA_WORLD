$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "HOTFIX_MANIFEST_v0_6D1_R3_12_BASETEMP.json"
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$Ok = 0
foreach ($F in $Manifest.files) {
    $P = Join-Path $Root ($F.path -replace '/', '\')
    if (-not (Test-Path $P)) { throw "Missing: $($F.path)" }
    $H = (Get-FileHash -Algorithm SHA256 $P).Hash.ToLowerInvariant()
    if ($H -ne $F.sha256.ToLowerInvariant()) { throw "SHA256 mismatch: $($F.path)" }
    $Ok++
}
Write-Host "PASS_R312_BASETEMP_HOTFIX_FILES_VERIFIED: $Ok/$($Manifest.payload_file_count)"
Write-Host "Scientific changes: NONE"
Write-Host "Then run: .\\run_v0_6D1_R3_12_sealed_checks.ps1"
