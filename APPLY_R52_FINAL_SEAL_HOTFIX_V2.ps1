$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $Root '_r52_hotfix_payload'

$Targets = @(
    @{
        Source = Join-Path $Payload 'r52_seal.py'
        Target = Join-Path $Root 'src\arcana_worldsim\state_query\r52_seal.py'
        Sha256 = '1d40e2b8868e99448969186c2bfcbae284910f809b6fab1f15166e7759e1031f'
    },
    @{
        Source = Join-Path $Payload 'test_r52_final_seal.py'
        Target = Join-Path $Root 'tests\test_r52_final_seal.py'
        Sha256 = 'ba0bb5571156fe3819f6c2ca2446d0ec3ff9665ba7e22936d8ade0b9ec4f3a11'
    },
    @{
        Source = Join-Path $Payload 'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_2.json'
        Target = Join-Path $Root 'SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_2.json'
        Sha256 = 'c4166640110d331b55308120108bd48f144691337eae53cd2c3526cea9381a31'
    }
)

Write-Host '=== R5.2 final-seal hotfix V2: forced overwrite ==='
foreach ($item in $Targets) {
    if (-not (Test-Path -LiteralPath $item.Source)) {
        throw "Missing payload file: $($item.Source)"
    }
    $parent = Split-Path -Parent $item.Target
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $item.Source -Destination $item.Target -Force
    $actual = (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $item.Sha256) {
        throw "SHA256 mismatch after overwrite: $($item.Target) expected=$($item.Sha256) actual=$actual"
    }
    Write-Host "PASS $($item.Target) $actual"
}

$sealPath = Join-Path $Root 'src\arcana_worldsim\state_query\r52_seal.py'
$text = Get-Content -LiteralPath $sealPath -Raw
if ($text -notmatch 'EXPECTED_R51_FINAL_SEAL_SHA256') {
    throw 'Correct R5.1 final-seal constant is still absent after overwrite.'
}
if ($text -match 'EXPECTED_R51_SEAL_SHA(?!256)') {
    throw 'Legacy EXPECTED_R51_SEAL_SHA reference is still present after overwrite.'
}

$line263 = (Get-Content -LiteralPath $sealPath)[262]
Write-Host '=== Verification ==='
Write-Host "r52_seal.py line 263: $line263"
Write-Host 'Expected symbol: EXPECTED_R51_FINAL_SEAL_SHA256'
Write-Host 'HOTFIX_R52_FINAL_SEAL_AUTHORITY_CONSTANTS_V2_APPLIED'
Write-Host ''
Write-Host 'Now run:'
Write-Host '  .\run_v0_6D1_R5_2.ps1 -SealOnly'
