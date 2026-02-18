# 🚀 DevOps AI Agent Pipeline v12.0

> A self-correcting, multi-agent DevOps platform that generates production-grade infrastructure files for any codebase — powered by 4 LLM providers working in parallel, with built-in policy enforcement, audit trails, and GitOps publishing.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 Table of Contents

- [What Is This?](#-what-is-this)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [The Pipeline Stages](#-the-pipeline-stages)
- [Production Features](#-production-features)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Mock Mode](#-mock-mode-offline-testing)
- [Troubleshooting](#-troubleshooting)

---

## 🤔 What Is This?

Point this at **any codebase** and it generates everything you need for production deployment:

| Stage | Output | File Generated |
|-------|--------|----------------|
| 1 | Code Analysis | `.devops_context.json` |
| 2 | Dockerfile | `Dockerfile` |
| 3 | Docker Compose | `docker-compose.yml` |
| 4 | K8s Manifests | `manifest.yaml` |
| 5 | CI/CD Workflows | `.github/workflows/main.yml` |
| 6 | Monitoring Stack | `helm/monitoring/Chart.yaml` |
| 7 | Incident Reports | `debug_reports/incident_*.md` |
| 8 | Cost Estimate | `cost_estimate.md` |

---

## 🏗️ Architecture

### The Core Engine (Every Stage)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         YOUR CODEBASE                                │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Stage 1: Code Analysis │ ──► .devops_context.json
              └────────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  ┌───────────┐     ┌───────────┐     ┌───────────┐
  │ Writer A  │     │ Writer B  │     │ Writer C  │
  │ (Gemini)  │     │ (Groq)    │     │ (NVIDIA)  │
  │ General   │     │ Security  │     │ Speed     │
  └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
        │                  │                  │
        │    ⚡ Parallel via asyncio.to_thread │
        └──────────────────┼──────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Deterministic Linting  │  ◄── Hadolint / Kubeval
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  AI Reviewer           │  ◄── Perplexity (sonar-pro)
              │  Merges best of 3      │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  🛡️  Policy Gate        │  ◄── OPA/Conftest + Built-in Rules
              │  Docker: no :latest    │
              │  K8s: resource limits  │
              │  CI: pin actions       │
              └────────────┬───────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  👤 Human Decision     │  ◄── Approve / Refine / Reject
              │  (up to 3 cycles)      │
              └────────────┬───────────┘
                           │ (approved)
                           ▼
              ┌────────────────────────┐
              │  🚀 GitOps Publisher    │  ◄── PR via GitHub API
              │  OR local file write   │      or local write (default)
              └────────────────────────┘
```

### LLM Provider Map

| Role | Provider | Model | Env Variable |
|------|----------|-------|-------------|
| Writer A (General) | Google Gemini | gemini-flash | `GOOGLE_API_KEY` |
| Writer B (Security) | Groq | llama-3.3-70b | `GROQ_API_KEY` |
| Writer C (Speed) | NVIDIA NIM | mixtral-8x7b | `NVIDIA_API_KEY` |
| Reviewer (Judge) | Perplexity | sonar-pro | `PPLX_API_KEY` |
| Fallback | Local MockClient | — | *(no key needed)* |

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
# Edit .env with your API keys
source .env
```

> **💡 No API keys?** The system auto-falls back to **Mock Mode** — see [Mock Mode](#-mock-mode-offline-testing).

### 3. Run

```bash
python3 main.py
```

```
============================================================
🚀 DevOps AI Agent Pipeline v12.0
============================================================
Enter project path: /path/to/your/app

8. [Cost]          Cloud Cost Estimation
0. Exit
Run Stage: _
```

---

## 🔄 The Pipeline Stages

### Stage 1: Code Analysis *(Automatic)*

Scans your codebase and creates `.devops_context.json` — the shared brain read by all other stages.

**Detects:** Language, framework, ports, env vars, dependencies, package manager.

> Delete `.devops_context.json` to force a rescan.

### Stage 2: Dockerfile

3 writers generate competing Dockerfiles → AI reviewer merges the best → Hadolint validates
3- **🧠 V2 Decision Engine**: Deterministic architecture planning, multi-model consensus, and auto-repair loops.
- **🛡️ Security-First**: Generated artifacts (Dockerfiles, K8s manifests) adhere to strict security baselines (non-root, pinned versions).
- **🔧 Self-Healing**: Automated error detection and retry logic for LLM calls and validation failures.
- **🏗️ Microservices Support**: Automatically detects and handles complex microservice architectures. → Policy checks (no `:latest`, `USER` required, `HEALTHCHECK`) → You approve.

### Stage 3: Docker Compose

Generates `docker-compose.yml` with service definitions. Auto-detects databases (MongoDB, Redis, PostgreSQL) from your dependencies.

### Stage 4: Kubernetes Manifests

Generates `Deployment` + `Service` YAML → Kubeval validates schema → Policy checks (resource limits, namespace, probes) → You approve.

### Stage 5: CI/CD (GitHub Actions)

3 perspectives (general CI, DevSecOps, speed-optimized) merged into a single `.github/workflows/main.yml`. Policy checks ensure actions are pinned.

### Stage 6: Observability (Helm)

Generates a Helm chart with Prometheus, Loki, and Grafana as dependencies.

### Stage 7: Debugging

### Stage 8: Cloud Cost Estimation (FinOps)

Analyzes generated manifests to estimate monthly cloud spend (AWS/GCP/Azure) for compute, storage, and networking.

---

## 🏭 Production Features

### Phase 2: Security Hardening

| Feature | Module | What It Does |
|---------|--------|-------------|
| **Secrets Management** | `src/utils/secrets.py` | AWS Secrets Manager → HashiCorp Vault → env var fallback |
| **Retry + Backoff** | `src/utils/resilience.py` | 3 retries with exponential backoff on all LLM calls |
| **Input Sanitization** | `src/utils/sanitizer.py` | Strips prompt injection patterns and shell metacharacters |
| **Dependency Locking** | `requirements.in` | Source file for `pip-compile` reproducible builds |

### Phase 3: Auditability & Performance

| Feature | Module | What It Does |
|---------|--------|-------------|
| **Structured Logging** | `src/utils/logger.py` | JSON logs (production) or emoji console (dev). Set `LOG_JSON=true` |
| **Correlation IDs** | `src/utils/logger.py` | Every run gets a unique 8-char ID visible in all logs |
| **Parallel Writers** | `src/utils/parallel.py` | All 3 writers run concurrently via `asyncio.to_thread` (~3x speedup) |
| **Audit Trail** | `src/audit/decision_log.py` | Every approve/refine/reject saved to `audit_logs/<run_id>.json` |

### Phase 4: GitOps & Policy Enforcement

| Feature | Module | What It Does |
|---------|--------|-------------|
| **GitOps PR Model** | `src/gitops/pr_creator.py` | On approve → creates branch + PR via GitHub API. Falls back to local writes |
| **Policy Engine** | `src/policy/validator.py` | Built-in rules (always run) + OPA/Conftest (when installed) |
| **Rego Policies** | `policies/docker/`, `policies/k8s/`, `policies/ci/` | Declarative policy-as-code for each stage |

#### Policy Rules

| Stage | Built-in Rules |
|-------|---------------|
| Docker | No `:latest` tags, `USER` required, `HEALTHCHECK` recommended, prefer `COPY` over `ADD` |
| K8s | Resource limits required, no `default` namespace, probes required, no privileged containers |
| CI/CD | Pin action versions, warn on `pull_request_target`, require job timeouts |

#### Enabling GitOps Mode

```bash
# In .env — approved artifacts become PRs instead of local files
GITHUB_TOKEN=your_personal_access_token
GITHUB_REPO=owner/repo
GITHUB_BASE_BRANCH=main   # optional, defaults to main
```

### Phase 8: Production-Grade Prompts (v8.0)

| Feature | Details |
|---------|---------|
| **Prompt Library** | Externalized prompts in `configs/prompts/` |
| **Role Personas** | Enforces "Senior DevOps" constraints (Non-root, ReadOnly FS) |
| **Istio Support** | K8s agents now generate VirtualService/Gateway resources |

### Phase 9: FinOps (v9.0)

| Feature | Details |
|---------|---------|
| **Cost Awareness** | Estimates monthly spend for generated infrastructure |
| **Resource Logic** | Maps CPU/RAM requests to standard cloud instances |

### Phase 10: Self-Healing (v10.0)

| Feature | Details |
|---------|---------|
| **Auto-Fix** | `SelfHealer` agent applies patches to broken code |
| **Integration** | Seamlessly available in `Debug` stage after RCA |

### Phase 11: Output Organization (v11.0)

| Feature | Details |
|---------|---------|
| **Clean Structures** | Groups artifacts into `k8s/` and `cost/` folders |
| **Context Aware** | Keeps Dockerfiles in build roots for valid contexts |

### Phase 12: Enhanced Analysis (v12.0)

| Feature | Details |
|---------|---------|
| **Smart Detection** | Identifies microservices, cloud SDKs, and existing DevOps files |
| **Interactive** | Reports findings at startup & asks to Keep or Overwrite |

---

## 📁 Project Structure

```
devops-agent/
├── main.py                              # Entry point (v5.0)
├── requirements.in                      # pip-compile source
├── requirements.txt                     # Python dependencies
├── .env.example                         # All env vars documented
├── validate_keys.py                     # API key validator
│
├── src/
│   ├── agents/                          # 🤖 Pipeline stage agents
│   │   ├── code_analysis_agent.py           # Stage 1: scans codebase
│   │   ├── docker_agents.py                 # Stage 2: Dockerfile
│   │   ├── docker_compose_agent.py          # Stage 3: Compose
│   │   ├── k8s_agents.py                    # Stage 4: K8s manifests
│   │   ├── cicd_agent.py                    # Stage 5: GitHub Actions
│   │   ├── observability_agent.py           # Stage 6: Helm charts
│   │   ├── debugging_agent.py               # Stage 7: Incident analysis
│   │   ├── deterministic_reviewer.py        # Hadolint + Kubeval
│   │   └── guidelines_compliance_agent.py   # Auto-learning quality gate
│   │
│   ├── llm_clients/                     # 🌐 LLM provider wrappers
│   │   ├── gemini_client.py                 # Google Gemini
│   │   ├── groq_client.py                   # Groq / LLaMA
│   │   ├── nvidia_client.py                 # NVIDIA NIM
│   │   ├── perplexity_client.py             # Perplexity AI
│   │   └── mock_client.py                   # Offline testing
│   │
│   ├── utils/                           # 🔧 Production utilities
│   │   ├── secrets.py                       # Multi-backend secrets
│   │   ├── resilience.py                    # Retry + backoff
│   │   ├── sanitizer.py                     # Input sanitization
│   │   ├── logger.py                        # Structured JSON logging
│   │   └── parallel.py                      # Async parallel execution
│   │
│   ├── audit/                           # 📋 Compliance
│   │   └── decision_log.py                  # Per-run audit trail
│   │
│   ├── gitops/                          # 🚀 GitOps publishing
│   │   └── pr_creator.py                    # GitHub PR creator
│   │
│   ├── policy/                          # 🛡️ Policy engine
│   │   └── validator.py                     # Built-in + Conftest
│   │
│   └── tools/                           # File/shell helpers
│       ├── file_ops.py
│       ├── context_gatherer.py
│       └── shell_tools.py
│
├── policies/                            # OPA Rego policies
│   ├── docker/dockerfile.rego
│   ├── k8s/manifests.rego
│   └── ci/workflow.rego
│
├── configs/guidelines/                  # Auto-learning best practices
│   ├── docker-guidelines.md
│   ├── k8s-guidelines.md
│   └── ci-guidelines.md
│
└── bin/                                 # Deterministic validators
    ├── hadolint
    └── kubeval
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required (for live mode)
GOOGLE_API_KEY=...
GROQ_API_KEY=...
NVIDIA_API_KEY=...
PPLX_API_KEY=...

# Optional: GitOps PR mode
GITHUB_TOKEN=...
GITHUB_REPO=owner/repo

# Optional: Secrets backends
AWS_REGION=ap-south-1
DEVOPS_AGENT_SECRET_NAME=devops-agent/llm-keys
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=...

# Optional: Logging
LOG_JSON=true   # JSON output for production
```

### Guidelines (Auto-Learning)

Guidelines in `configs/guidelines/` teach the AI best practices. The `GuidelinesComplianceAgent` automatically learns from AI reviewer reasoning and appends new best practices discovered during reviews.

### Installing Conftest (Optional)

For OPA Rego policy enforcement beyond built-in rules:

```bash
# macOS
brew install conftest

# Linux
wget https://github.com/open-policy-agent/conftest/releases/download/v0.46.0/conftest_0.46.0_Linux_x86_64.tar.gz
tar xzf conftest_0.46.0_Linux_x86_64.tar.gz
sudo mv conftest /usr/local/bin/
```

> Without conftest, built-in policy rules still run. Conftest adds deeper, declarative Rego-based validation.

---

## 🧪 Mock Mode (Offline Testing)

If API keys are missing, the system **auto-falls back** to `MockClient`:

- ✅ Full pipeline flow works
- ✅ All menu options functional
- ✅ Files generated with realistic placeholder content
- ⚠️ Output is pre-defined mock data, not AI-generated

**How to force Mock Mode:** Don't set API keys. The system prints:
```
⚠️ API Keys missing. Using MOCK clients.
```

---

## 🔧 Troubleshooting

### "GOOGLE_API_KEY environment variable is not set"

```bash
source .env
echo $GOOGLE_API_KEY  # verify it's set
```

### "ModuleNotFoundError: No module named 'langchain_google_genai'"

```bash
pip install -r requirements.txt
```

### Cache is stale / wrong language detected

```bash
rm /path/to/your/app/.devops_context.json
```

### Hadolint/Kubeval not found

The system gracefully skips linting and continues with AI-only review. To install:

```bash
# Hadolint
wget -O bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
chmod +x bin/hadolint

# Kubeval
wget https://github.com/instrumenta/kubeval/releases/download/v0.16.1/kubeval-linux-amd64.tar.gz
tar xf kubeval-linux-amd64.tar.gz -C bin/
chmod +x bin/kubeval
```

---

## 📊 Version History

| Version | Codename | Key Features |
|---------|----------|-------------|
| v1.0 | — | Basic single-writer pipeline |
| v2.0 | — | Multi-writer + reviewer pattern |
| v3.0 | — | 7 stages + refinement loop + deterministic validation |
| v4.0 | Auditable | Structured logging, parallel writers, audit trail |
| v6.0 | **Runtime** | K8s Jobs, NetworkPolicy, RBAC added |
| v7.0 | **Ops** | Grafana Dashboards & Monitoring Stack |
| v8.0 | **Pro Prompts** | Externalized Prompt Library + Role Personas |
| v9.0 | **FinOps** | Cloud Cost Estimation Agent |
| v10.0 | **Self-Healing** | Auto-Fix capabilities in Debug Stage |
| v11.0 | **Organized** | Clean output structure (`k8s/`, `cost/`) |
| v12.0 | **Auto-Pilot** | V2 Decision Engine, Real/Mock Mode switching, 8-stage DevSecOps Pipeline |

---

## 📄 License

See [LICENSE](LICENSE) for details.
