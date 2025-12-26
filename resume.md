# Session Resume - Permission Test Required

## FIRST THING TO DO (After Session Restart)

Run this test sequence to verify permissions work:

```bash
# 1. Script test (should run WITHOUT prompt)
python scripts/recorder.py --list-templates

# 2. CLI test (should run WITHOUT prompt)
osbc status

# 3. Pytest test (should run WITHOUT prompt)
pytest tests/unit/actions/test_window.py -v --tb=no

# 4. Git read test (should run WITHOUT prompt)
git status

# 5. Git write test (SHOULD PROMPT - human control)
git add .claude/settings.local.json
```

**Note on Python commands:** Use `python scripts/...` (not full absolute paths like `"C:/Users/.../python.exe"`). The patterns are set up to match:
- `python ...`
- `venv/Scripts/python ...`
- `./venv/Scripts/python ...`

**Expected Results:**
- Tests 1-4: Run immediately, no permission prompts
- Test 5: Prompts for permission (git write operations stay under human control)

If any of 1-4 prompt for permission, the fix didn't work and we need to debug.

---

## Current State

We've been working on two parallel tracks:
1. **Permission pattern fix** - Simplified to 18 clean patterns
2. **Login automation** - Building templates for automated login flow

---

## 1. Permission Pattern Fix (PENDING TEST)

### The Problem
Claude Code kept asking for permission to run Python scripts despite 100+ specific patterns.

### Solution: Simplified Patterns
Replaced 100+ complex path-specific patterns with 18 simple wildcards:

```json
{
  "permissions": {
    "allow": [
      "Bash(python:*)",      // Any python command
      "Bash(pytest:*)",      // Any pytest command
      "Bash(osbc:*)",        // Any osbc CLI command
      "Bash(git status:*)",  // Read-only git
      "Bash(git log:*)",
      "Bash(git diff:*)",
      "Bash(git branch:*)",
      // ... file ops (ls, cat, etc.)
    ]
  }
}
```

### Git Control (Human Only)
NOT in allow list (will still prompt):
- `git add` / `git commit` / `git push` / `git checkout`

### Behavior Change
Also updated `CLAUDE.md` with "Available Scripts" section to encourage using scripts instead of inline Python.

---

## 2. Login Automation (IN PROGRESS)

### Architecture
The login flow uses a two-stage detection:

1. **Welcome Screen** - Initial screen with "New User" / "Existing User" buttons
2. **Login Form** - Username/password entry after clicking "Existing User"

### Files Created/Modified

#### Core Login Files
| File | Purpose |
|------|---------|
| `src/model/login/login_screen.py` | Login screen detection (state machine, template matching, OCR fallback) |
| `src/model/login/login_service.py` | High-level login orchestration |
| `src/model/actions/login_action.py` | Action wrapper for CLI |

#### Templates (in `src/images/bot/login/`)
| Template | Size | Purpose |
|----------|------|---------|
| `existing_user_button.png` | 150x40 | Detect/click "Existing User" on welcome screen |
| `welcome_to_runescape.png` | 300x30 | Confirm we're on welcome screen |

### Still Needed
- `login_button.png` - Template for the login button on the credentials form
- Test the full login flow end-to-end

### Template Creation Workflow
Use the recorder script to capture templates:

```bash
# 1. List existing templates
python scripts/recorder.py --list-templates

# 2. Capture a session (with RuneLite open to login screen)
python scripts/recorder.py --duration 5 --window "RuneLite" --interval 1000

# 3. Extract template from captured session
python scripts/recorder.py --from-session "captures/YYYY-MM-DD_HH-MM-SS" --extract-template "X,Y,WIDTH,HEIGHT,template_name"

# 4. Test if template matches
python scripts/recorder.py --test-template src/images/bot/login/template_name.png --window "RuneLite"
```

---

## 3. CLI Commands Available

The CLI has been rationalized to these commands:

| Command | Purpose |
|---------|---------|
| `osbc status` | Check if OSBC/RuneLite windows are running |
| `osbc start` | Launch OSBC → select game → launch RuneLite → open GUI |
| `osbc start --headless` | Same but without GUI |
| `osbc login` | Perform automated login on RuneLite |
| `osbc gui` | Just open the GUI |

---

## 4. To Resume Work

### Step 1: Verify Environment
```bash
cd C:\Users\adamh\VSCodeProjects\Auto-OSBC

# Activate venv
.\venv\Scripts\activate

# Verify Python works
python -c "print('OK')"

# Verify CLI works
osbc status
```

### Step 2: Start Fresh Claude Code Session
The permission fix is in the settings file but only loads at session start. Start a new Claude Code session to pick up the fix.

### Step 3: Continue Login Template Work
With RuneLite open to the login form (after clicking "Existing User"):

```bash
# Capture the login form screen
python scripts/recorder.py --duration 2 --window "RuneLite" --interval 1000

# List what was captured
dir captures\

# Extract login button template
python scripts/recorder.py --from-session "captures/LATEST" --extract-template "X,Y,W,H,login_button"
```

### Step 4: Test Login Flow
```bash
osbc login
```

---

## 5. Key Code Locations

| What | Where |
|------|-------|
| CLI entry point | `src/cli.py` |
| Login state machine | `src/model/login/login_screen.py` |
| Login orchestration | `src/model/login/login_service.py` |
| Template images | `src/images/bot/login/` |
| Recorder script | `scripts/recorder.py` |
| Permission settings | `.claude/settings.local.json` |

---

## 6. Login State Machine

```
UNKNOWN
    ↓ (detect welcome text)
WELCOME_SCREEN → click "Existing User"
    ↓
LOGIN_SCREEN → enter credentials
    ↓
CLICK_TO_PLAY (if applicable)
    ↓
LOBBY (if applicable)
    ↓
LOGGED_IN ✓
```

Error states: `CONNECTION_ERROR`, `INVALID_CREDENTIALS`, `ACCOUNT_LOCKED`, `UPDATE_REQUIRED`

---

## 7. Environment Requirements

- Windows machine with RuneLite installed
- Python 3.10 venv at `.\venv\`
- `.env` file with `OSBC_USERNAME` and `OSBC_PASSWORD` (for login automation)
- OSBC installed (for `osbc start` to work)

---

## 8. Git Status

Branch: `claude-windows`

Uncommitted changes include:
- Login module (`src/model/login/`)
- CLI (`src/cli.py`)
- Recorder script (`scripts/recorder.py`)
- Templates (`src/images/bot/login/`)
- Test files

Consider committing when login flow is working end-to-end.
