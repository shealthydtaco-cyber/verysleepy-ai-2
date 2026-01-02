# automation/__init__.py
"""
Automation module for executing multiple explicit actions in sequence.
"""

from automation.parser import parse_automation
from automation.runner import AutomationRunner

__all__ = ["parse_automation", "AutomationRunner"]
