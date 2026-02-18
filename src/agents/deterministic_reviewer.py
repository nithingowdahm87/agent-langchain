import subprocess
import tempfile
import os
import json
from typing import Tuple, Dict, Any

class DeterministicReviewer:
    """
    A reviewer that uses deterministic tools (linters/validators) to check code.
    This provides an objective baseline before AI synthesis.
    """
    def __init__(self):
        # Locate binaries in local bin/ directory
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.hadolint_path = os.path.join(self.base_dir, "bin", "hadolint")
        self.kubeval_path = os.path.join(self.base_dir, "bin", "kubeval")

    def run_cmd(self, cmd: list) -> Tuple[bool, str]:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.returncode == 0, res.stdout + res.stderr
        except FileNotFoundError:
            return False, f"Tool not found: {cmd[0]}"
        except Exception as e:
            return False, f"Error running tool: {e}"

    def review_dockerfile(self, content: str) -> Tuple[bool, str]:
        """
        Runs hadolint on Dockerfile content.
        Returns: (is_valid, log_message)
        """
        if not os.path.exists(self.hadolint_path):
            return True, "⚠️ Hadolint binary not found. Skipping linting."

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Run hadolint
            # We use json format for cleaner parsing if needed, but text is fine for LLM context
            ok, out = self.run_cmd([self.hadolint_path, tmp_path])
            
            if ok:
                return True, "✅ Deterministic Validation: No syntax errors found by Hadolint."
            else:
                # Filter output to remove temp file path for cleanliness
                clean_out = out.replace(tmp_path, "Dockerfile")
                return False, f"⚠️ Deterministic Validation Errors (Hadolint):\n{clean_out}"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def review_k8s(self, content: str) -> Tuple[bool, str]:
        """
        Runs kubeval on Kubernetes manifest content.
        Returns: (is_valid, log_message)
        """
        if not os.path.exists(self.kubeval_path):
            return True, "⚠️ Kubeval binary not found. Skipping validation."

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".yaml") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Run kubeval
            ok, out = self.run_cmd([self.kubeval_path, tmp_path])
            
            if ok:
                return True, "✅ Deterministic Validation: Valid Kubernetes manifests (Kubeval passed)."
            else:
                clean_out = out.replace(tmp_path, "manifest.yaml")
                return False, f"⚠️ Deterministic Validation Errors (Kubeval):\n{clean_out}"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
