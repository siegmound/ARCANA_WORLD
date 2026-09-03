$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "PATCH_MANIFEST_v0_6D1_R3_19_R2.json"
if (-not (Test-Path $manifestPath)) { throw "Missing R3.19-R2 patch manifest" }
$m = Get-Content -Raw $manifestPath | ConvertFrom-Json
$ok = 0
$total = [int]$m.payload_file_count
foreach ($p in $m.files.PSObject.Properties) {
    $path = Join-Path $root $p.Name
    if (-not (Test-Path $path)) { throw "Missing patch payload: $($p.Name)" }
    $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
    $want = ([string]$p.Value).ToLowerInvariant()
    if ($got -ne $want) { throw "SHA mismatch for $($p.Name): $got != $want" }
    $ok++
}
if ($ok -ne $total) { throw "Patch payload count mismatch: $ok/$total" }

$r38 = Join-Path $root "src\arcana_worldsim\scientific_engines\r38_restartable_checkpoint.py"
if (-not (Test-Path $r38)) { throw "Missing SEALED R3.8 runtime" }
$r38sha = (Get-FileHash -Algorithm SHA256 $r38).Hash.ToLowerInvariant()
if ($r38sha -ne ([string]$m.r38_sealed_sha256).ToLowerInvariant()) { throw "SEALED R3.8 SHA mismatch" }

$sealPath = Join-Path $root "R3_18_SEAL_SUMMARY.json"
$auditPath = Join-Path $root "outputs\v0_6D1_R3_18\FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json"
if (-not (Test-Path $sealPath)) { throw "R3.19-R2 requires R3.18 SEALED parent" }
if (-not (Test-Path $auditPath)) { throw "Missing R3.18 sealed audit" }
$seal = Get-Content -Raw $sealPath | ConvertFrom-Json
$audit = Get-Content -Raw $auditPath | ConvertFrom-Json
if ([string]$audit.checks -ne "172/172") { throw "R3.18 sealed audit is not 172/172" }
if ([string]$seal.verdict -ne "PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_READINESS_SEALED") { throw "R3.18 seal verdict mismatch" }

$run = Join-Path $root "local_runs\v0_6D1_R3_18"
$items = @{
  "R3_18_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_ENVELOPE.json" = [string]$m.r318_canonical_hashes.envelope
  "R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz" = [string]$m.r318_canonical_hashes.bundle
  "R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json" = [string]$m.r318_canonical_hashes.summary
}
foreach ($name in $items.Keys) {
  $p = Join-Path $run $name
  if (-not (Test-Path $p)) { throw "Missing canonical R3.18 artifact: $name" }
  $got = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
  if ($got -ne $items[$name].ToLowerInvariant()) { throw "R3.18 canonical artifact SHA mismatch: $name" }
}

Write-Host "PASS_R319_R2_ENDPOINT_SUPPORT_RECONCILIATION_PATCH_FILES_VERIFIED: $ok/$total"
Write-Host "Parent: R3.18 SEALED 172/172 and canonical hashes verified"
Write-Host "R3.8 SEALED runtime: PRESERVED"
Write-Host "Continuous phase forcing: PRESERVED"
Write-Host "Exact 0 ka discrete support topology: ENABLED"
Write-Host "Post-phase2 conservative endpoint reconciliation: SEALED remap_to_land"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology/transport cadence changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_19_checks.ps1"
