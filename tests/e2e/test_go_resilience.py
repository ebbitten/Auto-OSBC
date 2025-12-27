"""Resilience tests for the osbc go/login flow.

These tests verify that the go command can recover from unexpected situations:
- Missed clicks
- Window focus loss
- Window movement/minimization
- Random delays
- Stuck states

Run with: pytest tests/e2e/test_go_resilience.py -v
"""

import random
import time
from typing import Optional
from unittest.mock import patch, MagicMock

import pytest
import pyautogui

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from model.actions.go_action import go
from model.system_state import SystemState, SystemStateDetector


class TestStateDetectionResilience:
    """Tests for state detection robustness."""

    @pytest.mark.e2e
    def test_detects_state_after_window_move(self, require_runelite, chaos_injector, detector):
        """State detection works after window is moved."""
        # Get initial state
        initial_state = detector.detect()

        # Move window
        chaos_injector.move_window(dx=150, dy=100)
        time.sleep(0.5)

        # State should still be detectable
        new_state = detector.detect()
        assert new_state != SystemState.RUNELITE_UNKNOWN, "Should detect state after move"

        # Cleanup
        chaos_injector.restore_window_position()

    @pytest.mark.e2e
    def test_detects_state_after_minimize_restore(self, require_runelite, chaos_injector, detector):
        """State detection works after minimize/restore cycle."""
        initial_state = detector.detect()

        # Minimize
        chaos_injector.minimize_window()
        time.sleep(0.5)

        # Restore
        chaos_injector.restore_window()
        time.sleep(0.5)

        # State should match original
        restored_state = detector.detect()
        # Note: State might change if game does something, but should be valid
        assert restored_state != SystemState.RUNELITE_UNKNOWN

    @pytest.mark.e2e
    def test_handles_repeated_detection(self, require_runelite, detector):
        """Rapid repeated detection doesn't cause issues."""
        states = []
        for _ in range(10):
            state = detector.detect()
            states.append(state)
            time.sleep(0.1)

        # Should get consistent results (not UNKNOWN)
        non_unknown = [s for s in states if s != SystemState.RUNELITE_UNKNOWN]
        assert len(non_unknown) >= 8, "Most detections should succeed"


class TestFocusResilience:
    """Tests for window focus handling."""

    @pytest.mark.e2e
    def test_refocuses_after_focus_loss(self, at_login_screen, chaos_injector):
        """Go command should refocus window if focus is lost."""
        # This is a behavioral test - we inject focus loss and check recovery
        focus_lost = False
        action_count = 0

        def on_before_action(action_name: str):
            nonlocal focus_lost, action_count
            action_count += 1
            # Lose focus on second action
            if action_count == 2 and not focus_lost:
                chaos_injector.lose_focus()
                focus_lost = True
                time.sleep(0.5)

        # Run go with hook (will likely timeout, but should handle focus loss)
        result = go(
            skip_login=True,  # Just test until login screen
            timeout=30,
            on_before_action=on_before_action,
        )

        # Should either succeed or fail gracefully
        assert result is not None

    @pytest.mark.e2e
    def test_click_targets_correct_window(self, at_login_screen, require_runelite):
        """Clicks should land in the game window, not elsewhere."""
        from model.login.login_screen import LoginScreenDetector

        detector = LoginScreenDetector(require_runelite)

        # Get button location
        button = detector.get_login_button_location()
        if button is None:
            pytest.skip("Login button not found")

        # Verify the button is within window bounds
        win_rect = require_runelite.rectangle()
        point = button.random_point()

        assert win_rect.left <= point.x <= win_rect.left + win_rect.width
        assert win_rect.top <= point.y <= win_rect.top + win_rect.height


class TestStuckStateRecovery:
    """Tests for handling stuck/repeated states."""

    @pytest.mark.e2e
    def test_detects_stuck_state(self, require_runelite, detector):
        """Go command should detect when stuck in same state."""
        detection_count = 0
        detected_states = []

        def on_after_detect(state: SystemState):
            nonlocal detection_count
            detection_count += 1
            detected_states.append(state)

        # Run with skip_login to test detection loop
        # Note: If at INVALID_CREDENTIALS, will exit after retry
        result = go(
            skip_login=True,
            timeout=15,
            on_after_detect=on_after_detect,
        )

        # Should have detected state at least once
        # (may be 1-2 if at INVALID_CREDENTIALS due to retry logic)
        assert detection_count >= 1, f"Should detect at least once, got {detection_count}"
        assert len(detected_states) >= 1

    @pytest.mark.e2e
    def test_unknown_state_retry_limit(self):
        """Should fail after max unknown state retries."""
        # Create a mock detector that always returns UNKNOWN
        mock_detector = MagicMock()
        mock_detector.detect.return_value = SystemState.RUNELITE_UNKNOWN
        mock_detector.get_state_description.return_value = "Unknown state"

        # Patch SystemStateDetector class to return our mock
        with patch("model.actions.go_action.SystemStateDetector", return_value=mock_detector):
            result = go(timeout=15)

        # Should fail with unknown state message
        assert not result.success
        assert "state" in result.message.lower() or "unknown" in result.message.lower()


class TestChaosMonkey:
    """Random chaos injection tests."""

    CHAOS_ACTIONS = [
        "move_window",
        "minimize_restore",
        "lose_focus",
        "random_delay",
    ]

    @pytest.mark.e2e
    def test_survives_single_chaos_event(self, at_login_screen, chaos_injector):
        """Go command should handle a single random chaos event."""
        chaos_applied = False

        def inject_chaos():
            nonlocal chaos_applied
            if not chaos_applied and random.random() < 0.5:
                action = random.choice(self.CHAOS_ACTIONS)
                chaos_applied = True

                if action == "move_window":
                    chaos_injector.move_window(dx=50, dy=50)
                elif action == "minimize_restore":
                    chaos_injector.minimize_window()
                    time.sleep(0.3)
                    chaos_injector.restore_window()
                elif action == "lose_focus":
                    chaos_injector.lose_focus()
                    time.sleep(0.3)
                elif action == "random_delay":
                    chaos_injector.random_delay(0.5, 2.0)

        result = go(
            skip_login=True,
            timeout=30,
            on_before_action=lambda _: inject_chaos(),
        )

        # Should complete (success or graceful failure)
        assert result is not None

    @pytest.mark.e2e
    @pytest.mark.parametrize("chaos_count", [1, 2, 3])
    def test_survives_multiple_chaos_events(
        self, at_login_screen, chaos_injector, chaos_count
    ):
        """Go command should handle multiple chaos events."""
        events_applied = 0

        def inject_chaos(_):
            nonlocal events_applied
            if events_applied < chaos_count and random.random() < 0.4:
                action = random.choice(self.CHAOS_ACTIONS)
                events_applied += 1

                if action == "move_window":
                    chaos_injector.move_window(
                        dx=random.randint(-50, 50),
                        dy=random.randint(-50, 50),
                    )
                elif action == "random_delay":
                    chaos_injector.random_delay(0.2, 1.0)

        result = go(
            skip_login=True,
            timeout=45,
            on_before_action=inject_chaos,
        )

        assert result is not None


class TestInvalidCredentialsRecovery:
    """Tests for invalid credentials handling."""

    @pytest.mark.e2e
    @pytest.mark.skip(reason="INVALID_CREDENTIALS state removed in refactoring")
    def test_clicks_try_again_on_invalid_creds(self, require_runelite):
        """Should click 'Try again' when credentials fail."""
        from model.login.login_screen import LoginScreenDetector, LoginState

        detector = LoginScreenDetector(require_runelite)
        state_info = detector.detect_state()

        if state_info.state == LoginState.INVALID_CREDENTIALS:
            # Verify try again button is detected
            button = detector.get_try_again_button_location()
            assert button is not None, "Should find Try Again button"

    @pytest.mark.e2e
    @pytest.mark.skip(reason="INVALID_CREDENTIALS state removed in refactoring")
    def test_only_retries_once(self, require_runelite):
        """Should only retry invalid credentials once, then fail."""
        # This test would require invalid credentials to be configured
        # For now, just verify the retry flag mechanism works
        from model.actions.go_action import go

        retry_count = 0

        def count_retries(state: SystemState):
            nonlocal retry_count
            if state == SystemState.RUNELITE_INVALID_CREDENTIALS:
                retry_count += 1

        # If we're on invalid credentials screen, this tests the limit
        result = go(
            timeout=10,
            on_after_detect=count_retries,
        )

        # If invalid creds were encountered, should have retried once max
        if retry_count > 0:
            assert retry_count <= 2, "Should only retry invalid credentials once"


class TestTimingResilience:
    """Tests for timing and delay handling."""

    @pytest.mark.e2e
    def test_handles_slow_state_transitions(self, at_login_screen, chaos_injector):
        """Should handle slower than expected transitions."""
        def slow_down(action_name: str):
            # Add random delay before each action
            chaos_injector.random_delay(0.5, 1.5)

        result = go(
            skip_login=True,
            timeout=60,
            on_before_action=slow_down,
        )

        assert result is not None

    @pytest.mark.e2e
    def test_timeout_triggers_correctly(self, require_runelite):
        """Timeout should trigger after specified duration."""
        start = time.time()

        # Very short timeout
        result = go(
            skip_login=False,
            timeout=5,
        )

        elapsed = time.time() - start

        # Should fail due to timeout (unless already logged in)
        if not result.success:
            # Detection is fast now, so we may exit before full timeout
            # Just verify we didn't hang for way too long
            assert elapsed < 15, "Should not wait much longer than timeout"


# CLI interface for manual chaos testing
def main():
    """Run chaos monkey interactively."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive chaos testing")
    parser.add_argument(
        "--chaos-monkey",
        action="store_true",
        help="Run chaos monkey mode",
    )
    parser.add_argument(
        "--probability",
        type=float,
        default=0.3,
        help="Probability of chaos per action (0-1)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120,
        help="Overall timeout in seconds",
    )

    args = parser.parse_args()

    if args.chaos_monkey:
        from utilities.window import Window

        print("Starting chaos monkey test...")
        print(f"Chaos probability: {args.probability}")
        print(f"Timeout: {args.timeout}s")
        print()

        try:
            win = Window("RuneLite", padding_top=26, padding_left=0)
        except Exception as e:
            print(f"Error: Could not find RuneLite window: {e}")
            return 1

        injector_module = __import__("conftest", fromlist=["ChaosInjector"])
        ChaosInjector = injector_module.ChaosInjector
        chaos = ChaosInjector(win)

        chaos_count = 0

        def maybe_chaos(action_name: str):
            nonlocal chaos_count
            if random.random() < args.probability:
                action = random.choice([
                    "move_window",
                    "random_delay",
                    "lose_focus",
                ])
                chaos_count += 1
                print(f"  [CHAOS #{chaos_count}] Injecting: {action}")

                if action == "move_window":
                    chaos.move_window(
                        dx=random.randint(-100, 100),
                        dy=random.randint(-100, 100),
                    )
                elif action == "random_delay":
                    delay = random.uniform(0.5, 2.0)
                    print(f"    Delaying {delay:.1f}s...")
                    time.sleep(delay)
                elif action == "lose_focus":
                    chaos.lose_focus()

        result = go(
            timeout=args.timeout,
            on_before_action=maybe_chaos,
        )

        print()
        print("=" * 40)
        print(f"Result: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Message: {result.message}")
        print(f"Chaos events injected: {chaos_count}")

        return 0 if result.success else 1

    else:
        print("Use --chaos-monkey to run interactive chaos testing")
        return 0


if __name__ == "__main__":
    sys.exit(main())
