@echo off
:: Demo of Claude Preferences Sync Tool
echo Claude Preferences Sync Tool - Demo Mode
echo ==========================================
echo.

set "TEST_CLAUDE_DIR=%~dp0test-claude-user"
set "PROJECT_PREFS_DIR=%~dp0user-preferences"

echo Creating demo Claude user directory at: %TEST_CLAUDE_DIR%
mkdir "%TEST_CLAUDE_DIR%" 2>nul

echo Creating demo preferences...
echo {"editor.theme": "dark", "auto-save": true} > "%TEST_CLAUDE_DIR%\settings.json"
echo {"ctrl+shift+p": "workbench.action.showCommands"} > "%TEST_CLAUDE_DIR%\keybindings.json"
echo ["extension1", "extension2"] > "%TEST_CLAUDE_DIR%\extensions.json"

echo.
echo Demo preferences created:
echo ✓ settings.json
echo ✓ keybindings.json
echo ✓ extensions.json

if "%1"=="export" goto demo_export
if "%1"=="import" goto demo_import
if "%1"=="status" goto demo_status

:demo_status
echo.
echo Demo Status:
if exist "%PROJECT_PREFS_DIR%" (
    echo ✓ Project preferences directory found
) else (
    echo ✗ No project preferences found
)

if exist "%TEST_CLAUDE_DIR%" (
    echo ✓ Demo Claude installation found
) else (
    echo ✗ Demo Claude not found
)

echo.
echo Demo Claude preferences:
if exist "%TEST_CLAUDE_DIR%\settings.json" (
    echo ✓ settings.json
) else (
    echo ✗ settings.json
)

if exist "%TEST_CLAUDE_DIR%\keybindings.json" (
    echo ✓ keybindings.json
) else (
    echo ✗ keybindings.json
)

goto :eof

:demo_export
echo.
echo Exporting demo Claude preferences...

mkdir "%PROJECT_PREFS_DIR%" 2>nul

copy "%TEST_CLAUDE_DIR%\settings.json" "%PROJECT_PREFS_DIR%\settings.json" >nul
copy "%TEST_CLAUDE_DIR%\keybindings.json" "%PROJECT_PREFS_DIR%\keybindings.json" >nul  
copy "%TEST_CLAUDE_DIR%\extensions.json" "%PROJECT_PREFS_DIR%\extensions.json" >nul

echo Demo Setup Information > "%PROJECT_PREFS_DIR%\setup-info.txt"
echo Export Date: %date% %time% >> "%PROJECT_PREFS_DIR%\setup-info.txt"
echo Machine: %COMPUTERNAME% >> "%PROJECT_PREFS_DIR%\setup-info.txt"
echo Mode: Demo >> "%PROJECT_PREFS_DIR%\setup-info.txt"

echo ✓ Demo preferences exported to %PROJECT_PREFS_DIR%
echo.
echo Files exported:
dir /b "%PROJECT_PREFS_DIR%"

goto :eof

:demo_import
echo.
echo Importing demo Claude preferences...

if not exist "%PROJECT_PREFS_DIR%" (
    echo ERROR: No preferences found at "%PROJECT_PREFS_DIR%"
    goto :eof
)

set "BACKUP_DIR=%TEST_CLAUDE_DIR%\backup-demo"
mkdir "%BACKUP_DIR%" 2>nul

echo Creating backup...
copy "%TEST_CLAUDE_DIR%\*" "%BACKUP_DIR%\" >nul 2>&1

echo Importing preferences...
copy "%PROJECT_PREFS_DIR%\settings.json" "%TEST_CLAUDE_DIR%\settings.json" >nul
copy "%PROJECT_PREFS_DIR%\keybindings.json" "%TEST_CLAUDE_DIR%\keybindings.json" >nul
copy "%PROJECT_PREFS_DIR%\extensions.json" "%TEST_CLAUDE_DIR%\extensions.json" >nul

echo ✓ Demo preferences imported successfully
echo.
echo Remember to restart Claude Code to apply settings

goto :eof