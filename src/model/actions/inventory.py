"""Inventory management action primitives for bot scripts.

This module provides reusable functions for inventory checking
and item management.

Actions that modify inventory state return intents for the Executor to perform.
Query functions (is_full, count_items, has_space) are pure and have no side effects.
"""

from typing import TYPE_CHECKING, List, Optional

from .base import ActionOutcome
from .intents import DropIntent, DropSlotsIntent, WaitIntent

if TYPE_CHECKING:
    from model.bot import Bot


def manage_if_full(
    bot: "Bot",
    skip_slots: Optional[List[int]] = None,
    skip_rows: int = 0,
) -> ActionOutcome:
    """
    Check if inventory is full and return an intent to drop items if so.

    This is the most common inventory management pattern:
    check if full, and if so, return a DropIntent for the Executor.

    Args:
        bot: The bot instance
        skip_slots: List of slot indices to keep (0-27)
        skip_rows: Number of rows from top to keep (0-6)

    Returns:
        ActionOutcome.ok() with intent=DropIntent if full
        ActionOutcome.skip() if inventory not full
    """
    if skip_slots is None:
        skip_slots = []

    if not bot.is_inventory_full_visual():
        return ActionOutcome.skip(
            "Inventory not full",
            dropped=False,
            inventory_count=bot.count_inventory_items_visual(),
        )

    # Inventory is full, create drop intent
    intent = DropIntent(
        skip_slots=skip_slots,
        skip_rows=skip_rows,
    )

    return ActionOutcome.ok(
        "Inventory full - drop intent created",
        intent=intent,
        dropped=True,
        skip_slots=skip_slots,
        skip_rows=skip_rows,
    )


def drop_all_items(
    bot: "Bot",
    skip_slots: Optional[List[int]] = None,
    skip_rows: int = 0,
) -> ActionOutcome:
    """
    Return an intent to drop all items in inventory.

    Unlike manage_if_full, this creates a drop intent regardless of
    whether inventory is full.

    Args:
        bot: The bot instance
        skip_slots: List of slot indices to keep (0-27)
        skip_rows: Number of rows from top to keep (0-6)

    Returns:
        ActionOutcome.ok() with intent=DropIntent
        ActionOutcome.skip() if inventory already empty
    """
    if skip_slots is None:
        skip_slots = []

    initial_count = bot.count_inventory_items_visual()

    if initial_count == 0:
        return ActionOutcome.skip(
            "Inventory already empty",
            initial_count=0,
        )

    intent = DropIntent(
        skip_slots=skip_slots,
        skip_rows=skip_rows,
    )

    return ActionOutcome.ok(
        f"Drop intent for {initial_count} items",
        intent=intent,
        initial_count=initial_count,
    )


def drop_slots(
    bot: "Bot",
    slots: List[int],
) -> ActionOutcome:
    """
    Return an intent to drop items in specific inventory slots.

    Use this when you need fine-grained control over which
    items to drop rather than dropping everything.

    Args:
        bot: The bot instance
        slots: List of slot indices to drop (0-27)

    Returns:
        ActionOutcome.ok() with intent=DropSlotsIntent
        ActionOutcome.skip() if no slots specified
    """
    if not slots:
        return ActionOutcome.skip(
            "No slots specified to drop",
            slots=[],
        )

    intent = DropSlotsIntent(slots=slots)

    return ActionOutcome.ok(
        f"Drop intent for slots {slots}",
        intent=intent,
        slots=slots,
    )


def is_full(bot: "Bot") -> ActionOutcome:
    """
    Check if inventory is full.

    Simple query action that returns the inventory state.
    No intent is returned - this is a pure query.

    Args:
        bot: The bot instance

    Returns:
        ActionOutcome.ok() with is_full and count data
    """
    full = bot.is_inventory_full_visual()
    count = bot.count_inventory_items_visual()

    return ActionOutcome.ok(
        f"Inventory {'full' if full else 'not full'} ({count}/28)",
        is_full=full,
        count=count,
        capacity=28,
    )


def count_items(bot: "Bot") -> ActionOutcome:
    """
    Count items in inventory.

    Simple query action that returns the item count.
    No intent is returned - this is a pure query.

    Args:
        bot: The bot instance

    Returns:
        ActionOutcome.ok() with count data
    """
    count = bot.count_inventory_items_visual()
    empty_slots = 28 - count

    return ActionOutcome.ok(
        f"Inventory has {count} items, {empty_slots} empty slots",
        count=count,
        empty_slots=empty_slots,
        capacity=28,
    )


def has_space(bot: "Bot", required_slots: int = 1) -> ActionOutcome:
    """
    Check if inventory has enough empty space.

    No intent is returned - this is a pure query.

    Args:
        bot: The bot instance
        required_slots: Number of empty slots needed

    Returns:
        ActionOutcome.ok() with has_space=True if enough space
        ActionOutcome.ok() with has_space=False if not enough space
    """
    count = bot.count_inventory_items_visual()
    empty_slots = 28 - count
    has_enough = empty_slots >= required_slots

    return ActionOutcome.ok(
        f"Inventory has {empty_slots} empty slots (need {required_slots})",
        has_space=has_enough,
        empty_slots=empty_slots,
        required_slots=required_slots,
        count=count,
    )


def wait_for_items(
    bot: "Bot",
    target_count: int,
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.5,
) -> ActionOutcome:
    """
    Return an intent to wait until inventory reaches a specific item count.

    Useful for waiting to collect a certain number of items
    before proceeding (e.g., wait for 28 items before banking).

    The returned WaitIntent should be executed by the Executor.

    Args:
        bot: The bot instance
        target_count: Number of items to wait for
        timeout_seconds: Maximum time to wait
        poll_interval: Time between checks

    Returns:
        ActionOutcome.ok() with intent=WaitIntent
    """
    # Create a condition closure that checks the inventory count
    def check_inventory_count() -> bool:
        return bot.count_inventory_items_visual() >= target_count

    intent = WaitIntent(
        condition=check_inventory_count,
        timeout=timeout_seconds,
        poll_interval=poll_interval,
        description=f"waiting for {target_count} items",
    )

    return ActionOutcome.ok(
        f"Wait intent for {target_count} items",
        intent=intent,
        target_count=target_count,
        timeout_seconds=timeout_seconds,
    )
