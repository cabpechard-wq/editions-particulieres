# Pipeline local unique avant push :
#   refresh JSON -> HTML site -> flipcards -> build_site
#
# Usage :
#   .\scripts\build_all.ps1
#   .\scripts\build_all.ps1 -Limit 5          # test Notion (pull + HTML)
#   .\scripts\build_all.ps1 -SkipPull         # saute extract.pull (JSON)
#   .\scripts\build_all.ps1 -SkipHtml         # saute export_html / dico / arrets
#   .\scripts\build_all.ps1 -SkipFlipcards    # saute matrice + generateur
#   .\scripts\build_all.ps1 -SkipBuild        # s'arrete avant build_site
#   .\scripts\build_all.ps1 -OfflineFlipcards # flipcards sans rappel Notion

param(
    [int]$Limit = 0,
    [switch]$SkipPull,
    [switch]$SkipHtml,
    [switch]$SkipFlipcards,
    [switch]$SkipBuild,
    [switch]$OfflineFlipcards
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$python = if (Test-Path ".venv\Scripts\python.exe") {
    (Resolve-Path ".venv\Scripts\python.exe").Path
} else {
    "python"
}

function Step([string]$title) {
    Write-Host ""
    Write-Host "=== $title ===" -ForegroundColor Cyan
}

function Invoke-Python([string[]]$PyArgs, [string]$label) {
    Write-Host ("> $python " + ($PyArgs -join " ")) -ForegroundColor DarkGray
    & $python @PyArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Echec ($label) - code $LASTEXITCODE"
    }
}

function Invoke-Script([string]$name, [hashtable]$Params = @{}) {
    $path = Join-Path $PSScriptRoot $name
    $extra = ""
    if ($Params.Count) {
        $extra = ($Params.GetEnumerator() | ForEach-Object { "-$($_.Key) $($_.Value)" }) -join " "
    }
    Write-Host ("> .\$name $extra").TrimEnd() -ForegroundColor DarkGray
    & $path @Params
    if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        # robocopy-style merges : codes 0-7 = OK
        if ($name -like "merge_*.ps1" -and $LASTEXITCODE -lt 8) { return }
        throw "Echec ($name) - code $LASTEXITCODE"
    }
}

$started = Get-Date
Write-Host "build_all.ps1 - pipeline local (repo: $repo)"
Write-Host "Python : $python"
if ($Limit -gt 0) { Write-Host "Limit  : $Limit (pull + HTML)" -ForegroundColor Yellow }

# --- 1. Caches JSON Drive ---------------------------------------------------
if (-not $SkipPull) {
    Step "1/4 Refresh extraction (JSON -> Drive)"
    $pullParams = @{ Register = "all" }
    if ($Limit -gt 0) { $pullParams.Limit = $Limit }
    Invoke-Script "refresh_extraction.ps1" $pullParams
} else {
    Write-Host "SkipPull : extract.pull ignore" -ForegroundColor DarkYellow
}

# --- 2. HTML pedagogique ----------------------------------------------------
if (-not $SkipHtml) {
    Step "2/4 Export HTML (Cours + Dictionnaire + Arrets)"
    $htmlArgs = @()
    if ($Limit -gt 0) { $htmlArgs = @("--limit", "$Limit") }
    Invoke-Python (@("export_html.py") + $htmlArgs) "export_html"
    Invoke-Python (@("export_dictionnaire.py") + $htmlArgs) "export_dictionnaire"
    Invoke-Python (@("export_arrets.py") + $htmlArgs) "export_arrets"
} else {
    Write-Host "SkipHtml : exports HTML ignores" -ForegroundColor DarkYellow
}

# --- 3. Flipcards -----------------------------------------------------------
if (-not $SkipFlipcards) {
    Step "3/4 Flipcards (matrice + generateur)"
    if (-not $OfflineFlipcards) {
        Invoke-Python @("-m", "flipcards.export_matrice") "flipcards.export_matrice"
        $fcArgs = @("-m", "flipcards")
    } else {
        Write-Host "OfflineFlipcards : generateur sans Notion (matrice locale)" -ForegroundColor DarkYellow
        $fcArgs = @("-m", "flipcards", "--offline")
    }
    if ($Limit -gt 0) { $fcArgs += @("--limit", "$Limit") }
    Invoke-Python $fcArgs "flipcards"
} else {
    Write-Host "SkipFlipcards : flipcards ignores" -ForegroundColor DarkYellow
}

# --- 4. Assemblage site -----------------------------------------------------
if (-not $SkipBuild) {
    Step "4/4 build_site (assets + merges + gate)"
    Invoke-Script "build_site.ps1"
} else {
    Write-Host "SkipBuild : build_site ignore" -ForegroundColor DarkYellow
}

$elapsed = (Get-Date) - $started
Write-Host ""
Write-Host ("OK - termine en {0:mm\:ss}" -f $elapsed) -ForegroundColor Green
Write-Host "Suite typique : .\scripts\serve_site.ps1  puis  git push origin main"
