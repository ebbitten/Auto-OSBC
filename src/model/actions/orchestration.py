"""Orchestration layer for complex multi-step workflows.

Combines individual action/confirmation pairs into complete workflows.
Each workflow function handles the full sequence of steps needed for a task.
"""

import time
from typing import Optional

from model.actions.base import ActionOutcome
from model.actions.executor import Executor
from model.actions import osbc, window


def auto_launch_runelite(
    game: str = "OSRS",
    skip_if_running: bool = True,
    login: bool = False,
    timeout: float = 120.0,
    step_delay: float = 0.5,
    character_name: Optional[str] = None,
    position_in_bot_zone: bool = True,
) -> ActionOutcome:
    """Full auto-launch workflow: OSBC -> Select Game -> Launch -> RuneLite.

    This orchestrates the complete workflow to get RuneLite running:
    1. Check if RuneLite is already running (skip if so)
    2. Launch OSBC GUI if not running
    3. Click game dropdown and select the game
    4. Click the Launch button
    5. Wait for RuneLite window to appear
    6. Position window in bot zone (ultrawide support)
    7. Optionally trigger login

    Args:
        game: Game to select (default "OSRS")
        skip_if_running: If True, return success immediately if RuneLite is running
        login: If True, trigger login after RuneLite launches
        timeout: Max time to wait for RuneLite window
        step_delay: Delay between steps for UI stability
        character_name: Expected character name. If provided, only considers a
                       RuneLite window as 'running' if it matches this character.
                       Allows launching a new window even if user has their own
                       RuneLite open with a different character.
        position_in_bot_zone: If True, position the launched window in the bot
                             zone (left third on ultrawide monitors)

    Returns:
        ActionOutcome with success if RuneLite is running, failure otherwise
    """
    from utilities.bot_window_service import get_bot_window_service
    from utilities.machine_config import get_machine_config

    service = get_bot_window_service()
    executor = Executor(bot=None)  # No bot needed for GUI interactions
    steps_completed = []

    # Step 1: Check current status using BotWindowService
    status = osbc.check_windows_status()
    steps_completed.append(f"Status: {status.message}")

    # Check for bot's RuneLite window
    if skip_if_running:
        bot_window = service.find_bot_runelite_window()
        if bot_window:
            steps_completed.append(f"Found bot's existing window: {bot_window.title}")

            # Position in bot zone if requested
            if position_in_bot_zone:
                config = get_machine_config()
                zone = config.get_bot_zone()
                target_width, target_height = config.get_window_target_size()
                try:
                    bot_window.moveTo(zone["left"], 0)
                    bot_window.resizeTo(target_width, target_height)
                    steps_completed.append(f"Positioned in bot zone (left={zone['left']}, size={target_width}x{target_height})")
                except Exception as e:
                    steps_completed.append(f"Warning: Could not position window: {e}")

            return ActionOutcome.ok(
                f"Bot's RuneLite already running",
                runelite_title=bot_window.title,
                steps=steps_completed,
                skipped=True,
                character_name=service.get_bot_character(),
            )

    # Step 2: Launch OSBC if not running
    if not status.data.get("osbc_running"):
        steps_completed.append("Launching OSBC...")

        launch_result = window.prepare_launch_osbc(timeout=30.0)
        if not launch_result.success:
            return ActionOutcome.fail(
                f"Failed to prepare OSBC launch: {launch_result.message}",
                steps=steps_completed,
            )

        exec_result = executor.execute(launch_result.data["intent"])
        if not exec_result.success:
            return ActionOutcome.fail(
                f"Failed to launch OSBC: {exec_result.message}",
                steps=steps_completed,
            )

        # Wait for OSBC window
        wait_result = window.wait_for_window("OS Bot", timeout=30.0)
        if not wait_result.success:
            return ActionOutcome.fail(
                f"OSBC window did not appear: {wait_result.message}",
                steps=steps_completed,
            )

        steps_completed.append(f"OSBC launched: {wait_result.data.get('window_title')}")
        time.sleep(step_delay)

    # Step 3: Click game dropdown
    steps_completed.append("Opening game dropdown...")

    dropdown_result = osbc.prepare_click_game_dropdown()
    if not dropdown_result.success:
        return ActionOutcome.fail(
            f"Failed to find game dropdown: {dropdown_result.message}",
            steps=steps_completed,
        )

    exec_result = executor.execute(dropdown_result.data["intent"])
    if not exec_result.success:
        return ActionOutcome.fail(
            f"Failed to click dropdown: {exec_result.message}",
            steps=steps_completed,
        )

    steps_completed.append("Dropdown clicked")
    time.sleep(step_delay)

    # Step 4: Select game
    steps_completed.append(f"Selecting {game}...")

    select_result = osbc.prepare_select_game(game)
    if not select_result.success:
        return ActionOutcome.fail(
            f"Failed to prepare game selection: {select_result.message}",
            steps=steps_completed,
        )

    exec_result = executor.execute(select_result.data["intent"])
    if not exec_result.success:
        return ActionOutcome.fail(
            f"Failed to select game: {exec_result.message}",
            steps=steps_completed,
        )

    steps_completed.append(f"Selected {game}")
    time.sleep(step_delay)

    # Step 5: Click Launch button
    steps_completed.append("Clicking Launch button...")

    launch_btn_result = osbc.prepare_click_launch_button()
    if not launch_btn_result.success:
        return ActionOutcome.fail(
            f"Failed to find Launch button: {launch_btn_result.message}",
            steps=steps_completed,
        )

    exec_result = executor.execute(launch_btn_result.data["intent"])
    if not exec_result.success:
        return ActionOutcome.fail(
            f"Failed to click Launch button: {exec_result.message}",
            steps=steps_completed,
        )

    steps_completed.append("Launch button clicked")

    # Step 6: Wait for RuneLite window
    steps_completed.append(f"Waiting for RuneLite (timeout: {timeout}s)...")

    confirm_result = osbc.confirm_runelite_window(timeout=timeout)
    if not confirm_result.success:
        if confirm_result.timed_out:
            return ActionOutcome.timeout(
                f"RuneLite did not start within {timeout}s",
                steps=steps_completed,
                timeout_seconds=timeout,
            )
        return ActionOutcome.fail(
            f"Failed to confirm RuneLite: {confirm_result.message}",
            steps=steps_completed,
        )

    steps_completed.append(f"RuneLite ready: {confirm_result.data.get('window_title')}")

    # Step 7: Position in bot zone
    if position_in_bot_zone:
        config = get_machine_config()
        zone = config.get_bot_zone()
        target_width, target_height = config.get_window_target_size()

        # Use BotWindowService to find only the bot's window
        runelite_win = service.find_bot_runelite_window()

        if runelite_win:
            try:
                time.sleep(0.5)  # Brief pause for window to stabilize
                runelite_win.moveTo(zone["left"], 0)
                runelite_win.resizeTo(target_width, target_height)
                steps_completed.append(f"Positioned in bot zone (left={zone['left']}, size={target_width}x{target_height})")
            except Exception as e:
                steps_completed.append(f"Warning: Could not position window: {e}")

    # Step 8: Optional login
    if login:
        steps_completed.append("Login requested - triggering login flow...")
        # Login flow would be triggered here
        # For now, just note that it was requested
        return ActionOutcome.ok(
            "RuneLite launched - login requested but not yet implemented in orchestration",
            runelite_title=confirm_result.data.get("window_title"),
            steps=steps_completed,
            login_pending=True,
        )

    return ActionOutcome.ok(
        "RuneLite launched successfully",
        runelite_title=confirm_result.data.get("window_title"),
        elapsed_seconds=confirm_result.data.get("elapsed_seconds"),
        steps=steps_completed,
    )


def shutdown_all(
    close_runelite: bool = True,
    close_osbc: bool = True,
) -> ActionOutcome:
    """Gracefully close bot's RuneLite and/or OSBC windows.

    Uses BotWindowService to ensure we only close the bot's windows,
    not the user's personal RuneLite windows.

    Args:
        close_runelite: Close bot's RuneLite if running
        close_osbc: Close OSBC if running

    Returns:
        ActionOutcome with status of shutdown
    """
    from utilities.bot_window_service import get_bot_window_service

    service = get_bot_window_service()
    closed = []

    if close_runelite:
        # Only close bot's RuneLite windows
        bot_runelite = service.find_bot_runelite_window()
        if bot_runelite:
            try:
                bot_runelite.close()
                closed.append(f"RuneLite ({bot_runelite.title})")
            except Exception as e:
                return ActionOutcome.fail(
                    f"Failed to close RuneLite: {e}",
                    closed=closed,
                )

    if close_osbc:
        osbc_win = service.find_osbc_window()
        if osbc_win:
            try:
                osbc_win.close()
                closed.append("OSBC")
            except Exception as e:
                return ActionOutcome.fail(
                    f"Failed to close OSBC: {e}",
                    closed=closed,
                )

    if not closed:
        return ActionOutcome.ok("No windows to close")

    return ActionOutcome.ok(
        f"Closed: {', '.join(closed)}",
        closed=closed,
    )
