# Visual Debugging Guide for Game Automation

## Overview
Debugging game automation requires specialized tools and techniques due to the visual, timing-dependent nature of bot interactions. This guide provides comprehensive debugging strategies for Auto-OSBC development.

## ⚠️ Implementation Status

**IMPORTANT**: This document describes the *aspirational architecture* for Auto-OSBC's debugging infrastructure. Many of the classes and utilities documented here (particularly `DebugCapture`, `DetectionDebugger`, and `PerformanceDebugger`) are **not yet implemented** and serve as design guidelines for future development.

**Currently Implemented**:
- Basic debug utilities in `src/utilities/debug.py`: `timer()`, `save_image()`, `get_test_window()`
- Interactive debug console: `scripts/debug_console.py`
- Visual regression testing: `tests/tools/visual_regression.py`

**Planned/Not Yet Implemented**:
- `DebugCapture` class (systematic screenshot collection)
- `DetectionDebugger` class (visual detection analysis)
- `PerformanceDebugger` class (comprehensive timing analysis)
- Log analysis scripts (`scripts/analyze_logs.py`, `scripts/monitor_logs.py`)

When these classes are documented below, treat them as *design specifications* rather than working code. For current debugging capabilities, see the "Currently Implemented" section above.

## Debug Infrastructure Setup

### 1. Debug Screenshots Directory
**Structure**:
```
debug_screenshots/
├── {bot_name}/
│   ├── {timestamp}/
│   │   ├── 001_initial_state.png
│   │   ├── 002_detection_result.png
│   │   ├── 003_mouse_overlay.png
│   │   └── debug_log.txt
│   └── latest/  # Symlink to most recent session
├── test_captures/
└── reference_images/
```

**Setup Script**:
```python
# scripts/setup_debug.py
import os
from pathlib import Path
import time

def setup_debug_environment(bot_name: str) -> Path:
    """Setup debug directory structure for a bot"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    debug_dir = Path("debug_screenshots") / bot_name / timestamp
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Create symlink to latest
    latest_link = Path("debug_screenshots") / bot_name / "latest"
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(timestamp)
    
    return debug_dir
```

### 2. Debug Configuration
**File**: `src/utilities/debug_config.py`
```python
class DebugConfig:
    ENABLE_SCREENSHOTS = True
    ENABLE_DETECTION_OVERLAY = True
    ENABLE_MOUSE_TRACKING = True
    ENABLE_PERFORMANCE_LOGGING = True
    
    # Screenshot settings
    SCREENSHOT_EVERY_N_SECONDS = 5
    SAVE_FAILED_DETECTIONS = True
    
    # Performance settings
    ENABLE_TIMING_LOGS = True
    PERFORMANCE_LOG_INTERVAL = 10
```

## Visual Debugging Tools

### 1. Screenshot Capture System

#### Automatic Screenshot Capture
```python
# src/utilities/debug_capture.py
import cv2
import time
from pathlib import Path
from typing import Optional

class DebugCapture:
    def __init__(self, bot_name: str, session_id: str):
        self.bot_name = bot_name
        self.session_id = session_id
        self.debug_dir = Path("debug_screenshots") / bot_name / session_id
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.capture_count = 0
        
    def capture_state(self, window, description: str) -> Path:
        """Capture current game state with description"""
        self.capture_count += 1
        timestamp = time.strftime("%H%M%S")
        filename = f"{self.capture_count:03d}_{timestamp}_{description}.png"
        filepath = self.debug_dir / filename
        
        # Capture screenshot
        screenshot = window.game_view.screenshot()
        cv2.imwrite(str(filepath), screenshot)
        
        # Log capture
        self.log_capture(description, filename)
        
        return filepath
    
    def capture_detection_overlay(self, image, detections, description: str):
        """Capture image with detection overlays"""
        overlay_image = image.copy()
        
        # Draw detection boxes
        for detection in detections:
            color = (0, 255, 0)  # Green boxes
            cv2.rectangle(overlay_image, 
                         (detection.left, detection.top),
                         (detection.left + detection.width, detection.top + detection.height),
                         color, 2)
            
            # Add detection info
            cv2.putText(overlay_image, f"{detection.color.name}",
                       (detection.left, detection.top - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Save overlay image
        self.capture_count += 1
        timestamp = time.strftime("%H%M%S")
        filename = f"{self.capture_count:03d}_{timestamp}_{description}_overlay.png"
        filepath = self.debug_dir / filename
        cv2.imwrite(str(filepath), overlay_image)
        
        return filepath
```

#### Manual Screenshot Tools
```python
# scripts/manual_capture.py
def capture_current_state(description: str = "manual_capture"):
    """Manually capture current game state"""
    from src.utilities.window import Window
    
    # Initialize window
    window = Window("RuneLite", padding_top=26, padding_left=0)
    window.initialize()
    
    # Capture all relevant areas
    captures = {
        'game_view': window.game_view.screenshot(),
        'inventory': window.control_panel.screenshot(),
        'minimap': window.minimap_area.screenshot(),
        'chat': window.chat.screenshot()
    }
    
    # Save captures
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    for area, image in captures.items():
        filename = f"{timestamp}_{description}_{area}.png"
        cv2.imwrite(f"debug_screenshots/{filename}", image)
    
    print(f"Captured state: {description}")
```

### 2. Detection Analysis Tools

#### Visual Detection Debugger
```python
# src/utilities/detection_debugger.py
class DetectionDebugger:
    def __init__(self, bot):
        self.bot = bot
        self.debug_capture = DebugCapture(bot.bot_title, time.strftime("%Y%m%d_%H%M%S"))
    
    def debug_color_detection(self, target_color, description: str):
        """Debug color-based object detection"""
        # Capture original image
        original = self.bot.win.game_view.screenshot()
        self.debug_capture.capture_state(self.bot.win, f"{description}_original")
        
        # Isolate target color
        isolated = clr.isolate_colors(original, target_color)
        cv2.imwrite(str(self.debug_capture.debug_dir / f"{description}_isolated.png"), isolated)
        
        # Find contours
        contours = rcv.extract_objects(isolated)
        
        # Create detection overlay
        self.debug_capture.capture_detection_overlay(original, contours, f"{description}_detections")
        
        # Log detection results
        self.log_detection_results(contours, description)
        
        return contours
    
    def debug_ocr_extraction(self, region, font, colors, description: str):
        """Debug OCR text extraction"""
        # Capture region
        region_image = region.screenshot()
        cv2.imwrite(str(self.debug_capture.debug_dir / f"{description}_region.png"), region_image)
        
        # Apply color isolation
        for i, color in enumerate(colors):
            isolated = clr.isolate_colors(region_image, color)
            cv2.imwrite(str(self.debug_capture.debug_dir / f"{description}_color_{i}.png"), isolated)
        
        # Extract text
        extracted_text = ocr.extract_text(region, font, colors)
        
        # Log results
        with open(self.debug_capture.debug_dir / f"{description}_ocr_result.txt", 'w') as f:
            f.write(f"Font: {font}\n")
            f.write(f"Colors: {[c.name for c in colors]}\n")
            f.write(f"Extracted: '{extracted_text}'\n")
        
        return extracted_text
    
    def debug_image_search(self, template_path, search_area, confidence, description: str):
        """Debug template image matching"""
        # Capture search area
        search_image = search_area.screenshot()
        self.debug_capture.capture_state(self.bot.win, f"{description}_search_area")
        
        # Perform search
        result = imsearch.search_img_in_rect(template_path, search_area, confidence)
        
        # Create overlay showing search result
        if result:
            overlay = search_image.copy()
            cv2.rectangle(overlay, 
                         (result.left - search_area.left, result.top - search_area.top),
                         (result.left - search_area.left + result.width, 
                          result.top - search_area.top + result.height),
                         (0, 255, 0), 2)
            cv2.imwrite(str(self.debug_capture.debug_dir / f"{description}_found.png"), overlay)
        else:
            cv2.imwrite(str(self.debug_capture.debug_dir / f"{description}_not_found.png"), search_image)
        
        # Log search results
        with open(self.debug_capture.debug_dir / f"{description}_search_result.txt", 'w') as f:
            f.write(f"Template: {template_path}\n")
            f.write(f"Confidence: {confidence}\n")
            f.write(f"Result: {result}\n")
        
        return result
```

### 3. Performance Debugging

#### Timing Analysis
```python
# src/utilities/performance_debugger.py
import time
import functools
from typing import Dict, List

class PerformanceDebugger:
    def __init__(self):
        self.timing_data: Dict[str, List[float]] = {}
        self.call_counts: Dict[str, int] = {}
    
    def time_function(self, name: str):
        """Decorator to time function execution"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                if name not in self.timing_data:
                    self.timing_data[name] = []
                    self.call_counts[name] = 0
                
                self.timing_data[name].append(execution_time)
                self.call_counts[name] += 1
                
                # Log slow operations
                if execution_time > 0.1:  # More than 100ms
                    print(f"SLOW: {name} took {execution_time:.3f}s")
                
                return result
            return wrapper
        return decorator
    
    def get_performance_report(self) -> str:
        """Generate performance report"""
        report = "Performance Report\n"
        report += "==================\n\n"
        
        for name, times in self.timing_data.items():
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            total_time = sum(times)
            
            report += f"{name}:\n"
            report += f"  Calls: {self.call_counts[name]}\n"
            report += f"  Avg: {avg_time:.3f}s\n"
            report += f"  Min: {min_time:.3f}s\n"
            report += f"  Max: {max_time:.3f}s\n"
            report += f"  Total: {total_time:.3f}s\n\n"
        
        return report

# Usage example
perf_debugger = PerformanceDebugger()

@perf_debugger.time_function("npc_detection")
def get_nearest_tagged_NPC(self, include_in_combat=False):
    # Original method implementation
    pass
```

### 4. Interactive Debugging Tools

#### Live Debug Console
```python
# scripts/debug_console.py
import cmd
import cv2
from src.model.your_bot import YourBot

class DebugConsole(cmd.Cmd):
    intro = 'Auto-OSBC Debug Console. Type help or ? to list commands.\n'
    prompt = '(osbc-debug) '
    
    def __init__(self):
        super().__init__()
        self.bot = None
        self.last_screenshot = None
    
    def do_init_bot(self, line):
        """Initialize bot for debugging: init_bot BotClassName"""
        if not line:
            print("Usage: init_bot BotClassName")
            return
        
        try:
            # Dynamic bot import
            module = __import__(f"src.model.{line.lower()}", fromlist=[line])
            bot_class = getattr(module, line)
            self.bot = bot_class()
            print(f"Initialized {line} bot")
        except Exception as e:
            print(f"Error initializing bot: {e}")
    
    def do_screenshot(self, line):
        """Take screenshot of game area: screenshot [area]"""
        if not self.bot:
            print("No bot initialized. Use 'init_bot' first.")
            return
        
        area = line.strip() if line else "game_view"
        
        try:
            if area == "game_view":
                self.last_screenshot = self.bot.win.game_view.screenshot()
            elif area == "inventory":
                self.last_screenshot = self.bot.win.control_panel.screenshot()
            elif area == "minimap":
                self.last_screenshot = self.bot.win.minimap_area.screenshot()
            else:
                print(f"Unknown area: {area}")
                return
            
            filename = f"debug_console_{area}.png"
            cv2.imwrite(filename, self.last_screenshot)
            print(f"Screenshot saved: {filename}")
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
    
    def do_detect_color(self, line):
        """Detect objects of specified color: detect_color CYAN"""
        if not self.bot or self.last_screenshot is None:
            print("Take a screenshot first using 'screenshot'")
            return
        
        try:
            color = getattr(clr, line.upper())
            isolated = clr.isolate_colors(self.last_screenshot, color)
            objects = rcv.extract_objects(isolated)
            
            print(f"Found {len(objects)} objects with color {line}")
            for i, obj in enumerate(objects):
                print(f"  Object {i}: {obj.width}x{obj.height} at ({obj.left}, {obj.top})")
            
            # Save debug image
            cv2.imwrite(f"debug_console_color_{line.lower()}.png", isolated)
            
        except Exception as e:
            print(f"Error detecting color: {e}")
    
    def do_extract_text(self, line):
        """Extract text from last screenshot: extract_text PLAIN_11"""
        if self.last_screenshot is None:
            print("Take a screenshot first using 'screenshot'")
            return
        
        font = line.strip() if line else "PLAIN_11"
        
        try:
            font_obj = getattr(ocr, font)
            text = ocr.extract_text(self.last_screenshot, font_obj, [clr.WHITE, clr.BLACK])
            print(f"Extracted text: '{text}'")
            
        except Exception as e:
            print(f"Error extracting text: {e}")
    
    def do_performance(self, line):
        """Show performance report"""
        if hasattr(self.bot, 'perf_debugger'):
            print(self.bot.perf_debugger.get_performance_report())
        else:
            print("No performance data available")
    
    def do_quit(self, line):
        """Exit debug console"""
        return True

if __name__ == '__main__':
    DebugConsole().cmdloop()
```

## Common Debugging Scenarios

### 1. Object Detection Issues

#### Problem: Objects not being detected
**Debug Steps**:
1. **Capture current state**:
   ```python
   debug_capture.capture_state(bot.win, "detection_failure")
   ```

2. **Test color isolation**:
   ```python
   isolated = clr.isolate_colors(image, target_color)
   cv2.imwrite("debug_color_isolation.png", isolated)
   ```

3. **Check contour extraction**:
   ```python
   contours = rcv.extract_objects(isolated)
   print(f"Found {len(contours)} contours")
   ```

4. **Verify object validation**:
   ```python
   for contour in contours:
       print(f"Size: {contour.width}x{contour.height}")
       print(f"Valid: {bot._validate_object(contour)}")
   ```

#### Problem: Wrong objects being detected
**Debug Steps**:
1. **Check color precision**:
   ```python
   # Test with tighter color tolerance
   strict_color = Color([255, 255, 0], tolerance=5)
   ```

2. **Add size filtering**:
   ```python
   valid_objects = [obj for obj in objects if 20 < obj.width < 100]
   ```

3. **Check for interference**:
   ```python
   debug_capture.capture_detection_overlay(image, all_objects, "all_detections")
   ```

### 2. OCR Reading Issues

#### Problem: Text not being extracted
**Debug Steps**:
1. **Test different fonts**:
   ```python
   fonts = [ocr.PLAIN_11, ocr.PLAIN_12, ocr.BOLD_12]
   for font in fonts:
       result = ocr.extract_text(region, font, colors)
       print(f"{font}: '{result}'")
   ```

2. **Test different colors**:
   ```python
   colors = [clr.WHITE, clr.BLACK, clr.ORB_GREEN, clr.YELLOW]
   for color in colors:
       result = ocr.extract_text(region, font, [color])
       print(f"{color.name}: '{result}'")
   ```

3. **Check region size**:
   ```python
   print(f"Region size: {region.width}x{region.height}")
   if region.width < 10 or region.height < 10:
       print("Region too small for OCR")
   ```

### 3. Timing and Performance Issues

#### Problem: Bot running too slowly
**Debug Steps**:
1. **Profile main operations**:
   ```python
   with perf_debugger.time_function("main_loop_iteration"):
       # Main loop code
       pass
   ```

2. **Check screenshot frequency**:
   ```python
   # Reduce screenshot frequency
   if time.time() - last_screenshot_time > 1.0:  # Only every second
       screenshot = bot.win.game_view.screenshot()
   ```

3. **Optimize detection algorithms**:
   ```python
   # Cache detection results
   if not hasattr(self, '_detection_cache') or time.time() - self._cache_time > 5:
       self._detection_cache = self.detect_objects()
       self._cache_time = time.time()
   ```

### 4. Mouse Movement Issues

#### Problem: Clicks missing targets
**Debug Steps**:
1. **Visualize click targets**:
   ```python
   # Draw click target on screenshot
   overlay = image.copy()
   cv2.circle(overlay, (target.x, target.y), 5, (0, 0, 255), -1)
   cv2.imwrite("click_target.png", overlay)
   ```

2. **Test click accuracy**:
   ```python
   # Add larger click area
   click_point = target.random_point()
   expanded_target = Rectangle(target.left - 5, target.top - 5, 
                              target.width + 10, target.height + 10)
   ```

3. **Check mouse speed**:
   ```python
   # Try different mouse speeds
   for speed in ["fastest", "fast", "medium", "slow"]:
       bot.mouse.move_to(target, mouseSpeed=speed)
   ```

## Debug Log Analysis

### 1. Log Structure
**Format**: `{timestamp}: {level}: {component}: {message}`

**Example**:
```
2024-01-15 14:30:15: INFO: NRMining: Starting mining session
2024-01-15 14:30:16: DEBUG: ObjectDetection: Found 3 pink objects
2024-01-15 14:30:16: DEBUG: MouseMovement: Moving to (150, 200) with speed 'fast'
2024-01-15 14:30:17: WARNING: API: Inventory request timeout
2024-01-15 14:30:18: ERROR: Detection: No valid mining rocks found
```

### 2. Log Analysis Tools

**Note**: This script is planned but not yet implemented.

```python
# scripts/analyze_logs.py (PLANNED - NOT YET IMPLEMENTED)
import re
from collections import defaultdict, Counter

def analyze_debug_log(log_file: str):
    """Analyze debug log for patterns and issues"""
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Parse log entries
    entries = []
    for line in lines:
        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): (\w+): (\w+): (.+)', line.strip())
        if match:
            timestamp, level, component, message = match.groups()
            entries.append({
                'timestamp': timestamp,
                'level': level,
                'component': component,
                'message': message
            })
    
    # Analysis
    print(f"Total log entries: {len(entries)}")
    
    # Level distribution
    levels = Counter(entry['level'] for entry in entries)
    print(f"Log levels: {dict(levels)}")
    
    # Component activity
    components = Counter(entry['component'] for entry in entries)
    print(f"Component activity: {dict(components)}")
    
    # Error analysis
    errors = [entry for entry in entries if entry['level'] == 'ERROR']
    if errors:
        print(f"\nFound {len(errors)} errors:")
        for error in errors[-5:]:  # Last 5 errors
            print(f"  {error['timestamp']}: {error['message']}")
    
    # Performance warnings
    slow_operations = [entry for entry in entries if 'SLOW:' in entry['message']]
    if slow_operations:
        print(f"\nFound {len(slow_operations)} slow operations:")
        for op in slow_operations[-5:]:
            print(f"  {op['timestamp']}: {op['message']}")
```

### 3. Real-time Log Monitoring

**Note**: This script is planned but not yet implemented.

```python
# scripts/monitor_logs.py (PLANNED - NOT YET IMPLEMENTED)
import time
import os

def monitor_bot_performance():
    """Monitor bot performance in real-time"""
    
    log_file = "debug_screenshots/current_session/debug.log"
    
    if not os.path.exists(log_file):
        print("No active debug log found")
        return
    
    print("Monitoring bot performance... (Ctrl+C to stop)")
    
    with open(log_file, 'r') as f:
        # Go to end of file
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                # Check for performance issues
                if 'SLOW:' in line:
                    print(f"⚠️  {line.strip()}")
                elif 'ERROR:' in line:
                    print(f"❌ {line.strip()}")
                elif 'detection took' in line:
                    print(f"🔍 {line.strip()}")
            else:
                time.sleep(0.1)
```

## Visual Test Validation

### 1. Screenshot Comparison
```python
# src/utilities/visual_validator.py
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

class VisualValidator:
    def __init__(self, tolerance: float = 0.05):
        self.tolerance = tolerance
    
    def compare_screenshots(self, reference_path: str, current_path: str) -> dict:
        """Compare two screenshots and return similarity metrics"""
        
        ref_img = cv2.imread(reference_path)
        cur_img = cv2.imread(current_path)
        
        if ref_img is None or cur_img is None:
            return {"error": "Could not load images"}
        
        # Resize to same dimensions if needed
        if ref_img.shape != cur_img.shape:
            cur_img = cv2.resize(cur_img, (ref_img.shape[1], ref_img.shape[0]))
        
        # Calculate similarity metrics
        similarity = ssim(ref_img, cur_img, multichannel=True)
        
        # Pixel difference
        diff = cv2.absdiff(ref_img, cur_img)
        pixel_diff_percentage = (np.sum(diff > 10) / diff.size) * 100
        
        # Generate difference image
        diff_highlighted = np.where(diff > 10, [0, 0, 255], cur_img)
        
        return {
            "similarity": similarity,
            "pixel_diff_percentage": pixel_diff_percentage,
            "passed": similarity > (1 - self.tolerance),
            "diff_image": diff_highlighted
        }
    
    def validate_detection_accuracy(self, image, expected_detections, actual_detections):
        """Validate that detection results match expectations"""
        
        if len(actual_detections) != len(expected_detections):
            return {
                "passed": False,
                "error": f"Expected {len(expected_detections)} detections, got {len(actual_detections)}"
            }
        
        # Check each detection
        for expected, actual in zip(expected_detections, actual_detections):
            distance = expected.distance_to(actual.get_center())
            if distance > 20:  # More than 20 pixels off
                return {
                    "passed": False,
                    "error": f"Detection off by {distance} pixels"
                }
        
        return {"passed": True}
```

### 2. Automated Visual Regression Testing
```python
# tests/tools/visual_regression.py
def run_visual_regression_tests():
    """Run automated visual regression tests"""
    
    test_scenarios = [
        "inventory_full_state",
        "mining_area_with_rocks",
        "bank_interface_open",
        "combat_with_npc"
    ]
    
    validator = VisualValidator(tolerance=0.1)
    results = {}
    
    for scenario in test_scenarios:
        print(f"Testing scenario: {scenario}")
        
        # Load reference image
        reference_path = f"tests/visual_references/{scenario}.png"
        
        # Capture current state
        current_path = f"debug_screenshots/regression_test_{scenario}.png"
        capture_scenario_state(scenario, current_path)
        
        # Compare
        result = validator.compare_screenshots(reference_path, current_path)
        results[scenario] = result
        
        if result.get("passed", False):
            print(f"  ✅ {scenario} passed (similarity: {result['similarity']:.3f})")
        else:
            print(f"  ❌ {scenario} failed: {result.get('error', 'Unknown error')}")
            
            # Save difference image
            if 'diff_image' in result:
                diff_path = f"debug_screenshots/diff_{scenario}.png"
                cv2.imwrite(diff_path, result['diff_image'])
                print(f"    Difference image saved: {diff_path}")
    
    return results
```

## Best Practices for Visual Debugging

### 1. Systematic Debugging Process
1. **Reproduce the issue** consistently
2. **Capture evidence** (screenshots, logs)
3. **Isolate the problem** (test components individually)
4. **Test hypotheses** (change one variable at a time)
5. **Document findings** (what worked, what didn't)
6. **Implement fix** with additional debugging
7. **Verify solution** doesn't break other functionality

### 2. Debug Information Organization
- **Use consistent naming** for debug files
- **Include timestamps** in all debug captures
- **Group related files** in directories
- **Document test conditions** (game state, settings)
- **Keep debug sessions separate**

### 3. Performance Debugging Guidelines
- **Profile regularly** during development
- **Set performance targets** (e.g., < 100ms detection)
- **Monitor memory usage** during long sessions
- **Test on different hardware** configurations
- **Optimize critical paths** first

### 4. Visual Test Maintenance
- **Update reference images** when game UI changes
- **Version control test assets** appropriately
- **Document test image capture conditions**
- **Automate regression testing** where possible
- **Review failed tests** before updating references

## Integration with Development Workflow

### 1. Debug During Development
```python
# Enable debug mode during development
class DebugBot(YourBot):
    def __init__(self):
        super().__init__()
        self.debug_mode = True
        self.debug_capture = DebugCapture(self.bot_title, "development")
    
    def main_loop(self):
        if self.debug_mode:
            self.debug_capture.capture_state(self.win, "loop_start")
        
        # Normal bot logic with debug points
        targets = self.find_targets()
        
        if self.debug_mode and not targets:
            self.debug_capture.capture_state(self.win, "no_targets_found")
        
        super().main_loop()
```

### 2. Automated Debug Reports
```python
# Generate debug report after bot session
def generate_debug_report(bot_session_dir: Path):
    """Generate comprehensive debug report"""
    
    report = f"""
# Debug Report: {bot_session_dir.name}

## Session Summary
- Duration: {calculate_session_duration(bot_session_dir)}
- Screenshots captured: {count_screenshots(bot_session_dir)}
- Errors encountered: {count_errors(bot_session_dir)}

## Performance Metrics
{load_performance_data(bot_session_dir)}

## Key Events
{extract_key_events(bot_session_dir)}

## Recommendations
{generate_recommendations(bot_session_dir)}
"""
    
    with open(bot_session_dir / "debug_report.md", 'w') as f:
        f.write(report)
```

### 3. Continuous Integration Debug Checks
```bash
# .github/workflows/debug_validation.yml
name: Debug Validation
on: [push, pull_request]

jobs:
  visual_tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run visual regression tests
        run: python tests/tools/visual_regression.py
      - name: Upload debug artifacts
        uses: actions/upload-artifact@v2
        if: failure()
        with:
          name: debug-screenshots
          path: debug_screenshots/
```