@echo off
setlocal
set "DIR=%~dp0"
set "VENV=%DIR%Env"
set "PY=%VENV%\Scripts\python.exe"
set "ENV_FILE=%DIR%.env"

findstr /C:"OPENROUTER_API_KEY=" "%ENV_FILE%" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ====================================
    echo   OpenRouter API Key Required
    echo ====================================
    set /p API_KEY="Paste your OpenRouter API key: "
    (
        echo # CUE Configuration — Auto-generated
        echo # DO NOT share this file or commit it to version control!
        echo OPENROUTER_API_KEY=%API_KEY%
    ) > "%ENV_FILE%"
    echo [OK] API key saved to .env
)

echo.
echo ====================================
echo         Select Mode
echo ====================================
echo   1^) CLI  — Terminal interface
echo   2^) GUI  — Graphical interface
echo ====================================
set /p MODE="Choice [1/2]: "

if "%MODE%"=="2" (
    "%PY%" "%DIR%handler.py" gui
) else (
    "%PY%" "%DIR%handler.py" cli
)
endlocal