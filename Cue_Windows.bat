@echo off
@REM Launches for Widnows!
setlocal enabledelayedexpansion
set "DIR=%~dp0"
set "VENV=%DIR%Env"
set "PY=%VENV%\Scripts\python.exe"
set "ENV_FILE=%DIR%.env"

REM ── Extract bundled venv if needed ──
if not exist "%VENV%" if exist "%DIR%Env.zip" (
    echo [Setup] Extracting environment...
    powershell -NoProfile -Command "Expand-Archive -Path '%DIR%Env.zip' -DestinationPath '%DIR%' -Force"
    echo [Setup] Done.
)

REM ── API Key validation loop ──
:validate_loop
set "CUR_KEY="
if exist "%ENV_FILE%" (
    for /f "tokens=1,* delims==" %%A in ('findstr /C:"OPENROUTER_API_KEY=" "%ENV_FILE%"') do set "CUR_KEY=%%B"
)

set "STATUS=INVALID"
if not "!CUR_KEY!"=="" (
    for /f %%S in ('"%PY%" "%DIR%test_api_key.py" "!CUR_KEY!" 2^>nul') do set "STATUS=%%S"
)

if not "!STATUS!"=="VALID" (
    echo.
    echo ====================================
    echo   OpenRouter API Key Required/Invalid
    echo ====================================
    set /p API_KEY="Paste your OpenRouter API key: "
    echo Validating...
    set "STATUS="
    for /f %%S in ('"%PY%" "%DIR%test_api_key.py" "!API_KEY!" 2^>nul') do set "STATUS=%%S"

    if "!STATUS!"=="VALID" (
        (
            echo # CUE Configuration — Auto-generated
            echo # DO NOT share this file or commit it to version control!
            echo OPENROUTER_API_KEY=!API_KEY!
        ) > "%ENV_FILE%"
        echo [OK] API key validated and saved.
    ) else (
        echo [Error] Key rejected ^(!STATUS!^). Try again.
        goto validate_loop
    )
)

REM ── Mode Selection ──
echo.
echo ====================================
echo         Select Mode
echo ====================================
echo   1) CLI  — Terminal interface
echo   2) GUI  — Graphical interface
echo ====================================
set /p MODE="Choice [1/2]: "

if "%MODE%"=="2" (
    "%PY%" "%DIR%handler.py" gui
) else (
    "%PY%" "%DIR%handler.py" cli
)
endlocal