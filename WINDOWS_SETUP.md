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

# Install all dependencies
pip install -r requirements.txt

# Install additional testing dependencies
pip install pytest mypy
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
├── requirements.txt        # Dependencies (shared)
├── CLAUDE.md              # Development workflow
├── WINDOWS_SETUP.md       # This file
└── ...
```

Both environments can coexist and share the same source code while having separate Python environments optimized for their respective platforms.