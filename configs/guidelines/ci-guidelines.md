# CI Guidelines

## Structure (Critical)
- Each pipeline stage = one separate job under `jobs:` — never all stages as steps in one job
- `needs:` is a job-level key — never place it inside a `steps:` block
- A step must have EITHER `run:` OR `uses:` — never both in the same step

## Authentication
- Docker login step required BEFORE any docker/build-push-action step
- OIDC preferred over static IAM credentials (aws-actions/configure-aws-credentials)
- All secrets via ${{ secrets.XYZ }} — zero hardcoded values anywhere

## Actions
- Pin all actions to specific version tags: actions/checkout@v4 (NOT @master or @latest)
- Correct branch context: ${{ github.ref_name }} (NOT ${{ github.branch }} — invalid)
- Correct Gitleaks action: gitleaks/gitleaks-action@v2 (not zricethezav CLI binary)

## Security Scan Order
Secrets scan → SAST → DAST → Build → Image scan → Notify

## Image Immutability
- Tags must include github.sha: myapp:sha-${{ github.sha }}
- provenance: false required on docker/build-push-action for ArgoCD compatibility

## Pipeline Hygiene
- Define concurrency group to cancel duplicate runs on same branch
- Permissions block: minimal (contents: read at minimum)
- Trivy: report CRITICAL and HIGH severity only
- Notify job: if: always() — must run even on pipeline failure
- No direct kubectl apply — GitOps via ArgoCD handles all deployments
