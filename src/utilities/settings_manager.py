import json
from pathlib import Path


class SettingsManager:
    def __init__(self):
        # Create settings directory if it doesn't exist
        self.settings_dir = Path.home() / ".osbc" / "bot_settings"
        self.settings_dir.mkdir(parents=True, exist_ok=True)

    def save_bot_settings(self, bot_name: str, settings: dict):
        """Save settings for a specific bot"""
        settings_file = self.settings_dir / f"{bot_name}.json"
        try:
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_bot_settings(self, bot_name: str) -> dict:
        """Load settings for a specific bot"""
        settings_file = self.settings_dir / f"{bot_name}.json"
        try:
            if settings_file.exists():
                with open(settings_file) as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {}
