"""
Policy Validator — OPA/Conftest policy-as-code enforcement.

Usage:
    from src.policy.validator import PolicyValidator

    validator = PolicyValidator()
    passed, violations = validator.validate(dockerfile_content, stage="docker")
"""

import logging
import os
import subprocess
import tempfile

logger = logging.getLogger("devops-agent.policy")

# Map stage names to policy directories and temp file extensions
_STAGE_CONFIG = {
    "docker": {"policy_dir": "policies/docker", "ext": ".dockerfile", "filename": "Dockerfile"},
    "compose": {"policy_dir": "policies/docker", "ext": ".yml", "filename": "docker-compose.yml"},
    "k8s": {"policy_dir": "policies/k8s", "ext": ".yaml", "filename": "manifest.yaml"},
    "ci/cd": {"policy_dir": "policies/ci", "ext": ".yml", "filename": "workflow.yml"},
    "observability": {"policy_dir": "policies/k8s", "ext": ".yaml", "filename": "chart.yaml"},
}


class PolicyValidator:
    """
    Validates generated content against OPA/Rego policies using conftest.

    Falls back gracefully if conftest is not installed.
    """

    def __init__(self):
        self.conftest_available = self._check_conftest()
        self.project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def _check_conftest(self) -> bool:
        """Check if conftest CLI is available."""
        try:
            result = subprocess.run(
                ["conftest", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info("conftest found: %s", version)
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        logger.warning(
            "conftest not found — policy checks will use built-in rules only. "
            "Install: https://www.conftest.dev/install/"
        )
        return False

    def validate(self, content: str, stage: str) -> tuple[bool, list[str]]:
        """
        Validate content against policies for the given stage.

        Args:
            content: The generated file content (Dockerfile, YAML, etc.)
            stage: Pipeline stage (docker, k8s, ci/cd, etc.)

        Returns:
            (passed: bool, violations: list[str])
        """
        stage_key = stage.lower()
        violations = []

        # 1. Built-in rules (always run, no external deps)
        builtin_violations = self._builtin_checks(content, stage_key)
        violations.extend(builtin_violations)

        # 2. Conftest/OPA rules (if available)
        if self.conftest_available:
            config = _STAGE_CONFIG.get(stage_key, {})
            policy_dir = os.path.join(self.project_root, config.get("policy_dir", ""))

            if os.path.isdir(policy_dir) and os.listdir(policy_dir):
                conftest_violations = self._run_conftest(content, policy_dir, config)
                violations.extend(conftest_violations)

        passed = len(violations) == 0

        if violations:
            logger.warning(
                "Policy violations found | stage=%s | count=%d",
                stage, len(violations),
                extra={"stage": stage},
            )
        else:
            logger.info("Policy check passed | stage=%s", stage, extra={"stage": stage})

        return passed, violations

    def _run_conftest(self, content: str, policy_dir: str, config: dict) -> list[str]:
        """Run conftest against the content."""
        violations = []
        ext = config.get("ext", ".txt")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, delete=False, prefix="devops_policy_"
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["conftest", "test", temp_path, "--policy", policy_dir, "--output", "json"],
                capture_output=True, text=True, timeout=30,
            )

            if result.returncode != 0:
                # Parse JSON output for violations
                try:
                    import json
                    output = json.loads(result.stdout)
                    for item in output:
                        for failure in item.get("failures", []):
                            msg = failure.get("msg", "Unknown violation")
                            violations.append(f"[POLICY] {msg}")
                        for warning in item.get("warnings", []):
                            msg = warning.get("msg", "Unknown warning")
                            violations.append(f"[POLICY-WARN] {msg}")
                except (json.JSONDecodeError, TypeError):
                    if result.stderr.strip():
                        violations.append(f"[CONFTEST] {result.stderr.strip()[:300]}")

        except subprocess.TimeoutExpired:
            logger.warning("conftest timed out")
            violations.append("[CONFTEST] Policy check timed out")
        finally:
            os.unlink(temp_path)

        return violations

    # ─── Built-in Rules (no external deps) ───────────────────────

    def _builtin_checks(self, content: str, stage: str) -> list[str]:
        """Run simple built-in policy checks."""
        violations = []
        content_lower = content.lower()

        if stage == "docker":
            violations.extend(self._check_dockerfile(content, content_lower))
        elif stage == "k8s":
            violations.extend(self._check_k8s(content, content_lower))
        elif stage == "ci/cd":
            violations.extend(self._check_ci(content, content_lower))

        return violations

    def _check_dockerfile(self, content: str, content_lower: str) -> list[str]:
        """Built-in Dockerfile policy checks."""
        violations = []

        # Check for :latest tag
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.upper().startswith("FROM "):
                image = stripped[5:].strip().split(" ")[0]
                if image.endswith(":latest") or ":" not in image.split("/")[-1]:
                    violations.append(
                        f"[BUILTIN] Line {i}: Image '{image}' uses :latest or unpinned tag. "
                        "Pin to a specific version."
                    )

        # Check for USER instruction
        if "user " not in content_lower or all(
            not line.strip().upper().startswith("USER ")
            for line in lines
            if not line.strip().startswith("#")
        ):
            violations.append(
                "[BUILTIN] No USER instruction found. Container will run as root."
            )

        # Check for HEALTHCHECK
        if not any(
            line.strip().upper().startswith("HEALTHCHECK ")
            for line in lines
            if not line.strip().startswith("#")
        ):
            violations.append(
                "[BUILTIN-WARN] No HEALTHCHECK instruction. Consider adding one for production."
            )

        return violations

    def _check_k8s(self, content: str, content_lower: str) -> list[str]:
        """Built-in Kubernetes manifest policy checks."""
        violations = []

        # Check for resource limits
        if "resources:" not in content_lower:
            violations.append(
                "[BUILTIN] No resource requests/limits found. "
                "All containers should have CPU and memory limits."
            )

        # Check for default namespace
        if "namespace: default" in content_lower:
            violations.append(
                "[BUILTIN] Deploying to 'default' namespace. "
                "Use a dedicated namespace for isolation."
            )

        # Check for readiness probe
        if "readinessprobe:" not in content_lower.replace(" ", ""):
            violations.append(
                "[BUILTIN-WARN] No readinessProbe found. "
                "Add readiness probes for zero-downtime deployments."
            )

        return violations

    def _check_ci(self, content: str, content_lower: str) -> list[str]:
        """Built-in CI/CD workflow policy checks."""
        violations = []

        # Check for unpinned actions
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("- uses:") or stripped.startswith("uses:"):
                action_ref = stripped.split("uses:")[-1].strip()
                if "@" not in action_ref and action_ref:
                    violations.append(
                        f"[BUILTIN] Line {i}: Action '{action_ref}' is not pinned. "
                        "Pin to a specific version or SHA."
                    )

        # Check for pull_request_target
        if "pull_request_target" in content_lower:
            violations.append(
                "[BUILTIN] 'pull_request_target' trigger detected. "
                "This can be a security risk — ensure proper approval gates."
            )

        return violations
