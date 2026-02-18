from src.llm_clients.gemini_client import GeminiClient
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.nvidia_client import NvidiaClient
from src.tools.file_ops import read_file, write_file
import os

class ObservabilityWriterA:
    def __init__(self):
        self.llm = GeminiClient()
        
    def generate(self, context: str) -> str:
        prompt = f"""
        You are a Site Reliability Engineer (SRE).
        PROJECT CONTEXT:
        {context}
        
        Task: Create a Helm Chart.yaml for specialized observability.
        Requirements:
        - Include Prometheus for metrics.
        - Include Loki for logs.
        - Include Grafana for visualization.
        - Set appropriate versions.
        
        Return ONLY the YAML content for Chart.yaml.
        """.strip()
        return self.llm.call(prompt)

class ObservabilityWriterB:
    def __init__(self):
        self.llm = GroqClient()
        
    def generate(self, context: str) -> str:
        prompt = f"""
        You are a SecOps Engineer.
        PROJECT CONTEXT:
        {context}
        
        Task: Create a secure Helm Chart.yaml for monitoring.
        Requirements:
        - Use hardened images for Prometheus/Grafana.
        - Enable persistence.
        - Add dependency on kube-state-metrics.
        
        Return ONLY the YAML content for Chart.yaml.
        """.strip()
        return self.llm.call(prompt)

class ObservabilityWriterC:
    def __init__(self):
        self.llm = NvidiaClient()
        
    def generate(self, context: str) -> str:
        prompt = f"""
        You are a Performance Engineer.
        PROJECT CONTEXT:
        {context}
        
        Task: Create a lightweight Helm Chart.yaml for monitoring.
        Requirements:
        - Minimal resource footprint.
        - Use VictoriaMetrics instead of Prometheus if possible (or optimized Prometheus).
        - Essential metrics only.
        
        Return ONLY the YAML content for Chart.yaml.
        """.strip()
        return self.llm.call(prompt)

class ObservabilityReviewer:
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
        You are a Lead SRE Architect. Review 3 Helm Chart definitions.
        
        Chart A (Standard):
        {yaml_a}
        
        Chart B (Secure):
        {yaml_b}
        
        Chart C (Performance):
        {yaml_c}
        {feedback_section}
        TASK:
        1. Synthesize the BEST `Chart.yaml` for a production-grade monitoring stack.
        2. Ensure standard dependencies (Prometheus, Loki, Grafana) are present.
        3. Address all feedback points if any.
        4. Explain reasoning.
        
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
        except Exception: return (yaml_a, "Fallback to Draft A")

class ObservabilityExecutor:
    def run(self, content: str, project_path: str):
        directory = os.path.join(project_path, "helm", "monitoring")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, "Chart.yaml")
        write_file(path, content)
        print(f"✅ Wrote Helm Chart to {path}")
