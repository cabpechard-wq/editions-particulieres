$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$root = Join-Path $repo "site\templates"
$port = 8777

Write-Host "Serveur local : http://localhost:$port/design-proposals/themes/"
Write-Host "Ctrl+C pour arrêter."
Push-Location $root
try {
    python -m http.server $port
} finally {
    Pop-Location
}
