#!/usr/bin/env python3
"""
Performance Profiler for Auto-OSBC
Benchmarks critical operations and identifies performance bottlenecks.
"""

import sys
import time
import json
import argparse
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import psutil
import cv2
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utilities.window import Window
from src.utilities import color as clr
from src.utilities import ocr
from src.utilities import imagesearch as imsearch


class PerformanceProfiler:
    """Performance profiling and benchmarking for game automation operations."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("debug_screenshots") / f"performance_profile_{int(time.time())}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.window: Optional[Window] = None
        self.test_screenshot: Optional[np.ndarray] = None
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            "screenshot_capture": 0.050,    # 50ms
            "color_detection": 0.100,       # 100ms
            "object_extraction": 0.150,     # 150ms
            "ocr_extraction": 0.200,        # 200ms
            "image_search": 0.300,          # 300ms
            "mouse_movement": 0.500,        # 500ms
        }
        
        # Results storage
        self.results = {
            "timestamp": time.time(),
            "system_info": self._get_system_info(),
            "thresholds": self.thresholds,
            "benchmarks": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warnings": []
            }
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Collect system information for performance context."""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "python_version": sys.version,
                "opencv_version": cv2.__version__
            }
        except Exception as e:
            return {"error": str(e)}
    
    def setup_window(self, window_title: str = "RuneLite") -> bool:
        """Initialize game window for testing."""
        try:
            self.window = Window(window_title, padding_top=26, padding_left=0)
            self.window.initialize()
            
            # Capture test screenshot
            self.test_screenshot = self.window.game_view.screenshot()
            
            print(f"✅ Window '{window_title}' initialized successfully")
            print(f"   Game view: {self.window.game_view.width}x{self.window.game_view.height}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize window: {e}")
            return False
    
    def time_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Time a function execution and return detailed results."""
        # Warm up (exclude from timing)
        try:
            func(*args, **kwargs)
        except:
            pass  # Warm-up can fail
        
        # Actual timing
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        return {
            "execution_time": execution_time,
            "memory_delta": memory_delta,
            "success": success,
            "error": error,
            "result": result
        }
    
    def benchmark_operation(self, operation_name: str, func: Callable, iterations: int = 10, 
                          *args, **kwargs) -> Dict[str, Any]:
        """Benchmark an operation multiple times and return statistics."""
        print(f"🏃 Benchmarking {operation_name} ({iterations} iterations)...")
        
        times = []
        memory_deltas = []
        successes = 0
        errors = []
        
        for i in range(iterations):
            result = self.time_function(func, *args, **kwargs)
            
            if result["success"]:
                times.append(result["execution_time"])
                memory_deltas.append(result["memory_delta"])
                successes += 1
            else:
                errors.append(result["error"])
            
            print(f"   Iteration {i+1}/{iterations}: {result['execution_time']*1000:.1f}ms", end="")
            if not result["success"]:
                print(f" ❌ {result['error']}")
            else:
                print()
        
        if not times:
            return {
                "operation": operation_name,
                "iterations": iterations,
                "success_rate": 0.0,
                "errors": errors,
                "status": "failed"
            }
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)
        
        avg_memory = statistics.mean(memory_deltas) if memory_deltas else 0
        
        # Check against threshold
        threshold = self.thresholds.get(operation_name, float('inf'))
        passed = avg_time <= threshold
        
        benchmark_result = {
            "operation": operation_name,
            "iterations": iterations,
            "success_rate": successes / iterations,
            "times": {
                "average": avg_time,
                "median": median_time,
                "std_dev": std_time,
                "min": min_time,
                "max": max_time
            },
            "memory": {
                "average_delta": avg_memory
            },
            "threshold": threshold,
            "passed": passed,
            "status": "passed" if passed else "failed",
            "errors": errors
        }
        
        # Update summary
        self.results["summary"]["total_tests"] += 1
        if passed:
            self.results["summary"]["passed_tests"] += 1
            print(f"   ✅ PASSED: {avg_time*1000:.1f}ms avg (threshold: {threshold*1000:.0f}ms)")
        else:
            self.results["summary"]["failed_tests"] += 1
            print(f"   ❌ FAILED: {avg_time*1000:.1f}ms avg exceeds {threshold*1000:.0f}ms threshold")
        
        # Add warnings for borderline performance
        if passed and avg_time > threshold * 0.8:
            warning = f"{operation_name} approaching threshold: {avg_time*1000:.1f}ms"
            self.results["summary"]["warnings"].append(warning)
            print(f"   ⚠️  Warning: {warning}")
        
        return benchmark_result
    
    def benchmark_screenshot_capture(self, iterations: int = 20) -> Dict[str, Any]:
        """Benchmark screenshot capture operations."""
        if not self.window:
            return {"error": "Window not initialized"}
        
        def capture_game_view():
            return self.window.game_view.screenshot()
        
        return self.benchmark_operation("screenshot_capture", capture_game_view, iterations)
    
    def benchmark_color_detection(self, iterations: int = 15) -> Dict[str, Any]:
        """Benchmark color isolation operations."""
        if self.test_screenshot is None:
            return {"error": "No test screenshot available"}
        
        def isolate_cyan():
            return clr.isolate_colors(self.test_screenshot, clr.CYAN)
        
        return self.benchmark_operation("color_detection", isolate_cyan, iterations)
    
    def benchmark_object_extraction(self, iterations: int = 10) -> Dict[str, Any]:
        """Benchmark object extraction from isolated colors."""
        if self.test_screenshot is None:
            return {"error": "No test screenshot available"}
        
        # Import here to avoid circular imports
        from src.utilities import runelite_cv as rcv
        
        def extract_objects():
            isolated = clr.isolate_colors(self.test_screenshot, clr.CYAN)
            return rcv.extract_objects(isolated)
        
        return self.benchmark_operation("object_extraction", extract_objects, iterations)
    
    def benchmark_ocr_extraction(self, iterations: int = 10) -> Dict[str, Any]:
        """Benchmark OCR text extraction."""
        if not self.window:
            return {"error": "Window not initialized"}
        
        def extract_hp_text():
            return ocr.extract_text(self.window.hp_orb_text, ocr.PLAIN_11, [clr.ORB_GREEN])
        
        return self.benchmark_operation("ocr_extraction", extract_hp_text, iterations)
    
    def benchmark_image_search(self, iterations: int = 8) -> Dict[str, Any]:
        """Benchmark template image searching."""
        if self.test_screenshot is None:
            return {"error": "No test screenshot available"}
        
        # Create a small template from the screenshot for testing
        template = self.test_screenshot[50:100, 50:100]
        template_path = self.output_dir / "test_template.png"
        cv2.imwrite(str(template_path), template)
        
        def search_template():
            return imsearch.search_img_in_rect(str(template_path), self.test_screenshot, 0.1)
        
        return self.benchmark_operation("image_search", search_template, iterations)
    
    def benchmark_mouse_simulation(self, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark mouse movement simulation (without actual movement)."""
        try:
            from src.utilities.mouse import Mouse
            mouse = Mouse()
            
            def simulate_movement():
                # Simulate movement calculation without actual mouse movement
                start_point = (100, 100)
                end_point = (200, 200)
                # This would normally move the mouse, but we'll just time the calculation
                return mouse._calculate_bezier_curve(start_point, end_point, 10)
            
            return self.benchmark_operation("mouse_movement", simulate_movement, iterations)
            
        except Exception as e:
            return {"error": f"Mouse simulation failed: {e}"}
    
    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage during operations."""
        if not self.window or self.test_screenshot is None:
            return {"error": "Window or screenshot not available"}
        
        import gc
        from src.utilities import runelite_cv as rcv
        
        print("🧠 Benchmarking memory usage...")
        
        # Get baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss
        
        memory_tests = {}
        
        # Test 1: Large screenshot operations
        print("   Testing screenshot memory usage...")
        screenshots = []
        start_memory = psutil.Process().memory_info().rss
        
        for i in range(10):
            screenshots.append(self.window.game_view.screenshot())
        
        peak_memory = psutil.Process().memory_info().rss
        memory_tests["screenshots"] = {
            "baseline": baseline_memory,
            "peak": peak_memory,
            "delta": peak_memory - start_memory,
            "per_screenshot": (peak_memory - start_memory) / 10
        }
        
        # Cleanup
        del screenshots
        gc.collect()
        
        # Test 2: Color detection memory usage
        print("   Testing color detection memory usage...")
        start_memory = psutil.Process().memory_info().rss
        
        isolated_images = []
        for _ in range(5):
            for color in [clr.CYAN, clr.PINK, clr.PURPLE]:
                isolated_images.append(clr.isolate_colors(self.test_screenshot, color))
        
        peak_memory = psutil.Process().memory_info().rss
        memory_tests["color_detection"] = {
            "baseline": start_memory,
            "peak": peak_memory,
            "delta": peak_memory - start_memory,
            "per_operation": (peak_memory - start_memory) / 15
        }
        
        # Cleanup
        del isolated_images
        gc.collect()
        
        # Test 3: Object extraction memory
        print("   Testing object extraction memory usage...")
        start_memory = psutil.Process().memory_info().rss
        
        all_objects = []
        for _ in range(5):
            isolated = clr.isolate_colors(self.test_screenshot, clr.CYAN)
            objects = rcv.extract_objects(isolated)
            all_objects.extend(objects)
        
        peak_memory = psutil.Process().memory_info().rss
        memory_tests["object_extraction"] = {
            "baseline": start_memory,
            "peak": peak_memory,
            "delta": peak_memory - start_memory,
            "per_operation": (peak_memory - start_memory) / 5
        }
        
        # Final cleanup
        del all_objects
        gc.collect()
        final_memory = psutil.Process().memory_info().rss
        
        # Overall memory health
        memory_tests["overall"] = {
            "baseline": baseline_memory,
            "final": final_memory,
            "net_increase": final_memory - baseline_memory,
            "memory_leak_suspected": (final_memory - baseline_memory) > 50 * 1024 * 1024  # 50MB
        }
        
        print(f"   Memory baseline: {baseline_memory / 1024 / 1024:.1f} MB")
        print(f"   Memory final: {final_memory / 1024 / 1024:.1f} MB")
        print(f"   Net increase: {(final_memory - baseline_memory) / 1024 / 1024:.1f} MB")
        
        return memory_tests
    
    def run_full_benchmark(self, window_title: str = "RuneLite") -> bool:
        """Run complete performance benchmark suite."""
        print("🚀 Starting Performance Benchmark Suite")
        print("=" * 60)
        
        # Initialize window
        if not self.setup_window(window_title):
            print("❌ Cannot run benchmarks without game window")
            return False
        
        # Run benchmarks
        print("\n📸 Screenshot Capture Performance...")
        self.results["benchmarks"]["screenshot_capture"] = self.benchmark_screenshot_capture()
        
        print("\n🎨 Color Detection Performance...")
        self.results["benchmarks"]["color_detection"] = self.benchmark_color_detection()
        
        print("\n🔍 Object Extraction Performance...")
        self.results["benchmarks"]["object_extraction"] = self.benchmark_object_extraction()
        
        print("\n📖 OCR Extraction Performance...")
        self.results["benchmarks"]["ocr_extraction"] = self.benchmark_ocr_extraction()
        
        print("\n🔎 Image Search Performance...")
        self.results["benchmarks"]["image_search"] = self.benchmark_image_search()
        
        print("\n🖱️  Mouse Simulation Performance...")
        self.results["benchmarks"]["mouse_simulation"] = self.benchmark_mouse_simulation()
        
        print("\n🧠 Memory Usage Analysis...")
        self.results["benchmarks"]["memory_usage"] = self.benchmark_memory_usage()
        
        # Generate summary
        self._generate_summary()
        
        # Save results
        results_file = self.output_dir / f"performance_benchmark_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Overall assessment
        total_tests = self.results["summary"]["total_tests"]
        passed_tests = self.results["summary"]["passed_tests"]
        success = passed_tests == total_tests
        
        if success:
            print("🎉 All performance benchmarks passed!")
        else:
            failed = total_tests - passed_tests
            print(f"⚠️  {failed}/{total_tests} benchmark(s) failed to meet performance targets")
        
        return success
    
    def _generate_summary(self):
        """Generate performance summary and recommendations."""
        print("\n" + "=" * 60)
        print("📊 Performance Summary")
        print("=" * 60)
        
        summary = self.results["summary"]
        
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        
        if summary["warnings"]:
            print(f"⚠️  Warnings: {len(summary['warnings'])}")
            for warning in summary["warnings"]:
                print(f"   - {warning}")
        
        # Performance recommendations
        print("\n🔧 Performance Recommendations:")
        
        recommendations = []
        
        # Check each benchmark for specific recommendations
        for name, result in self.results["benchmarks"].items():
            if isinstance(result, dict) and "status" in result:
                if result["status"] == "failed":
                    if name == "screenshot_capture":
                        recommendations.append("Consider reducing screenshot frequency or using ROI cropping")
                    elif name == "color_detection":
                        recommendations.append("Optimize color detection by caching results or reducing search areas")
                    elif name == "object_extraction":
                        recommendations.append("Implement object detection caching or use simpler contour algorithms")
                    elif name == "ocr_extraction":
                        recommendations.append("Cache OCR results or reduce OCR region sizes")
                    elif name == "image_search":
                        recommendations.append("Use smaller templates or implement template caching")
        
        # Memory recommendations
        memory_result = self.results["benchmarks"].get("memory_usage", {})
        if isinstance(memory_result, dict) and memory_result.get("overall", {}).get("memory_leak_suspected"):
            recommendations.append("Potential memory leak detected - review object cleanup and garbage collection")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges - no immediate optimizations needed")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # System performance context
        system_info = self.results["system_info"]
        if isinstance(system_info, dict) and "memory_available" in system_info:
            available_gb = system_info["memory_available"] / (1024**3)
            if available_gb < 2:
                print(f"\n⚠️  System Memory Warning: Only {available_gb:.1f}GB available")
                recommendations.append("Consider freeing up system memory for better performance")


def main():
    """Command-line interface for performance profiling."""
    parser = argparse.ArgumentParser(description="Auto-OSBC Performance Profiler")
    parser.add_argument("--window", default="RuneLite", help="Game window title")
    parser.add_argument("--output-dir", type=Path, help="Output directory for results")
    parser.add_argument("--iterations", type=int, help="Number of iterations for each benchmark")
    
    args = parser.parse_args()
    
    # Create profiler
    profiler = PerformanceProfiler(args.output_dir)
    
    # Override iterations if specified
    if args.iterations:
        # Adjust iterations for different operations based on their relative cost
        profiler.benchmark_screenshot_capture = lambda: profiler.benchmark_screenshot_capture(args.iterations)
        profiler.benchmark_color_detection = lambda: profiler.benchmark_color_detection(max(1, args.iterations // 2))
        profiler.benchmark_object_extraction = lambda: profiler.benchmark_object_extraction(max(1, args.iterations // 3))
        profiler.benchmark_ocr_extraction = lambda: profiler.benchmark_ocr_extraction(max(1, args.iterations // 3))
        profiler.benchmark_image_search = lambda: profiler.benchmark_image_search(max(1, args.iterations // 4))
        profiler.benchmark_mouse_simulation = lambda: profiler.benchmark_mouse_simulation(max(1, args.iterations // 5))
    
    try:
        success = profiler.run_full_benchmark(args.window)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Profiling cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())