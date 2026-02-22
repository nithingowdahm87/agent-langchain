import os
import yaml
from src.engine.utils import run_cmd
from src.engine.models import GeneratedFile, ValidationResult

class Validator:
    def validate(self, file: GeneratedFile) -> ValidationResult:
        path = file.path
        # If absolute path is short or relative, we might need to write to a temp file for some tools
        # But for now, let's assume the validators can handle the content if passed via stdin or temp file
        
        filetype = self._detect_type(path)
        errors = []

        if filetype == "docker":
            errors = self._validate_dockerfile(file)
        elif filetype == "k8s":
            errors = self._validate_k8s(file)
        elif filetype == "gha":
            errors = self._validate_github_actions(file)
        else:
            print(f"⚠️  No valid validator for {path}")
            return ValidationResult(True, [])

        return ValidationResult(len(errors) == 0, errors)

    def _detect_type(self, path: str):
        if path.endswith("Dockerfile"):
            return "docker"
        if ".github/workflows" in path:
            return "gha"
        if path.endswith(".yaml") or path.endswith(".yml"):
            return "k8s"
        return None

    def _validate_dockerfile(self, file: GeneratedFile) -> list[str]:
        errors = []
        # 1. hadolint (via stdin)
        code, out, err = run_cmd(["hadolint", "-"])
        # We need to pipe the content. run_cmd doesn't support pipe yet in its simple form.
        # Let's fix run_cmd logic or use a temp file.
        
        tmp_path = f"/tmp/hadolint_{os.getpid()}"
        with open(tmp_path, "w") as f:
            f.write(file.content)
        
        code, out, err = run_cmd(["hadolint", tmp_path])
        if code != 0:
            if "No such file or directory" in err or "not found" in err:
                print("⚠️  hadolint not installed. Skipping static analysis.")
            else:
                errors.append(f"HADOLINT ERROR:\n{out or err}")
        
        # 2. docker build (dry run / check) - too slow for local loop usually without a daemon
        # skip for now unless specifically requested.
        
        os.remove(tmp_path)
        return errors

    def _validate_k8s(self, file: GeneratedFile) -> list[str]:
        errors = []
        tmp_path = f"/tmp/k8s_{os.getpid()}.yaml"
        with open(tmp_path, "w") as f:
            f.write(file.content)

        code, out, err = run_cmd(["kubeconform", "-strict", tmp_path])
        if code != 0:
            if "No such file or directory" in err or "not found" in err:
                print("⚠️  kubeconform not installed. Skipping strict schema validation.")
            else:
                errors.append(f"KUBECONFORM ERROR:\n{out or err}")

        # Custom rules
        try:
            docs = list(yaml.safe_load_all(file.content))
            for doc in docs:
                if not doc: continue
                kind = doc.get("kind")
                if kind == "Deployment":
                    spec = doc.get("spec", {})
                    replicas = spec.get("replicas", 0)
                    if replicas < 2:
                        errors.append("Deployment replicas < 2")
                    
                    template = spec.get("template", {})
                    pod_spec = template.get("spec", {})
                    sc = pod_spec.get("securityContext", {})
                    if sc.get("runAsNonRoot") is not True:
                        errors.append("Pod securityContext.runAsNonRoot missing or not true")
        except Exception as e:
            errors.append(f"YAML PARSE ERROR: {str(e)}")

        os.remove(tmp_path)
        return errors

    def _validate_github_actions(self, file: GeneratedFile) -> list[str]:
        errors = []
        try:
            workflow = yaml.safe_load(file.content)
            jobs = workflow.get("jobs", {})
            if len(jobs) < 2:
                errors.append("All stages must be separate jobs (found < 2 jobs)")

            for job_name, job in jobs.items():
                steps = job.get("steps", [])
                for step in steps:
                    if "run" in step and "uses" in step:
                        errors.append(f"Step in job '{job_name}' contains both 'run' and 'uses'")
                
                # Check if needs is inside steps (shouldn't be possible to parse easily if it is, but let's check)
                # needs is a job-level key. If it's in steps, it shouldn't even be there.
        except Exception as e:
            errors.append(f"GHA YAML PARSE ERROR: {str(e)}")
            
        return errors

def validate_file(file: GeneratedFile) -> ValidationResult:
    return Validator().validate(file)
