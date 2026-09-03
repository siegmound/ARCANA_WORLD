param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "R317_SEAL_GATE_PATCH_MANIFEST.json"
if (-not (Test-Path $ManifestPath)) { throw "Missing R317_SEAL_GATE_PATCH_MANIFEST.json" }
$M = Get-Content $ManifestPath -Raw | ConvertFrom-Json

$Verified = 1
if ($M.stage -ne "v0.6D1-R3.17") { throw "R3.17 seal manifest stage mismatch" }
if ($M.scientific_parameter_changes -ne $false) { throw "Unexpected scientific changes in R3.17 seal gate" }
if ($M.biology_cadence_changes -ne $false) { throw "Unexpected biology cadence changes in R3.17 seal gate" }

foreach ($P in $M.payload_hashes.PSObject.Properties) {
    $Path = Join-Path $Root ($P.Name -replace '/', '\')
    if (-not (Test-Path $Path)) { throw "Missing seal payload file: $($P.Name)" }
    $Got = (Get-FileHash -Algorithm SHA256 $Path).Hash.ToLowerInvariant()
    $Want = ([string]$P.Value).ToLowerInvariant()
    if ($Got -ne $Want) { throw "SHA mismatch for $($P.Name): got $Got expected $Want" }
    $Verified++
}

$R316Seal = Join-Path $Root "R3_16_SEAL_SUMMARY.json"
$R316Audit = Join-Path $Root "outputs\v0_6D1_R3_16\FORMAL_AUDIT_SEALED_v0_6D1_R3_16.json"
if (-not (Test-Path $R316Seal)) { throw "Missing R3.16 seal summary" }
if (-not (Test-Path $R316Audit)) { throw "Missing R3.16 sealed audit" }
$S16 = Get-Content $R316Seal -Raw | ConvertFrom-Json
$A16 = Get-Content $R316Audit -Raw | ConvertFrom-Json
if ($S16.verdict -ne $M.required_parent.sealed_verdict) { throw "R3.16 parent seal verdict mismatch" }
if ($A16.verdict -ne $M.required_parent.sealed_verdict) { throw "R3.16 parent audit verdict mismatch" }
if ($A16.checks -ne $M.required_parent.formal_audit_checks) { throw "R3.16 parent audit count mismatch" }

foreach ($P in $M.canonical_artifacts.PSObject.Properties) {
    $Path = Join-Path $Root ($P.Name -replace '/', '\')
    if (-not (Test-Path $Path)) { throw "Missing canonical R3.17 artifact: $($P.Name)" }
    $Got = (Get-FileHash -Algorithm SHA256 $Path).Hash.ToLowerInvariant()
    $Want = ([string]$P.Value).ToLowerInvariant()
    if ($Got -ne $Want) { throw "Canonical artifact SHA mismatch for $($P.Name): got $Got expected $Want" }
}
$Summary = Join-Path $Root "local_runs\v0_6D1_R3_17\R3_17_EXACT_120KA_ENVIRONMENTAL_RESTART_SUMMARY.json"
if (-not (Test-Path $Summary)) { throw "Missing canonical R3.17 summary" }
$SR = Get-Content $Summary -Raw | ConvertFrom-Json
$Ready = "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__R316_125KA_BIOLOGY_PRESERVED_WITH_5KYR_PENDING_EXPOSURE"
if ($SR.verdict -ne $Ready) { throw "R3.17 canonical summary verdict mismatch" }
if ([math]::Abs([double]$SR.physical_restart_age_ma - 0.12) -gt 1e-12) { throw "R3.17 physical restart is not 120 ka" }
if ([math]::Abs([double]$SR.biology_state_age_ma - 0.125) -gt 1e-12) { throw "R3.17 biology state is not preserved at 125 ka" }
if ($SR.biology_state_mutated -ne $false -or $SR.biology_state_identity_exact -ne $true) { throw "R3.17 biology identity gate failed" }

Write-Host "PASS_R317_SEAL_GATE_PATCH_FILES_VERIFIED: $Verified/5"
Write-Host "Canonical physical restart: 120 ka"
Write-Host "Canonical biology state: 125 ka SEALED state preserved"
Write-Host "Pending exposure: 5 kyr (10 x 500-y C2 intervals)"
Write-Host "Independent exposure replay seal: ENABLED"
Write-Host "Scientific changes: NONE"
Write-Host "Biology/cadence changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_17_sealed_checks.ps1"
