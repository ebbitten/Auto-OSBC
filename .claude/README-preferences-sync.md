# Claude Code Preferences Synchronization

This directory contains tools and configuration for synchronizing Claude Code preferences across multiple development machines.

## Overview

The preference sync system allows you to:
- Export Claude Code settings from one machine
- Commit them to git for version control
- Import them on other machines
- Maintain consistent Claude experience across all development environments

## Files in This Directory

- **`sync-preferences.bat`** - Windows sync script
- **`sync-preferences.sh`** - Linux/macOS sync script  
- **`settings.json`** - Platform-agnostic project permissions (already version controlled)
- **`user-preferences/`** - Exported user preferences (created by sync scripts)

## Quick Start

### Step 1: Export Preferences (Machine with Current Setup)

**Windows:**
```cmd
cd .claude
sync-preferences.bat export
```

**Linux/macOS:**
```bash
cd .claude
./sync-preferences.sh export
```

### Step 2: Commit to Git
```bash
git add .claude/user-preferences/
git commit -m "Export Claude Code preferences for cross-machine sync"
git push origin multi-machine
```

### Step 3: Import on Other Machines

First, pull the latest changes:
```bash
git pull origin multi-machine
```

Then import preferences:

**Windows:**
```cmd
cd .claude
sync-preferences.bat import
```

**Linux/macOS:**
```bash
cd .claude
./sync-preferences.sh import
```

### Step 4: Restart Claude Code
Close all Claude Code windows and restart the application to apply imported settings.

## What Gets Synchronized

### ✅ Synchronized Files:
- **`settings.json`** - All Claude Code preferences (theme, editor settings, etc.)
- **`keybindings.json`** - Custom keyboard shortcuts
- **`extensions.json`** - List of installed extensions
- **Setup information** - Export metadata for troubleshooting

### ❌ Not Synchronized (Machine-Specific):
- **Active sessions** - Chat histories remain local
- **Machine ID** - Unique identifiers stay separate
- **Logs** - Local debugging information
- **Cache files** - Temporary data

## Commands Reference

All scripts support these commands:

### `export`
Exports current Claude preferences to the project directory for version control.

### `import` 
Imports preferences from the project directory to Claude Code.

### `status`
Shows the current sync status and what preferences are available.

### `help`
Displays usage information and examples.

## Troubleshooting

### Settings Not Applying
- **Solution**: Restart Claude Code completely (close all windows, restart application)
- **Cause**: Claude Code caches settings and requires restart to reload

### Preferences Not Found
- **Solution**: Run `git pull origin multi-machine` to get latest preferences
- **Cause**: Preferences haven't been exported from the source machine yet

### Permission Errors (Windows)
- **Solution**: Run Command Prompt as Administrator
- **Cause**: Windows may restrict access to AppData directory

### Script Not Executable (Linux/macOS)
- **Solution**: Run `chmod +x sync-preferences.sh`
- **Cause**: Git doesn't preserve execute permissions on some systems

## Security Notes

- User preferences may contain sensitive information (API keys, tokens)
- Only commit preferences to private repositories
- Review exported files before committing
- Use `.gitignore` to exclude sensitive files if needed

## Integration with Multi-Machine Setup

This preferences sync integrates seamlessly with the project's multi-machine configuration system:

1. **Project Settings**: `.claude/settings.json` (platform-agnostic permissions)
2. **Machine Profiles**: `machine_profiles/*.json` (display/coordinate settings)
3. **User Preferences**: `.claude/user-preferences/` (Claude Code personal settings)

Together, these provide a complete cross-machine development environment.