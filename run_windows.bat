@echo off
title Le Schema - School ERP
echo ================================
echo   Le Schema School ERP v1.0
echo   Innover - Creer - Exceller
echo ================================
echo.
echo Starting application...

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check

REM Launch the application
echo Launching Le Schema School ERP...
python main.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
