# Pipeline complet V1 (squelette — à implémenter).
# 1. setup_output_dirs
# 2. refresh extraction (matrices + registres)
# 3. flipcards
# 4. build site
# 5. export manuel + dictionnaire
# 6. sync host-repo

$ErrorActionPreference = "Stop"
$here = Split-Path $PSScriptRoot -Parent

& "$PSScriptRoot\setup_output_dirs.ps1"
# & "$PSScriptRoot\refresh_extraction.ps1"
# & "$PSScriptRoot\refresh_flipcards.ps1"
# & "$PSScriptRoot\build_site.ps1"
# & "$PSScriptRoot\sync_host_repo.ps1"

Write-Host "build_all.ps1 — squelette (étapes commentées)"
