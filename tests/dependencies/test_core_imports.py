"""
Test core dependency imports and compatibility across platforms
"""
import unittest
import sys
import importlib
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestCoreDependencies(unittest.TestCase):
    """Test that all core dependencies can be imported successfully"""
    
    def test_numpy_import(self):
        """Test numpy import and basic functionality"""
        try:
            import numpy as np
            # Test basic functionality
            arr = np.array([1, 2, 3])
            self.assertEqual(len(arr), 3)
            # NumPy 2.x uses int64 by default, NumPy 1.x used platform-specific defaults
            # Accept both int32 and int64 as valid integer types
            self.assertIn(arr.dtype, [np.int32, np.int64, np.dtype('int32'), np.dtype('int64')])
        except ImportError as e:
            self.skipTest(f"numpy not available: {e}")
    
    def test_opencv_import(self):
        """Test OpenCV import and basic functionality"""
        try:
            import cv2
            import numpy as np
            
            # Test basic OpenCV functionality
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            self.assertEqual(gray.shape, (100, 100))
            
            # Check OpenCV version
            version = cv2.__version__
            self.assertIsInstance(version, str)
            self.assertTrue(len(version) > 0)
            
        except ImportError as e:
            self.skipTest(f"opencv-python not available: {e}")
    
    def test_pillow_import(self):
        """Test Pillow/PIL import and basic functionality"""
        try:
            from PIL import Image
            import numpy as np
            
            # Test basic PIL functionality
            img = Image.new('RGB', (100, 100), color='red')
            self.assertEqual(img.size, (100, 100))
            self.assertEqual(img.mode, 'RGB')
            
            # Test numpy integration
            arr = np.array(img)
            self.assertEqual(arr.shape, (100, 100, 3))
            
        except ImportError as e:
            self.skipTest(f"Pillow not available: {e}")
    
    def test_pyautogui_import(self):
        """Test PyAutoGUI import and basic functionality"""
        try:
            import pyautogui as pag
            
            # Test basic functionality (that doesn't require GUI)
            size = pag.size()
            self.assertIsInstance(size, pag.Size)
            self.assertGreater(size.width, 0)
            self.assertGreater(size.height, 0)
            
            # Test version
            version = pag.__version__ if hasattr(pag, '__version__') else "unknown"
            self.assertIsInstance(version, str)
            
        except ImportError as e:
            self.skipTest(f"pyautogui not available: {e}")
        except Exception as e:
            # PyAutoGUI might fail in headless environments
            self.skipTest(f"pyautogui functionality unavailable: {e}")
    
    def test_customtkinter_import(self):
        """Test CustomTkinter import"""
        try:
            import customtkinter as ctk
            
            # Test basic import
            self.assertTrue(hasattr(ctk, 'CTk'))
            self.assertTrue(hasattr(ctk, 'CTkButton'))
            
            # Don't create actual windows in tests
            
        except ImportError as e:
            self.skipTest(f"customtkinter not available: {e}")
    
    def test_pynput_import(self):
        """Test pynput import and basic functionality"""
        try:
            from pynput import mouse, keyboard
            
            # Test basic functionality
            self.assertTrue(hasattr(mouse, 'Button'))
            self.assertTrue(hasattr(keyboard, 'Key'))
            
        except ImportError as e:
            self.skipTest(f"pynput not available: {e}")
    
    def test_requests_import(self):
        """Test requests import and basic functionality"""
        try:
            import requests
            
            # Test version
            version = requests.__version__
            self.assertIsInstance(version, str)
            
            # Test basic functionality (no network calls in unit tests)
            session = requests.Session()
            self.assertIsNotNone(session)
            
        except ImportError as e:
            self.skipTest(f"requests not available: {e}")


class TestPlatformSpecificDependencies(unittest.TestCase):
    """Test platform-specific dependencies"""
    
    def test_pywinctl_import(self):
        """Test PyWinCtl import and basic functionality"""
        try:
            import pywinctl
            
            # Test basic functionality
            self.assertTrue(hasattr(pywinctl, 'getAllWindows'))
            self.assertTrue(hasattr(pywinctl, 'getWindowsWithTitle'))
            
            # Try to get windows list (may be empty in headless environment)
            try:
                windows = pywinctl.getAllWindows()
                self.assertIsInstance(windows, list)
            except Exception as e:
                # May fail in headless/CI environment
                self.skipTest(f"PyWinCtl window enumeration failed: {e}")
                
        except ImportError as e:
            self.skipTest(f"PyWinCtl not available: {e}")
    
    def test_mss_import(self):
        """Test MSS screenshot library import"""
        try:
            import mss
            
            # Test basic functionality
            with mss.mss() as sct:
                self.assertIsNotNone(sct)
                
                # Try to get monitor info
                monitors = sct.monitors
                self.assertIsInstance(monitors, list)
                self.assertGreater(len(monitors), 0)  # Should have at least one monitor
                
        except ImportError as e:
            self.skipTest(f"mss not available: {e}")
        except Exception as e:
            # May fail in headless environment
            self.skipTest(f"MSS functionality unavailable: {e}")


class TestFrameworkImports(unittest.TestCase):
    """Test Auto-OSBC framework imports"""
    
    def test_platform_utils_import(self):
        """Test platform utilities import"""
        try:
            from src.platform import (
                get_platform,
                get_detailed_platform_info,
                is_platform_supported,
                check_python_version
            )
            
            # Test basic functionality
            platform = get_platform()
            self.assertIsInstance(platform, str)
            
            details = get_detailed_platform_info()
            self.assertIsInstance(details, tuple)
            self.assertEqual(len(details), 2)
            
            supported = is_platform_supported()
            self.assertIsInstance(supported, bool)
            
            python_check = check_python_version()
            self.assertIsInstance(python_check, tuple)
            self.assertEqual(len(python_check), 2)
            
        except ImportError as e:
            self.fail(f"platform_utils import failed: {e}")
    
    def test_geometry_import(self):
        """Test geometry utilities import"""
        try:
            from utilities.geometry import Point, Rectangle
            
            # Test Point creation
            point = Point(10, 20)
            self.assertEqual(point.x, 10)
            self.assertEqual(point.y, 20)
            
            # Test Rectangle creation
            rect = Rectangle(0, 0, 100, 100)
            self.assertEqual(rect.left, 0)
            self.assertEqual(rect.top, 0)
            self.assertEqual(rect.width, 100)
            self.assertEqual(rect.height, 100)
            
        except ImportError as e:
            self.fail(f"geometry utilities import failed: {e}")
    
    def test_color_import(self):
        """Test color utilities import"""
        try:
            import utilities.color as clr
            
            # Test basic color constants exist
            self.assertTrue(hasattr(clr, 'CYAN'))
            self.assertTrue(hasattr(clr, 'PINK'))
            self.assertTrue(hasattr(clr, 'WHITE'))
            self.assertTrue(hasattr(clr, 'BLACK'))
            
        except ImportError as e:
            self.fail(f"color utilities import failed: {e}")


class TestDevelopmentDependencies(unittest.TestCase):
    """Test development and testing dependencies"""
    
    def test_mypy_import(self):
        """Test mypy import (development dependency)"""
        try:
            import mypy
            # Basic import test - mypy is a package, check for __path__
            self.assertTrue(hasattr(mypy, '__path__'))
        except ImportError:
            self.skipTest("mypy not available (development dependency)")
    
    def test_flake8_import(self):
        """Test flake8 import (development dependency)"""
        try:
            import flake8
            # Basic import test
            version = getattr(flake8, '__version__', None)
            self.assertIsNotNone(version)
        except ImportError:
            self.skipTest("flake8 not available (development dependency)")
    
    def test_pytest_import(self):
        """Test pytest import (development dependency)"""
        try:
            import pytest
            # Basic import test
            version = pytest.__version__
            self.assertIsInstance(version, str)
        except ImportError:
            self.skipTest("pytest not available (development dependency)")


class TestImportPerformance(unittest.TestCase):
    """Test import performance to catch slow imports"""
    
    def test_framework_imports_fast(self):
        """Test that framework imports complete quickly"""
        import time
        
        start_time = time.time()
        
        try:
            from src.platform import get_platform
            from utilities.geometry import Point, Rectangle
            import utilities.color as clr
            
            end_time = time.time()
            import_time = end_time - start_time
            
            # Should import in less than 1 second
            self.assertLess(import_time, 1.0, f"Framework imports took {import_time:.2f}s")
            
        except ImportError as e:
            self.skipTest(f"Framework imports failed: {e}")


if __name__ == '__main__':
    unittest.main()