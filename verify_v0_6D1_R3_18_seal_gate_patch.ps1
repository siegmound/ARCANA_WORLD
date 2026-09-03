$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Expected = @{
  "scripts\formal_audit_v0_6D1_R3_18_sealed.py" = "63f2374a9fbad01e5641001faa58410b43e2d3a83b08ddb71e3eb16ee49de23d"
  "run_v0_6D1_R3_18_sealed_checks.ps1" = "4be340f1b09b21304ac2abcd382f26a3e71966c68a338748f4c0bcef84a00610"
  "README_R3_18_SEAL_GATE.md" = "5c03440112218c1017c661a774192e9ac083b329091a4f95d2a9cb57c0d48f07"
  "R3_18_CANONICAL_RUN_EVIDENCE_AUDIT.md" = "502f6c1898842e69d92b42dcd6d923ddf0ebf4f4c422af88b12d7e35ca275bc4"
  "R318_SEAL_GATE_PATCH_MANIFEST.json" = "09fda1014fb7258146d9b9ad701de7315f2fcad463c83bcca47ade2575c122a6"
}
foreach ($Rel in $Expected.Keys) {
  $P = Join-Path $Root $Rel
  if (-not (Test-Path $P)) { throw "Missing R3.18 seal-gate file: $Rel" }
  $Got = (Get-FileHash -Algorithm SHA256 $P).Hash.ToLowerInvariant()
  if ($Got -ne $Expected[$Rel]) { throw "SHA mismatch for ${Rel}: $Got != $($Expected[$Rel])" }
}

$Evidence = @{
  "local_runs\v0_6D1_R3_18\R3_18_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_ENVELOPE.json" = "45f42200faa315ad7fe69f4fa8bcb1019c8f0c8dcb90fc2a18488bd40a9df58a"
  "local_runs\v0_6D1_R3_18\R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz" = "54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70"
  "local_runs\v0_6D1_R3_18\R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json" = "189007565f3f70c89b73e71bb4c23e9339bb392c550408a08b0d43c60f71317a"
}
foreach ($Rel in $Evidence.Keys) {
  $P = Join-Path $Root $Rel
  if (-not (Test-Path $P)) { throw "Missing canonical R3.18 evidence: $Rel" }
  $Got = (Get-FileHash -Algorithm SHA256 $P).Hash.ToLowerInvariant()
  if ($Got -ne $Evidence[$Rel]) { throw "Canonical evidence SHA mismatch for ${Rel}: $Got != $($Evidence[$Rel])" }
}

$ParentSeal = Join-Path $Root "R3_17_SEAL_SUMMARY.json"
$ParentAudit = Join-Path $Root "outputs\v0_6D1_R3_17\FORMAL_AUDIT_SEALED_v0_6D1_R3_17.json"
if (-not (Test-Path $ParentSeal)) { throw "Missing R3.17 SEALED parent" }
if (-not (Test-Path $ParentAudit)) { throw "Missing R3.17 sealed audit" }
$S = Get-Content $ParentSeal -Raw | ConvertFrom-Json
$A = Get-Content $ParentAudit -Raw | ConvertFrom-Json
if ($S.verdict -ne "PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__125KA_BIOLOGY_STATE_AND_5KYR_PENDING_EXPOSURE_SEALED") { throw "R3.17 parent verdict mismatch" }
if ($A.checks -ne "123/123") { throw "R3.17 parent audit must be 123/123" }

Write-Host "PASS_R318_SEAL_GATE_PATCH_FILES_VERIFIED: 5/5"
Write-Host "Canonical evidence: envelope + integral bundle + summary SHA verified"
Write-Host "Parent boundary: R3.17 SEALED 120 ka environment / 125 ka biology (123/123)"
Write-Host "Independent R3.18 exposure replay seal: ENABLED"
Write-Host "Scientific changes: NONE"
Write-Host "Biology/transport cadence changes: NONE"
Write-Host "Next: .\run_v0_6D1_R3_18_sealed_checks.ps1"
