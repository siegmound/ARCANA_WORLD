$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "PATCH_MANIFEST_v0_6D1_R3_20_OVER_R3_19.json"
if (-not (Test-Path $manifestPath)) { throw "Missing R3.20 patch manifest" }
$m = Get-Content $manifestPath -Raw | ConvertFrom-Json
$ok = 0
$total = 0
foreach ($p in $m.files.PSObject.Properties) {
    $total++
    $path = Join-Path $root $p.Name
    if (-not (Test-Path $path)) { throw "Missing governed R3.20 file: $($p.Name)" }
    $got = (Get-FileHash -Algorithm SHA256 $path).Hash.ToLowerInvariant()
    $want = [string]$p.Value
    if ($got -ne $want.ToLowerInvariant()) { throw "SHA mismatch for $($p.Name): $got != $want" }
    $ok++
}
$sealPath = Join-Path $root "R3_19_SEAL_SUMMARY.json"
if (-not (Test-Path $sealPath)) { throw "R3.20 requires R3.19 SEALED summary" }
$seal = Get-Content $sealPath -Raw | ConvertFrom-Json
$sealChecks = $null
if ($null -ne $seal.formal_audit_checks) { $sealChecks = [string]$seal.formal_audit_checks }
elseif ($null -ne $seal.checks) { $sealChecks = [string]$seal.checks }
if ($sealChecks -ne "73/73") { throw "R3.19 seal is not 73/73; got '$sealChecks'" }
$expectedVerdict = "PASS_R319_CANONICAL_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_BOUNDARY_SEALED"
if ([string]$seal.verdict -ne $expectedVerdict) { throw "R3.19 seal verdict mismatch" }
$j = Join-Path $root "local_runs\v0_6D1_R3_19\WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.json"
$n = [System.IO.Path]::ChangeExtension($j,".npz")
$jh = (Get-FileHash -Algorithm SHA256 $j).Hash.ToLowerInvariant()
$nh = (Get-FileHash -Algorithm SHA256 $n).Hash.ToLowerInvariant()
if ($jh -ne "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71") { throw "R3.19 JSON authority mismatch" }
if ($nh -ne "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406") { throw "R3.19 NPZ authority mismatch" }
$c1 = Join-Path $root "src\arcana_worldsim\late_cenozoic\cha2_nested_50y.py"
$c1h = (Get-FileHash -Algorithm SHA256 $c1).Hash.ToLowerInvariant()
if ($c1h -ne "d0b121f0b0fe7214d6c6f4736176d1c64f419c77dd991659291fe12b633ada0f") { throw "CHA2 C1 authority was modified" }
Write-Host "PASS_R320_PATCH_FILES_VERIFIED: $ok/$total"
Write-Host "Parent: R3.19 SEALED H0 0 ka (73/73)"
Write-Host "CHA-2/C1 authority: PRESERVED"
Write-Host "R3.20 role: Younger-Dryas-class magnitude audit + derived 50-y hydrological hazard"
Write-Host "Impact origin required: NO"
Write-Host "Human/settlement/flood-myth/religion calibration targets: NONE"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_20_checks.ps1"
