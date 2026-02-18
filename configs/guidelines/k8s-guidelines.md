# Kubernetes Guidelines

- All Pods must have CPU and memory requests and limits.
- Use readiness and liveness probes where applicable.
- Do not run containers as privileged or as root when avoidable.
- Use labels: app, component, environment.
- Prefer Deployment + Service; add Ingress only when needed.
