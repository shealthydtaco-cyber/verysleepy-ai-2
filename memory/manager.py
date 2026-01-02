from utils.config import load_config
from utils.logger import setup_logger
from memory.preferences import UserPreferences
from memory.preference_detector import PreferenceDetector
from memory.habits import HabitTracker

logger = setup_logger("memory.manager")
config = load_config()

class MemoryManager:
    def __init__(self, user_profile, conversation, nsfw, habits=None):
        self.user_profile = user_profile
        self.conversation = conversation
        self.nsfw = nsfw
        self.preferences = UserPreferences()
        self.habits = habits or HabitTracker()

    def read(self, control: dict) -> str:
        if not config.get("memory", {}).get("enabled", True):
            return ""

        if control.get("mode") == "NSFW_OPEN_ANALYTICAL":
            return self.nsfw.read()

        if control.get("memory_read"):
            return self.user_profile.read() + "\n" + self.conversation.read()

        return ""

    def write(self, control: dict, content: str, user_input: str = ""):
        if not config.get("memory", {}).get("write_enabled", True):
            return
        
        # Check for preference statements first
        if user_input:
            preference = PreferenceDetector.detect(user_input)
            if preference:
                self.preferences.set(
                    preference["preference_key"],
                    preference["preference_value"],
                )
                logger.info(
                    "preference_stored_from_input",
                    extra={"key": preference["preference_key"]},
                )
                return

        if control.get("mode") == "NSFW_OPEN_ANALYTICAL":
            self.nsfw.write(content)
            return

        if control.get("memory_write"):
            self.user_profile.write(content)
    
    def get_preference(self, key: str, default=None):
        """Get a user preference."""
        return self.preferences.get(key, default)
    
    def get_all_preferences(self) -> dict:
        """Get all preferences for inspection."""
        return self.preferences.get_all()    
    # ========== GOVERNANCE API ==========
    
    def summary(self) -> dict:
        """
        Get a summary of all memory.
        Transparent and user-readable.
        
        Returns:
            Dict with preferences, habits, conversation history
        """
        preferences = self.preferences.get_all()
        habits = self.habits.get_all()
        
        logger.info(
            "memory_summary_requested",
            extra={
                "preferences_count": len(preferences),
                "habits_count": len(habits),
            },
        )
        
        return {
            "preferences": preferences if preferences else "None",
            "habits": habits if habits else "None",
            "conversation_history": self.conversation.read() if self.conversation.read() else "None",
            "nsfw_memory": "[Isolated - not shown for privacy]",
        }
    
    def clear_all(self):
        """Clear all memory completely."""
        self.user_profile.clear()
        self.conversation.clear()
        self.nsfw.clear()
        self.preferences.clear()
        self.habits.clear()
        
        logger.warning(
            "all_memory_cleared",
            extra={"action": "user_requested"},
        )
    
    def clear_preferences(self):
        """Clear user preferences only."""
        self.preferences.clear()
        
        logger.info(
            "preferences_cleared",
            extra={"action": "user_requested"},
        )
    
    def clear_habits(self):
        """Clear habit tracking only."""
        self.habits.clear()
        
        logger.info(
            "habits_cleared",
            extra={"action": "user_requested"},
        )
    
    def clear_conversation(self):
        """Clear conversation history only."""
        self.conversation.clear()
        
        logger.info(
            "conversation_cleared",
            extra={"action": "user_requested"},
        )