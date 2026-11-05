@echo off
rem Starts what the DinkDonk Cinema screens need, each in its own window: the chat relay, the screens server and the
rem OBS film-screen bridge. Anything already running is left alone, so running this twice is harmless.
title DinkDonk Cinema start-up
cd /d "%~dp0"

where node >nul 2>nul || (echo Node.js is not installed. Get the LTS version from https://nodejs.org/ & pause & exit /b 1)
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 22 ? 0 : 1)" || (
  echo Node.js 22 or newer is needed. Update it from https://nodejs.org/
  pause & exit /b 1
)

call :listening 18765 && (echo Chat relay       already running) || (
  echo Chat relay       starting
  start "Chat relay (:18765)" /d "%~dp0chat-relay" start-windows.bat
)
call :listening 18770 && (echo Screens server   already running) || (
  echo Screens server   starting
  start "Cinema screens (:18770)" /d "%~dp0screens" cmd /c "node standby-server.js & pause"
)
call :listening 18790 && (echo OBS bridge       already running) || (
  echo OBS bridge       starting
  start "OBS bridge (:18790)" /d "%~dp0screens" cmd /c "node obs-bridge.js & pause"
)

timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:18770/control.html"
echo.
echo Control panel opened in your browser. Leave the three windows open while you stream.
echo First time? See README.txt for the OBS part.
timeout /t 10 >nul
exit /b 0

:listening
netstat -ano | findstr /r /c:":%1 .*LISTENING" >nul
exit /b %errorlevel%
