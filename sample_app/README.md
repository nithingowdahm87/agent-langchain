# Sample App (React + Node + Postgres)

This directory contains a multi-container application to test the DevOps Agent's capabilities.

## Architecture
- **Frontend**: React (Vite) running on port 5173
- **Backend**: Node.js (Express) running on port 3000
- **Database**: PostgreSQL (containerized)

## How to Test the Agent
Since the agent focuses on one service at a time, run it twice:

### 1. Generate Backend Infrastructure
1. Run `python main.py`
2. Enter Path: `/home/nithin/devops-agent/sample_app/backend`
3. Select **Stage 4 (K8s)**.
4. Observe **Job** (for DB init), **NetworkPolicy** (isolating DB), and **RBAC**.
5. Select **Stage 3 (Compose)** to generate backend + DB stack.

### 2. Generate Frontend Infrastructure
1. Run `python main.py`
2. Enter Path: `/home/nithin/devops-agent/sample_app/frontend`
3. Select **Stage 2 (Dockerfile)** and **Stage 5 (CI/CD)**.

## Manual Run (Without Agent)
1. `cd backend && npm install && npm start`
2. `cd frontend && npm install && npm run dev`
3. Ensure Postgres is running locally.
