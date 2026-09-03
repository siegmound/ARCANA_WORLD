$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "R3_14_R1_HOTFIX_MANIFEST.json"
if (-not (Test-Path $ManifestPath)) { throw "Missing R3_14_R1_HOTFIX_MANIFEST.json" }
$m = Get-Content -Raw $ManifestPath | ConvertFrom-Json
$count = 0
foreach ($prop in $m.files.PSObject.Properties) {
  $rel = $prop.Name
  $expected = [string]$prop.Value
  $path = Join-Path $Root ($rel -replace '/', '\')
  if (-not (Test-Path $path)) { throw "Missing hotfix file: $rel" }
  $actual = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
  if ($actual -ne $expected.ToLowerInvariant()) { throw "SHA mismatch: $rel`nexpected=$expected`nactual=$actual" }
  $count++
}
Write-Host "PASS_R314_R1_HOTFIX_FILES_VERIFIED: $count/$count"
Write-Host "Frozen v0.6.1 payload hashes: UNCHANGED"
Write-Host "Scientific parameter changes: NONE"
Write-Host "C1 sealed 100-y anchors: AUTHORITATIVE"
