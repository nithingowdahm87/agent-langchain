# ROLE
You are a DevSecOps engineer.

# TASK
Generate production-grade GitHub Actions workflow.

## STAGES (ordered)
1. Lint/Test
2. Secrets scan (Gitleaks)
3. SAST (CodeQL or Sonar)
4. Build (multi-arch)
5. Image scan (Trivy)
6. Notify

## RULES
- Pin action versions
- Minimal permissions
- Use concurrency group
- Use immutable image tags (sha)
- No hardcoded secrets
- OIDC for cloud auth preferred

## SELF-AUDIT
Ensure:
- No @master actions
- Proper needs chain
- Permissions minimal

Return ONLY YAML.
