param(
  [string]$Python = "python",
  [double]$EndAgeMa = 150.0,
  [switch]$DiagnosticSmoke,
  [string]$Seal = ""
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$args = @("scripts\run_v0_6D1_R3_7I_canonical_runtime.py", "--end-age-ma", $EndAgeMa)
if ($DiagnosticSmoke) { $args += "--diagnostic-smoke" }
if ($Seal) { $args += @("--seal", $Seal) }
& $Python @args
if ($LASTEXITCODE -ne 0) { throw "R3.7I canonical runtime failed" }
