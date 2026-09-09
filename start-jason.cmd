@echo off
setlocal
set "WEBOT_APP_HOME=%~dp0"
if not exist "%~dp0dist\webot.exe" (
  echo Build dist\webot.exe before starting Jason AI.
  exit /b 1
)
start "" "%~dp0dist\webot.exe"
endlocal
