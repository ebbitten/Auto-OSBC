"""Waiting action primitives for bot scripts.

This module provides reusable waiting functions that return WaitIntent
objects for the Executor to poll game state until a condition is met
or timeout occurs.
"""

from typing import TYPE_CHECKING, Callable

from .base import ActionOutcome
from .intents import WaitIntent

if TYPE_CHECKING:
    from model.bot import Bot


def wait_for_idle(
    bot: "Bot",
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.1,
) -> ActionOutcome:
    """
    Return an intent to wait until the player becomes idle.

    Args:
        bot: The bot instance with game state access
        timeout_seconds: Maximum time to wait before timing out
        poll_interval: Time between state checks

    Returns:
        ActionOutcome.ok() with intent=WaitIntent
    """
    def check_idle() -> bool:
        return bot.is_player_idle_visual()

    intent = WaitIntent(
        condition=check_idle,
        timeout=timeout_seconds,
        poll_interval=poll_interval,
        description="player idle",
    )

    return ActionOutcome.ok(
        "Wait intent for player idle",
        intent=intent,
        timeout_seconds=timeout_seconds,
    )


def wait_for_action(
    bot: "Bot",
    action_name: str,
    timeout_seconds: float = 5.0,
    poll_interval: float = 0.1,
) -> ActionOutcome:
    """
    Return an intent to wait until the player starts a specific action.

    Useful for verifying that a click registered and the player
    began the expected action (e.g., "Mining", "Woodcutting").

    Args:
        bot: The bot instance with game state access
        action_name: The action text to wait for (case-insensitive)
        timeout_seconds: Maximum time to wait before timing out
        poll_interval: Time between state checks

    Returns:
        ActionOutcome.ok() with intent=WaitIntent
    """
    def check_action() -> bool:
        if hasattr(bot, 'game_state') and bot.game_state is not None:
            return bot.game_state.is_player_doing_action(action_name)
        else:
            # Fallback: Player is NOT idle means they're doing something
            return not bot.is_player_idle_visual()

    intent = WaitIntent(
        condition=check_action,
        timeout=timeout_seconds,
        poll_interval=poll_interval,
        description=f"action '{action_name}' started",
    )

    return ActionOutcome.ok(
        f"Wait intent for action '{action_name}'",
        intent=intent,
        action=action_name,
        timeout_seconds=timeout_seconds,
    )


def wait_while_action(
    bot: "Bot",
    action_name: str,
    timeout_seconds: float = 60.0,
    poll_interval: float = 0.1,
) -> ActionOutcome:
    """
    Return an intent to wait while the player is doing a specific action.

    Continues waiting as long as the player is performing the action,
    returns when they stop or timeout is reached.

    Args:
        bot: The bot instance with game state access
        action_name: The action text to wait during (case-insensitive)
        timeout_seconds: Maximum time to wait before timing out
        poll_interval: Time between state checks

    Returns:
        ActionOutcome.ok() with intent=WaitIntent
    """
    def check_not_action() -> bool:
        if hasattr(bot, 'game_state') and bot.game_state is not None:
            return not bot.game_state.is_player_doing_action(action_name)
        else:
            # Fallback: Player is idle means action finished
            return bot.is_player_idle_visual()

    intent = WaitIntent(
        condition=check_not_action,
        timeout=timeout_seconds,
        poll_interval=poll_interval,
        description=f"action '{action_name}' completed",
    )

    return ActionOutcome.ok(
        f"Wait intent for action '{action_name}' to complete",
        intent=intent,
        action=action_name,
        timeout_seconds=timeout_seconds,
    )


def wait_until(
    bot: "Bot",
    condition: Callable[["Bot"], bool],
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.1,
    description: str = "condition",
) -> ActionOutcome:
    """
    Return an intent to wait until a custom condition is met.

    Generic waiting function for any condition that can be checked
    against the bot's game state.

    Args:
        bot: The bot instance with game state access
        condition: Callable that takes bot and returns True when condition is met
        timeout_seconds: Maximum time to wait before timing out
        poll_interval: Time between state checks
        description: Human-readable description for logging

    Returns:
        ActionOutcome.ok() with intent=WaitIntent

    Example:
        # Wait until inventory has at least 10 items
        result = wait_until(
            bot,
            lambda b: b.count_inventory_items_visual() >= 10,
            timeout_seconds=60.0,
            description="inventory has 10+ items"
        )
        executor.execute(result.data["intent"])
    """
    # Wrap the condition to not require bot arg (Executor doesn't pass it)
    def wrapped_condition() -> bool:
        try:
            return condition(bot)
        except Exception:
            return False

    intent = WaitIntent(
        condition=wrapped_condition,
        timeout=timeout_seconds,
        poll_interval=poll_interval,
        description=description,
    )

    return ActionOutcome.ok(
        f"Wait intent for '{description}'",
        intent=intent,
        timeout_seconds=timeout_seconds,
    )


def wait_for_inventory_change(
    bot: "Bot",
    expected_change: int,
    timeout_seconds: float = 10.0,
    poll_interval: float = 0.1,
) -> ActionOutcome:
    """
    Return an intent to wait for inventory count to change by expected amount.

    Args:
        bot: The bot instance with game state access
        expected_change: Expected change in count (+1 for gain, -1 for loss)
        timeout_seconds: Maximum time to wait before timing out
        poll_interval: Time between state checks

    Returns:
        ActionOutcome.ok() with intent=WaitIntent
    """
    start_count = bot.count_inventory_items_visual()
    target_count = start_count + expected_change

    def check_inventory_change() -> bool:
        current_count = bot.count_inventory_items_visual()
        if current_count == target_count:
            return True
        # Also succeed if we went past target
        if expected_change > 0 and current_count >= target_count:
            return True
        if expected_change < 0 and current_count <= target_count:
            return True
        return False

    intent = WaitIntent(
        condition=check_inventory_change,
        timeout=timeout_seconds,
        poll_interval=poll_interval,
        description=f"inventory change of {expected_change}",
    )

    return ActionOutcome.ok(
        f"Wait intent for inventory change by {expected_change}",
        intent=intent,
        start_count=start_count,
        expected_change=expected_change,
        timeout_seconds=timeout_seconds,
    )
