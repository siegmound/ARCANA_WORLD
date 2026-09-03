param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest = Join-Path $Root "PATCH_MANIFEST_v0_6D1_R3_15_SEAL_GATE.json"
if (!(Test-Path $Manifest)) { throw "Missing R3.15 seal-gate manifest" }
$M = Get-Content $Manifest -Raw | ConvertFrom-Json
$count = 0
foreach ($p in $M.payload.PSObject.Properties) {
    $Path = Join-Path $Root $p.Name
    if (!(Test-Path $Path)) { throw "Missing seal-gate file: $($p.Name)" }
    $got = (Get-FileHash -Algorithm SHA256 $Path).Hash.ToLowerInvariant()
    $want = [string]$p.Value
    if ($got -ne $want) { throw "SHA mismatch: $($p.Name) $got != $want" }
    $count++
}
$RunDir = Join-Path $Root "local_runs\v0_6D1_R3_15"
$J = Join-Path $RunDir "WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.json"
$N = Join-Path $RunDir "WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.npz"
$S = Join-Path $RunDir "R3_15_LATE_CENOZOIC_SECULAR_BIOLOGY_SUMMARY.json"
foreach ($x in @($J,$N,$S)) { if (!(Test-Path $x)) { throw "Missing canonical R3.15 evidence: $x" } }
$jh=(Get-FileHash -Algorithm SHA256 $J).Hash.ToLowerInvariant(); if ($jh -ne $M.canonical_checkpoint_expected.json_sha256) { throw "R3.15 JSON checkpoint SHA mismatch" }
$nh=(Get-FileHash -Algorithm SHA256 $N).Hash.ToLowerInvariant(); if ($nh -ne $M.canonical_checkpoint_expected.npz_sha256) { throw "R3.15 NPZ checkpoint SHA mismatch" }
$sh=(Get-FileHash -Algorithm SHA256 $S).Hash.ToLowerInvariant(); if ($sh -ne $M.canonical_checkpoint_expected.summary_sha256) { throw "R3.15 summary SHA mismatch" }
Write-Host "PASS_R315_SEAL_GATE_PATCH_FILES_VERIFIED: $count/$count"
Write-Host "Canonical boundary: 250 ka PRE-C2-200ka-BRIDGE"
Write-Host "Scientific changes: NONE"
Write-Host "Biology changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_15_sealed_checks.ps1"
