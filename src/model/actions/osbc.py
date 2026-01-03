"""OSBC GUI interaction actions.

Building blocks for interacting with the OSBC application GUI.
Follows the action/confirmation tuple pattern.
"""

import time
from typing import Optional, Tuple

from model.actions.base import ActionOutcome
from model.actions.intents import ClickIntent
from model.actions.window import find_window
from utilities.imagesearch import BOT_IMAGES, get_template_path


def check_windows_status() -> ActionOutcome:
    """Check status of OSBC and bot's RuneLite windows.

    Uses BotWindowService to ensure we only check the bot's windows,
    not the user's personal RuneLite windows.

    Returns:
        ActionOutcome with window status data:
        - osbc_running: True if OSBC window found
        - runelite_running: True if bot's RuneLite window found
        - osbc_title: OSBC window title (if found)
        - runelite_title: RuneLite window title (if found)
    """
    from utilities.bot_window_service import get_bot_window_service

    service = get_bot_window_service()
    osbc_running, runelite_running, runelite_title = service.check_windows_status()

    osbc_window = service.find_osbc_window()
    osbc_title = osbc_window.title if osbc_window else None

    status_parts = []
    if osbc_running:
        status_parts.append(f"OSBC: {osbc_title}")
    else:
        status_parts.append("OSBC: not running")

    if runelite_running:
        status_parts.append(f"RuneLite: {runelite_title}")
    else:
        status_parts.append("RuneLite: not running")

    return ActionOutcome.ok(
        " | ".join(status_parts),
        osbc_running=osbc_running,
        runelite_running=runelite_running,
        osbc_title=osbc_title,
        runelite_title=runelite_title,
    )


def find_game_dropdown(osbc_window) -> Tuple[int, int]:
    """Find the 'Select a game' dropdown in OSBC sidebar.

    The dropdown is in the left sidebar, near the top.
    Uses machine profile for coordinates if available.

    Args:
        osbc_window: pywinctl Window object for OSBC

    Returns:
        (x, y) center point of dropdown
    """
    from utilities.machine_config import get_machine_config

    config = get_machine_config()
    osbc_ui = config.get("osbc_ui", default={})

    # Get dropdown position from config or use defaults
    dropdown_config = osbc_ui.get("game_dropdown", {})
    rel_x = dropdown_config.get("x", 130)  # Default: 130px from left
    rel_y = dropdown_config.get("y", 128)  # Default: 128px from top

    dropdown_x = osbc_window.left + rel_x
    dropdown_y = osbc_window.top + rel_y

    return (dropdown_x, dropdown_y)


def prepare_click_game_dropdown() -> ActionOutcome:
    """Prepare to click the 'Select a game' dropdown in OSBC.

    This is the first step to select a game before launching.

    Returns:
        ActionOutcome with ClickIntent for the dropdown
    """
    osbc_window = find_window("OS Bot")
    if not osbc_window:
        return ActionOutcome.fail("OSBC window not found")

    # Bring to foreground
    try:
        osbc_window.activate()
        time.sleep(0.3)
    except Exception:
        pass

    dropdown_point = find_game_dropdown(osbc_window)

    intent = ClickIntent(
        point=dropdown_point,
        speed="medium",
    )

    return ActionOutcome.ok(
        "Ready to click game dropdown",
        intent=intent,
        dropdown_point=dropdown_point,
    )


def prepare_select_game(game_name: str = "OSRS") -> ActionOutcome:
    """Prepare to select a game from the dropdown menu.

    Call this AFTER clicking the dropdown (prepare_click_game_dropdown).
    The dropdown must be open for this to work.

    Args:
        game_name: Name of game to select ("OSRS", "Alora", etc.)

    Returns:
        ActionOutcome with ClickIntent for the game option
    """
    import pyautogui

    osbc_window = find_window("OS Bot")
    if not osbc_window:
        return ActionOutcome.fail("OSBC window not found")

    # Try template matching for the game option
    template_path = BOT_IMAGES / "actions" / f"game_{game_name.lower()}.png"
    if template_path.exists():
        try:
            location = pyautogui.locateOnScreen(
                str(template_path),
                region=(osbc_window.left, osbc_window.top, osbc_window.width, osbc_window.height),
                confidence=0.7,
            )
            if location:
                center = pyautogui.center(location)
                intent = ClickIntent(point=(center.x, center.y), speed="medium")
                return ActionOutcome.ok(
                    f"Ready to select {game_name}",
                    intent=intent,
                    game_name=game_name,
                )
        except Exception:
            pass

    # Fallback: Calculate position based on machine config and dropdown order
    from utilities.machine_config import get_machine_config

    config = get_machine_config()
    osbc_ui = config.get("osbc_ui", default={})

    # Get dropdown position for base calculation
    dropdown_config = osbc_ui.get("game_dropdown", {})
    dropdown_x = dropdown_config.get("x", 110)
    dropdown_y = dropdown_config.get("y", 105)

    # OSRS option is below dropdown by offset
    osrs_offset = osbc_ui.get("osrs_option_offset_y", 60)

    game_order = {"osrs": 0, "alora": 1, "near reality": 2}
    game_index = game_order.get(game_name.lower(), 0)

    option_height = 33  # Each dropdown option is ~33px tall
    game_y = osbc_window.top + dropdown_y + osrs_offset + (game_index * option_height)
    game_x = osbc_window.left + dropdown_x

    intent = ClickIntent(point=(game_x, game_y), speed="medium")

    return ActionOutcome.ok(
        f"Ready to select {game_name} (fallback position)",
        intent=intent,
        game_name=game_name,
        position=(game_x, game_y),
    )


def find_launch_button(osbc_window) -> Optional[Tuple[int, int]]:
    """Find the Launch button in OSBC window using template matching.

    The Launch button only appears when a bot is selected. If no bot is
    selected, this function returns None.

    Args:
        osbc_window: pywinctl Window object for OSBC

    Returns:
        (x, y) center point of button, or None if not found
    """
    import pyautogui

    # Use template matching to find the button (supports per-machine templates)
    template_path = get_template_path("actions", "launch_button.png")
    if not template_path.exists():
        return None

    try:
        location = pyautogui.locateOnScreen(
            str(template_path),
            region=(
                osbc_window.left,
                osbc_window.top,
                osbc_window.width,
                osbc_window.height,
            ),
            confidence=0.85,  # Higher confidence to avoid false matches on similar blue UI elements
        )
        if location:
            center = pyautogui.center(location)
            return (center.x, center.y)
    except Exception:
        pass

    return None


def prepare_click_launch_button() -> ActionOutcome:
    """Find the Launch button in OSBC and prepare to click it.

    Uses template matching with fallback to calculated coordinates.
    This is the ACTION part of the action/confirmation pattern.

    PREREQUISITE: A game and bot must be selected in OSBC first.
    The Launch button only appears after selecting a bot from the Scripts menu.

    Returns:
        ActionOutcome with ClickIntent if button found, failure otherwise
    """
    # 1. Find OSBC window
    osbc_window = find_window("OS Bot")
    if not osbc_window:
        return ActionOutcome.fail("OSBC window not found")

    # 2. Bring window to foreground so click hits OSBC
    try:
        osbc_window.activate()
        time.sleep(0.3)  # Brief delay for window to come to front
    except Exception:
        pass  # Best effort - continue even if activation fails

    # 3. Find the Launch button
    button_point = find_launch_button(osbc_window)
    if not button_point:
        return ActionOutcome.fail(
            "Launch button not found. Make sure a game and bot are selected in OSBC."
        )

    # 4. Return click intent for button
    intent = ClickIntent(
        point=button_point,
        speed="medium",
    )

    return ActionOutcome.ok(
        "Ready to click Launch button",
        intent=intent,
        button_point=button_point,
    )


def click_launch_button() -> ActionOutcome:
    """Find and click the Launch button in OSBC.

    This combines prepare + execute for OSBC GUI interaction.
    Uses pyautogui directly since OSBC is outside the game.

    Returns:
        ActionOutcome with success if button clicked, failure otherwise
    """
    import pyautogui

    # Prepare (find the button)
    result = prepare_click_launch_button()
    if not result.success:
        return result

    # Execute (click the button)
    button_point = result.data["button_point"]
    try:
        pyautogui.click(button_point[0], button_point[1])
    except Exception as e:
        return ActionOutcome.fail(
            f"Failed to click Launch button: {e}",
            button_point=button_point,
            error=str(e),
        )

    return ActionOutcome.ok(
        "Clicked Launch button",
        button_point=button_point,
    )


def confirm_runelite_window(timeout: float = 60.0) -> ActionOutcome:
    """Confirm bot's RuneLite window appears after launch.

    This is the CONFIRMATION part of the action/confirmation pattern.
    Waits for the bot's RuneLite window to appear.

    Uses BotWindowService to ensure we only detect the bot's window.

    Args:
        timeout: Max time to wait for RuneLite window

    Returns:
        ActionOutcome with success if bot's RuneLite window found
    """
    from utilities.bot_window_service import get_bot_window_service

    service = get_bot_window_service()
    start_time = time.time()

    while time.time() - start_time < timeout:
        bot_window = service.find_bot_runelite_window()
        if bot_window:
            return ActionOutcome.ok(
                "RuneLite window detected",
                window_title=bot_window.title,
                elapsed_seconds=time.time() - start_time,
            )
        time.sleep(1.0)

    return ActionOutcome.timeout(
        f"Bot's RuneLite window not detected within {timeout}s",
        timeout_seconds=timeout,
    )


def confirm_runelite_login_screen(timeout: float = 60.0) -> ActionOutcome:
    """Confirm bot's RuneLite window exists and shows login screen.

    This is the CONFIRMATION part of the action/confirmation pattern.
    Waits for bot's RuneLite window to appear and verifies it's on the login screen.

    Uses BotWindowService to ensure we only detect the bot's window.

    Args:
        timeout: Max time to wait for RuneLite with login screen

    Returns:
        ActionOutcome with success if login screen detected
    """
    from model.login.login_screen import LoginScreenDetector, LoginState
    from utilities.bot_window_service import get_bot_window_service

    service = get_bot_window_service()
    start_time = time.time()

    while time.time() - start_time < timeout:
        # 1. Check if bot's RuneLite window exists
        bot_window = service.find_bot_runelite_window()
        if not bot_window:
            time.sleep(1.0)
            continue

        # 2. Get Window object for detector
        try:
            game_window = service.get_bot_window()

            # 3. Check if login screen is showing
            detector = LoginScreenDetector(window=game_window)
            state_info = detector.detect_state()

            if state_info.state == LoginState.LOGIN_SCREEN:
                return ActionOutcome.ok(
                    "RuneLite login screen detected",
                    window_title=bot_window.title,
                    login_state=state_info.state.name,
                    elapsed_seconds=time.time() - start_time,
                )
        except Exception:
            pass  # Detection failed, keep trying

        time.sleep(1.0)

    return ActionOutcome.timeout(
        f"RuneLite login screen not detected within {timeout}s",
        timeout_seconds=timeout,
    )
