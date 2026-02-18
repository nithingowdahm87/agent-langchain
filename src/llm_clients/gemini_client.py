import os
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.secrets import get_secret
from tenacity import retry, stop_after_attempt, wait_exponential

class GeminiClient:
    def __init__(self, model: str = "gemini-flash-latest", temperature: float = 0.1):
        api_key = get_secret("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call(self, prompt: str) -> str:
        resp = self.llm.invoke(prompt)
        return resp.content if hasattr(resp, "content") else str(resp)
