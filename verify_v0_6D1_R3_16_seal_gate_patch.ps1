$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "R3_16_SEAL_GATE_PATCH_MANIFEST.json"
if (-not (Test-Path $ManifestPath)) { throw "Missing R3.16 seal-gate patch manifest" }
$m = Get-Content -Raw $ManifestPath | ConvertFrom-Json
$ok = 0; $total = 0
foreach ($p in $m.payload.PSObject.Properties) {
    $total++
    $path = Join-Path $Root $p.Name
    if (-not (Test-Path $path)) { throw "Missing seal-gate payload file: $($p.Name)" }
    $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
    $want = [string]$p.Value
    if ($got -ne $want) { throw "SHA mismatch for $($p.Name): got=$got want=$want" }
    $ok++
}

$R315Seal = Join-Path $Root "R3_15_SEAL_SUMMARY.json"
if (-not (Test-Path $R315Seal)) { throw "Missing authoritative R3.15 seal" }
$s15 = Get-Content -Raw $R315Seal | ConvertFrom-Json
if ($s15.verdict -ne "PASS_R315_CANONICAL_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__250KA_PRE_C2_BRIDGE_RESTART_BOUNDARY_SEALED") { throw "R3.15 seal verdict mismatch" }

$RunDir = Join-Path $Root "local_runs\v0_6D1_R3_16"
$CkJson = Join-Path $RunDir "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.json"
$CkNpz = Join-Path $RunDir "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.npz"
foreach ($x in @($CkJson,$CkNpz)) { if (-not (Test-Path $x)) { throw "Missing canonical R3.16 checkpoint artifact: $x" } }
$hj = (Get-FileHash -Algorithm SHA256 $CkJson).Hash.ToLowerInvariant()
$hn = (Get-FileHash -Algorithm SHA256 $CkNpz).Hash.ToLowerInvariant()
if ($hj -ne $m.canonical_checkpoint_hashes.json) { throw "R3.16 canonical JSON SHA mismatch" }
if ($hn -ne $m.canonical_checkpoint_hashes.npz) { throw "R3.16 canonical NPZ SHA mismatch" }

Write-Host "PASS_R316_SEAL_GATE_PATCH_FILES_VERIFIED: $ok/$total"
Write-Host "Canonical checkpoint: 125 ka PRE-120ka-restart verified"
Write-Host "Independent replay seal: ENABLED"
Write-Host "Scientific changes: NONE"
Write-Host "Biology/cadence changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_16_sealed_checks.ps1"
