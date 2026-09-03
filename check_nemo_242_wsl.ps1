$ErrorActionPreference = "Stop"
Write-Host "Checking NEMO 2.4.2 inside WSL2..."
$probe = wsl.exe bash -lc "command -v nemo2.4.2 || true; nemo2.4.2 2>&1 | head -n 8 || true"
$probe | Write-Host
if ($probe -notmatch "2\.4\.2") {
    Write-Error "NEMO 2.4.2 was not confirmed. Inside WSL2 install with: conda create -n nemo -c conda-forge -c ecoevo nemo"
    exit 2
}
Write-Host "PASS_NEMO_2_4_2_WSL_PREFLIGHT"
