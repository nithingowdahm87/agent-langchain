class MockClient:
    def __init__(self, name="MockAI"):
        self.name = name
    
    def call(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        print(f"  [MockClient:{self.name}] Received prompt length: {len(prompt)}")
        
        # --- DEBUG-SPECIFIC (most specific first) ---
        if "lead sre" in prompt_lower or "incident report" in prompt_lower:
            return """
REASONING:
- Primary issue is missing MongoDB connection configuration
- No security breach detected
- Performance can be improved with connection pooling

REPORT:
## Incident Report
**Severity:** HIGH
**Root Cause:** Missing MONGO_URI environment variable causing startup crash
**Security Impact:** NO
**Performance Impact:** YES - no connection pooling

### Remediation Steps
1. Add MONGO_URI to environment configuration
2. Implement connection retry with exponential backoff
3. Configure connection pooling (poolSize: 10)
"""
        elif "root cause" in prompt_lower or ("incident" in prompt_lower and "review" not in prompt_lower):
            return """
SEVERITY: HIGH
ROOT_CAUSE: Application crashes due to unhandled promise rejection in database connection.
ANALYSIS:
- MongoDB connection string is missing from environment variables.
- The app attempts to connect on startup without retry logic.
FIX:
```
1. Add MONGO_URI to .env file
2. Add retry logic with exponential backoff
```
"""
        elif "security" in prompt_lower and "engineer" in prompt_lower:
            return """
SECURITY_RISK: NO
ANALYSIS:
- No exposed secrets detected in the error output.
- The connection failure is a configuration issue, not a security breach.
FIX:
```
Ensure MONGO_URI uses TLS and authentication.
```
"""
        elif "performance" in prompt_lower and "engineer" in prompt_lower:
            return """
PERF_ISSUE: YES
ANALYSIS:
- No connection pooling configured for MongoDB.
- Each request creates a new connection, causing latency spikes.
FIX:
```
Use mongoose connection pooling: { poolSize: 10 }
```
"""
        # --- INFRASTRUCTURE ---
        elif "docker-compose" in prompt_lower:
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
        elif "kubernetes" in prompt_lower and "review" not in prompt_lower:
            return """
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
    - port: 80
"""
        elif "github actions" in prompt_lower or "ci/cd" in prompt_lower:
            return """
name: CI/CD Pipeline
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: npm test
"""
        elif "helm" in prompt_lower or "observability" in prompt_lower:
            return """
apiVersion: v2
name: myapp-monitoring
description: Prometheus and Loki stack for myapp
type: application
version: 0.1.0
appVersion: "1.0.0"
dependencies:
  - name: prometheus
    version: 15.0.0
    repository: https://prometheus-community.github.io/helm-charts
  - name: loki
    version: 2.0.0
    repository: https://grafana.github.io/helm-charts
"""
        # --- GENERIC REVIEW (last resort) ---
        elif "review" in prompt_lower:
            if "manifest" in prompt_lower or "kubernetes" in prompt_lower:
                return """
REASONING:
- Mock K8s review: valid structure
- Mock K8s review: secure defaults

YAML:
```yaml
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
```
"""
            else:
                return """
REASONING:
- Mock Docker review: optimized layers
- Mock Docker review: non-root user

DOCKERFILE:
FROM node:18-alpine
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]
"""
        return "Mock response"
