from pathlib import Path
from utils.config import load_config
from utils.logger import setup_logger
from actions.executor import open_app, open_file, open_url, open_file_path, open_latest_download
from actions.allowlist import is_app_allowed

logger = setup_logger("actions.manager")
config = load_config()

class ActionManager:
    def __init__(self, habit_tracker=None):
        """
        Args:
            habit_tracker: Optional HabitTracker instance for passive recording
        """
        self.habit_tracker = habit_tracker
    
    def run(self, control: dict):
        if not config.get("actions", {}).get("enabled", False):
            logger.warning("actions_disabled")
            return "Local actions are disabled."

        action = control.get("action")
        target = control.get("target")

        # Validate action and target
        if not action:
            logger.error("action_missing", extra={"target": target})
            return "No action detected. Please try again."

        # Target is required for most actions except open_latest_download
        if not target and action != "open_latest_download":
            logger.error("action_target_missing", extra={"action": action})
            return f"I didn't catch what you want to {action}. Please try again."

        if action == "open_app":
            # Extract app name and optional URL from combined target
            url_param = control.get("_url_param")
            app_name = control.get("_app_name", target)
            
            if not is_app_allowed(app_name):
                logger.warning("action_app_not_allowed", extra={"app": app_name})
                return f"I can't open '{app_name}'. It's not in my allowed list."
            try:
                open_app(app_name, url=url_param)
                # Record habit (success only)
                if self.habit_tracker:
                    self.habit_tracker.record(f"action.open_app.{app_name.lower()}")
                if url_param:
                    logger.info("action_open_app_with_url_success", extra={"app": app_name, "url": url_param})
                    return f"Opened {app_name} with {url_param}."
                else:
                    logger.info("action_open_app_success", extra={"app": app_name})
                    return f"Opened {app_name}."
            except Exception as e:
                logger.error("action_open_app_failed", extra={"app": app_name, "error": str(e)})
                return f"Failed to open {app_name}. Check if it's installed."

        if action == "open_file":
            try:
                open_file(target)
                logger.info("action_open_file_success", extra={"file": target})
                return f"Opened file."
            except Exception as e:
                logger.error("action_open_file_failed", extra={"file": target, "error": str(e)})
                return f"Failed to open the file."

        if action == "open_url":
            try:
                open_url(target)
                logger.info("action_open_url_success", extra={"url": target})
                return f"Opened URL."
            except Exception as e:
                logger.error("action_open_url_failed", extra={"url": target, "error": str(e)})
                return f"Failed to open the URL."

        if action == "open_file_path":
            if not target:
                logger.error("action_file_path_missing")
                return "No file specified."
            try:
                open_file_path(Path(target))
                folder_name = control.get("_folder_name")
                file_name = control.get("_file_name")
                # Record habit (success only)
                if self.habit_tracker:
                    if folder_name:
                        self.habit_tracker.record(f"action.open_folder.{folder_name.lower()}")
                    self.habit_tracker.record("action.open_file")
                if folder_name and file_name:
                    logger.info("action_open_file_from_folder_success", extra={"folder": folder_name, "file": file_name})
                    return f"Opened {file_name} from {folder_name}."
                else:
                    logger.info("action_open_file_path_success", extra={"file": target})
                    return f"Opened {Path(target).name}."
            except FileNotFoundError:
                logger.warning("action_file_not_found", extra={"file": target})
                return f"File '{target}' not found."
            except ValueError as e:
                logger.warning("action_file_type_not_allowed", extra={"file": target})
                return f"File type not allowed. Allowed types: .pdf, .txt, .docx, .png, .jpg, .jpeg"
            except Exception as e:
                logger.error("action_open_file_path_failed", extra={"file": target, "error": str(e)})
                return f"Failed to open '{target}'."

        if action == "open_latest_download":
            try:
                open_latest_download()
                # Record habit (success only)
                if self.habit_tracker:
                    self.habit_tracker.record("action.open_latest_download")
                logger.info("action_open_latest_download_success")
                return "Opened latest download."
            except FileNotFoundError as e:
                logger.warning("action_latest_download_not_found", extra={"reason": str(e)})
                return str(e)
            except ValueError as e:
                logger.warning("action_latest_download_type_not_allowed")
                return f"Latest file type not allowed. {str(e)}"
            except Exception as e:
                logger.error("action_open_latest_download_failed", extra={"error": str(e)})
                return "Failed to open latest download."

        logger.error("action_unknown", extra={"action": action})
        return "Unknown or unsupported action."
