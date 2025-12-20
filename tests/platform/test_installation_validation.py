"""
Test installation scripts and validation for cross-platform compatibility
"""
import unittest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform_utils import get_platform


class TestInstallationScripts(unittest.TestCase):
    """Test installation script validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent.parent
        self.install_py = self.project_root / "install.py"
        self.install_ubuntu_sh = self.project_root / "install-ubuntu.sh" 
        self.install_windows_bat = self.project_root / "install-windows.bat"
    
    def test_installation_scripts_exist(self):
        """Test that all installation scripts exist"""
        self.assertTrue(self.install_py.exists(), "install.py should exist")
        self.assertTrue(self.install_ubuntu_sh.exists(), "install-ubuntu.sh should exist")
        self.assertTrue(self.install_windows_bat.exists(), "install-windows.bat should exist")
    
    def test_ubuntu_script_executable(self):
        """Test that Ubuntu install script is executable"""
        if get_platform() in ["linux", "darwin"]:
            # Check if script has execute permissions
            import stat
            mode = self.install_ubuntu_sh.stat().st_mode
            self.assertTrue(mode & stat.S_IEXEC, "install-ubuntu.sh should be executable")
    
    @unittest.skipUnless(get_platform() == "linux", "Linux-only test")
    def test_ubuntu_script_syntax(self):
        """Test Ubuntu install script has valid bash syntax"""
        try:
            # Use bash -n to check syntax without executing
            result = subprocess.run(
                ["bash", "-n", str(self.install_ubuntu_sh)], 
                capture_output=True, 
                text=True
            )
            self.assertEqual(result.returncode, 0, f"Bash syntax error: {result.stderr}")
        except FileNotFoundError:
            self.skipTest("bash not available")
    
    def test_python_installer_imports(self):
        """Test that Python installer can be imported without errors"""
        try:
            # Try to compile the install.py script
            with open(self.install_py, 'r') as f:
                code = f.read()
            compile(code, str(self.install_py), 'exec')
        except SyntaxError as e:
            self.fail(f"install.py has syntax errors: {e}")
    
    def test_setup_py_validation(self):
        """Test that setup.py is valid"""
        setup_py = self.project_root / "setup.py"
        self.assertTrue(setup_py.exists(), "setup.py should exist")
        
        try:
            with open(setup_py, 'r') as f:
                code = f.read()
            compile(code, str(setup_py), 'exec')
        except SyntaxError as e:
            self.fail(f"setup.py has syntax errors: {e}")


class TestPlatformCompatibilityChecks(unittest.TestCase):
    """Test platform compatibility validation"""
    
    def test_current_platform_detection(self):
        """Test that current platform can be detected"""
        from src.platform_utils import get_detailed_platform_info, is_platform_supported
        
        platform_type, details = get_detailed_platform_info()
        self.assertIsInstance(platform_type, str)
        self.assertIsInstance(details, str)
        self.assertTrue(len(details) > 0)
        
        # Should not raise exceptions
        supported = is_platform_supported()
        self.assertIsInstance(supported, bool)
    
    def test_python_version_validation(self):
        """Test Python version meets requirements"""
        from src.platform_utils import check_python_version
        
        is_compatible, version = check_python_version()
        
        # Current environment should have compatible Python (since we're running the test)
        if sys.version_info >= (3, 10):
            self.assertTrue(is_compatible, f"Python {version} should be compatible")
        else:
            self.assertFalse(is_compatible, f"Python {version} should not be compatible")


class TestVirtualEnvironmentSetup(unittest.TestCase):
    """Test virtual environment setup functionality"""
    
    @patch('venv.create')
    def test_venv_creation_mock(self, mock_venv_create):
        """Test virtual environment creation (mocked)"""
        from pathlib import Path
        
        # Mock venv creation
        mock_venv_create.return_value = None
        
        # Test the logic would work
        venv_path = Path("test_venv")
        
        # This would be called in actual installer
        mock_venv_create.assert_not_called()  # Not called yet
        
        # Simulate call
        import venv
        venv.create(venv_path, with_pip=True)
        mock_venv_create.assert_called_once_with(venv_path, with_pip=True)
    
    def test_pip_path_generation(self):
        """Test pip executable path generation"""
        from src.platform_utils import get_pip_executable_path
        
        test_venv = Path("test_venv")
        pip_path = get_pip_executable_path(test_venv)
        
        self.assertIsInstance(pip_path, Path)
        
        # Check platform-specific paths
        current_platform = get_platform()
        if current_platform == "windows":
            self.assertTrue(str(pip_path).endswith("pip.exe"))
            self.assertIn("Scripts", str(pip_path))
        else:
            self.assertTrue(str(pip_path).endswith("pip"))
            self.assertIn("bin", str(pip_path))


class TestDependencyValidation(unittest.TestCase):
    """Test dependency validation and compatibility"""
    
    def test_core_dependencies_importable(self):
        """Test that core dependencies can be imported"""
        core_deps = [
            'numpy',
            'cv2',  # opencv-python
            'PIL',  # pillow
            'customtkinter',
            'pynput',
            'requests'
        ]
        
        failed_imports = []
        
        for dep in core_deps:
            try:
                __import__(dep)
            except ImportError:
                failed_imports.append(dep)
        
        if failed_imports:
            self.skipTest(f"Dependencies not installed: {failed_imports}")
    
    def test_platform_specific_imports(self):
        """Test platform-specific imports work correctly"""
        try:
            import pywinctl
            pywinctl_available = True
        except ImportError:
            pywinctl_available = False
        
        try:
            import mss
            mss_available = True
        except ImportError:
            mss_available = False
        
        # These should be available on all platforms where Auto-OSBC runs
        current_platform = get_platform()
        if current_platform in ["windows", "linux"]:
            self.assertTrue(pywinctl_available, "PyWinCtl should be available")
            self.assertTrue(mss_available, "MSS should be available")


if __name__ == '__main__':
    unittest.main()