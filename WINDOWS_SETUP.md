# Setting Up Claude Code on Windows

This guide will help you set up Claude Code on Windows for optimal Auto-OSBC development and testing.

## Why Windows Setup?

For Auto-OSBC game automation, Windows provides significant advantages:
- ✅ Native game client compatibility
- ✅ Full GUI automation support (`pyautogui`, `pywinctl`, `mss`)
- ✅ Proper window detection and management
- ✅ All visual tests pass without display issues
- ✅ Screenshot capture works natively

## Installation Steps

### 1. Download and Install Claude Code

1. Visit https://claude.ai/code
2. Download the Windows installer (.exe file)
3. Run the installer and follow the setup wizard
4. Launch Claude Code after installation

### 2. Open Your Auto-OSBC Project

1. In Claude Code, click "Open Folder"
2. Navigate to your project directory:
   ```
   C:\Users\adamh\VSCodeProjects\Auto-OSBC
   ```
3. Select the folder and open it

### 3. Set Up Python Environment

Open the integrated terminal in Claude Code (Terminal → New Terminal) and run:

```cmd
# Navigate to project directory
cd C:\Users\adamh\VSCodeProjects\Auto-OSBC

# Create Windows-specific virtual environment
python -m venv venv-windows

# Activate the virtual environment
venv-windows\Scripts\activate

# Install all dependencies (includes dev/testing tools)
pip install -e ".[dev]"
```

### 4. Verify Installation

Run the test suite to verify everything works:

```cmd
# Make sure venv is activated
venv-windows\Scripts\activate

# Run all tests
python -m pytest tests/ -v

# Run type checking
mypy src/
```

## Expected Results on Windows

With Windows setup, you should see significantly better test results:

- **GUI Tests**: `pyautogui` and `pywinctl` tests should pass
- **Screenshot Tests**: MSS screenshot capture should work
- **Window Management**: All window detection tests should pass
- **Mouse Automation**: Full mouse automation capabilities

## Development Workflow Options

### Option 1: Full Windows Development
- Develop entirely in Claude Code on Windows
- Run all tests and bots natively
- Best for active bot development and testing

### Option 2: Hybrid Development
- Continue development in WSL2 for some tasks
- Use Windows for GUI testing and bot execution
- Sync code between environments as needed

### Option 3: Dual Environment
- Keep both environments active
- Use WSL2 for backend/API development
- Use Windows for frontend/GUI automation

## Troubleshooting

### Common Issues and Solutions

**Python not found:**
```cmd
# Install Python from https://python.org or Microsoft Store
# Ensure "Add Python to PATH" is checked during installation
```

**Permission errors:**
```cmd
# Run PowerShell as Administrator if needed
# Or use Windows Terminal with elevated privileges
```

**Dependencies fail to install:**
```cmd
# Update pip first
python -m pip install --upgrade pip

# Install Visual C++ Build Tools if needed:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

## Next Steps

1. **Test Your Setup**: Run the full test suite to ensure everything works
2. **Run Your Bots**: Try running existing bots to verify GUI automation
3. **Continue Development**: Follow the TDD workflow from CLAUDE.md

## File Structure After Setup

```
Auto-OSBC/
├── venv/                    # WSL2 virtual environment
├── venv-windows/           # Windows virtual environment
├── src/                    # Source code (shared)
├── tests/                  # Test suite (shared)
├── pyproject.toml          # Dependencies and project config (shared)
├── CLAUDE.md              # Development workflow
├── WINDOWS_SETUP.md       # This file
└── ...
```

Both environments can coexist and share the same source code while having separate Python environments optimized for their respective platforms.

## Multi-Machine Setup Notes (Desktop Implementation)

### Current Status
- **Multi-machine support implementation**: ✅ COMPLETE
- **Machine profiles system**: ✅ Implemented in `machine_profiles/`
- **Dynamic coordinate system**: ✅ Window class refactored
- **CLI profile selection**: ✅ `osbc --profile <name>` support

### Quick Setup for This Desktop
Use the simplified installer that follows this setup guide:

```cmd
# Run the setup script (creates venv-windows as recommended)
setup-windows.bat

# Test the multi-machine system works
venv-windows\Scripts\activate
python -c "from utilities.machine_config import get_machine_config; print(f'Using profile: {get_machine_config().profile_name}')"
```

### Machine Configuration Files
- `machine_profiles/default.json` - Base configuration with all hardcoded values extracted
- `machine_profiles/desktop.json` - Desktop-specific overrides (if needed)  
- `machine_profiles/laptop.json` - Laptop-specific overrides (if needed)
- `.claude/settings.json` - Platform-agnostic Claude permissions (shared across machines)

### Key Changes Made
1. **MachineConfig class** (`src/utilities/machine_config.py`) - Loads profiles automatically
2. **Window class updated** - All hardcoded coordinates now use machine config
3. **RuneLiteBot updated** - Dynamic window sizing and padding
4. **OSBC GUI updated** - Dynamic window dimensions  
5. **CLI enhanced** - Profile selection via `--profile` flag

### Testing Multi-Machine Features
```cmd
# Test different profiles
set OSBC_MACHINE_PROFILE=laptop
osbc status

# Test with CLI flag
osbc --profile desktop status

# Test machine config loading
python scripts/recorder.py --list-templates
```

### Benefits
- No more hardcoded screen resolutions or coordinates
- Seamless switching between desktop and laptop
- Same codebase works on different display configurations
- Profile settings are version controlled and shared