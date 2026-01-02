import subprocess
import os
from pathlib import Path
from actions.allowlist import get_app_command, is_file_allowed, get_folder
from utils.logger import setup_logger

logger = setup_logger("actions.executor")

def open_app(app_name: str, url: str = None):
    cmd = get_app_command(app_name)
    if not cmd:
        raise ValueError("App not allowed")
    
    # If URL provided, append it to the command
    if url:
        logger.info("action_open_app_with_url", extra={"app": app_name, "url": url})
        cmd = f"{cmd} {url}"
    else:
        logger.info("action_open_app", extra={"app": app_name})
    
    subprocess.Popen(cmd, shell=True)

def open_file(path: str):
    logger.info("action_open_file", extra={"path": path})
    os.startfile(path)

def open_url(url: str):
    logger.info("action_open_url", extra={"url": url})
    os.startfile(url)

def open_file_path(file_path: Path):
    """Open a file with validation."""
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    if not is_file_allowed(file_path):
        raise ValueError(f"File type {file_path.suffix} is not allowed")

    logger.info("action_open_file_safe", extra={"file": str(file_path)})
    os.startfile(file_path)

def open_latest_download():
    """Open the most recently modified file in Downloads."""
    downloads = get_folder("downloads")
    if not downloads or not downloads.exists():
        raise FileNotFoundError("Downloads folder not found")

    files = [f for f in downloads.iterdir() if f.is_file()]
    if not files:
        raise FileNotFoundError("No files in Downloads folder")

    latest = max(files, key=lambda f: f.stat().st_mtime)
    
    if not is_file_allowed(latest):
        raise ValueError(f"Latest file type {latest.suffix} is not allowed to open")

    logger.info("action_open_latest_download", extra={"file": str(latest)})
    os.startfile(latest)
