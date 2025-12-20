#!/usr/bin/env python3
"""
Installation Validation Script for Auto-OSBC
Performs smoke tests to ensure all critical dependencies are properly installed.
"""

import sys
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path (we're in tests/smoke/, so go up two levels)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_core_imports():
    """Test that all core dependencies can be imported."""
    print("=" * 60)
    print("CORE DEPENDENCY VALIDATION")
    print("=" * 60)

    tests = [
        ("NumPy", "numpy", lambda m: f"version {m.__version__}"),
        ("OpenCV", "cv2", lambda m: f"version {m.__version__}"),
        ("Pillow", "PIL", lambda m: f"version {m.__version__}"),
        ("PyAutoGUI", "pyautogui", lambda m: f"version {m.__version__}"),
        ("CustomTkinter", "customtkinter", lambda m: "✓"),
        ("Pynput", "pynput", lambda m: "✓"),
        ("Requests", "requests", lambda m: f"version {m.__version__}"),
        ("MSS", "mss", lambda m: f"version {m.__version__}"),
        ("PyWinCtl", "pywinctl", lambda m: "✓"),
    ]

    passed = 0
    failed = []

    for name, module_name, version_func in tests:
        try:
            module = __import__(module_name)
            version_info = version_func(module)
            print(f"✅ {name:20s} {version_info}")
            passed += 1
        except ImportError as e:
            print(f"❌ {name:20s} FAILED: {e}")
            failed.append(name)
        except Exception as e:
            print(f"⚠️  {name:20s} WARNING: {e}")
            passed += 1  # Still counts as passed if import worked

    print(f"\nCore Dependencies: {passed}/{len(tests)} passed")
    return len(failed) == 0, failed


def test_framework_imports():
    """Test that Auto-OSBC framework modules can be imported."""
    print("\n" + "=" * 60)
    print("FRAMEWORK MODULE VALIDATION")
    print("=" * 60)

    tests = [
        ("Color utilities", "src.utilities.color"),
        ("Geometry utilities", "src.utilities.geometry"),
        ("Platform utilities", "src.utilities.platform_utils"),
        ("Window management", "src.utilities.window"),
        ("Bot base class", "src.model.bot"),
    ]

    passed = 0
    failed = []

    for name, module_name in tests:
        try:
            __import__(module_name)
            print(f"✅ {name:30s} imported successfully")
            passed += 1
        except ImportError as e:
            print(f"❌ {name:30s} FAILED: {e}")
            failed.append(name)
        except Exception as e:
            print(f"⚠️  {name:30s} WARNING: {e}")

    print(f"\nFramework Modules: {passed}/{len(tests)} passed")
    return len(failed) == 0, failed


def test_development_tools():
    """Test that development tools are installed."""
    print("\n" + "=" * 60)
    print("DEVELOPMENT TOOLS VALIDATION")
    print("=" * 60)

    tests = [
        ("pytest", "pytest", lambda m: f"version {m.__version__}"),
        ("mypy", "mypy", lambda m: f"version {m.version.__version__}"),
        ("flake8", "flake8", lambda m: "✓"),
    ]

    passed = 0
    failed = []

    for name, module_name, version_func in tests:
        try:
            module = __import__(module_name)
            version_info = version_func(module)
            print(f"✅ {name:20s} {version_info}")
            passed += 1
        except ImportError as e:
            print(f"❌ {name:20s} FAILED: {e}")
            failed.append(name)
        except Exception as e:
            print(f"⚠️  {name:20s} WARNING: {e}")
            passed += 1

    print(f"\nDevelopment Tools: {passed}/{len(tests)} passed")
    return len(failed) == 0, failed


def test_type_stubs():
    """Test that type stubs are installed."""
    print("\n" + "=" * 60)
    print("TYPE STUBS VALIDATION")
    print("=" * 60)

    tests = [
        ("types-PyAutoGUI", "types_pyautogui"),
        ("types-Deprecated", "types_deprecated"),
    ]

    passed = 0
    failed = []

    for name, module_name in tests:
        try:
            __import__(module_name)
            print(f"✅ {name:25s} installed")
            passed += 1
        except ImportError:
            print(f"⚠️  {name:25s} not found (optional)")
            # Type stubs are optional, don't count as failure

    print(f"\nType Stubs: {passed}/{len(tests)} found")
    return True, []  # Always return success for optional components


def test_platform_detection():
    """Test platform detection utilities."""
    print("\n" + "=" * 60)
    print("PLATFORM DETECTION VALIDATION")
    print("=" * 60)

    try:
        from src.platform_utils import (
            get_platform,
            get_detailed_platform_info,
            check_python_version,
            is_platform_supported
        )

        platform = get_platform()
        platform_type, details = get_detailed_platform_info()
        is_compatible, version = check_python_version()
        is_supported = is_platform_supported()

        print(f"✅ Platform: {platform}")
        print(f"✅ Platform details: {platform_type} - {details}")
        print(f"✅ Python version: {version} (compatible: {is_compatible})")
        print(f"✅ Platform supported: {is_supported}")

        return True, []
    except Exception as e:
        print(f"❌ Platform detection failed: {e}")
        return False, ["Platform detection"]


def test_basic_functionality():
    """Test basic functionality with simple operations."""
    print("\n" + "=" * 60)
    print("BASIC FUNCTIONALITY TESTS")
    print("=" * 60)

    passed = 0
    failed = []

    # Test 1: NumPy array operations
    try:
        import numpy as np
        arr = np.array([1, 2, 3, 4, 5])
        assert arr.sum() == 15
        print("✅ NumPy array operations")
        passed += 1
    except Exception as e:
        print(f"❌ NumPy array operations: {e}")
        failed.append("NumPy operations")

    # Test 2: OpenCV image creation
    try:
        import cv2
        import numpy as np
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        assert img.shape == (100, 100, 3)
        print("✅ OpenCV image creation")
        passed += 1
    except Exception as e:
        print(f"❌ OpenCV image creation: {e}")
        failed.append("OpenCV operations")

    # Test 3: Geometry utilities
    try:
        from src.utilities.geometry import Rectangle, Point
        rect = Rectangle.from_points(Point(0, 0), Point(100, 100))
        assert rect.width == 100
        assert rect.height == 100
        print("✅ Geometry utilities")
        passed += 1
    except Exception as e:
        print(f"❌ Geometry utilities: {e}")
        failed.append("Geometry operations")

    # Test 4: Color utilities
    try:
        from src.utilities import color as clr
        assert hasattr(clr, 'CYAN')
        assert hasattr(clr, 'PINK')
        assert hasattr(clr, 'PURPLE')
        print("✅ Color utilities")
        passed += 1
    except Exception as e:
        print(f"❌ Color utilities: {e}")
        failed.append("Color operations")

    print(f"\nBasic Functionality: {passed}/4 passed")
    return len(failed) == 0, failed


def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("AUTO-OSBC INSTALLATION VALIDATION")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()

    all_passed = True
    all_failures = []

    # Run all test suites
    test_suites = [
        test_core_imports,
        test_framework_imports,
        test_development_tools,
        test_type_stubs,
        test_platform_detection,
        test_basic_functionality,
    ]

    for test_suite in test_suites:
        passed, failures = test_suite()
        all_passed = all_passed and passed
        all_failures.extend(failures)

    # Final summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("\nYour Auto-OSBC installation is ready for development.")
        print("\nNext steps:")
        print("  1. Review CLAUDE.md for TDD development workflow")
        print("  2. Check docs/current-state.md for architecture overview")
        print("  3. Run full test suite: python -m pytest tests/ -v")
        print("  4. Try running an existing bot")
        return 0
    else:
        print("❌ SOME VALIDATION TESTS FAILED")
        print(f"\nFailed components: {', '.join(all_failures)}")
        print("\nPlease address the failures above before proceeding.")
        print("Refer to WINDOWS_SETUP.md for installation instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
