$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $root "run_v0_6D1_R3_20_sealed_checks.ps1"
$manifest = Join-Path $root "R320_SEAL_GATE_PATCH_MANIFEST.json"
if (-not (Test-Path $runner)) { throw "Missing repaired R3.20 sealed-check runner" }
if (-not (Test-Path $manifest)) { throw "Missing updated R3.20 seal manifest" }
$rh = (Get-FileHash -Algorithm SHA256 $runner).Hash.ToLowerInvariant()
if ($rh -ne "d41324506bb096f1ae2fb602e942f29ee8488fab658d10cf0755d96314225920") { throw "Runner SHA mismatch: $rh" }
$mh = (Get-FileHash -Algorithm SHA256 $manifest).Hash.ToLowerInvariant()
if ($mh -ne "64fe9fa1ffa3e2cdbb228f2f7a3ab8c78404901a1384634bd38a03c137979b19") { throw "Manifest SHA mismatch: $mh" }
$m = Get-Content $manifest -Raw | ConvertFrom-Json
if ([string]$m.files.'run_v0_6D1_R3_20_sealed_checks.ps1' -ne "d41324506bb096f1ae2fb602e942f29ee8488fab658d10cf0755d96314225920") { throw "Manifest does not govern repaired runner SHA" }
$text = Get-Content $runner -Raw
if ($text -notmatch '57/57') { throw "Repaired runner does not require 57/57" }
if ($text -match '51/51') { throw "Stale 51/51 remains in repaired runner" }
Write-Host "PASS_R320_R1_SEAL_COUNT_HOTFIX_VERIFIED: 2/2"
Write-Host "Candidate formal-audit authority: 57/57"
Write-Host "Scientific changes: NONE"
Write-Host "Next: .\verify_v0_6D1_R3_20_seal_gate_patch.ps1"
Write-Host "Then: .\run_v0_6D1_R3_20_sealed_checks.ps1"
