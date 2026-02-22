import sys
import os
from dotenv import load_dotenv

# Load environment variables (API keys etc)
load_dotenv()

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
    
    task_type = None
    if len(sys.argv) < 2:
        print("\nAvailable DevOps Tasks:")
        print(" [1] 🐳 Docker      (Generate Dockerfiles)")
        print(" [2] ☸️  Kubernetes  (Generate Manifests)")
        print(" [3] 🚀 CI/CD       (Generate Pipeline)")
        print(" [4] 🌟 All         (Run full pipeline sequentially)")
        print(" [q] 🚪 Exit")
        
        choice = input("\nSelect: ").strip().lower()
        if choice == '1': task_type = 'docker'
        elif choice == '2': task_type = 'k8s'
        elif choice == '3': task_type = 'ci'
        elif choice == '4': task_type = 'all'
        elif choice in ['q', 'exit']: sys.exit(0)
        else:
            print("❌ Invalid choice. Please run again.")
            sys.exit(1)
    else:
        task_type = sys.argv[1].lower()

    if task_type not in ["docker", "k8s", "ci", "all"]:
        print(f"❌ Invalid task '{task_type}'. Choose: docker, k8s, ci, or all")
        sys.exit(1)

    from utils.analysis_utils import load_or_run_analysis

    project_path = input("\nEnter project path: ").strip()
    if not project_path:
        print("❌ Project path is required.")
        sys.exit(1)
        
    if not os.path.exists(project_path):
        print(f"❌ Path {project_path} does not exist.")
        sys.exit(1)

    # 1. Extract context (once)
    print("\n📦 Analyzing project architecture...")
    context_obj = load_or_run_analysis(project_path)
    context = context_obj.model_dump()

    # Determine tasks to run
    tasks_to_run = [task_type] if task_type != 'all' else ['docker', 'k8s', 'ci']

    for current_task in tasks_to_run:
        print_header(f"Starting Stage: {current_task.upper()}")
        
        # 2. Generate
        print(f"🧠 Generating {current_task.upper()} infrastructure...")
        generated_files = generate(current_task, context)

        if not generated_files:
            print(f"⚠️  LLM failed to generate {current_task} files. Skipping.")
            continue

        # 3. Process (Validate + Heal + Save)
        success_count = 0
        for file in generated_files:
            if process_file(file, project_path):
                success_count += 1

        print(f"✅ Finished {current_task}: Successfully processed {success_count}/{len(generated_files)} files.")

    print("\n" + "*"*60)
    print("🎉 Pipeline Execution Completed Successfully!")
    print("*"*60 + "\n")

if __name__ == "__main__":
    main()
