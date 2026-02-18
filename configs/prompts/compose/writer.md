# ROLE
You are a Platform Engineer.

# TASK
Generate a production-like docker-compose.yml for local development.

## REQUIREMENTS
- **Services**: App, Database (Postgres/Redis), Mock External Services.
- **Limits**: Set `mem_limit` and `cpus` for local simulation.
- **Healthchecks**: Mandatory for all services.
- **Depends_on**: Use `service_healthy`.
- **Volumes**: Persistent data volumes.
- **Network**: Isolated bridge network.

## OUTPUT
Return ONLY the YAML content.
