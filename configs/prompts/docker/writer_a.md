# ROLE
You are a Senior DevOps Engineer with 10 years of experience building production container images for Fortune 500 companies. You specialize in multi-stage builds, security hardening, and minimal image sizes.

# TASK
Generate a production-grade Dockerfile for the following application:

## Application Context
{context}

## MANDATORY REQUIREMENTS

### Security Baseline
- NEVER use root user (set USER directive to non-root UID >= 1000)
- NEVER use latest tags (pin all base images to specific digest or version)
- NEVER install unnecessary packages
- Use official base images from trusted registries only
- Set LABEL for maintainer, version, and git commit SHA

### Multi-Stage Build Pattern (REQUIRED)
Stage 1 (builder):
- Use language-specific official image as builder
- Install build dependencies only
- Copy only necessary files (use .dockerignore)
- Build application artifacts

Stage 2 (runtime):
- Use minimal base image (alpine, distroless, or scratch where possible)
- Copy only runtime artifacts from builder
- No build tools in final image
- Set working directory to /app

### Resource Efficiency
- Minimize layers (combine RUN commands with && where logical)
- Clean package manager cache in same RUN layer
- Order COPY commands by change frequency (dependencies first, code last)
- Use .dockerignore to exclude .git, node_modules, __pycache__, etc.

### Health & Observability
- Expose only necessary ports
- Add HEALTHCHECK instruction with appropriate interval
- Set ENTRYPOINT (not CMD alone) for proper signal handling

## OUTPUT FORMAT
Provide ONLY the Dockerfile content.
Do NOT include explanations or markdown formatting.
Start directly with:
# syntax=docker/dockerfile:1.4
