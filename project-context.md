# Claude Code Testing Workflow - bump.md

**Project Context:** Python hobby project on Windows 11, using Claude Code in VSCode terminal

---

## CURRENT STATE

### What Works
- ✅ Test scripts exist and are functional (unit & integration tests)
- ✅ VSCode terminal accessible
- ✅ Claude Code connected and operational

### What Doesn't Work
- ❌ Claude keeps asking permission to run tests (should auto-run)
- ❌ Claude recreates inline Python scripts instead of using existing test files
- ❌ Preference file changes don't persist between sessions
- ❌ Permission prompts appear even after "fixing" the issue

### Explicit Unknowns
- Exact location of Claude Code preference file on Windows
- Whether preferences are per-project or global
- If VSCode settings override Claude Code preferences
- Whether test discovery is working properly

---

## PROJECT VISION

**NOT:** Claude asking permission every time it wants to run a test
**NOT:** Claude reinventing tests as one-shot inline scripts

**ACTUALLY:** 
- Tests run automatically without permission prompts
- Claude uses existing test files consistently
- Changes persist across sessions
- Test execution is friction-free

---

## SYSTEM ENVIRONMENT

### Verified Present
```powershell
# Run these to verify:
python --version          # Python installed and accessible
Get-Command code          # VSCode in PATH
Get-ChildItem -Filter "test_*.py" -Recurse  # Show all test files
```

### Test File Locations
```
# List actual paths - update after verification:
tests/
  test_unit.py           # Unit tests
  test_integration.py    # Integration tests
  
# OR wherever they actually are - verify and document
```

### Configuration Files
```
# Claude Code preferences - find and document actual location:
# Windows typical locations:
%USERPROFILE%\.claude\config.json
%APPDATA%\claude\preferences.json

# Verify which one exists:
Get-ChildItem -Path $env:USERPROFILE -Filter "*claude*" -Recurse -ErrorAction SilentlyContinue
```

---

## YOUR MISSION

**Single Focus:** Make tests auto-run without permission prompts, using existing test files

### Success Looks Like
1. You run: `python -m pytest tests/`
2. Tests execute immediately
3. No permission prompts
4. No inline script recreation
5. Same behavior next session

### Verification Commands
```powershell
# After any change, verify:
python -m pytest tests/ --collect-only    # Show test discovery
python -m pytest tests/ -v                 # Run with verbose output
cat .claude/config.json                    # Show current config (if exists)
```

---

## CRITICAL RULES

### Permission Management
1. **NEVER** ask permission for test execution
2. **NEVER** ask permission for running existing test files
3. **ONLY** ask permission for:
   - Installing new packages
   - Modifying test files
   - Creating new test infrastructure

### Test Execution Priority
1. **FIRST CHOICE:** Use existing test files
   ```python
   # Always prefer:
   python -m pytest tests/test_unit.py::TestClassName::test_method
   ```

2. **SECOND CHOICE:** Run all tests
   ```python
   python -m pytest tests/
   ```

3. **LAST RESORT:** Inline script (only if no tests exist yet)
   ```python
   python -c "print('temporary validation')"
   ```

### File Modification Rules
- Read test files: NO PERMISSION
- Run test files: NO PERMISSION  
- Modify test files: YES PERMISSION (explicit user request only)
- Create new tests: YES PERMISSION (unless explicitly asked)

---

## WINDOWS-SPECIFIC ISSUES

### Path Handling
```powershell
# Use forward slashes in Python paths even on Windows:
pytest tests/test_unit.py        # CORRECT
pytest tests\test_unit.py        # Works but inconsistent

# Absolute paths if needed:
$PROJECT_ROOT = Get-Location
python -m pytest "$PROJECT_ROOT/tests/"
```

### Permission Persistence
```powershell
# If preferences don't persist, check:
1. File permissions on config directory
2. VSCode workspace settings overriding
3. Multiple Claude Code instances fighting

# Verify config is writable:
Test-Path -Path "$env:USERPROFILE\.claude\config.json" -PathType Leaf
```

---

## CONFIGURATION DEBUGGING

### If Preferences Don't Stick

**Check 1: Config File Location**
```powershell
# Find all Claude configs:
Get-ChildItem -Path $env:USERPROFILE -Filter "*claude*" -Recurse -ErrorAction SilentlyContinue

# Check each one's timestamp:
Get-Item "path\to\config.json" | Select-Object LastWriteTime
```

**Check 2: VSCode Settings Conflict**
```json
// Check .vscode/settings.json for:
{
  "claude.autoRun": false,  // If this exists, it overrides
  "python.testing.autoTestDiscoverOnSaveEnabled": false
}
```

**Check 3: Multiple Config Sources**
```
Priority (highest first):
1. Project .claude/config.json
2. VSCode workspace settings
3. User-level Claude config
4. Global defaults
```

### Proper Auto-Run Config
```json
{
  "autoApprove": {
    "enabled": true,
    "patterns": [
      "pytest*",
      "python -m pytest*",
      "python tests/*",
      "python -m unittest*"
    ]
  },
  "alwaysAllowCommands": [
    "pytest",
    "python -m pytest"
  ]
}
```

---

## TROUBLESHOOTING CHECKLIST

When permission prompts reappear:

- [ ] Check config file timestamp (did it revert?)
- [ ] Verify pytest is installed: `pip list | Select-String pytest`
- [ ] Confirm test discovery works: `pytest --collect-only`
- [ ] Check for workspace-level settings override
- [ ] Restart Claude Code session (config might need reload)
- [ ] Check if VSCode Python extension is interfering

---

## WORK SESSIONS

### Session Template
```markdown
**Date:** YYYY-MM-DD
**Issue:** [what triggered this session]
**Changes Made:**
- [specific file changes]
- [configuration updates]
**Verification:**
- [what commands were run]
- [what output confirmed success]
**Status:** [Working / Broken / Partially Fixed]
**Next:** [what to try if issue reappears]
```

---

## FOR FUTURE CLAUDE INSTANCES

### When You First Read This

1. **DO FIRST:**
   ```powershell
   # Verify test structure
   Get-ChildItem -Filter "test_*.py" -Recurse
   
   # Check current config
   Get-Content "$env:USERPROFILE\.claude\config.json" -ErrorAction SilentlyContinue
   
   # Test auto-run status
   python -m pytest tests/ -v
   ```

2. **EXPECT:** You might ask for permission. This is the bug we're fixing.

3. **YOUR JOB:** 
   - Fix the config so you DON'T ask permission next time
   - Document what you changed
   - Verify it worked
   - Update this document if you discover new information

### When Tests Need to Run

**Decision Tree:**
```
Do test files exist?
├─ YES → Use them directly (python -m pytest tests/)
│         NO permission needed
└─ NO → Ask user: "Should I create proper test files?"
          (Don't create inline scripts)
```

### When Permission Prompt Appears

**This means the fix didn't work. Debug:**
1. What command triggered the prompt?
2. Is that command in autoApprove patterns?
3. Does config file still contain our changes?
4. Is there a workspace setting overriding?
5. Document findings in Work Sessions below

---

## KNOWN ISSUES

### Issue 1: Config Changes Don't Persist
**Symptom:** Permission prompts return after fixing
**Cause:** Unknown - investigating
**Current Theory:** 
- Multiple config sources fighting?
- VSCode workspace settings override?
- Config file not being saved properly?

**Debug Steps Tried:**
- [ ] Manual config edit and verification
- [ ] Check file permissions
- [ ] Look for workspace-level overrides
- [ ] Verify config syntax validity

### Issue 2: Inline Scripts Instead of Test Files
**Symptom:** Claude creates `python -c "..."` instead of using test files
**Root Cause:** Claude defaults to quickest validation path
**Solution:** This bump.md explicitly prioritizes existing test files

---

## SUCCESS CRITERIA

**Tomorrow's Test:**
1. You read this document
2. User says "run the tests"
3. You execute: `python -m pytest tests/` 
4. Tests run immediately (no permission prompt)
5. You report results
6. Next session: Same behavior

**If you fail Tomorrow's Test:**
- Something is still broken
- Update this document with what you learned
- Try the next debugging approach

---

## WORK SESSION LOG

### Most Recent First

**Session: [PENDING - YOUR FIRST SESSION]**
- Read this document completely
- Run verification commands
- Document current state
- Make configuration changes
- Verify they work
- Update this section with results

---

## APPENDIX: Quick Reference

### Run Tests (No Permission)
```powershell
python -m pytest tests/                    # All tests
python -m pytest tests/test_unit.py        # Specific file  
python -m pytest tests/ -k test_function   # By name
python -m pytest tests/ -v                 # Verbose
```

### Verify Configuration
```powershell
Get-Content "$env:USERPROFILE\.claude\config.json"
Get-Content .vscode/settings.json
Test-Path tests/test_*.py
```

### When Everything Breaks
```powershell
# Nuclear option:
# 1. Back up config
Copy-Item "$env:USERPROFILE\.claude\config.json" backup-config.json

# 2. Reset to minimal config
@"
{
  "autoApprove": {
    "enabled": true,
    "patterns": ["pytest*", "python -m pytest*"]
  }
}
"@ | Out-File "$env:USERPROFILE\.claude\config.json" -Encoding utf8

# 3. Restart Claude Code
# 4. Test
```

---

**Remember:** The goal is ZERO PERMISSION PROMPTS for test execution. If you're asking permission to run tests, the fix isn't working yet.
