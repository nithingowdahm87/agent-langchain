import concurrent.futures
from src.llm_clients.groq_client import GroqClient
from src.engine.rag import save_to_rag

class InnovationFlywheel:
    def __init__(self):
        # We will use Groq to simulate the multi-LLM personas if others are unavailable
        self.groq = GroqClient()

    def _ask_advisory(self, persona: str, prompt: str) -> str:
        try:
            print(f"  [>] Innovation Layer ({persona}): Analyzing...")
            self.groq.temperature = 0.5
            response = self.groq.call(prompt)
            return response
        except Exception as e:
            print(f"  [!] Innovation Layer failed for {persona}: {e}")
            return ""

    def run_async(self, artifact_content: str, artifact_type: str, original_prompt: str):
        """Runs the innovation flywheel non-blocking"""
        print(f"  [>] Starting Async Innovation Flywheel for {artifact_type}...")
        
        prompts = [
            ("Modernization", f"You are a DevOps architect. Review this {artifact_type} and suggest modern API replacements or patterns for 2026. File:\n{artifact_content}"),
            ("Performance", f"You are a DevOps architect. Review this {artifact_type} and suggest performance improvements or caching strategies. File:\n{artifact_content}"),
            ("Security", f"You are a DevOps architect. Review this {artifact_type} and identify any subtle security gaps or hardening opportunities. File:\n{artifact_content}")
        ]
        
        suggestions = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_persona = {
                executor.submit(self._ask_advisory, persona, p): persona 
                for persona, p in prompts
            }
            
            for future in concurrent.futures.as_completed(future_to_persona):
                persona = future_to_persona[future]
                res = future.result()
                if res.strip():
                    suggestions.append(f"[{persona} Advisory]:\n{res}")

        if suggestions:
            combined = "\n\n".join(suggestions)
            # Write to ChromaDB
            save_to_rag(artifact_type, combined, source=f"innovation_flywheel_{artifact_type}")
            print(f"  [+] Saved {len(suggestions)} innovation advisories to RAG.")

def run_innovation_async(artifact_content: str, artifact_type: str, original_prompt: str):
    # This function itself can be called in a background thread by the orchestrator
    flywheel = InnovationFlywheel()
    flywheel.run_async(artifact_content, artifact_type, original_prompt)
