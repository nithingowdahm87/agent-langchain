import os
import requests
from src.utils.secrets import get_secret

class PerplexityClient:
    def __init__(self, model: str = "sonar", temperature: float = 0.1):
        token = get_secret("PPLX_API_KEY")
        self.token = token
        self.model = model
        self.temperature = temperature
        self.base_url = "https://api.perplexity.ai/chat/completions"

    def call(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }
        resp = requests.post(self.base_url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        j = resp.json()
        return j["choices"][0]["message"]["content"]
