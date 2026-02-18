# Kubernetes Guidelines

## General
- All Pods must have CPU and memory requests and limits.
- Use readiness and liveness probes where applicable.
- Do not run containers as privileged or as root when avoidable.
- Use labels: `app`, `component`, `environment`.
- Prefer Deployment + Service; add Ingress only when needed.

## NetworkPolicy
- **Default Deny**: Implement a "default deny-all" policy for the namespace.
- **Allow List**: Explicitly allow traffic between specific components (e.g., Frontend -> Backend -> DB).
- **Egress**: Restrict egress traffic to necessary external services.
- **Isolation**: Database pods should NOT accept traffic from the public internet.

## RBAC (Role-Based Access Control)
- **ServiceAccount**: Create a specific ServiceAccount for each app. Do NOT use `default`.
- **Least Privilege**: Grant only necessary permissions via Role/RoleBinding.
- **AutomountServiceAccountToken**: Set to `false` if the pod doesn't need API access.

## Jobs vs Deployments
- **Deployments**: For long-running stateless services (APIs, frontends).
- **StatefulSets**: For stateful apps (Databases).
- **Jobs**: For one-off tasks (DB migrations, batch processing).
- **CronJobs**: For scheduled tasks (backups).
