import re
from src.engine.models import GeneratedFile

class Constitution:
    def __init__(self, llm_client):
        self.llm = llm_client

    def _get_rules(self, task_type: str) -> str:
        if task_type == 'docker':
            return """
- Ensure non-root user execution.
- Avoid 'latest' tags for base images; use specific versions.
- Ensure multi-stage builds are used for compiled languages.
- Minimize layer count; combine RUN commands where appropriate.
- Never hardcode secrets or AWS/GCP credentials.
"""
        elif task_type == 'k8s':
            return """
- Ensure memory and CPU limits/requests are set for all containers.
- Ensure securityContext is configured (runAsNonRoot: true, allowPrivilegeEscalation: false).
- Ensure liveness and readiness probes are configured.
- Avoid using the 'default' namespace implicitly; use namespace isolation.
- Never hardcode secrets; reference Secret resources or use external vaults.
"""
        elif task_type == 'ci':
            return """
- Ensure granular permissions for GITHUB_TOKEN (e.g., contents: read).
- Ensure workflow triggers are restricted appropriately (e.g., branches: [main]).
- Avoid using third-party actions from unverified creators or without pinned SHAs.
- Ensure secrets are passed via GitHub Secrets, not hardcoded.
"""
        return "- Follow general production-grade infrastructure best practices."

    def critique(self, file: GeneratedFile, task_type: str) -> GeneratedFile:
        print(f"  [>] Running Constitutional Critique against {task_type} standards...")
        rules = self._get_rules(task_type)
        
        prompt = f"""
You are an expert DevOps Architect.
Review the following {task_type.upper()} configuration against these strict corporate standards:

{rules}

If the configuration violates any of these rules, REWRITE IT to comply. 
If it is already compliant, output the original configuration unaltered.

RULES FOR YOUR OUTPUT:
- Return the ENTIRE file as raw text.
- NO markdown blocks. NO backticks. NO explanations or apologies.
- Output ONLY the raw configuration content.

FILE CONTENT TO REVIEW:
{file.content}
"""
        
        response = self.llm.call(prompt)
        
        # Clean response (prompt says raw text, but let's be safe against markdown bleed)
        cleaned_content = response.strip()
        if cleaned_content.startswith("```"):
            lines = cleaned_content.splitlines()
            if len(lines) > 2:
                cleaned_content = "\n".join(lines[1:-1])
                
        return GeneratedFile(path=file.path, content=cleaned_content)

def critique_file(file: GeneratedFile, task_type: str, llm_client) -> GeneratedFile:
    return Constitution(llm_client).critique(file, task_type)
