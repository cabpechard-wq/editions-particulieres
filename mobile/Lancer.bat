@echo off
setlocal
set "NODE_DIR=%~dp0..\.\tools\node-v22.14.0-win-x64"
if not exist "%NODE_DIR%\npm.cmd" (
  echo Node introuvable dans %NODE_DIR%
  echo Telecharge Node LTS ou ajoute npm au PATH.
  exit /b 1
)
set "PATH=%NODE_DIR%;%PATH%"
cd /d "%~dp0"
call npm run sync-data
call npm start %*
