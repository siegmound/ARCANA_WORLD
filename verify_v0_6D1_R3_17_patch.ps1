$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "PATCH_MANIFEST_v0_6D1_R3_17_OVER_R3_16.json"
if (-not (Test-Path $manifestPath)) { throw "Missing R3.17 patch manifest" }
$m = Get-Content $manifestPath -Raw | ConvertFrom-Json
$ok = 0; $total = 0
foreach ($p in $m.payload_files.PSObject.Properties) {
    $total++
    $path = Join-Path $root ($p.Name -replace '/', '\')
    if (-not (Test-Path $path)) { throw "Missing R3.17 payload file: $($p.Name)" }
    $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
    $want = ([string]$p.Value).ToLowerInvariant()
    if ($got -ne $want) { throw "SHA mismatch: $($p.Name)`n got=$got`nwant=$want" }
    $ok++
}

$sealPath = Join-Path $root "R3_16_SEAL_SUMMARY.json"
$auditPath = Join-Path $root "outputs\v0_6D1_R3_16\FORMAL_AUDIT_SEALED_v0_6D1_R3_16.json"
$runDir = Join-Path $root "local_runs\v0_6D1_R3_16"
$cj = Join-Path $runDir "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.json"
$cn = Join-Path $runDir "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.npz"
foreach ($p in @($sealPath,$auditPath,$cj,$cn)) { if (-not (Test-Path $p)) { throw "R3.17 requires R3.16 SEALED parent artifact: $p" } }
$seal = Get-Content $sealPath -Raw | ConvertFrom-Json
$audit = Get-Content $auditPath -Raw | ConvertFrom-Json
$expectedVerdict = "PASS_R316_CANONICAL_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__125KA_PRE_120KA_RESTART_BOUNDARY_SEALED"
if ($seal.stage -ne "v0.6D1-R3.16" -or $seal.verdict -ne $expectedVerdict -or $seal.checks -ne "193/193") { throw "R3.16 seal is not the expected 193/193 authority" }
if ($audit.verdict -ne $expectedVerdict -or $audit.checks -ne "193/193") { throw "R3.16 sealed audit is not the expected 193/193 authority" }
$jsha = (Get-FileHash -Algorithm SHA256 $cj).Hash.ToLowerInvariant()
$nsha = (Get-FileHash -Algorithm SHA256 $cn).Hash.ToLowerInvariant()
if ($jsha -ne ([string]$m.expected_parent_checkpoint_json_sha256).ToLowerInvariant()) { throw "R3.16 checkpoint JSON SHA mismatch" }
if ($nsha -ne ([string]$m.expected_parent_checkpoint_npz_sha256).ToLowerInvariant()) { throw "R3.16 checkpoint NPZ SHA mismatch" }

Write-Host "PASS_R317_PATCH_FILES_VERIFIED: $ok/$total"
Write-Host "Parent boundary: R3.16 SEALED 125 ka (193/193)"
Write-Host "R3.17 physical restart: 120 ka; biology state remains 125 ka"
Write-Host "Pending exposure: 10 x 500-y C2 intervals = 5 kyr"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology/cadence changes: NONE"
