@echo off
title Stop Camera Stream
echo Stopping the camera streamer...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'streamer\.py' -or $_.CommandLine -match '8554/camera' } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }"
echo [OK] Camera stream stopped (autostart stays installed).
timeout /t 2 >nul
