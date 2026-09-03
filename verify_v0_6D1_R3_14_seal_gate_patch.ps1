$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "R314_SEAL_GATE_PATCH_MANIFEST.json"
if (-not (Test-Path $ManifestPath)) { throw "Missing R314_SEAL_GATE_PATCH_MANIFEST.json" }
$M = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$Count = 0
foreach ($P in $M.files.PSObject.Properties) {
  $Rel = $P.Name.Replace('/', [IO.Path]::DirectorySeparatorChar)
  $Path = Join-Path $Root $Rel
  if (-not (Test-Path $Path)) { throw "Missing R3.14 seal-gate file: $($P.Name)" }
  $Got = (Get-FileHash -Algorithm SHA256 $Path).Hash.ToLowerInvariant()
  if ($Got -ne [string]$P.Value) { throw "SHA256 mismatch: $($P.Name)`nexpected=$($P.Value)`ngot=$Got" }
  $Count++
}
Write-Host "PASS_R314_SEAL_GATE_PATCH_FILES_VERIFIED: $Count/$Count"
Write-Host "Scientific changes: NONE"
Write-Host "Biology changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_14_sealed_checks.ps1"
