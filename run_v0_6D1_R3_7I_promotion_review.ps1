param(
  [string]$Python = "python",
  [string]$R37HResultsZip = "",
  [string]$R37HResultsDir = "",
  [switch]$ApprovePromotion
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$args = @("scripts\review_and_seal_v0_6D1_R3_7I.py")
if ($R37HResultsZip) { $args += @("--r37h-results-zip", $R37HResultsZip) }
if ($R37HResultsDir) { $args += @("--r37h-results-dir", $R37HResultsDir) }
if ($ApprovePromotion) { $args += "--approve-promotion" }
& $Python @args
if ($LASTEXITCODE -ne 0) { throw "R3.7I promotion review/seal did not pass" }
