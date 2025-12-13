#!/usr/bin/env python3
"""
Basic platform detection test that doesn't require external dependencies
Tests core platform utilities functionality in WSL2/Ubuntu environment
"""
import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utilities.platform_utils import (
    get_platform,
    get_ubuntu_version,
    get_detailed_platform_info,
    is_platform_supported,
    detect_wsl2,
    get_wsl2_compatibility_warnings,
    check_python_version,
    get_python_executable_name
)


class TestBasicPlatformDetection(unittest.TestCase):
    """Test platform detection without external dependencies"""
    
    def test_get_platform(self):
        """Test basic platform detection"""
        platform = get_platform()
        self.assertIn(platform, ["windows", "linux", "darwin", "unknown"])
        print(f"✅ Platform detected: {platform}")
    
    def test_get_ubuntu_version(self):
        """Test Ubuntu version detection"""
        version = get_ubuntu_version()
        self.assertIn(version, ["20.04", "22.04", "24.04", "unknown"])
        print(f"✅ Ubuntu version: {version}")
    
    def test_detailed_platform_info(self):
        """Test detailed platform information"""
        platform_type, details = get_detailed_platform_info()
        self.assertIsInstance(platform_type, str)
        self.assertIsInstance(details, str)
        print(f"✅ Platform details: {details}")
    
    def test_platform_supported(self):
        """Test platform support detection"""
        supported = is_platform_supported()
        self.assertIsInstance(supported, bool)
        print(f"✅ Platform supported: {supported}")
    
    def test_wsl2_detection(self):
        """Test WSL2 detection"""
        is_wsl2 = detect_wsl2()
        self.assertIsInstance(is_wsl2, bool)
        print(f"✅ WSL2 detected: {is_wsl2}")
        
        if is_wsl2:
            warnings = get_wsl2_compatibility_warnings()
            self.assertIsInstance(warnings, list)
            self.assertGreater(len(warnings), 0)
            print(f"✅ WSL2 warnings count: {len(warnings)}")
    
    def test_python_version_check(self):
        """Test Python version compatibility"""
        compatible, version = check_python_version()
        self.assertIsInstance(compatible, bool)
        self.assertIsInstance(version, str)
        print(f"✅ Python {version} compatible: {compatible}")
    
    def test_python_executable_name(self):
        """Test Python executable name detection"""
        executable = get_python_executable_name()
        self.assertIn(executable, ["python", "python3"])
        print(f"✅ Python executable: {executable}")


class TestWSL2SpecificBehavior(unittest.TestCase):
    """Test WSL2-specific behavior and warnings"""
    
    def test_wsl2_proc_version(self):
        """Test WSL2 detection via /proc/version"""
        try:
            with open('/proc/version', 'r') as f:
                proc_version = f.read().lower()
                has_microsoft = 'microsoft' in proc_version
                has_wsl = 'wsl' in proc_version
                
                print(f"✅ /proc/version contains 'microsoft': {has_microsoft}")
                print(f"✅ /proc/version contains 'wsl': {has_wsl}")
                
                # Should match our detect_wsl2 function
                if has_microsoft or has_wsl:
                    self.assertTrue(detect_wsl2())
                    
        except FileNotFoundError:
            self.skipTest("/proc/version not found - not on Linux")
    
    def test_wsl2_environment_variables(self):
        """Test WSL2 environment variable detection"""
        import os
        
        wsl_vars = ['WSL_DISTRO_NAME', 'WSL_INTEROP', 'WSLENV']
        found_vars = []
        
        for var in wsl_vars:
            if os.getenv(var):
                found_vars.append(var)
        
        print(f"✅ WSL environment variables found: {found_vars}")
        
        if found_vars:
            self.assertTrue(detect_wsl2())


def run_basic_tests():
    """Run basic platform tests"""
    print("🧪 Auto-OSBC Basic Platform Tests")
    print("=" * 50)
    
    # Show platform info first
    print("\n📋 Platform Information:")
    platform_type, details = get_detailed_platform_info()
    supported = is_platform_supported()
    python_compatible, python_version = check_python_version()
    is_wsl2 = detect_wsl2()
    
    print(f"Platform: {details}")
    print(f"Python: {python_version} {'✅' if python_compatible else '❌'}")
    print(f"Supported: {'✅' if supported else '⚠️'}")
    
    if is_wsl2:
        print("WSL2: ⚠️ Detected")
        warnings = get_wsl2_compatibility_warnings()
        print("\nWSL2 Limitations:")
        for warning in warnings[:3]:  # Show first 3 warnings
            print(f"  {warning}")
    
    print("\n🔍 Running Tests...")
    print("-" * 30)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestBasicPlatformDetection))
    suite.addTest(loader.loadTestsFromTestCase(TestWSL2SpecificBehavior))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
    result = runner.run(suite)
    
    # Summary
    print(f"\n📊 Results: {result.testsRun} tests, {len(result.failures)} failed, {len(result.errors)} errors")
    
    if result.wasSuccessful():
        print("🎉 All basic platform tests passed!")
        print("✅ Platform detection is working correctly")
        if is_wsl2:
            print("ℹ️  WSL2 detected - GUI functionality will be limited")
        return True
    else:
        print("❌ Some basic platform tests failed")
        return False


if __name__ == '__main__':
    success = run_basic_tests()
    sys.exit(0 if success else 1)