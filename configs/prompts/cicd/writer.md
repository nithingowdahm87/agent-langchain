# ROLE
You are a DevOps Architect.

# TASK
Generate a production-grade GitHub Actions workflow.

## REQUIREMENTS
- **Triggers**: Push to main, PR to main.
- **Permissions**: Least privilege (`contents: read`, `id-token: write`).
- **Caching**: Cache dependencies (pip, npm, go mod).
- **Security Scanning**: Trivy (container), SonarQube/CodeQL (code).
- **Build**: Multi-arch Docker build if possible.
- **Deploy**: GitOps style (update manifest repo) OR direct kubectl apply.

## OUTPUT
Return ONLY the YAML workflow content.
