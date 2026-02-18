import json
import os
from datetime import datetime
from typing import Dict, Any, List

class LongTermMemory:
    """
    Simple file-based memory to store past decisions, approved artifacts, 
    and reviewer feedback. Acts as a history for the agent to 'learn' 
    (or at least recall) what worked before.
    """
    def __init__(self, project_path: str):
        self.memory_file = os.path.join(project_path, ".devops_memory.json")
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {"history": []}
        return {"history": []}

    def _save(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save memory: {e}")

    def store_decision(self, stage: str, content: str, reason: str, decision: str):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": stage,
            "decision": decision,
            "reason": reason,
            "content_snippet": content[:200] + "..." if len(content) > 200 else content
        }
        self.data.setdefault("history", []).append(entry)
        self._save()

    def get_history(self, stage: str = None) -> List[Dict[str, Any]]:
        if not stage:
            return self.data.get("history", [])
        return [h for h in self.data.get("history", []) if h["stage"] == stage]
