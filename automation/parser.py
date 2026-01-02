# automation/parser.py
"""
Parse automation commands into explicit steps.
"""

def parse_automation(text: str) -> list[str]:
    """
    Split a command like:
    'Open Chrome and open https://youtube.com'
    into explicit steps.
    
    Args:
        text: User input command
        
    Returns:
        List of parsed steps. Empty list if only one action.
    """
    separators = [" and ", ", then ", " then "]
    
    for sep in separators:
        if sep in text:
            steps = [t.strip() for t in text.split(sep) if t.strip()]
            # Only return as automation if multiple steps
            if len(steps) > 1:
                return steps
    
    # Single step or no separators found - NOT automation
    return []
