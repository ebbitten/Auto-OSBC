# Multi-Machine Support - Session Handoff

## Current Status (Updated Dec 27, 2025)

| Component | Status |
|-----------|--------|
| Machine profiles | ✅ `machine_profiles/default.json`, `desktop.json`, `laptop.json` |
| MachineConfig class | ✅ `src/utilities/machine_config.py` |
| CLI --profile option | ✅ `src/cli.py` |
| Sync scripts | ✅ `.claude/sync-preferences.sh` and `.bat` |
| Laptop hostname mapping | ✅ `"adamhblade": "laptop"` added |
| Desktop hostname mapping | ❌ Pending (next session) |
| User preferences exported | ❌ Pending (do this now on laptop) |

---

## NEXT SESSION: DESKTOP

### What Claude Should Do

1. **Get desktop hostname and add mapping**
   ```bash
   hostname  # Expected: DESKTOP-AGH04LJ or similar
   ```

2. **Edit `src/utilities/machine_config.py` lines 75-78**
   ```python
   hostname_map = {
       "adamhblade": "laptop",
       "desktop-agh04lj": "desktop",  # <-- Add this (lowercase)
   }
   ```

3. **Import user preferences (if exported from laptop)**
   ```bash
   cd .claude
   sync-preferences.bat import
   # Then restart Claude Code
   ```

### What User Should Do (git operations)

```bash
# Before starting Claude session:
git pull origin multi-machine

# After Claude makes edits:
git add src/utilities/machine_config.py
git commit -m "Add desktop hostname mapping"
git push origin multi-machine
```

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
| `desktop-agh04lj` | `desktop` | ❌ Add next session |

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
