package main

import rego.v1

# Deny deployments to default namespace
deny contains msg if {
    input.kind == "Deployment"
    input.metadata.namespace == "default"
    msg := sprintf("K8s: Deployment '%s' targets 'default' namespace. Use a dedicated namespace.", [input.metadata.name])
}

deny contains msg if {
    input.kind == "Deployment"
    not input.metadata.namespace
    msg := sprintf("K8s: Deployment '%s' has no namespace. Specify a namespace explicitly.", [input.metadata.name])
}

# Deny containers without resource limits
deny contains msg if {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.resources.limits
    msg := sprintf("K8s: Container '%s' has no resource limits. Set CPU and memory limits.", [container.name])
}

# Deny containers without resource requests
warn contains msg if {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.resources.requests
    msg := sprintf("K8s: Container '%s' has no resource requests. Set CPU and memory requests.", [container.name])
}

# Warn if no readiness probe
warn contains msg if {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.readinessProbe
    msg := sprintf("K8s: Container '%s' has no readinessProbe. Add one for zero-downtime deployments.", [container.name])
}

# Warn if no liveness probe
warn contains msg if {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.livenessProbe
    msg := sprintf("K8s: Container '%s' has no livenessProbe. Add one for auto-healing.", [container.name])
}

# Deny privileged containers
deny contains msg if {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("K8s: Container '%s' is privileged. Remove privileged mode.", [container.name])
}

# Deny latest image tag
deny contains msg if {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    image := container.image
    endswith(image, ":latest")
    msg := sprintf("K8s: Container '%s' uses :latest image tag. Pin to specific version.", [container.name])
}
