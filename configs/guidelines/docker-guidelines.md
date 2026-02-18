# Docker Guidelines

- Do not use :latest tags, always pin base image versions.
- Use multi-stage builds when compiling or building artifacts.
- Copy only the required files from builder stage into runtime stage.
- Use a non-root user in the final stage.
- Set WORKDIR explicitly.
- Add HEALTHCHECK when possible.
