# validation/guard.py

import re
import logging
from typing import Callable
from utils.config import load_config

logger = logging.getLogger("guard")
config = load_config()
NSFW_ENABLED = config.get("nsfw", {}).get("enabled", True)


class ResponseGuard:
    def apply(self, control: dict, response: str) -> str:
        """
        Entry point. Routes response through the appropriate guard
        based on control mode.
        """
        mode = control.get("mode", "UNKNOWN")
        response = response.strip()

        guard = self._get_guard(mode)
        return guard(response)

    # -------------------- Router --------------------

    def _get_guard(self, mode: str) -> Callable[[str], str]:
        return {
            "FACTUAL": self._guard_factual,
            "OPINION": self._guard_opinion,
            "NSFW_OPEN_ANALYTICAL": self._guard_nsfw,
        }.get(mode, self._guard_passthrough)

    # -------------------- Guards --------------------

    def _guard_factual(self, text: str) -> str:
        text = self._remove_opinion_phrases(text)
        return self._keep_first_sentence(text)

    def _guard_opinion(self, text: str) -> str:
        return self._ensure_opinion_framing(text)

    def _guard_nsfw(self, text: str) -> str:
        """
        NSFW responses must not contain refusals, policy language,
        moral framing, or meta commentary.
        If such content exists, strip it aggressively.
        """

        refusal_patterns = [
            r"i'm here to.*",
            r"i am here to.*",
            r"my purpose is.*",
            r"as per.*guidelines.*",
            r"against.*guidelines.*",
            r"i cannot.*",
            r"i can't.*",
            r"i won't.*",
            r"i will not.*",
            r"i do not.*engage.*",
            r"this is not appropriate.*",
            r"i am not allowed.*",
            r"i can help with.*instead.*",
            r"i can provide.*information.*",
            r"warning.*",
            r"illegal.*",
            r"immoral.*",
        ]

        cleaned = text
        found_refusal = False
        for pattern in refusal_patterns:
            if re.search(pattern, cleaned, flags=re.IGNORECASE | re.DOTALL):
                found_refusal = True
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

        if found_refusal:
            logger.debug(
                "guard_stripped_response",
                extra={
                    "mode": "NSFW_OPEN_ANALYTICAL",
                    "reason": "refusal_or_policy_detected",
                },
            )

        return cleaned.strip()

    def _guard_passthrough(self, text: str) -> str:
        return text

    # -------------------- Transformations --------------------

    def _remove_opinion_phrases(self, text: str) -> str:
        patterns = [
            r"\bI think\b.*",
            r"\bin my opinion\b.*",
            r"\bmay be\b.*",
            r"\bperhaps\b.*",
        ]
        for p in patterns:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
        return text.strip()

    def _keep_first_sentence(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return sentences[0].strip() if sentences else text.strip()

    def _ensure_opinion_framing(self, text: str) -> str:
        if not re.search(r"\b(opinion|believe|think|view)\b", text, re.IGNORECASE):
            return "Opinions vary, but " + text
        return text

    def _remove_refusals_and_warnings(self, text: str) -> str:
        patterns = [
            r"\bthis is not appropriate\b.*",
            r"\bI cannot\b.*",
            r"\bI can't\b.*",
            r"\bwarning\b.*",
            r"\bimmoral\b.*",
            r"\billegal\b.*",
        ]
        for p in patterns:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
        return text.strip()
