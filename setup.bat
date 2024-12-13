@echo off

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in the PATH.
    pause
    exit /b 1
)

python setup.py build
if errorlevel 1 (
    echo Build failed. Check for errors in setup.py.
    exit /b 1
)

exit /b 0
