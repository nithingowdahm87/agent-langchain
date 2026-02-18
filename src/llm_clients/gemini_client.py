import os
from langchain_google_genai import ChatGoogleGenerativeAI

class GeminiClient:
    def __init__(self, model: str = "gemini-flash-latest", temperature: float = 0.1):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable is not set")
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
        )

    def call(self, prompt: str) -> str:
        resp = self.llm.invoke(prompt)
        return resp.content if hasattr(resp, "content") else str(resp)
