import sys
import os
import subprocess

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from engine.context import extract_context
from engine.llm import generate
from engine.validate import validate
from engine.heal import heal

MAX_RETRIES = 3

def print_header(title):
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def write_to_disk(file):
    os.makedirs(os.path.dirname(file.path) if os.path.dirname(file.path) else ".", exist_ok=True)
    with open(file.path, 'w') as f:
        f.write(file.content)
    print(f"✅ Saved clean file to: {file.path}")

def sort_yaml(file_path):
    """Sort YAML keys using yq deterministically to minimize diff noise"""
    if subprocess.run(["which", "yq"], capture_output=True).returncode == 0:
        subprocess.run(["yq", "eval", "sort_keys(..)", "-i", file_path])
        print(f"🧹 Normalized YAML keys for {file_path}")

def main():
    print_header("DevOps AI Agent Pipeline v13.0 [Solo-Copilot]")
    
    if len(sys.argv) < 2:
        print("Usage: python agent.py [docker|k8s|ci]")
        sys.exit(1)
        
    task_type = sys.argv[1].lower()
    if task_type not in ["docker", "k8s", "ci"]:
        print("Invalid task. Choose: docker, k8s, or ci")
        sys.exit(1)

    project_path = input("Enter project path: ").strip()
    if not os.path.exists(project_path):
        print(f"❌ Path {project_path} does not exist.")
        sys.exit(1)

    # 1. Extract context
    print("\n📦 Extracting local project context...")
    context = extract_context(project_path)
    print(f"Context detected: {context['language']} (v{context['runtime_version']})")

    # 2. Generate initial draft
    print(f"\n🧠 Generating {task_type} files...")
    draft_files = generate(task_type, context)

    if not draft_files:
        print("❌ LLM failed to generate any valid files.")
        sys.exit(1)

    for file in draft_files:
        print(f"\n--- Processing: {file.path} ---")
        retries = 0

        # Adjust absolute paths if needed
        file.path = os.path.normpath(os.path.join(project_path, file.path))
        
        while retries < MAX_RETRIES:
            # 3. Validate
            result = validate(file)

            if result.passed:
                print("✅ Validation passed!")
                break

            # 4. Heal
            print(f"❌ Validation failed with errors:\n" + "\n".join(result.errors[:5]))
            file = heal(file, result.errors)
            retries += 1

        if retries == MAX_RETRIES:
            print(f"⛔ Failed to auto-fix {file.path} after {MAX_RETRIES} attempts.")
            sys.exit(1)

        # 5. Write and Format
        write_to_disk(file)
        if file.path.endswith(".yaml") or file.path.endswith(".yml"):
            sort_yaml(file.path)

    print("\n🎉 Generation complete!")

if __name__ == "__main__":
    main()
