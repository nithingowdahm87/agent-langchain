# Kubernetes Guidelines

## Security
- Pod-level securityContext: runAsNonRoot, fsGroup, seccompProfile: RuntimeDefault
- Container-level securityContext: allowPrivilegeEscalation: false, drop ALL capabilities
- readOnlyRootFilesystem: true — always add emptyDir volumes for /tmp and /var/run
- Never run privileged containers or use hostNetwork / hostPID
- Namespace must have Pod Security Standard label: enforce: restricted
- Dedicated ServiceAccount per app, automountServiceAccountToken: false

## Resources
- CPU and memory requests AND limits mandatory on every container
- Requests = limits for critical services (Guaranteed QoS)

## Availability
- Minimum 2 replicas for all production workloads
- RollingUpdate: maxUnavailable: 0
- preStop sleep hook required (sleep 15) for zero-downtime deploys
- terminationGracePeriodSeconds >= 60
- All three probes required: startupProbe, livenessProbe, readinessProbe
- Liveness: slow failure (failureThreshold: 3, periodSeconds: 30)
- Readiness: fast fail (failureThreshold: 2, periodSeconds: 10)
- HPA: CPU target 70%, scaleDown stabilization 300s
- PodDisruptionBudget: minAvailable: 1
- TopologySpread across zones and nodes

## Networking
- Default deny-all NetworkPolicy required in every namespace
- DNS egress (UDP+TCP port 53) MUST be explicitly allowed — pods cannot start without it
- Database pods must not accept traffic from public internet
- No NodePort — ClusterIP only for services, Ingress or Istio for external traffic

## Resource Types
- Deployments  : long-running stateless services
- StatefulSets : stateful apps (databases)
- Jobs         : one-off tasks (migrations)
- CronJobs     : scheduled tasks (backups)
