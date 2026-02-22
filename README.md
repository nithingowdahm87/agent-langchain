# 🚀 DevOps AI Agent Pipeline v13.0

> A self-correcting, multi-agent DevOps platform that generates production-grade infrastructure files for any codebase — powered by 3 LLM providers working in parallel, with built-in policy enforcement, automatic microservice detection, and zero-pollution cleanup.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 Table of Contents

- [What Is This?](#-what-is-this)
- [Quick Start](#-quick-start)
- [V2 Auto-Pilot](#-v2-auto-pilot-mode)
- [Code Analysis Summary](#-code-analysis-summary)
- [The Pipeline Stages](#-the-pipeline-stages)
- [Production Features](#-production-features)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Version History](#-version-history)

---

## 🤔 What Is This?

Point this at **any codebase** and it automatically generates everything you need for production deployment — no config, no manual input for microservice paths.

| Stage | Output | Files Generated |
|-------|--------|-----------------|
| 1 | Code Analysis | *(in-memory, auto-cleaned)* |
| 2 | Dockerfiles | `<service>/Dockerfile` per microservice |
| 3 | Docker Compose | `docker-compose.yml` |
| 4 | K8s Manifests | `k8s/*.yaml` |
| 5 | CI/CD Pipeline | `.github/workflows/main.yml` |

> **Zero pollution**: `.devops_context.json` and `.devops_memory.json` are auto-deleted after the pipeline completes or exits.

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/nithingowdahm87/agent-langchain.git
cd agent-langchain

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Fill in GOOGLE_API_KEY, GROQ_API_KEY, NVIDIA_API_KEY
```

> **No API keys?** The system auto-falls back to **Mock Mode** — full pipeline runs with placeholder content.

### 3. Run

```bash
./run_agent.sh
```

Select **`1` → Auto-Pilot (V2)** to generate all DevOps artifacts automatically.

---

## 🧠 V2 Auto-Pilot Mode

The V2 pipeline is fully automated — no manual directory input required.

```
Enter project path: /your/app

--- Stage: Dockerfile ---       ← auto-detects backend/ and frontend/
--- Stage: Docker Compose ---   ← 3 LLMs compete, best draft wins
--- Stage: Kubernetes ---       ← generates per-resource YAML files
--- Stage: CI Pipeline ---      ← DevSecOps-grade GitHub Actions
```

### How It Works

```
YOUR CODEBASE
     │
     ▼
┌─────────────────────────┐
│  CodeAnalysisAgent       │  Scans dirs, detects services, tech, ports, DBs
└─────────────┬───────────┘
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
  Gemini    Groq    NVIDIA      ← 3 writers run in parallel (ThreadPoolExecutor)
     └────────┼────────┘
              │
     ┌────────▼────────┐
     │  Evaluator       │  Content-based heuristic scoring (security + best-practices)
     └────────┬────────┘
              │
     ┌────────▼────────┐
     │  Confidence Gate │  Auto-approve (≥80%) or recommend review (<80%)
     └────────┬────────┘
              │
     ┌────────▼────────┐
     │  File Writer     │  Writes FILENAME: blocks to correct paths
     └─────────────────┘
```

### LLM Provider Map

| Role | Provider | Model |
|------|----------|-------|
| Writer A (General) | Google Gemini | `gemini-1.5-flash` |
| Writer B (Security) | Groq | `llama-3.3-70b-versatile` |
| Writer C (Speed) | NVIDIA NIM | `mixtral-8x22b` |
| Fallback | MockClient | *(no key needed)* |

---

## 📋 Code Analysis Summary

Every run prints a rich analysis block before generating anything:

```
================================================================
  📋  CODE ANALYSIS SUMMARY
================================================================
  📁  Project       : sample_app
  🏛️   Architecture  : Microservices
  🐳  Dockerfiles   : 2 file(s) will be generated
  🔌  Port chain    : :3000  →  :5432  →  :5173

  ── MICROSERVICES ──────────────────────────────────────────────
  #1  backend/  —  REST API Server + DB Layer
       Language    : Node.js · Express
       Runtime     : Node.js 20
       Base image  : node:20-alpine
       Port chain  : :3000  →  :5432
       Key deps    : cors, dotenv, express, pg
       Uses DBs    : PostgreSQL

  #2  frontend/  —  Frontend Web App (SPA)
       Language    : Node.js · React · Vite
       Runtime     : Node.js 20
       Base image  : node:20-alpine → nginx:alpine (runtime)
       Port chain  : :5173
       Key deps    : react, react-dom

  ── DATABASES ────────────────────────────────────────────────
  🗄️   RDBMS   PostgreSQL            ← #1 backend
  ⚡  Cache   Redis                  ← #1 backend
  🍃  NoSQL   MongoDB                ← #2 worker
  📨  Broker  Kafka                  ← #3 events

================================================================
```

### What Gets Auto-Detected Per Service

| Field | How It's Detected |
|-------|-------------------|
| Role | Inferred from frameworks + deps + folder name |
| Language / Runtime | `package.json` engines, `.nvmrc`, `.python-version` |
| Base Image | Framework-appropriate (e.g. frontend → multi-stage with nginx) |
| Port chain | Scanned from `.js`/`.ts` source + `vite.config.js` |
| Databases | All prod deps matched against 30+ DB patterns |

### Supported Service Roles (Auto-Inferred)

`REST API Server + DB Layer` · `Frontend Web App (SPA)` · `Backend Worker / Message Consumer` · `API Gateway / Reverse Proxy` · `Authentication Service` · `Notification Service` · `Django Web Application` · `Python FastAPI Service` · more

### Supported Database Detection (30+)

| Category | Detected |
|----------|---------|
| 🗄️ RDBMS | PostgreSQL, MySQL, MariaDB, SQLite, CockroachDB, MS SQL Server, Oracle DB |
| ✦ ORM | Sequelize, TypeORM, Prisma, Knex, SQLAlchemy, Alembic |
| ⚡ Cache | Redis, Dragonfly, Valkey, KeyDB, Memcached |
| 🍃 NoSQL | MongoDB, Cassandra, Elasticsearch, OpenSearch, DynamoDB, Firestore, Firebase, CouchDB, Neo4j, InfluxDB, TimescaleDB, ArangoDB |
| 📨 Broker | Kafka, RabbitMQ, NATS, Bull/BullMQ, Celery |

---

## 🔄 The Pipeline Stages

### Stage 1: Code Analysis *(Automatic, Cached)*

Scans your project on first run and caches results. Detects:
- Language, frameworks, runtime versions
- All microservice directories + their individual tech stacks
- Ports from source code scanning
- Databases categorized by type (RDBMS / Cache / NoSQL / Broker)
- Environment variables, existing DevOps files

### Stage 2: Dockerfile *(Auto-Injected)*

For microservice projects, the correct subdirectory paths are **automatically** injected into the prompt — no manual input needed.

**Production-Grade Rules (20):** multi-stage builds, non-root user, pinned base images, no `:latest`, cache hygiene, `HEALTHCHECK`, exec-form `CMD`, OCI labels, no secrets in layers, `.dockerignore` enforced.

Output: `backend/Dockerfile`, `frontend/Dockerfile` (per detected service)

### Stage 3: Docker Compose

3 LLM writers generate competing `docker-compose.yml` drafts. The highest-scoring draft (content-based heuristics) is selected. You approve or edit.

### Stage 4: Kubernetes Manifests

Each K8s resource (Deployment, Service, Ingress, ConfigMap, Secrets, Namespace) is output as a **separate file** in `k8s/`.

### Stage 5: CI Pipeline

Generates `.github/workflows/main.yml` with:
- Test → Build → Security scan → Deploy stages
- Pinned action versions (policy-enforced)
- Docker image caching
- Multi-environment support

---

## 🏭 Production Features

### Confidence Scoring

Every generated artifact gets a real content-based score:

| Check | Points |
|-------|--------|
| Non-root user (`USER`/`adduser`) | +15 |
| No `:latest` image tags | +10 |
| Cache cleaned (`--no-cache`) | +10 |
| No secrets in image | +5 |
| Multi-stage build (`AS builder`) | +15 |
| `WORKDIR` set | +10 |
| Exec-form `CMD` | +10 |
| OCI labels | +5 |
| Model agreement bonus (2+ models agree) | +up to 20 |

**Score ≥ 80% → AUTO_APPROVE. Score < 80% → RECOMMEND_DRAFT (human review).**

### Policy Enforcement

| Stage | Built-in Rules |
|-------|----------------|
| Docker | No `:latest`, `USER` required, `HEALTHCHECK` recommended |
| K8s | Resource limits required, no `default` namespace, probes required |
| CI/CD | Pin action versions, require job timeouts |

### Secret Management

```
AWS Secrets Manager → HashiCorp Vault → Environment Variable
```

### GitOps Mode

```bash
# .env
GITHUB_TOKEN=your_token
GITHUB_REPO=owner/repo
```

Approved artifacts are opened as GitHub PRs instead of local writes.

---

## 📁 Project Structure

```
devops-agent/
├── run_agent.sh                          # One-command launcher (recommended)
├── main.py                               # Entry point
├── requirements.txt
├── .env.example
│
├── src/
│   ├── agents/
│   │   ├── code_analysis_agent.py        # Per-service detection, DB categorization
│   │   ├── cicd_agent.py
│   │   └── ...
│   │
│   ├── decision_engine/
│   │   ├── orchestrator.py               # V2 pipeline, rich summary, auto-cleanup
│   │   ├── planner.py                    # Architecture planning
│   │   ├── evaluator.py                  # Best-draft selector
│   │   ├── confidence/
│   │   │   └── confidence_score.py       # Heuristic content scoring
│   │   └── generator/
│   │       └── llm_generator.py          # Parallel LLM writer
│   │
│   ├── llm_clients/
│   │   ├── gemini_client.py              # gemini-1.5-flash
│   │   ├── groq_client.py
│   │   ├── nvidia_client.py
│   │   └── mock_client.py
│   │
│   ├── schemas.py                        # Pydantic models (ProjectContext)
│   └── utils/
│       ├── prompt_loader.py              # Safe template rendering (no KeyError)
│       ├── secrets.py
│       └── logger.py
│
└── configs/
    └── prompts/
        ├── dockerfile/
        │   ├── writer_a_generalist.md    # 20-rule production Dockerfile spec
        │   └── writer_b_security.md
        ├── docker_compose/
        ├── kubernetes/
        └── cicd/
```

---

## ⚙️ Configuration

```bash
# Required (for live generation)
GOOGLE_API_KEY=...
GROQ_API_KEY=...
NVIDIA_API_KEY=...

# Optional: GitOps PR mode
GITHUB_TOKEN=...
GITHUB_REPO=owner/repo

# Optional: Secrets backends
AWS_REGION=ap-south-1
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=...

# Optional: Logging
LOG_JSON=true
```

---

## 📊 Version History

| Version | Key Features |
|---------|-------------|
| v1–v3 | Single-writer pipeline → multi-writer + reviewer |
| v4.0 | Parallel writers, audit trail, structured logging |
| v6–v8 | K8s RBAC/NetworkPolicy, Helm monitoring, externalized prompts |
| v9.0 | Cloud cost estimation (FinOps) |
| v10.0 | Self-healing / auto-fix agent |
| v11.0 | Output organized into `k8s/`, `cost/` folders |
| v12.0 | V2 Decision Engine, Auto-Pilot mode, 8-stage DevSecOps pipeline |
| **v13.0** | **Auto microservice detection, per-service DB/port/role analysis, rich code analysis summary, 30+ DB types, heuristic confidence scoring, Gemini fix, zero-pollution auto-cleanup** |

---

## 📄 License

See [LICENSE](LICENSE) for details.
