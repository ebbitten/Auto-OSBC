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
        Find the target window and return its bounds.

        Returns:
            Dictionary with x, y, width, height or None if not found
        """
        try:
            # Try using pywinctl if available (cross-platform)
            import pywinctl as pwc

            windows = pwc.getWindowsWithTitle(self.window_title)
            if windows:
                win = windows[0]
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
            if window.initialize():
                rect = window.rectangle()
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


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Game State Recorder for Auto-OSBC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/recorder.py                      # Record for 10 seconds
  python scripts/recorder.py --duration 30       # Record for 30 seconds
  python scripts/recorder.py --until-stop        # Record until Ctrl+C
  python scripts/recorder.py --window "RuneLite" # Specify window title
  python scripts/recorder.py --interval 250      # Capture every 250ms
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

    args = parser.parse_args()

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

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
