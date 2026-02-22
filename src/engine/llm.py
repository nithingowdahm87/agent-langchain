import os
import re
from src.llm_clients.groq_client import GroqClient
from src.engine.models import GeneratedFile
from src.engine.sampler import Sampler
from src.engine.constitution import Constitution

class LLMGenerator:
    def __init__(self):
        self.llm = GroqClient()
        self.sampler = Sampler(self.llm)
        self.constitution = Constitution(self.llm)
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

        print(f"🧠 Generating {task_type} candidates (Self-Consistency)...")
        candidates = self.sampler.sample(full_prompt)
        
        if not candidates:
             print("❌ Failed to generate any valid candidates.")
             return []
             
        # Pick the most consistent candidate (for simplicity, we grab the first valid one if not doing real embedding scores here, but usually, you'd score. Let's pick the longest one as a simple heuristic for completeness)
        winner_text = max(candidates, key=len)
        
        # Parse the winner into GeneratedFile objects
        files = self._parse_files(winner_text)
        
        # Constitutional Critique
        critiqued_files = []
        for f in files:
            cf = self.constitution.critique(f, task_type)
            critiqued_files.append(cf)
            
        return critiqued_files

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
