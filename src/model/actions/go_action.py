"""Unified launch and login orchestrator.

The 'go' action gets the system to a logged-in state from any starting point.
It detects the current state and takes appropriate actions to progress.
"""

import time
from typing import Callable, Optional

from model.actions.base import ActionOutcome
from model.system_state import SystemState, SystemStateDetector


# Type aliases for hook callbacks (used for testing/profiling)
BeforeDetectHook = Callable[[], None]
AfterDetectHook = Callable[[SystemState], None]
BeforeActionHook = Callable[[str], None]

# Global recorder instance for action recording
_action_recorder = None


def _get_recorder():
    """Get the action recorder if recording is enabled."""
    global _action_recorder
    return _action_recorder


def go(
    force_restart: bool = False,
    skip_login: bool = False,
    timeout: float = 180.0,
    record: bool = False,
    # Optional hooks for testing/profiling
    on_before_detect: Optional[BeforeDetectHook] = None,
    on_after_detect: Optional[AfterDetectHook] = None,
    on_before_action: Optional[BeforeActionHook] = None,
) -> ActionOutcome:
    """Get to logged-in state from any starting point.

    This is the main entry point for the unified launch/login flow.
    It detects the current state and takes appropriate actions.

    Args:
        force_restart: If True, close existing windows and start fresh.
        skip_login: If True, stop at the login screen (don't enter credentials).
        timeout: Overall timeout for the entire process.
        record: If True, record before/after screenshots of each action.
        on_before_detect: Optional callback before each state detection.
        on_after_detect: Optional callback after detection with detected state.
        on_before_action: Optional callback before each action with action name.

    Returns:
        ActionOutcome indicating success or failure.
    """
    global _action_recorder

    start_time = time.time()
    detector = SystemStateDetector()
    unknown_count = 0
    max_unknown_retries = 3

    # Track actions to prevent duplicates
    launch_initiated = False
    last_state = None

    # Start action recording if requested
    if record:
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
            from recorder import ActionRecorder
            _action_recorder = ActionRecorder("RuneLite")
            _action_recorder.start_session("osbc_go")
        except Exception as e:
            print(f"[GO] Warning: Could not start action recording: {e}")
            _action_recorder = None

    def _finish_recording(outcome: ActionOutcome) -> ActionOutcome:
        """End recording session and generate report."""
        global _action_recorder
        if _action_recorder:
            try:
                _action_recorder.end_session()
                report = _action_recorder.generate_report()
                if report:
                    outcome.data["recording_report"] = str(report)
            except Exception as e:
                print(f"[GO] Warning: Could not finish recording: {e}")
            _action_recorder = None
        return outcome

    # Force restart if requested
    if force_restart:
        result = _close_all_windows()
        if not result.success:
            return _finish_recording(result)
        time.sleep(3)  # Wait for windows to fully close

    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return _finish_recording(ActionOutcome.fail(
                f"Timeout after {elapsed:.0f}s",
                elapsed=elapsed,
            ))

        # Hook: before detection
        if on_before_detect:
            on_before_detect()

        # Detect current state
        state = detector.detect()
        description = detector.get_state_description(state)

        # Hook: after detection
        if on_after_detect:
            on_after_detect(state)

        # Only print if state changed
        if state != last_state:
            print(f"[GO] State: {state.name} - {description}")
            last_state = state

        # Check for success conditions
        if state == SystemState.RUNELITE_LOGGED_IN:
            return _finish_recording(ActionOutcome.ok(
                "Successfully logged in",
                state=state.name,
                elapsed=elapsed,
            ))

        if skip_login and state == SystemState.RUNELITE_LOGIN:
            return _finish_recording(ActionOutcome.ok(
                "At login screen (skip_login=True)",
                state=state.name,
                elapsed=elapsed,
            ))

        # Handle unknown state
        if state == SystemState.RUNELITE_UNKNOWN:
            unknown_count += 1
            if unknown_count >= max_unknown_retries:
                return _finish_recording(ActionOutcome.fail(
                    f"Unable to determine state after {unknown_count} attempts. "
                    "Try --force-restart to start fresh.",
                    state=state.name,
                    unknown_count=unknown_count,
                ))
            print(f"[GO] Unknown state, retrying... ({unknown_count}/{max_unknown_retries})")
            time.sleep(2)
            continue
        else:
            unknown_count = 0  # Reset counter on successful detection

        # Skip launch actions if we already initiated one
        if state in (SystemState.NO_WINDOWS, SystemState.OSBC_ONLY):
            if launch_initiated:
                print("[GO] Waiting for RuneLite to load...")
                time.sleep(5)
                continue
            else:
                launch_initiated = True

        # If we see RuneLite states, reset the launch flag
        if state in (SystemState.RUNELITE_LAUNCHER, SystemState.RUNELITE_WELCOME,
                     SystemState.RUNELITE_LOGIN, SystemState.RUNELITE_CLICK_TO_PLAY):
            launch_initiated = False

        # Hook: before action
        if on_before_action:
            on_before_action(state.name)

        # Execute action for current state
        result = _handle_state(state, skip_login)
        if not result.success:
            return _finish_recording(result)

        # Wait for state transition (longer for launch operations)
        if state in (SystemState.NO_WINDOWS, SystemState.OSBC_ONLY):
            time.sleep(10)  # Longer wait after launching
        else:
            time.sleep(1)


def _handle_state(state: SystemState, skip_login: bool) -> ActionOutcome:
    """Handle the current state by taking appropriate action.

    Args:
        state: Current system state.
        skip_login: Whether to skip login actions.

    Returns:
        ActionOutcome indicating success of the action.
    """
    handlers = {
        SystemState.NO_WINDOWS: _handle_no_windows,
        SystemState.OSBC_ONLY: _handle_osbc_only,
        SystemState.RUNELITE_LAUNCHER: _handle_launcher,
        SystemState.RUNELITE_WELCOME: _handle_welcome,
        SystemState.RUNELITE_LOGIN: lambda: _handle_login(skip_login),
        SystemState.RUNELITE_CLICK_TO_PLAY: _handle_click_to_play,
    }

    handler = handlers.get(state)
    if handler:
        return handler()
    else:
        return ActionOutcome.fail(f"No handler for state: {state.name}")


def _handle_no_windows() -> ActionOutcome:
    """Launch OSBC when no windows are running."""
    print("[GO] Launching OSBC...")
    from model.actions import orchestration

    result = orchestration.auto_launch_runelite(
        game="OSRS",
        skip_if_running=False,
        timeout=120,
    )

    if result.success:
        return ActionOutcome.ok("OSBC launched")
    else:
        return ActionOutcome.fail(f"Failed to launch: {result.message}")


def _handle_osbc_only() -> ActionOutcome:
    """Select game and click launch when OSBC is running but RuneLite is not."""
    print("[GO] OSBC running, launching RuneLite...")
    from model.actions import orchestration

    # The orchestration module handles game selection and launch
    result = orchestration.auto_launch_runelite(
        game="OSRS",
        skip_if_running=False,
        timeout=120,
    )

    if result.success:
        return ActionOutcome.ok("RuneLite launch initiated")
    else:
        return ActionOutcome.fail(f"Failed to launch RuneLite: {result.message}")


def _handle_launcher() -> ActionOutcome:
    """Wait for RuneLite Launcher to load the game."""
    print("[GO] Waiting for game to load...")
    # Just wait - the main loop will re-detect state
    time.sleep(5)
    return ActionOutcome.ok("Waiting for game to load")


def _handle_welcome() -> ActionOutcome:
    """Click 'Existing User' button on welcome screen."""
    print("[GO] Clicking 'Existing User'...")
    from utilities.window import Window
    from model.login.login_screen import LoginScreenDetector
    from model.actions.executor import Executor
    from model.actions.intents import ClickIntent

    recorder = _get_recorder()

    try:
        win = Window("RuneLite", padding_top=26, padding_left=0)

        # Focus window before clicking
        try:
            win.focus()
            time.sleep(0.3)
        except Exception:
            pass

        detector = LoginScreenDetector(win)
        button = detector.get_existing_user_button_location()

        if not button:
            if recorder:
                recorder.before_action("click_existing_user", "Looking for 'Existing User' button", detected_state="WELCOME")
                recorder.after_action("click_existing_user", success=False, message="Button not found")
            return ActionOutcome.fail("Could not find 'Existing User' button")

        # Record before action
        click_point = button.random_point()
        if recorder:
            # Convert to relative coordinates
            rect = win.rectangle()
            rel_x = click_point.x - rect.left
            rel_y = click_point.y - rect.top
            recorder.before_action(
                "click_existing_user",
                "Clicking 'Existing User' button",
                target_point=(rel_x, rel_y),
                detected_state="WELCOME",
            )

        # Create a minimal context for the executor
        class MinimalContext:
            def __init__(self, window):
                self.win = window
                from utilities.mouse import Mouse
                self.mouse = Mouse()

            def log_msg(self, msg, **kwargs):
                print(f"[GO] {msg}")

        context = MinimalContext(win)
        executor = Executor(context)

        click = ClickIntent(point=click_point, speed="medium")
        result = executor.execute(click)

        if result.success:
            time.sleep(1)  # Wait for transition
            if recorder:
                recorder.after_action("click_existing_user", success=True, message="Button clicked")
            return ActionOutcome.ok("Clicked 'Existing User'")
        else:
            if recorder:
                recorder.after_action("click_existing_user", success=False, message=result.message)
            return ActionOutcome.fail(f"Failed to click: {result.message}")

    except Exception as e:
        if recorder:
            recorder.after_action("click_existing_user", success=False, message=str(e))
        return ActionOutcome.fail(f"Error clicking Existing User: {e}")


def _handle_login(skip_login: bool) -> ActionOutcome:
    """Enter credentials and login."""
    if skip_login:
        return ActionOutcome.ok("At login screen, skipping login")

    print("[GO] Performing login...")

    # Focus window before login (login_service also focuses, but be sure)
    try:
        from utilities.window import Window
        win = Window("RuneLite", padding_top=26, padding_left=0)
        win.focus()
        time.sleep(0.3)
    except Exception:
        pass

    from model.actions.login_action import perform_login

    result = perform_login(window_title="RuneLite", max_attempts=3)
    return result


def _handle_click_to_play() -> ActionOutcome:
    """Click the 'Click to Play' button after login."""
    print("[GO] Clicking to play...")
    from utilities.window import Window
    from model.login.login_screen import LoginScreenDetector
    from model.actions.executor import Executor
    from model.actions.intents import ClickIntent

    recorder = _get_recorder()

    try:
        win = Window("RuneLite", padding_top=26, padding_left=0)

        # Focus window before clicking
        try:
            win.focus()
            time.sleep(0.3)
        except Exception:
            pass

        detector = LoginScreenDetector(win)
        button = detector.get_click_to_play_button_location()

        if not button:
            # If no button found, try clicking center of screen
            rect = win.rectangle()
            from utilities.geometry import Point
            center = Point(rect.left + rect.width // 2, rect.top + rect.height // 2)
            print("[GO] Play button not found, clicking center of screen")
            button_found = False
        else:
            center = button.random_point()
            button_found = True

        # Record before action
        if recorder:
            rect = win.rectangle()
            rel_x = center.x - rect.left
            rel_y = center.y - rect.top
            recorder.before_action(
                "click_to_play",
                f"Clicking 'Click to Play' {'button' if button_found else '(center fallback)'}",
                target_point=(rel_x, rel_y),
                detected_state="CLICK_TO_PLAY",
            )

        class MinimalContext:
            def __init__(self, window):
                self.win = window
                from utilities.mouse import Mouse
                self.mouse = Mouse()

            def log_msg(self, msg, **kwargs):
                print(f"[GO] {msg}")

        context = MinimalContext(win)
        executor = Executor(context)

        click = ClickIntent(point=center, speed="medium")
        result = executor.execute(click)

        if result.success:
            time.sleep(2)  # Wait for transition to game
            if recorder:
                recorder.after_action("click_to_play", success=True, message="Clicked")
            return ActionOutcome.ok("Clicked to play")
        else:
            if recorder:
                recorder.after_action("click_to_play", success=False, message=result.message)
            return ActionOutcome.fail(f"Failed to click: {result.message}")

    except Exception as e:
        if recorder:
            recorder.after_action("click_to_play", success=False, message=str(e))
        return ActionOutcome.fail(f"Error clicking to play: {e}")


def _close_all_windows() -> ActionOutcome:
    """Close all OSBC and RuneLite windows.

    Uses PID-based taskkill to force close since RuneLite has a confirmation dialog.
    """
    print("[GO] Closing existing windows...")
    import subprocess
    import ctypes
    import pywinctl

    try:
        closed = 0

        # Get all windows and kill by PID (bypasses confirmation dialogs)
        windows = pywinctl.getAllWindows()
        for window in windows:
            title = window.title or ""
            if "RuneLite" in title or "OS Bot" in title:
                try:
                    # Get the window's process ID
                    user32 = ctypes.windll.user32
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(window.getHandle(), ctypes.byref(pid))

                    # Force kill the process
                    result = subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid.value)],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        print(f"[GO] Killed {title} (PID {pid.value})")
                        closed += 1
                except Exception as e:
                    print(f"[GO] Failed to kill {title}: {e}")

        if closed > 0:
            print(f"[GO] Closed {closed} window(s)")

        # Wait for processes to fully terminate
        time.sleep(3)

        return ActionOutcome.ok(f"Closed {closed} window(s)")

    except Exception as e:
        return ActionOutcome.fail(f"Failed to close windows: {e}")
