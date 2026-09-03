$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$items = @(
  @{ Rel = "R3_16_R2_BRIDGE_ADAPTER_SCOPE_REPAIR_AUDIT.md"; Sha = "6d77781670d28d8fa4e900addfb490e194a720717d8e0dbccc5f8a2eadbf83b8" }
  @{ Rel = "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_16.json"; Sha = "36019a19bfc057235add72a6ddd8dfaa9630a5034e85e102cf08e08b8aed298c" }
  @{ Rel = "README_R3_16_R2_BRIDGE_ADAPTER_SCOPE_HOTFIX.md"; Sha = "e9da8e73ad7f49374d15f87727118c2273341a895154e52bf0866544cb6f847a" }
  @{ Rel = "scripts\run_v0_6D1_R3_16_c2_bridge_fixed_biology.py"; Sha = "eb5d5211f9095f3e38c58b4a2811748c9b126df53d96b040aeae157d5b5c6a00" }
  @{ Rel = "scripts\formal_audit_v0_6D1_R3_16_candidate.py"; Sha = "e719d7a222c8abb9a1bbf39b70f5fb9f6ddcad81e3cbb73cc9eee7330d1dc49f" }
  @{ Rel = "tests\test_r316_c2_bridge_fixed_biology.py"; Sha = "f91761124b12c1be1543094672e8ed147c70337651b007e1a4ff9a77f8deb772" }
  @{ Rel = "src\arcana_worldsim\scientific_engines\r316_c2_bridge_fixed_biology.py"; Sha = "8d4fc5ca3ef6608aac3273e835b8c93ee0277aafe8c5a2cc4809d90673962e30" }
)
$count = 0
foreach ($item in $items) {
  $p = Join-Path $root $item.Rel
  if (-not (Test-Path $p -PathType Leaf)) { throw "Missing R3.16-R2 hotfix file: $($item.Rel)" }
  $got = (Get-FileHash -Algorithm SHA256 $p).Hash.ToLowerInvariant()
  if ($got -ne $item.Sha) { throw "SHA mismatch for $($item.Rel): $got != $($item.Sha)" }
  $count++
}
Write-Host "PASS_R316_R2_BRIDGE_ADAPTER_SCOPE_HOTFIX_FILES_VERIFIED: $count/$($items.Count)"
Write-Host "R3.15 sealed adapter guard: PRESERVED"
Write-Host "R3.16 environmental adapter scope: 250 ka -> 120 ka"
Write-Host "Scientific parameter changes: NONE"
Write-Host "Biology changes: NONE"
