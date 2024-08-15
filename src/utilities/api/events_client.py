from typing import Dict, Any, List, Tuple, Union
from src.utilities.api.events_server import EventsAPIHandler

class EventsAPIClient:
    @staticmethod
    def get_data(endpoint: str) -> Dict[str, Any]:
        return EventsAPIHandler.cache.get(endpoint, {})

    @classmethod
    def get_player_status(cls) -> Dict[str, Any]:
        return cls.get_data("player_status")

    @classmethod
    def get_inventory_items(cls) -> Dict[str, Any]:
        return cls.get_data("inventory_items")

    @classmethod
    def get_hitpoints(cls) -> Tuple[int, int]:
        status = cls.get_player_status()
        return status.get('currentHealth', -1), status.get('maxHealth', -1)

    @classmethod
    def get_run_energy(cls) -> int:
        status = cls.get_player_status()
        return status.get('currentRun', -1) // 100  # Convert from 0-10000 to 0-100

    @classmethod
    def get_player_position(cls) -> Tuple[int, int, int]:
        status = cls.get_player_status()
        world_point = status.get('worldPoint', {})
        return (
            world_point.get('x', -1),
            world_point.get('y', -1),
            world_point.get('plane', -1)
        )

    @classmethod
    def get_is_player_idle(cls) -> bool:
        # We can consider the player idle if their position hasn't changed
        # This would require storing and comparing the last known position
        # For now, we'll return False as a placeholder
        return False

    @classmethod
    def get_combat_level(cls) -> int:
        status = cls.get_player_status()
        return status.get('combatLevel', -1)

    @classmethod
    def get_total_weight(cls) -> int:
        status = cls.get_player_status()
        return status.get('currentWeight', -1)

    @classmethod
    def get_prayer_points(cls) -> Tuple[int, int]:
        status = cls.get_player_status()
        return status.get('currentPrayer', -1), status.get('maxPrayer', -1)

    @classmethod
    def get_world(cls) -> int:
        status = cls.get_player_status()
        return status.get('world', -1)

    @classmethod
    def get_account_type(cls) -> str:
        status = cls.get_player_status()
        return status.get('accountType', '')

    @classmethod
    def get_username(cls) -> str:
        status = cls.get_player_status()
        return status.get('userName', '')

    @classmethod
    def get_is_inv_full(cls) -> bool:
        inventory = cls.get_inventory_items().get('inventory', [])
        return len([item for item in inventory if item['id'] != 0]) == 28

    @classmethod
    def get_inv_item_indices(cls, item_id: Union[List[int], int]) -> list:
        inventory = cls.get_inventory_items().get('inventory', [])
        if isinstance(item_id, int):
            return [i for i, item in enumerate(inventory) if item['id'] == item_id]
        elif isinstance(item_id, list):
            return [i for i, item in enumerate(inventory) if item['id'] in item_id]

    @classmethod
    def get_inv_item_stack_amount(cls, item_id: Union[int, List[int]]) -> int:
        inventory = cls.get_inventory_items().get('inventory', [])
        if isinstance(item_id, int):
            item_id = [item_id]
        return sum(item['quantity'] for item in inventory if item['id'] in item_id)

    @classmethod
    def get_inv(cls) -> List[Dict[str, Any]]:
        inventory = cls.get_inventory_items().get('inventory', [])
        return [{'index': i, 'id': item['id'], 'quantity': item['quantity']} 
                for i, item in enumerate(inventory) if item['id'] != 0]

    @classmethod
    def get_first_occurrence(cls, item_id: Union[List[int], int]) -> Union[int, List[int]]:
        inventory = cls.get_inventory_items().get('inventory', [])
        if isinstance(item_id, int):
            return next((i for i, item in enumerate(inventory) if item['id'] == item_id), -1)
        elif isinstance(item_id, list):
            return [next((i for i, item in enumerate(inventory) if item['id'] == id), -1) for id in item_id]

    @classmethod
    def get_total_inv_value(cls) -> int:
        inventory_data = cls.get_inventory_items()
        return inventory_data.get('gePrice', 0)

    # The following methods are not directly implementable from the current data
    # but are kept as placeholders in case the data becomes available in the future

    @classmethod
    def get_animation(cls) -> int:
        return -1

    @classmethod
    def get_animation_id(cls) -> int:
        return -1

    @classmethod
    def get_skill_level(cls, skill: str) -> int:
        return -1

    @classmethod
    def get_skill_xp(cls, skill: str) -> int:
        return -1

    @classmethod
    def get_skill_xp_gained(cls, skill: str) -> int:
        return -1

    @classmethod
    def wait_til_gained_xp(cls, skill: str, timeout: int = 10) -> int:
        # This method needs to be implemented based on your specific needs
        pass

    @classmethod
    def get_game_tick(cls) -> int:
        return -1

    @classmethod
    def get_latest_chat_message(cls) -> str:
        return ""

    @classmethod
    def get_player_region_data(cls) -> Tuple[int, int, int]:
        return (-1, -1, -1)

    @classmethod
    def get_camera_position(cls) -> Union[dict, None]:
        return None

    @classmethod
    def get_mouse_position(cls) -> Tuple[int, int]:
        return (-1, -1)

    @classmethod
    def get_interaction_code(cls) -> str:
        return ""

    @classmethod
    def get_is_in_combat(cls) -> Union[bool, None]:
        return None

    @classmethod
    def get_npc_hitpoints(cls) -> Union[int, None]:
        return None

    @classmethod
    def get_is_item_equipped(cls, item_id: Union[int, List[int]]) -> bool:
        return False

    @classmethod
    def get_equipped_item_quantity(cls, item_id: int) -> int:
        return 0