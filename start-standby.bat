@echo off
title Standby screens (127.0.0.1:18770)
cd /d "%~dp0"
where node >nul 2>nul || (echo Node.js is not installed: https://nodejs.org/ & pause & exit /b 1)
node standby-server.js
pause
