# Crée l'arborescence de sortie sur Google Drive.
# Usage : .\scripts\setup_output_dirs.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root

if (Test-Path ".venv\Scripts\python.exe") {
    & .venv\Scripts\python.exe -c "from packages.ep_core.paths import ensure_output_dirs; ensure_output_dirs(); print('OK')"
} else {
    python -c "from packages.ep_core.paths import ensure_output_dirs; ensure_output_dirs(); print('OK')"
}

Pop-Location
