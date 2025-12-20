"""
Test platform detection utilities using production values
Tests run on the actual current platform without mocking
"""
import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform_utils import (
    get_platform,
    get_windows_version,
    get_ubuntu_version,
    get_detailed_platform_info,
    is_platform_supported,
    check_python_version,
    get_python_executable_name,
    get_venv_activation_command,
    get_pip_executable_path
)


class TestPlatformDetection(unittest.TestCase):
    """Test core platform detection functionality"""

    def test_get_platform_returns_valid_type(self):
        """Test that get_platform returns a valid platform type"""
        result = get_platform()
        valid_platforms = ["windows", "linux", "darwin", "unknown"]
        self.assertIn(result, valid_platforms)

    def test_get_detailed_platform_info(self):
        """Test detailed platform info returns valid data"""
        platform_type, details = get_detailed_platform_info()

        self.assertIsInstance(platform_type, str)
        self.assertIsInstance(details, str)
        self.assertIn(platform_type, ["windows", "linux", "darwin", "unknown"])
        self.assertGreater(len(details), 0)


class TestWindowsDetection(unittest.TestCase):
    """Test Windows-specific detection on Windows platform"""

    def test_windows_version_on_windows(self):
        """Test Windows version detection returns valid value"""
        current_platform = get_platform()
        result = get_windows_version()

        if current_platform == "windows":
            # Should return actual Windows version (10, 11, or unknown)
            self.assertIn(result, ["10", "11", "unknown"])
        else:
            # On non-Windows, should return unknown
            self.assertEqual(result, "unknown")


class TestUbuntuDetection(unittest.TestCase):
    """Test Ubuntu-specific detection"""

    def test_ubuntu_version_returns_valid_value(self):
        """Test Ubuntu version detection returns valid value"""
        current_platform = get_platform()
        result = get_ubuntu_version()

        if current_platform == "linux":
            # On Linux, should return Ubuntu version or unknown
            valid_versions = ["20.04", "22.04", "24.04", "unknown"]
            self.assertIn(result, valid_versions)
        else:
            # On non-Linux, should return unknown
            self.assertEqual(result, "unknown")


class TestPlatformSupport(unittest.TestCase):
    """Test platform support detection"""

    def test_current_platform_support(self):
        """Test that platform support detection returns a boolean"""
        result = is_platform_supported()
        self.assertIsInstance(result, bool)

    def test_platform_support_consistency(self):
        """Test platform support is consistent with platform type"""
        current_platform = get_platform()
        is_supported = is_platform_supported()

        # Unknown platforms should not be supported
        if current_platform == "unknown":
            self.assertFalse(is_supported)


class TestPythonVersion(unittest.TestCase):
    """Test Python version checking"""

    def test_check_python_version_returns_tuple(self):
        """Test that check_python_version returns (bool, str) tuple"""
        is_compatible, version = check_python_version()

        self.assertIsInstance(is_compatible, bool)
        self.assertIsInstance(version, str)
        self.assertRegex(version, r'\d+\.\d+\.\d+')

    def test_current_python_version_compatible(self):
        """Test current Python version (should be 3.10+)"""
        is_compatible, version = check_python_version()

        # We're running tests, so Python should be compatible
        self.assertTrue(is_compatible, f"Python {version} should be 3.10+")

        # Verify version format
        parts = version.split('.')
        self.assertEqual(len(parts), 3)
        major = int(parts[0])
        minor = int(parts[1])
        self.assertGreaterEqual(major, 3)
        self.assertGreaterEqual(minor, 10)


class TestPlatformUtilities(unittest.TestCase):
    """Test platform-specific utility functions"""

    def test_python_executable_name_current_platform(self):
        """Test Python executable name for current platform"""
        current_platform = get_platform()
        result = get_python_executable_name()

        if current_platform == "windows":
            self.assertEqual(result, "python")
        else:
            self.assertEqual(result, "python3")

    def test_venv_activation_command(self):
        """Test virtual environment activation command"""
        current_platform = get_platform()
        venv_path = Path("venv")
        result = get_venv_activation_command(venv_path)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

        if current_platform == "windows":
            self.assertIn("Scripts", result)
            self.assertIn("activate.bat", result)
        else:
            self.assertTrue(result.startswith("source"))
            self.assertIn("bin/activate", result)

    def test_pip_executable_path(self):
        """Test pip executable path"""
        current_platform = get_platform()
        venv_path = Path("venv")
        result = get_pip_executable_path(venv_path)

        self.assertIsInstance(result, Path)

        if current_platform == "windows":
            self.assertEqual(result, venv_path / "Scripts" / "pip.exe")
        else:
            self.assertEqual(result, venv_path / "bin" / "pip")


if __name__ == '__main__':
    unittest.main()
