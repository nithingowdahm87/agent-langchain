from src.agents.code_analysis_agent import CodeAnalysisAgent
from src.schemas import ProjectContext

def load_or_run_analysis(project_path: str) -> ProjectContext:
    agent = CodeAnalysisAgent(project_path)
    context = agent.get_cached_analysis()
    
    if context.architecture:
        print(f"🏗️  Detected Architecture: {', '.join(context.architecture)}")
        
    if context.existing_files:
        print("\n📂 Existing DevOps Files Found:")
        for type_, path in context.existing_files.items():
            print(f"  - {type_}: {path}")
        print("\n💡 Tip: The agent will generate new files. You can choose to overwrite or keep existing ones during review.")
        
    return context
