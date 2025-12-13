# Smart Reference Tree - Navigation Guide

## When Working On: Backlog Management

### If: Need to Prioritize Future Work
**Look At**:
- `docs/backlog/BACK-001-testability-framework.md` - Testing infrastructure (HIGH priority)
- `docs/backlog/BACK-002-debug-infrastructure.md` - Debug improvements (MEDIUM priority) 
- `docs/backlog/BACK-003-bot-development-tools.md` - Dev tools (LOW priority)
- `docs/backlog/BACK-004-framework-enhancements.md` - Architecture changes (LOW priority)
- `docs/backlog/BACK-005-documentation-cleanup.md` - Doc alignment (MEDIUM priority)

### If: Planning Implementation Phases
**Look At**:
- Each backlog ticket has effort estimates and dependencies
- BACK-001 (testability) is foundation for most other work
- BACK-005 (doc cleanup) should happen after major features

## When Working On: Multi-OS Compatibility

### If: Dependency Issues
**Look At**:
- `requirements.txt` - Current dependency list
- `setup.py` - Alternative dependency specification  
- `pyproject.toml` - Modern Python project config

### If: Window Management Problems
**Look At**:
- `src/utilities/window.py` - Core window detection/management
- Dependencies: `PyWinCtl==0.0.42` in requirements.txt
- Usage: Search for `pywinctl` imports across codebase

### If: Threading Issues Across OS
**Look At**:  
- `src/model/bot.py:57-66` - Platform-specific thread termination
- Method: `BotThread.stop()` - already handles Windows vs Linux

### If: Game Launcher Problems
**Look At**:
- `src/utilities/game_launcher.py:114-119` - OS-specific process spawning
- Current: Windows vs everything else (needs Ubuntu-specific validation)

### If: Input/Output System Issues  
**Look At**:
- `PyAutoGUI` usage throughout codebase (search for `pag.` or `pyautogui`)
- Mouse: `src/utilities/mouse.py` 
- Keyboard: Search for keyboard input methods
- Linux-specific: `evdev`, `python-xlib` in requirements.txt

## When Working On: Testing/Validation

### If: Need to Test Cross-Platform
**Look At**:
- No existing test framework (tests/ directory empty)
- Manual testing required for each OS
- Debug tools: `scripts/debug_console.py`, `scripts/manual_capture.py`

### If: Need Installation Scripts  
**Look At**:
- Current: Only `setup.py` exists
- Missing: Platform-specific install scripts
- Consider: Dockerfile, shell scripts for Ubuntu, batch files for Windows

## When Working On: Architecture Understanding

### If: Need System Overview
**Look At**:
- `docs/current-state.md` - Comprehensive architecture doc
- Core components: Bot framework, Window management, Computer vision
- Not needed for multi-OS work unless modifying core architecture

### If: Need Development Process
**Look At**:  
- `CLAUDE.md` - Development roadmap (ignore for multi-OS focus)
- `docs/development-workflow.md` - TDD process (not relevant for multi-OS)

## Decision Tree: What to Check First

```
Problem with multi-OS? 
├── Dependencies not installing?
│   └── → requirements.txt + OS-specific package managers
├── Window detection failing?  
│   └── → src/utilities/window.py + PyWinCtl compatibility
├── Bot crashes on startup?
│   └── → src/model/bot.py threading + OS-specific libraries  
├── Game launcher not working?
│   └── → src/utilities/game_launcher.py platform detection
└── Input/mouse not working?
    └── → PyAutoGUI compatibility + Linux input libs (evdev, xlib)
```

## File Locations Quick Reference

**Core Multi-OS Code**:
- `src/model/bot.py:57-66` - Thread management  
- `src/utilities/window.py:13` - Window detection
- `src/utilities/game_launcher.py:114-119` - Process spawning

**Dependencies**:
- `requirements.txt` - All current dependencies
- `setup.py` - Alternative dep specification

**OS-Specific Libraries** (problematic):
- `evdev` - Linux input events
- `python-xlib`, `python3-xlib` - X11 bindings  
- `PyWinCtl` - Cross-platform window control (verify compatibility)

**Testing Tools** (for validation):
- `scripts/debug_console.py` - Interactive debugging
- `scripts/manual_capture.py` - Screenshot capture for testing