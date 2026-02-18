# Terraform Guidelines

- Use a remote backend with state locking where possible.
- Use meaningful resource naming conventions.
- Avoid hardcoding secrets; load from variables or secret stores.
- Prefer modules for reusable pieces (network, cluster, etc.).
