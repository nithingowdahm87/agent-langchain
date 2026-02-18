try:
    from src.agents.docker_agents import DockerWriterA
    from src.agents.k8s_agents import K8sWriterA
    from src.agents.prompt_improvement_agent import PromptImprover
    import langchain
    import langchain_google_genai
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
