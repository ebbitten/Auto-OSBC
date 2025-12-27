"""
Machine-specific configuration management for Auto-OSBC.
Handles loading and accessing machine profiles for multi-machine support.
"""
import json
import os
import socket
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class MachineConfig:
    """
    Manages machine-specific configurations for different systems.
    
    Loads configuration from JSON files in the machine_profiles directory,
    with automatic machine detection and environment variable override support.
    """
    
    _instance = None
    _profile: Dict[str, Any] = None
    _profile_name: str = None
    
    def __new__(cls):
        """Singleton pattern to ensure single config instance."""
        if cls._instance is None:
            cls._instance = super(MachineConfig, cls).__new__(cls)
            cls._instance._load_profile()
        return cls._instance
    
    def _load_profile(self) -> None:
        """Load the appropriate machine profile."""
        # Determine profile name
        profile_name = self._get_profile_name()
        
        # Get profiles directory
        profiles_dir = Path(__file__).parent.parent.parent / "machine_profiles"
        profile_path = profiles_dir / f"{profile_name}.json"
        
        # Fall back to default if specific profile doesn't exist
        if not profile_path.exists():
            print(f"Machine profile '{profile_name}' not found, using default")
            profile_path = profiles_dir / "default.json"
            profile_name = "default"
        
        # Load the profile
        try:
            with open(profile_path, 'r') as f:
                self._profile = json.load(f)
                self._profile_name = profile_name
                print(f"Loaded machine profile: {profile_name}")
        except Exception as e:
            print(f"Error loading machine profile: {e}")
            # Create minimal default profile
            self._profile = self._create_minimal_profile()
            self._profile_name = "minimal"
    
    def _get_profile_name(self) -> str:
        """
        Determine which profile to use.
        
        Priority:
        1. OSBC_MACHINE_PROFILE environment variable
        2. Machine hostname mapping
        3. Default profile
        """
        # Check environment variable first
        if env_profile := os.getenv("OSBC_MACHINE_PROFILE"):
            return env_profile
        
        # Check hostname mapping
        hostname = socket.gethostname().lower()
        
        # Add your machine hostname mappings here
        hostname_map = {
            # Example: "adams-desktop": "desktop",
            # Example: "adams-laptop": "laptop",
        }
        
        if hostname in hostname_map:
            return hostname_map[hostname]
        
        # Default profile
        return "default"
    
    def _create_minimal_profile(self) -> Dict[str, Any]:
        """Create a minimal default profile with hardcoded values."""
        return {
            "machine_name": "minimal",
            "display": {
                "primary_resolution": [1920, 1080],
                "dpi_scale": 1.0,
                "runelite_window": {
                    "default_size": [773, 534],
                    "padding": {"top": 26, "left": 0}
                }
            },
            "app": {
                "width": 680,
                "height": 480
            },
            "options_ui": {
                "width": 500,
                "height": 400
            }
        }
    
    @property
    def profile_name(self) -> str:
        """Get the current profile name."""
        return self._profile_name
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a value from the profile using dot notation.
        
        Args:
            *keys: Path to the value (e.g., "display", "runelite_window", "padding")
            default: Default value if key not found
            
        Returns:
            The value at the specified path, or default if not found
        """
        value = self._profile
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_window_padding(self) -> Tuple[int, int]:
        """Get window padding values (top, left)."""
        padding = self.get("display", "runelite_window", "padding", default={})
        return padding.get("top", 26), padding.get("left", 0)
    
    def get_window_default_size(self) -> Tuple[int, int]:
        """Get default window size (width, height)."""
        size = self.get("display", "runelite_window", "default_size", default=[773, 534])
        return tuple(size)
    
    def get_app_dimensions(self) -> Tuple[int, int]:
        """Get OSBC app window dimensions."""
        width = self.get("app", "width", default=680)
        height = self.get("app", "height", default=480)
        return width, height
    
    def get_options_ui_dimensions(self) -> Tuple[int, int]:
        """Get options UI dimensions."""
        width = self.get("options_ui", "width", default=500)
        height = self.get("options_ui", "height", default=400)
        return width, height
    
    def get_ui_coordinates(self, mode: str, element: str) -> Optional[Dict[str, int]]:
        """
        Get UI element coordinates for fixed or resizable mode.
        
        Args:
            mode: "fixed_mode" or "resizable_mode"
            element: Element name (e.g., "minimap", "hp_orb_text")
            
        Returns:
            Dictionary with coordinates or None if not found
        """
        return self.get("ui_coordinates", mode, element)
    
    def get_inventory_config(self) -> Dict[str, int]:
        """Get inventory slot configuration."""
        return self.get("ui_coordinates", "inventory", default={
            "slot_width": 31,
            "slot_height": 31,
            "gap_x": 6,
            "gap_y": 4,
            "start_x": 40,
            "start_y": 44
        })
    
    def get_prayers_config(self) -> Dict[str, int]:
        """Get prayers grid configuration."""
        return self.get("ui_coordinates", "prayers", default={
            "prayer_width": 33,
            "prayer_height": 33,
            "gap_x": 3,
            "gap_y": 3,
            "start_x": 30,
            "start_y": 46
        })
    
    def get_spellbook_config(self) -> Dict[str, int]:
        """Get spellbook configuration."""
        return self.get("ui_coordinates", "spellbook", default={
            "spell_width": 23,
            "spell_height": 23,
            "gap_x": 4,
            "gap_y": 2,
            "start_x": 30,
            "start_y": 37
        })
    
    def get_chat_tabs_config(self) -> Dict[str, Any]:
        """Get chat tabs configuration."""
        return self.get("ui_coordinates", "chat_tabs", default={
            "fixed_mode": {
                "positions": [
                    [14, 303, 52, 19],  # [x, y, width, height]
                    [72, 303, 52, 19],
                    [129, 303, 52, 19],
                    [188, 303, 52, 19],
                    [246, 303, 52, 19],
                    [303, 303, 52, 19],
                    [361, 303, 52, 28],
                    [419, 303, 52, 28],
                    [478, 303, 26, 28]
                ]
            }
        })
    
    def get_control_panel_tabs_config(self) -> Dict[str, Any]:
        """Get control panel tabs configuration."""
        return self.get("ui_coordinates", "control_panel_tabs", default={
            "rows": [
                {"y": 298, "height": 26, "positions": [10, 52, 94, 136, 178, 219, 261]},
                {"y": 326, "height": 36, "positions": [10, 52, 94, 136, 178, 219, 261]}
            ],
            "tab_width": 30,
            "combat_tab": {"width": 38, "x": 5}
        })
    
    def reload(self) -> None:
        """Reload the configuration from disk."""
        self._load_profile()


# Global instance getter
def get_machine_config() -> MachineConfig:
    """Get the global MachineConfig instance."""
    return MachineConfig()