# Session Resume - Auto-OSBC

## Current State (2025-12-25)

Both major tracks are now **COMPLETE**:

| Track | Status |
|-------|--------|
| Permission patterns | VERIFIED WORKING |
| Login automation | WORKING END-TO-END |
| Unit tests | 253/253 passing |

---

## 1. Permission Patterns (COMPLETE)

### What Works Without Prompts
- `python scripts/...` - All Python scripts
- `./venv/Scripts/python ...` - Venv Python
- `pytest ...` - All test commands
- `osbc ...` - All CLI commands
- `git status/log/diff/branch` - Read-only git
- File ops (`ls`, `cat`, `dir`, etc.)

### What Still Prompts (Human Control)
- `git add` / `git commit` / `git push` / `git checkout`

### Key File
`.claude/settings.local.json` - 20 wildcard patterns

---

## 2. Login Automation (COMPLETE)

### CLI Commands
```bash
osbc start --headless   # Launch OSBC + RuneLite
osbc login              # Automated login (uses .env credentials)
osbc status             # Check window status
```

### Templates (in `src/images/bot/login/`)
| Template | Size | Purpose |
|----------|------|---------|
| `existing_user_button.png` | 150x40 | Detect/click "Existing User" on welcome screen |
| `welcome_to_runescape.png` | 300x30 | Confirm we're on welcome screen |
| `login_button.png` | 80x30 | Detect/click "Login" on credentials form |

### Bugs Fixed This Session
| File | Fix |
|------|-----|
| `scripts/recorder.py` | Unicode encoding (`[OK]` instead of checkmark) |
| `src/model/login/login_screen.py` | Detection priority (check login_button before existing_user) |
| `src/model/login/login_service.py` | Relaxed field requirements (only need login_button, not username_field) |

### Login State Machine
```
UNKNOWN
    |
WELCOME_SCREEN --> click "Existing User"
    |
LOGIN_SCREEN --> type credentials, click "Login"
    |
LOGGED_IN
```

---

## 3. Key Code Locations

| What | Where |
|------|-------|
| CLI entry point | `src/cli.py` |
| Login state machine | `src/model/login/login_screen.py` |
| Login orchestration | `src/model/login/login_service.py` |
| Template images | `src/images/bot/login/` |
| Recorder script | `scripts/recorder.py` |
| Permission settings | `.claude/settings.local.json` |

---

## 4. Template Creation Workflow

If you need to create new templates:

```bash
# 1. List existing templates
python scripts/recorder.py --list-templates

# 2. Capture interactive screenshot with grid
python scripts/recorder.py --interactive --window "RuneLite"

# 3. View the gridded image to find coordinates
# (saved to captures/interactive/)

# 4. Extract template region
python scripts/recorder.py --from-session captures/interactive --extract-template X,Y,W,H,name

# 5. Test if template matches
python scripts/recorder.py --test-template src/images/bot/login/name.png --window "RuneLite"
```

---

## 5. Environment Requirements

- Windows with RuneLite installed
- Python 3.10 venv at `.\venv\`
- `.env` file with `OSBC_USERNAME` and `OSBC_PASSWORD`
- OSBC installed (for `osbc start` to work)

---

## 6. Git Status

Branch: `claude-windows`

Uncommitted changes:
- Login module (`src/model/login/`)
- CLI (`src/cli.py`)
- Recorder script (`scripts/recorder.py`)
- Templates (`src/images/bot/login/`)
- Test files
- Bug fixes from this session

**Ready to commit** - login flow is working end-to-end.

---

## 7. Next Steps (Future Work)

Potential improvements:
- Add more error state detection (CONNECTION_ERROR, ACCOUNT_LOCKED, etc.)
- Add CLICK_TO_PLAY and LOBBY state handling
- Improve username field OCR detection (currently works without it)
- Add retry logic for template matching failures
