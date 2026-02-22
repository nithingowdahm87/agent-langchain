import os
from src.engine.validate import validate_file
from src.engine.heal import heal_file
from src.engine.config import MAX_RETRIES
from src.engine.models import GeneratedFile

class Orchestrator:
    def process(self, file: GeneratedFile, project_path: str):
        print(f"\n--- Processing: {file.path} ---")
        retries = 0

        # Ensure correct path inside project
        original_path = file.path
        file.path = os.path.normpath(os.path.join(project_path, original_path))
        
        while retries < MAX_RETRIES:
            # 1. Validate
            result = validate_file(file)

            if result.passed:
                print(f"✅ {original_path} PASSED validation.")
                break

            # 2. Heal
            print(f"❌ {original_path} FAILED validation (Attempt {retries+1}/{MAX_RETRIES})")
            print("Errors detected:")
            for err in result.errors[:3]:
                print(f"  - {err}")
            
            file = heal_file(file, result.errors)
            retries += 1

        if retries == MAX_RETRIES:
            print(f"⛔ FAILED to auto-fix {original_path} after {MAX_RETRIES} attempts.")
            return False

        # 3. Write to disk
        self._write_to_disk(file)
        return True

    def _write_to_disk(self, file: GeneratedFile):
        os.makedirs(os.path.dirname(file.path), exist_ok=True)
        with open(file.path, 'w') as f:
            f.write(file.content)
        print(f"💾 Saved to: {file.path}")

def process_file(file: GeneratedFile, project_path: str) -> bool:
    return Orchestrator().process(file, project_path)
