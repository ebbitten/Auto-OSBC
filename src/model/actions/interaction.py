"""Interaction action primitives for bot scripts.

This module provides reusable functions for finding and interacting
with tagged objects in the game world.

Actions in this module return intents instead of performing side effects.
Use the Executor to actually perform the mouse movements and clicks.
"""

from typing import TYPE_CHECKING, List, Optional

from .base import ActionOutcome
from .intents import ClickIntent, MoveIntent

if TYPE_CHECKING:
    from model.runelite_bot import RuneLiteBot
    from utilities.color import Color
    from utilities.geometry import Rectangle, RuneLiteObject


def find_and_interact(
    bot: "RuneLiteBot",
    color: "Color",
    search_rect: Optional["Rectangle"] = None,
    mouse_speed: str = "medium",
    right_click: bool = False,
) -> ActionOutcome:
    """
    Find the nearest tagged object and return an intent to click on it.

    This is the most common interaction pattern in bots:
    1. Search for tagged objects of a specific color
    2. Find the nearest one to the player
    3. Return a ClickIntent for the Executor to perform

    Args:
        bot: The RuneLiteBot instance
        color: The tag color to search for (e.g., clr.PINK, clr.CYAN)
        search_rect: Rectangle to search in (defaults to game_view)
        mouse_speed: Mouse movement speed ("slowest", "slow", "medium", "fast", "fastest")
        right_click: Whether to right-click instead of left-click

    Returns:
        ActionOutcome.ok() with intent=ClickIntent if object found
        ActionOutcome.fail() if no objects found
    """
    rect = search_rect or bot.win.game_view

    # Find all tagged objects
    objects = bot.get_all_tagged_in_rect(rect, color)

    if not objects:
        return ActionOutcome.fail(
            f"No objects found with color {color.name if hasattr(color, 'name') else color}",
            color=str(color),
        )

    # Get the nearest object (sorted by distance from center of search rect)
    # Use the object's rect reference if available, otherwise use simple distance
    def get_distance(obj):
        if hasattr(obj, 'rect') and obj.rect is not None:
            from utilities.geometry import RuneLiteObject
            return RuneLiteObject.distance_from_rect_center(obj)
        # Fallback: distance from origin (0,0) for simple sorting
        center = obj.center() if hasattr(obj, 'center') else obj._center
        if hasattr(center, 'x'):
            return (center.x ** 2 + center.y ** 2) ** 0.5
        return (center[0] ** 2 + center[1] ** 2) ** 0.5

    sorted_objects = sorted(objects, key=get_distance)
    nearest = sorted_objects[0]

    # Calculate click target
    target_point = nearest.random_point()
    click_point = (target_point.x, target_point.y)

    # Create intent for execution
    intent = ClickIntent(
        point=click_point,
        speed=mouse_speed,
        right_click=right_click,
    )

    return ActionOutcome.ok(
        f"Found object at ({click_point[0]}, {click_point[1]})",
        intent=intent,
        object_center=nearest._center,
        click_point=click_point,
        object_count=len(objects),
    )


def find_all_tagged(
    bot: "RuneLiteBot",
    color: "Color",
    search_rect: Optional["Rectangle"] = None,
) -> ActionOutcome:
    """
    Find all tagged objects of a specific color.

    Use this when you need to examine multiple objects before
    deciding which one to interact with.

    Args:
        bot: The RuneLiteBot instance
        color: The tag color to search for
        search_rect: Rectangle to search in (defaults to game_view)

    Returns:
        ActionOutcome.ok() with list of objects
        ActionOutcome.fail() if no objects found
    """
    rect = search_rect or bot.win.game_view

    objects = bot.get_all_tagged_in_rect(rect, color)

    if not objects:
        return ActionOutcome.fail(
            f"No objects found with color {color.name if hasattr(color, 'name') else color}",
            color=str(color),
        )

    # Sort by distance from center of search rect
    def get_distance(obj):
        if hasattr(obj, 'rect') and obj.rect is not None:
            from utilities.geometry import RuneLiteObject
            return RuneLiteObject.distance_from_rect_center(obj)
        center = obj.center() if hasattr(obj, 'center') else obj._center
        if hasattr(center, 'x'):
            return (center.x ** 2 + center.y ** 2) ** 0.5
        return (center[0] ** 2 + center[1] ** 2) ** 0.5

    sorted_objects = sorted(objects, key=get_distance)

    return ActionOutcome.ok(
        f"Found {len(objects)} objects",
        objects=sorted_objects,
        count=len(objects),
    )


def click_object(
    bot: "RuneLiteBot",
    obj: "RuneLiteObject",
    mouse_speed: str = "medium",
    right_click: bool = False,
) -> ActionOutcome:
    """
    Return an intent to click on a specific RuneLiteObject.

    Use this when you already have a reference to an object
    (e.g., from find_all_tagged) and want to click it.

    Args:
        bot: The RuneLiteBot instance (not used, kept for API compatibility)
        obj: The RuneLiteObject to click
        mouse_speed: Mouse movement speed
        right_click: Whether to right-click instead of left-click

    Returns:
        ActionOutcome.ok() with intent=ClickIntent
    """
    target_point = obj.random_point()
    click_point = (target_point.x, target_point.y)

    intent = ClickIntent(
        point=click_point,
        speed=mouse_speed,
        right_click=right_click,
    )

    return ActionOutcome.ok(
        f"Click intent for object at ({click_point[0]}, {click_point[1]})",
        intent=intent,
        click_point=click_point,
        right_click=right_click,
    )


def find_nearest_npc(
    bot: "RuneLiteBot",
    include_in_combat: bool = False,
) -> ActionOutcome:
    """
    Find the nearest tagged NPC.

    Uses cyan color tag for NPC detection and optionally
    filters out NPCs that are already in combat.

    Args:
        bot: The RuneLiteBot instance
        include_in_combat: Whether to include NPCs already in combat

    Returns:
        ActionOutcome.ok() with nearest NPC
        ActionOutcome.fail() if no NPCs found
    """
    npc = bot.get_nearest_tagged_NPC(include_in_combat=include_in_combat)

    if npc is None:
        return ActionOutcome.fail(
            "No tagged NPCs found",
            include_in_combat=include_in_combat,
        )

    return ActionOutcome.ok(
        "Found nearest NPC",
        npc=npc,
        center=npc._center,
    )


def interact_with_nearest_npc(
    bot: "RuneLiteBot",
    include_in_combat: bool = False,
    mouse_speed: str = "medium",
) -> ActionOutcome:
    """
    Find the nearest tagged NPC and return an intent to click it.

    Combines find_nearest_npc and click_object into a single
    convenient action.

    Args:
        bot: The RuneLiteBot instance
        include_in_combat: Whether to include NPCs already in combat
        mouse_speed: Mouse movement speed

    Returns:
        ActionOutcome.ok() with intent=ClickIntent if NPC found
        ActionOutcome.fail() if no NPCs found
    """
    find_result = find_nearest_npc(bot, include_in_combat)

    if find_result.failed:
        return find_result

    npc = find_result.data["npc"]
    click_result = click_object(bot, npc, mouse_speed=mouse_speed)

    # Combine NPC data with click intent
    return ActionOutcome.ok(
        f"Found NPC to click at {click_result.data['click_point']}",
        intent=click_result.data["intent"],
        npc=npc,
        click_point=click_result.data["click_point"],
    )


def click_at_point(
    bot: "RuneLiteBot",
    x: int,
    y: int,
    mouse_speed: str = "medium",
    right_click: bool = False,
) -> ActionOutcome:
    """
    Return an intent to click at a specific screen coordinate.

    Lower-level function for when you need precise control
    over where to click.

    Args:
        bot: The RuneLiteBot instance (not used, kept for API compatibility)
        x: X coordinate
        y: Y coordinate
        mouse_speed: Mouse movement speed
        right_click: Whether to right-click instead of left-click

    Returns:
        ActionOutcome.ok() with intent=ClickIntent
    """
    intent = ClickIntent(
        point=(x, y),
        speed=mouse_speed,
        right_click=right_click,
    )

    return ActionOutcome.ok(
        f"Click intent at ({x}, {y})",
        intent=intent,
        click_point=(x, y),
        right_click=right_click,
    )


def hover_object(
    bot: "RuneLiteBot",
    obj: "RuneLiteObject",
    mouse_speed: str = "medium",
) -> ActionOutcome:
    """
    Return an intent to move mouse over an object without clicking.

    Useful for checking mouseover text before deciding
    to click, or for preparation before a timed click.

    Args:
        bot: The RuneLiteBot instance (not used, kept for API compatibility)
        obj: The RuneLiteObject to hover over
        mouse_speed: Mouse movement speed

    Returns:
        ActionOutcome.ok() with intent=MoveIntent
    """
    target_point = obj.random_point()
    hover_point = (target_point.x, target_point.y)

    intent = MoveIntent(
        point=hover_point,
        speed=mouse_speed,
    )

    return ActionOutcome.ok(
        f"Move intent to ({hover_point[0]}, {hover_point[1]})",
        intent=intent,
        hover_point=hover_point,
    )
