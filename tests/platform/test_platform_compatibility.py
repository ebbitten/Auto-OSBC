"""
Comprehensive tests for platform_utils.compatibility module
Tests platform support checking, dependency retrieval, and WSL2 warnings
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform_utils.compatibility import (
    check_python_version,
    is_platform_supported,
    get_platform_specific_dependencies,
    get_wsl2_compatibility_warnings,
    show_platform_info
)
from src.platform_utils.detection import get_detailed_platform_info


class TestPythonVersionCheck(unittest.TestCase):
    """Test Python version compatibility checking"""

    def test_check_python_version_returns_tuple(self):
        """Test that check_python_version returns (bool, str) tuple"""
        is_compatible, version = check_python_version()

        self.assertIsInstance(is_compatible, bool)
        self.assertIsInstance(version, str)
        # Version should be in format X.Y.Z
        self.assertRegex(version, r'\d+\.\d+\.\d+')

    def test_current_python_compatible(self):
        """Test current Python version (should be 3.10+)"""
        is_compatible, version = check_python_version()

        # We're running tests, so Python should be compatible
        self.assertTrue(is_compatible, f"Python {version} should be 3.10+")

        # Parse version
        parts = version.split('.')
        self.assertEqual(len(parts), 3)
        major = int(parts[0])
        minor = int(parts[1])

        self.assertEqual(major, 3)
        self.assertGreaterEqual(minor, 10)

    @patch('sys.version_info', (3, 9, 0, 'final', 0))
    def test_python_39_incompatible(self):
        """Test that Python 3.9 is detected as incompatible"""
        is_compatible, version = check_python_version()

        self.assertFalse(is_compatible)
        self.assertEqual(version, "3.9.0")

    @patch('sys.version_info', (2, 7, 18, 'final', 0))
    def test_python_2_incompatible(self):
        """Test that Python 2.x is detected as incompatible"""
        is_compatible, version = check_python_version()

        self.assertFalse(is_compatible)
        self.assertEqual(version, "2.7.18")


class TestPlatformSupport(unittest.TestCase):
    """Test platform support detection"""

    @patch('src.platform_utils.compatibility.get_platform')
    @patch('src.platform_utils.compatibility.get_windows_version')
    def test_windows_10_supported(self, mock_win_ver, mock_platform):
        """Test Windows 10 is supported"""
        mock_platform.return_value = "windows"
        mock_win_ver.return_value = "10"

        result = is_platform_supported()
        self.assertTrue(result)

    @patch('src.platform_utils.compatibility.get_platform')
    @patch('src.platform_utils.compatibility.get_windows_version')
    def test_windows_11_supported(self, mock_win_ver, mock_platform):
        """Test Windows 11 is supported"""
        mock_platform.return_value = "windows"
        mock_win_ver.return_value = "11"

        result = is_platform_supported()
        self.assertTrue(result)

    @patch('src.platform_utils.compatibility.get_platform')
    @patch('src.platform_utils.compatibility.get_windows_version')
    def test_windows_7_not_supported(self, mock_win_ver, mock_platform):
        """Test Windows 7 is not supported"""
        mock_platform.return_value = "windows"
        mock_win_ver.return_value = "7"

        result = is_platform_supported()
        self.assertFalse(result)

    @patch('src.platform_utils.compatibility.get_platform')
    @patch('src.platform_utils.compatibility.get_ubuntu_version')
    def test_ubuntu_2004_supported(self, mock_ubuntu_ver, mock_platform):
        """Test Ubuntu 20.04 is supported"""
        mock_platform.return_value = "linux"
        mock_ubuntu_ver.return_value = "20.04"

        result = is_platform_supported()
        self.assertTrue(result)

    @patch('src.platform_utils.compatibility.get_platform')
    @patch('src.platform_utils.compatibility.get_ubuntu_version')
    def test_ubuntu_2204_supported(self, mock_ubuntu_ver, mock_platform):
        """Test Ubuntu 22.04 is supported"""
        mock_platform.return_value = "linux"
        mock_ubuntu_ver.return_value = "22.04"

        result = is_platform_supported()
        self.assertTrue(result)

    @patch('src.platform_utils.compatibility.get_platform')
    @patch('src.platform_utils.compatibility.get_ubuntu_version')
    def test_ubuntu_2404_supported(self, mock_ubuntu_ver, mock_platform):
        """Test Ubuntu 24.04 is supported"""
        mock_platform.return_value = "linux"
        mock_ubuntu_ver.return_value = "24.04"

        result = is_platform_supported()
        self.assertTrue(result)

    @patch('src.platform_utils.compatibility.get_platform')
    @patch('src.platform_utils.compatibility.get_ubuntu_version')
    def test_ubuntu_1804_not_supported(self, mock_ubuntu_ver, mock_platform):
        """Test Ubuntu 18.04 is not supported"""
        mock_platform.return_value = "linux"
        mock_ubuntu_ver.return_value = "18.04"

        result = is_platform_supported()
        self.assertFalse(result)

    @patch('src.platform_utils.compatibility.get_platform')
    def test_macos_not_supported(self, mock_platform):
        """Test macOS is not supported"""
        mock_platform.return_value = "darwin"

        result = is_platform_supported()
        self.assertFalse(result)

    @patch('src.platform_utils.compatibility.get_platform')
    def test_unknown_platform_not_supported(self, mock_platform):
        """Test unknown platform is not supported"""
        mock_platform.return_value = "unknown"

        result = is_platform_supported()
        self.assertFalse(result)


class TestPlatformSpecificDependencies(unittest.TestCase):
    """Test platform-specific dependency retrieval"""

    @patch('src.platform_utils.compatibility.get_platform')
    def test_windows_dependencies(self, mock_platform):
        """Test Windows-specific dependencies"""
        mock_platform.return_value = "windows"

        deps = get_platform_specific_dependencies()
        self.assertIsInstance(deps, list)
        # Currently returns empty list for Windows
        self.assertEqual(deps, [])

    @patch('src.platform_utils.compatibility.get_platform')
    def test_linux_dependencies(self, mock_platform):
        """Test Linux-specific dependencies"""
        mock_platform.return_value = "linux"

        deps = get_platform_specific_dependencies()
        self.assertIsInstance(deps, list)
        # Currently returns empty list for Linux
        self.assertEqual(deps, [])

    @patch('src.platform_utils.compatibility.get_platform')
    def test_macos_dependencies(self, mock_platform):
        """Test macOS-specific dependencies"""
        mock_platform.return_value = "darwin"

        deps = get_platform_specific_dependencies()
        self.assertIsInstance(deps, list)
        # Currently returns empty list for macOS
        self.assertEqual(deps, [])

    @patch('src.platform_utils.compatibility.get_platform')
    def test_unknown_platform_dependencies(self, mock_platform):
        """Test unknown platform dependencies"""
        mock_platform.return_value = "unknown"

        deps = get_platform_specific_dependencies()
        self.assertIsInstance(deps, list)
        self.assertEqual(deps, [])


class TestWSL2CompatibilityWarnings(unittest.TestCase):
    """Test WSL2 compatibility warnings"""

    @patch('src.platform_utils.compatibility.detect_wsl2')
    def test_wsl2_warnings_present(self, mock_detect):
        """Test WSL2 warnings are returned when WSL2 detected"""
        mock_detect.return_value = True

        warnings = get_wsl2_compatibility_warnings()

        self.assertIsInstance(warnings, list)
        self.assertGreater(len(warnings), 0)

        # Check for expected warning content
        warning_text = '\n'.join(warnings)
        self.assertIn("WSL2", warning_text)
        self.assertIn("Window detection", warning_text)
        self.assertIn("Screenshot capture", warning_text)
        self.assertIn("Mouse automation", warning_text)

    @patch('src.platform_utils.compatibility.detect_wsl2')
    def test_no_wsl2_warnings(self, mock_detect):
        """Test no warnings when not in WSL2"""
        mock_detect.return_value = False

        warnings = get_wsl2_compatibility_warnings()

        self.assertIsInstance(warnings, list)
        self.assertEqual(len(warnings), 0)


class TestShowPlatformInfo(unittest.TestCase):
    """Test platform info display function"""

    @patch('src.platform_utils.compatibility.detect_wsl2')
    @patch('src.platform_utils.compatibility.is_platform_supported')
    @patch('src.platform_utils.compatibility.check_python_version')
    @patch('src.platform_utils.detection.get_detailed_platform_info')
    @patch('builtins.print')
    def test_show_platform_info_supported(self, mock_print, mock_detailed,
                                          mock_python, mock_supported, mock_wsl2):
        """Test show_platform_info for supported platform"""
        mock_detailed.return_value = ("windows", "Windows 11")
        mock_python.return_value = (True, "3.10.11")
        mock_supported.return_value = True
        mock_wsl2.return_value = False

        show_platform_info()

        # Verify print was called
        self.assertGreater(mock_print.call_count, 0)

        # Check printed content contains expected info
        printed_text = ' '.join(str(call[0][0]) for call in mock_print.call_args_list)
        self.assertIn("Windows 11", printed_text)
        self.assertIn("3.10.11", printed_text)

    @patch('src.platform_utils.compatibility.detect_wsl2')
    @patch('src.platform_utils.compatibility.is_platform_supported')
    @patch('src.platform_utils.compatibility.check_python_version')
    @patch('src.platform_utils.detection.get_detailed_platform_info')
    @patch('builtins.print')
    def test_show_platform_info_wsl2(self, mock_print, mock_detailed,
                                     mock_python, mock_supported, mock_wsl2):
        """Test show_platform_info displays WSL2 warnings"""
        mock_detailed.return_value = ("linux", "Ubuntu 22.04")
        mock_python.return_value = (True, "3.10.11")
        mock_supported.return_value = True
        mock_wsl2.return_value = True

        show_platform_info()

        # Verify print was called
        self.assertGreater(mock_print.call_count, 0)

        # Check WSL2 warning is printed
        printed_text = ' '.join(str(call[0][0]) for call in mock_print.call_args_list)
        self.assertIn("WSL2", printed_text)

    @patch('src.platform_utils.compatibility.detect_wsl2')
    @patch('src.platform_utils.compatibility.is_platform_supported')
    @patch('src.platform_utils.compatibility.check_python_version')
    @patch('src.platform_utils.detection.get_detailed_platform_info')
    @patch('builtins.print')
    def test_show_platform_info_unsupported(self, mock_print, mock_detailed,
                                            mock_python, mock_supported, mock_wsl2):
        """Test show_platform_info for unsupported platform"""
        mock_detailed.return_value = ("darwin", "macOS 13.0")
        mock_python.return_value = (True, "3.10.11")
        mock_supported.return_value = False
        mock_wsl2.return_value = False

        show_platform_info()

        # Verify print was called
        self.assertGreater(mock_print.call_count, 0)

        # Check unsupported platform message
        printed_text = ' '.join(str(call[0][0]) for call in mock_print.call_args_list)
        self.assertIn("supported", printed_text.lower())


if __name__ == '__main__':
    unittest.main()
