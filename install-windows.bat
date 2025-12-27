@echo off
REM Auto-OSBC Installation Script for Windows 10/11 with UV Package Manager
REM Usage: install-windows.bat
REM This script will automatically install UV and set up Python 3.10 environment

echo 🚀 Auto-OSBC Windows Installation (UV + Python 3.10)
echo ====================================================

REM Check Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo 🖥️  Windows Version: %VERSION%

REM Basic Windows 10/11 check (simplified)
if "%VERSION%" LSS "10.0" (
    echo ❌ Windows 10 or later required
    echo Current version: %VERSION%
    pause
    exit /b 1
)
echo ✅ Windows version supported

REM ============================================================================
REM Step 1: Check for Python 3.10
REM ============================================================================
echo.
echo 📋 Step 1: Checking for Python 3.10...
echo ======================================

REM Try py launcher first (recommended for Windows)
py -3.10 --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Python 3.10 not found via 'py -3.10'
    echo.
    echo 📥 Python 3.10 Installation Required
    echo.
    echo Please install Python 3.10 from:
    echo https://www.python.org/downloads/release/python-31011/
    echo.
    echo ⚠️  IMPORTANT during installation:
    echo   ✓ Check "Add Python to PATH"
    echo   ✓ Check "Install py launcher for all users"
    echo.
    echo After installation, run this script again.
    pause
    exit /b 1
)

REM Get Python 3.10 version
for /f "tokens=2" %%i in ('py -3.10 --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Found Python %PYTHON_VERSION%

REM Set Python executable for this script
set PYTHON_EXE=py -3.10

REM ============================================================================
REM Step 2: Install UV Package Manager
REM ============================================================================
echo.
echo 📋 Step 2: Installing UV Package Manager...
echo ===========================================

REM Check if UV is already installed
where uv >nul 2>&1
if errorlevel 1 (
    echo 📥 UV not found, installing automatically...

    REM Install UV using PowerShell installer
    echo Running: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    if errorlevel 1 (
        echo ❌ Failed to install UV automatically
        echo.
        echo Please try manual installation:
        echo 1. Open PowerShell as Administrator
        echo 2. Run: irm https://astral.sh/uv/install.ps1 ^| iex
        echo 3. Restart this script
        pause
        exit /b 1
    )

    echo ✅ UV installed successfully

    REM Add UV to PATH for this session (UV installer adds to user PATH)
    REM Refresh environment variables
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo ✅ UV already installed
)

REM Verify UV installation
where uv >nul 2>&1
if errorlevel 1 (
    echo ⚠️  UV installed but not in PATH for this session
    echo Adding UV to PATH...
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

REM Final UV check
uv --version >nul 2>&1
if errorlevel 1 (
    echo ❌ UV installation verification failed
    echo.
    echo Falling back to standard pip installation...
    goto FALLBACK_PIP
)

REM Get UV version
for /f "tokens=*" %%i in ('uv --version 2^>^&1') do set UV_VERSION=%%i
echo ✅ Using %UV_VERSION%

REM ============================================================================
REM Step 3: Create Virtual Environment with UV
REM ============================================================================
echo.
echo 📋 Step 3: Creating Python 3.10 virtual environment...
echo ======================================================

if exist "venv" (
    echo 📁 Virtual environment already exists
    echo.
    choice /C YN /M "Recreate virtual environment? (Y=Yes, N=Keep existing)"
    if errorlevel 2 goto SKIP_VENV_CREATE
    if errorlevel 1 (
        echo 🗑️  Removing existing venv...
        rmdir /s /q venv
    )
)

:CREATE_VENV
echo 🔨 Creating venv with UV (Python 3.10)...
uv venv --python 3.10

if errorlevel 1 (
    echo ⚠️  UV venv creation failed, trying fallback...
    goto FALLBACK_PIP
)

echo ✅ Virtual environment created with UV

:SKIP_VENV_CREATE

REM ============================================================================
REM Step 4: Install Dependencies with UV
REM ============================================================================
echo.
echo 📋 Step 4: Installing dependencies with UV...
echo =============================================

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install with UV (much faster than pip)
echo 📦 Installing Auto-OSBC with UV...
uv pip install -e ".[dev]"

if errorlevel 1 (
    echo ⚠️  UV installation failed, falling back to pip...
    deactivate
    goto FALLBACK_PIP
)

echo ✅ Dependencies installed with UV

goto VERIFY_INSTALL

REM ============================================================================
REM Fallback: Standard pip installation
REM ============================================================================
:FALLBACK_PIP
echo.
echo 📋 Fallback: Using standard pip installation...
echo ===============================================

REM Create venv with standard Python
if not exist "venv" (
    echo 🔨 Creating venv with standard Python...
    %PYTHON_EXE% -m venv venv

    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo ✅ Virtual environment created

REM Activate and install with pip
call venv\Scripts\activate.bat

echo 📦 Upgrading pip...
python -m pip install --upgrade pip

echo 📦 Installing Auto-OSBC with pip...
pip install -e ".[dev]"

if errorlevel 1 (
    echo ❌ Failed to install dependencies with pip
    pause
    exit /b 1
)

echo ✅ Dependencies installed with pip

REM ============================================================================
REM Step 5: Verify Installation
REM ============================================================================
:VERIFY_INSTALL
echo.
echo 📋 Step 5: Verifying installation...
echo ====================================

python -c "import src.OSBC" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Could not import src.OSBC
    echo Installation may be incomplete, but continuing...
) else (
    echo ✅ Auto-OSBC imports successfully
)

REM Check core dependencies
python -c "import numpy, cv2, PIL" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Some core dependencies missing (numpy, opencv, PIL)
) else (
    echo ✅ Core dependencies verified
)

REM ============================================================================
REM Installation Complete
REM ============================================================================
echo.
echo 🎉 Installation Complete!
echo ========================
echo.
echo 📊 Installation Summary:
echo   • Python: %PYTHON_VERSION%
if defined UV_VERSION (
    echo   • UV: %UV_VERSION%
    echo   • Package Manager: UV (10-100x faster than pip^)
) else (
    echo   • Package Manager: pip (fallback^)
)
echo   • Environment: venv\
echo   • Dependencies: Installed from pyproject.toml
echo.
echo 📋 Next Steps:
echo ============
echo.
echo 1️⃣  Activate the virtual environment:
echo    venv\Scripts\activate.bat
echo    # or in PowerShell:
echo    venv\Scripts\Activate.ps1
echo.
echo 2️⃣  Run Auto-OSBC:
echo    python src\OSBC.py
echo.
echo 3️⃣  To deactivate later:
echo    deactivate
echo.
echo 📦 Dependency Management (with UV):
echo    Add package:     uv pip install package-name
echo    Update all:      uv pip install -e ".[dev]" --upgrade
echo    List installed:  uv pip list
echo.
echo 📝 Notes:
echo   • Your game client must be installed and configured
echo   • See README.md for configuration instructions
echo   • See CLAUDE.md for development workflow
echo.

pause
