#!/usr/bin/env python3
"""
Windows-specific test runner for Auto-OSBC
Tests Windows 10/11 compatibility and functionality
"""
import sys
import unittest
import unittest.util
import time
import logging
import io
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utilities.platform_utils import (
    get_platform, 
    get_windows_version,
    get_detailed_platform_info,
    is_platform_supported
)


def check_windows_environment():
    """Check if running on supported Windows environment"""
    platform_type = get_platform()
    
    if platform_type != "windows":
        print(f"❌ Error: This test runner is for Windows only. Detected: {platform_type}")
        return False
    
    windows_version = get_windows_version()
    if windows_version not in ["10", "11"]:
        print(f"⚠️  Warning: Windows {windows_version} not officially supported")
        print("Officially supported: Windows 10, Windows 11")
        
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    return True


def setup_logging():
    """Setup logging to file and console"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"test_run_windows_{timestamp}.log"
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return log_file


def run_windows_specific_tests():
    """Run Windows-specific test suites"""
    # Setup logging first
    log_file = setup_logging()
    
    print("🚀 Auto-OSBC Windows Test Suite")
    print("=" * 40)
    print(f"📄 Logging to: {log_file}")
    
    logging.info("Starting Windows test suite")
    logging.info(f"Log file: {log_file}")
    
    # Environment check
    if not check_windows_environment():
        logging.error("Environment check failed")
        sys.exit(1)
    
    # Display environment info
    platform_type, details = get_detailed_platform_info()
    supported = is_platform_supported()
    
    print(f"🖥️  Platform: {details}")
    print(f"✅ Supported: {'Yes' if supported else 'No'}")
    print(f"🐍 Python: {sys.version}")
    print()
    
    logging.info(f"Platform: {details}")
    logging.info(f"Supported: {'Yes' if supported else 'No'}")
    logging.info(f"Python: {sys.version}")
    logging.info(f"Working directory: {Path.cwd()}")
    
    # Test discovery and execution
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    print("🔍 Discovering tests...")
    test_count = 0
    
    # Add __init__.py files if missing to make directories importable
    test_dirs = ['tests', 'tests/platform', 'tests/dependencies', 'tests/integration']
    for test_dir in test_dirs:
        init_file = Path(test_dir) / '__init__.py'
        if not init_file.exists() and Path(test_dir).exists():
            init_file.touch()
    
    # Discover all tests in tests directory
    try:
        tests = test_loader.discover(
            'tests',
            pattern='test_*.py',
            top_level_dir='.'
        )
        test_suite.addTest(tests)
        test_count = tests.countTestCases()
    except Exception as e:
        print(f"❌ Error discovering tests: {e}")
        # Fallback: try to run individual test files
        test_files = [
            'tests/platform/test_platform_detection.py',
            'tests/platform/test_installation_validation.py',
            'tests/dependencies/test_core_imports.py',
            'tests/dependencies/test_pywinctl_compatibility.py',
            'tests/integration/test_window_management.py',
            'tests/integration/test_screenshot_capture.py'
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                try:
                    spec = unittest.util.spec_from_file_location("test_module", test_file)
                    module = unittest.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    suite = test_loader.loadTestsFromModule(module)
                    test_suite.addTest(suite)
                    test_count += suite.countTestCases()
                except Exception as file_error:
                    print(f"⚠️  Could not load {test_file}: {file_error}")
    
    print(f"📋 Found {test_count} test cases")
    print()
    
    if test_count == 0:
        print("❌ No tests found. Make sure test files exist in tests/ directory.")
        return False
    
    # Run tests
    print("🧪 Running Windows compatibility tests...")
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
            print(f"   {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    if errors > 0:
        print(f"\n💥 {errors} Test Errors:")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"{i}. {test}")
            print(f"   {traceback.split(chr(10))[-2] if chr(10) in traceback else traceback}")
    
    # Windows-specific recommendations
    print("\n🔧 Windows-specific Notes:")
    
    if failures > 0 or errors > 0:
        print("- Ensure RuneLite or game client is closed during testing")
        print("- Check Windows Defender isn't blocking PyAutoGUI")
        print("- Verify Python has permission to access display/windows")
    
    print("- For full functionality testing, ensure a game client is available")
    print("- Some tests may require administrator privileges")
    
    return result.wasSuccessful()


def main():
    """Main entry point"""
    try:
        success = run_windows_specific_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()