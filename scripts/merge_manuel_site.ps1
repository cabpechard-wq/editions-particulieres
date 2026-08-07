$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$distSite = Join-Path $repo "site\dist\site"
$manuelDst = Join-Path $distSite "manuel"

# Source : export GUI/HTML → export/site/manuel (Google Drive)
$exportSite = $null
try {
    $exportSite = python -c "from packages.ep_core.paths import resolve_path; print(resolve_path('export_site'))"
} catch {
    Write-Host "merge_manuel_site : config/paths.json introuvable, ignoré."
    exit 0
}

$manuelSrc = Join-Path $exportSite "manuel"
if (-not (Test-Path $manuelSrc)) {
    Write-Host "Pas de manuel exporté : $manuelSrc (lancez l'export HTML Manuel dans la GUI)"
    exit 0
}

if (-not (Test-Path $distSite)) {
    Write-Error "Build site manquant : lancez scripts\build_site.ps1 d'abord."
}

if (Test-Path $manuelDst) {
    Remove-Item $manuelDst -Recurse -Force
}

robocopy $manuelSrc $manuelDst /E /NFL /NDL /NJH /NJS /NC /NS | Out-Null
if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }

Write-Host "Manuel intégré : $manuelSrc -> $manuelDst"
Write-Host "URL : /editions-particulieres/manuel/"
