# control/phi3_controller.py

import json
import re
from llm_clients.ollama_client import OllamaClient
from utils.logger import setup_logger

logger = setup_logger("control")


# -------------------- Errors --------------------

class ControlError(Exception):
    pass


class ControlParseError(ControlError):
    pass


class ControlValidationError(ControlError):
    pass


# -------------------- Constants --------------------

REQUIRED_KEYS = {
    "intent",
    "mode",
    "explicitness",
    "context",
    "web_required",
    "memory_read",
    "memory_write",
    "tone",
    "risk",
}

VALID_MODES = {
    "FACTUAL",
    "OPINION",
    "ANALYSIS",
    "SEARCH",
    "NSFW_OPEN_ANALYTICAL",
    "ACTION",
    "AUTOMATION",
    "MEMORY_GOVERNANCE",
    "UNKNOWN",
}


CONTROL_SYSTEM_PROMPT = """
You are a control and classification engine.

YOU MUST FOLLOW THESE RULES STRICTLY:

- Output ONLY raw JSON
- NO markdown
- NO explanations
- NO text outside JSON
- Use ONLY the keys listed below
- Values must be simple types (string, number, boolean)
- DO NOT create nested objects
- DO NOT rename keys
- DO NOT add extra keys

You do NOT answer the user.
You ONLY classify intent and control behavior.

--------------------------------------------------
LEGALITY RULES
--------------------------------------------------

- Fictional or consensual sexual content is ALWAYS legal.
- NSFW_OPEN_ANALYTICAL content is legal by default.
- Set risk = "illegal" ONLY if the request involves:
  - minors
  - non-consensual acts
  - real-person sexual content
  - instructions for crimes
Otherwise → risk = "legal".

--------------------------------------------------
MODE GUIDELINES
--------------------------------------------------

FACTUAL → facts, definitions, static knowledge  
OPINION → beliefs, viewpoints, public opinion  
ANALYSIS → comparison, reasoning, evaluation  
SEARCH → latest, current, real-time, external info  
NSFW_OPEN_ANALYTICAL → explicit sexual content  
ACTION → explicit requests to open apps, files, folders, or URLs on the local machine
  Examples: "Open Chrome", "Open VS Code", "Open https://google.com"
  Rules: Only classify as ACTION if user explicitly uses action verbs (open, launch)
  Do NOT infer actions.
AUTOMATION → multiple explicit actions requested in ONE command
  Examples: "Open Opera and open https://google.com", "Open Downloads then open mama.pdf"
  Rules: Only classify as AUTOMATION if the user explicitly uses separators (and, then, ,)
  that separate MULTIPLE distinct action steps. Each step will be parsed separately.
  If only one action → classify as ACTION instead.
UNKNOWN → unclear intent

--------------------------------------------------
IMPORTANT
--------------------------------------------------

- Choose ONE mode only
- intent MUST be a short string (e.g. "compare", "search", "opinion")
- explicitness must be 0–4
- Erotic / fictional content NEVER needs web search
- memory_read defaults to false
- memory_write only if user explicitly asks to save

--------------------------------------------------
JSON OUTPUT FORMAT (KEYS ONLY)
--------------------------------------------------

{
  "intent": "string",
  "mode": "string",
  "explicitness": number,
  "context": "string",
  "web_required": boolean,
  "memory_read": boolean,
  "memory_write": boolean,
  "tone": "string",
  "risk": "string",
  "action": "string or null",
  "target": "string or null"
}
"""


# -------------------- Controller --------------------

class Phi3Controller:
    def __init__(self):
        self.client = OllamaClient()

    # ---------- Public API ----------

    def classify(self, user_input: str) -> dict:
        # Pre-detect explicit memory governance (highest priority)
        if self._is_memory_governance(user_input):
            return self._create_governance_response(user_input)
        
        # Pre-detect explicit automation (multiple steps)
        if self._is_explicit_automation(user_input):
            return self._create_automation_response(user_input)
        
        # Pre-detect explicit action requests
        if self._is_explicit_action(user_input):
            return self._create_action_response(user_input)
        
        prompt = CONTROL_SYSTEM_PROMPT + "\n\nUSER INPUT:\n" + user_input.strip()

        raw = self.client.generate(
            model="phi3:mini",
            prompt=prompt,
            temperature=0.1,
            top_p=0.9,
            max_tokens=512,
        )

        clean = self._sanitize_output(raw)

        try:
            data = json.loads(clean)
        except json.JSONDecodeError as e:
            raise ControlParseError(f"Invalid JSON from Phi-3:\n{clean}") from e

        data = self._repair_and_validate(data)
        
        logger.info(
            "control_decision",
            extra={
                "mode": data.get("mode"),
                "risk": data.get("risk"),
                "explicitness": data.get("explicitness"),
                "web_required": data.get("web_required"),
                "memory_read": data.get("memory_read"),
                "memory_write": data.get("memory_write"),
            },
        )
        
        return data

    # ---------- Sanitization ----------

    def _sanitize_output(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]

        text = re.sub(r"^\s*json\s*", "", text, flags=re.IGNORECASE)

        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ControlParseError(f"No JSON object found:\n{text}")

        return match.group(0).strip()

    # ---------- Repair & Validate ----------

    def _repair_and_validate(self, data: dict) -> dict:
        self._apply_defaults(data)
        self._normalize_explicitness(data)
        self._normalize_context(data)
        self._normalize_tone(data)
        self._normalize_risk(data)
        self._normalize_mode(data)
        self._extract_action(data)
        self._validate_required_keys(data)
        return data

    # ---------- Helpers ----------

    def _apply_defaults(self, data: dict):
        data.setdefault("risk", "legal")
        data.setdefault("explicitness", 0)
        data.setdefault("memory_read", False)
        data.setdefault("memory_write", False)
        data.setdefault("web_required", False)
        data.setdefault("action", None)
        data.setdefault("target", None)

    def _normalize_explicitness(self, data: dict):
        try:
            data["explicitness"] = int(data.get("explicitness", 0))
        except (ValueError, TypeError):
            logger.info("Explicitness parse failed, defaulting to 0")
            data["explicitness"] = 0

        if not (0 <= data["explicitness"] <= 4):
            logger.info("Explicitness out of range, clamping to 0")
            data["explicitness"] = 0

    def _normalize_context(self, data: dict):
        context_map = {
            "real": "real_world",
            "real_world": "real_world",
            "static_knowledge": "real_world",
            "general": "real_world",
            "informational": "real_world",
            "fiction": "fictional",
            "fictional": "fictional",
        }

        raw = data.get("context", "")
        data["context"] = context_map.get(raw, "real_world")

    def _normalize_tone(self, data: dict):
        tone_map = {
            "": "neutral",
            "neutral": "neutral",
            "objective": "neutral",
            "informational": "neutral",
            "analytical": "analytical",
            "analysis": "analytical",
            "opinion": "opinionated",
            "opinionated": "opinionated",
            "erotic": "erotic",
        }

        raw = data.get("tone", "")
        data["tone"] = tone_map.get(raw, "neutral")

    def _normalize_risk(self, data: dict):
        if data.get("risk") not in ("legal", "illegal"):
            logger.info("Invalid risk value, defaulting to legal")
            data["risk"] = "legal"

    def _normalize_mode(self, data: dict):
        raw_mode = str(data.get("mode", "")).strip()

        if "|" in raw_mode:
            logger.info("Enum leak detected in mode: %s", raw_mode)
            raw_mode = raw_mode.split("|")[0].strip()

        if raw_mode == "ACTION":
            data["mode"] = "ACTION"
            return

        if raw_mode not in VALID_MODES:
            logger.info("Invalid mode '%s', applying fallback", raw_mode)
            self._infer_mode(data)
        else:
            data["mode"] = raw_mode

    def _infer_mode(self, data: dict):
        intent = str(data.get("intent", "")).lower()
        explicitness = data.get("explicitness", 0)

        if explicitness > 0:
            data["mode"] = "NSFW_OPEN_ANALYTICAL"
        elif "opinion" in intent or "think" in intent:
            data["mode"] = "OPINION"
        elif "compare" in intent or "analysis" in intent:
            data["mode"] = "ANALYSIS"
        elif data.get("web_required"):
            data["mode"] = "SEARCH"
        else:
            data["mode"] = "FACTUAL"

    def _extract_action(self, data: dict):
        if data.get("mode") != "ACTION":
            return

        # Strip punctuation early for better pattern matching
        intent = str(data.get("intent", "")).lower().rstrip(".,!?;:")

        # Check for latest/recent download (variations)
        download_keywords = ["latest", "most recent", "newest"]
        file_keywords = ["download", "file"]
        
        if any(dk in intent for dk in download_keywords) and any(fk in intent for fk in file_keywords):
            data["action"] = "open_latest_download"
            return

        # Check for file with extension (e.g., "Open resume.pdf")
        if "open" in intent and ("." in intent):
            target = intent.replace("open", "").strip()
            if target and target.count(".") == 1:  # Has exactly one dot (filename.ext)
                data["action"] = "open_file_path"
                data["target"] = target
                return

        # Default: app opening
        if "open" in intent or "launch" in intent:
            data["action"] = "open_app"
            # Extract target from intent (e.g., "Open Chrome" → "Chrome")
            target = intent.replace("open", "").replace("launch", "").strip()
            if target:
                data["target"] = target

    def _is_explicit_action(self, user_input: str) -> bool:
        """Check if input starts with explicit action verbs."""
        lower_input = user_input.lower().strip()
        action_verbs = ["open ", "launch ", "run ", "execute "]
        return any(lower_input.startswith(verb) for verb in action_verbs)

    def _is_memory_governance(self, user_input: str) -> bool:
        """Check if input is a memory governance command."""
        lower_input = user_input.lower().strip()
        
        governance_keywords = [
            "what do you remember",
            "show my memory",
            "forget my preferences",
            "forget my habits",
            "clear memory",
            "disable memory",
            "enable memory",
            "forget this",
        ]
        
        return any(keyword in lower_input for keyword in governance_keywords)
    
    def _create_governance_response(self, user_input: str) -> dict:
        """Create a MEMORY_GOVERNANCE response."""
        response = {
            "intent": "memory governance",
            "mode": "MEMORY_GOVERNANCE",
            "explicitness": 0,
            "context": "real_world",
            "web_required": False,
            "memory_read": False,
            "memory_write": False,
            "tone": "neutral",
            "risk": "legal",
            "action": None,
            "target": None,
        }
        
        logger.info(
            "control_decision",
            extra={
                "mode": response["mode"],
                "input": user_input,
            },
        )
        
        return response
    
    def _is_explicit_automation(self, user_input: str) -> bool:
        """Check if input contains automation separators with explicit action verbs."""
        lower_input = user_input.lower().strip()
        
        # Must start with action verb
        action_verbs = ["open ", "launch ", "run ", "execute "]
        starts_with_action = any(lower_input.startswith(verb) for verb in action_verbs)
        
        if not starts_with_action:
            return False
        
        # Must contain separators
        separators = [" and ", ", then ", " then "]
        return any(sep in lower_input for sep in separators)
    
    def _create_automation_response(self, user_input: str) -> dict:
        """Create an AUTOMATION response for multi-step action requests."""
        response = {
            "intent": "multiple explicit actions",
            "mode": "AUTOMATION",
            "explicitness": 0,
            "context": "real_world",
            "web_required": False,
            "memory_read": False,
            "memory_write": False,
            "tone": "neutral",
            "risk": "legal",
            "action": None,
            "target": None,
        }
        
        logger.info(
            "control_decision",
            extra={
                "mode": response["mode"],
                "input": user_input,
            },
        )
        
        return response

    def _create_action_response(self, user_input: str) -> dict:
        """Create an ACTION response for explicit action requests."""
        lower_input = user_input.lower().strip()
        
        # Extract action and target
        for verb in ["open ", "launch ", "run ", "execute "]:
            if lower_input.startswith(verb):
                target = user_input[len(verb):].strip()
                
                # Clean up target: remove trailing punctuation
                target = target.rstrip(".,!?;:")
                
                # Initialize response
                response = {
                    "intent": f"{verb.strip()} {target}".lower(),
                    "mode": "ACTION",
                    "explicitness": 0,
                    "context": "real_world",
                    "web_required": False,
                    "memory_read": False,
                    "memory_write": False,
                    "tone": "neutral",
                    "risk": "legal",
                    "action": None,
                    "target": None,
                }
                
                # Determine action type
                intent_lower = response["intent"].lower()
                
                # Check for URL first (before file extension check)
                if target.startswith(("http://", "https://", "www.")):
                    response["action"] = "open_url"
                    response["target"] = target
                # Check for latest/recent download (variations)
                elif any(dk in intent_lower for dk in ["latest", "most recent", "newest"]) and any(fk in intent_lower for fk in ["download", "file"]):
                    response["action"] = "open_latest_download"
                # Check for file with extension (e.g., "Open resume.pdf")
                elif "." in target and target.count(".") == 1:
                    response["action"] = "open_file_path"
                    response["target"] = target
                # Default: app opening
                else:
                    response["action"] = "open_app"
                    response["target"] = target
                
                logger.info(
                    "control_decision",
                    extra={
                        "mode": response["mode"],
                        "action": response["action"],
                        "target": response.get("target"),
                    },
                )
                
                return response
        
        # Fallback (shouldn't reach here)
        return {
            "intent": "unknown",
            "mode": "UNKNOWN",
            "action": None,
            "target": None,
            "explicitness": 0,
            "context": "real_world",
            "web_required": False,
            "memory_read": False,
            "memory_write": False,
            "tone": "neutral",
            "risk": "legal",
        }


    def _validate_required_keys(self, data: dict):
        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise ControlValidationError(f"Missing required keys: {missing}")
