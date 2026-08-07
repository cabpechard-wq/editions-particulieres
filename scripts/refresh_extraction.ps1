# Refresh extraction Notion → JSON (Google Drive)
# Usage : .\scripts\refresh_extraction.ps1
#         .\scripts\refresh_extraction.ps1 -Limit 5

param(
    [string]$Register = "all",
    [int]$Limit = 0
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root

$python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
$args = @("-m", "extract", $Register)
if ($Limit -gt 0) { $args += @("--limit", "$Limit") }

& $python @args
$code = $LASTEXITCODE
Pop-Location
exit $code
