$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$expected = @{
  "CANONICAL_RECENT_H0_EXPOSURE_COMPLETION_TRANSPORT_PHASE_READINESS_CONTRACT_v0_6D1_R3_18.md" = "c5942a2c96d89d00f20cb592fcc974972fa5c4b1b20f278b11aa06fa54f4f65b"
  "NEXT_STAGE_HANDOFF_v0_6D1_R3_18.md" = "41ced87469b05f74861f6a1e06fd0b831b5eb7cc9002cbe36bbe12501aaf55d3"
  "PATCH_MANIFEST_v0_6D1_R3_18_OVER_R3_17.json" = "ad9ab97cc9d4c6c2f71378418a3a3bd2c669ab6b8a7730c7d82e86cad4dc337f"
  "R3_18_TRANSPORT_PHASE_OPERATOR_AUDIT.md" = "bdd1478c987528f11b634c848a3ed9e6adacae267770e89c1523da921307c7f7"
  "README_R3_18.md" = "4c421a24ce252d32adccbb7c0243a0900b262a0641ad3d9e28c04dcbb7d32851"
  "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_18.json" = "0fac56479bb1a4f8521d8ed3a506e9526938878f0b4c9b31c3c0c2f7f133d635"
  "V0_6D1_R3_18_STATUS.md" = "da3a0f8553fd18401852bc542a710ec2ec968796d5a0812066b2c6a08eddc036"
  "configs\world1_r318_recent_exposure_transport_readiness_v0_6D1_R3_18.json" = "d87632afe40a9bbb06dc9f212e993bd5cf7c89baf87c23173428416df2ae4ad9"
  "outputs\v0_6D1_R3_18\FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_18.json" = "3959ecd1b3c0f8dddc76b37736eda40774ae70851795ee7503e5a46692753610"
  "run_v0_6D1_R3_18_checks.ps1" = "c2bf69043e794495aade063dcc913e544b15e0508bd6bd5c75434feccbb88c81"
  "run_v0_6D1_R3_18_recent_exposure_transport_readiness.ps1" = "a028dd8b71d11990cde66260df83f04f0bf0e0b51cbc9e7c63b4d1d8062e9194"
  "scripts\formal_audit_v0_6D1_R3_18_candidate.py" = "9fa5c3c3c24a03b182a6279a8eb12ea91c94f5cc9a220e75dd3e25213fbfcadf"
  "scripts\run_v0_6D1_R3_18_recent_exposure_transport_readiness.py" = "d31d9e442cc192d8e96151bd2f6901a68f7750de80373d51db5fb5d4e0f1230c"
  "src\arcana_worldsim\scientific_engines\r318_recent_exposure_transport_readiness.py" = "b04283d1adccbe6c8f7b7af4c7354e811809163db2b5c8268bd86372e0c6cec9"
  "tests\test_r318_recent_exposure_transport_readiness.py" = "9193a70c331a18fef2b477a00c431d47310acc1f315b476e1325e974f8e94ba9"
}
$bad = @()
foreach ($rel in $expected.Keys) {
  $p = Join-Path $root $rel
  if (-not (Test-Path $p -PathType Leaf)) { $bad += "MISSING $rel"; continue }
  $got = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
  if ($got -ne $expected[$rel]) { $bad += "SHA $rel $got" }
}
$sealPath = Join-Path $root "R3_17_SEAL_SUMMARY.json"
$auditPath = Join-Path $root "outputs\v0_6D1_R3_17\FORMAL_AUDIT_SEALED_v0_6D1_R3_17.json"
$envPath = Join-Path $root "local_runs\v0_6D1_R3_17\R3_17_120KA_DUAL_CLOCK_RESTART_ENVELOPE.json"
$accPath = Join-Path $root "local_runs\v0_6D1_R3_17\R3_17_PENDING_125_TO_120KA_EXPOSURE_ACCUMULATOR.npz"
foreach ($p in @($sealPath,$auditPath,$envPath,$accPath)) { if (-not (Test-Path $p -PathType Leaf)) { $bad += "MISSING_PARENT $p" } }
if (Test-Path $sealPath) { $s = Get-Content $sealPath -Raw | ConvertFrom-Json; if ($s.stage -ne "v0.6D1-R3.17" -or $s.verdict -ne "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__125KA_BIOLOGY_STATE_AND_5KYR_PENDING_EXPOSURE_SEALED") { $bad += "R317_SEAL_VERDICT" } }
if (Test-Path $auditPath) { $a = Get-Content $auditPath -Raw | ConvertFrom-Json; if ($a.checks -ne "123/123" -or $a.verdict -ne "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__125KA_BIOLOGY_STATE_AND_5KYR_PENDING_EXPOSURE_SEALED") { $bad += "R317_AUDIT" } }
if (Test-Path $envPath) { $h=(Get-FileHash -Algorithm SHA256 $envPath).Hash.ToLowerInvariant(); if ($h -ne "5b800279324afdd19279fa0c395ace822b4104155690191f81c6be884d2aeca8") { $bad += "R317_ENVELOPE_SHA $h" } }
if (Test-Path $accPath) { $h=(Get-FileHash -Algorithm SHA256 $accPath).Hash.ToLowerInvariant(); if ($h -ne "b191faae44b4db8bc0afaaba942b0f04087758fa554c480375eb0f753ab309cc") { $bad += "R317_ACCUMULATOR_SHA $h" } }
if ($bad.Count -gt 0) { $bad | ForEach-Object { Write-Error $_ }; exit 1 }
Write-Host "PASS_R318_PATCH_FILES_VERIFIED: 15/15"
Write-Host "Parent boundary: R3.17 SEALED 120 ka environment / 125 ka biology (123/123)"
Write-Host "R3.18 physical exposure: 120 ka -> 0 ka; biology remains 125 ka"
Write-Host "Exact transport boundary: 62.5 ka inserted for coupling audit"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology/transport cadence changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_18_checks.ps1"
