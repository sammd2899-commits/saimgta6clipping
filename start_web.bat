@echo off
setlocal enabledelayedexpansion

:: Ensure execution from repository root directory
cd /d "%~dp0"

title SaimClip Studio — Local Web Launcher

echo ===============================================================================
echo                SAIMCLIP STUDIO — 1-CLICK LOCAL LAUNCHER
echo ===============================================================================
echo.

:: 1. Detect Python executable
set "PY_CMD=python"
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set "PY_CMD=py"
    ) else (
        echo [ERROR] Python 3.10+ was not found in PATH.
        echo Please install Python from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

:: Run fast bootstrap check (installs only missing dependencies, no bloat)
echo [1/3] Verifying environment ^& dependencies...
%PY_CMD% scripts\bootstrap.py
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Bootstrap encountered a non-critical check warning. Proceeding...
)

:: 2. Check if web\dist\index.html exists; build if missing
echo.
echo [2/3] Checking SaimClip Studio frontend bundle...
if not exist "web\dist\index.html" (
    echo [INFO] web\dist\index.html not found. Building production bundle...
    where npm >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        cd web
        call npm install --legacy-peer-deps
        call npm run build
        cd /d "%~dp0"
    ) else (
        echo [WARNING] npm not found in PATH. Frontend will run in server mode.
    )
) else (
    echo   [OK] Production web bundle ready in web\dist\.
)

:: 3. Launch browser after 2-second delay and run FastAPI server on 127.0.0.1:8765
echo.
echo [3/3] Starting local FastAPI server on http://127.0.0.1:8765...
echo Opening SaimClip Studio in your default browser...
start "" cmd /c "ping 127.0.0.1 -n 3 >nul && start http://127.0.0.1:8765"

%PY_CMD% -m uvicorn server:app --host 127.0.0.1 --port 8765
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Server terminated unexpectedly.
    pause
)
