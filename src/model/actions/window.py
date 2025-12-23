"""Window launching and confirmation actions.

Provides actions for launching applications and confirming their windows appear.
This is a building block for scripts that need to launch OSBC, RuneLite, etc.

Follows the action/confirmation tuple pattern:
- prepare_* functions return LaunchIntent (action)
- confirm_* functions check if action succeeded (confirmation)
- Executor._execute_launch() performs the actual side effect
"""

import time
from typing import List, Optional

import pywinctl

from model.actions.base import ActionOutcome
from model.actions.intents import LaunchIntent


def find_window(title_pattern: str, exact: bool = False) -> Optional[pywinctl.Window]:
    """Find a window by title pattern.

    Args:
        title_pattern: Text to search for in window titles
        exact: If True, require exact match; if False, partial match

    Returns:
        The matching window, or None if not found
    """
    windows = pywinctl.getAllWindows()
    for window in windows:
        if exact:
            if window.title == title_pattern:
                return window
        else:
            if title_pattern.lower() in window.title.lower():
                return window
    return None


def wait_for_window(
    title_pattern: str,
    timeout: float = 30.0,
    poll_interval: float = 0.5,
    exact: bool = False,
) -> ActionOutcome:
    """Wait for a window with the given title to appear.

    Args:
        title_pattern: Text to search for in window titles
        timeout: Maximum time to wait in seconds
        poll_interval: Time between checks in seconds
        exact: If True, require exact title match

    Returns:
        ActionOutcome with success if window found, timeout if not
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        window = find_window(title_pattern, exact=exact)
        if window:
            return ActionOutcome.ok(
                f"Window '{title_pattern}' found",
                window_title=window.title,
                elapsed_seconds=time.time() - start_time,
            )
        time.sleep(poll_interval)

    return ActionOutcome.timeout(
        f"Window '{title_pattern}' not found within {timeout}s",
        timeout_seconds=timeout,
    )


def prepare_launch_osbc(
    timeout: float = 30.0,
) -> ActionOutcome:
    """Prepare to launch the OSBC GUI - returns LaunchIntent.

    This follows the action/confirmation tuple pattern:
    - Returns LaunchIntent (action) that can be executed by Executor
    - Use confirm_window_exists("OS Bot") to verify launch succeeded

    Args:
        timeout: Maximum time to wait for OSBC window

    Returns:
        ActionOutcome with intent=LaunchIntent if executable found, failure otherwise
    """
    import sys
    from pathlib import Path

    # Find the osbc executable in the same venv
    venv_scripts = Path(sys.executable).parent
    osbc_exe = venv_scripts / "osbc.exe"

    if not osbc_exe.exists():
        osbc_exe = venv_scripts / "osbc"  # Linux/Mac

    if not osbc_exe.exists():
        return ActionOutcome.fail(
            "Could not find osbc executable",
            searched_path=str(venv_scripts),
        )

    intent = LaunchIntent(
        command=[str(osbc_exe), "gui"],
        expected_window="OS Bot",
        timeout=timeout,
    )

    return ActionOutcome.ok(
        "Ready to launch OSBC",
        intent=intent,
        executable=str(osbc_exe),
    )


def prepare_launch_runelite(
    runelite_path: Optional[str] = None,
    timeout: float = 60.0,
) -> ActionOutcome:
    """Prepare to launch RuneLite - returns LaunchIntent.

    This follows the action/confirmation tuple pattern:
    - Returns LaunchIntent (action) that can be executed by Executor
    - Use confirm_window_exists("RuneLite") to verify launch succeeded

    Args:
        runelite_path: Path to RuneLite executable (auto-detected if not provided)
        timeout: Maximum time to wait for RuneLite window

    Returns:
        ActionOutcome with intent=LaunchIntent if executable found, failure otherwise
    """
    import os

    # Try to find RuneLite
    possible_paths = []
    if runelite_path is None:
        # Common locations
        possible_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\RuneLite\RuneLite.exe"),
            os.path.expandvars(r"%USERPROFILE%\.runelite\RuneLite.exe"),
            r"C:\Program Files\RuneLite\RuneLite.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                runelite_path = path
                break

    if runelite_path is None or not os.path.exists(runelite_path):
        return ActionOutcome.fail(
            "Could not find RuneLite executable",
            searched_paths=possible_paths if not runelite_path else [runelite_path],
        )

    intent = LaunchIntent(
        command=[runelite_path],
        expected_window="RuneLite",
        timeout=timeout,
    )

    return ActionOutcome.ok(
        "Ready to launch RuneLite",
        intent=intent,
        executable=runelite_path,
    )


# Keep old names as aliases for backwards compatibility
def launch_osbc(timeout: float = 30.0) -> ActionOutcome:
    """Deprecated: Use prepare_launch_osbc() and Executor instead."""
    return prepare_launch_osbc(timeout)


def launch_runelite(runelite_path: Optional[str] = None, timeout: float = 60.0) -> ActionOutcome:
    """Deprecated: Use prepare_launch_runelite() and Executor instead."""
    return prepare_launch_runelite(runelite_path, timeout)


def confirm_window_exists(
    window_pattern: str,
    exact: bool = False,
) -> ActionOutcome:
    """Check if a window exists right now (no waiting).

    Args:
        window_pattern: Title pattern to search for
        exact: Require exact title match

    Returns:
        ActionOutcome with success if window exists, failure if not
    """
    window = find_window(window_pattern, exact=exact)
    if window:
        return ActionOutcome.ok(
            f"Window '{window_pattern}' exists",
            window_title=window.title,
        )
    else:
        return ActionOutcome.fail(
            f"Window '{window_pattern}' not found",
        )
