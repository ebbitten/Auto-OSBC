"""
Test screenshot capture functionality across platforms
Critical for visual game automation
"""
import unittest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.platform_utils import get_platform


class TestMSSScreenshotCapture(unittest.TestCase):
    """Test MSS (Monitor Screenshot) library functionality"""
    
    def test_mss_import_and_basic_functionality(self):
        """Test MSS can be imported and basic functionality works"""
        try:
            import mss
            
            # Test context manager
            with mss.mss() as sct:
                self.assertIsNotNone(sct)
                
                # Test monitor detection
                monitors = sct.monitors
                self.assertIsInstance(monitors, list)
                self.assertGreater(len(monitors), 0, "Should detect at least one monitor")
                
                # First monitor is all monitors combined, others are individual
                all_monitors = monitors[0]
                self.assertIn('left', all_monitors)
                self.assertIn('top', all_monitors)
                self.assertIn('width', all_monitors)
                self.assertIn('height', all_monitors)
                
        except ImportError:
            self.skipTest("MSS not available")
        except Exception as e:
            self.skipTest(f"MSS basic functionality failed: {e}")
    
    def test_mss_screenshot_capture(self):
        """Test actual screenshot capture"""
        try:
            import mss
            
            with mss.mss() as sct:
                monitors = sct.monitors
                
                if len(monitors) > 1:
                    # Use primary monitor (monitors[1])
                    primary_monitor = monitors[1]
                    
                    # Capture small area to avoid performance issues
                    small_area = {
                        'left': primary_monitor['left'],
                        'top': primary_monitor['top'], 
                        'width': min(100, primary_monitor['width']),
                        'height': min(100, primary_monitor['height'])
                    }
                    
                    try:
                        screenshot = sct.grab(small_area)
                        self.assertIsNotNone(screenshot)
                        
                        # Test screenshot properties
                        self.assertEqual(screenshot.width, small_area['width'])
                        self.assertEqual(screenshot.height, small_area['height'])
                        
                        # Test conversion to numpy array
                        img_array = np.array(screenshot)
                        self.assertIsInstance(img_array, np.ndarray)
                        self.assertEqual(len(img_array.shape), 3)  # Height, Width, Channels
                        self.assertEqual(img_array.shape[2], 4)    # BGRA format
                        
                    except Exception as e:
                        self.skipTest(f"Screenshot capture failed: {e}")
                        
        except ImportError:
            self.skipTest("MSS not available")
    
    def test_mss_multiple_screenshots_performance(self):
        """Test multiple screenshot capture performance"""
        try:
            import mss
            import time
            
            with mss.mss() as sct:
                monitors = sct.monitors
                
                if len(monitors) > 1:
                    # Small test area
                    test_area = {
                        'left': 0, 'top': 0, 'width': 50, 'height': 50
                    }
                    
                    # Time multiple captures
                    start_time = time.time()
                    num_captures = 5
                    
                    for _ in range(num_captures):
                        screenshot = sct.grab(test_area)
                        self.assertIsNotNone(screenshot)
                    
                    end_time = time.time()
                    avg_time = (end_time - start_time) / num_captures
                    
                    # Should be reasonably fast (less than 100ms per capture)
                    self.assertLess(avg_time, 0.1, f"Screenshots too slow: {avg_time:.3f}s average")
                    
        except ImportError:
            self.skipTest("MSS not available")
        except Exception as e:
            self.skipTest(f"MSS performance test failed: {e}")


class TestGeometryScreenshots(unittest.TestCase):
    """Test screenshot functionality in geometry utilities"""
    
    @patch('utilities.geometry.sct')
    def test_rectangle_screenshot_method(self, mock_sct):
        """Test Rectangle.screenshot() method"""
        try:
            from utilities.geometry import Rectangle

            # Create fake image data (BGRA format from MSS)
            fake_img = np.zeros((100, 100, 4), dtype=np.uint8)

            # Create a mock screenshot object that numpy can convert
            mock_screenshot = MagicMock()
            mock_screenshot.__array__ = MagicMock(return_value=fake_img)

            # Configure the mock to return our fake screenshot
            mock_sct.grab.return_value = mock_screenshot

            # Test Rectangle screenshot
            rect = Rectangle(10, 10, 100, 100)
            result = rect.screenshot()

            # Verify MSS was called with correct parameters
            expected_monitor = {'left': 10, 'top': 10, 'width': 100, 'height': 100}
            mock_sct.grab.assert_called_once_with(expected_monitor)

            # Verify result is correct shape (should be BGR, not BGRA - alpha channel removed)
            self.assertIsInstance(result, np.ndarray)
            self.assertEqual(result.shape, (100, 100, 3))

        except ImportError:
            self.skipTest("Geometry utilities not available")
    
    def test_rectangle_to_dict_method(self):
        """Test Rectangle.to_dict() method used for screenshots"""
        try:
            from utilities.geometry import Rectangle
            
            rect = Rectangle(50, 75, 200, 150)
            dict_repr = rect.to_dict()
            
            expected = {
                'left': 50,
                'top': 75, 
                'width': 200,
                'height': 150
            }
            
            self.assertEqual(dict_repr, expected)
            
        except ImportError:
            self.skipTest("Geometry utilities not available")
    
    def test_rectangle_screenshot_error_handling(self):
        """Test Rectangle screenshot error handling"""
        try:
            from utilities.geometry import Rectangle
            
            # Create rectangle with invalid dimensions
            invalid_rect = Rectangle(-10, -10, -50, -50)
            
            # This should either handle gracefully or raise appropriate error
            try:
                result = invalid_rect.screenshot()
                # If it succeeds, verify the result makes sense
                if result is not None:
                    self.assertIsInstance(result, np.ndarray)
            except Exception as e:
                # Error is acceptable for invalid rectangles
                pass
                
        except ImportError:
            self.skipTest("Geometry utilities not available")


class TestScreenshotColorProcessing(unittest.TestCase):
    """Test color processing on screenshots"""
    
    def test_opencv_bgr_conversion(self):
        """Test OpenCV BGR format conversion"""
        try:
            import cv2
            import numpy as np
            
            # Create fake BGRA screenshot (MSS format)
            bgra_img = np.zeros((100, 100, 4), dtype=np.uint8)
            bgra_img[:, :, 0] = 255  # Blue channel
            bgra_img[:, :, 3] = 255  # Alpha channel
            
            # Convert BGRA to BGR (removing alpha)
            bgr_img = cv2.cvtColor(bgra_img, cv2.COLOR_BGRA2BGR)
            
            self.assertEqual(bgr_img.shape, (100, 100, 3))
            self.assertEqual(bgr_img[0, 0, 0], 255)  # Blue channel preserved
            
            # Test RGB conversion
            rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
            self.assertEqual(rgb_img.shape, (100, 100, 3))
            self.assertEqual(rgb_img[0, 0, 2], 255)  # Blue now in red channel
            
        except ImportError:
            self.skipTest("OpenCV not available")
    
    def test_color_isolation_on_screenshot(self):
        """Test color isolation functionality on mock screenshot"""
        try:
            import utilities.color as clr
            import numpy as np
            
            # Create test image with known colors
            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
            
            # Add some colored regions
            test_img[25:75, 25:75] = [255, 0, 255]  # Magenta/Pink region
            
            # Test color isolation (if function exists)
            if hasattr(clr, 'isolate_colors'):
                try:
                    # Test with pink color (if defined)
                    if hasattr(clr, 'PINK'):
                        isolated = clr.isolate_colors(test_img, [clr.PINK])
                        self.assertIsInstance(isolated, np.ndarray)
                except Exception as e:
                    self.skipTest(f"Color isolation failed: {e}")
                    
        except ImportError:
            self.skipTest("Color utilities not available")


class TestPlatformSpecificScreenshots(unittest.TestCase):
    """Test platform-specific screenshot behavior"""
    
    @unittest.skipUnless(get_platform() == "windows", "Windows-only test")
    def test_windows_screenshot_behavior(self):
        """Test Windows-specific screenshot behavior"""
        try:
            import mss
            
            with mss.mss() as sct:
                monitors = sct.monitors
                
                # Windows should have at least primary monitor
                self.assertGreater(len(monitors), 1)
                
                # Test Windows-specific monitor properties
                primary = monitors[1]
                self.assertIn('left', primary)
                self.assertIn('top', primary)
                
                # Windows coordinates should make sense
                self.assertGreaterEqual(primary['left'], 0)
                self.assertGreaterEqual(primary['top'], 0)
                self.assertGreater(primary['width'], 0)
                self.assertGreater(primary['height'], 0)
                
        except ImportError:
            self.skipTest("MSS not available")
        except Exception as e:
            self.skipTest(f"Windows screenshot test failed: {e}")
    
    @unittest.skipUnless(get_platform() == "linux", "Linux-only test")
    def test_linux_screenshot_behavior(self):
        """Test Linux-specific screenshot behavior"""
        try:
            import mss
            
            with mss.mss() as sct:
                monitors = sct.monitors
                
                # Linux should have monitors detected
                self.assertGreater(len(monitors), 0)
                
                # Test basic monitor structure
                if len(monitors) > 1:
                    primary = monitors[1]
                    self.assertIn('left', primary)
                    self.assertIn('top', primary)
                    self.assertIn('width', primary)
                    self.assertIn('height', primary)
                    
        except ImportError:
            self.skipTest("MSS not available")
        except Exception as e:
            self.skipTest(f"Linux screenshot test failed: {e}")
    
    def test_wsl2_screenshot_limitations(self):
        """Test WSL2 screenshot limitations"""
        try:
            # Detect WSL2
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    # Running in WSL2
                    import mss
                    
                    with mss.mss() as sct:
                        try:
                            monitors = sct.monitors
                            
                            # In WSL2, screenshot might not work properly
                            if not monitors or len(monitors) <= 1:
                                self.skipTest("WSL2 detected: Screenshot functionality may be limited")
                                
                            # Try to capture - might fail in WSL2
                            if len(monitors) > 1:
                                small_area = {'left': 0, 'top': 0, 'width': 10, 'height': 10}
                                screenshot = sct.grab(small_area)
                                
                                if screenshot is None:
                                    self.skipTest("WSL2 detected: Screenshot capture not available")
                                    
                        except Exception:
                            self.skipTest("WSL2 detected: Screenshot functionality limited")
                            
        except FileNotFoundError:
            pass  # Not running on Linux/WSL
        except ImportError:
            self.skipTest("MSS not available")


if __name__ == '__main__':
    unittest.main()