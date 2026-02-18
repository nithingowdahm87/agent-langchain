# CI Guidelines

- Use a build and test job that runs on push and pull_request to main branches.
- Cache dependencies where possible to speed up builds.
- Fail fast on lint and tests.
- Do not hardcode secrets; use GitHub Secrets.
