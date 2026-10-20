@echo off
title Camera Stream - Auto-Start Setup
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_autostart.ps1"
echo.
pause
