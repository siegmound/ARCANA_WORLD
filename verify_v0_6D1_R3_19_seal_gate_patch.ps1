$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Expected = @{
  "scripts\formal_audit_v0_6D1_R3_19_sealed.py" = "5fea980a6171ed86f791b661a13058dfe4dff405779a2e4940fc7acc5ea4b203"
  "run_v0_6D1_R3_19_sealed_checks.ps1" = "36a37fe4314b0155f1732477d7ee4ec743b2a015612b82d6edb77ef35693933e"
  "README_R3_19_SEAL_GATE.md" = "ad3a3b4acf8cddee6a5df2fb650b8059350273d9a62c51dce5389a078703d499"
  "R3_19_CANONICAL_RUN_EVIDENCE_AUDIT.md" = "d312b783422880953b98bfc2bcf799760f4b9733e573f98269b1181e08ceeac5"
  "R319_SEAL_GATE_PATCH_MANIFEST.json" = "07d3d8bc350fb8404a07eff057f0d55a4e02f6d317251a00695a93e86b5ffcf4"
}
foreach ($Rel in $Expected.Keys) {
  $P = Join-Path $Root $Rel
  if (-not (Test-Path $P)) { throw "Missing R3.19 seal-gate file: $Rel" }
  $Got = (Get-FileHash -Algorithm SHA256 $P).Hash.ToLowerInvariant()
  if ($Got -ne $Expected[$Rel]) { throw "SHA mismatch for ${Rel}: $Got != $($Expected[$Rel])" }
}
$Evidence = @{
  "local_runs\v0_6D1_R3_19\WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.json" = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
  "local_runs\v0_6D1_R3_19\WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.npz" = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
}
foreach ($Rel in $Evidence.Keys) {
  $P = Join-Path $Root $Rel
  if (-not (Test-Path $P)) { throw "Missing canonical R3.19 checkpoint evidence: $Rel" }
  $Got = (Get-FileHash -Algorithm SHA256 $P).Hash.ToLowerInvariant()
  if ($Got -ne $Evidence[$Rel]) { throw "Canonical checkpoint SHA mismatch for ${Rel}: $Got != $($Evidence[$Rel])" }
}
$SummaryPath = Join-Path $Root "local_runs\v0_6D1_R3_19\R3_19_H0_PRESENT_BIOLOGY_CLOSURE_SUMMARY.json"
if (-not (Test-Path $SummaryPath)) { throw "Missing canonical R3.19 summary" }
$Summary = Get-Content $SummaryPath -Raw | ConvertFrom-Json
if ($Summary.verdict -ne "PASS_CANONICAL_R319_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_CHECKPOINT_READY") { throw "R3.19 canonical summary verdict mismatch" }
if ($Summary.biology_steps -ne 1 -or [double]$Summary.biology_age_ma -ne 0.0) { throw "R3.19 canonical biology boundary mismatch" }
if ($Summary.constant_forcing_equivalence_bit_exact -ne $true) { throw "R3.19 constant-forcing equivalence gate not proven" }
if ([double]$Summary.exact_0ka_inaccessible_population_mass -ne 0.0) { throw "R3.19 exact 0 ka support gate not closed" }
if ($Summary.serialization_identity -ne $true) { throw "R3.19 serialization identity not proven" }
$ParentSeal = Join-Path $Root "R3_18_SEAL_SUMMARY.json"
$ParentAudit = Join-Path $Root "outputs\v0_6D1_R3_18\FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json"
if (-not (Test-Path $ParentSeal)) { throw "Missing R3.18 SEALED parent" }
if (-not (Test-Path $ParentAudit)) { throw "Missing R3.18 sealed audit" }
$S = Get-Content $ParentSeal -Raw | ConvertFrom-Json
$A = Get-Content $ParentAudit -Raw | ConvertFrom-Json
if ($S.verdict -ne "PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_READINESS_SEALED") { throw "R3.18 parent verdict mismatch" }
if ($A.checks -ne "172/172") { throw "R3.18 parent audit must be 172/172" }
$R319 = Join-Path $Root "src\arcana_worldsim\scientific_engines\r319_phase_aware_transport_closure.py"
$R38 = Join-Path $Root "src\arcana_worldsim\scientific_engines\r38_restartable_checkpoint.py"
if ((Get-FileHash -Algorithm SHA256 $R319).Hash.ToLowerInvariant() -ne "9d5ab41af8d0711f5010c029b83d5add31a02536e5994b117dd96ff8ebb8e1a8") { throw "R3.19-R2 engine authority hash mismatch" }
if ((Get-FileHash -Algorithm SHA256 $R38).Hash.ToLowerInvariant() -ne "67211772a20bd942569d7bb8cc3e8c19c6a4071e0bca8ca0cfb1fe15b5d79698") { throw "R3.8 SEALED runtime hash mismatch" }
Write-Host "PASS_R319_SEAL_GATE_PATCH_FILES_VERIFIED: 5/5"
Write-Host "Canonical checkpoint: 0 ka H0 biology SHA verified"
Write-Host "Parent boundary: R3.18 SEALED recent exposure / 125 ka biology (172/172)"
Write-Host "Phase-aware transport: 2 x 62.5 kyr"
Write-Host "Exact endpoint support reconciliation: 0 inaccessible mass"
Write-Host "Independent 125 ka -> 0 ka replay seal: ENABLED"
Write-Host "R3.8 constant-forcing bit-exact gate: REQUIRED"
Write-Host "Candidate formal audit 218/218: REQUIRED by sealed checks"
Write-Host "Scientific changes: NONE"
Write-Host "Biology/transport cadence changes: NONE"
Write-Host "Deep biological coupling: OFF"
Write-Host "Next: .\run_v0_6D1_R3_19_sealed_checks.ps1"
