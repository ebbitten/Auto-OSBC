#!/usr/bin/env python3
"""
Game State Recorder for Auto-OSBC

Continuously captures screenshots, mouse positions, and window state
for template image creation and debugging.

Usage:
    python scripts/recorder.py                     # Record for 10 seconds
    python scripts/recorder.py --duration 30      # Record for 30 seconds
    python scripts/recorder.py --until-stop       # Record until Ctrl+C
    python scripts/recorder.py --window "RuneLite" --interval 500
"""

import argparse
import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import cv2
import mss
import pyautogui


class Recorder:
    """Continuous game state recorder."""

    def __init__(
        self,
        window_title: str = "RuneLite",
        interval_ms: int = 500,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the recorder.

        Args:
            window_title: Title of the window to record
            interval_ms: Interval between captures in milliseconds
            output_dir: Base directory for captures (default: captures/)
        """
        self.window_title = window_title
        self.interval_ms = interval_ms
        self.output_dir = output_dir or Path("captures")

        self._running = False
        self._session_dir: Optional[Path] = None
        self._screenshots: List[Dict[str, Any]] = []
        self._mouse_log: List[Dict[str, Any]] = []
        self._start_time: Optional[datetime] = None
        self._window_bounds: Optional[Dict[str, int]] = None
        self._sct = mss.mss()

    def _find_window(self) -> Optional[Dict[str, int]]:
        """
        Find the target window, bring it to foreground, and return its bounds.

        Returns:
            Dictionary with x, y, width, height or None if not found
        """
        try:
            # Try using pywinctl if available (cross-platform)
            import pywinctl as pwc

            windows = pwc.getWindowsWithTitle(self.window_title)
            if windows:
                win = windows[0]
                # Bring window to foreground for accurate capture
                try:
                    win.activate()
                    time.sleep(0.3)
                except Exception:
                    pass  # Best effort
                box = win.box
                return {
                    "x": box.left,
                    "y": box.top,
                    "width": box.width,
                    "height": box.height,
                }
        except ImportError:
            pass

        # Fallback: try using the Window class from the project
        try:
            from utilities.window import Window

            window = Window(self.window_title, padding_top=26, padding_left=0)
            # Don't call initialize() - it requires in-game UI elements
            # rectangle() works without initialization
            rect = window.rectangle()
            if rect:
                return {
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.width,
                    "height": rect.height,
                }
        except Exception:
            pass

        return None

    def _capture_screenshot(self, index: int) -> Optional[str]:
        """
        Capture a screenshot of the target window.

        Args:
            index: Screenshot index number

        Returns:
            Filename of saved screenshot or None on failure
        """
        if not self._window_bounds or not self._session_dir:
            return None

        try:
            # Define capture region
            monitor = {
                "left": self._window_bounds["x"],
                "top": self._window_bounds["y"],
                "width": self._window_bounds["width"],
                "height": self._window_bounds["height"],
            }

            # Capture screenshot
            screenshot = self._sct.grab(monitor)

            # Convert to numpy array (BGR for OpenCV)
            import numpy as np

            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # Save to file
            filename = f"screenshot_{index:04d}.png"
            filepath = self._session_dir / filename
            cv2.imwrite(str(filepath), img)

            return filename

        except Exception as e:
            print(f"  Warning: Failed to capture screenshot: {e}")
            return None

    def _get_mouse_position(self) -> Dict[str, int]:
        """Get current mouse position."""
        pos = pyautogui.position()
        return {"x": pos.x, "y": pos.y}

    def _create_session_dir(self) -> Path:
        """Create timestamped session directory."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir = self.output_dir / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def start(self, duration_seconds: Optional[float] = None) -> bool:
        """
        Start recording.

        Args:
            duration_seconds: How long to record (None = until stopped)

        Returns:
            True if recording completed successfully
        """
        print(f"Recorder: Looking for window '{self.window_title}'...")

        # Find window
        self._window_bounds = self._find_window()
        if not self._window_bounds:
            print(f"Error: Could not find window '{self.window_title}'")
            print("  Make sure the game client is running and visible.")
            return False

        print(f"  Found window: {self._window_bounds['width']}x{self._window_bounds['height']}")
        print(f"  Position: ({self._window_bounds['x']}, {self._window_bounds['y']})")

        # Create session directory
        self._session_dir = self._create_session_dir()
        print(f"  Output: {self._session_dir}")

        # Initialize recording state
        self._running = True
        self._screenshots = []
        self._mouse_log = []
        self._start_time = datetime.now()

        interval_sec = self.interval_ms / 1000.0
        screenshot_index = 0

        if duration_seconds:
            print(f"  Recording for {duration_seconds} seconds...")
        else:
            print("  Recording until Ctrl+C...")

        print()

        try:
            end_time = time.time() + duration_seconds if duration_seconds else None

            while self._running:
                capture_time = datetime.now()

                # Check if we should stop
                if end_time and time.time() >= end_time:
                    break

                # Capture screenshot
                filename = self._capture_screenshot(screenshot_index)
                if filename:
                    self._screenshots.append({
                        "file": filename,
                        "timestamp": capture_time.isoformat(),
                        "index": screenshot_index,
                    })
                    screenshot_index += 1

                # Log mouse position
                mouse_pos = self._get_mouse_position()
                self._mouse_log.append({
                    "timestamp": capture_time.isoformat(),
                    "x": mouse_pos["x"],
                    "y": mouse_pos["y"],
                    # Relative to window
                    "rel_x": mouse_pos["x"] - self._window_bounds["x"],
                    "rel_y": mouse_pos["y"] - self._window_bounds["y"],
                })

                # Progress indicator
                if screenshot_index % 10 == 0:
                    elapsed = (datetime.now() - self._start_time).total_seconds()
                    print(f"  Captured {screenshot_index} screenshots ({elapsed:.1f}s elapsed)")

                # Wait for next interval
                time.sleep(interval_sec)

        except KeyboardInterrupt:
            print("\n  Recording stopped by user")

        self._running = False
        self._save_metadata()

        print(f"\nRecording complete:")
        print(f"  Screenshots: {len(self._screenshots)}")
        print(f"  Mouse samples: {len(self._mouse_log)}")
        print(f"  Output: {self._session_dir}")

        return True

    def stop(self):
        """Stop recording."""
        self._running = False

    def _save_metadata(self):
        """Save session metadata to JSON files."""
        if not self._session_dir:
            return

        end_time = datetime.now()

        # Main metadata
        metadata = {
            "session_start": self._start_time.isoformat() if self._start_time else None,
            "session_end": end_time.isoformat(),
            "duration_seconds": (end_time - self._start_time).total_seconds() if self._start_time else 0,
            "window_title": self.window_title,
            "window_bounds": self._window_bounds,
            "capture_interval_ms": self.interval_ms,
            "screenshot_count": len(self._screenshots),
            "mouse_sample_count": len(self._mouse_log),
            "screenshots": self._screenshots,
        }

        metadata_path = self._session_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Mouse log (separate file for potentially large data)
        mouse_path = self._session_dir / "mouse_log.json"
        with open(mouse_path, "w") as f:
            json.dump(self._mouse_log, f, indent=2)


def setup_signal_handler(recorder: Recorder):
    """Set up Ctrl+C handler to gracefully stop recording."""
    def handler(signum, frame):
        recorder.stop()

    signal.signal(signal.SIGINT, handler)


def extract_template(
    session_dir: Path,
    screenshot_index: int,
    x: int,
    y: int,
    width: int,
    height: int,
    output_name: str,
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Extract a template region from a captured screenshot.

    Args:
        session_dir: Path to the capture session directory
        screenshot_index: Index of the screenshot to use (0-based)
        x, y: Top-left corner of the region (relative to screenshot)
        width, height: Size of the region
        output_name: Name for the output template file
        output_dir: Directory to save template (default: src/images/bot/login)

    Returns:
        Path to saved template, or None on failure
    """
    screenshot_path = session_dir / f"screenshot_{screenshot_index:04d}.png"
    if not screenshot_path.exists():
        print(f"  Screenshot not found: {screenshot_path}")
        return None

    try:
        img = cv2.imread(str(screenshot_path))
        if img is None:
            print(f"  Failed to load: {screenshot_path}")
            return None

        # Crop the region
        cropped = img[y : y + height, x : x + width]

        # Save to templates directory
        templates_dir = output_dir or Path("src/images/bot/login")
        templates_dir.mkdir(parents=True, exist_ok=True)
        output_path = templates_dir / f"{output_name}.png"
        cv2.imwrite(str(output_path), cropped)

        print(f"  Saved template: {output_path}")
        print(f"  Size: {width}x{height}")
        return output_path

    except Exception as e:
        print(f"  Template extraction failed: {e}")
        return None


def preview_region(
    session_dir: Path,
    screenshot_index: int,
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    """Preview a region from a captured screenshot.

    Saves a preview image and prints info about the region.

    Args:
        session_dir: Path to the capture session directory
        screenshot_index: Index of the screenshot to use
        x, y: Top-left corner of the region
        width, height: Size of the region
    """
    screenshot_path = session_dir / f"screenshot_{screenshot_index:04d}.png"
    if not screenshot_path.exists():
        print(f"  Screenshot not found: {screenshot_path}")
        return

    try:
        img = cv2.imread(str(screenshot_path))
        if img is None:
            print(f"  Failed to load: {screenshot_path}")
            return

        # Get image dimensions
        img_height, img_width = img.shape[:2]
        print(f"Screenshot size: {img_width}x{img_height}")
        print(f"Region: ({x}, {y}) to ({x + width}, {y + height})")

        # Validate bounds
        if x < 0 or y < 0 or x + width > img_width or y + height > img_height:
            print(f"  Warning: Region extends outside image bounds!")

        # Crop and save preview
        cropped = img[max(0, y) : min(img_height, y + height), max(0, x) : min(img_width, x + width)]
        preview_path = session_dir / "preview_region.png"
        cv2.imwrite(str(preview_path), cropped)
        print(f"  Preview saved: {preview_path}")

        # Also draw rectangle on full image for context
        annotated = img.copy()
        cv2.rectangle(annotated, (x, y), (x + width, y + height), (0, 255, 0), 2)
        annotated_path = session_dir / "preview_annotated.png"
        cv2.imwrite(str(annotated_path), annotated)
        print(f"  Annotated view: {annotated_path}")

    except Exception as e:
        print(f"  Preview failed: {e}")


def test_template(
    template_path: Path,
    window_title: str,
    confidence: float = 0.8,
) -> bool:
    """Test if a template can be found in a window.

    Args:
        template_path: Path to the template image
        window_title: Title of the window to search in
        confidence: Matching confidence threshold

    Returns:
        True if template found, False otherwise
    """
    import pyautogui

    if not template_path.exists():
        print(f"  Template not found: {template_path}")
        return False

    # Find window
    try:
        import pywinctl as pwc

        windows = pwc.getWindowsWithTitle(window_title)
        if not windows:
            print(f"  Window '{window_title}' not found")
            return False

        win = windows[0]
        try:
            win.activate()
            time.sleep(0.3)
        except Exception:
            pass

        region = (win.box.left, win.box.top, win.box.width, win.box.height)
        print(f"Window: {win.title}")
        print(f"Region: {region}")

    except ImportError:
        print("  pywinctl not available, searching full screen")
        region = None

    # Try to find template
    try:
        location = pyautogui.locateOnScreen(
            str(template_path),
            region=region,
            confidence=confidence,
        )

        if location:
            center = pyautogui.center(location)
            print(f"  ✓ Template FOUND at ({center.x}, {center.y})")
            print(f"    Box: {location}")
            return True
        else:
            print(f"  ✗ Template NOT FOUND (confidence={confidence})")
            return False

    except Exception as e:
        print(f"  Template matching error: {e}")
        return False


def list_templates(template_dir: Path = None) -> None:
    """List all available templates in a directory.

    Args:
        template_dir: Directory to list (default: src/images/bot/login)
    """
    if template_dir is None:
        template_dir = Path("src/images/bot/login")

    if not template_dir.exists():
        print(f"  Template directory not found: {template_dir}")
        return

    templates = list(template_dir.glob("*.png"))
    if not templates:
        print(f"  No templates in {template_dir}")
        return

    print(f"Templates in {template_dir}:")
    for t in sorted(templates):
        # Get image size
        img = cv2.imread(str(t))
        if img is not None:
            h, w = img.shape[:2]
            print(f"  {t.name}: {w}x{h}")
        else:
            print(f"  {t.name}: (unable to read)")


def interactive_capture(window_title: str) -> None:
    """Capture a single screenshot for interactive template building.

    Saves screenshot with grid overlay to help identify coordinates.

    Args:
        window_title: Title of window to capture
    """
    import pyautogui

    try:
        import pywinctl as pwc

        windows = pwc.getWindowsWithTitle(window_title)
        if not windows:
            print(f"Window '{window_title}' not found")
            return

        win = windows[0]
        try:
            win.activate()
            time.sleep(0.5)
        except Exception:
            pass

        # Capture
        region = (win.box.left, win.box.top, win.box.width, win.box.height)
        screenshot = pyautogui.screenshot(region=region)

        # Save raw screenshot
        output_dir = Path("captures/interactive")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        raw_path = output_dir / f"capture_{timestamp}.png"
        screenshot.save(str(raw_path))
        print(f"Screenshot: {raw_path}")
        print(f"Size: {win.box.width}x{win.box.height}")

        # Create gridded version for coordinate reference
        img = cv2.imread(str(raw_path))
        grid_spacing = 50

        # Draw grid
        h, w = img.shape[:2]
        for x in range(0, w, grid_spacing):
            cv2.line(img, (x, 0), (x, h), (0, 255, 0), 1)
            cv2.putText(img, str(x), (x + 2, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        for y in range(0, h, grid_spacing):
            cv2.line(img, (0, y), (w, y), (0, 255, 0), 1)
            cv2.putText(img, str(y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        grid_path = output_dir / f"capture_{timestamp}_grid.png"
        cv2.imwrite(str(grid_path), img)
        print(f"Gridded: {grid_path}")

        print(f"\nUse the gridded image to identify coordinates, then:")
        print(f"  --from-session {output_dir} --preview X,Y,W,H")
        print(f"  --from-session {output_dir} --extract-template X,Y,W,H,name")

    except Exception as e:
        print(f"Capture failed: {e}")


def analyze_ocr(session_dir: Path, window_bounds: Dict[str, int]) -> None:
    """Run OCR analysis on captured screenshots.

    Args:
        session_dir: Path to the capture session directory
        window_bounds: Window bounds dictionary with x, y, width, height
    """
    try:
        from utilities import ocr
        import utilities.color as clr
        from utilities.geometry import Rectangle
    except ImportError as e:
        print(f"  OCR analysis skipped: {e}")
        return

    # Create Rectangle from bounds
    rect = Rectangle(
        window_bounds["x"],
        window_bounds["y"],
        window_bounds["width"],
        window_bounds["height"],
    )

    print("\nOCR Analysis:")

    # Try different font/color combinations
    font_options = [
        ("PLAIN_12", ocr.PLAIN_12),
        ("BOLD_12", ocr.BOLD_12),
        ("PLAIN_11", ocr.PLAIN_11),
    ]

    color_options = [
        ("WHITE", [clr.WHITE]),
        ("YELLOW", [clr.YELLOW]),
        ("ORANGE", [clr.ORANGE]),
        ("CYAN", [clr.CYAN]),
    ]

    for font_name, font in font_options:
        for color_name, colors in color_options:
            try:
                text = ocr.extract_text(rect, font, colors)
                if text.strip():
                    print(f"  {font_name} + {color_name}: {text[:100]!r}")
            except Exception as e:
                print(f"  {font_name} + {color_name}: Error - {e}")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Game State Recorder and Template Builder for Auto-OSBC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Recording Examples:
  python scripts/recorder.py                      # Record for 10 seconds
  python scripts/recorder.py --duration 30       # Record for 30 seconds
  python scripts/recorder.py --until-stop        # Record until Ctrl+C
  python scripts/recorder.py --window "RuneLite" # Specify window title

Template Building Workflow:
  1. Capture:   python scripts/recorder.py --interactive --window "RuneLite"
  2. Preview:   python scripts/recorder.py --from-session captures/interactive --preview 300,200,150,40
  3. Extract:   python scripts/recorder.py --from-session captures/interactive --extract-template 300,200,150,40,button_name
  4. Test:      python scripts/recorder.py --test-template src/images/bot/login/button_name.png --window "RuneLite"
  5. List:      python scripts/recorder.py --list-templates
        """,
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Recording duration in seconds (default: 10)",
    )
    parser.add_argument(
        "--until-stop",
        action="store_true",
        help="Record until Ctrl+C (overrides --duration)",
    )
    parser.add_argument(
        "--window",
        type=str,
        default="RuneLite",
        help="Window title to capture (default: RuneLite)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=500,
        help="Capture interval in milliseconds (default: 500)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("captures"),
        help="Output directory (default: captures/)",
    )
    parser.add_argument(
        "--analyze-ocr",
        action="store_true",
        help="Run OCR analysis after recording (debugging)",
    )
    parser.add_argument(
        "--extract-template",
        type=str,
        metavar="X,Y,W,H,NAME",
        help="Extract template from screenshot 0: X,Y,Width,Height,name (e.g., 450,200,120,30,existing_user)",
    )
    parser.add_argument(
        "--from-session",
        type=Path,
        metavar="DIR",
        help="Use existing capture session instead of recording new one",
    )

    # Template building tools
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Capture single screenshot with grid overlay for coordinate finding",
    )
    parser.add_argument(
        "--preview",
        type=str,
        metavar="X,Y,W,H",
        help="Preview a region from captured screenshot (use with --from-session)",
    )
    parser.add_argument(
        "--test-template",
        type=Path,
        metavar="PATH",
        help="Test if a template can be found in the window",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates in src/images/bot/login",
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        metavar="DIR",
        help="Template directory for --list-templates or --extract-template",
    )

    args = parser.parse_args()

    # Handle standalone template tools first
    if args.list_templates:
        list_templates(args.template_dir)
        return 0

    if args.test_template:
        found = test_template(args.test_template, args.window)
        return 0 if found else 1

    if args.interactive:
        interactive_capture(args.window)
        return 0

    # Handle session-based operations
    if args.from_session:
        if args.preview:
            try:
                parts = args.preview.split(",")
                x, y, w, h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                print(f"Previewing region from {args.from_session}")
                preview_region(args.from_session, 0, x, y, w, h)
            except Exception as e:
                print(f"Preview error: {e}")
                return 1
            return 0

        if args.extract_template:
            try:
                parts = args.extract_template.split(",")
                x, y, w, h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                name = parts[4] if len(parts) > 4 else "template"
                print(f"Extracting template from {args.from_session}")
                extract_template(args.from_session, 0, x, y, w, h, name, args.template_dir)
            except Exception as e:
                print(f"Extraction error: {e}")
                return 1
            return 0

        print("--from-session requires --extract-template or --preview")
        return 1

    # Create recorder
    recorder = Recorder(
        window_title=args.window,
        interval_ms=args.interval,
        output_dir=args.output,
    )

    # Set up signal handler
    setup_signal_handler(recorder)

    # Determine duration
    duration = None if args.until_stop else args.duration

    # Start recording
    success = recorder.start(duration_seconds=duration)

    # Run OCR analysis if requested
    if args.analyze_ocr and success and recorder._window_bounds:
        analyze_ocr(recorder._session_dir, recorder._window_bounds)

    # Extract template if requested
    if args.extract_template and success:
        try:
            parts = args.extract_template.split(",")
            x, y, w, h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            name = parts[4] if len(parts) > 4 else "template"
            extract_template(recorder._session_dir, 0, x, y, w, h, name)
        except Exception as e:
            print(f"Template extraction error: {e}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
