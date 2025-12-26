# Session Resume - Auto-OSBC

## Current State (2025-12-26)

All major tracks are **COMPLETE**:

| Track | Status |
|-------|--------|
| Permission patterns | VERIFIED WORKING |
| Login automation | WORKING END-TO-END |
| `osbc go` unified flow | WORKING |
| Performance optimization | 85% faster detection |
| Unit tests | 397/397 passing |
| E2E resilience tests | 8/8 passing |

---

## 1. Unified `osbc go` Command (NEW)

The `go` command handles the complete flow from any starting state:

```bash
osbc go                    # Full flow: launch + login
osbc go --skip-login       # Stop at login screen
osbc go --force-restart    # Close all windows first
osbc go --timeout 120      # Custom timeout
```

### State Machine
```
NO_WINDOWS ──► Launch OSBC
     │
OSBC_ONLY ──► Click "Launch RuneLite"
     │
RUNELITE_LAUNCHER ──► Wait for load
     │
RUNELITE_WELCOME ──► Click "Existing User"
     │
RUNELITE_LOGIN ──► Enter credentials
     │
RUNELITE_INVALID_CREDENTIALS ──► Click "Try again" (once)
     │
RUNELITE_CLICK_TO_PLAY ──► Click to enter game
     │
RUNELITE_LOGGED_IN ──► Success!
```

---

## 2. Performance Optimization (NEW)

### Results
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| `full_detect_state` | ~480ms | 74ms | **85% faster** |
| Template match | 65-90ms | 20-30ms | 60% faster |

### Optimizations Applied
1. **Template caching** - `imagesearch.py` caches loaded images (no disk I/O per search)
2. **Screenshot caching** - `login_screen.py` captures once per detect() call
3. **Detection reordering** - Cheap checks first, expensive `is_logged_in()` last
4. **Redundant search elimination** - `_check_welcome_screen()` returns button location

---

## 3. Testing Tools (NEW)

### Flow Profiler
```bash
python scripts/flow_profiler.py --detection-only   # Profile state detection
python scripts/flow_profiler.py --output results.json
```

### Resilience Tests
```bash
pytest tests/e2e/test_go_resilience.py -v          # Run all E2E tests
python tests/e2e/test_go_resilience.py --chaos-monkey --probability 0.3
```

### Test Hooks (for chaos injection)
```python
go(
    on_before_detect=lambda: ...,
    on_after_detect=lambda state: ...,
    on_before_action=lambda action: ...,
)
```

---

## 4. Key Code Locations

| What | Where |
|------|-------|
| CLI entry point | `src/cli.py` |
| Unified go action | `src/model/actions/go_action.py` |
| Login state machine | `src/model/login/login_screen.py` |
| Login orchestration | `src/model/login/login_service.py` |
| System state detection | `src/model/system_state.py` |
| Template images | `src/images/bot/login/` |
| Image search (cached) | `src/utilities/imagesearch.py` |
| Flow profiler | `scripts/flow_profiler.py` |
| Resilience tests | `tests/e2e/test_go_resilience.py` |
| E2E fixtures | `tests/e2e/conftest.py` |
| Permission settings | `.claude/settings.local.json` |

---

## 5. Templates (in `src/images/bot/login/`)

| Template | Purpose |
|----------|---------|
| `existing_user_button.png` | Detect/click "Existing User" on welcome screen |
| `new_user_button.png` | Validate welcome screen structure |
| `login_button.png` | Detect/click "Login" on credentials form |
| `cancel_button.png` | Distinguish login screen from welcome screen |
| `try_again_button.png` | Detect invalid credentials screen |
| `click_to_play.png` | Post-login "Click to Play" button (TODO: create) |

---

## 6. Permission Patterns (COMPLETE)

### What Works Without Prompts
- `python scripts/...` - All Python scripts
- `./venv/Scripts/python ...` - Venv Python
- `./venv/Scripts/pytest ...` - All test commands
- `osbc ...` - All CLI commands
- `git status/log/diff/branch` - Read-only git
- File ops (`ls`, `cat`, `dir`, etc.)

### What Still Prompts (Human Control)
- `git add` / `git commit` / `git push` / `git checkout`

---

## 7. Environment Requirements

- Windows with RuneLite installed
- Python 3.10 venv at `.\venv\`
- `.env` file with `OSBC_USERNAME` and `OSBC_PASSWORD`
- OSBC installed (for `osbc start` to work)

---

## 8. Git Status

Branch: `claude-windows`

Recent work:
- Unified `osbc go` command
- Flow profiler and resilience testing
- Performance optimizations (template/screenshot caching)
- Detection order optimization

---

## 9. Next Steps (Future Work)

- [ ] Create `click_to_play.png` template
- [ ] Add CONNECTION_ERROR state handling
- [ ] Add ACCOUNT_LOCKED state handling
- [ ] Profile and optimize Window.initialize() (still ~280ms)
- [ ] Add more chaos scenarios to resilience tests
