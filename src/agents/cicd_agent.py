from src.llm_clients.gemini_client import GeminiClient
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.nvidia_client import NvidiaClient
from src.tools.file_ops import read_file, write_file
import os

class CIWriterA:
    def __init__(self):
        self.llm = GeminiClient()
        
    def generate(self, context: str) -> str:
        prompt = f"""
        You are a DevOps Engineer specializing in GitHub Actions.
        PROJECT CONTEXT:
        {context}
        
        Task: Write a .github/workflows/ci.yml file.
        Requirements:
        - Checkout code.
        - Setup language environment.
        - Install dependencies.
        - Run Linting.
        - Run Tests.
        - Build Docker image.
        
        Return ONLY the YAML content.
        """.strip()
        return self.llm.call(prompt)

class CIWriterB:
    def __init__(self):
        self.llm = GroqClient()
        
    def generate(self, context: str) -> str:
        prompt = f"""
        You are a Security Engineer specializing in DevSecOps.
        PROJECT CONTEXT:
        {context}
        
        Task: Write a .github/workflows/security.yml file.
        Requirements:
        - Run Trivy vulnerability scanner.
        - Run SonarQube analysis (placeholder).
        - Check for secrets in code.
        - Build Docker image securely.
        
        Return ONLY the YAML content.
        """.strip()
        return self.llm.call(prompt)

class CIWriterC:
    def __init__(self):
        self.llm = NvidiaClient()
        
    def generate(self, context: str) -> str:
        prompt = f"""
        You are a Release Engineer focused on Speed.
        PROJECT CONTEXT:
        {context}
        
        Task: Write a .github/workflows/deploy.yml file.
        Requirements:
        - Aggressive caching (npm/pip/docker).
        - Parallel jobs where possible.
        - Build and Push to Registry (placeholder).
        
        Return ONLY the YAML content.
        """.strip()
        return self.llm.call(prompt)

class CIReviewer:
    def __init__(self):
        from src.llm_clients.perplexity_client import PerplexityClient
        self.llm = PerplexityClient()
    
    def review_and_merge(self, yaml_a: str, yaml_b: str, yaml_c: str, validation_report: str = "") -> tuple[str, str]:
        feedback_section = ""
        if validation_report:
            feedback_section = f"""
        VALIDATION/USER FEEDBACK (MUST ADDRESS):
        {validation_report}
        """
        prompt = f"""
        You are a Lead DevOps Architect. Review 3 GitHub Actions workflows.
        
        Workflow A (General):
        {yaml_a}
        
        Workflow B (Security):
        {yaml_b}
        
        Workflow C (Speed):
        {yaml_c}
        {feedback_section}
        TASK:
        1. Combine them into a SINGLE comprehensive `.github/workflows/main.yml`.
        2. Ensure correct order: Checkout -> Lint/Test -> Security Scan -> Build -> Push.
        3. Use caching from C, Security from B, and standard steps from A.
        4. Address all feedback points if any.
        
        OUTPUT FORMAT:
        REASONING:
        - point 1
        - point 2
        
        YAML:
        ```yaml
        ...
        ```
        """.strip()
        
        response = self.llm.call(prompt)
        try:
            if "YAML:" in response:
                parts = response.split("YAML:")
                return (parts[1].replace("```yaml", "").replace("```", "").strip(), parts[0].replace("REASONING:", "").strip())
            return (response, "AI Review Completed")
        except: return (yaml_a, "Fallback to Draft A")

class CIExecutor:
    def run(self, content: str, project_path: str):
        directory = os.path.join(project_path, ".github", "workflows")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, "main.yml")
        write_file(path, content)
        print(f"✅ Wrote CI/CD workflow to {path}")
