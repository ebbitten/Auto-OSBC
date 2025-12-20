"""
Test platform detection utilities for cross-platform compatibility
"""
import unittest
import sys
import platform
from pathlib import Path
from unittest.mock import patch, mock_open

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform import (
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

    def test_get_platform_returns_valid_types(self):
        """Test that get_platform returns expected platform types"""
        result = get_platform()
        valid_platforms = ["windows", "linux", "darwin", "unknown"]
        self.assertIn(result, valid_platforms)
    
    @patch('platform.system')
    def test_get_platform_windows(self, mock_system):
        """Test Windows platform detection"""
        mock_system.return_value = "Windows"
        self.assertEqual(get_platform(), "windows")
    
    @patch('platform.system')
    def test_get_platform_linux(self, mock_system):
        """Test Linux platform detection"""
        mock_system.return_value = "Linux"
        self.assertEqual(get_platform(), "linux")
    
    @patch('platform.system') 
    def test_get_platform_macos(self, mock_system):
        """Test macOS platform detection"""
        mock_system.return_value = "Darwin"
        self.assertEqual(get_platform(), "darwin")
    
    @patch('platform.system')
    def test_get_platform_unknown(self, mock_system):
        """Test unknown platform detection"""
        mock_system.return_value = "FreeBSD"
        self.assertEqual(get_platform(), "unknown")


class TestWindowsDetection(unittest.TestCase):
    """Test Windows-specific detection"""
    
    @patch('utilities.platform_utils.get_platform')
    @patch('platform.version')
    def test_windows_10_detection(self, mock_version, mock_get_platform):
        """Test Windows 10 detection"""
        mock_get_platform.return_value = "windows"
        mock_version.return_value = "10.0.19041"
        
        result = get_windows_version()
        self.assertEqual(result, "10")
    
    @patch('utilities.platform_utils.get_platform')  
    @patch('platform.version')
    def test_windows_11_detection(self, mock_version, mock_get_platform):
        """Test Windows 11 detection"""
        mock_get_platform.return_value = "windows"
        mock_version.return_value = "10.0.22000"
        
        result = get_windows_version()
        self.assertEqual(result, "11")
    
    @patch('utilities.platform_utils.get_platform')
    def test_windows_version_on_non_windows(self, mock_get_platform):
        """Test Windows version detection on non-Windows system"""
        mock_get_platform.return_value = "linux"
        
        result = get_windows_version()
        self.assertEqual(result, "unknown")


class TestUbuntuDetection(unittest.TestCase):
    """Test Ubuntu-specific detection"""
    
    @patch('utilities.platform_utils.get_platform')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_ubuntu_2004_detection(self, mock_read_text, mock_exists, mock_get_platform):
        """Test Ubuntu 20.04 detection"""
        mock_get_platform.return_value = "linux"
        mock_exists.return_value = True
        mock_read_text.return_value = '''NAME="Ubuntu"
VERSION="20.04.5 LTS (Focal Fossa)"
VERSION_ID="20.04"
ID=ubuntu'''
        
        result = get_ubuntu_version()
        self.assertEqual(result, "20.04")
    
    @patch('utilities.platform_utils.get_platform')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_ubuntu_2204_detection(self, mock_read_text, mock_exists, mock_get_platform):
        """Test Ubuntu 22.04 detection"""
        mock_get_platform.return_value = "linux"
        mock_exists.return_value = True
        mock_read_text.return_value = '''NAME="Ubuntu"
VERSION="22.04.1 LTS (Jammy Jellyfish)"
VERSION_ID="22.04"
ID=ubuntu'''
        
        result = get_ubuntu_version()
        self.assertEqual(result, "22.04")
    
    @patch('utilities.platform_utils.get_platform')
    @patch('pathlib.Path.exists')
    def test_ubuntu_version_no_os_release(self, mock_exists, mock_get_platform):
        """Test Ubuntu version when /etc/os-release doesn't exist"""
        mock_get_platform.return_value = "linux"
        mock_exists.return_value = False
        
        result = get_ubuntu_version()
        self.assertEqual(result, "unknown")
    
    @patch('utilities.platform_utils.get_platform')
    def test_ubuntu_version_on_non_linux(self, mock_get_platform):
        """Test Ubuntu version detection on non-Linux system"""
        mock_get_platform.return_value = "windows"
        
        result = get_ubuntu_version()
        self.assertEqual(result, "unknown")


class TestPlatformSupport(unittest.TestCase):
    """Test platform support detection"""
    
    @patch('utilities.platform_utils.get_platform')
    @patch('utilities.platform_utils.get_windows_version')
    def test_windows_10_supported(self, mock_windows_version, mock_get_platform):
        """Test Windows 10 is supported"""
        mock_get_platform.return_value = "windows"
        mock_windows_version.return_value = "10"
        
        self.assertTrue(is_platform_supported())
    
    @patch('utilities.platform_utils.get_platform')
    @patch('utilities.platform_utils.get_ubuntu_version')
    def test_ubuntu_2004_supported(self, mock_ubuntu_version, mock_get_platform):
        """Test Ubuntu 20.04 is supported"""
        mock_get_platform.return_value = "linux"
        mock_ubuntu_version.return_value = "20.04"
        
        self.assertTrue(is_platform_supported())
    
    @patch('utilities.platform_utils.get_platform')
    def test_macos_not_supported(self, mock_get_platform):
        """Test macOS is not officially supported"""
        mock_get_platform.return_value = "darwin"
        
        self.assertFalse(is_platform_supported())


class TestPythonVersion(unittest.TestCase):
    """Test Python version checking"""
    
    def test_check_python_version_returns_tuple(self):
        """Test that check_python_version returns (bool, str) tuple"""
        is_compatible, version = check_python_version()
        
        self.assertIsInstance(is_compatible, bool)
        self.assertIsInstance(version, str)
        self.assertRegex(version, r'\d+\.\d+\.\d+')
    
    @patch('sys.version_info', (3, 10, 0))
    def test_python_310_compatible(self):
        """Test Python 3.10 is compatible"""
        is_compatible, version = check_python_version()
        
        self.assertTrue(is_compatible)
        self.assertEqual(version, "3.10.0")
    
    @patch('sys.version_info', (3, 9, 0))
    def test_python_39_not_compatible(self):
        """Test Python 3.9 is not compatible"""
        is_compatible, version = check_python_version()
        
        self.assertFalse(is_compatible)
        self.assertEqual(version, "3.9.0")


class TestPlatformUtilities(unittest.TestCase):
    """Test platform-specific utility functions"""
    
    @patch('utilities.platform_utils.get_platform')
    def test_python_executable_name_windows(self, mock_get_platform):
        """Test Python executable name on Windows"""
        mock_get_platform.return_value = "windows"
        
        result = get_python_executable_name()
        self.assertEqual(result, "python")
    
    @patch('utilities.platform_utils.get_platform')
    def test_python_executable_name_linux(self, mock_get_platform):
        """Test Python executable name on Linux"""
        mock_get_platform.return_value = "linux"
        
        result = get_python_executable_name()
        self.assertEqual(result, "python3")
    
    @patch('utilities.platform_utils.get_platform')
    def test_venv_activation_windows(self, mock_get_platform):
        """Test virtual environment activation command on Windows"""
        mock_get_platform.return_value = "windows"
        venv_path = Path("venv")
        
        result = get_venv_activation_command(venv_path)
        self.assertIn("Scripts", result)
        self.assertIn("activate.bat", result)
    
    @patch('utilities.platform_utils.get_platform')
    def test_venv_activation_linux(self, mock_get_platform):
        """Test virtual environment activation command on Linux"""
        mock_get_platform.return_value = "linux"
        venv_path = Path("venv")
        
        result = get_venv_activation_command(venv_path)
        self.assertTrue(result.startswith("source"))
        self.assertIn("bin/activate", result)
    
    @patch('utilities.platform_utils.get_platform')
    def test_pip_executable_path_windows(self, mock_get_platform):
        """Test pip executable path on Windows"""
        mock_get_platform.return_value = "windows"
        venv_path = Path("venv")
        
        result = get_pip_executable_path(venv_path)
        self.assertEqual(result, venv_path / "Scripts" / "pip.exe")
    
    @patch('utilities.platform_utils.get_platform')
    def test_pip_executable_path_linux(self, mock_get_platform):
        """Test pip executable path on Linux"""
        mock_get_platform.return_value = "linux"
        venv_path = Path("venv")
        
        result = get_pip_executable_path(venv_path)
        self.assertEqual(result, venv_path / "bin" / "pip")


if __name__ == '__main__':
    unittest.main()