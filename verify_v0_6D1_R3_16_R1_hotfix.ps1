$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$expected = @{
  "R3_16_R1_WINDOWS_BASETEMP_REPAIR_AUDIT.md" = "9a277fc5c3de60ca610c064dfb895ee2401ede16339427e8a17f12155b8f22fe"
  "README_R3_16_R1_WINDOWS_BASETEMP_HOTFIX.md" = "ecea258a86ecd804c77be85020f1dc39a7abeee256ec936e71fb74b920b2c333"
  "run_v0_6D1_R3_16_checks.ps1" = "1d36a4051c776c1b109195d40d9e0a5da0bcef41577ba9d8f08ffb4b02fb03ea"
}
foreach ($rel in $expected.Keys) {
  $p = Join-Path $root $rel
  if (-not (Test-Path $p)) { throw "Missing hotfix file: $rel" }
  $got = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
  if ($got -ne $expected[$rel]) { throw "SHA256 mismatch: $rel`nexpected=$($expected[$rel])`ngot=$got" }
}
Write-Host "PASS_R316_R1_WINDOWS_BASETEMP_HOTFIX_FILES_VERIFIED: $($expected.Count)/$($expected.Count)"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology changes: NONE"
Write-Host "Repair: pytest nested basetemp parent is explicitly materialized"
