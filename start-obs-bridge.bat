@echo off
title OBS bridge - film screen (:18790)
cd /d "%~dp0"
where node >nul 2>nul || (echo Node.js is not installed: https://nodejs.org/ & pause & exit /b 1)
node obs-bridge.js
pause
