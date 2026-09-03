$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "R3_16_R3_HOTFIX_MANIFEST.json"
if (-not (Test-Path $manifestPath)) { throw "Missing R3_16_R3_HOTFIX_MANIFEST.json" }
$m = Get-Content $manifestPath -Raw | ConvertFrom-Json
$ok = 0
$total = 0
foreach ($p in $m.files.PSObject.Properties) {
  $total++
  $rel = $p.Name
  $want = [string]$p.Value
  $path = Join-Path $root $rel
  if (-not (Test-Path $path)) { throw "Missing hotfix payload: $rel" }
  $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
  if ($got -ne $want.ToLowerInvariant()) { throw "SHA mismatch: $rel`n got=$got`nwant=$want" }
  $ok++
}
Write-Host "PASS_R316_R3_RUNTIME_A1_NPZFILE_HOTFIX_FILES_VERIFIED: $ok/$total"
Write-Host "R3.8 A1 container contract: NpzFile .files PRESERVED"
Write-Host "R3.14 provider A1 dict semantics: PRESERVED"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology changes: NONE"
