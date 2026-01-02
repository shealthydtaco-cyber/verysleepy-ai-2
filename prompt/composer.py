# prompt/composer.py

from pathlib import Path
from typing import Optional


class PromptComposer:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.templates_dir = base_dir / "templates"

        self.philosophy = self._load("philosophy.txt")
        self.persona = self._load("persona.txt")
        self.limits = self._load("limits.txt")

        self.mode_templates = {
            "FACTUAL": self._load_template("factual.txt"),
            "OPINION": self._load_template("opinion.txt"),
            "ANALYSIS": self._load_template("analysis.txt"),
            "SEARCH": self._load_template("search.txt"),
            "NSFW_OPEN_ANALYTICAL": self._load_template("nsfw.txt"),
            "UNKNOWN": "",
        }

    def _load(self, name: str) -> str:
        path = self.base_dir / name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def _load_template(self, name: str) -> str:
        path = self.templates_dir / name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def compose(
        self,
        control: dict,
        user_input: str,
        memory_context: Optional[str] = None,
        web_context: Optional[str] = None,
    ) -> str:
        parts = []

        if self.philosophy:
            parts.append(self.philosophy)

        if self.persona:
            parts.append(self.persona)

        if self.limits:
            parts.append(self.limits)

        mode = control.get("mode", "UNKNOWN")
        template = self.mode_templates.get(mode, "")
        if template:
            parts.append(template)

        if control.get("memory_read") and memory_context:
            parts.append("MEMORY CONTEXT:\n" + memory_context)

        if control.get("web_required") and web_context:
            parts.append("WEB CONTEXT:\n" + web_context)

        parts.append("USER INPUT:\n" + user_input.strip())

        return "\n\n".join(parts)
