@echo off
REM Double-click launcher. The real work is in scripts\windows_setup.ps1 —
REM PowerShell is used because batch has no Tee-Object, and the whole point of
REM this file is that the user sees progress AND gets a log to send back.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows_setup.ps1"
