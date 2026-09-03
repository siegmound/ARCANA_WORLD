$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
    $env:ARCANA_PROJECT_ROOT = $Root
    $Python = $null
    if (Test-Path ".\.venv\Scripts\python.exe") {
        $Python = ".\.venv\Scripts\python.exe"
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $Python = "python"
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $Python = "py"
    } else {
        throw "No Python interpreter found (.venv, python, or py)."
    }

    & $Python ".\tools\r4_32_r1_geonomics_static_validation_diagnostic.py"
    if ($LASTEXITCODE -ne 0) {
        throw "R4.32-R1 diagnostic failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
