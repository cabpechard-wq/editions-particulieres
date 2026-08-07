$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$distSite = Join-Path $repo "site\dist\site"
$dictDst = Join-Path $distSite "dictionnaire"

$exportSite = $null
try {
    $exportSite = python -c "from packages.ep_core.paths import resolve_path; print(resolve_path('export_site'))"
} catch {
    Write-Host "merge_dictionnaire_site : config/paths.json introuvable, ignoré."
    exit 0
}

$dictSrc = Join-Path $exportSite "dictionnaire"
if (-not (Test-Path $dictSrc)) {
    Write-Host "Pas de dictionnaire exporté : $dictSrc (lancez l'export HTML Glossaire dans la GUI)"
    exit 0
}

python (Join-Path $PSScriptRoot "fix_legacy_crumbs.py") $dictSrc
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path $distSite)) {
    Write-Error "Build site manquant : lancez scripts\build_site.ps1 d'abord."
}

if (Test-Path $dictDst) {
    Remove-Item $dictDst -Recurse -Force
}

robocopy $dictSrc $dictDst /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null
if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }

Write-Host "Dictionnaire intégré : $dictSrc -> $dictDst"
Write-Host "URL : /editions-particulieres/dictionnaire/"
