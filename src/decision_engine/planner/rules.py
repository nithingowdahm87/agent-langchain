from src.schemas import ProjectContext

def detect_service_type(context: ProjectContext) -> str:
    """
    Deterministically decide if this is an API, Worker, Monolith, etc.
    based on dependencies and detected artifacts.
    """
    # 1. Check for API frameworks
    api_frameworks = ["fastapi", "flask", "django", "express", "nestjs", "gin", "echo", "spring-boot"]
    deps_str = str(context.dependencies).lower()
    
    is_api = any(fw in deps_str for fw in api_frameworks) or context.ports
    
    # 2. Check for Worker patterns (celery, bull, kafka consumers)
    worker_libs = ["celery", "bull", "kafka", "rabbitmq", "sqs"]
    is_worker = any(lib in deps_str for lib in worker_libs)
    
    # Heuristics
    if is_api and is_worker:
        return "monolith" # Likely a monolithic service handling both
    if is_api:
        return "api"
    if is_worker:
        return "worker"
    
    # Default fallback
    return "monolith"

def determine_scaling(service_type: str) -> str:
    if service_type == "api":
        return "horizontal" # HPA
    if service_type == "worker":
        return "queue" # KEDA or just replica count based on queue depth (advanced)
    return "manual"

def needs_database(context: ProjectContext) -> bool:
    db_drivers = ["psycopg2", "pg", "mysql", "mongodb", "mongoose", "sqlalchemy", "typeorm"]
    return any(d in str(context.dependencies).lower() for d in db_drivers)

def needs_cache(context: ProjectContext) -> bool:
    cache_drivers = ["redis", "memcached"]
    return any(d in str(context.dependencies).lower() for d in cache_drivers)
