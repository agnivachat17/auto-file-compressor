@echo off
:: stop.bat — Kill the silent background watcher (run_silent.pyw)
echo Stopping PDF Auto-Compressor background process...
taskkill /F /IM pythonw.exe /T >nul 2>&1
if errorlevel 1 (
    echo No background watcher process was found.
) else (
    echo Done. Watcher stopped.
)
pause
