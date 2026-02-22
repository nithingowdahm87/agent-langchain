import subprocess
import os
from src.engine.models import GeneratedFile, ValidationResult

class Validator:
    def validate(self, generated_file: GeneratedFile) -> ValidationResult:
        if generated_file.path.endswith("Dockerfile"):
            return self._run_hadolint(generated_file)
        
        if generated_file.path.endswith(".yaml") or generated_file.path.endswith(".yml"):
            if "k8s" in generated_file.path.lower() or "manifest" in generated_file.path.lower():
                return self._run_kubeconform(generated_file)
            if ".github/workflows" in generated_file.path.lower():
                return self._run_actionlint(generated_file)
            
        print(f"⚠️  No specific validator configured for {generated_file.path}, passing by default.")
        return ValidationResult(True, [])

    def _run_hadolint(self, file: GeneratedFile) -> ValidationResult:
        # Check if hadolint is installed
        if subprocess.run(["which", "hadolint"], capture_output=True).returncode != 0:
            print("⚠️  hadolint not found. Skipping Dockerfile validation. Please install it.")
            return ValidationResult(True, [])

        print(f"🔍 Validating {file.path} with hadolint...")
        result = subprocess.run(
            ["hadolint", "-"],
            input=file.content,
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            return ValidationResult(False, result.stdout.splitlines() + result.stderr.splitlines())
        return ValidationResult(True, [])

    def _run_kubeconform(self, file: GeneratedFile) -> ValidationResult:
        if subprocess.run(["which", "kubeconform"], capture_output=True).returncode != 0:
            print("⚠️  kubeconform not found. Skipping K8s validation. Please install it.")
            return ValidationResult(True, [])
            
        print(f"🔍 Validating {file.path} with kubeconform...")
        # Write temporarily to feed kubeconform
        tmp_path = "/tmp/manifest_to_check.yaml"
        with open(tmp_path, "w") as f:
            f.write(file.content)
            
        result = subprocess.run(
            ["kubeconform", "-strict", tmp_path],
            text=True,
            capture_output=True
        )
        os.remove(tmp_path)

        if result.returncode != 0:
            return ValidationResult(False, result.stdout.splitlines() + result.stderr.splitlines())
        return ValidationResult(True, [])

    def _run_actionlint(self, file: GeneratedFile) -> ValidationResult:
        if subprocess.run(["which", "actionlint"], capture_output=True).returncode != 0:
            print("⚠️  actionlint not found. Skipping Action validation. Please install it.")
            return ValidationResult(True, [])

        print(f"🔍 Validating {file.path} with actionlint...")
        result = subprocess.run(
            ["actionlint", "-"],
            input=file.content,
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            return ValidationResult(False, result.stdout.splitlines() + result.stderr.splitlines())
        return ValidationResult(True, [])

def validate(generated_file: GeneratedFile) -> ValidationResult:
    return Validator().validate(generated_file)
