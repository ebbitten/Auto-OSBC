"""GameState protocol defining the interface for game state queries.

This protocol allows bots to query game state through an injectable interface,
enabling both live game detection (RealGameState) and testing (MockGameState).
"""

from typing import TYPE_CHECKING, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from utilities.color import Color
    from utilities.geometry import Rectangle, RuneLiteObject


@runtime_checkable
class GameState(Protocol):
    """Protocol for querying game state.

    This abstraction allows bot logic to be tested without a running game client
    by injecting a MockGameState instead of the RealGameState.
    """

    # ===== Inventory =====

    def is_inventory_full(self) -> bool:
        """Check if the inventory has 28 items."""
        ...

    def count_inventory_items(self) -> int:
        """Count the number of items in inventory."""
        ...

    def is_slot_empty(self, slot_index: int) -> bool:
        """Check if a specific inventory slot is empty."""
        ...

    # ===== Player Status =====

    def is_player_idle(self) -> bool:
        """Check if the player is currently idle (not performing an action)."""
        ...

    def is_player_doing_action(self, action: str) -> bool:
        """Check if the player is doing a specific action (e.g., 'Mining', 'Woodcutting')."""
        ...

    def is_in_combat(self) -> bool:
        """Check if the player is currently in combat."""
        ...

    def get_hp(self) -> int:
        """Get the player's current HP percentage (0-100)."""
        ...

    def get_prayer(self) -> int:
        """Get the player's current prayer points."""
        ...

    def get_run_energy(self) -> int:
        """Get the player's current run energy percentage."""
        ...

    # ===== Object Detection =====

    def find_tagged_objects(self, rect: "Rectangle", color: "Color") -> List["RuneLiteObject"]:
        """Find all objects of a specific color within a rectangle."""
        ...

    def find_nearest_tag(self, color: "Color") -> Optional["RuneLiteObject"]:
        """Find the nearest tagged object of a specific color."""
        ...

    def find_nearest_npc(self, include_in_combat: bool = False) -> Optional["RuneLiteObject"]:
        """Find the nearest tagged NPC."""
        ...

    # ===== Safety =====

    def are_friends_nearby(self) -> bool:
        """Check if friends are nearby (green dots on minimap)."""
        ...

    # ===== UI State =====

    def get_mouseover_text(self) -> str:
        """Get the text currently shown in mouseover tooltip."""
        ...

    def has_hp_bar(self) -> bool:
        """Check if an HP bar is visible (indicates combat)."""
        ...
