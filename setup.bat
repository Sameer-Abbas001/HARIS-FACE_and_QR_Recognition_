@echo off
echo ========================================================
echo Installing HARIS Dependencies
echo ========================================================
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Dependencies installed successfully!
echo To run the web dashboard:
echo    python web_app.py
echo.
pause
