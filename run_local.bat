@echo off
title HARIS Biometric Core - Local Web Server
echo ========================================================
echo Starting HARIS Biometric & QR System directly...
echo ========================================================
python3.10 web_app.py
if %ERRORLEVEL% NEQ 0 (
    python web_app.py
)
pause
