@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo Auto-OSBC Windows Setup (following WINDOWS_SETUP.md)
echo ============================================================
echo.

REM Check if Python 3.10 is available
echo [1/4] Checking Python 3.10...
py -3.10 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10 not found
    echo Please install Python 3.10 from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('py -3.10 --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python !PYTHON_VERSION!

REM Check if UV is available
echo.
echo [2/4] Checking UV package manager...
uv --version >nul 2>&1
if errorlevel 1 (
    echo UV not found, installing...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo WARNING: UV install failed, will use pip
        set USE_UV=false
    ) else (
        echo UV installed successfully
        set USE_UV=true
    )
) else (
    for /f "tokens=*" %%i in ('uv --version 2^>^&1') do set UV_VERSION=%%i
    echo Found !UV_VERSION!
    set USE_UV=true
)

REM Create virtual environment (following WINDOWS_SETUP.md naming)
echo.
echo [3/4] Creating virtual environment venv-windows...
if exist "venv-windows" (
    echo Removing existing venv-windows...
    rmdir /s /q "venv-windows"
)

if "!USE_UV!"=="true" (
    echo Using UV to create venv...
    uv venv venv-windows --python 3.10
    if errorlevel 1 (
        echo UV venv creation failed, using standard Python
        py -3.10 -m venv venv-windows
    )
) else (
    echo Using standard Python venv...
    py -3.10 -m venv venv-windows
)

if not exist "venv-windows" (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Virtual environment created successfully

REM Install dependencies
echo.
echo [4/4] Installing dependencies...
call venv-windows\Scripts\activate.bat

if "!USE_UV!"=="true" (
    echo Installing with UV...
    uv pip install -e ".[dev]"
) else (
    echo Installing with pip...
    python -m pip install --upgrade pip
    pip install -e ".[dev]"
)

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo To activate the environment:
echo   venv-windows\Scripts\activate
echo.
echo To test the installation:
echo   python src\OSBC.py
echo.
echo To run tests:
echo   python -m pytest tests/ -v
echo.
pause