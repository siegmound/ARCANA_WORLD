$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $Root "PATCH_MANIFEST_v0_6D1_R3_13_OVER_R3_12.json"
$Manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$Ok = 0
foreach ($f in $Manifest.files) {
  $p = Join-Path $Root ($f.path -replace '/', '\')
  if (!(Test-Path $p)) { throw "Missing R3.13 patch file: $($f.path)" }
  $h = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
  if ($h -ne $f.sha256) { throw "SHA256 mismatch: $($f.path)" }
  $Ok++
}
$Seal = Join-Path $Root "R3_12_SEAL_SUMMARY.json"
$CkJ = Join-Path $Root "local_runs\v0_6D1_R3_12\WORLD1_H0_46Ma_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_v0_6D1_R3_12.json"
$CkN = Join-Path $Root "local_runs\v0_6D1_R3_12\WORLD1_H0_46Ma_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_v0_6D1_R3_12.npz"
if (!(Test-Path $Seal)) { throw "Missing R3.12 seal summary" }
if (!(Test-Path $CkJ) -or !(Test-Path $CkN)) { throw "Missing R3.12 canonical 46 Ma checkpoint" }
$SealObj = Get-Content $Seal -Raw | ConvertFrom-Json
if ($SealObj.verdict -ne "PASS_R312_CANONICAL_POST_CHA1_61_TO_46_H0_DIVERSITY_RECOVERY__46MA_RESTART_BOUNDARY_SEALED") { throw "R3.12 seal verdict mismatch" }
$hj = (Get-FileHash -Algorithm SHA256 $CkJ).Hash.ToLowerInvariant()
$hn = (Get-FileHash -Algorithm SHA256 $CkN).Hash.ToLowerInvariant()
if ($hj -ne $Manifest.parent_checkpoint_json_sha256) { throw "R3.12 JSON checkpoint hash mismatch" }
if ($hn -ne $Manifest.parent_checkpoint_npz_sha256) { throw "R3.12 NPZ checkpoint hash mismatch" }
Write-Host "PASS_R313_PATCH_FILES_VERIFIED: $Ok/$($Manifest.payload_file_count)"
Write-Host "Parent boundary: R3.12 SEALED 46.0 Ma verified"
Write-Host "Then run: .\run_v0_6D1_R3_13_checks.ps1"
Write-Host "Then run: .\run_v0_6D1_R3_13_longterm_reassembly.ps1"
