# llm_clients/ollama_client.py

import requests
import json
from typing import Optional


class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host.rstrip("/")

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a prompt to Ollama and return raw text output.
        """
        url = f"{self.host}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
        }

        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        try:
            response = requests.post(url, json=payload, timeout=120)
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama connection failed: {e}")

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama error {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise RuntimeError("Invalid JSON response from Ollama")

        if "response" not in data:
            raise RuntimeError(f"Unexpected Ollama response: {data}")

        return data["response"].strip()
