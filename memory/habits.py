# memory/habits.py
"""
Habit tracking (passive observation only).
Records repeated user behaviors without triggering actions.
"""

from utils.logger import setup_logger

logger = setup_logger("memory.habits")


class HabitTracker:
    """
    Tracks user behaviors passively.
    Records frequencies of user actions, not decisions.
    
    This is observational only — no behavior changes, no automation.
    """
    
    def __init__(self):
        """Initialize habit tracker with empty counts."""
        self.counts = {}
    
    def record(self, event: str):
        """
        Record a habit event.
        
        Safe events to record:
        - action.open_app.chrome
        - action.open_app.firefox
        - action.open_folder.downloads
        - search.web
        - mode.factual
        - mode.opinion
        - mode.analysis
        
        DO NOT record:
        - raw text
        - NSFW content
        - file names
        - URLs
        - personal data
        
        Args:
            event: Event string (e.g., "action.open_app.chrome")
        """
        self.counts[event] = self.counts.get(event, 0) + 1
        logger.info(
            "habit_recorded",
            extra={"event": event, "count": self.counts[event]},
        )
    
    def most_common(self, prefix: str = None):
        """
        Get the most common event (optionally filtered by prefix).
        
        Args:
            prefix: Optional prefix to filter events (e.g., "action.open_app")
            
        Returns:
            Most common event string, or None if no matches
        """
        if prefix:
            filtered = {
                k: v for k, v in self.counts.items()
                if k.startswith(prefix)
            }
        else:
            filtered = self.counts
        
        if not filtered:
            return None
        
        most_common_event = max(filtered, key=filtered.get)
        logger.info(
            "habit_most_common_read",
            extra={"prefix": prefix, "event": most_common_event, "count": filtered[most_common_event]},
        )
        return most_common_event
    
    def get_frequency(self, event: str) -> int:
        """
        Get the frequency of a specific event.
        
        Args:
            event: Event string
            
        Returns:
            Number of times the event occurred
        """
        count = self.counts.get(event, 0)
        if count > 0:
            logger.info(
                "habit_frequency_read",
                extra={"event": event, "count": count},
            )
        return count
    
    def get_all(self) -> dict:
        """Get all recorded habits."""
        return self.counts.copy()
    
    def clear(self):
        """Clear all habit records."""
        self.counts = {}
        logger.info("habits_cleared")
