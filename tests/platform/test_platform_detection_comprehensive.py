"""
Comprehensive tests for platform_utils.detection module
Tests detailed platform detection across Windows, Linux, and macOS
"""
import unittest
import sys
import platform as stdlib_platform
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform_utils.detection import (
    get_platform,
    get_windows_version,
    get_ubuntu_version,
    detect_wsl2,
    get_detailed_platform_info,
    PlatformType,
    WindowsVersion,
    UbuntuVersion
)


class TestGetPlatform(unittest.TestCase):
    """Test basic platform detection"""

    @patch('platform.system')
    def test_windows_detection(self, mock_system):
        """Test Windows platform detection"""
        mock_system.return_value = "Windows"

        result = get_platform()
        self.assertEqual(result, "windows")

    @patch('platform.system')
    def test_linux_detection(self, mock_system):
        """Test Linux platform detection"""
        mock_system.return_value = "Linux"

        result = get_platform()
        self.assertEqual(result, "linux")

    @patch('platform.system')
    def test_darwin_detection(self, mock_system):
        """Test macOS (Darwin) platform detection"""
        mock_system.return_value = "Darwin"

        result = get_platform()
        self.assertEqual(result, "darwin")

    @patch('platform.system')
    def test_unknown_platform(self, mock_system):
        """Test unknown platform detection"""
        mock_system.return_value = "FreeBSD"

        result = get_platform()
        self.assertEqual(result, "unknown")


class TestGetWindowsVersion(unittest.TestCase):
    """Test Windows version detection"""

    @patch('platform.system')
    @patch('platform.release')
    def test_windows_10_detection(self, mock_release, mock_system):
        """Test Windows 10 detection"""
        mock_system.return_value = "Windows"
        mock_release.return_value = "10"

        result = get_windows_version()
        self.assertEqual(result, "10")

    @patch('platform.system')
    @patch('platform.release')
    def test_windows_11_detection(self, mock_release, mock_system):
        """Test Windows 11 detection via build number"""
        mock_system.return_value = "Windows"
        mock_release.return_value = "10"  # Windows 11 reports as 10

        # Mock version to return Win11 build number
        with patch('platform.version', return_value='10.0.22000'):
            result = get_windows_version()
            # Should detect as 11 based on build number >= 22000
            self.assertEqual(result, "11")

    @patch('platform.system')
    def test_non_windows_returns_unknown(self, mock_system):
        """Test non-Windows platform returns unknown"""
        mock_system.return_value = "Linux"

        result = get_windows_version()
        self.assertEqual(result, "unknown")

    @patch('platform.system')
    @patch('platform.release')
    def test_old_windows_returns_unknown(self, mock_release, mock_system):
        """Test old Windows version returns unknown"""
        mock_system.return_value = "Windows"
        mock_release.return_value = "7"

        result = get_windows_version()
        self.assertEqual(result, "unknown")


class TestGetUbuntuVersion(unittest.TestCase):
    """Test Ubuntu version detection"""

    @patch('platform.system')
    def test_ubuntu_2004_detection(self, mock_system):
        """Test Ubuntu 20.04 detection"""
        mock_system.return_value = "Linux"

        os_release_content = '''NAME="Ubuntu"
VERSION="20.04.5 LTS (Focal Fossa)"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 20.04.5 LTS"
VERSION_ID="20.04"
'''

        with patch('builtins.open', mock_open(read_data=os_release_content)):
            result = get_ubuntu_version()
            self.assertEqual(result, "20.04")

    @patch('platform.system')
    def test_ubuntu_2204_detection(self, mock_system):
        """Test Ubuntu 22.04 detection"""
        mock_system.return_value = "Linux"

        os_release_content = '''NAME="Ubuntu"
VERSION="22.04.1 LTS (Jammy Jellyfish)"
ID=ubuntu
VERSION_ID="22.04"
'''

        with patch('builtins.open', mock_open(read_data=os_release_content)):
            result = get_ubuntu_version()
            self.assertEqual(result, "22.04")

    @patch('platform.system')
    def test_ubuntu_2404_detection(self, mock_system):
        """Test Ubuntu 24.04 detection"""
        mock_system.return_value = "Linux"

        os_release_content = '''NAME="Ubuntu"
VERSION="24.04 LTS (Noble Numbat)"
ID=ubuntu
VERSION_ID="24.04"
'''

        with patch('builtins.open', mock_open(read_data=os_release_content)):
            result = get_ubuntu_version()
            self.assertEqual(result, "24.04")

    @patch('platform.system')
    def test_non_ubuntu_linux_returns_unknown(self, mock_system):
        """Test non-Ubuntu Linux returns unknown"""
        mock_system.return_value = "Linux"

        os_release_content = '''NAME="Fedora Linux"
VERSION="37 (Workstation Edition)"
ID=fedora
VERSION_ID="37"
'''

        with patch('builtins.open', mock_open(read_data=os_release_content)):
            result = get_ubuntu_version()
            self.assertEqual(result, "unknown")

    @patch('platform.system')
    def test_non_linux_returns_unknown(self, mock_system):
        """Test non-Linux platform returns unknown"""
        mock_system.return_value = "Windows"

        result = get_ubuntu_version()
        self.assertEqual(result, "unknown")

    @patch('platform.system')
    def test_missing_os_release_file(self, mock_system):
        """Test handling of missing /etc/os-release file"""
        mock_system.return_value = "Linux"

        with patch('builtins.open', side_effect=FileNotFoundError):
            result = get_ubuntu_version()
            self.assertEqual(result, "unknown")


class TestDetectWSL2(unittest.TestCase):
    """Test WSL2 environment detection"""

    @patch('platform.system')
    def test_wsl2_detection_via_proc_version(self, mock_system):
        """Test WSL2 detection via /proc/version"""
        mock_system.return_value = "Linux"

        proc_version_content = "Linux version 5.10.16.3-microsoft-standard-WSL2"

        with patch('builtins.open', mock_open(read_data=proc_version_content)):
            result = detect_wsl2()
            self.assertTrue(result)

    @patch('platform.system')
    def test_wsl_detection_via_proc_version(self, mock_system):
        """Test WSL (version 1) detection via /proc/version"""
        mock_system.return_value = "Linux"

        proc_version_content = "Linux version 4.4.0-19041-Microsoft"

        with patch('builtins.open', mock_open(read_data=proc_version_content)):
            result = detect_wsl2()
            self.assertTrue(result)

    @patch('platform.system')
    def test_native_linux_not_wsl2(self, mock_system):
        """Test native Linux is not detected as WSL2"""
        mock_system.return_value = "Linux"

        proc_version_content = "Linux version 5.15.0-56-generic (buildd@lcy02-amd64-001)"

        with patch('builtins.open', mock_open(read_data=proc_version_content)):
            result = detect_wsl2()
            self.assertFalse(result)

    @patch('platform.system')
    def test_non_linux_not_wsl2(self, mock_system):
        """Test non-Linux platform is not WSL2"""
        mock_system.return_value = "Windows"

        result = detect_wsl2()
        self.assertFalse(result)

    @patch('platform.system')
    def test_missing_proc_version_file(self, mock_system):
        """Test handling of missing /proc/version file"""
        mock_system.return_value = "Linux"

        with patch('builtins.open', side_effect=FileNotFoundError):
            result = detect_wsl2()
            self.assertFalse(result)


class TestGetDetailedPlatformInfo(unittest.TestCase):
    """Test detailed platform information retrieval"""

    @patch('src.platform_utils.detection.get_windows_version')
    @patch('platform.system')
    def test_windows_detailed_info(self, mock_system, mock_win_ver):
        """Test detailed Windows platform info"""
        mock_system.return_value = "Windows"
        mock_win_ver.return_value = "11"

        platform_type, details = get_detailed_platform_info()

        self.assertEqual(platform_type, "windows")
        self.assertIn("Windows", details)
        self.assertIn("11", details)

    @patch('src.platform_utils.detection.get_ubuntu_version')
    @patch('platform.system')
    def test_ubuntu_detailed_info(self, mock_system, mock_ubuntu_ver):
        """Test detailed Ubuntu platform info"""
        mock_system.return_value = "Linux"
        mock_ubuntu_ver.return_value = "22.04"

        platform_type, details = get_detailed_platform_info()

        self.assertEqual(platform_type, "linux")
        self.assertIn("Ubuntu", details)
        self.assertIn("22.04", details)

    @patch('platform.system')
    @patch('platform.release')
    def test_macos_detailed_info(self, mock_release, mock_system):
        """Test detailed macOS platform info"""
        mock_system.return_value = "Darwin"
        mock_release.return_value = "22.1.0"

        platform_type, details = get_detailed_platform_info()

        self.assertEqual(platform_type, "darwin")
        self.assertIn("macOS", details)

    @patch('platform.system')
    def test_unknown_platform_detailed_info(self, mock_system):
        """Test detailed info for unknown platform"""
        mock_system.return_value = "FreeBSD"

        platform_type, details = get_detailed_platform_info()

        self.assertEqual(platform_type, "unknown")
        self.assertIn("FreeBSD", details)


class TestPlatformTypeEnum(unittest.TestCase):
    """Test PlatformType enum if it exists"""

    def test_platform_type_enum_exists(self):
        """Test that PlatformType enum has expected values"""
        # Check if PlatformType is a string literal type or enum
        # This test validates the type exists and can be imported
        self.assertIsNotNone(PlatformType)


class TestVersionTypeEnums(unittest.TestCase):
    """Test WindowsVersion and UbuntuVersion enums if they exist"""

    def test_windows_version_enum_exists(self):
        """Test that WindowsVersion enum exists"""
        self.assertIsNotNone(WindowsVersion)

    def test_ubuntu_version_enum_exists(self):
        """Test that UbuntuVersion enum exists"""
        self.assertIsNotNone(UbuntuVersion)


if __name__ == '__main__':
    unittest.main()
