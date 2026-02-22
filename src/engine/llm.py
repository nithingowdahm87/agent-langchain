import os
import re
from src.llm_clients.groq_client import GroqClient
from src.engine.models import GeneratedFile

class LLMGenerator:
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = self._load_prompt("configs/prompts/system/system_core.md")
        
    def _load_prompt(self, filepath: str) -> str:
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""
            
    def _get_task_prompt(self, task_type: str) -> str:
        task_map = {
            "docker": "configs/prompts/docker/docker_production.md",
            "k8s": "configs/prompts/k8s/k8s_production.md",
            "ci": "configs/prompts/cicd/cicd_production.md"
        }
        path = task_map.get(task_type.lower())
        if path:
            return self._load_prompt(path)
        return ""

    def generate(self, task_type: str, context: dict) -> list[GeneratedFile]:
        task_prompt = self._get_task_prompt(task_type)
        if not task_prompt:
            raise ValueError(f"Unknown task type: {task_type}")

        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        full_prompt = f"{self.system_prompt}\n\n{task_prompt}\n\nAPPLICATION CONTEXT:\n{context_str}"

        print(f"🧠 Generating {task_type} files...")
        try:
            response = self.llm.call(full_prompt)
        except Exception as e:
            # Handle blocked/leaked API keys gracefully
            if "RetryError" in type(e).__name__:
                try:
                    e = e.last_attempt.exception()
                except Exception:
                    pass
            print(f"❌ API Error: {e}")
            if "PERMISSION_DENIED" in str(e) or "403" in str(e) or "NOT_FOUND" in str(e):
                print("⚠️  Your Google API key is expired, leaked, or the model is invalid for this key. Please check your .env file.")
            return []
            
        return self._parse_files(response)

    def _parse_files(self, response: str) -> list[GeneratedFile]:
        files = []
        # Match FILENAME: filepath\n```ext\ncontent``` or FILENAME: filepath\ncontent
        pattern = r"FILENAME:\s*(.*?)\n(?:```[\w]*\n)?(.*?)(?:```|$)"
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            path = match.group(1).strip()
            content = match.group(2).strip()
            # Clean trailing backticks from content if present
            if content.endswith('```'):
                 content = content[:-3].strip()
            files.append(GeneratedFile(path=path, content=content))
        
        # Fallback if the strict FILENAME format wasn't produced perfectly
        if not files:
            # Try splitting by markdown blocks if there's only one block
            blocks = re.findall(r"```.*?\n(.*?)```", response, re.DOTALL)
            if blocks:
                 files.append(GeneratedFile(path="generated_file", content=blocks[0].strip()))
                 
        return files

def generate(task_type: str, context: dict) -> list[GeneratedFile]:
    return LLMGenerator().generate(task_type, context)
