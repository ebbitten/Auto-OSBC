# Auto-OSBC CLI Guide

The `osbc` command provides a unified interface for all Auto-OSBC tools. This guide covers installation, usage, and common workflows.

## Quick Start

```powershell
# The recommended way to start Auto-OSBC
osbc start
```

This single command will:
1. Launch OSBC (if not running)
2. Select OSRS from the game dropdown
3. Click "Launch OSRS" to start RuneLite
4. Wait for RuneLite window to appear
5. Open the bot selection GUI

---

## Installation

After cloning the repository, install the package in development mode:

```powershell
# Navigate to project directory
cd C:\Users\adamh\VSCodeProjects\Auto-OSBC

# Install package with CLI (uses uv package manager)
uv pip install -e . --python .\venv\Scripts\python.exe
```

Verify installation:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Test the CLI
osbc --help
```

---

## Commands Overview

### Primary Entry Points

| Command | Description |
|---------|-------------|
| `osbc start` | **RECOMMENDED**: Auto-launch RuneLite + open bot GUI |
| `osbc start --no-launch` | Skip auto-launch, just open GUI |
| `osbc start --headless` | Auto-launch only, no GUI |

### Automation Commands

| Command | Description |
|---------|-------------|
| `osbc auto-launch` | Launch RuneLite via OSBC (no GUI) |
| `osbc gui` | Open the bot selection GUI |
| `osbc login` | Automate game login |
| `osbc status` | Check if OSBC/RuneLite are running |
| `osbc select-game` | Select a game in OSBC dropdown |
| `osbc launch` | Click Launch button in OSBC |

### Development Tools

| Command | Description |
|---------|-------------|
| `osbc record` | Record game state (screenshots, mouse, timing) |
| `osbc capture` | Take screenshots of game regions |
| `osbc debug` | Launch interactive debug console |
| `osbc profile` | Run performance benchmarks |

---

## Architecture

Auto-OSBC follows a layered architecture:

```
Human Entry Points
├── CLI (osbc commands)      → Quick automation
├── GUI (osbc gui)           → Visual bot management
└── Python imports           → Developer scripting

Framework Layers
├── Orchestration            → Multi-step workflows (auto_launch_runelite)
├── Actions/Confirmations    → Single-step building blocks
├── Intents                  → Pure data, no side effects
├── Executor                 → Performs side effects (mouse, keyboard)
└── Bot Scripts              → Combine actions into runnable bots
```

### Layer Details

| Layer | Purpose | Files |
|-------|---------|-------|
| **Entry Points** | Human interaction | `src/cli.py`, `src/OSBC.py` |
| **Orchestration** | Multi-step workflows | `model/actions/orchestration.py` |
| **Actions** | Single-step building blocks | `model/actions/*.py` |
| **Intents** | Pure data, no side effects | `model/actions/intents.py` |
| **Executor** | Performs side effects | `model/actions/executor.py` |
| **Bot Scripts** | Combine actions into bots | `model/osrs/*.py` |

---

## osbc start

**The main entry point for Auto-OSBC.** Combines auto-launch with the bot GUI.

### Basic Usage

```powershell
# Full workflow: launch RuneLite + open GUI
osbc start

# Skip auto-launch (RuneLite already running)
osbc start --no-launch

# Auto-launch only, no GUI (for scripting)
osbc start --headless
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--game` | "OSRS" | Game to select in OSBC |
| `--timeout` | 120 | Timeout waiting for RuneLite (seconds) |
| `--no-launch` | false | Skip auto-launch, just open GUI |
| `--headless` | false | Auto-launch only, don't open GUI |
| `--force-gui` | false | Open GUI even if auto-launch fails |

---

## osbc auto-launch

Launch RuneLite via OSBC without opening the bot GUI.

```powershell
# Launch with defaults
osbc auto-launch

# Custom game selection
osbc auto-launch --game OSRS

# With login trigger
osbc auto-launch --login
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--game` | "OSRS" | Game to select |
| `--timeout` | 120 | Timeout for RuneLite window |
| `--login` | false | Trigger login after launch |
| `--no-skip` | false | Launch even if RuneLite running |

---

## osbc status

Check if OSBC and RuneLite windows are running.

```powershell
osbc status
# Output: OSBC: OS Bot COLOR | RuneLite: RuneLite - player123

osbc status -v
# Verbose output with window titles
```

---

## osbc login

Automate game login using environment credentials.

### Setup Credentials

```powershell
# Set environment variables
$env:OSBC_USERNAME = "your_username"
$env:OSBC_PASSWORD = "your_password"

# Or use a .env file in project root
```

### Usage

```powershell
# Login with default window
osbc login

# Specify window title
osbc login --window "RuneLite - player123"

# Set max retry attempts
osbc login --max-attempts 5
```

---

## osbc record

Continuously capture screenshots, mouse positions, and window state.

```powershell
# Record for 10 seconds (default)
osbc record

# Record for 30 seconds
osbc record --duration 30

# Record until Ctrl+C
osbc record --until-stop
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--duration` | 10 | Recording duration in seconds |
| `--until-stop` | false | Record until Ctrl+C |
| `--window` | "RuneLite" | Window title to capture |
| `--interval` | 500 | Capture interval (milliseconds) |
| `--output` | captures/ | Output directory |

---

## osbc capture

Take one-time screenshots of game regions.

```powershell
# Capture all game regions
osbc capture "login_screen_test"

# Capture specific regions
osbc capture "inventory_check" --regions game_view inventory

# Capture inventory with slot overlays
osbc capture "full_inventory" --inventory
```

---

## osbc debug

Launch an interactive console for debugging.

```powershell
osbc debug
```

Commands: `window`, `screenshot`, `mouse`, `help`

---

## osbc profile

Run performance benchmarks.

```powershell
osbc profile
osbc profile --window "RuneLite" --output-dir ./benchmarks
```

---

## Common Workflows

### Workflow 1: Daily Bot Session

```powershell
# One command to start everything
osbc start
```

This launches OSBC → selects OSRS → launches RuneLite → opens the bot GUI.

### Workflow 2: RuneLite Already Running

```powershell
# Skip auto-launch, just open bot selection
osbc start --no-launch
```

### Workflow 3: Scripted/Headless Launch

```powershell
# Just get RuneLite running (no GUI)
osbc start --headless

# Or equivalently
osbc auto-launch
```

### Workflow 4: Capture Login Templates

```powershell
# 1. Launch RuneLite
osbc auto-launch

# 2. Wait for login screen, then record
osbc record --duration 60 --window "RuneLite"

# 3. View captures
explorer .\captures\
```

### Workflow 5: Debug a Running Game

```powershell
osbc debug
# > window    (check detection)
# > mouse     (check position)
# > screenshot (capture state)
```

---

## Python API

For developers building bots or scripts:

```python
from model.actions import orchestration

# Launch RuneLite programmatically
result = orchestration.auto_launch_runelite(
    game="OSRS",
    skip_if_running=True,
    timeout=120.0,
)

if result.success:
    print(f"RuneLite ready: {result.data['runelite_title']}")
```

---

## Troubleshooting

### "osbc" command not found

```powershell
.\venv\Scripts\Activate.ps1
uv pip install -e . --python .\venv\Scripts\python.exe
```

### Auto-launch fails

```powershell
# Check window status
osbc status -v

# Try manual approach
osbc gui  # Open OSBC manually, then use GUI to launch
```

### Window not found

```powershell
# Check exact window title
Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object ProcessName, MainWindowTitle
```

### Permission errors

```powershell
New-Item -ItemType Directory -Path .\captures -Force
```
