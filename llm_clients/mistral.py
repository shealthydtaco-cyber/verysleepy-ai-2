# llm_clients/mistral.py

from llm_clients.ollama_client import OllamaClient


class MistralClient:
    def __init__(self):
        self.client = OllamaClient()
        self.model_name = "mistral:7b"

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 1024,
    ) -> str:
        """
        Generate a response from Mistral using Ollama.
        """
        return self.client.generate(
            model=self.model_name,
            prompt=prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
