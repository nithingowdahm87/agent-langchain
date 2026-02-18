import os
import requests

class NvidiaClient:
    def __init__(self, model: str = "meta/llama-3.1-405b-instruct", temperature: float = 0.1):
        self.api_key = os.environ.get("NVIDIA_API_KEY")
        if not self.api_key:
            raise RuntimeError("NVIDIA_API_KEY environment variable is not set")
        self.model = model
        self.temperature = temperature
        self.base_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    def call(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": 1024,
        }
        resp = requests.post(self.base_url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
