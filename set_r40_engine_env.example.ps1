# Explicit WSL bindings are preferred on Windows because Python PATH discovery
# can differ from PowerShell PATH discovery.
$env:ARCANA_WSL_EXE = "C:\Windows\System32\wsl.exe"
$env:ARCANA_WSL_CONDA = "conda"

# Optional overrides. The governed default provisioning path uses WSL2 Conda environments.
# These values are only needed if you choose different environment names or native runtimes.
$env:ARCANA_NEMO_CONDA_ENV = "arcana-nemo242"
$env:ARCANA_GEONOMICS_CONDA_ENV = "arcana-geonomics-149"
$env:ARCANA_R40_R_CONDA_ENV = "arcana-r40-r"
$env:ARCANA_CDMETAPOP_CONDA_ENV = "arcana-cdmetapop-308"
$env:ARCANA_CDMETAPOP_ROOT = "$PSScriptRoot\.arcana_engines\CDMetaPOP-3.08"
$env:ARCANA_SLIM_CONDA_ENV = "arcana-slim52"

# Native-runtime alternatives remain supported:
# $env:ARCANA_NEMO_EXECUTABLE = "C:\path\nemo2.4.2.exe"
# $env:ARCANA_GEONOMICS_PYTHON = "C:\path\python.exe"
# $env:ARCANA_RSCRIPT = "C:\Program Files\R\R-4.x.y\bin\Rscript.exe"
# $env:ARCANA_CDMETAPOP_PYTHON = "C:\path\python.exe"
# $env:ARCANA_SLIM_EXECUTABLE = "C:\path\slim.exe"
# $env:ARCANA_SLIM_PYTHON = "C:\path\python.exe"
