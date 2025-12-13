@echo off
REM Auto-OSBC Installation Script for Windows 10/11
REM Usage: install-windows.bat

echo 🚀 Auto-OSBC Windows Installation
echo ==================================

REM Check Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo 🖥️ Windows Version: %VERSION%

REM Basic Windows 10/11 check (simplified)
if "%VERSION%" LSS "10.0" (
    echo ❌ Windows 10 or later required
    echo Current version: %VERSION%
    pause
    exit /b 1
)
echo ✅ Windows version supported

REM Check Python version
echo 🐍 Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found in PATH
    echo Please install Python 3.10+ from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version and check if it's 3.10+
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Extract major.minor version (simplified check)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3.10+ required
    echo Found: %PYTHON_VERSION%
    echo Please install Python 3.10+ from https://python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python version compatible

REM Create virtual environment
echo 🔨 Creating virtual environment...
if exist "venv" (
    echo 📁 Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

REM Activate virtual environment and install dependencies
echo 📦 Installing Auto-OSBC dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip first
python -m pip install --upgrade pip

REM Install the package
pip install -e .
if errorlevel 1 (
    echo ❌ Failed to install core dependencies
    pause
    exit /b 1
)

REM Install development dependencies
pip install -e .[dev]
if errorlevel 1 (
    echo ⚠️ Warning: Could not install development dependencies
    echo Core installation should still work
)

echo ✅ Dependencies installed

REM Verify installation
echo 🔍 Verifying installation...
python -c "import src.OSBC" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Could not verify installation
    echo You may need to check for missing dependencies
) else (
    echo ✅ Installation verified
)

REM Show completion message
echo.
echo 🎉 Installation complete!
echo.
echo 📋 Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate.bat
echo    # or in PowerShell:
echo    venv\Scripts\Activate.ps1
echo.
echo 2. Run Auto-OSBC:
echo    python src\OSBC.py
echo.
echo 3. To deactivate later:
echo    deactivate
echo.
echo 📝 Note: Make sure your game client is installed and configured

pause