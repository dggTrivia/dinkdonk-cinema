@echo off
rem Compatibility shortcut: one bridge now handles both captures.
call "%~dp0start-obs-bridge.bat" %*
exit /b %errorlevel%
