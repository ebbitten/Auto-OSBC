#!/usr/bin/env python3
"""
Ubuntu-specific test runner for Auto-OSBC
Tests Ubuntu 20.04/22.04 compatibility and functionality
"""
import sys
import unittest
import time
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utilities.platform_utils import (
    get_platform, 
    get_ubuntu_version,
    get_detailed_platform_info,
    is_platform_supported
)


def check_ubuntu_environment():
    """Check if running on supported Ubuntu environment"""
    platform_type = get_platform()
    
    if platform_type != "linux":
        print(f"❌ Error: This test runner is for Ubuntu/Linux only. Detected: {platform_type}")
        return False
    
    ubuntu_version = get_ubuntu_version()
    if ubuntu_version not in ["20.04", "22.04", "24.04"]:
        print(f"⚠️  Warning: Ubuntu {ubuntu_version} not officially tested")
        print("Officially supported: Ubuntu 20.04, Ubuntu 22.04, Ubuntu 24.04")
        
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    return True


def check_wsl2_environment():
    """Check if running in WSL2 and warn about limitations"""
    try:
        with open('/proc/version', 'r') as f:
            proc_version = f.read().lower()
            if 'microsoft' in proc_version or 'wsl' in proc_version:
                print("⚠️  WSL2 Environment Detected")
                print("Note: GUI functionality may be limited in WSL2")
                print("For full compatibility testing, use native Ubuntu")
                print()
                
                response = input("Continue with WSL2 testing? (y/N): ")
                if response.lower() != 'y':
                    return False
                    
        # Check WSL environment variables
        wsl_env_vars = ['WSL_DISTRO_NAME', 'WSL_INTEROP']
        for var in wsl_env_vars:
            if os.getenv(var):
                print(f"WSL environment variable detected: {var}={os.getenv(var)}")
                
    except FileNotFoundError:
        pass  # Not running on Linux
    
    return True


def check_display_environment():
    """Check display environment for GUI functionality"""
    display = os.getenv('DISPLAY')
    wayland_display = os.getenv('WAYLAND_DISPLAY')
    
    if not display and not wayland_display:
        print("⚠️  No display environment detected")
        print("GUI-related tests may fail without X11 or Wayland")
        print("This is expected in headless/CI environments")
        print()
    else:
        if display:
            print(f"🖥️  X11 display: {display}")
        if wayland_display:
            print(f"🖥️  Wayland display: {wayland_display}")
        print()


def run_ubuntu_specific_tests():
    """Run Ubuntu-specific test suites"""
    print("🚀 Auto-OSBC Ubuntu Test Suite")
    print("=" * 40)
    
    # Environment checks
    if not check_ubuntu_environment():
        sys.exit(1)
    
    if not check_wsl2_environment():
        sys.exit(1)
    
    check_display_environment()
    
    # Display environment info
    platform_type, details = get_detailed_platform_info()
    supported = is_platform_supported()
    
    print(f"🖥️  Platform: {details}")
    print(f"✅ Supported: {'Yes' if supported else 'No'}")
    print(f"🐍 Python: {sys.version}")
    print()
    
    # Test discovery and execution
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Test directories to include
    test_directories = [
        'tests/platform',
        'tests/dependencies', 
        'tests/integration'
    ]
    
    # Ubuntu-specific test patterns
    ubuntu_patterns = [
        'test_platform_detection.py',
        'test_installation_validation.py',
        'test_core_imports.py',
        'test_pywinctl_compatibility.py',
        'test_window_management.py',
        'test_screenshot_capture.py'
    ]
    
    print("🔍 Discovering tests...")
    test_count = 0
    
    for test_dir in test_directories:
        test_path = Path(test_dir)
        if test_path.exists():
            for pattern in ubuntu_patterns:
                tests = test_loader.discover(
                    str(test_path), 
                    pattern=pattern,
                    top_level_dir='.'
                )
                test_suite.addTest(tests)
                test_count += tests.countTestCases()
    
    print(f"📋 Found {test_count} test cases")
    print()
    
    if test_count == 0:
        print("❌ No tests found. Make sure test files exist in tests/ directory.")
        return False
    
    # Run tests
    print("🧪 Running Ubuntu compatibility tests...")
    print("-" * 40)
    
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True
    )
    
    start_time = time.time()
    result = runner.run(test_suite)
    end_time = time.time()
    
    # Results summary
    print("\n" + "=" * 40)
    print("📊 Test Results Summary")
    print("=" * 40)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"Total tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"⏱️  Time: {end_time - start_time:.2f} seconds")
    
    # Pass rate
    if total_tests > 0:
        pass_rate = (passed / total_tests) * 100
        print(f"📈 Pass rate: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("🎉 Excellent compatibility!")
        elif pass_rate >= 70:
            print("✅ Good compatibility")
        else:
            print("⚠️  Some compatibility issues detected")
    
    # Failure details
    if failures > 0:
        print(f"\n❌ {failures} Test Failures:")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"{i}. {test}")
            # Show last line of traceback for brevity
            lines = traceback.strip().split('\n')
            print(f"   {lines[-1] if lines else 'Unknown error'}")
    
    if errors > 0:
        print(f"\n💥 {errors} Test Errors:")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"{i}. {test}")
            lines = traceback.strip().split('\n')
            print(f"   {lines[-1] if lines else 'Unknown error'}")
    
    # Ubuntu-specific recommendations
    print("\n🔧 Ubuntu-specific Notes:")
    
    if skipped > total_tests * 0.3:  # More than 30% skipped
        print("- Many tests skipped - likely due to missing GUI environment")
        print("- Install X11 or run in desktop environment for full testing")
        print("- System packages may be missing (see install-ubuntu.sh)")
    
    if failures > 0 or errors > 0:
        print("- Ensure required system packages are installed:")
        print("  sudo apt install python3-tk libgl1-mesa-glx libglib2.0-0")
        print("- Check permissions for screenshot and window access")
        print("- Some features may require desktop environment")
    
    print("- For full functionality testing, ensure a game client is available")
    print("- WSL2 users: GUI functionality will be limited")
    
    return result.wasSuccessful()


def main():
    """Main entry point"""
    try:
        success = run_ubuntu_specific_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()