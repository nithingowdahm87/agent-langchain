from src.engine.models import GeneratedFile
from src.llm_clients.gemini_client import GeminiClient

class Healer:
    def __init__(self):
        self.llm = GeminiClient()
        self.prompt = self._load_prompt("configs/prompts/debug/healer.md")
        
    def _load_prompt(self, filepath: str) -> str:
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "Fix the code to resolve the error. Minimal diff."

    def heal(self, file: GeneratedFile, errors: list[str]) -> GeneratedFile:
        print(f"🚑 Healing {file.path}...")
        error_str = "\n".join(errors)
        
        full_prompt = f"{self.prompt}\n\nBROKEN FILE:\n```\n{file.content}\n```\n\nERROR:\n{error_str}"
        
        response = self.llm.call(full_prompt)
        
        # Clean markdown formatting if returned
        healed_content = response.strip()
        if healed_content.startswith("```"):
            lines = healed_content.splitlines()
            if len(lines) > 2:
                healed_content = "\n".join(lines[1:-1])
                
        return GeneratedFile(path=file.path, content=healed_content)

def heal(file: GeneratedFile, errors: list[str]) -> GeneratedFile:
    return Healer().heal(file, errors)
