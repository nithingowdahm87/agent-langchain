package main

import rego.v1

# Deny :latest or unpinned FROM tags
deny contains msg if {
    input[i].Cmd == "from"
    val := input[i].Value[0]
    not contains(val, ":")
    msg := sprintf("Dockerfile: FROM '%s' has no pinned version tag (line %d)", [val, i + 1])
}

deny contains msg if {
    input[i].Cmd == "from"
    val := input[i].Value[0]
    endswith(val, ":latest")
    msg := sprintf("Dockerfile: FROM '%s' uses :latest tag. Pin to specific version (line %d)", [val, i + 1])
}

# Deny running as root (no USER instruction)
deny contains msg if {
    not any_user_instruction
    msg := "Dockerfile: No USER instruction found. Container will run as root."
}

any_user_instruction if {
    input[i].Cmd == "user"
}

# Warn if no HEALTHCHECK
warn contains msg if {
    not any_healthcheck
    msg := "Dockerfile: No HEALTHCHECK instruction. Add one for production readiness."
}

any_healthcheck if {
    input[i].Cmd == "healthcheck"
}

# Deny ADD when COPY would suffice
warn contains msg if {
    input[i].Cmd == "add"
    val := concat(" ", input[i].Value)
    not startswith(val, "http")
    not endswith(val, ".tar")
    not endswith(val, ".gz")
    msg := sprintf("Dockerfile: Prefer COPY over ADD for local files (line %d)", [i + 1])
}
