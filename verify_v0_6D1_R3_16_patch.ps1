$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "PATCH_MANIFEST_v0_6D1_R3_16_OVER_R3_15.json"
if (!(Test-Path $manifestPath)) { throw "Missing R3.16 patch manifest" }
$m = Get-Content $manifestPath -Raw | ConvertFrom-Json
$n = 0
foreach ($row in $m.files) {
  $p = Join-Path $root $row.path
  if (!(Test-Path $p -PathType Leaf)) { throw "Missing patch file: $($row.path)" }
  $h = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
  if ($h -ne $row.sha256) { throw "SHA mismatch: $($row.path) $h != $($row.sha256)" }
  $n++
}
$sealPath = Join-Path $root "R3_15_SEAL_SUMMARY.json"
$auditPath = Join-Path $root "outputs\v0_6D1_R3_15\FORMAL_AUDIT_SEALED_v0_6D1_R3_15.json"
$jp = Join-Path $root "local_runs\v0_6D1_R3_15\WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.json"
$np = Join-Path $root "local_runs\v0_6D1_R3_15\WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.npz"
foreach ($p in @($sealPath,$auditPath,$jp,$np)) { if (!(Test-Path $p -PathType Leaf)) { throw "Missing R3.15 SEALED parent evidence: $p" } }
$seal = Get-Content $sealPath -Raw | ConvertFrom-Json
$audit = Get-Content $auditPath -Raw | ConvertFrom-Json
$wantVerdict = "PASS_R315_CANONICAL_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__250KA_PRE_C2_BRIDGE_RESTART_BOUNDARY_SEALED"
if ($seal.verdict -ne $wantVerdict) { throw "R3.15 seal verdict mismatch" }
if ([math]::Abs([double]$seal.boundary.age_ma - 0.25) -gt 1e-12) { throw "R3.15 boundary is not 250 ka" }
if ($audit.verdict -ne $wantVerdict -or $audit.checks -ne "292/292") { throw "R3.15 sealed audit mismatch" }
$jph = (Get-FileHash -Algorithm SHA256 $jp).Hash.ToLowerInvariant()
$nph = (Get-FileHash -Algorithm SHA256 $np).Hash.ToLowerInvariant()
if ($jph -ne "4fb4ffdd711b7a5439ffff15a0a6f381e42ca560b00a2338d70edb77d848bcf6") { throw "R3.15 checkpoint JSON hash mismatch" }
if ($nph -ne "f8e79ea862de6c48f01784c727ca15abf9d8fd53b07f47d1aaab5bf589ee5692") { throw "R3.15 checkpoint NPZ hash mismatch" }
Write-Host "PASS_R316_PATCH_FILES_VERIFIED: $n/$n"
Write-Host "Parent boundary: R3.15 SEALED 250 ka PRE-C2 bridge"
Write-Host "Canonical R3.16 biology endpoint: 125 ka"
Write-Host "C2 environmental exposure: 150 x 500-y intervals consumed; 10 x 500-y intervals remain to 120 ka"
Write-Host "Biology cadence changes: NONE (125 kyr preserved)"
Write-Host "Scientific parameter changes: NONE"
