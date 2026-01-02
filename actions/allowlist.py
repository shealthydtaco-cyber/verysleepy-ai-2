import os
from pathlib import Path

def _get_spotify_path() -> str:
    """Get Spotify executable path from common locations."""
    common_paths = [
        Path.home() / "AppData" / "Roaming" / "Spotify" / "Spotify.exe",
        Path("C:/Program Files/Spotify/Spotify.exe"),
        Path("C:/Program Files (x86)/Spotify/Spotify.exe"),
    ]
    for path in common_paths:
        if path.exists():
            return str(path)
    return "spotify"  # Fallback to command line

def _get_opera_path() -> str:
    """Get Opera executable path from common locations."""
    common_paths = [
        Path("C:/Program Files/Opera/opera.exe"),
        Path("C:/Program Files (x86)/Opera/opera.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "Opera GX" / "opera.exe",
        Path.home() / "AppData" / "Local" / "Programs" / "Opera" / "opera.exe",
    ]
    for path in common_paths:
        if path.exists():
            return str(path)
    return "opera"  # Fallback to command line

ALLOWED_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "spotify": _get_spotify_path(),
    "opera": _get_opera_path(),
    "downloads": "explorer.exe shell:Downloads",
    "downloads folder": "explorer.exe shell:Downloads",
    "pictures": "explorer.exe shell:Pictures",
    "pictures folder": "explorer.exe shell:Pictures",
}

ALLOWED_URL_SCHEMES = ("http://", "https://")

# Allowed file extensions (open-only, no write/delete)
ALLOWED_FILE_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".docx",
}

# Safe known folders
ALLOWED_FOLDERS = {
    "downloads": Path("D:/Downloads"),
}

def is_app_allowed(name: str) -> bool:
    if name is None:
        return False
    return name.lower() in ALLOWED_APPS

def get_app_command(name: str) -> str | None:
    return ALLOWED_APPS.get(name.lower())

def is_file_allowed(path: Path) -> bool:
    """Check if file extension is in the allowlist."""
    return path.suffix.lower() in ALLOWED_FILE_EXTENSIONS

def get_folder(name: str) -> Path | None:
    """Get safe folder path by name."""
    return ALLOWED_FOLDERS.get(name.lower())
