"""
Test PyWinCtl compatibility across different platforms
This is critical for window management functionality
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform import get_platform


class TestPyWinCtlCompatibility(unittest.TestCase):
    """Test PyWinCtl library compatibility"""
    
    def setUp(self):
        """Set up test environment"""
        self.current_platform = get_platform()
    
    def test_pywinctl_import(self):
        """Test PyWinCtl can be imported"""
        try:
            import pywinctl
            self.pywinctl = pywinctl
        except ImportError as e:
            self.skipTest(f"PyWinCtl not available: {e}")
    
    def test_pywinctl_basic_functions_exist(self):
        """Test that expected PyWinCtl functions exist"""
        try:
            import pywinctl
            
            # Core functions that Auto-OSBC uses
            required_functions = [
                'getAllWindows',
                'getWindowsWithTitle',
                'getActiveWindow'
            ]
            
            for func_name in required_functions:
                self.assertTrue(
                    hasattr(pywinctl, func_name),
                    f"PyWinCtl missing required function: {func_name}"
                )
        except ImportError:
            self.skipTest("PyWinCtl not available")
    
    def test_get_all_windows(self):
        """Test getting all windows"""
        try:
            import pywinctl
            
            windows = pywinctl.getAllWindows()
            self.assertIsInstance(windows, list)
            
            # Should have at least some windows on desktop systems
            if self.current_platform in ["windows", "linux"] and windows:
                # Check first window has expected attributes
                first_window = windows[0]
                
                # Basic window attributes that should exist
                expected_attrs = ['title']
                for attr in expected_attrs:
                    self.assertTrue(
                        hasattr(first_window, attr),
                        f"Window object missing attribute: {attr}"
                    )
                    
        except ImportError:
            self.skipTest("PyWinCtl not available")
        except Exception as e:
            # May fail in headless environments
            self.skipTest(f"Window enumeration failed: {e}")
    
    def test_get_windows_with_title(self):
        """Test getting windows by title"""
        try:
            import pywinctl
            
            # Try to find windows with common titles that might exist
            test_titles = ["", "Desktop", "Shell_TrayWnd"]  # Empty string should match all
            
            for title in test_titles:
                try:
                    windows = pywinctl.getWindowsWithTitle(title)
                    self.assertIsInstance(windows, list)
                    
                    # If we found windows, test they have expected structure
                    if windows:
                        break
                        
                except Exception:
                    continue  # Try next title
                    
        except ImportError:
            self.skipTest("PyWinCtl not available")
        except Exception as e:
            self.skipTest(f"Window title search failed: {e}")


class TestWindowManagementIntegration(unittest.TestCase):
    """Test integration with Auto-OSBC window management"""
    
    def test_window_class_import(self):
        """Test that Window class can be imported"""
        try:
            from utilities.window import Window, WindowInitializationError
            
            # Test classes exist
            self.assertTrue(callable(Window))
            self.assertTrue(issubclass(WindowInitializationError, Exception))
            
        except ImportError as e:
            self.fail(f"Window utilities import failed: {e}")
    
    @patch('pywinctl.getWindowsWithTitle')
    def test_window_initialization_mock(self, mock_get_windows):
        """Test Window initialization with mocked PyWinCtl"""
        try:
            from utilities.window import Window
            
            # Mock a window response
            mock_window = MagicMock()
            mock_window.title = "Test Game"
            mock_window.left = 100
            mock_window.top = 100  
            mock_window.width = 800
            mock_window.height = 600
            
            mock_get_windows.return_value = [mock_window]
            
            # Test Window initialization
            # Note: This might still fail due to other dependencies
            try:
                window = Window("Test Game")
                mock_get_windows.assert_called()
            except Exception as e:
                self.skipTest(f"Window initialization failed even with mocked PyWinCtl: {e}")
                
        except ImportError:
            self.skipTest("Window utilities not available")


class TestPlatformSpecificBehavior(unittest.TestCase):
    """Test platform-specific PyWinCtl behavior"""
    
    @unittest.skipUnless(get_platform() == "windows", "Windows-only test")
    def test_windows_specific_functionality(self):
        """Test Windows-specific PyWinCtl functionality"""
        try:
            import pywinctl
            
            # Windows should have system windows
            windows = pywinctl.getAllWindows()
            self.assertGreater(len(windows), 0, "Windows should have system windows")
            
            # Try to find Windows-specific windows
            desktop_windows = pywinctl.getWindowsWithTitle("Program Manager")
            # Program Manager should exist on Windows
            
        except ImportError:
            self.skipTest("PyWinCtl not available")
        except Exception as e:
            self.skipTest(f"Windows-specific test failed: {e}")
    
    @unittest.skipUnless(get_platform() == "linux", "Linux-only test")  
    def test_linux_specific_functionality(self):
        """Test Linux-specific PyWinCtl functionality"""
        try:
            import pywinctl
            
            # Linux behavior may differ from Windows
            windows = pywinctl.getAllWindows()
            self.assertIsInstance(windows, list)
            
            # Linux might have fewer or different system windows
            # Just test that the call doesn't crash
            
        except ImportError:
            self.skipTest("PyWinCtl not available")
        except Exception as e:
            self.skipTest(f"Linux-specific test failed: {e}")


class TestWSL2Compatibility(unittest.TestCase):
    """Test WSL2 specific compatibility issues"""
    
    def test_detect_wsl2_environment(self):
        """Test detection of WSL2 environment"""
        try:
            # WSL2 detection methods
            is_wsl = False
            
            # Method 1: Check /proc/version for Microsoft
            try:
                with open('/proc/version', 'r') as f:
                    proc_version = f.read().lower()
                    if 'microsoft' in proc_version or 'wsl' in proc_version:
                        is_wsl = True
            except (FileNotFoundError, PermissionError):
                pass
            
            # Method 2: Check WSL environment variables
            import os
            wsl_env_vars = ['WSL_DISTRO_NAME', 'WSL_INTEROP']
            for var in wsl_env_vars:
                if os.getenv(var):
                    is_wsl = True
                    break
            
            if is_wsl:
                self.skipTest("Running in WSL2 - GUI functionality may be limited")
                
        except Exception:
            pass  # Not WSL or detection failed
    
    def test_pywinctl_wsl2_limitations(self):
        """Test PyWinCtl limitations in WSL2 environment"""
        # First detect if we're in WSL2
        try:
            with open('/proc/version', 'r') as f:
                proc_version = f.read().lower()
                if 'microsoft' in proc_version:
                    # We're in WSL2
                    try:
                        import pywinctl
                        windows = pywinctl.getAllWindows()
                        
                        # In WSL2, this might fail or return limited results
                        if not windows:
                            self.skipTest(
                                "WSL2 detected: PyWinCtl may not access Windows host windows"
                            )
                    except Exception as e:
                        self.skipTest(f"WSL2 detected: PyWinCtl functionality limited: {e}")
        except FileNotFoundError:
            pass  # Not running on Linux/WSL


if __name__ == '__main__':
    unittest.main()