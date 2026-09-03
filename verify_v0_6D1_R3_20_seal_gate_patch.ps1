$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "R320_SEAL_GATE_PATCH_MANIFEST.json"
if (-not (Test-Path $manifestPath)) { throw "Missing R3.20 seal gate manifest" }
$m = Get-Content $manifestPath -Raw | ConvertFrom-Json
$ok = 0; $total = 0
foreach ($p in $m.files.PSObject.Properties) {
  $total++
  $path = Join-Path $root $p.Name
  if (-not (Test-Path $path)) { throw "Missing governed R3.20 seal file: $($p.Name)" }
  $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
  $want = ([string]$p.Value).ToLowerInvariant()
  if ($got -ne $want) { throw "SHA mismatch for $($p.Name): $got != $want" }
  $ok++
}
$seal19 = Join-Path $root "R3_19_SEAL_SUMMARY.json"
if (-not (Test-Path $seal19)) { throw "Missing R3.19 SEALED parent" }
$s19 = Get-Content $seal19 -Raw | ConvertFrom-Json
$c19 = if ($null -ne $s19.formal_audit_checks) { [string]$s19.formal_audit_checks } else { [string]$s19.checks }
if ($c19 -ne "73/73") { throw "R3.19 parent is not 73/73" }
if ([string]$s19.verdict -ne "PASS_R319_CANONICAL_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_BOUNDARY_SEALED") { throw "R3.19 parent verdict mismatch" }
$run = Join-Path $root "local_runs\v0_6D1_R3_20"
$sum = Join-Path $run "R3_20_CHA2_YD_MAGNITUDE_AND_HYDROLOGICAL_HAZARD_SUMMARY.json"
$npz = Join-Path $run "R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz"
if (-not (Test-Path $sum) -or -not (Test-Path $npz)) { throw "Missing canonical R3.20 evidence" }
if ((Get-FileHash -Algorithm SHA256 $sum).Hash.ToLowerInvariant() -ne "ab5abbe28bccab3df2d18384ff9563e71d82af4d6a59a4e5484ab5c2b5116cab") { throw "R3.20 summary SHA mismatch" }
if ((Get-FileHash -Algorithm SHA256 $npz).Hash.ToLowerInvariant() -ne "4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14") { throw "R3.20 hazard NPZ SHA mismatch" }
$c1 = Join-Path $root "src\arcana_worldsim\late_cenozoic\cha2_nested_50y.py"
if ((Get-FileHash -Algorithm SHA256 $c1).Hash.ToLowerInvariant() -ne "d0b121f0b0fe7214d6c6f4736176d1c64f419c77dd991659291fe12b633ada0f") { throw "CHA-2/C1 authority mismatch" }
Write-Host "PASS_R320_SEAL_GATE_PATCH_FILES_VERIFIED: $ok/$total"
Write-Host "Parent: R3.19 SEALED H0 0 ka (73/73)"
Write-Host "CHA-2 classification: YOUNGER_DRYAS_CLASS"
Write-Host "Canonical evidence: summary + 15-11 ka / 50-y hazard NPZ SHA verified"
Write-Host "Independent magnitude + full hazard array replay seal: ENABLED"
Write-Host "CHA-2/C1 physical authority: PRESERVED"
Write-Host "R3.19 H0 biology: PRESERVED"
Write-Host "Human/cultural calibration targets: NONE"
Write-Host "Next: .\run_v0_6D1_R3_20_sealed_checks.ps1"
