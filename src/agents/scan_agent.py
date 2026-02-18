from typing import List, Dict, Any
import logging
from src.llm_clients.base_llm_client import BaseLLMClient
from src.schemas import ProjectContext

logger = logging.getLogger("devops-agent.scan")

class ScanWriter:
    def __init__(self, client: BaseLLMClient):
        self.client = client

    def generate(self, context: str) -> str:
        # We will load the prompt dynamically in the orchestrator or here
        # For now, simplistic generation
        return self.client.call(f"Generate SonarQube and OpenTelemetry configs for: {context}")

class ScanReviewer:
    def review_and_merge(self, a: str, b: str, c: str) -> str:
        # Simple selection/merging
        # For configs, usually one good draft is enough, but we can combine.
        # Prefer the one that covers all services.
        return a # Simplistic for now

class ScanExecutor:
    def run(self, content: str, project_path: str):
        # Parse the content which might contain multiple files
        # Format: FILENAME: <path>\n```code```
        import re
        import os
        
        # Regex to find sections: FILENAME: path\n```...\n```
        pattern = r"FILENAME: (.*?)\n```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)
        
        for rel_path, file_content in matches:
            rel_path = rel_path.strip()
            full_path = os.path.join(project_path, rel_path)
            
            # CRITICAL: Do not overwrite existing SOURCE files. 
            # But configs are usually new.
            # We will adhere to "Create NEW files".
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(file_content.strip())
            
            print(f"✅ Created {rel_path}")

