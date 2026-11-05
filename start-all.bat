@echo off
rem Starts everything the DINK DONK screens need, each in its own window. Anything already running is left alone,
rem so running this twice is harmless. VLC (the movie) is still yours to open.
title DINK DONK start-up
cd /d "%~dp0"
where node >nul 2>nul || (echo Node.js is not installed: https://nodejs.org/ & pause & exit /b 1)

call :listening 18765 && (echo Chat relay          already running) || (
  echo Chat relay          starting
  start "Chat relay (:18765)" /d "%USERPROFILE%\Desktop\customchat\destinygg-obs-overlay" start-windows.bat
)
call :listening 18770 && (echo Standby server      already running) || (
  echo Standby server      starting
  start "Standby screens (:18770)" /d "%~dp0" start-standby.bat
)
call :listening 18790 && (echo OBS bridge          already running) || (
  echo OBS bridge          starting
  start "OBS bridge (:18790)" /d "%~dp0" start-obs-bridge.bat
)
tasklist /fi "imagename eq obs64.exe" | findstr /i "obs64.exe" >nul && (
  echo OBS                 already running - check the scene collection is "Moobies 1440p poll"
) || (
  echo OBS                 starting with "Moobies 1440p poll"
  start "" /d "C:\Program Files\obs-studio\bin\64bit" obs64.exe --profile "Angelthump h264 1440p" --collection "Moobies 1440p poll"
)

rem give the standby server a moment before opening its control panel
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:18770/control.html"
echo.
echo Control panel opened. Pick Auditorium and check the director is on.
echo Phones/tablets only: node lan-proxy.js   (not needed for OBS)
timeout /t 8 >nul
exit /b 0

:listening
netstat -ano | findstr /r /c:":%1 .*LISTENING" >nul
exit /b %errorlevel%
