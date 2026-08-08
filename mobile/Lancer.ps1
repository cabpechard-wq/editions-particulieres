$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  $portable = Join-Path $PSScriptRoot "..\.tools\node-v22.14.0-win-x64"
  if (Test-Path (Join-Path $portable "npm.cmd")) {
    $env:Path = "$portable;$env:Path"
  } else {
    Write-Error "Node.js introuvable. Installe Node 20+ ou place un binaire dans .tools/node-v22.14.0-win-x64."
  }
}

if (-not (Test-Path (Join-Path $PSScriptRoot "node_modules"))) {
  npm install
}

npm run sync-data
npm start @args
