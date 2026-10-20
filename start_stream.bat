@echo off
title Real-Time Live Camera Streamer
cd /d "%~dp0"
echo Starting the camera streamer... (Ctrl+C stops it)
echo.
python "%~dp0streamer.py"
echo.
echo Streamer stopped. Check streamer.log for details.
pause
