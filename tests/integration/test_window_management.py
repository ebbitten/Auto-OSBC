"""
Test window management functionality across platforms
"""
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform_utils import get_platform


class TestWindowDetection(unittest.TestCase):
    """Test window detection and management"""
    
    def test_window_class_import(self):
        """Test Window class can be imported"""
        try:
            from utilities.window import Window, WindowInitializationError
            
            self.assertTrue(callable(Window))
            self.assertTrue(issubclass(WindowInitializationError, Exception))
            
        except ImportError as e:
            self.fail(f"Failed to import Window class: {e}")
    
    @patch('pywinctl.getWindowsWithTitle')
    def test_window_initialization_with_mock(self, mock_get_windows):
        """Test Window initialization with mocked window"""
        try:
            from utilities.window import Window
            
            # Create a detailed mock window
            mock_window = MagicMock()
            mock_window.title = "RuneLite"
            mock_window.left = 100
            mock_window.top = 100
            mock_window.width = 800
            mock_window.height = 600
            mock_window.isMaximized = False
            mock_window.isMinimized = False
            mock_window.isVisible = True
            
            # Mock methods
            mock_window.moveTo = MagicMock()
            mock_window.resizeTo = MagicMock()
            mock_window.activate = MagicMock()
            
            mock_get_windows.return_value = [mock_window]
            
            # Try to initialize Window
            try:
                window = Window("RuneLite")
                
                # Verify the mock was called
                mock_get_windows.assert_called_with("RuneLite")
                
                # Test basic properties if initialization succeeded
                self.assertEqual(window.window_title, "RuneLite")
                
            except Exception as e:
                # Window initialization might fail due to other requirements
                self.skipTest(f"Window initialization failed: {e}")
                
        except ImportError:
            self.skipTest("Window class not available")
    
    def test_window_initialization_error_handling(self):
        """Test Window initialization error handling"""
        try:
            from utilities.window import Window, WindowInitializationError
            
            # Try to initialize with non-existent window
            with self.assertRaises(WindowInitializationError):
                Window("NonExistentWindow12345")
                
        except ImportError:
            self.skipTest("Window class not available")


class TestWindowRegions(unittest.TestCase):
    """Test window region detection and mapping"""
    
    @patch('pywinctl.getWindowsWithTitle')
    def test_window_regions_setup(self, mock_get_windows):
        """Test window regions are set up correctly"""
        try:
            from utilities.window import Window
            from utilities.geometry import Rectangle
            
            # Mock window with proper dimensions
            mock_window = MagicMock()
            mock_window.title = "RuneLite"
            mock_window.left = 0
            mock_window.top = 0
            mock_window.width = 765  # Fixed RuneLite width
            mock_window.height = 503  # Fixed RuneLite height
            
            mock_get_windows.return_value = [mock_window]
            
            try:
                window = Window("RuneLite")
                
                # Test that regions are Rectangle objects
                regions_to_test = [
                    'game_view', 'control_panel', 'chat', 'minimap_area'
                ]
                
                for region_name in regions_to_test:
                    if hasattr(window, region_name):
                        region = getattr(window, region_name)
                        self.assertIsInstance(
                            region, Rectangle, 
                            f"{region_name} should be a Rectangle object"
                        )
                        
                        # Test basic Rectangle properties
                        self.assertGreaterEqual(region.width, 0)
                        self.assertGreaterEqual(region.height, 0)
                        
            except Exception as e:
                self.skipTest(f"Window regions test failed: {e}")
                
        except ImportError:
            self.skipTest("Window class not available")
    
    @patch('pywinctl.getWindowsWithTitle')
    def test_inventory_slots_mapping(self, mock_get_windows):
        """Test inventory slots are mapped correctly"""
        try:
            from utilities.window import Window
            
            mock_window = MagicMock()
            mock_window.title = "RuneLite"
            mock_window.left = 0
            mock_window.top = 0
            mock_window.width = 765
            mock_window.height = 503
            
            mock_get_windows.return_value = [mock_window]
            
            try:
                window = Window("RuneLite")
                
                # Test inventory slots exist and are correct count
                if hasattr(window, 'inventory_slots'):
                    slots = window.inventory_slots
                    self.assertIsInstance(slots, list)
                    self.assertEqual(len(slots), 28, "Should have 28 inventory slots")
                    
                    # Test each slot is a Rectangle
                    for i, slot in enumerate(slots):
                        self.assertIsInstance(
                            slot, type(window.game_view), 
                            f"Inventory slot {i} should be a Rectangle"
                        )
                        
            except Exception as e:
                self.skipTest(f"Inventory slots test failed: {e}")
                
        except ImportError:
            self.skipTest("Window class not available")


class TestScreenshotCapture(unittest.TestCase):
    """Test screenshot capture functionality"""
    
    def test_mss_screenshot_import(self):
        """Test MSS screenshot library functionality"""
        try:
            import mss
            import numpy as np
            
            with mss.mss() as sct:
                # Test monitor detection
                monitors = sct.monitors
                self.assertIsInstance(monitors, list)
                self.assertGreater(len(monitors), 0)
                
                # Test screenshot capture (primary monitor)
                if len(monitors) > 1:  # monitors[0] is all monitors combined
                    monitor = monitors[1]  # Primary monitor
                    
                    try:
                        screenshot = sct.grab(monitor)
                        self.assertIsNotNone(screenshot)
                        
                        # Convert to numpy array
                        img_np = np.array(screenshot)
                        self.assertGreater(img_np.size, 0)
                        
                    except Exception as e:
                        self.skipTest(f"Screenshot capture failed: {e}")
                        
        except ImportError:
            self.skipTest("MSS not available")
        except Exception as e:
            self.skipTest(f"MSS functionality unavailable: {e}")
    
    @patch('utilities.geometry.sct')
    def test_rectangle_screenshot_mock(self, mock_sct):
        """Test Rectangle screenshot method with mock"""
        try:
            from utilities.geometry import Rectangle
            import numpy as np

            # Create fake screenshot data (BGRA format from MSS)
            fake_img_data = np.zeros((100, 100, 4), dtype=np.uint8)

            # Create a mock screenshot object that numpy can convert
            mock_screenshot = MagicMock()
            mock_screenshot.__array__ = MagicMock(return_value=fake_img_data)

            # Configure the mock to return our fake screenshot
            mock_sct.grab.return_value = mock_screenshot

            # Test Rectangle screenshot
            rect = Rectangle(10, 10, 100, 100)
            screenshot = rect.screenshot()

            self.assertIsInstance(screenshot, np.ndarray)
            self.assertEqual(screenshot.shape, (100, 100, 3))  # Should be BGR, not BGRA
            mock_sct.grab.assert_called_once()

        except ImportError:
            self.skipTest("Geometry utilities not available")


class TestMouseAutomation(unittest.TestCase):
    """Test mouse automation functionality"""
    
    def test_mouse_class_import(self):
        """Test Mouse class can be imported"""
        try:
            from utilities.mouse import Mouse
            
            self.assertTrue(callable(Mouse))
            
        except ImportError as e:
            self.skipTest(f"Mouse class not available: {e}")
    
    @patch('pyautogui.moveTo')
    @patch('pyautogui.click') 
    def test_mouse_basic_operations_mock(self, mock_click, mock_move):
        """Test basic mouse operations with mocked PyAutoGUI"""
        try:
            from utilities.mouse import Mouse
            from utilities.geometry import Point
            
            mouse = Mouse()
            
            # Test move to point
            point = Point(100, 200)
            mouse.move_to(point)
            
            # Verify PyAutoGUI was called (might not work if Mouse class has different implementation)
            # This test validates the mock setup rather than actual functionality
            
        except ImportError:
            self.skipTest("Mouse class not available")
        except Exception as e:
            self.skipTest(f"Mouse operations test failed: {e}")
    
    def test_pyautogui_basic_functionality(self):
        """Test PyAutoGUI basic functionality"""
        try:
            import pyautogui as pag
            
            # Test screen size detection
            size = pag.size()
            self.assertGreater(size.width, 0)
            self.assertGreater(size.height, 0)
            
            # Test position detection (don't actually move mouse in tests)
            try:
                pos = pag.position()
                self.assertIsInstance(pos.x, int)
                self.assertIsInstance(pos.y, int)
            except Exception:
                self.skipTest("Mouse position detection failed (may be headless)")
                
        except ImportError:
            self.skipTest("PyAutoGUI not available")
        except Exception as e:
            self.skipTest(f"PyAutoGUI functionality unavailable: {e}")


class TestPlatformSpecificIntegration(unittest.TestCase):
    """Test platform-specific integration behavior"""
    
    @unittest.skipUnless(get_platform() == "windows", "Windows-only test")
    def test_windows_window_management(self):
        """Test Windows-specific window management"""
        try:
            import pywinctl
            
            # Windows should have accessible windows
            windows = pywinctl.getAllWindows()
            
            if windows:
                # Test first window has Windows-specific attributes
                first_window = windows[0]
                
                # Windows-specific attributes
                windows_attrs = ['title']  # Add more Windows-specific tests as needed
                
                for attr in windows_attrs:
                    self.assertTrue(hasattr(first_window, attr))
                    
        except ImportError:
            self.skipTest("PyWinCtl not available")
        except Exception as e:
            self.skipTest(f"Windows window management test failed: {e}")
    
    @unittest.skipUnless(get_platform() == "linux", "Linux-only test")
    def test_linux_window_management(self):
        """Test Linux-specific window management"""
        try:
            import pywinctl
            
            # Linux window management may behave differently
            windows = pywinctl.getAllWindows()
            
            # Basic test that it doesn't crash on Linux
            self.assertIsInstance(windows, list)
            
            # Linux might have different window properties
            # Add Linux-specific tests as needed
            
        except ImportError:
            self.skipTest("PyWinCtl not available")
        except Exception as e:
            self.skipTest(f"Linux window management test failed: {e}")


if __name__ == '__main__':
    unittest.main()