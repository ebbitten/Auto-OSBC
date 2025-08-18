#!/usr/bin/env python3
"""
Interactive Debug Console for Auto-OSBC
Provides command-line interface for debugging game automation issues.
"""

import cmd
import cv2
import time
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utilities import color as clr
from src.utilities import ocr
from src.utilities import imagesearch as imsearch
from src.utilities.window import Window
from src.utilities.geometry import Rectangle, Point


class OSBCDebugConsole(cmd.Cmd):
    """Interactive debug console for Auto-OSBC development."""
    
    intro = '''
╔══════════════════════════════════════════════════════════════════════════════╗
║                        Auto-OSBC Debug Console                              ║
║                                                                              ║
║  Type 'help' or '?' to list commands.                                       ║
║  Type 'help <command>' for detailed help on a specific command.             ║
║                                                                              ║
║  Essential commands: init, screenshot, detect, ocr, benchmark               ║
╚══════════════════════════════════════════════════════════════════════════════╝
'''
    
    prompt = '(osbc-debug) '
    
    def __init__(self):
        super().__init__()
        self.window: Optional[Window] = None
        self.last_screenshot: Optional[cv2.Mat] = None
        self.debug_dir = Path("debug_screenshots") / f"console_session_{int(time.time())}"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_count = 0
        
        print(f"Debug files will be saved to: {self.debug_dir}")
    
    def do_init(self, line):
        """Initialize game window connection: init [window_title]"""
        window_title = line.strip() if line.strip() else "RuneLite"
        
        try:
            self.window = Window(window_title, padding_top=26, padding_left=0)
            self.window.initialize()
            print(f"✅ Successfully initialized window: '{window_title}'")
            print(f"   Game view: {self.window.game_view.width}x{self.window.game_view.height}")
            print(f"   Client mode: {'Fixed' if self.window.client_fixed else 'Resizable'}")
        except Exception as e:
            print(f"❌ Failed to initialize window '{window_title}': {e}")
            print("   Make sure the game client is running and visible.")
            self.window = None
    
    def do_screenshot(self, line):
        """Take screenshot of game area: screenshot [area] [description]"""
        if not self.window:
            print("❌ No window initialized. Use 'init' command first.")
            return
        
        parts = line.strip().split(' ', 1) if line.strip() else ['game_view']
        area = parts[0]
        description = parts[1] if len(parts) > 1 else "manual"
        
        # Map area names to window regions
        areas = {
            'game_view': self.window.game_view,
            'game': self.window.game_view,  # alias
            'inventory': self.window.control_panel,
            'inv': self.window.control_panel,  # alias
            'minimap': self.window.minimap_area,
            'chat': self.window.chat,
            'full': self.window.rectangle(),
            'client': self.window.rectangle(),  # alias
        }
        
        if area not in areas:
            print(f"❌ Unknown area '{area}'. Available: {', '.join(areas.keys())}")
            return
        
        try:
            region = areas[area]
            self.last_screenshot = region.screenshot()
            
            self.screenshot_count += 1
            filename = f"{self.screenshot_count:03d}_{area}_{description}.png"
            filepath = self.debug_dir / filename
            
            cv2.imwrite(str(filepath), self.last_screenshot)
            print(f"📸 Screenshot saved: {filename}")
            print(f"   Size: {self.last_screenshot.shape[1]}x{self.last_screenshot.shape[0]}")
            
        except Exception as e:
            print(f"❌ Error taking screenshot: {e}")
    
    def do_detect(self, line):
        """Detect objects by color: detect <color> [min_size]"""
        if self.last_screenshot is None:
            print("❌ No screenshot available. Use 'screenshot' command first.")
            return
        
        parts = line.strip().split()
        if not parts:
            print("❌ Usage: detect <color> [min_size]")
            print("   Available colors: CYAN, PINK, PURPLE, GREEN, RED, WHITE, BLACK")
            return
        
        color_name = parts[0].upper()
        min_size = int(parts[1]) if len(parts) > 1 else 10
        
        try:
            color = getattr(clr, color_name)
        except AttributeError:
            print(f"❌ Unknown color '{color_name}'. Available: CYAN, PINK, PURPLE, GREEN, RED, WHITE, BLACK")
            return
        
        try:
            # Import here to avoid circular imports
            from src.utilities import runelite_cv as rcv
            
            # Isolate color
            isolated = clr.isolate_colors(self.last_screenshot, color)
            
            # Extract objects
            objects = rcv.extract_objects(isolated)
            
            # Filter by size
            valid_objects = [obj for obj in objects if obj.width >= min_size and obj.height >= min_size]
            
            print(f"🔍 Color {color_name} detection results:")
            print(f"   Total objects found: {len(objects)}")
            print(f"   Objects >= {min_size}px: {len(valid_objects)}")
            
            if valid_objects:
                print("   Valid objects:")
                for i, obj in enumerate(valid_objects[:10]):  # Show first 10
                    print(f"     {i+1}: {obj.width}x{obj.height} at ({obj.left}, {obj.top})")
                
                if len(valid_objects) > 10:
                    print(f"     ... and {len(valid_objects) - 10} more")
            
            # Save debug images
            isolated_path = self.debug_dir / f"detect_{color_name.lower()}_isolated.png"
            cv2.imwrite(str(isolated_path), isolated)
            
            # Create overlay with detections
            overlay = self.last_screenshot.copy()
            for obj in valid_objects:
                cv2.rectangle(overlay, (obj.left, obj.top), 
                             (obj.left + obj.width, obj.top + obj.height),
                             (0, 255, 0), 2)
                cv2.putText(overlay, f"{obj.width}x{obj.height}",
                           (obj.left, obj.top - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
            overlay_path = self.debug_dir / f"detect_{color_name.lower()}_overlay.png"
            cv2.imwrite(str(overlay_path), overlay)
            
            print(f"   Debug images saved: detect_{color_name.lower()}_{{isolated,overlay}}.png")
            
        except Exception as e:
            print(f"❌ Error detecting objects: {e}")
    
    def do_ocr(self, line):
        """Extract text from screenshot: ocr [font] [color]"""
        if self.last_screenshot is None:
            print("❌ No screenshot available. Use 'screenshot' command first.")
            return
        
        parts = line.strip().split()
        font_name = parts[0] if parts else "PLAIN_11"
        color_name = parts[1] if len(parts) > 1 else "WHITE"
        
        try:
            font = getattr(ocr, font_name)
            color = getattr(clr, color_name.upper())
        except AttributeError as e:
            print(f"❌ Unknown font or color: {e}")
            print("   Available fonts: PLAIN_11, PLAIN_12, BOLD_12, QUILL")
            print("   Available colors: WHITE, BLACK, ORB_GREEN, YELLOW, etc.")
            return
        
        try:
            # Extract text
            extracted_text = ocr.extract_text(self.last_screenshot, font, [color])
            
            print(f"📖 OCR Results (font={font_name}, color={color_name}):")
            if extracted_text:
                print(f"   Text: '{extracted_text}'")
                print(f"   Length: {len(extracted_text)} characters")
            else:
                print("   No text extracted")
            
            # Save color isolation for debugging
            isolated = clr.isolate_colors(self.last_screenshot, color)
            isolated_path = self.debug_dir / f"ocr_{font_name}_{color_name.lower()}.png"
            cv2.imwrite(str(isolated_path), isolated)
            print(f"   Debug image saved: ocr_{font_name}_{color_name.lower()}.png")
            
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
    
    def do_search(self, line):
        """Search for template image: search <template_path> [confidence]"""
        if self.last_screenshot is None:
            print("❌ No screenshot available. Use 'screenshot' command first.")
            return
        
        parts = line.strip().split()
        if not parts:
            print("❌ Usage: search <template_path> [confidence]")
            return
        
        template_path = parts[0]
        confidence = float(parts[1]) if len(parts) > 1 else 0.15
        
        if not Path(template_path).exists():
            # Try relative to project root
            project_template = Path(__file__).parent.parent / template_path
            if project_template.exists():
                template_path = str(project_template)
            else:
                print(f"❌ Template image not found: {template_path}")
                return
        
        try:
            # Create a rectangle from the screenshot for search
            search_rect = Rectangle(0, 0, self.last_screenshot.shape[1], self.last_screenshot.shape[0])
            
            # Perform search
            result = imsearch.search_img_in_rect(template_path, self.last_screenshot, confidence)
            
            print(f"🔍 Template search results:")
            print(f"   Template: {Path(template_path).name}")
            print(f"   Confidence: {confidence}")
            
            if result:
                print(f"   ✅ Found at: ({result.left}, {result.top})")
                print(f"   Size: {result.width}x{result.height}")
                
                # Create overlay showing found location
                overlay = self.last_screenshot.copy()
                cv2.rectangle(overlay, (result.left, result.top),
                             (result.left + result.width, result.top + result.height),
                             (0, 255, 0), 2)
                cv2.putText(overlay, "FOUND", (result.left, result.top - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                overlay_path = self.debug_dir / f"search_found_{Path(template_path).stem}.png"
                cv2.imwrite(str(overlay_path), overlay)
                print(f"   Debug image saved: search_found_{Path(template_path).stem}.png")
            else:
                print("   ❌ Template not found")
                
        except Exception as e:
            print(f"❌ Error searching for template: {e}")
    
    def do_benchmark(self, line):
        """Run performance benchmark: benchmark [iterations]"""
        if not self.window:
            print("❌ No window initialized. Use 'init' command first.")
            return
        
        iterations = int(line.strip()) if line.strip().isdigit() else 5
        
        print(f"🏃 Running performance benchmark ({iterations} iterations)...")
        
        # Import here to avoid circular imports
        from src.utilities import runelite_cv as rcv
        
        screenshot_times = []
        detection_times = []
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}", end="")
            
            # Benchmark screenshot
            start_time = time.time()
            screenshot = self.window.game_view.screenshot()
            screenshot_time = time.time() - start_time
            screenshot_times.append(screenshot_time)
            
            # Benchmark detection
            start_time = time.time()
            isolated = clr.isolate_colors(screenshot, clr.CYAN)
            objects = rcv.extract_objects(isolated)
            detection_time = time.time() - start_time
            detection_times.append(detection_time)
            
            print(f" ✓")
        
        # Calculate statistics
        avg_screenshot = sum(screenshot_times) / len(screenshot_times)
        avg_detection = sum(detection_times) / len(detection_times)
        
        print(f"\n📊 Performance Results:")
        print(f"   Screenshot: {avg_screenshot*1000:.1f}ms avg (target: <50ms)")
        print(f"   Detection:  {avg_detection*1000:.1f}ms avg (target: <100ms)")
        print(f"   Total:      {(avg_screenshot + avg_detection)*1000:.1f}ms avg")
        
        # Performance assessment
        if avg_screenshot > 0.05:
            print("   ⚠️  Screenshot time exceeds target")
        if avg_detection > 0.1:
            print("   ⚠️  Detection time exceeds target")
        if avg_screenshot <= 0.05 and avg_detection <= 0.1:
            print("   ✅ Performance targets met")
    
    def do_info(self, line):
        """Show current debug session information"""
        print(f"📋 Debug Session Information:")
        print(f"   Window initialized: {'✅ Yes' if self.window else '❌ No'}")
        if self.window:
            print(f"   Client mode: {'Fixed' if self.window.client_fixed else 'Resizable'}")
            print(f"   Game view: {self.window.game_view.width}x{self.window.game_view.height}")
        print(f"   Last screenshot: {'✅ Available' if self.last_screenshot is not None else '❌ None'}")
        if self.last_screenshot is not None:
            h, w = self.last_screenshot.shape[:2]
            print(f"   Screenshot size: {w}x{h}")
        print(f"   Debug directory: {self.debug_dir}")
        print(f"   Screenshots taken: {self.screenshot_count}")
    
    def do_colors(self, line):
        """List available color constants"""
        print("🎨 Available Color Constants:")
        
        # Get all color constants from the clr module
        color_attrs = [attr for attr in dir(clr) if isinstance(getattr(clr, attr), clr.Color)]
        
        # Group colors by category
        game_colors = [c for c in color_attrs if c in ['CYAN', 'PINK', 'PURPLE', 'GREEN', 'RED']]
        ui_colors = [c for c in color_attrs if c in ['WHITE', 'BLACK', 'YELLOW']]
        orb_colors = [c for c in color_attrs if 'ORB' in c]
        off_colors = [c for c in color_attrs if 'OFF' in c]
        
        print("   Game Objects:", ", ".join(game_colors))
        print("   UI Elements: ", ", ".join(ui_colors))
        print("   Orb Colors: ", ", ".join(orb_colors))
        print("   Off Colors: ", ", ".join(off_colors))
    
    def do_save_session(self, line):
        """Save current session state: save_session [description]"""
        description = line.strip() if line.strip() else "debug_session"
        
        session_data = {
            "timestamp": time.time(),
            "description": description,
            "window_initialized": self.window is not None,
            "screenshots_taken": self.screenshot_count,
            "debug_directory": str(self.debug_dir)
        }
        
        if self.window:
            session_data["window_info"] = {
                "client_fixed": self.window.client_fixed,
                "game_view_size": f"{self.window.game_view.width}x{self.window.game_view.height}"
            }
        
        session_file = self.debug_dir / f"session_{description}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"💾 Session saved: {session_file}")
    
    def do_quit(self, line):
        """Exit the debug console"""
        print("👋 Goodbye! Debug files saved in:", self.debug_dir)
        return True
    
    def do_exit(self, line):
        """Exit the debug console (alias for quit)"""
        return self.do_quit(line)
    
    def do_EOF(self, line):
        """Handle Ctrl+D"""
        print()  # New line for clean exit
        return self.do_quit(line)
    
    def emptyline(self):
        """Don't repeat last command on empty line"""
        pass
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"❌ Unknown command: {line}")
        print("   Type 'help' for available commands.")


if __name__ == '__main__':
    try:
        OSBCDebugConsole().cmdloop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Console error: {e}")