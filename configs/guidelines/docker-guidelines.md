# Docker Guidelines

- NEVER use :latest — pin to major.minor minimum (node:20-alpine)
- Multi-stage builds mandatory for any compiled or transpiled application
- Non-root user required (UID >= 10001) — recreate in RUNTIME stage, not just builder
- HEALTHCHECK required in every production image
- WORKDIR must be set explicitly (/app) in all stages
- COPY must be explicit — NEVER COPY . . in any stage
- .dockerignore must be generated alongside every Dockerfile
- OCI labels (org.opencontainers.image.*) required with ARG-injected values
- No build tools, shells, or debug utilities in final stage
- CMD and ENTRYPOINT must use exec form (JSON array)
- Cache cleaning must happen in same RUN layer OR via BuildKit cache mount
- readOnlyRootFilesystem compatible: /tmp and /var/run must use emptyDir volumes
- Signal handling: tini required for Python; exec node directly for Node.js
- Layer order: FROM → user setup → manifests → install → config → source → build
