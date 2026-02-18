from src.llm_clients.perplexity_client import PerplexityClient
from src.tools.file_ops import read_file

class PromptImprover:
    def __init__(self):
        self.llm = PerplexityClient()
        
    def improve(self, original: str, domain: str) -> str:
        guidelines_path = f"configs/guidelines/{domain}-guidelines.md"
        try:
            guidelines = read_file(guidelines_path)
        except FileNotFoundError:
            guidelines = ""
            
        prompt = f"""
You are an expert prompt engineer for DevOps.
Domain: {domain}
Guidelines:
{guidelines}
Original prompt:
{original}
Rewrite the prompt to:
- Be more explicit and precise.
- Include relevant DevOps best practices.
Return ONLY the improved prompt.
""".strip()
        return self.llm.call(prompt)
