@echo off
setlocal
title Cinema bridge - Firefox and mpv (:18790)
cd /d "%~dp0"
set "CINEMA_NODE="
for /f "delims=" %%N in ('where.exe node.exe 2^>nul') do if not defined CINEMA_NODE set "CINEMA_NODE=%%N"
if not defined CINEMA_NODE if exist "%ProgramFiles%\nodejs\node.exe" set "CINEMA_NODE=%ProgramFiles%\nodejs\node.exe"
if not defined CINEMA_NODE if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" set "CINEMA_NODE=%LOCALAPPDATA%\Programs\nodejs\node.exe"
if not defined CINEMA_NODE if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" set "CINEMA_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if not defined CINEMA_NODE (
  echo Node.js could not be found. Install Node 22 or newer from https://nodejs.org/
  pause
  exit /b 1
)
if /i "%~1"=="--check-runtime" (
  "%CINEMA_NODE%" --version
  exit /b
)
"%CINEMA_NODE%" obs-bridge.js
pause
