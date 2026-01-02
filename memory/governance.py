# memory/governance.py
"""
Memory governance handler for user control.
Users can inspect, delete, and opt-out of memory.
"""

from utils.logger import setup_logger

logger = setup_logger("memory.governance")


class MemoryGovernanceHandler:
    """
    Handles memory governance commands.
    Users have complete control over their memory.
    """
    
    def __init__(self, memory_manager, config):
        """
        Args:
            memory_manager: MemoryManager instance
            config: Configuration dict
        """
        self.memory = memory_manager
        self.config = config
    
    def run(self, user_input: str) -> str:
        """
        Process memory governance commands.
        
        Args:
            user_input: User's input text
            
        Returns:
            Response string
        """
        text = user_input.lower().strip()
        
        # ========== INSPECT MEMORY ==========
        
        if "show" in text or "remember" in text:
            summary = self.memory.summary()
            
            logger.info(
                "memory_inspected",
                extra={"action": "user_requested"},
            )
            
            response = "Here's what I remember about you:\n\n"
            
            if summary["preferences"] != "None":
                response += "📋 **Preferences:**\n"
                for key, value in summary["preferences"].items():
                    response += f"  • {key}: {value}\n"
                response += "\n"
            
            if summary["habits"] != "None":
                response += "📊 **Habits:**\n"
                for event, count in summary["habits"].items():
                    response += f"  • {event}: {count}x\n"
                response += "\n"
            
            if summary["conversation_history"] != "None":
                response += "💬 **Conversation Memory:**\n"
                response += f"  {summary['conversation_history']}\n\n"
            
            response += "🔒 NSFW memory is isolated for your privacy.\n"
            response += "\nYou can clear any of this with: 'Clear memory', 'Forget my preferences', or 'Forget my habits'"
            
            return response
        
        # ========== CLEAR PREFERENCES ==========
        
        if "forget my preferences" in text:
            self.memory.clear_preferences()
            
            logger.info(
                "memory_governance_action",
                extra={"action": "clear_preferences", "triggered_by": "user"},
            )
            
            return "✓ Your preferences have been cleared. I'll treat each interaction fresh."
        
        # ========== CLEAR HABITS ==========
        
        if "forget my habits" in text:
            self.memory.clear_habits()
            
            logger.info(
                "memory_governance_action",
                extra={"action": "clear_habits", "triggered_by": "user"},
            )
            
            return "✓ Your habit history has been cleared. I won't remember patterns anymore."
        
        # ========== CLEAR ALL MEMORY ==========
        
        if "clear memory" in text or "clear all memory" in text:
            self.memory.clear_all()
            
            logger.warning(
                "memory_governance_action",
                extra={"action": "clear_all", "triggered_by": "user"},
            )
            
            return "✓ All memory has been cleared completely. I'm starting fresh."
        
        # ========== DISABLE MEMORY ==========
        
        if "disable memory" in text:
            self.config["memory"]["enabled"] = False
            
            logger.warning(
                "memory_governance_action",
                extra={"action": "disable_memory", "triggered_by": "user"},
            )
            
            return "⏸️ Memory has been disabled. I won't learn or remember anything from now on."
        
        # ========== ENABLE MEMORY ==========
        
        if "enable memory" in text:
            self.config["memory"]["enabled"] = True
            
            logger.info(
                "memory_governance_action",
                extra={"action": "enable_memory", "triggered_by": "user"},
            )
            
            return "▶️ Memory has been enabled. I'll start learning from this point forward."
        
        # ========== UNRECOGNIZED COMMAND ==========
        
        logger.warning(
            "memory_governance_unrecognized",
            extra={"input": user_input},
        )
        
        return (
            "I didn't understand that memory command.\n\n"
            "Try:\n"
            "  • 'What do you remember about me?' - Show all memory\n"
            "  • 'Forget my preferences' - Clear preferences only\n"
            "  • 'Forget my habits' - Clear habits only\n"
            "  • 'Clear memory' - Clear everything\n"
            "  • 'Disable memory' - Stop learning\n"
            "  • 'Enable memory' - Start learning again"
        )
