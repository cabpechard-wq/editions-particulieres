$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$commerce = Join-Path $repo "site\commerce"
$config = Join-Path $commerce "config.json"
$example = Join-Path $commerce "config.json.example"

if (-not (Test-Path $config) -and (Test-Path $example)) {
    Copy-Item $example $config
    Write-Host "config.json créé depuis config.json.example"
}

Push-Location $commerce
try {
    python build_assets.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "Site généré : site\commerce\dist\site"
