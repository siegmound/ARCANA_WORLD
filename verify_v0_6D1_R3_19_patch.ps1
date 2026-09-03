$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$expected = @{
  "CANONICAL_PHASE_AWARE_TRANSPORT_H0_PRESENT_CLOSURE_CONTRACT_v0_6D1_R3_19.md" = "4127f92fc3b24307f77d562b119a4b4d4f8132d78984a5111115040d70605bcf"
  "NEXT_STAGE_HANDOFF_v0_6D1_R3_19.md" = "42169508911c7e85e824d1617fa5bf57f10c3ddec655efc979d32963378bfadf"
  "PATCH_MANIFEST_v0_6D1_R3_19_OVER_R3_18.json" = "c193c0197a59420975fbef5d0f3de14264f13c70497e1336b9d2793f8e66adcc"
  "R3_19_PHASE_AWARE_TRANSPORT_PROMOTION_AUDIT.md" = "d5699be67f4aba9bacc334573355fcb0f1054842b70f25145c9ac5a878f6c64a"
  "README_R3_19.md" = "94ae813f71b2aeb4d76de4399c318055ce25fc8d35302e2ff5df485788c460c3"
  "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_19.json" = "cd937bc094960ff8159148a6a01be3a2c77ee25a72b9ca729c1fd963846809d5"
  "V0_6D1_R3_19_STATUS.md" = "085aedf2e02476b28881049b5dd25a5b5967ce237a3b595c92e427e7e59065de"
  "configs\world1_r319_phase_aware_transport_closure_v0_6D1_R3_19.json" = "a6386f6c8d2af9bb48d5570179ea6b99fa338fc33d56d0798de94e05a516a9cc"
  "outputs\v0_6D1_R3_19\FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_19.json" = "7d209bd9d85b25bc01d6e707047cbe92ee99e29a765d8e3f03a6b0dc96c6a68a"
  "run_v0_6D1_R3_19_checks.ps1" = "9c85ea8814674f8d7fce65ae444c8f1e96d65ab1d77b57f8252a192d2230bc54"
  "run_v0_6D1_R3_19_phase_aware_transport_closure.ps1" = "838da2b90b04a215737ae11b2db2823e575e0fda23a268d783c2fbe91a863fdf"
  "scripts\formal_audit_v0_6D1_R3_19_candidate.py" = "26f4c581b206fe9680837613a15dce074285ecbbb72030d6e23c324d28a7a4a5"
  "scripts\run_v0_6D1_R3_19_phase_aware_transport_closure.py" = "4df09f53c19302ce09726ce25164dd7fc2c53923049456c46ed158da1401740d"
  "src\arcana_worldsim\scientific_engines\r319_phase_aware_transport_closure.py" = "32788c986ead725faa5f5ab1e1350a2428c8ee29da3c9bee7a6cf0e2de6b7e20"
  "tests\test_r319_phase_aware_transport_closure.py" = "03f9e54c876b05c9ecf7a29c4cf7f2391e4a02dd6a6ebb3eaa7da0a67e1f929d"
}
$bad = @()
foreach ($rel in $expected.Keys) {
  $p = Join-Path $root $rel
  if (-not (Test-Path $p -PathType Leaf)) { $bad += "MISSING $rel"; continue }
  $got = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
  if ($got -ne $expected[$rel]) { $bad += "SHA $rel $got" }
}
$sealPath = Join-Path $root "R3_18_SEAL_SUMMARY.json"
$auditPath = Join-Path $root "outputs\v0_6D1_R3_18\FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json"
$sumPath = Join-Path $root "local_runs\v0_6D1_R3_18\R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json"
$envPath = Join-Path $root "local_runs\v0_6D1_R3_18\R3_18_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_ENVELOPE.json"
$bundlePath = Join-Path $root "local_runs\v0_6D1_R3_18\R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz"
foreach ($p in @($sealPath,$auditPath,$sumPath,$envPath,$bundlePath)) { if (-not (Test-Path $p -PathType Leaf)) { $bad += "MISSING_PARENT $p" } }
$verdict = "PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_READINESS_SEALED"
if (Test-Path $sealPath) {
  $s = Get-Content $sealPath -Raw | ConvertFrom-Json
  if ($s.stage -ne "v0.6D1-R3.18" -or $s.verdict -ne $verdict) { $bad += "R318_SEAL_VERDICT" }
}
if (Test-Path $auditPath) {
  $a = Get-Content $auditPath -Raw | ConvertFrom-Json
  if ($a.checks -ne "172/172" -or $a.verdict -ne $verdict) { $bad += "R318_AUDIT" }
}
if (Test-Path $sumPath) { $h=(Get-FileHash -Algorithm SHA256 $sumPath).Hash.ToLowerInvariant(); if ($h -ne "189007565f3f70c89b73e71bb4c23e9339bb392c550408a08b0d43c60f71317a") { $bad += "R318_SUMMARY_SHA $h" } }
if (Test-Path $envPath) { $h=(Get-FileHash -Algorithm SHA256 $envPath).Hash.ToLowerInvariant(); if ($h -ne "45f42200faa315ad7fe69f4fa8bcb1019c8f0c8dcb90fc2a18488bd40a9df58a") { $bad += "R318_ENVELOPE_SHA $h" } }
if (Test-Path $bundlePath) { $h=(Get-FileHash -Algorithm SHA256 $bundlePath).Hash.ToLowerInvariant(); if ($h -ne "54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70") { $bad += "R318_BUNDLE_SHA $h" } }
if ($bad.Count -gt 0) { $bad | ForEach-Object { Write-Error $_ }; exit 1 }
Write-Host "PASS_R319_PATCH_FILES_VERIFIED: 15/15"
Write-Host "Parent boundary: R3.18 SEALED recent exposure complete / biology preserved at 125 ka (172/172)"
Write-Host "R3.19 biology closure: 125 ka -> 0 ka"
Write-Host "Transport: exactly 2 x 62.5 kyr with phase-specific forcing"
Write-Host "Constant-forcing bit-exact R3.8 promotion gate: REQUIRED"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology/transport cadence changes: NONE"
Write-Host "Deep biological coupling: OFF"
Write-Host "Next: .\run_v0_6D1_R3_19_checks.ps1"
