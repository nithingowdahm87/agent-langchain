import concurrent.futures
from tenacity import retry, stop_after_attempt, wait_exponential

class Sampler:
    def __init__(self, llm_client, temperatures=[0.2, 0.4, 0.6]):
        self.llm = llm_client
        self.temperatures = temperatures

    def _generate_candidate(self, prompt: str, temp: float) -> str:
        # Override temperature for this specific call if the client supports it
        original_temp = getattr(self.llm, 'temperature', None)
        if original_temp is not None:
            self.llm.temperature = temp
            
        try:
            print(f"  [>] Generating candidate at temp {temp}...")
            response = self.llm.call(prompt)
            return response
        except Exception as e:
            print(f"  [!] Failed to generate candidate at temp {temp}: {e}")
            return ""
        finally:
            if original_temp is not None:
                 self.llm.temperature = original_temp

    def sample(self, prompt: str) -> list[str]:
        candidates = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.temperatures)) as executor:
            futures = {executor.submit(self._generate_candidate, prompt, t): t for t in self.temperatures}
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res.strip():
                    candidates.append(res)
                    
        return candidates
