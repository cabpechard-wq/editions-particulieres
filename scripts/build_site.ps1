$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$site = Join-Path $repo "site"
$config = Join-Path $site "config.json"
$example = Join-Path $site "config.json.example"

if (-not (Test-Path $config) -and (Test-Path $example)) {
    Copy-Item $example $config
    Write-Host "config.json créé depuis config.json.example"
}

Push-Location $site
try {
    python build_assets.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "Site généré : site\dist\site"

& (Join-Path $PSScriptRoot "merge_manuel_site.ps1")
if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }

& (Join-Path $PSScriptRoot "merge_dictionnaire_site.ps1")
if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }

& (Join-Path $PSScriptRoot "merge_arrets_site.ps1")
if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }

Push-Location $site
try {
    python build_membre_gate.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
