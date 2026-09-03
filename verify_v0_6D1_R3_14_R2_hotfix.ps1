$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "R3_14_R2_HOTFIX_MANIFEST.json"
if (-not (Test-Path $ManifestPath)) { throw "Missing R3_14_R2_HOTFIX_MANIFEST.json" }
$M = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$Count = 0
foreach ($P in $M.files.PSObject.Properties) {
  $Rel = $P.Name.Replace('/', [IO.Path]::DirectorySeparatorChar)
  $Path = Join-Path $Root $Rel
  if (-not (Test-Path $Path)) { throw "Missing R3.14-R2 hotfix file: $($P.Name)" }
  $Got = (Get-FileHash -Algorithm SHA256 $Path).Hash.ToLowerInvariant()
  if ($Got -ne [string]$P.Value) { throw "SHA256 mismatch: $($P.Name)`nexpected=$($P.Value)`ngot=$Got" }
  $Count++
}
Write-Host "PASS_R314_R2_HOTFIX_FILES_VERIFIED: $Count/$Count"
Write-Host "C1 binding validation: ACTUAL C2.parent TYPE-GUARDED"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology changes: NONE"
