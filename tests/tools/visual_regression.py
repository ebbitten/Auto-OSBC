#!/usr/bin/env python3
"""
Visual Regression Testing for Auto-OSBC
Automated testing to detect when UI changes break bot functionality.
"""

import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utilities.window import Window
from src.utilities import color as clr
from src.utilities import ocr


class VisualRegressionTester:
    """Automated visual regression testing for game automation."""
    
    def __init__(self, reference_dir: Path, output_dir: Path, tolerance: float = 0.05):
        self.reference_dir = reference_dir
        self.output_dir = output_dir
        self.tolerance = tolerance
        self.window: Optional[Window] = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test results
        self.results = {
            "timestamp": time.time(),
            "tolerance": tolerance,
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
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
    
    def compare_screenshots(self, reference_path: Path, current_image: np.ndarray, test_name: str) -> Dict:
        """Compare reference image with current screenshot."""
        if not reference_path.exists():
            return {
                "status": "skipped",
                "reason": f"Reference image not found: {reference_path}",
                "similarity": 0.0,
                "pixel_diff_percentage": 100.0
            }
        
        try:
            ref_img = cv2.imread(str(reference_path))
            if ref_img is None:
                return {
                    "status": "error",
                    "reason": f"Could not load reference image: {reference_path}",
                    "similarity": 0.0,
                    "pixel_diff_percentage": 100.0
                }
            
            # Resize current image to match reference if needed
            if ref_img.shape != current_image.shape:
                current_image = cv2.resize(current_image, (ref_img.shape[1], ref_img.shape[0]))
            
            # Calculate structural similarity
            similarity = ssim(ref_img, current_image, multichannel=True, channel_axis=2)
            
            # Calculate pixel differences
            diff = cv2.absdiff(ref_img, current_image)
            diff_mask = np.any(diff > 10, axis=2)
            pixel_diff_percentage = (np.sum(diff_mask) / diff_mask.size) * 100
            
            # Generate difference visualization
            diff_highlighted = current_image.copy()
            diff_highlighted[diff_mask] = [0, 0, 255]  # Highlight differences in red
            
            # Save comparison images
            current_path = self.output_dir / f"{test_name}_current.png"
            diff_path = self.output_dir / f"{test_name}_diff.png"
            
            cv2.imwrite(str(current_path), current_image)
            cv2.imwrite(str(diff_path), diff_highlighted)
            
            # Determine if test passed
            passed = similarity > (1 - self.tolerance)
            
            result = {
                "status": "passed" if passed else "failed",
                "similarity": similarity,
                "pixel_diff_percentage": pixel_diff_percentage,
                "reference_image": str(reference_path),
                "current_image": str(current_path),
                "diff_image": str(diff_path)
            }
            
            if not passed:
                result["reason"] = f"Similarity {similarity:.3f} below threshold {1-self.tolerance:.3f}"
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e),
                "similarity": 0.0,
                "pixel_diff_percentage": 100.0
            }
    
    def test_ui_elements(self) -> Dict[str, Dict]:
        """Test core UI element detection."""
        if not self.window:
            return {"error": "Window not initialized"}
        
        results = {}
        
        # Test regions
        test_regions = {
            "game_view": self.window.game_view,
            "control_panel": self.window.control_panel,
            "minimap_area": self.window.minimap_area,
            "chat": self.window.chat
        }
        
        for region_name, region in test_regions.items():
            try:
                current_screenshot = region.screenshot()
                reference_path = self.reference_dir / f"{region_name}.png"
                
                result = self.compare_screenshots(reference_path, current_screenshot, region_name)
                results[region_name] = result
                
                # Update summary
                self.results["summary"]["total"] += 1
                if result["status"] == "passed":
                    self.results["summary"]["passed"] += 1
                    print(f"✅ {region_name}: PASSED (similarity: {result['similarity']:.3f})")
                elif result["status"] == "failed":
                    self.results["summary"]["failed"] += 1
                    print(f"❌ {region_name}: FAILED ({result['reason']})")
                elif result["status"] == "skipped":
                    self.results["summary"]["skipped"] += 1
                    print(f"⏭️  {region_name}: SKIPPED ({result['reason']})")
                else:
                    self.results["summary"]["failed"] += 1
                    print(f"💥 {region_name}: ERROR ({result['reason']})")
                
            except Exception as e:
                results[region_name] = {
                    "status": "error",
                    "reason": str(e),
                    "similarity": 0.0,
                    "pixel_diff_percentage": 100.0
                }
                self.results["summary"]["total"] += 1
                self.results["summary"]["failed"] += 1
                print(f"💥 {region_name}: ERROR ({e})")
        
        return results
    
    def test_inventory_detection(self) -> Dict[str, Dict]:
        """Test inventory slot detection accuracy."""
        if not self.window:
            return {"error": "Window not initialized"}
        
        results = {}
        
        try:
            # Capture current inventory
            inventory_screenshot = self.window.control_panel.screenshot()
            
            # Create overlay with detected slots
            overlay = inventory_screenshot.copy()
            
            # Test slot detection
            detected_slots = len(self.window.inventory_slots)
            expected_slots = 28
            
            if detected_slots == expected_slots:
                # Draw all slots
                for i, slot in enumerate(self.window.inventory_slots):
                    rel_x = slot.left - self.window.control_panel.left
                    rel_y = slot.top - self.window.control_panel.top
                    
                    cv2.rectangle(overlay,
                                 (rel_x, rel_y),
                                 (rel_x + slot.width, rel_y + slot.height),
                                 (0, 255, 0), 1)
                
                # Compare with reference
                reference_path = self.reference_dir / "inventory_slots.png"
                result = self.compare_screenshots(reference_path, overlay, "inventory_slots")
                
            else:
                result = {
                    "status": "failed",
                    "reason": f"Expected 28 slots, detected {detected_slots}",
                    "similarity": 0.0,
                    "pixel_diff_percentage": 100.0
                }
            
            results["inventory_slots"] = result
            
            # Update summary
            self.results["summary"]["total"] += 1
            if result["status"] == "passed":
                self.results["summary"]["passed"] += 1
                print(f"✅ inventory_slots: PASSED")
            else:
                self.results["summary"]["failed"] += 1
                print(f"❌ inventory_slots: FAILED ({result.get('reason', 'Unknown error')})")
            
        except Exception as e:
            results["inventory_slots"] = {
                "status": "error",
                "reason": str(e),
                "similarity": 0.0,
                "pixel_diff_percentage": 100.0
            }
            self.results["summary"]["total"] += 1
            self.results["summary"]["failed"] += 1
            print(f"💥 inventory_slots: ERROR ({e})")
        
        return results
    
    def test_color_detection(self) -> Dict[str, Dict]:
        """Test color detection accuracy."""
        if not self.window:
            return {"error": "Window not initialized"}
        
        results = {}
        
        # Test colors
        test_colors = [clr.CYAN, clr.PINK, clr.PURPLE, clr.GREEN, clr.RED]
        
        try:
            game_screenshot = self.window.game_view.screenshot()
            
            for color in test_colors:
                color_name = color.name.lower()
                
                try:
                    # Isolate color
                    isolated = clr.isolate_colors(game_screenshot, color)
                    
                    # Compare with reference
                    reference_path = self.reference_dir / f"color_{color_name}.png"
                    result = self.compare_screenshots(reference_path, isolated, f"color_{color_name}")
                    
                    results[f"color_{color_name}"] = result
                    
                    # Update summary
                    self.results["summary"]["total"] += 1
                    if result["status"] == "passed":
                        self.results["summary"]["passed"] += 1
                        print(f"✅ color_{color_name}: PASSED")
                    elif result["status"] == "skipped":
                        self.results["summary"]["skipped"] += 1
                        print(f"⏭️  color_{color_name}: SKIPPED")
                    else:
                        self.results["summary"]["failed"] += 1
                        print(f"❌ color_{color_name}: FAILED")
                
                except Exception as e:
                    results[f"color_{color_name}"] = {
                        "status": "error",
                        "reason": str(e),
                        "similarity": 0.0,
                        "pixel_diff_percentage": 100.0
                    }
                    self.results["summary"]["total"] += 1
                    self.results["summary"]["failed"] += 1
                    print(f"💥 color_{color_name}: ERROR ({e})")
        
        except Exception as e:
            print(f"💥 Color detection test failed: {e}")
        
        return results
    
    def test_ocr_accuracy(self) -> Dict[str, Dict]:
        """Test OCR text extraction accuracy."""
        if not self.window:
            return {"error": "Window not initialized"}
        
        results = {}
        
        # Test OCR regions
        ocr_regions = {
            "hp_orb": self.window.hp_orb_text,
            "prayer_orb": self.window.prayer_orb_text,
            "run_orb": self.window.run_orb_text
        }
        
        for region_name, region in ocr_regions.items():
            try:
                # Capture region
                region_screenshot = region.screenshot()
                
                # Test OCR extraction
                fonts = [ocr.PLAIN_11, ocr.PLAIN_12]
                colors = [clr.ORB_GREEN, clr.WHITE]
                
                extracted_texts = []
                for font in fonts:
                    for color in colors:
                        try:
                            text = ocr.extract_text(region, font, [color])
                            if text:
                                extracted_texts.append(text)
                        except:
                            pass
                
                # Compare region screenshot with reference
                reference_path = self.reference_dir / f"ocr_{region_name}.png"
                result = self.compare_screenshots(reference_path, region_screenshot, f"ocr_{region_name}")
                
                # Add OCR results to result
                result["extracted_texts"] = extracted_texts
                result["ocr_success"] = len(extracted_texts) > 0
                
                results[f"ocr_{region_name}"] = result
                
                # Update summary
                self.results["summary"]["total"] += 1
                if result["status"] == "passed":
                    self.results["summary"]["passed"] += 1
                    print(f"✅ ocr_{region_name}: PASSED (extracted: {extracted_texts})")
                elif result["status"] == "skipped":
                    self.results["summary"]["skipped"] += 1
                    print(f"⏭️  ocr_{region_name}: SKIPPED")
                else:
                    self.results["summary"]["failed"] += 1
                    print(f"❌ ocr_{region_name}: FAILED")
                
            except Exception as e:
                results[f"ocr_{region_name}"] = {
                    "status": "error",
                    "reason": str(e),
                    "similarity": 0.0,
                    "pixel_diff_percentage": 100.0
                }
                self.results["summary"]["total"] += 1
                self.results["summary"]["failed"] += 1
                print(f"💥 ocr_{region_name}: ERROR ({e})")
        
        return results
    
    def run_all_tests(self, window_title: str = "RuneLite") -> bool:
        """Run complete visual regression test suite."""
        print("🔍 Starting Visual Regression Tests")
        print("=" * 50)
        
        # Initialize window
        if not self.setup_window(window_title):
            print("❌ Cannot run tests without game window")
            return False
        
        # Run test suites
        print("\n📋 Testing UI Elements...")
        ui_results = self.test_ui_elements()
        self.results["tests"]["ui_elements"] = ui_results
        
        print("\n📦 Testing Inventory Detection...")
        inventory_results = self.test_inventory_detection()
        self.results["tests"]["inventory_detection"] = inventory_results
        
        print("\n🎨 Testing Color Detection...")
        color_results = self.test_color_detection()
        self.results["tests"]["color_detection"] = color_results
        
        print("\n📖 Testing OCR Accuracy...")
        ocr_results = self.test_ocr_accuracy()
        self.results["tests"]["ocr_accuracy"] = ocr_results
        
        # Generate summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        skipped = summary["skipped"]
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)" if total > 0 else "✅ Passed: 0")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)" if total > 0 else "❌ Failed: 0")
        print(f"⏭️  Skipped: {skipped} ({skipped/total*100:.1f}%)" if total > 0 else "⏭️  Skipped: 0")
        
        # Save results
        results_file = self.output_dir / f"regression_test_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Overall result
        success = failed == 0
        if success:
            print("🎉 All visual regression tests passed!")
        else:
            print(f"⚠️  {failed} test(s) failed. Review results for details.")
        
        return success
    
    def create_reference_baseline(self, window_title: str = "RuneLite") -> bool:
        """Create reference images for future regression testing."""
        print("📸 Creating Visual Regression Reference Baseline")
        print("=" * 50)
        
        if not self.setup_window(window_title):
            print("❌ Cannot create baseline without game window")
            return False
        
        # Create reference directory
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        
        captures = 0
        
        try:
            # Capture UI elements
            ui_regions = {
                "game_view": self.window.game_view,
                "control_panel": self.window.control_panel,
                "minimap_area": self.window.minimap_area,
                "chat": self.window.chat
            }
            
            print("📋 Capturing UI elements...")
            for region_name, region in ui_regions.items():
                screenshot = region.screenshot()
                ref_path = self.reference_dir / f"{region_name}.png"
                cv2.imwrite(str(ref_path), screenshot)
                print(f"   ✅ {region_name}: {ref_path}")
                captures += 1
            
            # Capture inventory with slots
            print("📦 Capturing inventory slots...")
            inventory_screenshot = self.window.control_panel.screenshot()
            overlay = inventory_screenshot.copy()
            
            for i, slot in enumerate(self.window.inventory_slots):
                rel_x = slot.left - self.window.control_panel.left
                rel_y = slot.top - self.window.control_panel.top
                cv2.rectangle(overlay, (rel_x, rel_y),
                             (rel_x + slot.width, rel_y + slot.height),
                             (0, 255, 0), 1)
            
            ref_path = self.reference_dir / "inventory_slots.png"
            cv2.imwrite(str(ref_path), overlay)
            print(f"   ✅ inventory_slots: {ref_path}")
            captures += 1
            
            # Capture color isolations
            print("🎨 Capturing color isolations...")
            game_screenshot = self.window.game_view.screenshot()
            test_colors = [clr.CYAN, clr.PINK, clr.PURPLE, clr.GREEN, clr.RED]
            
            for color in test_colors:
                isolated = clr.isolate_colors(game_screenshot, color)
                ref_path = self.reference_dir / f"color_{color.name.lower()}.png"
                cv2.imwrite(str(ref_path), isolated)
                print(f"   ✅ color_{color.name.lower()}: {ref_path}")
                captures += 1
            
            # Capture OCR regions
            print("📖 Capturing OCR regions...")
            ocr_regions = {
                "hp_orb": self.window.hp_orb_text,
                "prayer_orb": self.window.prayer_orb_text,
                "run_orb": self.window.run_orb_text
            }
            
            for region_name, region in ocr_regions.items():
                screenshot = region.screenshot()
                ref_path = self.reference_dir / f"ocr_{region_name}.png"
                cv2.imwrite(str(ref_path), screenshot)
                print(f"   ✅ ocr_{region_name}: {ref_path}")
                captures += 1
            
            # Create metadata
            metadata = {
                "created_timestamp": time.time(),
                "window_title": window_title,
                "client_mode": "fixed" if self.window.client_fixed else "resizable",
                "game_view_size": f"{self.window.game_view.width}x{self.window.game_view.height}",
                "total_captures": captures,
                "reference_files": [f.name for f in self.reference_dir.glob("*.png")]
            }
            
            metadata_file = self.reference_dir / "baseline_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\n✅ Reference baseline created successfully!")
            print(f"   Total captures: {captures}")
            print(f"   Reference directory: {self.reference_dir}")
            print(f"   Metadata: {metadata_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create baseline: {e}")
            return False


def main():
    """Command-line interface for visual regression testing."""
    parser = argparse.ArgumentParser(description="Auto-OSBC Visual Regression Testing")
    parser.add_argument("--window", default="RuneLite", help="Game window title")
    parser.add_argument("--reference-dir", type=Path, default=Path("tests/visual_references"),
                       help="Directory containing reference images")
    parser.add_argument("--output-dir", type=Path, default=Path("debug_screenshots/regression_tests"),
                       help="Directory for test output")
    parser.add_argument("--tolerance", type=float, default=0.05,
                       help="Similarity tolerance (0.0 = exact match, 1.0 = no match)")
    parser.add_argument("--create-baseline", action="store_true",
                       help="Create reference baseline instead of running tests")
    
    args = parser.parse_args()
    
    # Create tester
    tester = VisualRegressionTester(args.reference_dir, args.output_dir, args.tolerance)
    
    try:
        if args.create_baseline:
            success = tester.create_reference_baseline(args.window)
        else:
            success = tester.run_all_tests(args.window)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())