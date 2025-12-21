"""Unit tests for interaction action primitives.

These tests verify that actions return correct intents without performing side effects.
The Executor is responsible for actually executing the intents.
"""

import pytest

from model.actions.interaction import (
    find_and_interact,
    find_all_tagged,
    click_object,
    find_nearest_npc,
    interact_with_nearest_npc,
    click_at_point,
    hover_object,
)
from model.actions.base import ActionResult
from model.actions.intents import ClickIntent, MoveIntent


class MockPoint:
    """Mock Point for testing."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class MockRuneLiteObject:
    """Mock RuneLiteObject for testing."""
    def __init__(self, center_x: int, center_y: int):
        self._center = (center_x, center_y)

    def random_point(self) -> MockPoint:
        return MockPoint(self._center[0], self._center[1])

    def center(self) -> MockPoint:
        """Return the center point of the object."""
        return MockPoint(self._center[0], self._center[1])

    @staticmethod
    def distance_from_rect_center(obj):
        """Distance calculation for sorting."""
        # Simple distance from origin for testing
        return (obj._center[0] ** 2 + obj._center[1] ** 2) ** 0.5


class MockColor:
    """Mock color for testing."""
    def __init__(self, name: str):
        self.name = name


class MockRectangle:
    """Mock Rectangle for testing."""
    def __init__(self):
        self.left = 0
        self.top = 0
        self.width = 100
        self.height = 100


class MockWindow:
    """Mock Window for testing."""
    def __init__(self):
        self.game_view = MockRectangle()


class MockBot:
    """Mock bot for testing interaction functions."""

    def __init__(self, tagged_objects=None, nearest_npc=None):
        self.win = MockWindow()
        self._tagged_objects = tagged_objects or []
        self._nearest_npc = nearest_npc

    def get_all_tagged_in_rect(self, rect, color):
        return self._tagged_objects

    def get_nearest_tagged_NPC(self, include_in_combat=False):
        return self._nearest_npc


class TestFindAndInteract:
    """Tests for find_and_interact function."""

    def test_returns_fail_when_no_objects(self):
        """Should fail when no objects found."""
        bot = MockBot(tagged_objects=[])
        color = MockColor("PINK")

        result = find_and_interact(bot, color)

        assert result.failed is True
        assert result.result == ActionResult.FAILED

    def test_returns_click_intent_for_nearest_object(self):
        """Should return ClickIntent for the nearest object."""
        # Create objects at different distances
        far_obj = MockRuneLiteObject(100, 100)
        near_obj = MockRuneLiteObject(10, 10)
        bot = MockBot(tagged_objects=[far_obj, near_obj])
        color = MockColor("PINK")

        result = find_and_interact(bot, color)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, ClickIntent)
        # Should target the nearer object (10, 10)
        assert intent.point == (10, 10)

    def test_returns_object_count(self):
        """Should return count of found objects."""
        objs = [MockRuneLiteObject(10, 10), MockRuneLiteObject(20, 20)]
        bot = MockBot(tagged_objects=objs)
        color = MockColor("PINK")

        result = find_and_interact(bot, color)

        assert result.data["object_count"] == 2

    def test_uses_custom_mouse_speed(self):
        """Should use provided mouse speed in intent."""
        bot = MockBot(tagged_objects=[MockRuneLiteObject(50, 50)])
        color = MockColor("PINK")

        result = find_and_interact(bot, color, mouse_speed="fastest")

        intent = result.data["intent"]
        assert intent.speed == "fastest"

    def test_right_click_option(self):
        """Should set right_click in intent when specified."""
        bot = MockBot(tagged_objects=[MockRuneLiteObject(50, 50)])
        color = MockColor("PINK")

        result = find_and_interact(bot, color, right_click=True)

        intent = result.data["intent"]
        assert intent.right_click is True

    def test_uses_custom_search_rect(self):
        """Should use provided search rectangle."""
        bot = MockBot(tagged_objects=[MockRuneLiteObject(50, 50)])
        color = MockColor("PINK")
        custom_rect = MockRectangle()

        # Mock to verify the rect is passed
        called_rect = None

        def capture_rect(rect, color):
            nonlocal called_rect
            called_rect = rect
            return bot._tagged_objects

        bot.get_all_tagged_in_rect = capture_rect

        find_and_interact(bot, color, search_rect=custom_rect)

        assert called_rect is custom_rect


class TestFindAllTagged:
    """Tests for find_all_tagged function."""

    def test_returns_fail_when_no_objects(self):
        """Should fail when no objects found."""
        bot = MockBot(tagged_objects=[])
        color = MockColor("CYAN")

        result = find_all_tagged(bot, color)

        assert result.failed is True

    def test_returns_sorted_objects(self):
        """Should return objects sorted by distance."""
        far_obj = MockRuneLiteObject(100, 100)
        near_obj = MockRuneLiteObject(10, 10)
        bot = MockBot(tagged_objects=[far_obj, near_obj])
        color = MockColor("CYAN")

        result = find_all_tagged(bot, color)

        assert result.success is True
        assert result.data["count"] == 2
        # First object should be nearest
        assert result.data["objects"][0]._center == (10, 10)

    def test_returns_object_list(self):
        """Should return list of objects in data."""
        objs = [MockRuneLiteObject(10, 10)]
        bot = MockBot(tagged_objects=objs)
        color = MockColor("CYAN")

        result = find_all_tagged(bot, color)

        assert "objects" in result.data
        assert len(result.data["objects"]) == 1


class TestClickObject:
    """Tests for click_object function."""

    def test_returns_click_intent(self):
        """Should return ClickIntent for the object."""
        bot = MockBot()
        obj = MockRuneLiteObject(50, 50)

        result = click_object(bot, obj)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, ClickIntent)
        assert intent.point == (50, 50)

    def test_right_click_intent(self):
        """Should set right_click in intent when specified."""
        bot = MockBot()
        obj = MockRuneLiteObject(50, 50)

        result = click_object(bot, obj, right_click=True)

        intent = result.data["intent"]
        assert intent.right_click is True
        assert result.data["right_click"] is True


class TestFindNearestNpc:
    """Tests for find_nearest_npc function."""

    def test_returns_fail_when_no_npc(self):
        """Should fail when no NPC found."""
        bot = MockBot(nearest_npc=None)

        result = find_nearest_npc(bot)

        assert result.failed is True

    def test_returns_npc_when_found(self):
        """Should return NPC when found."""
        npc = MockRuneLiteObject(30, 30)
        bot = MockBot(nearest_npc=npc)

        result = find_nearest_npc(bot)

        assert result.success is True
        assert result.data["npc"] is npc


class TestInteractWithNearestNpc:
    """Tests for interact_with_nearest_npc function."""

    def test_fails_when_no_npc(self):
        """Should fail when no NPC found."""
        bot = MockBot(nearest_npc=None)

        result = interact_with_nearest_npc(bot)

        assert result.failed is True

    def test_returns_click_intent_for_npc(self):
        """Should return ClickIntent for NPC when found."""
        npc = MockRuneLiteObject(30, 30)
        bot = MockBot(nearest_npc=npc)

        result = interact_with_nearest_npc(bot)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, ClickIntent)
        assert intent.point == (30, 30)


class TestClickAtPoint:
    """Tests for click_at_point function."""

    def test_returns_click_intent_at_coordinates(self):
        """Should return ClickIntent at specified coordinates."""
        bot = MockBot()

        result = click_at_point(bot, 100, 200)

        assert result.success is True
        intent = result.data["intent"]
        assert isinstance(intent, ClickIntent)
        assert intent.point == (100, 200)

    def test_right_click_intent(self):
        """Should set right_click in intent when specified."""
        bot = MockBot()

        result = click_at_point(bot, 100, 200, right_click=True)

        intent = result.data["intent"]
        assert intent.right_click is True


class TestHoverObject:
    """Tests for hover_object function."""

    def test_returns_move_intent(self):
        """Should return MoveIntent without click."""
        bot = MockBot()
        obj = MockRuneLiteObject(75, 75)

        result = hover_object(bot, obj)

        assert result.success is True
        assert "intent" in result.data
        intent = result.data["intent"]
        assert isinstance(intent, MoveIntent)
        assert intent.point == (75, 75)
