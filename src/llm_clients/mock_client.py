class MockClient:
    def __init__(self, name="MockAI"):
        self.name = name
    
    def call(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        print(f"  [MockClient:{self.name}] Received prompt length: {len(prompt)}")
        
        if "sonar-project.properties" in prompt_lower or ("opentelemetry" in prompt_lower and "tracing.js" in prompt_lower):
            return """
FILENAME: backend/sonar-project.properties
```properties
sonar.projectKey=backend
sonar.sources=src
sonar.exclusions=node_modules/**,tests/**
```

FILENAME: frontend/sonar-project.properties
```properties
sonar.projectKey=frontend
sonar.sources=src
sonar.exclusions=node_modules/**
```

FILENAME: backend/tracing.js
```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const sdk = new NodeSDK({ instrumentations: [getNodeAutoInstrumentations()] });
sdk.start();
```

FILENAME: .gitleaks.toml
```toml
[allowlist]
description = "Global allowlist"
```
"""

        if "github actions" in prompt_lower or "ci/cd" in prompt_lower:
            return """
name: CI/CD — DevSecOps Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  security-events: write

env:
  IMAGE_TAG: ${{ github.sha }}

jobs:
  # STAGE 1: COMPILE
  compile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Syntax Check (Frontend)
        run: cd frontend && npm install && node --check src/*.jsx
      - name: Syntax Check (Backend)
        run: cd backend && npm install && node --check index.js

  # STAGE 2: SECRET SCAN
  gitleaks-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
        env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }

  # STAGE 3: FILESYSTEM SCAN
  trivy-fs-scan:
    runs-on: ubuntu-latest
    needs: gitleaks-scan
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: fs
          scan-ref: .
          exit-code: '0'

  # STAGE 4: SONARQUBE (Parallel)
  sonar-frontend:
    runs-on: ubuntu-latest
    needs: trivy-fs-scan
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: SonarSource/sonarqube-github-action@master
        with: { projectBaseDir: frontend }
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN_FRONTEND }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

  sonar-backend:
    runs-on: ubuntu-latest
    needs: trivy-fs-scan
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: SonarSource/sonarqube-github-action@master
        with: { projectBaseDir: backend }
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN_BACKEND }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

  # STAGE 5: DOCKER BUILD (Parallel)
  docker-frontend:
    runs-on: ubuntu-latest
    needs: sonar-frontend
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: ./frontend
          push: true
          tags: ${{ vars.DOCKERHUB_USERNAME }}/frontend:${{ env.IMAGE_TAG }}

  docker-backend:
    runs-on: ubuntu-latest
    needs: sonar-backend
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: ./backend
          push: true
          tags: ${{ vars.DOCKERHUB_USERNAME }}/backend:${{ env.IMAGE_TAG }}

  # STAGE 6: IMAGE SCAN
  trivy-image-frontend:
    runs-on: ubuntu-latest
    needs: docker-frontend
    steps:
      - uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: ${{ vars.DOCKERHUB_USERNAME }}/frontend:${{ env.IMAGE_TAG }}

  trivy-image-backend:
    runs-on: ubuntu-latest
    needs: docker-backend
    steps:
      - uses: aquasecurity/trivy-action@0.28.0
        with:
          image-ref: ${{ vars.DOCKERHUB_USERNAME }}/backend:${{ env.IMAGE_TAG }}

  # STAGE 7: DAST
  owasp-zap:
    runs-on: ubuntu-latest
    needs: [trivy-image-frontend, trivy-image-backend]
    steps:
      - uses: zaproxy/action-baseline@v0.12.0
        with:
          target: ${{ secrets.APP_STAGING_URL }}

  # STAGE 8: NOTIFY
  notify:
    runs-on: ubuntu-latest
    if: always()
    needs: owasp-zap
    steps:
      - uses: 8398a7/action-slack@v3
        with:
          status: custom
          fields: repo,message,commit,author,action,eventName,ref,workflow,job,took
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
"""

        if "docker-compose" in prompt_lower:
            return """
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
  mongo:
    image: mongo:latest
    ports:
      - "27017:27017"
"""
        # "dockerfile" or "docker" but NOT "compose"
        if "dockerfile" in prompt_lower or ("docker" in prompt_lower and "build" in prompt_lower):
            return """
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
"""
        if "kubernetes" in prompt_lower and "review" not in prompt_lower:
            return """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 3000
"""
        if "helm" in prompt_lower or "observability" in prompt_lower:
            return """
apiVersion: v2
name: myapp-monitoring
version: 0.1.0
dependencies:
  - name: prometheus
    version: 15.0.0
"""

        # --- 3. DEBUG / ANALYSIS (Specific triggers) ---
        if "lead sre" in prompt_lower or "incident report" in prompt_lower:
             return """
REASONING:
- Primary issue is missing MongoDB connection configuration
- No security breach detected

REPORT:
## Incident Report
**Severity:** HIGH
**Root Cause:** Missing MONGO_URI environment variable
**Remediation:** Add MONGO_URI to environment
"""
        if "security" in prompt_lower and "engineer" in prompt_lower:
            return """
SECURITY_RISK: NO
ANALYSIS:
- No exposed secrets detected.
- Configuration issue only.
FIX:
```
Ensure MONGO_URI uses TLS.
```
"""

        # --- 4. GENERIC REVIEW (Last Resort) ---
        if "review" in prompt_lower:
            if "manifest" in prompt_lower or "kubernetes" in prompt_lower:
                return """
REASONING:
- Mock K8s review: valid structure
YAML:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
```
"""
            else:
                return """
REASONING:
- Mock Docker review: optimized layers
DOCKERFILE:
FROM node:alpine
"""
                
        return "Mock response"
