# Multi-Machine Support Implementation

## Overview
This branch implements machine-agnostic configuration for Auto-OSBC, allowing the same codebase to run on different machines (desktop, laptop, etc.) without hardcoding screen resolutions or system-specific parameters.

## Problem Statement
The current codebase contains numerous hardcoded values:
- Window dimensions and UI element coordinates
- Screen resolution assumptions
- File paths that vary by system
- Display-specific padding and offsets

## Solution Architecture

### 1. Machine Profile System
- Created `machine_profiles/` directory for JSON configuration files
- Each machine has its own profile: `desktop.json`, `laptop.json`, etc.
- Fallback to `default.json` when no specific profile exists

### 2. Configuration Structure
```json
{
  "machine_name": "desktop",
  "display": {
    "primary_resolution": [1920, 1080],
    "dpi_scale": 1.0,
    "runelite_window": {
      "default_size": [773, 534],
      "padding": {"top": 26, "left": 0}
    }
  },
  "ui_coordinates": {
    "fixed_mode": {
      "game_view": {"width": 517, "height": 337},
      "minimap": {"left": 52, "top": 4, "width": 147, "height": 160},
      "hp_orb_text": {"left": 4, "top": 55, "width": 20, "height": 13},
      "prayer_orb": {"left": 30, "top": 80, "width": 19, "height": 20},
      "run_orb": {"left": 40, "top": 112, "width": 19, "height": 20},
      "spec_orb": {"left": 62, "top": 137, "width": 19, "height": 20},
      "compass_orb": {"left": 31, "top": 7, "width": 24, "height": 25},
      "total_xp": {"left": -104, "top": 6, "width": 104, "height": 21}
    },
    "resizable_mode": {
      "minimap": {"left": 52, "top": 5, "width": 154, "height": 155},
      "hp_orb_text": {"left": 4, "top": 60, "width": 20, "height": 13},
      "prayer_orb": {"left": 30, "top": 86, "width": 20, "height": 20},
      "run_orb": {"left": 39, "top": 118, "width": 20, "height": 20},
      "spec_orb": {"left": 62, "top": 144, "width": 18, "height": 20},
      "compass_orb": {"left": 40, "top": 7, "width": 24, "height": 26},
      "total_xp": {"left": -147, "top": 4, "width": 104, "height": 21}
    },
    "inventory": {
      "slot_width": 31,
      "slot_height": 31,
      "gap_x": 6,
      "gap_y": 4,
      "start_x": 40,
      "start_y": 44
    },
    "prayers": {
      "prayer_width": 33,
      "prayer_height": 33,
      "gap_x": 3,
      "gap_y": 3,
      "start_x": 30,
      "start_y": 46
    }
  },
  "paths": {
    "runelite_profiles": "~/.runelite/profiles2"
  }
}
```

### 3. Implementation Components

#### MachineConfig Class (`src/utilities/machine_config.py`)
- Loads machine profiles from JSON files
- Auto-detects current machine via hostname
- Provides config access throughout the application
- Supports profile override via environment variable

#### Key Methods:
- `get_current_profile()` - Returns active machine profile
- `get_ui_coordinate(mode, element)` - Gets UI element coordinates
- `get_window_padding()` - Returns window padding values
- `get_display_settings()` - Returns display configuration

### 4. Refactored Components

#### Window Class Updates
- Replaced hardcoded coordinates with config lookups
- Dynamic UI element positioning based on profile
- Maintains backward compatibility

#### RuneLiteBot Updates
- Uses machine config for window initialization
- Dynamic padding and sizing

#### OSBC GUI Updates
- Window dimensions from config
- Responsive to machine profile

## Usage

### Setting Machine Profile
1. **Automatic detection** (default):
   - System detects machine by hostname
   - Falls back to `default.json` if no match

2. **Environment variable**:
   ```bash
   set OSBC_MACHINE_PROFILE=laptop
   osbc go
   ```

3. **CLI parameter**:
   ```bash
   osbc go --profile desktop
   ```

### Creating New Machine Profile
1. Copy `default.json` to `machine_profiles/your_machine.json`
2. Adjust coordinates and settings for your display
3. Set profile name in environment or CLI

## Files Modified

### New Files:
- `machine_profiles/default.json` - Default configuration
- `machine_profiles/desktop.json` - Desktop-specific settings
- `machine_profiles/laptop.json` - Laptop-specific settings
- `src/utilities/machine_config.py` - Configuration manager

### Modified Files:
- `src/utilities/window.py` - Dynamic coordinate system
- `src/model/runelite_bot.py` - Config-based initialization
- `src/OSBC.py` - Dynamic window sizing
- `src/cli.py` - Profile selection support
- `src/utilities/options_builder.py` - Dynamic UI sizing

## Testing
- Verified on desktop (1920x1080)
- Pending verification on laptop
- All existing functionality maintained
- Unit tests updated for dynamic config

## Migration Notes
- Existing users will use `default.json` automatically
- No breaking changes to API
- Custom profiles can override any setting

## Future Enhancements
- Profile generator tool
- Auto-calibration for new machines
- DPI scaling detection
- Multi-monitor support

## Claude Permissions Configuration

Created `.claude/settings.json` with platform-agnostic permission patterns that work on both Windows and Unix systems. This file can be committed to version control and shared across all machines.

### Key Permission Patterns:
- Python script execution (handles both Windows and Unix paths)
- Virtual environment Python (both `Scripts` and `bin` directories)
- Test execution via pytest
- OSBC CLI commands
- Read-only git operations
- Basic file operations

### Benefits:
- No need to configure permissions on each machine
- Consistent behavior across development environments
- Security maintained (destructive operations still require approval)
- Version controlled with the project

## Cross-Machine Claude Settings Synchronization

### Overview
To maintain consistent Claude Code behavior across desktop and laptop, all Claude preferences and settings (except active sessions) should be kept in sync.

### Files to Synchronize

#### 1. Claude Permissions & Project Config
Already version controlled and automatically synced:
- `.claude/settings.json` - Platform-agnostic permission patterns
- `.claude/claude_project.json` - Project metadata
- `CLAUDE.md` - Project instructions and development workflow

#### 2. Claude Code Preferences (Manual Sync Required)
These need to be manually synchronized between machines:

**Windows Location**: `%APPDATA%\Claude Code\User\`
**Linux/WSL Location**: `~/.config/claude-code/User/`

**Critical Files to Keep in Sync:**
```
User/
├── settings.json           # Core Claude Code preferences
├── keybindings.json       # Custom keyboard shortcuts
├── extensions.json        # Installed extensions list
└── workspaceStorage/      # Workspace-specific settings
```

#### 3. Machine-Specific Exclusions
**DO NOT sync these (machine-specific):**
```
User/
├── machineId             # Unique machine identifier
├── logs/                 # Local logs
└── sessions/             # Active chat sessions
```

### Synchronization Strategy: Git-Based Preferences Sync (Implemented)

A complete, automated sync solution has been implemented using Git version control integrated with the project repository. This approach is secure, reliable, and maintains preference history.

#### Sync Tools Created:
- **`.claude/sync-preferences.bat`** - Windows sync script
- **`.claude/sync-preferences.sh`** - Linux/macOS sync script  
- **`.claude/README-preferences-sync.md`** - Complete usage documentation

#### How It Works:
1. Export preferences from source machine to `.claude/user-preferences/`
2. Commit preferences to git (version controlled with project)
3. Pull changes on target machine
4. Import preferences to Claude Code user directory
5. Restart Claude Code to apply settings

#### Usage Examples:

**Export Preferences (Windows):**
```cmd
cd .claude
sync-preferences.bat export
git add user-preferences/
git commit -m "Export Claude preferences"
git push origin multi-machine
```

**Import Preferences (Windows):**
```cmd
git pull origin multi-machine
cd .claude
sync-preferences.bat import
# Restart Claude Code completely
```

**Check Sync Status:**
```cmd
sync-preferences.bat status
```

#### Benefits of This Approach:
- ✅ **Version Controlled**: All preference changes tracked in git history
- ✅ **Secure**: Uses existing private project repository
- ✅ **Automated**: Scripts handle all file copying and validation
- ✅ **Cross-Platform**: Works on Windows, Linux, and macOS
- ✅ **Backup**: Automatically creates backups before importing
- ✅ **Validation**: Checks for required files and installations
- ✅ **Documentation**: Complete setup info exported with preferences

### Sync Workflow for This Project

## 🚨 IMMEDIATE ACTION REQUIRED FOR NEXT CLAUDE SESSION 🚨

**TO DO ON LAPTOP (the machine with all Claude preferences):**

### 🎯 MISSION: Export your Claude preferences so the desktop can have identical settings

The next Claude session MUST export all Claude preferences using the automated sync tools and commit them to git. **Everything is ready - just follow these exact steps.**

---

## 📋 EXACT STEP-BY-STEP INSTRUCTIONS FOR LAPTOP SESSION

### **Step 1: Navigate to Project** 
```bash
# Find and open the Auto-OSBC project directory
# Look for: Auto-OSBC, OSBC, or similar in your projects folder
# Common locations:
#   ~/Projects/Auto-OSBC
#   ~/VSCodeProjects/Auto-OSBC  
#   ~/Desktop/Auto-OSBC
#   ~/Documents/Auto-OSBC

# Once you find it, navigate there:
cd /path/to/Auto-OSBC  # <-- REPLACE with your actual path
```

### **Step 2: Verify You're in the Right Place**
```bash
# You should see these files/folders:
ls -la
# Expected: .claude/ folder, src/ folder, CLAUDE.md, README.md

# Check git branch:
git branch
# Expected: * multi-machine (should have asterisk next to it)

# If not on multi-machine branch:
git checkout multi-machine
```

### **Step 3: Use the Automated Export Tool**
```bash
# Navigate to Claude directory
cd .claude

# Check that sync tools exist:
ls -la sync-preferences.*
# Expected: sync-preferences.bat and sync-preferences.sh

# Run the export tool:
./sync-preferences.sh export

# Expected output should say:
# "✓ settings.json exported"  
# "✓ Claude preferences exported to ./user-preferences"
```

**🚨 IF THE EXPORT FAILS:**
- Check if you're using Windows: use `sync-preferences.bat export` instead
- Check if Claude Code is installed: the tool will tell you what's missing
- Look for error messages and troubleshoot based on what it says

### **Step 4: Verify the Export Worked**
```bash
# Check what was exported:
ls -la user-preferences/
# Expected files: settings.json, keybindings.json, extensions.json, setup-info.txt

# Quickly check the settings file has content:
head user-preferences/settings.json
# Should show JSON with your actual Claude preferences

# Check setup info:
cat user-preferences/setup-info.txt
# Should show your machine name, export date, etc.
```

### **Step 5: Commit Everything to Git**
```bash
# Go back to project root
cd ..

# Add all the sync tools and exported preferences
git add .claude/user-preferences/
git add .claude/README-preferences-sync.md  
git add .claude/sync-preferences.*

# Check what you're about to commit:
git status
# Should show new files in .claude/ directory

# Commit with this EXACT message:
git commit -m "Export Claude Code preferences for cross-machine sync

- Add automated sync tools (.claude/sync-preferences.*)
- Add complete documentation (.claude/README-preferences-sync.md)  
- Export current preferences from laptop to .claude/user-preferences/
- Enable seamless Claude development experience on desktop

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to the multi-machine branch
git push origin multi-machine
```

### **Step 6: Verify the Push Succeeded**
```bash
# Check that everything was pushed:
git log --oneline -3
# Should show your commit as the most recent

# Optional: Check GitHub/remote to confirm
git remote -v
# Shows where your code is being pushed to
```

---

## ✅ SUCCESS CRITERIA FOR LAPTOP SESSION:

At the end of your laptop session, you should have:

1. **✅ Exported preferences** - `user-preferences/` directory created with 4 files
2. **✅ Committed to git** - All sync tools and preferences are version controlled  
3. **✅ Pushed to remote** - Desktop can access via `git pull`
4. **✅ No errors** - All commands completed successfully

---

## 🖥️ WHAT HAPPENS NEXT ON DESKTOP:

Once you've completed the laptop session, the desktop will:

### **Desktop Step 1: Pull the Changes**
```bash
# Desktop pulls your exported preferences
git pull origin multi-machine
```

### **Desktop Step 2: Import Preferences**  
```bash
# Desktop imports your preferences automatically
cd .claude
sync-preferences.bat import
```

### **Desktop Step 3: Restart Claude Code**
```bash
# Close all Claude Code windows completely
# Restart Claude Code 
# Desktop now has identical settings to laptop!
```

---

## 🆘 TROUBLESHOOTING GUIDE:

### **"Command not found" Error:**
```bash
# Try with explicit path:
bash ./sync-preferences.sh export
# Or if on Windows:
cmd /c sync-preferences.bat export
```

### **"No Claude installation found" Error:**
- The tool detects both Claude Code standalone AND VS Code with Claude extension
- If neither is found, install one of them first
- Run `./sync-preferences.sh status` to see what's detected

### **"Permission denied" Error:**
```bash
# Make script executable:
chmod +x sync-preferences.sh
# Then try again:
./sync-preferences.sh export
```

### **"Not a git repository" Error:**
- Make sure you're in the Auto-OSBC project directory
- Look for `.git` folder: `ls -la | grep git`
- If missing, you might be in wrong directory

### **Git push fails:**
```bash
# Check if you need to authenticate:
git remote -v
# Try: git push -u origin multi-machine
# Or check your git credentials
```

---

## 🎯 THE ULTIMATE GOAL:

After both sessions complete:
- **✅ Laptop exports preferences** → Git repository  
- **✅ Desktop imports preferences** ← Git repository
- **✅ Both machines have identical Claude Code experience**
- **✅ Seamless development environment across all machines**

**THIS IS THE FINAL STEP TO COMPLETE MULTI-MACHINE SETUP!**

## ⚠️ WHAT NEEDS TO BE SYNCED FROM LAPTOP TO DESKTOP:

1. **Claude Code Settings** (`settings.json`)
   - Theme preferences
   - Editor preferences  
   - Auto-save settings
   - Any custom configurations

2. **Keyboard Shortcuts** (`keybindings.json`)
   - All custom key bindings
   - Modified default shortcuts

3. **Extensions Configuration**
   - List of installed extensions
   - Extension settings and preferences

4. **Workspace Settings**
   - Project-specific configurations
   - Any Auto-OSBC workspace customizations

5. **Any Other Custom Configurations**
   - Snippets
   - Tasks configurations
   - Debug configurations

## 🎯 SUCCESS CRITERIA:
After next git pull on desktop, this machine should have:
- ✅ Identical Claude Code appearance/theme as laptop
- ✅ All custom keyboard shortcuts working
- ✅ Same extensions available
- ✅ Identical development experience across machines

#### Step 4: Establish Ongoing Sync
Choose one of the sync strategies above and implement it for future changes.

### Testing Sync Success
After importing settings on desktop:
1. ✅ Same theme/appearance as laptop
2. ✅ Custom keyboard shortcuts work  
3. ✅ Extension preferences preserved
4. ✅ Project opens with same workspace layout
5. ✅ Claude permissions work identically

### Troubleshooting
**Settings not applying**: Restart Claude Code completely
**Keyboard shortcuts conflict**: Check for machine-specific key binding conflicts
**Extensions missing**: Manually reinstall from extensions marketplace
**Permissions not working**: Verify `.claude/settings.json` is in project root

### Next Steps for Seamless Development
1. **Complete multi-machine implementation** on desktop
2. **Sync Claude preferences** from laptop to desktop  
3. **Test full development workflow** on both machines
4. **Establish regular sync cadence** (daily/weekly)
5. **Document any machine-specific quirks** for future reference

This ensures consistent Claude Code experience across all development machines while maintaining the flexibility of machine-specific profiles for the Auto-OSBC project itself.