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
| `click_to_play.png` | Post-login "Click to Play" button |

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

## 9. Known Issues & Gotchas

### Template False Positives (RESOLVED)
The login templates at 0.8 confidence were matching inventory slots on the logged-in screen.

**Root cause (5 Whys analysis):**
- 0.8 threshold cargo-culted from other bots without validation
- Full-screen search instead of region-constrained search
- Mock-only tests didn't catch real-world false positives

**Solution implemented:**
1. Detection order: Check `is_logged_in()` FIRST before template matching
2. Structural validation: Welcome screen requires BOTH buttons at same Y position
3. Cancel button check: Distinguishes LOGIN from WELCOME screen

### Detection Order (Current)
```
1. LOGGED_IN         ← Check FIRST to avoid template false positives
2. WELCOME_SCREEN    ← Structural validation (both buttons at same Y)
3. LOGIN_SCREEN      ← Requires cancel button present
4. CLICK_TO_PLAY
5. UNKNOWN
```

### Remaining Technical Debt
See backlog for systemic fixes:
- Visual test fixtures needed
- Confidence thresholds inconsistent across codebase
- Region constraints not used in login detection

---

## 10. Backlog

### Completed
- [x] Create `click_to_play.png` template
- [x] **TICKET-1: Visual Test Fixtures** - Created `tests/fixtures/login_states/` with WELCOME, LOGIN, LOGGED_IN screenshots
- [x] **TICKET-5: Integration Tests with Real Screenshots** - Created `tests/integration/test_login_detection_visual.py` (8 tests)
- [x] **TICKET-2: Standardize Confidence Thresholds** - Added CONFIDENCE_STRICT/MODERATE/LOOSE constants to `imagesearch.py`, updated `login_screen.py` and `bot.py`
- [x] **TICKET-3: Region Constraints for Login Detection** - Added `use_center_region` parameter to `_search_template()`, all login buttons now search center 60% only

### High Priority (from 5 Whys analysis)
(None remaining)

### Medium Priority
- [ ] Improve template uniqueness (capture more distinct regions)
- [ ] Profile and optimize Window.initialize() (still ~280ms)

### Low Priority
- [ ] **TICKET-4: State Transition Validation** - Add valid transition map, reject impossible transitions
- [ ] Add CONNECTION_ERROR state handling
- [ ] Add ACCOUNT_LOCKED state handling
- [ ] Add more chaos scenarios to resilience tests

---

## 11. Quick Verification Commands

```bash
# Check current state
./venv/Scripts/python -m src.cli status

# Test go command (will fail on bad credentials, but should detect states correctly)
./venv/Scripts/python -m src.cli go --timeout 15

# Run all tests
./venv/Scripts/pytest tests/ -q --tb=no

# Run E2E tests only
./venv/Scripts/pytest tests/e2e/ -v

# Profile detection performance
./venv/Scripts/python scripts/flow_profiler.py --detection-only

# Test individual template
./venv/Scripts/python scripts/recorder.py --test-template src/images/bot/login/existing_user_button.png --window "RuneLite"
```
