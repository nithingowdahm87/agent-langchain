import sys
import os

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from engine.context import extract_context
from engine.llm import generate
from engine.orchestrator import process_file

def print_header(title):
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def main():
    print_header("DevOps AI Agent Pipeline v14.0 [Solo-Copilot]")
    
    if len(sys.argv) < 2:
        print("Usage: python agent.py [docker|k8s|ci]")
        sys.exit(1)
        
    task_type = sys.argv[1].lower()
    if task_type not in ["docker", "k8s", "ci"]:
        print("Invalid task. Choose: docker, k8s, or ci")
        sys.exit(1)

    project_path = input("Enter project path (default: ./sample_app): ").strip()
    if not project_path:
        project_path = "./sample_app"
        
    if not os.path.exists(project_path):
        print(f"❌ Path {project_path} does not exist.")
        sys.exit(1)

    # 1. Extract context
    print("\n📦 Analyzing project architecture...")
    context = extract_context(project_path)
    print(f"Context detected: {context['language']} project")

    # 2. Generate
    print(f"\n🧠 Generating {task_type.upper()} infrastructure...")
    generated_files = generate(task_type, context)

    if not generated_files:
        print("❌ Failed to generate files.")
        sys.exit(1)

    # 3. Process (Validate + Heal + Save)
    success_count = 0
    for file in generated_files:
        if process_file(file, project_path):
            success_count += 1

    print(f"\n🎉 Finished! Successfully generated and validated {success_count}/{len(generated_files)} files.")

if __name__ == "__main__":
    main()
