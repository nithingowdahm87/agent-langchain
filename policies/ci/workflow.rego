package main

import rego.v1

# Deny unpinned GitHub Actions
deny contains msg if {
    job := input.jobs[job_name]
    step := job.steps[i]
    uses := step.uses
    not contains(uses, "@")
    msg := sprintf("CI: Step '%s' in job '%s' uses unpinned action '%s'. Pin to version or SHA.", [step.name, job_name, uses])
}

# Warn about pull_request_target trigger
warn contains msg if {
    trigger := input.on
    trigger.pull_request_target
    msg := "CI: 'pull_request_target' trigger detected. This can expose secrets to untrusted code."
}

# Deny workflows without timeout
warn contains msg if {
    job := input.jobs[job_name]
    not job["timeout-minutes"]
    msg := sprintf("CI: Job '%s' has no timeout-minutes. Add a timeout to prevent hung runs.", [job_name])
}

# Deny workflows that checkout untrusted code with elevated permissions
deny contains msg if {
    job := input.jobs[job_name]
    job.permissions.contents == "write"
    step := job.steps[_]
    contains(step.uses, "actions/checkout")
    input.on.pull_request_target
    msg := sprintf("CI: Job '%s' checks out code with write permissions on pull_request_target. This is a critical security risk.", [job_name])
}
