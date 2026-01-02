# suggestions/engine.py
"""
Suggestion engine for soft intelligence.
Enhances responses with preference and habit-based suggestions.
Does NOT modify control, execution, or routing.
"""

from utils.logger import setup_logger

logger = setup_logger("suggestions")


class SuggestionEngine:
    """
    Applies suggestions to responses based on preferences and habits.
    
    Core principle:
    - Suggestions may influence phrasing
    - Suggestions must NEVER change control, execution, or routing
    - Suggestions are text only
    """
    
    def __init__(self, preferences, habits):
        """
        Args:
            preferences: UserPreferences instance
            habits: HabitTracker instance
        """
        self.preferences = preferences
        self.habits = habits
    
    def apply(self, user_input: str, control: dict, response: str) -> str:
        """
        Apply suggestions to a response.
        
        Args:
            user_input: Original user input
            control: Control dict (unchanged)
            response: Generated response text
            
        Returns:
            Enhanced response with suggestions (or original if no suggestions)
        """
        suggestions = []
        
        # ========== PREFERENCE-BASED SUGGESTIONS ==========
        
        # Short answer preference
        if self.preferences.get("answer_length") == "short":
            if control.get("mode") in ["FACTUAL", "ANALYSIS", "OPINION"]:
                suggestions.append("💡 Keeping it brief as you prefer.")
        
        # Voice preference
        if self.preferences.get("voice_enabled") == "true":
            suggestions.append("🔊 I can read this aloud for you.")
        
        # Browser preference (for ACTION mode with browser)
        preferred_browser = self.preferences.get("preferred_browser")
        if preferred_browser and control.get("mode") == "ACTION":
            if "open" in user_input.lower() and ("browser" in user_input.lower() or "chrome" in user_input.lower() or "firefox" in user_input.lower()):
                suggestions.append(f"🌐 You usually prefer {preferred_browser.capitalize()}.")
        
        # Folder preference (for ACTION mode with folders)
        preferred_folder = self.preferences.get("preferred_folder")
        if preferred_folder and control.get("mode") == "ACTION":
            if "open" in user_input.lower() and "folder" in user_input.lower():
                suggestions.append(f"📁 You usually use {preferred_folder.capitalize()}.")
        
        # ========== HABIT-BASED SUGGESTIONS ==========
        
        # Most common browser
        common_browser = self.habits.most_common("action.open_app")
        if common_browser and control.get("mode") == "ACTION":
            if "open" in user_input.lower() and ("browser" in user_input.lower() or "application" in user_input.lower()):
                browser = common_browser.split(".")[-1]
                frequency = self.habits.get_frequency(common_browser)
                if frequency >= 2:  # Only suggest if used 2+ times
                    suggestions.append(f"📊 You usually open {browser.capitalize()} ({frequency}x).")
        
        # Most common folder
        common_folder = self.habits.most_common("action.open_folder")
        if common_folder and control.get("mode") == "ACTION":
            if "open" in user_input.lower() and ("folder" in user_input.lower() or "directory" in user_input.lower()):
                folder = common_folder.split(".")[-1]
                frequency = self.habits.get_frequency(common_folder)
                if frequency >= 2:
                    suggestions.append(f"📊 You often access {folder.capitalize()} ({frequency}x).")
        
        # ========== APPLY SUGGESTIONS ==========
        
        if not suggestions:
            return response
        
        suggestion_text = " ".join(suggestions)
        
        logger.info(
            "suggestion_applied",
            extra={
                "count": len(suggestions),
                "control_mode": control.get("mode"),
                "control_action": control.get("action"),
            },
        )
        
        return f"{suggestion_text}\n\n{response}"
    
    def apply_without_icons(self, user_input: str, control: dict, response: str) -> str:
        """
        Apply suggestions without emoji icons (for plain text output).
        
        Args:
            user_input: Original user input
            control: Control dict
            response: Generated response text
            
        Returns:
            Enhanced response with plain text suggestions
        """
        suggestions = []
        
        # Preference-based
        if self.preferences.get("answer_length") == "short":
            if control.get("mode") in ["FACTUAL", "ANALYSIS", "OPINION"]:
                suggestions.append("Keeping it brief as you prefer.")
        
        if self.preferences.get("voice_enabled") == "true":
            suggestions.append("I can read this aloud for you.")
        
        preferred_browser = self.preferences.get("preferred_browser")
        if preferred_browser and control.get("mode") == "ACTION":
            if "open" in user_input.lower() and ("browser" in user_input.lower() or "chrome" in user_input.lower()):
                suggestions.append(f"You usually prefer {preferred_browser.capitalize()}.")
        
        # Habit-based
        common_browser = self.habits.most_common("action.open_app")
        if common_browser and control.get("mode") == "ACTION":
            if "open" in user_input.lower() and "browser" in user_input.lower():
                browser = common_browser.split(".")[-1]
                frequency = self.habits.get_frequency(common_browser)
                if frequency >= 2:
                    suggestions.append(f"You usually open {browser.capitalize()} ({frequency}x).")
        
        if not suggestions:
            return response
        
        suggestion_text = " ".join(suggestions)
        
        logger.info(
            "suggestion_applied",
            extra={
                "count": len(suggestions),
                "control_mode": control.get("mode"),
            },
        )
        
        return f"{suggestion_text}\n\n{response}"
