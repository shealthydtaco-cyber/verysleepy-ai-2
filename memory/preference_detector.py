# memory/preference_detector.py
"""
Detect preference statements in user input.
"""

from utils.logger import setup_logger

logger = setup_logger("memory.preferences")


class PreferenceDetector:
    """
    Detects explicit preference statements and extracts preference key/value pairs.
    """
    
    # Preference patterns: (trigger phrase, preference_key, extraction_pattern)
    PREFERENCE_PATTERNS = [
        # Browser preferences
        ("prefer chrome", "preferred_browser", "chrome"),
        ("prefer firefox", "preferred_browser", "firefox"),
        ("prefer opera", "preferred_browser", "opera"),
        ("prefer edge", "preferred_browser", "edge"),
        ("always use chrome", "preferred_browser", "chrome"),
        ("always use firefox", "preferred_browser", "firefox"),
        ("always use opera", "preferred_browser", "opera"),
        ("always use edge", "preferred_browser", "edge"),
        
        # Voice preferences
        ("enable voice", "voice_enabled", "true"),
        ("disable voice", "voice_enabled", "false"),
        ("use voice", "voice_enabled", "true"),
        ("no voice", "voice_enabled", "false"),
        
        # Answer length preferences
        ("prefer short answers", "answer_length", "short"),
        ("prefer long answers", "answer_length", "long"),
        ("prefer detailed", "answer_length", "detailed"),
        ("keep it brief", "answer_length", "short"),
        
        # Folder preferences
        ("prefer downloads", "preferred_folder", "downloads"),
        ("use downloads", "preferred_folder", "downloads"),
        ("prefer documents", "preferred_folder", "documents"),
        ("use documents", "preferred_folder", "documents"),
    ]
    
    @staticmethod
    def detect(user_input: str) -> dict:
        """
        Detect if user input contains preference statement.
        
        Args:
            user_input: User's input text
            
        Returns:
            Dict with "preference_key" and "preference_value" if found, else empty dict
        """
        lower_input = user_input.lower().strip()
        
        for trigger, key, value in PreferenceDetector.PREFERENCE_PATTERNS:
            if trigger in lower_input:
                logger.info(
                    "preference_detected",
                    extra={"trigger": trigger, "key": key, "value": value},
                )
                return {
                    "preference_key": key,
                    "preference_value": value,
                    "trigger": trigger,
                }
        
        return {}
