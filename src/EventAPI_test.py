import time
import sys
import os

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.utilities.api.events_client import EventsAPIClient
from src.utilities.api.events_server import start_server_thread, EventsAPIHandler

def test_events_api_client():
    # Start the server thread
    server_thread = start_server_thread()

    # Wait for the server to start
    time.sleep(1)

    # Simulate some data in the cache
    EventsAPIHandler.cache = {
        "events": {
            "health": "50/99",
            "run energy": 75,
            "animation": 1500,
            "animation pose": 808,
            "game tick": 1234,
            "worldPoint": {"x": 3200, "y": 3200, "plane": 0, "regionX": 50, "regionY": 50, "regionID": 12850},
            "mouse": {"x": 500, "y": 300},
            "npc name": "Goblin",
            "npc health": 10,
            "latest msg": "Welcome to RuneScape!"
        },
        "inv": {
            "inventory": [
                {"id": 1355, "quantity": 1},  # Axe
                {"id": 1521, "quantity": 10},  # Oak logs
                {"id": 0, "quantity": 0},
                # ... (remaining inventory slots)
            ]
        },
        "stats": [
            {"stat": "Overall", "level": 1000, "xp": 13034431},
            {"stat": "Woodcutting", "level": 70, "xp": 737627, "xp gained": 1000},
            # ... (other skills)
        ],
        "equip": [
            {"id": 1355, "quantity": 1},  # Axe equipped
            # ... (other equipped items)
        ]
    }

    # Player Data
    print(f"Current HP: {EventsAPIClient.get_hitpoints()}")
    print(f"Run Energy: {EventsAPIClient.get_run_energy()}")
    print(f"Animation: {EventsAPIClient.get_animation()}")
    print(f"Animation ID: {EventsAPIClient.get_animation_id()}")
    print(f"Is player idle: {EventsAPIClient.get_is_player_idle()}")

    # World Data
    print(f"Game tick: {EventsAPIClient.get_game_tick()}")
    print(f"Player position: {EventsAPIClient.get_player_position()}")
    print(f"Player region data: {EventsAPIClient.get_player_region_data()}")
    print(f"Mouse position: {EventsAPIClient.get_mouse_position()}")
    print(f"Is in combat?: {EventsAPIClient.get_is_in_combat()}")
    print(f"NPC health: {EventsAPIClient.get_npc_hitpoints()}")

    # Inventory Data
    print(f"Inventory: {EventsAPIClient.get_inv()}")
    print(f"Is inventory full: {EventsAPIClient.get_is_inv_full()}")
    print(f"Is inventory empty: {EventsAPIClient.get_is_inv_empty()}")
    print(f"Are logs in inventory?: {EventsAPIClient.get_if_item_in_inv(1521)}")  # 1521 is the ID for oak logs
    print(f"Find amount of axes in inv: {EventsAPIClient.get_inv_item_stack_amount(1355)}")  # 1355 is the ID for axe
    print(f"Get position of all logs in inv: {EventsAPIClient.get_inv_item_indices(1521)}")
    print(f"Get position of first axe in inventory: {EventsAPIClient.get_first_occurrence(1355)}")

    # Skill Data
    print(f"Woodcutting Level: {EventsAPIClient.get_skill_level('Woodcutting')}")
    print(f"Woodcutting XP: {EventsAPIClient.get_skill_xp('Woodcutting')}")
    print(f"Woodcutting XP Gained: {EventsAPIClient.get_skill_xp_gained('Woodcutting')}")

    # Equipment Data
    print(f"Is axe equipped?: {EventsAPIClient.get_is_item_equipped(1355)}")
    print(f"How many axes equipped?: {EventsAPIClient.get_equipped_item_quantity(1355)}")

    # Chatbox Data
    print(f"Latest chat message: {EventsAPIClient.get_latest_chat_message()}")

    # Test wait_til_gained_xp (this will timeout after 10 seconds as we're not actually gaining XP)
    print("Testing wait_til_gained_xp (will timeout after 10 seconds):")
    result = EventsAPIClient.wait_til_gained_xp("Woodcutting", timeout=30)
    print(f"XP gained: {result}")

    print("\nAll tests completed.")

if __name__ == "__main__":
    test_events_api_client()