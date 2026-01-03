# Multi-Machine Support - Session Handoff

## Current Status (Updated Jan 3, 2026)

| Component | Status |
|-----------|--------|
| Machine profiles | ✅ `machine_profiles/default.json`, `desktop.json`, `laptop.json` |
| MachineConfig class | ✅ `src/utilities/machine_config.py` |
| CLI --profile option | ✅ `src/cli.py` |
| Sync scripts | ✅ `.claude/sync-preferences.sh` and `.bat` |
| Per-machine templates | ✅ `machine_profiles/desktop/images/` created |
| FancyZones config | ✅ (57, 0) at 958x1087 in `desktop.json` |
| BotWindowService | ✅ Centralized window detection |
| State detection | ✅ **FIXED** - confidence threshold corrected |
| E2E Tests (resilience) | ✅ 8 passed, 7 skipped (with bot window) |
| E2E Tests (launch/login) | ✅ Created, marked with `@pytest.mark.launch` |
| Window detection | ✅ **FIXED** - only detects bot's window |

---

## COMPLETED: BotWindowService Refactor

### The Problem (SOLVED)
Window detection was scattered across 20+ files. The bot accidentally interacted with the user's personal RuneLite window ("RuneLite - goa hellbit") instead of only the bot's window.

### The Solution (IMPLEMENTED)
Created centralized `BotWindowService` singleton at `src/utilities/bot_window_service.py`:
- Knows which window belongs to the bot (via `OSBC_USERNAME` from .env)
- Single source of truth for window detection
- Never returns or interacts with user's personal windows

### Files Updated
1. ✅ **CREATED** `src/utilities/bot_window_service.py` - Core service
2. ✅ **UPDATED** `src/model/system_state.py` - Uses service for window detection
3. ✅ **UPDATED** `src/model/actions/go_action.py` - Uses service for Window instantiation
4. ✅ **UPDATED** `src/model/actions/osbc.py` - Uses service in `check_windows_status()`
5. ✅ **UPDATED** `src/model/actions/orchestration.py` - Uses service instead of `find_runelite_by_character()`
6. ✅ **UPDATED** `tests/e2e/conftest.py` - Uses service, skips if bot window not running
7. ✅ **UPDATED** `tests/e2e/test_launch_login.py` - Marked with `@pytest.mark.launch`

### Test Commands
```bash
# Run resilience tests (safe - won't launch anything)
pytest tests/e2e/ -m "not launch" -v

# Run launch tests (WILL launch OSBC/RuneLite)
pytest tests/e2e/test_launch_login.py -m launch -v
```

---

## NEXT SESSION: Per-Machine Templates & Window Sizing

### Context
E2E tests fail because UI templates don't match. Root cause:
1. Templates captured at different window size/resolution
2. Window size not consistently enforced on launch
3. All machines share same templates, but display characteristics differ

### Plan File
Full plan available at: `.claude/plans/groovy-booping-thunder.md`

### What Claude Should Do

**QUESTION TO ANSWER FIRST**: What window size should RuneLite use on desktop?
- Bot zone is 1280px wide (left third of 3840x1080 ultrawide)
- Options: Full zone (1280x1080), Fixed mode (773x534), or custom size
- User needs to answer this before proceeding

**After user answers window size question:**

1. **Part 1: Fix Window Sizing**
   - Update `desktop.json` with target window size
   - Modify `orchestration.py` to use fixed size instead of zone dimensions
   - Test that window launches at correct size

2. **Part 2: Per-Machine Template System**
   - Add `get_template_path(category, filename)` to `imagesearch.py`
   - Check machine-specific path first, fall back to default
   - Update `login_screen.py` and `window.py` to use new function
   - Create `machine_profiles/desktop/images/` directory

3. **Part 3: Capture Desktop Templates**
   - Launch RuneLite at fixed size
   - Capture new templates for login screens
   - Capture new templates for UI elements (minimap, chat, control panel)
   - Store in `machine_profiles/desktop/images/`

4. **Part 4: Verify**
   - Run E2E tests
   - Verify state detection works
   - Verify template matching confidence levels

### Key Files to Modify
- `machine_profiles/desktop.json` - Add target window size
- `src/utilities/imagesearch.py` - Add `get_template_path()` function
- `src/model/login/login_screen.py` - Use per-machine templates
- `src/utilities/window.py` - Use per-machine templates
- `src/model/actions/orchestration.py` - Use target size from config

### What Was Already Fixed This Session
- `tests/e2e/conftest.py`: `require_runelite` fixture now auto-launches RuneLite via `auto_launch_runelite()` instead of skipping tests
- `src/utilities/window.py`: Fixed `tab_width` bug in `__locate_cp_tabs()` - was looking for it per-row but it's at top level
- `.env`: Created with `OSBC_USERNAME` and `OSBC_PASSWORD` credentials

### Template System Details (from exploration)
- `BOT_IMAGES` defined in `imagesearch.py` as `src/images/bot/`
- `LOGIN_IMAGES_PATH` hardcoded in `login_screen.py`
- Template cache exists in `imagesearch.py` for performance
- Proposed: Check `machine_profiles/{machine}/images/{category}/{filename}` first, fall back to `src/images/bot/`

---

## Key Information

### Two Types of Settings (Important!)

| Type | Location | Sync Method |
|------|----------|-------------|
| **Project Permissions** | `.claude/settings.json`, `.claude/settings.local.json` | Already in git, syncs automatically |
| **User Preferences** | `AppData/.../Code/User/` | Use sync-preferences scripts |

Project permissions (the ones with all the Bash patterns) are already version-controlled!

### Hostname Mappings

| Hostname | Profile | Machine |
|----------|---------|---------|
| `adamhblade` | `laptop` | ✅ Added |
| `desktop-agh04lj` | `desktop` | ✅ Added |

The code lowercases hostnames automatically, so use lowercase in the mapping.

### Machine Profiles Location

```
machine_profiles/
├── default.json   # Fallback config
├── desktop.json   # 1920x1080, DPI 1.0
└── laptop.json    # 1366x768, DPI 1.25
```

---

## Reference: Sync Commands

### Export Preferences (source machine)
```bash
cd .claude
./sync-preferences.sh export   # Linux/Git Bash
sync-preferences.bat export    # Windows CMD
```

### Import Preferences (target machine)
```bash
cd .claude
./sync-preferences.sh import   # Linux/Git Bash
sync-preferences.bat import    # Windows CMD
# Restart Claude Code after import!
```

### Check Status
```bash
cd .claude
./sync-preferences.sh status
```

---

## Architecture Summary

The `MachineConfig` class (`src/utilities/machine_config.py`):
1. Auto-detects machine via hostname
2. Loads appropriate JSON profile from `machine_profiles/`
3. Falls back to `default.json` if no match
4. Can be overridden via `OSBC_MACHINE_PROFILE` env var or `--profile` CLI arg

Usage:
```bash
osbc status                    # Auto-detect profile
osbc --profile desktop status  # Force specific profile
OSBC_MACHINE_PROFILE=laptop osbc status  # Via env var
```
