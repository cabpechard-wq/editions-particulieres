$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$distSite = Join-Path $repo "site\dist\site"
$arretsDst = Join-Path $distSite "arrets"

$exportSite = $null
try {
    $exportSite = python -c "from packages.ep_core.paths import resolve_path; print(resolve_path('export_site'))"
} catch {
    Write-Host "merge_arrets_site : config/paths.json introuvable, ignoré."
    exit 0
}

$arretsSrc = Join-Path $exportSite "arrets"
if (-not (Test-Path $arretsSrc)) {
    Write-Host "Pas d'arrêts exportés : $arretsSrc (lancez l'export HTML Jurisprudence dans la GUI)"
    exit 0
}

python (Join-Path $PSScriptRoot "fix_legacy_crumbs.py") $arretsSrc
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path $distSite)) {
    Write-Error "Build site manquant : lancez scripts\build_site.ps1 d'abord."
}

if (Test-Path $arretsDst) {
    Remove-Item $arretsDst -Recurse -Force
}

robocopy $arretsSrc $arretsDst /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null
if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }

Write-Host "Arrêts intégrés : $arretsSrc -> $arretsDst"
Write-Host "URL : /editions-particulieres/arrets/"
