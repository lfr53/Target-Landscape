@echo off
REM Double-click launcher. Re-runs the current rules over every target already in the curated
REM library. No network; about a second per target.
REM
REM The window is held open at the end on purpose. If PowerShell dies before
REM it can print anything - a blocked script, antivirus, a parse error - the
REM window would otherwise vanish and take the reason with it.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows_refresh_library.ps1"
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo [PowerShell exited with code %RC%]
if not exist "%~dp0scripts\windows_refresh_library.ps1" echo [missing file: scripts\windows_refresh_library.ps1]
pause
