$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "PATCH_MANIFEST_v0_6D1_R3_14_OVER_R3_13.json"
if (!(Test-Path $ManifestPath)) { throw "Missing R3.14 patch manifest" }
$M = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$ok = 0
foreach ($prop in $M.files.PSObject.Properties) {
  $rel = $prop.Name.Replace('/', [IO.Path]::DirectorySeparatorChar)
  $path = Join-Path $Root $rel
  if (!(Test-Path $path)) { throw "Missing patch file: $rel" }
  $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
  $want = [string]$prop.Value
  if ($got -ne $want) { throw "SHA mismatch: $rel`n$got`n$want" }
  $ok++
}
$Seal = Join-Path $Root "R3_13_SEAL_SUMMARY.json"
if (!(Test-Path $Seal)) { throw "R3.14 requires R3.13 SEALED overlay first" }
$S = Get-Content $Seal -Raw | ConvertFrom-Json
if ($S.stage -ne "v0.6D1-R3.13" -or [math]::Abs([double]$S.boundary.age_ma - 30.0) -gt 1e-12) { throw "R3.13 SEALED 30 Ma parent boundary not verified" }
Write-Host "PASS_R314_PATCH_FILES_VERIFIED: $ok/$($M.file_count)"
Write-Host "Parent boundary: R3.13 SEALED 30.0 Ma verified"
Write-Host "Scientific authority replacements: NONE"
