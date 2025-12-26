"""Flow Profiler - Timing analysis for the osbc go/login flow.

Profiles each step of the login flow to identify bottlenecks:
- State detection time (template matching, OCR)
- Action execution time (clicks, typing)
- State transition time
- Overall flow duration

Usage:
    python scripts/flow_profiler.py --detection-only
    python scripts/flow_profiler.py --full-flow
    python scripts/flow_profiler.py --output profile.json
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class TimingResult:
    """Result of a single timed operation."""
    name: str
    duration_ms: float
    success: bool = True
    error: Optional[str] = None

    @property
    def passed_threshold(self) -> bool:
        """Check if timing is within acceptable threshold."""
        thresholds = {
            "window_check": 50,
            "existing_user_template": 30,
            "new_user_template": 30,
            "login_button_template": 30,
            "try_again_template": 30,
            "cancel_template": 30,
            "click_to_play_template": 30,
            "is_welcome_screen": 80,  # Combines 2-3 templates
            "minimap_orbs": 50,
            "window_initialize": 100,
            "full_detect_state": 100,
            "mouse_move": 300,
            "mouse_click": 100,
            "type_char": 60,
        }
        threshold = thresholds.get(self.name, 100)
        return self.duration_ms <= threshold


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: str
    to_state: str
    duration_ms: float
    action_taken: str


@dataclass
class ProfileReport:
    """Complete profiling report."""
    timestamp: str
    window_title: str
    detection_timings: dict[str, TimingResult] = field(default_factory=dict)
    action_timings: list[TimingResult] = field(default_factory=list)
    state_transitions: list[StateTransition] = field(default_factory=list)
    total_duration_ms: float = 0.0
    bottlenecks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "timestamp": self.timestamp,
            "window_title": self.window_title,
            "detection_timings": {
                name: {
                    "duration_ms": t.duration_ms,
                    "passed": t.passed_threshold,
                    "error": t.error,
                }
                for name, t in self.detection_timings.items()
            },
            "action_timings": [
                {"name": t.name, "duration_ms": t.duration_ms, "passed": t.passed_threshold}
                for t in self.action_timings
            ],
            "state_transitions": [
                {
                    "from": st.from_state,
                    "to": st.to_state,
                    "duration_ms": st.duration_ms,
                    "action": st.action_taken,
                }
                for st in self.state_transitions
            ],
            "total_duration_ms": self.total_duration_ms,
            "bottlenecks": self.bottlenecks,
            "recommendations": self.recommendations,
        }


class FlowProfiler:
    """Profiles the go/login flow with detailed timing breakdown."""

    def __init__(self, window_title: str = "RuneLite"):
        self.window_title = window_title
        self.window = None
        self.detector = None
        self.report = ProfileReport(
            timestamp=datetime.now().isoformat(),
            window_title=window_title,
        )

    def _time(self, func: Callable, name: str, *args, **kwargs) -> TimingResult:
        """Time a function call and return result."""
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            return TimingResult(name=name, duration_ms=duration_ms, success=True)
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return TimingResult(
                name=name, duration_ms=duration_ms, success=False, error=str(e)
            )

    def _init_window(self) -> bool:
        """Initialize window connection."""
        try:
            from utilities.window import Window
            self.window = Window(self.window_title, padding_top=26, padding_left=0)
            _ = self.window.rectangle()  # Verify it exists
            return True
        except Exception as e:
            print(f"Could not connect to window '{self.window_title}': {e}")
            return False

    def _init_detector(self) -> bool:
        """Initialize login screen detector."""
        try:
            from model.login.login_screen import LoginScreenDetector
            self.detector = LoginScreenDetector(self.window)
            return True
        except Exception as e:
            print(f"Could not initialize detector: {e}")
            return False

    def profile_state_detection(self, iterations: int = 3) -> dict[str, TimingResult]:
        """Profile each detection method individually.

        Args:
            iterations: Number of times to run each test (uses average)

        Returns:
            Dict of operation name to timing result
        """
        if not self._init_window() or not self._init_detector():
            return {}

        from utilities import imagesearch as imsearch
        from model.login.login_screen import LOGIN_IMAGES_PATH

        results = {}
        win_rect = self.window.rectangle()

        # Helper to run multiple iterations
        def profile_multi(name: str, func: Callable) -> TimingResult:
            times = []
            last_result = None
            for _ in range(iterations):
                result = self._time(func, name)
                times.append(result.duration_ms)
                last_result = result
            avg_ms = sum(times) / len(times)
            return TimingResult(
                name=name,
                duration_ms=round(avg_ms, 2),
                success=last_result.success,
                error=last_result.error,
            )

        # Window check
        import pywinctl
        results["window_check"] = profile_multi(
            "window_check",
            lambda: pywinctl.getWindowsWithTitle(self.window_title),
        )

        # Template matches
        templates = [
            ("existing_user_template", "existing_user_button.png"),
            ("new_user_template", "new_user_button.png"),
            ("login_button_template", "login_button.png"),
            ("try_again_template", "try_again_button.png"),
            ("cancel_template", "cancel_button.png"),
            ("click_to_play_template", "click_to_play.png"),
        ]

        for name, filename in templates:
            path = LOGIN_IMAGES_PATH / filename
            if path.exists():
                results[name] = profile_multi(
                    name,
                    lambda p=str(path): imsearch.search_img_in_rect(p, win_rect, confidence=0.8),
                )
            else:
                results[name] = TimingResult(
                    name=name, duration_ms=0, success=False, error=f"Template not found: {filename}"
                )

        # Structural validation
        results["is_welcome_screen"] = profile_multi(
            "is_welcome_screen",
            lambda: self.detector._is_welcome_screen(),
        )

        # Logged-in detection
        results["minimap_orbs"] = profile_multi(
            "minimap_orbs",
            lambda: self.detector._has_minimap_orbs(),
        )

        def try_initialize():
            try:
                self.window.initialize()
                return True
            except Exception:
                return False

        results["window_initialize"] = profile_multi(
            "window_initialize",
            try_initialize,
        )

        # Full detect_state
        results["full_detect_state"] = profile_multi(
            "full_detect_state",
            lambda: self.detector.detect_state(),
        )

        self.report.detection_timings = results
        return results

    def profile_actions(self) -> list[TimingResult]:
        """Profile action execution (mouse, keyboard)."""
        from utilities.mouse import Mouse
        from utilities.geometry import Point
        import pyautogui

        results = []
        mouse = Mouse()

        # Mouse move
        start_pos = pyautogui.position()
        target = Point(start_pos[0] + 100, start_pos[1] + 100)
        result = self._time(
            lambda: mouse.move_to(target, mouseSpeed="medium"),
            "mouse_move",
        )
        results.append(result)

        # Mouse click
        result = self._time(
            lambda: mouse.click(),
            "mouse_click",
        )
        results.append(result)

        # Typing (measure per-character)
        test_text = "test123"
        start = time.perf_counter()
        pyautogui.typewrite(test_text, interval=0.05)
        duration_ms = (time.perf_counter() - start) * 1000
        per_char = duration_ms / len(test_text)
        results.append(TimingResult(
            name="type_char",
            duration_ms=round(per_char, 2),
        ))

        self.report.action_timings = results
        return results

    def analyze_bottlenecks(self) -> tuple[list[str], list[str]]:
        """Analyze results and identify bottlenecks."""
        bottlenecks = []
        recommendations = []

        # Check detection timings
        for name, timing in self.report.detection_timings.items():
            if not timing.passed_threshold:
                bottlenecks.append(f"{name}: {timing.duration_ms:.1f}ms")

        # Count slow template matches
        slow_templates = sum(
            1 for name, t in self.report.detection_timings.items()
            if "template" in name and not t.passed_threshold
        )
        if slow_templates > 0:
            recommendations.append(
                f"{slow_templates} template matches exceed 30ms - consider caching within same frame"
            )

        # Check full detection time
        full_detect = self.report.detection_timings.get("full_detect_state")
        if full_detect and not full_detect.passed_threshold:
            recommendations.append(
                "Full state detection exceeds 100ms - reduce template count or add early exit"
            )

        # Check action timings
        for timing in self.report.action_timings:
            if not timing.passed_threshold:
                bottlenecks.append(f"{timing.name}: {timing.duration_ms:.1f}ms")

        self.report.bottlenecks = bottlenecks
        self.report.recommendations = recommendations
        return bottlenecks, recommendations

    def print_report(self):
        """Print formatted report to console."""
        print("\n" + "=" * 50)
        print("       FLOW PROFILE REPORT")
        print("=" * 50)
        print(f"Timestamp: {self.report.timestamp}")
        print(f"Window: {self.report.window_title}")
        print()

        # Detection timings
        print("State Detection Breakdown:")
        print("-" * 40)
        for name, timing in self.report.detection_timings.items():
            status = "" if timing.passed_threshold else " [SLOW]"
            if timing.error:
                print(f"  {name:30} ERROR: {timing.error}")
            else:
                print(f"  {name:30} {timing.duration_ms:7.1f}ms{status}")
        print()

        # Action timings
        if self.report.action_timings:
            print("Action Timings:")
            print("-" * 40)
            for timing in self.report.action_timings:
                status = "" if timing.passed_threshold else " [SLOW]"
                print(f"  {timing.name:30} {timing.duration_ms:7.1f}ms{status}")
            print()

        # State transitions
        if self.report.state_transitions:
            print("State Transitions:")
            print("-" * 40)
            for st in self.report.state_transitions:
                print(f"  {st.from_state} -> {st.to_state}: {st.duration_ms:.0f}ms ({st.action_taken})")
            print()

        # Summary
        if self.report.bottlenecks:
            print("Bottlenecks Identified:")
            print("-" * 40)
            for b in self.report.bottlenecks:
                print(f"  - {b}")
            print()

        if self.report.recommendations:
            print("Recommendations:")
            print("-" * 40)
            for r in self.report.recommendations:
                print(f"  - {r}")
            print()

        # Pass/fail summary
        all_passed = len(self.report.bottlenecks) == 0
        status = "PASSED" if all_passed else "NEEDS OPTIMIZATION"
        print(f"Overall: {status}")
        print("=" * 50)

    def run_detection_profile(self, iterations: int = 3) -> ProfileReport:
        """Run detection-only profiling."""
        print(f"Profiling state detection ({iterations} iterations each)...")
        self.profile_state_detection(iterations=iterations)
        self.analyze_bottlenecks()
        return self.report

    def run_full_profile(self) -> ProfileReport:
        """Run full flow profiling with state transitions."""
        from model.actions.go_action import go
        from model.system_state import SystemState, SystemStateDetector

        print("Running full flow profile...")
        print("This will execute the go command and measure each step.")

        # Profile detection first
        self.profile_state_detection(iterations=1)
        self.profile_actions()

        # Run go flow with timing
        detector = SystemStateDetector()
        last_state = None
        last_time = time.perf_counter()

        # Custom timing wrapper for go flow
        start = time.perf_counter()
        result = go(force_restart=False, skip_login=False, timeout=120)
        total_ms = (time.perf_counter() - start) * 1000
        self.report.total_duration_ms = total_ms

        self.analyze_bottlenecks()
        return self.report


def main():
    parser = argparse.ArgumentParser(
        description="Profile the osbc go/login flow timing"
    )
    parser.add_argument(
        "--detection-only",
        action="store_true",
        help="Only profile state detection (no full flow)",
    )
    parser.add_argument(
        "--full-flow",
        action="store_true",
        help="Profile complete go flow (requires valid credentials)",
    )
    parser.add_argument(
        "--window",
        type=str,
        default="RuneLite",
        help="Window title to profile (default: RuneLite)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations for averaging (default: 3)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--include-actions",
        action="store_true",
        help="Include mouse/keyboard action profiling",
    )

    args = parser.parse_args()

    profiler = FlowProfiler(window_title=args.window)

    if args.full_flow:
        report = profiler.run_full_profile()
    else:
        report = profiler.run_detection_profile(iterations=args.iterations)
        if args.include_actions:
            print("\nProfiling actions...")
            profiler.profile_actions()
            profiler.analyze_bottlenecks()

    profiler.print_report()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
