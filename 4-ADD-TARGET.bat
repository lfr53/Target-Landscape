@echo off
REM Double-click launcher. Builds one or more targets into the curated library.
REM
REM The window is held open at the end on purpose. If PowerShell dies before
REM it can print anything - a blocked script, antivirus, a parse error - the
REM window would otherwise vanish and take the reason with it.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows_add_target.ps1"
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo [PowerShell exited with code %RC%]
if not exist "%~dp0scripts\windows_add_target.ps1" echo [missing file: scripts\windows_add_target.ps1]
pause
