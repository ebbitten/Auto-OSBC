# Auto-OSBC Testing Guide

## Quick Start Testing

### Windows 10/11
```batch
# Run Windows-specific test suite
python test_runner_windows.py
```

### Ubuntu 20.04/22.04/24.04  
```bash
# Run Ubuntu-specific test suite
python test_runner_ubuntu.py
```

### Universal Testing
```bash
# Run all tests (any platform)
python -m pytest tests/ -v

# Run basic platform test (no dependencies required)
python test_basic_platform.py

# Run specific test categories
python -m pytest tests/platform/ -v     # Platform detection tests
python -m pytest tests/dependencies/ -v # Dependency compatibility
python -m pytest tests/integration/ -v  # Integration tests
```

## Test Categories

### 1. Platform Detection Tests (`tests/platform/`)
- **Platform identification**: Windows 10/11, Ubuntu 20.04/22.04/24.04
- **Version detection**: Accurate OS version identification
- **WSL2 detection**: Identifies WSL2 environment and limitations
- **Installation validation**: Verifies installation scripts work

### 2. Dependency Tests (`tests/dependencies/`)
- **Core imports**: numpy, OpenCV, PIL, PyAutoGUI, CustomTkinter
- **PyWinCtl compatibility**: Window detection across platforms
- **MSS screenshot**: Screenshot capture functionality
- **Framework imports**: Auto-OSBC utilities and modules

### 3. Integration Tests (`tests/integration/`)
- **Window management**: Window detection and region mapping
- **Screenshot capture**: Cross-platform screenshot functionality
- **Mouse automation**: PyAutoGUI integration testing

## WSL2 Compatibility

### WSL2 Limitations ⚠️
**Auto-OSBC has significant limitations in WSL2:**

- **Window detection**: Cannot access Windows host game clients
- **Screenshot capture**: Limited to WSL2 environment only
- **Mouse automation**: Cannot control Windows host mouse
- **Game client interaction**: Must run games on Windows host

### WSL2 Testing
```bash
# Check if running in WSL2
python -c "from src.platform_utils import detect_wsl2, get_wsl2_compatibility_warnings; print('WSL2:', detect_wsl2()); [print(w) for w in get_wsl2_compatibility_warnings()]"

# Run tests with WSL2 awareness
python test_runner_ubuntu.py  # Will detect and warn about WSL2
```

### Recommendations for WSL2 Users
1. **Use native Windows**: Install Auto-OSBC directly on Windows for full functionality
2. **Use native Ubuntu**: Use real Ubuntu (20.04/22.04/24.04) instead of WSL2 for Linux testing  
3. **Development only**: WSL2 is fine for code editing and non-GUI testing

## Expected Test Results

### ✅ **Passing Tests** (All Platforms)
- Platform detection and version identification
- Core dependency imports (numpy, OpenCV, etc.)
- Framework utility imports
- Basic functionality without GUI requirements

### ⚠️ **Expected Skips**
- **Headless environments**: GUI tests skip when no display available
- **Missing dependencies**: Tests skip if optional dependencies not installed
- **WSL2 limitations**: GUI functionality tests skip in WSL2

### ❌ **Failing Tests** (Troubleshooting)

#### Windows Issues:
- **PyWinCtl failures**: Check Windows Defender, antivirus blocking
- **PyAutoGUI failures**: Verify Python has display access permissions
- **Screenshot failures**: Ensure display drivers are working

#### Ubuntu Issues:
- **Missing system packages**: Run `sudo apt install python3-tk libgl1-mesa-glx`
- **No display**: Tests fail without X11/Wayland (expected in headless)
- **Permission errors**: Check user permissions for screenshot/window access

#### WSL2 Issues:
- **GUI functionality fails**: Expected - use native Windows/Ubuntu instead

## Manual Validation Checklist

After automated tests pass, manually verify:

### Windows Manual Tests:
- [ ] Can detect and focus Notepad window
- [ ] Screenshots capture correctly
- [ ] Mouse can move and click accurately
- [ ] Game launcher can start processes

### Ubuntu Manual Tests:  
- [ ] Can detect terminal/browser windows
- [ ] Screenshots work in X11/Wayland
- [ ] Mouse automation works in desktop environment
- [ ] System packages installed correctly

## Continuous Integration

### GitHub Actions Example:
```yaml
name: Cross-Platform Tests

on: [push, pull_request]

jobs:
  test-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v3
        with:
          python-version: '3.10'
      - run: python test_runner_windows.py

  test-ubuntu:
    runs-on: ubuntu-latest  
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v3
        with:
          python-version: '3.10'
      - run: |
          sudo apt update
          sudo apt install -y python3-tk libgl1-mesa-glx xvfb
          xvfb-run -a python test_runner_ubuntu.py
```

## Performance Benchmarks

Expected performance targets:
- **Platform detection**: < 10ms
- **Screenshot capture**: < 100ms per screenshot
- **Window enumeration**: < 500ms
- **Test suite completion**: < 60 seconds

## Debugging Failed Tests

### Enable Verbose Testing:
```bash
# Maximum verbosity
python test_runner_windows.py -v
python test_runner_ubuntu.py -v

# Or with pytest
python -m pytest tests/ -v -s --tb=long
```

### Check Platform Info:
```bash
# Detailed platform information
python -c "from src.platform_utils import show_platform_info; show_platform_info()"
```

### Common Issues:
1. **Import errors**: Check virtual environment activation
2. **Permission denied**: Run with appropriate permissions
3. **Display not found**: Expected in headless environments
4. **WSL2 limitations**: Use native OS installation