# memory/preferences.py
"""
User preference storage and retrieval.
Preferences are explicit settings stored when user directly states them.
"""

import json
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger("memory.preferences")


class UserPreferences:
    """
    Simple key-value store for user preferences.
    """
    
    def __init__(self, storage_path: Path = None):
        """
        Args:
            storage_path: Path to preferences JSON file.
                         Defaults to memory/user_profile/preferences.json
        """
        if storage_path is None:
            storage_path = Path(__file__).parent / "user_profile" / "preferences.json"
        
        self.storage_path = storage_path
        self.data = self._load()
    
    def set(self, key: str, value: str):
        """
        Set a preference explicitly.
        
        Args:
            key: Preference key (e.g., "preferred_browser")
            value: Preference value (e.g., "chrome")
        """
        self.data[key] = value
        self._save()
        logger.info(
            "preference_set",
            extra={"key": key, "value": value},
        )
    
    def get(self, key: str, default=None):
        """
        Get a preference value.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        value = self.data.get(key, default)
        if value != default:
            logger.info(
                "preference_read",
                extra={"key": key, "value": value},
            )
        return value
    
    def get_all(self) -> dict:
        """Get all preferences."""
        return self.data.copy()
    
    def clear(self):
        """Clear all preferences."""
        self.data = {}
        self._save()
        logger.info("preferences_cleared")
    
    def remove(self, key: str):
        """Remove a specific preference."""
        if key in self.data:
            del self.data[key]
            self._save()
            logger.info("preference_removed", extra={"key": key})
    
    def _load(self) -> dict:
        """Load preferences from JSON file."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    logger.info("preferences_loaded", extra={"count": len(data)})
                    return data
        except Exception as e:
            logger.error("preferences_load_failed", extra={"error": str(e)})
        
        return {}
    
    def _save(self):
        """Save preferences to JSON file."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(self.data, f, indent=2)
            logger.info("preferences_saved", extra={"count": len(self.data)})
        except Exception as e:
            logger.error("preferences_save_failed", extra={"error": str(e)})
