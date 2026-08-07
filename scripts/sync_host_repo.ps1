$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repo "site\commerce\dist\site"
$dst = Join-Path $repo "site\commerce\host-repo"

if (-not (Test-Path $src)) {
    Write-Error "Build manquant : lancez scripts\build_site.ps1 d'abord."
}

# Conserve .github/ et .gitkeep ; remplace le reste du contenu publié
Get-ChildItem $dst -Force | Where-Object {
    $_.Name -notin @(".git", ".github", ".gitkeep")
} | Remove-Item -Recurse -Force

robocopy $src $dst /E /XD .git .github /NFL /NDL /NJH /NJS /NC /NS | Out-Null
if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }

Write-Host "Synchronisé : $src -> $dst"
Write-Host "Publier : cd site\commerce\host-repo && git add -A && git commit && git push"
