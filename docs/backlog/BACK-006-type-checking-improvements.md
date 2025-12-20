# BACK-006: Type Checking Improvements

## Epic Overview
**Priority**: Low
**Effort**: Small (1-2 weeks)
**Status**: Not Started
**Dependencies**: None

## Problem Statement
During WSL2 development session, mypy type checking revealed 13 errors across 8 files:
- Missing type stubs for third-party libraries (`pyautogui`, `customtkinter`, `pytweening`)
- Module path conflicts (e.g., `events_server.py` found under multiple names)
- Import resolution issues affecting type safety

While type checking is non-critical for runtime functionality, it provides:
- Better IDE autocomplete and intellisense
- Early detection of type-related bugs
- Improved code maintainability
- Better developer experience

## Success Criteria
- [ ] Mypy runs without errors on `src/` directory
- [ ] All required type stubs installed
- [ ] Module path conflicts resolved
- [ ] Type checking integrated into CI/CD quality gates
- [ ] Development documentation updated with type checking workflow

## Implementation Breakdown

### Sub-Task 1: Install Missing Type Stubs
**Effort**: 1 day
- ✅ `types-PyAutoGUI` - Added to requirements.txt
- ✅ `types-Deprecated` - Added to requirements.txt
- [ ] `types-customtkinter` - Check if available or create custom stubs
- [ ] `types-pytweening` - Check if available or create custom stubs
- [ ] Verify all stubs resolve mypy errors

### Sub-Task 2: Fix Module Path Conflicts
**Effort**: 2-3 days
- [ ] Investigate `events_server.py` multiple name resolution issue
- [ ] Add `__init__.py` files to ensure proper package structure
- [ ] Use `--explicit-package-bases` flag if needed
- [ ] Refactor import paths to be consistent

### Sub-Task 3: Add Type Annotations
**Effort**: 3-5 days
- [ ] Add type hints to functions missing annotations
- [ ] Use `typing` module for complex types (List, Dict, Optional, etc.)
- [ ] Add return type annotations to all public methods
- [ ] Document complex type signatures

### Sub-Task 4: CI/CD Integration
**Effort**: 1 day
- [ ] Add mypy check to pre-commit hooks
- [ ] Configure mypy.ini or pyproject.toml for project settings
- [ ] Add mypy to test/quality gate scripts
- [ ] Document mypy workflow in development guides

## Technical Requirements

### Type Checking Configuration
Create `mypy.ini` or add to `pyproject.toml`:
```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Start permissive, tighten over time
ignore_missing_imports = False
explicit_package_bases = True

[mypy-tests.*]
disallow_untyped_defs = False  # More lenient for tests
```

### Development Dependencies
Already added to `requirements.txt`:
- `mypy==1.13.0`
- `types-PyAutoGUI==0.9.3`
- `types-Deprecated==1.2.10`

### Commands for Type Checking
```bash
# Run mypy on source code
mypy src/

# Run with verbose output for debugging
mypy src/ --verbose

# Check specific files
mypy src/utilities/platform_utils.py

# Generate HTML coverage report
mypy src/ --html-report ./mypy-report
```

## Acceptance Criteria

### Functional Requirements
- Mypy completes without errors on entire `src/` directory
- Type stubs available for all third-party libraries used
- Module imports resolve correctly without path conflicts
- Type hints added to core framework components

### Non-Functional Requirements
- Type checking completes in < 30 seconds
- No false positives requiring `# type: ignore` comments (unless justified)
- Clear error messages for legitimate type issues
- Documentation explains how to run and interpret mypy results

## Known Issues from WSL2 Session

### Original Mypy Error Summary (13 errors in 8 files):
1. **Missing imports**: `pyautogui`, `customtkinter`, `deprecated`, `pytweening`
2. **Module paths**: `events_server.py` duplicate name detection
3. **Import resolution**: Packages not found in expected locations

### Files Affected:
- Framework utilities (color detection, geometry, platform utils)
- Bot base classes
- Game launcher components
- Test infrastructure

## Blocked Dependencies
- **None currently** - can be implemented independently

## Future Enhancements (Not in Scope)
- Strict type checking mode (`disallow_untyped_defs = True`)
- Protocol-based type checking for duck typing
- Type checking for test files
- Advanced generic types and type variables
- Integration with IDE type checking (VSCode, PyCharm)

## Definition of Done
- [ ] `mypy src/` runs without errors
- [ ] All type stubs documented in requirements.txt
- [ ] Type checking added to CI/CD pipeline
- [ ] Developer documentation includes type checking guidelines
- [ ] At least one example bot demonstrates proper type annotation patterns

---

**Source**: WSL2_SESSION_NOTES.md (lines 52-67)
**Related**: BACK-001 (Testing Framework), quality gates in development workflow
**Date Created**: 2025-12-15
