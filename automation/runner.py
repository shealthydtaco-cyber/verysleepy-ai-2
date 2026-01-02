# automation/runner.py
"""
Execute automation steps sequentially.
"""

from utils.logger import setup_logger

logger = setup_logger("automation")


class AutomationRunner:
    """
    Execute multiple ACTION controls in sequence.
    Stops on first failure.
    """
    
    def __init__(self, action_manager):
        """
        Args:
            action_manager: ActionManager instance
        """
        self.action_manager = action_manager
    
    def run(self, controls: list[dict]) -> list[str]:
        """
        Execute controls sequentially.
        Combines app+url patterns into single actions.
        
        Args:
            controls: List of control dicts (all must be ACTION mode)
            
        Returns:
            List of results from each step
        """
        # Pre-process: combine app + URL patterns
        controls = self._combine_app_url_pattern(controls)
        
        results = []
        
        for i, control in enumerate(controls):
            step_num = i + 1
            action = control.get("action")
            target = control.get("target", "")
            
            logger.info(
                "automation_step",
                extra={
                    "step": step_num,
                    "total": len(controls),
                    "action": action,
                    "target": target,
                },
            )
            
            try:
                result = self.action_manager.run(control)
                results.append(result)
                logger.info(
                    "automation_step_success",
                    extra={"step": step_num, "action": action},
                )
            except Exception as e:
                logger.error(
                    "automation_step_failed",
                    extra={
                        "step": step_num,
                        "action": action,
                        "error": str(e),
                    },
                )
                raise
        
        return results
    
    def _combine_app_url_pattern(self, controls: list[dict]) -> list[dict]:
        """
        Combine consecutive patterns:
        1. app + url: [open_app(Opera), open_url(google.com)] → [open_app(Opera, url=google.com)]
        2. folder + file: [open_app(Downloads), open_file_path(mama.pdf)] → [open_file_path(Downloads/mama.pdf)]
        
        Args:
            controls: Original list of controls
            
        Returns:
            List with combined patterns
        """
        combined = []
        i = 0
        
        while i < len(controls):
            control = controls[i]
            
            # Pattern 1: app + URL
            if (
                i + 1 < len(controls)
                and control.get("action") == "open_app"
                and controls[i + 1].get("action") == "open_url"
            ):
                # Combine: open app with URL as target
                app_name = control.get("target", "")
                url = controls[i + 1].get("target", "")
                
                combined_control = control.copy()
                combined_control["target"] = f"{app_name} {url}"
                combined_control["_url_param"] = url
                combined_control["_app_name"] = app_name
                
                logger.info(
                    "automation_combine_app_url",
                    extra={"app": app_name, "url": url},
                )
                
                combined.append(combined_control)
                i += 2  # Skip both steps
            
            # Pattern 2: folder + file
            elif (
                i + 1 < len(controls)
                and control.get("action") == "open_app"
                and controls[i + 1].get("action") == "open_file_path"
            ):
                # Combine: open file from within folder
                folder_name = control.get("target", "")
                file_name = controls[i + 1].get("target", "")
                
                # Get the folder path
                from actions.allowlist import get_folder
                folder_path = get_folder(folder_name.lower())
                
                if folder_path:
                    # Create combined control for file in folder
                    combined_control = controls[i + 1].copy()  # Use file_path control
                    full_path = str(folder_path / file_name)
                    combined_control["target"] = full_path
                    combined_control["_folder_name"] = folder_name
                    combined_control["_file_name"] = file_name
                    
                    logger.info(
                        "automation_combine_folder_file",
                        extra={"folder": folder_name, "file": file_name, "path": full_path},
                    )
                    
                    combined.append(combined_control)
                else:
                    # Folder not found, keep both separate
                    combined.append(control)
                    i += 1
                    continue
                
                i += 2  # Skip both steps
            
            else:
                combined.append(control)
                i += 1
        
        return combined
