@echo off
:: Claude Code Preferences Sync Script for Windows
:: This script manages syncing Claude preferences between machines via Git

set "CLAUDE_USER_DIR=%APPDATA%\Claude Code\User"
set "VSCODE_USER_DIR=%APPDATA%\Code\User"
set "PROJECT_PREFS_DIR=%~dp0user-preferences"

:: Check if Claude Code is installed (standalone or as VS Code extension)
if exist "%ACTIVE_USER_DIR%" (
    set "ACTIVE_USER_DIR=%CLAUDE_USER_DIR%"
    echo Using Claude Code standalone installation
) else if exist "%VSCODE_USER_DIR%" (
    set "ACTIVE_USER_DIR=%VSCODE_USER_DIR%"
    echo Using VS Code with Claude Code extension
) else (
    echo ERROR: Neither Claude Code nor VS Code found
    echo Expected locations:
    echo   "%ACTIVE_USER_DIR%"
    echo   "%VSCODE_USER_DIR%"
    echo Please install Claude Code or VS Code with Claude Code extension.
    exit /b 1
)

:: Parse command line arguments
if "%1"=="export" goto export_prefs
if "%1"=="import" goto import_prefs
if "%1"=="status" goto check_status
if "%1"=="help" goto show_help

:show_help
echo Claude Preferences Sync Tool
echo.
echo Usage: sync-preferences.bat [command]
echo.
echo Commands:
echo   export  - Export current Claude preferences to git
echo   import  - Import preferences from git to Claude
echo   status  - Check sync status
echo   help    - Show this help
echo.
echo Examples:
echo   sync-preferences.bat export   (run on machine with current preferences)
echo   sync-preferences.bat import   (run on machine to receive preferences)
goto :eof

:export_prefs
echo Exporting Claude Code preferences for cross-machine sync...

:: Create preferences directory if it doesn't exist
if not exist "%PROJECT_PREFS_DIR%" mkdir "%PROJECT_PREFS_DIR%"

:: Export core settings
echo Copying settings.json...
copy "%ACTIVE_USER_DIR%\settings.json" "%PROJECT_PREFS_DIR%\settings.json" >nul 2>&1
if errorlevel 1 (
    echo WARNING: settings.json not found or failed to copy
) else (
    echo ✓ settings.json exported
)

:: Export keybindings
echo Copying keybindings.json...
copy "%ACTIVE_USER_DIR%\keybindings.json" "%PROJECT_PREFS_DIR%\keybindings.json" >nul 2>&1
if errorlevel 1 (
    echo WARNING: keybindings.json not found - using default keybindings
    echo {} > "%PROJECT_PREFS_DIR%\keybindings.json"
) else (
    echo ✓ keybindings.json exported
)

:: Export extensions list if it exists
echo Copying extensions.json...
copy "%ACTIVE_USER_DIR%\extensions.json" "%PROJECT_PREFS_DIR%\extensions.json" >nul 2>&1
if errorlevel 1 (
    echo WARNING: extensions.json not found - no extensions configured
    echo [] > "%PROJECT_PREFS_DIR%\extensions.json"
) else (
    echo ✓ extensions.json exported
)

:: Document current setup
echo Documenting current setup...
echo Claude Code Setup Information > "%PROJECT_PREFS_DIR%\setup-info.txt"
echo Export Date: %date% %time% >> "%PROJECT_PREFS_DIR%\setup-info.txt"
echo Machine: %COMPUTERNAME% >> "%PROJECT_PREFS_DIR%\setup-info.txt"
echo User: %USERNAME% >> "%PROJECT_PREFS_DIR%\setup-info.txt"
echo Claude User Directory: %CLAUDE_USER_DIR% >> "%PROJECT_PREFS_DIR%\setup-info.txt"

:: List installed extensions
echo. >> "%PROJECT_PREFS_DIR%\setup-info.txt"
echo Installed Extensions: >> "%PROJECT_PREFS_DIR%\setup-info.txt"
if exist "%CLAUDE_USER_DIR%\extensions" (
    dir /b "%CLAUDE_USER_DIR%\extensions" >> "%PROJECT_PREFS_DIR%\setup-info.txt" 2>nul
) else (
    echo No extensions directory found >> "%PROJECT_PREFS_DIR%\setup-info.txt"
)

echo.
echo ✓ Claude preferences exported to %PROJECT_PREFS_DIR%
echo.
echo Next steps:
echo 1. Review exported files to ensure they contain your preferences
echo 2. Commit these files to git: 
echo    git add .claude/user-preferences/
echo    git commit -m "Export Claude Code preferences for cross-machine sync"
echo    git push origin multi-machine
goto :eof

:import_prefs
echo Importing Claude Code preferences from git...

:: Check if preferences directory exists
if not exist "%PROJECT_PREFS_DIR%" (
    echo ERROR: No preferences found at "%PROJECT_PREFS_DIR%"
    echo Run 'git pull origin multi-machine' first to sync preferences.
    exit /b 1
)

:: Backup current preferences
set "BACKUP_DIR=%CLAUDE_USER_DIR%\backup-%date:~-4%%date:~4,2%%date:~7,2%"
echo Creating backup at "%BACKUP_DIR%"...
mkdir "%BACKUP_DIR%" >nul 2>&1
copy "%CLAUDE_USER_DIR%\settings.json" "%BACKUP_DIR%\" >nul 2>&1
copy "%CLAUDE_USER_DIR%\keybindings.json" "%BACKUP_DIR%\" >nul 2>&1
copy "%CLAUDE_USER_DIR%\extensions.json" "%BACKUP_DIR%\" >nul 2>&1

:: Import settings
echo Importing settings.json...
if exist "%PROJECT_PREFS_DIR%\settings.json" (
    copy "%PROJECT_PREFS_DIR%\settings.json" "%CLAUDE_USER_DIR%\settings.json" >nul
    echo ✓ settings.json imported
) else (
    echo WARNING: settings.json not found in preferences
)

:: Import keybindings
echo Importing keybindings.json...
if exist "%PROJECT_PREFS_DIR%\keybindings.json" (
    copy "%PROJECT_PREFS_DIR%\keybindings.json" "%CLAUDE_USER_DIR%\keybindings.json" >nul
    echo ✓ keybindings.json imported
) else (
    echo WARNING: keybindings.json not found in preferences
)

:: Import extensions list
echo Importing extensions.json...
if exist "%PROJECT_PREFS_DIR%\extensions.json" (
    copy "%PROJECT_PREFS_DIR%\extensions.json" "%CLAUDE_USER_DIR%\extensions.json" >nul
    echo ✓ extensions.json imported
) else (
    echo WARNING: extensions.json not found in preferences
)

echo.
echo ✓ Claude preferences imported successfully
echo.
echo IMPORTANT: Restart Claude Code completely to apply all settings
echo           Close all Claude Code windows and restart the application
goto :eof

:check_status
echo Claude Preferences Sync Status
echo ==============================
echo.

:: Check if project preferences exist
if exist "%PROJECT_PREFS_DIR%" (
    echo ✓ Project preferences directory found
    if exist "%PROJECT_PREFS_DIR%\setup-info.txt" (
        echo.
        echo Last export information:
        type "%PROJECT_PREFS_DIR%\setup-info.txt"
    )
) else (
    echo ✗ No project preferences found
    echo   Run 'sync-preferences.bat export' to export current preferences
)

echo.
:: Check Claude installation
if exist "%ACTIVE_USER_DIR%" (
    echo ✓ Claude Code installation found at %CLAUDE_USER_DIR%
) else (
    echo ✗ Claude Code not installed
)

:: Check for current preferences
echo.
echo Current Claude preferences:
if exist "%CLAUDE_USER_DIR%\settings.json" (
    echo ✓ settings.json
) else (
    echo ✗ settings.json
)

if exist "%CLAUDE_USER_DIR%\keybindings.json" (
    echo ✓ keybindings.json
) else (
    echo ✗ keybindings.json (using defaults)
)

if exist "%CLAUDE_USER_DIR%\extensions.json" (
    echo ✓ extensions.json
) else (
    echo ✗ extensions.json (no extensions)
)

goto :eof