@echo off
:: run.bat — Start the PDF Auto-Compressor
:: Double-click this file to launch the watcher in a visible terminal window.

title PDF Auto-Compressor
cd /d "%~dp0"

echo ============================================================
echo  PDF Auto-Compressor
echo ============================================================
echo.

:: Check that Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check that dependencies are installed; install them if missing
python -c "import watchdog, pypdf, PIL" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install packages. Check your internet connection.
        pause
        exit /b 1
    )
    echo.
)

echo Starting watcher... Press Ctrl+C to stop.
echo.
python watcher.py

pause
