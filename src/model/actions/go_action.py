"""Unified launch and login orchestrator.

The 'go' action gets the system to a logged-in state from any starting point.
It detects the current state and takes appropriate actions to progress.
"""

import time
from typing import Optional

from model.actions.base import ActionOutcome
from model.system_state import SystemState, SystemStateDetector


def go(
    force_restart: bool = False,
    skip_login: bool = False,
    timeout: float = 180.0,
) -> ActionOutcome:
    """Get to logged-in state from any starting point.

    This is the main entry point for the unified launch/login flow.
    It detects the current state and takes appropriate actions.

    Args:
        force_restart: If True, close existing windows and start fresh.
        skip_login: If True, stop at the login screen (don't enter credentials).
        timeout: Overall timeout for the entire process.

    Returns:
        ActionOutcome indicating success or failure.
    """
    start_time = time.time()
    detector = SystemStateDetector()
    unknown_count = 0
    max_unknown_retries = 3

    # Track actions to prevent duplicates
    launch_initiated = False
    last_state = None
    credentials_retry_used = False  # Only retry on invalid credentials once

    # Force restart if requested
    if force_restart:
        result = _close_all_windows()
        if not result.success:
            return result
        time.sleep(3)  # Wait for windows to fully close

    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return ActionOutcome.fail(
                f"Timeout after {elapsed:.0f}s",
                elapsed=elapsed,
            )

        # Detect current state
        state = detector.detect()
        description = detector.get_state_description(state)

        # Only print if state changed
        if state != last_state:
            print(f"[GO] State: {state.name} - {description}")
            last_state = state

        # Check for success conditions
        if state == SystemState.RUNELITE_LOGGED_IN:
            return ActionOutcome.ok(
                "Successfully logged in",
                state=state.name,
                elapsed=elapsed,
            )

        if skip_login and state == SystemState.RUNELITE_LOGIN:
            return ActionOutcome.ok(
                "At login screen (skip_login=True)",
                state=state.name,
                elapsed=elapsed,
            )

        # Handle invalid credentials - retry once
        if state == SystemState.RUNELITE_INVALID_CREDENTIALS:
            if credentials_retry_used:
                return ActionOutcome.fail(
                    "Invalid credentials. Already retried once - check your OSBC_USERNAME and OSBC_PASSWORD.",
                    state=state.name,
                    retry_used=True,
                )
            print("[GO] Invalid credentials detected, clicking 'Try again'...")
            credentials_retry_used = True
            result = _handle_invalid_credentials()
            if not result.success:
                return result
            time.sleep(1)
            continue

        # Handle unknown state
        if state == SystemState.RUNELITE_UNKNOWN:
            unknown_count += 1
            if unknown_count >= max_unknown_retries:
                return ActionOutcome.fail(
                    f"Unable to determine state after {unknown_count} attempts. "
                    "Try --force-restart to start fresh.",
                    state=state.name,
                    unknown_count=unknown_count,
                )
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

        # Execute action for current state
        result = _handle_state(state, skip_login)
        if not result.success:
            return result

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


def _handle_invalid_credentials() -> ActionOutcome:
    """Click 'Try again' button to return to login screen."""
    from utilities.window import Window
    from model.login.login_screen import LoginScreenDetector
    from model.actions.executor import Executor
    from model.actions.intents import ClickIntent

    try:
        win = Window("RuneLite", padding_top=26, padding_left=0)

        # Focus window before clicking
        try:
            win.focus()
            time.sleep(0.3)
        except Exception:
            pass

        detector = LoginScreenDetector(win)
        button = detector.get_try_again_button_location()

        if not button:
            return ActionOutcome.fail("Could not find 'Try again' button")

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

        click = ClickIntent(point=button.random_point(), speed="medium")
        result = executor.execute(click)

        if result.success:
            time.sleep(1)  # Wait for transition
            return ActionOutcome.ok("Clicked 'Try again'")
        else:
            return ActionOutcome.fail(f"Failed to click: {result.message}")

    except Exception as e:
        return ActionOutcome.fail(f"Error clicking Try again: {e}")


def _handle_welcome() -> ActionOutcome:
    """Click 'Existing User' button on welcome screen."""
    print("[GO] Clicking 'Existing User'...")
    from utilities.window import Window
    from model.login.login_screen import LoginScreenDetector
    from model.actions.executor import Executor
    from model.actions.intents import ClickIntent

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
            return ActionOutcome.fail("Could not find 'Existing User' button")

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

        click = ClickIntent(point=button.random_point(), speed="medium")
        result = executor.execute(click)

        if result.success:
            time.sleep(1)  # Wait for transition
            return ActionOutcome.ok("Clicked 'Existing User'")
        else:
            return ActionOutcome.fail(f"Failed to click: {result.message}")

    except Exception as e:
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
        else:
            center = button.random_point()

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
            return ActionOutcome.ok("Clicked to play")
        else:
            return ActionOutcome.fail(f"Failed to click: {result.message}")

    except Exception as e:
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
