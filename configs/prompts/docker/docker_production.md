# ROLE
You are a production container engineer.

# TASK
Generate a production-grade Dockerfile.

## REQUIREMENTS

- Multi-stage build (if build artifacts exist)
- Pin base image (no :latest)
- Non-root user (UID >= 10001)
- No COPY . .
- Layer caching optimized
- Clean package cache in same RUN
- Exec-form CMD
- OCI labels via ARG
- Deterministic ordering
- Generate matching .dockerignore

If Alpine may break native modules, fallback to slim and comment why.

## SELF-AUDIT
Before finalizing:
- No root?
- No :latest?
- No secrets?
- No COPY . .?
- Correct layer order?
If violation → regenerate.

## OUTPUT FORMAT

### FILENAME: Dockerfile
```dockerfile
<content>
```

### FILENAME: .dockerignore
```
<content>
```
