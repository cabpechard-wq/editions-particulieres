$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$root = Join-Path $repo "site\dist\site"

if (-not (Test-Path (Join-Path $root "index.html"))) {
    Write-Error "Build manquant : lancez .\scripts\build_site.ps1 d'abord."
}

function Test-PortFree([int]$Port) {
    $used = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return -not $used
}

$port = 8080
if (-not (Test-PortFree $port)) {
    Write-Host "Port $port occupé — essai sur 8081…" -ForegroundColor Yellow
    $port = 8081
    if (-not (Test-PortFree $port)) {
        Write-Error "Ports 8080 et 8081 occupés. Fermez l'autre serveur (Ctrl+C dans son terminal) puis relancez."
    }
}

$lan = $null
try {
    $lan = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
        Select-Object -ExpandProperty IPAddress -First 1
} catch {
    $lan = (ipconfig | Select-String "IPv4" | Select-Object -First 1) -replace ".*:\s*", ""
}

$url = "http://127.0.0.1:$port/"
$fiche = "http://127.0.0.1:$port/arrets/ce-1822-laffitte/"

Write-Host ""
Write-Host "=== Serveur local ===" -ForegroundColor Cyan
Write-Host "Laissez CE terminal ouvert tant que vous testez."
Write-Host "Ne lancez pas build_site.ps1 pendant que le serveur tourne."
Write-Host ""
Write-Host "Accueil : $url"
Write-Host "Fiche TTS : $fiche"
if ($lan) { Write-Host "Réseau  : http://${lan}:$port/" }
Write-Host ""
Write-Host "Utilisez 127.0.0.1 (pas localhost) si le navigateur bloque localhost."
Write-Host "Ctrl+C pour arrêter."
Write-Host ""

if (-not (Test-Path (Join-Path $root "arrets\index.html"))) {
    Write-Host "Attention : dossier arrets absent — lancez python export_arrets.py --out site/dist/site" -ForegroundColor Yellow
}

try {
    Start-Process $url
} catch {
    # ouverture navigateur optionnelle
}

Push-Location $root
try {
    python -m http.server $port --bind 127.0.0.1
} finally {
    Pop-Location
}
