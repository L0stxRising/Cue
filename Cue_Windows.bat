@echo off
@REM Launches for Windows!
setlocal enabledelayedexpansion
set "DIR=%~dp0"
set "VENV=%DIR%Env"
set "PY=%VENV%\Scripts\python.exe"
set "ENV_FILE=%DIR%.env"

REM ── Dynamic Environment Creation / Repair ──
if not exist "%PY%" (
    if exist "%VENV%" (
        echo [Setup] Existing environment appears broken or incomplete. Rebuilding...
        rmdir /s /q "%VENV%"
    ) else (
        echo [Setup] Creating Python virtual environment...
    )

    python --version >nul 2>&1
    if errorlevel 1 (
        echo [Error] Python is not installed or not in your PATH. Please install Python 3.10 or newer.
        pause
        exit /b 1
    )

    python -m venv "%VENV%"
    if not exist "%PY%" (
        echo [Error] Failed to create virtual environment.
        pause
        exit /b 1
    )

    if exist "%DIR%requirements.txt" (
        echo [Setup] Installing dependencies from requirements.txt...
        "%PY%" -m pip install --upgrade pip -q
        "%PY%" -m pip install -r "%DIR%requirements.txt" -q
        if errorlevel 1 (
            echo [Error] Dependency installation failed.
            pause
            exit /b 1
        )
        echo [Setup] Environment setup complete.
    ) else (
        echo [Error] requirements.txt not found! Expected at %DIR%requirements.txt
        pause
        exit /b 1
    )
)

if not exist "%PY%" (
    echo [Error] Python not found at %PY%. Environment creation may have failed.
    pause
    exit /b 1
)
REM ───────────────────────────────────────

if not exist "%DIR%tmp" mkdir "%DIR%tmp"
if not exist "%DIR%Output" mkdir "%DIR%Output"

REM ── API Key validation loop ──
:validate_loop
set "CUR_KEY="
if exist "%ENV_FILE%" (
    for /f "tokens=1,* delims==" %%A in ('findstr /C:"OPENROUTER_API_KEY=" "%ENV_FILE%"') do set "CUR_KEY=%%B"
)

set "STATUS=INVALID"
if not "!CUR_KEY!"=="" (
    for /f "usebackq delims=" %%S in (`""%PY%" "%DIR%test_api_key.py" "!CUR_KEY!""`) do set "STATUS=%%S"
)

if not "!STATUS:~0,5!"=="VALID" (
    echo.
    echo ====================================
    echo   OpenRouter API Key Required/Invalid
    echo ====================================
    set "API_KEY="
    set /p API_KEY="Paste your OpenRouter API key (or Q to quit): "
    if /i "!API_KEY!"=="Q" (
        echo Exiting.
        exit /b 0
    )
    if "!API_KEY!"=="" goto validate_loop

    echo Validating...
    set "STATUS="
    for /f "usebackq delims=" %%S in (`""%PY%" "%DIR%test_api_key.py" "!API_KEY!""`) do set "STATUS=%%S"

    if "!STATUS:~0,5!"=="VALID" (
        echo # CUE Configuration - Auto-generated> "%ENV_FILE%"
        echo # DO NOT share this file or commit it to version control!>> "%ENV_FILE%"
        echo OPENROUTER_API_KEY=!API_KEY!>> "%ENV_FILE%"
        echo [OK] API key validated and saved.
    ) else (
        echo [Error] Key rejected ^(!STATUS!^). Try again.
        goto validate_loop
    )
)

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