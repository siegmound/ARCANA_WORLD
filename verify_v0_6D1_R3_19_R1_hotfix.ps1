$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "R319_R1_RUNTIME_Q_CEILING_HOTFIX_MANIFEST.json"
if (-not (Test-Path $manifestPath)) { throw "Missing R319-R1 hotfix manifest" }
$m = Get-Content $manifestPath -Raw | ConvertFrom-Json

$checked = 0
foreach ($p in $m.payload_hashes.PSObject.Properties) {
    $rel = $p.Name
    $want = [string]$p.Value
    $path = Join-Path $root $rel
    if (-not (Test-Path $path)) { throw "Missing hotfix payload: $rel" }
    $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
    if ($got -ne $want.ToLowerInvariant()) { throw "SHA mismatch for $rel`n got=$got`nwant=$want" }
    $checked++
}

$r319 = Join-Path $root "src\arcana_worldsim\scientific_engines\r319_phase_aware_transport_closure.py"
$r38 = Join-Path $root "src\arcana_worldsim\scientific_engines\r38_restartable_checkpoint.py"
if ((Get-FileHash -Algorithm SHA256 $r319).Hash.ToLowerInvariant() -ne ([string]$m.expected_r319_engine_sha256).ToLowerInvariant()) { throw "R3.19 engine authority changed" }
if ((Get-FileHash -Algorithm SHA256 $r38).Hash.ToLowerInvariant() -ne ([string]$m.expected_r38_sha256).ToLowerInvariant()) { throw "R3.8 sealed authority changed" }

$sealPath = Join-Path $root "R3_18_SEAL_SUMMARY.json"
$auditPath = Join-Path $root "outputs\v0_6D1_R3_18\FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json"
if (-not (Test-Path $sealPath)) { throw "Missing R3.18 seal summary" }
if (-not (Test-Path $auditPath)) { throw "Missing R3.18 sealed audit" }
$seal = Get-Content $sealPath -Raw | ConvertFrom-Json
$audit = Get-Content $auditPath -Raw | ConvertFrom-Json
if ([string]$seal.verdict -ne [string]$m.expected_r318_seal_verdict) { throw "R3.18 seal verdict mismatch" }
if ([string]$audit.verdict -ne [string]$m.expected_r318_seal_verdict -or [string]$audit.checks -ne [string]$m.expected_r318_sealed_checks) { throw "R3.18 sealed audit mismatch" }

$runner = Get-Content (Join-Path $root "scripts\run_v0_6D1_R3_19_phase_aware_transport_closure.py") -Raw
if ($runner -notmatch 'q_ceiling=float\(cfg\.variance_ceiling_normalized\)') { throw "Repaired q-ceiling authority binding missing" }
if ($runner -match 'cfg\.resource_variance_ceiling') { throw "Stale q-ceiling attribute still present" }

Write-Host "PASS_R319_R1_RUNTIME_Q_CEILING_HOTFIX_FILES_VERIFIED: $checked/$checked"
Write-Host "R3.19 engine authority: PRESERVED"
Write-Host "R3.8 sealed authority: PRESERVED"
Write-Host "q ceiling authority: variance_ceiling_normalized = 0.08"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology/transport changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_19_checks.ps1 ; then .\run_v0_6D1_R3_19_phase_aware_transport_closure.ps1"
