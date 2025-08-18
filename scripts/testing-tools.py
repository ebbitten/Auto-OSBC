#!/usr/bin/env python3
"""
Visual Testing Tools for Auto-OSBC
Provides utilities for visual debugging, regression testing, and performance validation.
"""

import cv2
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from skimage.metrics import structural_similarity as ssim

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utilities import color as clr
from src.utilities import debug
from src.utilities.geometry import Rectangle, Point
from src.utilities.window import Window


class VisualTestingTools:
    """Comprehensive visual testing and debugging utilities."""
    
    def __init__(self, debug_dir: Optional[Path] = None):
        self.debug_dir = debug_dir or Path("debug_screenshots")
        self.debug_dir.mkdir(exist_ok=True)
        
        # Initialize window for testing
        self.window = None
        self.last_screenshot = None
        
    def setup_window(self, window_title: str = "RuneLite") -> bool:
        """Initialize game window for testing."""
        try:
            self.window = Window(window_title, padding_top=26, padding_left=0)
            self.window.initialize()
            print(f"✅ Window '{window_title}' initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize window: {e}")
            return False
    
    def capture_current_state(self, description: str = "manual_capture") -> Dict[str, Path]:
        """Capture current game state across all regions."""
        if not self.window:
            raise ValueError("Window not initialized. Call setup_window() first.")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        captures = {}
        
        # Capture all relevant areas
        regions = {
            'game_view': self.window.game_view,
            'inventory': self.window.control_panel,
            'minimap': self.window.minimap_area,
            'chat': self.window.chat,
            'full_client': self.window.rectangle()
        }
        
        for region_name, region in regions.items():
            try:
                screenshot = region.screenshot()
                filename = f"{timestamp}_{description}_{region_name}.png"
                filepath = self.debug_dir / filename
                cv2.imwrite(str(filepath), screenshot)
                captures[region_name] = filepath
                print(f"📸 Captured {region_name}: {filepath}")
            except Exception as e:
                print(f"⚠️  Failed to capture {region_name}: {e}")
        
        return captures
    
    def test_color_detection(self, target_colors: List[clr.Color], description: str = "color_test") -> Dict:
        """Test color detection with current game state."""
        if not self.window:
            raise ValueError("Window not initialized. Call setup_window() first.")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results = {}
        
        # Capture base screenshot
        base_screenshot = self.window.game_view.screenshot()
        base_path = self.debug_dir / f"{timestamp}_{description}_original.png"
        cv2.imwrite(str(base_path), base_screenshot)
        
        for i, color in enumerate(target_colors):
            try:
                # Isolate color
                isolated = clr.isolate_colors(base_screenshot, color)
                isolated_path = self.debug_dir / f"{timestamp}_{description}_color_{i}_{color.name}.png"
                cv2.imwrite(str(isolated_path), isolated)
                
                # Count non-zero pixels
                non_zero_pixels = np.count_nonzero(isolated)
                total_pixels = isolated.size
                coverage_percentage = (non_zero_pixels / total_pixels) * 100
                
                results[color.name] = {
                    "coverage_percentage": coverage_percentage,
                    "non_zero_pixels": non_zero_pixels,
                    "isolated_image": str(isolated_path)
                }
                
                print(f"🎨 Color {color.name}: {coverage_percentage:.2f}% coverage ({non_zero_pixels} pixels)")
                
            except Exception as e:
                print(f"❌ Error processing color {color.name}: {e}")
                results[color.name] = {"error": str(e)}
        
        # Save results
        results_path = self.debug_dir / f"{timestamp}_{description}_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results
    
    def test_object_detection(self, target_colors: List[clr.Color], description: str = "object_test") -> Dict:
        """Test object detection and contour extraction."""
        if not self.window:
            raise ValueError("Window not initialized. Call setup_window() first.")
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results = {}
        
        # Import here to avoid circular imports
        from src.utilities import runelite_cv as rcv
        
        base_screenshot = self.window.game_view.screenshot()
        
        for i, color in enumerate(target_colors):
            try:
                # Color isolation
                isolated = clr.isolate_colors(base_screenshot, color)
                
                # Object extraction
                objects = rcv.extract_objects(isolated)
                
                # Create overlay with detected objects
                overlay = base_screenshot.copy()
                for obj in objects:
                    cv2.rectangle(overlay,
                                (obj.left, obj.top),
                                (obj.left + obj.width, obj.top + obj.height),
                                (0, 255, 0), 2)
                    cv2.putText(overlay, f"{obj.width}x{obj.height}",
                              (obj.left, obj.top - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                overlay_path = self.debug_dir / f"{timestamp}_{description}_objects_{color.name}.png"
                cv2.imwrite(str(overlay_path), overlay)
                
                results[color.name] = {
                    "object_count": len(objects),
                    "objects": [
                        {
                            "x": obj.left,
                            "y": obj.top,
                            "width": obj.width,
                            "height": obj.height,
                            "area": obj.width * obj.height
                        }
                        for obj in objects
                    ],
                    "overlay_image": str(overlay_path)
                }
                
                print(f"🔍 {color.name}: Found {len(objects)} objects")
                
            except Exception as e:
                print(f"❌ Error detecting objects for {color.name}: {e}")
                results[color.name] = {"error": str(e)}
        
        return results
    
    def test_ocr_extraction(self, regions: Optional[Dict[str, Rectangle]] = None, description: str = "ocr_test") -> Dict:
        """Test OCR text extraction from various regions."""
        if not self.window:
            raise ValueError("Window not initialized. Call setup_window() first.")
        
        # Import here to avoid circular imports
        from src.utilities import ocr
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results = {}
        
        # Default regions if none provided
        if regions is None:
            regions = {
                "hp_orb": self.window.hp_orb_text,
                "prayer_orb": self.window.prayer_orb_text,
                "run_orb": self.window.run_orb_text,
                "chat_area": self.window.chat
            }
        
        fonts = [ocr.PLAIN_11, ocr.PLAIN_12, ocr.BOLD_12]
        colors = [clr.WHITE, clr.BLACK, clr.ORB_GREEN, clr.YELLOW]
        
        for region_name, region in regions.items():
            region_results = {}
            
            try:
                # Capture region
                region_screenshot = region.screenshot()
                region_path = self.debug_dir / f"{timestamp}_{description}_{region_name}_region.png"
                cv2.imwrite(str(region_path), region_screenshot)
                
                # Test different font and color combinations
                for font in fonts:
                    font_results = {}
                    for color in colors:
                        try:
                            extracted_text = ocr.extract_text(region, font, [color])
                            font_results[color.name] = {
                                "text": extracted_text,
                                "length": len(extracted_text) if extracted_text else 0
                            }
                        except Exception as e:
                            font_results[color.name] = {"error": str(e)}
                    
                    region_results[font] = font_results
                
                results[region_name] = {
                    "region_image": str(region_path),
                    "extractions": region_results
                }
                
                print(f"📖 OCR tested for region: {region_name}")
                
            except Exception as e:
                print(f"❌ Error testing OCR for {region_name}: {e}")
                results[region_name] = {"error": str(e)}
        
        return results
    
    def compare_screenshots(self, reference_path: str, current_path: str, tolerance: float = 0.05) -> Dict:
        """Compare two screenshots for visual regression testing."""
        try:
            ref_img = cv2.imread(reference_path)
            cur_img = cv2.imread(current_path)
            
            if ref_img is None:
                return {"error": f"Could not load reference image: {reference_path}"}
            if cur_img is None:
                return {"error": f"Could not load current image: {current_path}"}
            
            # Resize to same dimensions if needed
            if ref_img.shape != cur_img.shape:
                cur_img = cv2.resize(cur_img, (ref_img.shape[1], ref_img.shape[0]))
            
            # Calculate similarity
            similarity = ssim(ref_img, cur_img, multichannel=True)
            
            # Calculate pixel differences
            diff = cv2.absdiff(ref_img, cur_img)
            diff_mask = np.any(diff > 10, axis=2)
            pixel_diff_percentage = (np.sum(diff_mask) / diff_mask.size) * 100
            
            # Generate difference visualization
            diff_highlighted = cur_img.copy()
            diff_highlighted[diff_mask] = [0, 0, 255]  # Highlight differences in red
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            diff_path = self.debug_dir / f"{timestamp}_comparison_diff.png"
            cv2.imwrite(str(diff_path), diff_highlighted)
            
            passed = similarity > (1 - tolerance)
            
            result = {
                "similarity": similarity,
                "pixel_diff_percentage": pixel_diff_percentage,
                "tolerance": tolerance,
                "passed": passed,
                "diff_image": str(diff_path),
                "reference_image": reference_path,
                "current_image": current_path
            }
            
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status} Visual comparison: {similarity:.3f} similarity, {pixel_diff_percentage:.2f}% diff")
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def performance_benchmark(self, iterations: int = 10, description: str = "benchmark") -> Dict:
        """Benchmark detection performance."""
        if not self.window:
            raise ValueError("Window not initialized. Call setup_window() first.")
        
        print(f"🏃 Running performance benchmark ({iterations} iterations)...")
        
        results = {
            "iterations": iterations,
            "screenshot_times": [],
            "color_detection_times": [],
            "object_detection_times": []
        }
        
        # Import here to avoid circular imports
        from src.utilities import runelite_cv as rcv
        
        test_colors = [clr.CYAN, clr.PINK, clr.PURPLE]
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}")
            
            # Benchmark screenshot capture
            start_time = time.time()
            screenshot = self.window.game_view.screenshot()
            screenshot_time = time.time() - start_time
            results["screenshot_times"].append(screenshot_time)
            
            # Benchmark color detection
            start_time = time.time()
            for color in test_colors:
                isolated = clr.isolate_colors(screenshot, color)
            color_detection_time = time.time() - start_time
            results["color_detection_times"].append(color_detection_time)
            
            # Benchmark object detection
            start_time = time.time()
            for color in test_colors:
                isolated = clr.isolate_colors(screenshot, color)
                objects = rcv.extract_objects(isolated)
            object_detection_time = time.time() - start_time
            results["object_detection_times"].append(object_detection_time)
        
        # Calculate statistics
        for metric in ["screenshot_times", "color_detection_times", "object_detection_times"]:
            times = results[metric]
            results[f"{metric}_avg"] = sum(times) / len(times)
            results[f"{metric}_min"] = min(times)
            results[f"{metric}_max"] = max(times)
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_path = self.debug_dir / f"{timestamp}_{description}_benchmark.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"📊 Performance Results:")
        print(f"  Screenshot: {results['screenshot_times_avg']:.3f}s avg (target: <0.050s)")
        print(f"  Color Detection: {results['color_detection_times_avg']:.3f}s avg")
        print(f"  Object Detection: {results['object_detection_times_avg']:.3f}s avg (target: <0.100s)")
        
        return results
    
    def generate_test_report(self, test_results: Dict, report_name: str = "test_report") -> Path:
        """Generate comprehensive test report."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = self.debug_dir / f"{timestamp}_{report_name}.md"
        
        report = f"""# Visual Testing Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Summary
"""
        
        for test_name, results in test_results.items():
            report += f"\n### {test_name.replace('_', ' ').title()}\n"
            
            if "error" in results:
                report += f"❌ **Error**: {results['error']}\n"
            else:
                # Add test-specific reporting
                if "coverage_percentage" in results:
                    report += f"Coverage: {results['coverage_percentage']:.2f}%\n"
                elif "object_count" in results:
                    report += f"Objects detected: {results['object_count']}\n"
                elif "similarity" in results:
                    status = "✅ PASSED" if results['passed'] else "❌ FAILED"
                    report += f"Result: {status}\n"
                    report += f"Similarity: {results['similarity']:.3f}\n"
        
        report += f"\n## Debug Files\nAll debug files saved to: `{self.debug_dir}`\n"
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"📋 Test report generated: {report_path}")
        return report_path


def main():
    """Command-line interface for visual testing tools."""
    parser = argparse.ArgumentParser(description="Auto-OSBC Visual Testing Tools")
    parser.add_argument("--window", default="RuneLite", help="Game window title")
    parser.add_argument("--debug-dir", help="Debug output directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Capture current game state")
    capture_parser.add_argument("description", help="Description for the capture")
    
    # Color test command
    color_parser = subparsers.add_parser("color-test", help="Test color detection")
    color_parser.add_argument("--colors", nargs="+", choices=["CYAN", "PINK", "PURPLE", "GREEN", "RED"],
                             default=["CYAN", "PINK"], help="Colors to test")
    
    # Object test command
    object_parser = subparsers.add_parser("object-test", help="Test object detection")
    object_parser.add_argument("--colors", nargs="+", choices=["CYAN", "PINK", "PURPLE", "GREEN", "RED"],
                              default=["CYAN", "PINK"], help="Colors to test")
    
    # OCR test command
    ocr_parser = subparsers.add_parser("ocr-test", help="Test OCR extraction")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare screenshots")
    compare_parser.add_argument("reference", help="Reference image path")
    compare_parser.add_argument("current", help="Current image path")
    compare_parser.add_argument("--tolerance", type=float, default=0.05, help="Comparison tolerance")
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run performance benchmark")
    benchmark_parser.add_argument("--iterations", type=int, default=10, help="Number of iterations")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize tools
    debug_dir = Path(args.debug_dir) if args.debug_dir else None
    tools = VisualTestingTools(debug_dir)
    
    if args.command != "compare":
        if not tools.setup_window(args.window):
            print("❌ Failed to setup window. Ensure game client is running.")
            return
    
    # Execute command
    try:
        if args.command == "capture":
            tools.capture_current_state(args.description)
        
        elif args.command == "color-test":
            colors = [getattr(clr, color) for color in args.colors]
            results = tools.test_color_detection(colors)
            tools.generate_test_report({"color_detection": results})
        
        elif args.command == "object-test":
            colors = [getattr(clr, color) for color in args.colors]
            results = tools.test_object_detection(colors)
            tools.generate_test_report({"object_detection": results})
        
        elif args.command == "ocr-test":
            results = tools.test_ocr_extraction()
            tools.generate_test_report({"ocr_extraction": results})
        
        elif args.command == "compare":
            results = tools.compare_screenshots(args.reference, args.current, args.tolerance)
            tools.generate_test_report({"screenshot_comparison": results})
        
        elif args.command == "benchmark":
            results = tools.performance_benchmark(args.iterations)
            tools.generate_test_report({"performance_benchmark": results})
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error executing command: {e}")


if __name__ == "__main__":
    main()