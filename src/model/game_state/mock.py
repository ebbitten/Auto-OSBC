"""Mock game state for testing bot logic without a running game client.

Usage:
    mock_state = MockGameState(
        inventory_count=28,
        is_idle=True,
        friends_nearby=False
    )
    bot.game_state = mock_state

    # Test bot decisions
    action = bot.decide_next_action()
    assert action.name == "drop_all"
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from utilities.color import Color
    from utilities.geometry import Rectangle, RuneLiteObject


@dataclass
class MockGameState:
    """Mock implementation of GameState for testing.

    All state values are configurable via constructor or direct assignment.
    This allows testing bot logic in isolation without game client dependencies.
    """

    # Inventory state
    inventory_count: int = 0
    slot_states: Dict[int, bool] = field(default_factory=dict)  # slot_index -> is_empty

    # Player status
    is_idle: bool = True
    current_action: str = ""
    in_combat: bool = False
    hp: int = 99
    prayer: int = 99
    run_energy: int = 100

    # Object detection - maps color name to list of mock objects
    tagged_objects: Dict[str, List["RuneLiteObject"]] = field(default_factory=dict)
    nearest_npc: Optional["RuneLiteObject"] = None

    # Safety
    friends_nearby: bool = False

    # UI state
    mouseover_text: str = ""
    hp_bar_visible: bool = False

    # ===== Inventory Methods =====

    def is_inventory_full(self) -> bool:
        """Check if inventory has 28 items."""
        return self.inventory_count >= 28

    def count_inventory_items(self) -> int:
        """Return configured inventory count."""
        return self.inventory_count

    def is_slot_empty(self, slot_index: int) -> bool:
        """Check if specific slot is empty."""
        if slot_index in self.slot_states:
            return self.slot_states[slot_index]
        # Default: empty if slot_index >= inventory_count
        return slot_index >= self.inventory_count

    # ===== Player Status Methods =====

    def is_player_idle(self) -> bool:
        """Return configured idle state."""
        return self.is_idle

    def is_player_doing_action(self, action: str) -> bool:
        """Check if current action matches."""
        return self.current_action.lower() == action.lower()

    def is_in_combat(self) -> bool:
        """Return configured combat state."""
        return self.in_combat

    def get_hp(self) -> int:
        """Return configured HP."""
        return self.hp

    def get_prayer(self) -> int:
        """Return configured prayer points."""
        return self.prayer

    def get_run_energy(self) -> int:
        """Return configured run energy."""
        return self.run_energy

    # ===== Object Detection Methods =====

    def find_tagged_objects(self, rect: "Rectangle", color: "Color") -> List["RuneLiteObject"]:
        """Return configured tagged objects for the color.

        Args:
            rect: The rectangle to search in (ignored in mock)
            color: The color to search for

        Returns:
            List of mock RuneLiteObjects configured for this color
        """
        # Get color name from Color object or use as string
        color_name = getattr(color, 'name', str(color)).upper()
        return self.tagged_objects.get(color_name, [])

    def find_nearest_tag(self, color: "Color") -> Optional["RuneLiteObject"]:
        """Return first tagged object for the color (simulating 'nearest')."""
        objects = self.find_tagged_objects(None, color)
        return objects[0] if objects else None

    def find_nearest_npc(self, include_in_combat: bool = False) -> Optional["RuneLiteObject"]:
        """Return configured nearest NPC."""
        return self.nearest_npc

    # ===== Safety Methods =====

    def are_friends_nearby(self) -> bool:
        """Return configured friends nearby state."""
        return self.friends_nearby

    # ===== UI State Methods =====

    def get_mouseover_text(self) -> str:
        """Return configured mouseover text."""
        return self.mouseover_text

    def has_hp_bar(self) -> bool:
        """Return configured HP bar visibility."""
        return self.hp_bar_visible

    # ===== Test Helper Methods =====

    def set_inventory_full(self) -> "MockGameState":
        """Set inventory to full (28 items). Returns self for chaining."""
        self.inventory_count = 28
        return self

    def set_inventory_empty(self) -> "MockGameState":
        """Set inventory to empty (0 items). Returns self for chaining."""
        self.inventory_count = 0
        return self

    def set_action(self, action: str) -> "MockGameState":
        """Set current action and mark player as not idle. Returns self for chaining."""
        self.current_action = action
        self.is_idle = False
        return self

    def set_idle(self) -> "MockGameState":
        """Set player to idle. Returns self for chaining."""
        self.is_idle = True
        self.current_action = ""
        return self

    def add_tagged_object(self, color: str, obj: "RuneLiteObject") -> "MockGameState":
        """Add a tagged object for a color. Returns self for chaining."""
        color_upper = color.upper()
        if color_upper not in self.tagged_objects:
            self.tagged_objects[color_upper] = []
        self.tagged_objects[color_upper].append(obj)
        return self

    def set_low_hp(self, hp: int = 30) -> "MockGameState":
        """Set HP to a low value. Returns self for chaining."""
        self.hp = hp
        return self

    def set_friends_nearby(self, nearby: bool = True) -> "MockGameState":
        """Set friends nearby state. Returns self for chaining."""
        self.friends_nearby = nearby
        return self
