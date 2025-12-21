"""Unit tests for MockGameState."""

import pytest

from model.game_state.mock import MockGameState


class TestMockGameStateInventory:
    """Tests for inventory-related MockGameState methods."""

    def test_default_inventory_empty(self):
        """Default inventory should be empty."""
        state = MockGameState()

        assert state.is_inventory_full() is False
        assert state.count_inventory_items() == 0

    def test_inventory_full_at_28(self):
        """Inventory should be full at 28 items."""
        state = MockGameState(inventory_count=28)

        assert state.is_inventory_full() is True
        assert state.count_inventory_items() == 28

    def test_inventory_not_full_at_27(self):
        """Inventory should not be full at 27 items."""
        state = MockGameState(inventory_count=27)

        assert state.is_inventory_full() is False

    def test_set_inventory_full_helper(self):
        """Test set_inventory_full helper method."""
        state = MockGameState().set_inventory_full()

        assert state.is_inventory_full() is True
        assert state.count_inventory_items() == 28

    def test_set_inventory_empty_helper(self):
        """Test set_inventory_empty helper method."""
        state = MockGameState(inventory_count=28).set_inventory_empty()

        assert state.is_inventory_full() is False
        assert state.count_inventory_items() == 0

    def test_slot_empty_default(self):
        """Slots beyond inventory count should be empty."""
        state = MockGameState(inventory_count=5)

        assert state.is_slot_empty(0) is False  # Within count
        assert state.is_slot_empty(4) is False  # Within count
        assert state.is_slot_empty(5) is True  # Beyond count
        assert state.is_slot_empty(27) is True  # Beyond count

    def test_slot_empty_explicit(self):
        """Test explicitly set slot states."""
        state = MockGameState(slot_states={0: True, 5: False})

        assert state.is_slot_empty(0) is True  # Explicitly empty
        assert state.is_slot_empty(5) is False  # Explicitly filled


class TestMockGameStatePlayerStatus:
    """Tests for player status MockGameState methods."""

    def test_default_player_idle(self):
        """Default player should be idle."""
        state = MockGameState()

        assert state.is_player_idle() is True

    def test_player_doing_action(self):
        """Test action detection."""
        state = MockGameState(current_action="Mining", is_idle=False)

        assert state.is_player_idle() is False
        assert state.is_player_doing_action("Mining") is True
        assert state.is_player_doing_action("Woodcutting") is False

    def test_action_case_insensitive(self):
        """Action detection should be case insensitive."""
        state = MockGameState(current_action="Mining")

        assert state.is_player_doing_action("mining") is True
        assert state.is_player_doing_action("MINING") is True

    def test_set_action_helper(self):
        """Test set_action helper method."""
        state = MockGameState().set_action("Fishing")

        assert state.is_player_idle() is False
        assert state.is_player_doing_action("Fishing") is True

    def test_set_idle_helper(self):
        """Test set_idle helper method."""
        state = MockGameState(current_action="Mining", is_idle=False).set_idle()

        assert state.is_player_idle() is True
        assert state.current_action == ""

    def test_combat_state(self):
        """Test combat state."""
        state = MockGameState(in_combat=True)

        assert state.is_in_combat() is True

    def test_hp_and_prayer(self):
        """Test HP and prayer values."""
        state = MockGameState(hp=50, prayer=25)

        assert state.get_hp() == 50
        assert state.get_prayer() == 25

    def test_set_low_hp_helper(self):
        """Test set_low_hp helper method."""
        state = MockGameState().set_low_hp(25)

        assert state.get_hp() == 25


class TestMockGameStateSafety:
    """Tests for safety-related MockGameState methods."""

    def test_default_no_friends(self):
        """Default should have no friends nearby."""
        state = MockGameState()

        assert state.are_friends_nearby() is False

    def test_friends_nearby(self):
        """Test friends nearby detection."""
        state = MockGameState(friends_nearby=True)

        assert state.are_friends_nearby() is True

    def test_set_friends_nearby_helper(self):
        """Test set_friends_nearby helper method."""
        state = MockGameState().set_friends_nearby()

        assert state.are_friends_nearby() is True


class TestMockGameStateObjectDetection:
    """Tests for object detection MockGameState methods."""

    def test_no_tagged_objects_default(self):
        """Default should have no tagged objects."""
        state = MockGameState()

        # Mock a color object
        class MockColor:
            name = "PINK"

        assert state.find_tagged_objects(None, MockColor()) == []
        assert state.find_nearest_tag(MockColor()) is None

    def test_find_tagged_objects(self):
        """Test finding tagged objects by color."""
        mock_obj = object()  # Simple mock object
        state = MockGameState(tagged_objects={"PINK": [mock_obj]})

        class MockColor:
            name = "PINK"

        objects = state.find_tagged_objects(None, MockColor())
        assert len(objects) == 1
        assert objects[0] is mock_obj

    def test_find_nearest_tag(self):
        """Test finding nearest tag (returns first object)."""
        mock_obj = object()
        state = MockGameState(tagged_objects={"CYAN": [mock_obj]})

        class MockColor:
            name = "CYAN"

        nearest = state.find_nearest_tag(MockColor())
        assert nearest is mock_obj

    def test_add_tagged_object_helper(self):
        """Test add_tagged_object helper method."""
        mock_obj = object()
        state = MockGameState().add_tagged_object("GREEN", mock_obj)

        class MockColor:
            name = "GREEN"

        objects = state.find_tagged_objects(None, MockColor())
        assert mock_obj in objects


class TestMockGameStateChaining:
    """Tests for method chaining."""

    def test_helper_methods_return_self(self):
        """Helper methods should return self for chaining."""
        state = (
            MockGameState()
            .set_inventory_full()
            .set_action("Mining")
            .set_low_hp(50)
            .set_friends_nearby()
        )

        assert state.is_inventory_full() is True
        assert state.is_player_doing_action("Mining") is True
        assert state.get_hp() == 50
        assert state.are_friends_nearby() is True
