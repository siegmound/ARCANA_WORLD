param(
  [switch]$AllowNonScientificDevParent
)
$ErrorActionPreference='Stop'
$Root=(Get-Location).Path
$env:PYTHONPATH=Join-Path $Root 'src'

Write-Host '=== R5.5 source + immutable R5.4/R5.3/R5.2/R5.1/J14 candidate authority ==='
python scripts/check_v0_6D1_R5_5_source_manifest.py --root $Root
if($LASTEXITCODE -ne 0){ throw 'R5.5 source manifest failed closed.' }
$parentArgs=@('scripts/check_v0_6D1_R5_5_parent_authority.py','--root',$Root)
if($AllowNonScientificDevParent){ $parentArgs += '--allow-non-scientific-dev' }
python @parentArgs
if($LASTEXITCODE -ne 0){ throw 'R5.5 parent candidate authority failed closed.' }

Write-Host '=== R5.5 contact-history regression (project-local pytest basetemp) ==='
$PytestBase=Join-Path $Root '.pytest_tmp\r55'
if(Test-Path $PytestBase){ Remove-Item -Recurse -Force $PytestBase }
New-Item -ItemType Directory -Force -Path $PytestBase | Out-Null
python -m pytest tests/test_r55_contact_history.py -q --basetemp $PytestBase
if($LASTEXITCODE -ne 0){ throw 'R5.5 regression failed closed.' }

$Out=Join-Path $Root 'outputs\v0_6D1_R5_5'
if(Test-Path $Out){
  $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $dst=Join-Path $Root "outputs\v0_6D1_R5_5_attempt_$stamp"
  Move-Item $Out $dst; Write-Host "Preserved prior R5.5 attempt: $dst"
}
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Write-Host '=== R5.5 ARCANA-native contact-zone + gene-flow history consolidation ==='
$run=@('scripts/run_v0_6D1_R5_5.py','--root',$Root)
if($AllowNonScientificDevParent){ $run += '--allow-non-scientific-dev-parent' }
python @run
if($LASTEXITCODE -ne 0){ throw 'R5.5 contact-history consolidation failed closed.' }
Write-Host 'PASS_R55_CONTACT_ZONE_AND_GENE_FLOW_HISTORY_CONSOLIDATION_CANDIDATE_RUN'
Write-Host 'PASS_R55_INTEGRATED_CONTACT_HISTORY_CANDIDATE_RUN'
Write-Host 'R5.5 remains CANDIDATE by design; no micro-seal is created at this stage.'
