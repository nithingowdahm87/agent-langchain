# 🚀 DevOps AI Agent Pipeline

> A self-correcting, multi-agent DevOps platform that automatically generates production-grade infrastructure files for any codebase — powered by 4 LLM providers working in parallel.

---

## 📖 Table of Contents

- [What Is This?](#-what-is-this)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup Instructions](#-setup-instructions)
- [How to Run](#-how-to-run)
- [The 7 Pipeline Stages](#-the-7-pipeline-stages)
- [How Input & Output Works](#-how-input--output-works)
- [LLM Clients](#-llm-clients)
- [Configuration & Guidelines](#-configuration--guidelines)
- [Mock Mode (Offline Testing)](#-mock-mode-offline-testing)
- [Troubleshooting](#-troubleshooting)

---

## 🤔 What Is This?

This is an **AI-powered DevOps pipeline** that takes any application codebase and generates:

| Output | File Generated |
|--------|---------------|
| Code Analysis | `.devops_context.json` |
| Dockerfile | `Dockerfile` |
| Docker Compose | `docker-compose.yml` |
| Kubernetes Manifests | `manifest.yaml` |
| CI/CD Workflows | `.github/workflows/main.yml` |
| Monitoring Stack | `helm/monitoring/Chart.yaml` |
| Incident Reports | `debug_reports/incident_*.md` |

**In one command**, point it at your code and it generates everything you need for production deployment.

---

## 🏗️ Architecture

### High-Level Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION CODEBASE                        │
│                     (Node.js / Python / Go / etc.)                      │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
                   ┌──────────────────────────┐
                   │   STAGE 1: CODE ANALYSIS  │
                   │   (CodeAnalysisAgent)      │
                   │   Scans files, detects:    │
                   │   • Language & Framework   │
                   │   • Ports & Env Vars       │
                   │   • Dependencies           │
                   └────────────┬───────────────┘
                                │
                                ▼
              ┌──────────────────────────────────────┐
              │     .devops_context.json              │
              │     ════════════════════              │
              │     THE SHARED BRAIN / CACHE          │
              │                                      │
              │  {                                   │
              │    "project_name": "my-app",         │
              │    "language": "javascript/node",    │
              │    "ports": ["3000"],                │
              │    "env_vars": ["MONGO_URI"],        │
              │    "dependencies": ["express"],      │
              │    "frameworks": ["express"]          │
              │  }                                   │
              │                                      │
              │  ⚡ Created ONCE, read by ALL stages  │
              │  🗑️  Delete this file to force rescan │
              └──┬────┬────┬────┬────┬────┬──────────┘
                 │    │    │    │    │    │
                 ▼    ▼    ▼    ▼    ▼    ▼
              Stage  Stage Stage Stage Stage Stage
                2     3     4     5     6     7
```

---

### The Core Engine: 3 Writers → 1 Reviewer → Human Decision

**Every single stage (2 through 7)** runs through this exact same engine. The only thing that changes is *what* is being generated.

```
══════════════════════════════════════════════════════════════════════
                    THE AGENT ENGINE (per stage)
══════════════════════════════════════════════════════════════════════

  .devops_context.json ──────────────────────────────────┐
                                                         │
  ┌──────────────────────────────────────────────────────┐│
  │              STEP 1: PARALLEL GENERATION             ││
  │                                                      ││
  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
  │  │   WRITER A      │  │   WRITER B      │  │   WRITER C      │
  │  │   ═══════════   │  │   ═══════════   │  │   ═══════════   │
  │  │                 │  │                 │  │                 │
  │  │  LLM: Gemini    │  │  LLM: Groq      │  │  LLM: NVIDIA    │
  │  │  Focus: General │  │  Focus: Security │  │  Focus: Speed   │
  │  │  Best Practices │  │  Hardening       │  │  Performance    │
  │  │                 │  │                 │  │                 │
  │  │  Reads context ◄┘  │  Reads context ◄┘  │  Reads context ◄┘
  │  │  + guidelines   │  │  + guidelines   │  │  + guidelines   │
  │  │                 │  │                 │  │                 │
  │  │  OUTPUT:        │  │  OUTPUT:        │  │  OUTPUT:        │
  │  │  Draft A        │  │  Draft B        │  │  Draft C        │
  │  └───────┬─────────┘  └───────┬─────────┘  └───────┬─────────┘
  │          │                    │                    │
  └──────────┼────────────────────┼────────────────────┘
             │                    │                    │
             ▼                    ▼                    ▼
  ┌──────────────────────────────────────────────────────┐
  │            STEP 2: DETERMINISTIC VALIDATION          │
  │                                                      │
  │  Runs BEFORE AI review to catch objective errors:    │
  │                                                      │
  │  • Hadolint  → Dockerfile syntax & best practices    │
  │  • Kubeval   → K8s YAML schema validation            │
  │                                                      │
  │  OUTPUT: Validation Report (errors per draft)        │
  │                                                      │
  │  Example:                                            │
  │  "Draft A: ⚠️ DL3018 - Pin versions in apk add"     │
  │  "Draft B: ✅ No errors found"                       │
  │  "Draft C: ⚠️ DL3025 - Use JSON for CMD"            │
  └──────────────────────┬───────────────────────────────┘
                         │
                         ▼
  ┌──────────────────────────────────────────────────────┐
  │            STEP 3: AI REVIEWER (Perplexity)          │
  │                                                      │
  │  RECEIVES:                                           │
  │  • Draft A (from Gemini)                             │
  │  • Draft B (from Groq)                               │
  │  • Draft C (from NVIDIA)                             │
  │  • Validation Report (from linters)                  │
  │  • Guidelines (from configs/)                        │
  │                                                      │
  │  DOES:                                               │
  │  1. Compares all 3 drafts                            │
  │  2. Picks the best elements from each                │
  │  3. Fixes any linter errors from the report          │
  │  4. Merges into ONE final output                     │
  │  5. Explains reasoning (WHY this choice)             │
  │                                                      │
  │  OUTPUT:                                             │
  │  • Final merged file content                         │
  │  • Reasoning points (bullet list)                    │
  └──────────────────────┬───────────────────────────────┘
                         │
                         ▼
  ┌──────────────────────────────────────────────────────┐
  │            STEP 4: HUMAN APPROVAL GATE               │
  │                                                      │
  │  The system SHOWS you:                               │
  │  • The AI's reasoning                                │
  │  • The proposed file content                         │
  │                                                      │
  │  Then asks: ✅ Approve and Write? (y/n)              │
  │                                                      │
  │  ┌─────────────────────────────────────────────┐     │
  │  │  "y" (YES)  →  Executor writes file to disk │     │
  │  │                 ✅ Done. Back to menu.        │     │
  │  ├─────────────────────────────────────────────┤     │
  │  │  "n" (NO)   →  Output is DISCARDED          │     │
  │  │                 ❌ Nothing is written.        │     │
  │  │                 Returns to menu.             │     │
  │  ├─────────────────────────────────────────────┤     │
  │  │  REFINE     →  You type feedback             │     │
  │  │  ("r")         "Add health check"            │     │
  │  │                 System re-runs the review    │     │
  │  │                 with your feedback injected  │     │
  │  │                 into the next cycle.         │     │
  │  │                 🔄 Loop up to 3 times.       │     │
  │  └─────────────────────────────────────────────┘     │
  │                                                      │
  │  Refine is available on ALL stages (2-7).            │
  │  Prompt: ✅ Approve (y) / 🔄 Refine (r) / ❌ Reject (n) │
  └──────────────────────┬───────────────────────────────┘
                         │ (if approved)
                         ▼
  ┌──────────────────────────────────────────────────────┐
  │            STEP 5: EXECUTOR                          │
  │                                                      │
  │  Writes the final approved content to disk.          │
  │  Each stage writes to a specific path:               │
  │                                                      │
  │  Stage 2 → {project}/Dockerfile                      │
  │  Stage 3 → {project}/docker-compose.yml              │
  │  Stage 4 → {project}/manifest.yaml                   │
  │  Stage 5 → {project}/.github/workflows/main.yml      │
  │  Stage 6 → {project}/helm/monitoring/Chart.yaml      │
  │  Stage 7 → {project}/debug_reports/incident_*.md     │
  └──────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════
```

---

### Stage-by-Stage Writer Breakdown

Every stage has **3 writers**, each with a unique perspective. Here is exactly who does what:

#### Stage 2: Dockerfile Generation

| Role | LLM | Class | What It Generates |
|------|-----|-------|-------------------|
| **Writer A** | Google Gemini | `DockerWriterA` | Standard multi-stage Dockerfile with caching |
| **Writer B** | Groq (LLaMA) | `DockerWriterB` | Security-hardened Dockerfile (non-root, minimal base) |
| **Writer C** | NVIDIA (Mixtral) | `DockerWriterC` | Performance-optimized Dockerfile (layer caching, size) |
| **Reviewer** | Perplexity | `DockerReviewer` | Merges best of A+B+C, fixes Hadolint errors |
| **Validator** | Hadolint | `DeterministicReviewer` | Catches syntax issues before AI review |

#### Stage 3: Docker Compose

| Role | LLM | Class | What It Generates |
|------|-----|-------|-------------------|
| **Writer A** | Google Gemini | `DockerComposeWriter` | Standard compose with app + detected services |
| **Writer B** | Groq (LLaMA) | `DockerComposeWriter` | Compose with security env vars and networks |
| **Writer C** | NVIDIA (Mixtral) | `DockerComposeWriter` | Compose with resource limits and health checks |
| **Reviewer** | Perplexity | `ComposeReviewer` | Merges into single production-ready yml |

#### Stage 4: Kubernetes Manifests

| Role | LLM | Class | What It Generates |
|------|-----|-------|-------------------|
| **Writer A** | Google Gemini | `K8sWriterA` | Standard Deployment + Service |
| **Writer B** | Groq (LLaMA) | `K8sWriterB` | Security-focused (Pod Security, resource limits) |
| **Writer C** | NVIDIA (Mixtral) | `K8sWriterC` | Scalability-focused (HPA, probes, PDB) |
| **Reviewer** | Perplexity | `K8sReviewer` | Merges best of A+B+C, fixes Kubeval errors |
| **Validator** | Kubeval | `DeterministicReviewer` | Validates YAML against K8s schema |

#### Stage 5: CI/CD (GitHub Actions)

| Role | LLM | Class | What It Generates |
|------|-----|-------|-------------------|
| **Writer A** | Google Gemini | `CIWriterA` | Standard CI: lint, test, build |
| **Writer B** | Groq (LLaMA) | `CIWriterB` | Security CI: Trivy scan, secret detection |
| **Writer C** | NVIDIA (Mixtral) | `CIWriterC` | Fast CI: aggressive caching, parallel jobs |
| **Reviewer** | Perplexity | `CIReviewer` | Merges into single comprehensive workflow |

#### Stage 6: Observability (Helm)

| Role | LLM | Class | What It Generates |
|------|-----|-------|-------------------|
| **Writer A** | Google Gemini | `ObservabilityWriterA` | Standard Prometheus + Loki + Grafana chart |
| **Writer B** | Groq (LLaMA) | `ObservabilityWriterB` | Hardened monitoring with persistence |
| **Writer C** | NVIDIA (Mixtral) | `ObservabilityWriterC` | Lightweight monitoring (minimal footprint) |
| **Reviewer** | Perplexity | `ObservabilityReviewer` | Merges into production-grade Chart.yaml |

#### Stage 7: Debugging & Troubleshooting

| Role | LLM | Class | What It Analyzes |
|------|-----|-------|------------------|
| **Writer A** | Google Gemini | `DebugWriterA` | Root Cause Analysis (RCA) |
| **Writer B** | Groq (LLaMA) | `DebugWriterB` | Security implications of the error |
| **Writer C** | NVIDIA (Mixtral) | `DebugWriterC` | Performance bottlenecks |
| **Reviewer** | Perplexity | `DebugReviewer` | Synthesizes Incident Report with remediation steps |

---

### The Human Decision Flow (Detailed)

```
                    ┌─────────────────────────┐
                    │  AI Reviewer presents:  │
                    │  • Reasoning points     │
                    │  • Final proposed file   │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │  ✅ Approve? (y/n)       │
                    └───┬───────┬─────────────┘
                        │       │
              ┌─────────┘       └──────────┐
              ▼                            ▼
     ┌─────────────────┐         ┌─────────────────┐
     │    YES ("y")     │         │     NO ("n")    │
     │                  │         │                 │
     │ What happens:    │         │ What happens:   │
     │ 1. Executor runs │         │ 1. Output is    │
     │ 2. File is       │         │    DISCARDED    │
     │    written to    │         │ 2. Nothing is   │
     │    your project  │         │    written      │
     │ 3. "✅ Wrote     │         │ 3. Returns to   │
     │    Dockerfile"   │         │    main menu    │
     │ 4. Returns to    │         │ 4. You can      │
     │    main menu     │         │    re-run the   │
     │                  │         │    stage again   │
     └─────────────────┘         └─────────────────┘

     ═══════════════════════════════════════════════
     ALL STAGES: Refinement Loop (up to 3 cycles)
     ═══════════════════════════════════════════════

     If you press "r" (Refine) on ANY stage:

  ┌──────────────┐
  │ REFINE FLOW  │
  │              │
  │ 1. You type  │
  │    feedback: │
  │    "Add      │
  │    healthchk"│
  │              │
  │ 2. Feedback  │
  │    injected  │
  │    into the  │
  │    AI prompt │
  │    as "USER  │
  │    FEEDBACK  │
  │    (MUST     │
  │    ADDRESS)" │
  │              │
  │ 3. System    │
  │    re-runs   │──────► Back to AI Reviewer
  │    the AI    │        with your feedback.
  │    review    │        Up to 3 cycles.
  │    cycle     │
  └──────────────┘

     ═══════════════════════════════════════════════
     GUIDELINES AUTO-LEARNING
     ═══════════════════════════════════════════════

     After each AI review, the system also runs:
     GuidelinesComplianceAgent.analyze_and_update()

     This extracts UNIVERSAL best practices from
     the AI's reasoning and appends them to the
     appropriate guidelines file:

       Stage 2,3 → configs/guidelines/docker-guidelines.md
       Stage 4,6 → configs/guidelines/k8s-guidelines.md
       Stage 5   → configs/guidelines/ci-guidelines.md

     Over time, the guidelines grow smarter with
     each pipeline run. The system LEARNS.
```

---

### Shared Context Cache (`.devops_context.json`)

This is the **single source of truth** that connects all stages:

```
                .devops_context.json
                ════════════════════

  CREATED BY:   Stage 1 (CodeAnalysisAgent)
  READ BY:      Stages 2, 3, 4, 5, 6, 7
  LOCATION:     {your_project_path}/.devops_context.json

  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │  Stage 1 ──WRITES──► .devops_context.json       │
  │                           │                     │
  │                    ┌──────┼──────┐               │
  │                    │      │      │               │
  │                    ▼      ▼      ▼               │
  │                 Stage   Stage  Stage             │
  │                  2,3    4,5    6,7               │
  │                 Docker  K8s   Monitor            │
  │                 +Comp   +CI   +Debug             │
  │                    │      │      │               │
  │                    ▼      ▼      ▼               │
  │              Dockerfile  manifst  Chart.yaml     │
  │              compose.yml main.yml incident.md    │
  │                                                 │
  └─────────────────────────────────────────────────┘

  WHY?
  • Avoids scanning the codebase 7 times
  • Each stage knows the language, ports, deps
  • Consistency: all files use the same port numbers
  • Speed: Stage 1 runs once, rest read from cache
```

---

### Full Pipeline Execution Flow

```
  YOU RUN: python3 main.py
       │
       ▼
  Enter project path: /path/to/app
       │
       ▼
  ╔═══════════════════════════════════════╗
  ║  STAGE 1: Code Analysis (auto-runs)  ║
  ║  Scans → .devops_context.json        ║
  ╚═══════════════╦═══════════════════════╝
                  ║
                  ▼
  ┌─────── Pipeline Menu ──────────────┐
  │                                    │
  │  2. [Docker]        Dockerfile     │
  │  3. [Compose]       docker-compose │
  │  4. [K8s]           manifest.yaml  │
  │  5. [CI/CD]         GitHub Actions │
  │  6. [Observability] Helm Chart     │
  │  7. [Debug]         Troubleshoot   │
  │  0. Exit                           │
  │                                    │
  │  You pick a number.                │
  │  That stage runs the engine:       │
  │  3 Writers → Validator → Reviewer  │
  │  → You approve → File written      │
  │  → Back to this menu.              │
  │                                    │
  │  Run stages in ANY ORDER.          │
  │  Run the SAME stage multiple times.│
  │  Exit when done.                   │
  └────────────────────────────────────┘
```

---

### LLM Provider Map

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                     LLM PROVIDER MAPPING                       │
  ├─────────────┬──────────────┬────────────┬──────────────────────┤
  │  ROLE       │  PROVIDER    │  MODEL     │  ENV VARIABLE        │
  ├─────────────┼──────────────┼────────────┼──────────────────────┤
  │  Writer A   │  Google      │  gemini-   │  GOOGLE_API_KEY      │
  │  (General)  │  Gemini      │  flash     │                      │
  ├─────────────┼──────────────┼────────────┼──────────────────────┤
  │  Writer B   │  Groq        │  llama-3.3 │  GROQ_API_KEY        │
  │  (Security) │  Cloud       │  -70b      │                      │
  ├─────────────┼──────────────┼────────────┼──────────────────────┤
  │  Writer C   │  NVIDIA      │  mixtral-  │  NVIDIA_API_KEY      │
  │  (Speed)    │  NIM         │  8x7b      │                      │
  ├─────────────┼──────────────┼────────────┼──────────────────────┤
  │  Reviewer   │  Perplexity  │  sonar-pro │  PERPLEXITY_API_KEY  │
  │  (Judge)    │  AI          │            │                      │
  ├─────────────┼──────────────┼────────────┼──────────────────────┤
  │  Fallback   │  Local       │  MockClient│  (no key needed)     │
  │  (Offline)  │              │            │                      │
  └─────────────┴──────────────┴────────────┴──────────────────────┘
```

## 📁 Project Structure

```
devops-agent/
├── main.py                         # 🎯 Entry point — the pipeline wizard
├── requirements.txt                # Python dependencies
├── validate_keys.py                # API key validation utility
│
├── src/
│   ├── agents/                     # 🤖 All pipeline stage agents
│   │   ├── code_analysis_agent.py      # Stage 1: Scans your codebase
│   │   ├── docker_agents.py            # Stage 2: Dockerfile generation
│   │   ├── docker_compose_agent.py     # Stage 3: Docker Compose generation
│   │   ├── k8s_agents.py              # Stage 4: Kubernetes manifests
│   │   ├── cicd_agent.py              # Stage 5: GitHub Actions workflows
│   │   ├── observability_agent.py     # Stage 6: Helm/Prometheus/Loki
│   │   ├── debugging_agent.py         # Stage 7: Error troubleshooting
│   │   ├── deterministic_reviewer.py  # Hadolint + Kubeval runner
│   │   ├── guidelines_compliance_agent.py  # Quality gate
│   │   └── prompt_improvement_agent.py     # Prompt refinement
│   │
│   ├── llm_clients/                # 🌐 LLM provider wrappers
│   │   ├── gemini_client.py        # Google Gemini (Writer A)
│   │   ├── groq_client.py          # Groq / LLaMA (Writer B)
│   │   ├── nvidia_client.py        # NVIDIA NIM (Writer C)
│   │   ├── perplexity_client.py    # Perplexity AI (Reviewer)
│   │   └── mock_client.py          # Offline testing mock
│   │
│   └── tools/                      # 🔧 Utilities
│       ├── context_gatherer.py     # Scans directory trees
│       ├── file_ops.py             # Read/write file helpers
│       └── shell_tools.py          # Shell command runner
│
├── configs/
│   └── guidelines/                 # 📋 Best practice guidelines
│       ├── docker-guidelines.md
│       ├── k8s-guidelines.md
│       ├── ci-guidelines.md
│       ├── shell-guidelines.md
│       ├── terraform-guidelines.md
│       └── test-guidelines.md
│
├── bin/                            # 🔨 Deterministic validator binaries
│   ├── hadolint                    # Dockerfile linter
│   └── kubeval                     # Kubernetes YAML validator
│
└── venv/                           # Python virtual environment
```

---

## ✅ Prerequisites

- **Python 3.10+**
- **pip** (comes with Python)
- **Git** (optional, for cloning)

### API Keys (Required for LIVE mode)

You need API keys from **4 providers**:

| Provider | Env Variable | Get Key |
|----------|-------------|---------|
| Google Gemini | `GOOGLE_API_KEY` | https://aistudio.google.com/apikey |
| Groq | `GROQ_API_KEY` | https://console.groq.com/keys |
| NVIDIA NIM | `NVIDIA_API_KEY` | https://build.nvidia.com |
| Perplexity | `PERPLEXITY_API_KEY` | https://www.perplexity.ai/settings/api |

> **💡 No API keys?** The system automatically falls back to **Mock Mode** for offline testing. See [Mock Mode](#-mock-mode-offline-testing).

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repo-url>
cd devops-agent
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up API Keys

Create a `.env` file in the project root:

```bash
cat > .env << 'EOF'
export GOOGLE_API_KEY="your-google-api-key"
export GROQ_API_KEY="your-groq-api-key"
export NVIDIA_API_KEY="your-nvidia-api-key"
export PERPLEXITY_API_KEY="your-perplexity-api-key"
EOF
```

Then source it:

```bash
source .env
```

### 5. Validate Keys (Optional)

```bash
venv/bin/python3 validate_keys.py
```

---

## ▶️ How to Run

### Interactive Mode (Recommended)

```bash
source venv/bin/activate
source .env  # if using real API keys
python3 main.py
```

You will see:

```
============================================================
🚀 DevOps AI Agent Pipeline v3.0
============================================================
Enter project path: /path/to/your/app

============================================================
🚀 Stage 1: Code Analysis & Caching
============================================================
✅ Context Loaded: javascript/node app, Ports: ['3000']

--- Pipeline Menu ---
2. [Docker] Generate Dockerfile
3. [Compose] Generate Docker Compose
4. [K8s] Generate Kubernetes Manifests
5. [CI/CD] Generate GitHub Actions
6. [Observability] Generate Helm/Monitoring
7. [Debug] Troubleshoot Errors
0. Exit
Run Stage: _
```

### Scripted Mode (For automation)

```bash
# Run stages 2, 3, 4 sequentially, auto-approve all
printf "/path/to/app\n2\ny\n3\ny\n4\ny\n0\n" | venv/bin/python3 main.py
```

---

## 🔄 The 7 Pipeline Stages

### Stage 1: Code Analysis (Automatic)

Runs automatically when you start the pipeline. Scans your codebase and creates a `.devops_context.json` cache.

**What it detects:**
- Programming language (Node.js, Python, Go, etc.)
- Package manager and dependencies
- Exposed ports
- Environment variables
- Framework (Express, Django, FastAPI, etc.)

**Output example** (`.devops_context.json`):
```json
{
  "project_name": "my-app",
  "language": "javascript/node",
  "ports": ["3000"],
  "env_vars": ["MONGO_URI", "API_KEY"],
  "dependencies": ["express", "mongoose"],
  "frameworks": ["express"]
}
```

> **Caching:** This file is cached. Delete it to force a re-scan.

---

### Stage 2: Dockerfile (Option `2`)

Generates a production-ready `Dockerfile`.

**Input:** `.devops_context.json` (automatic)
**Output:** `Dockerfile` in your project root
**Validation:** Hadolint lints the output before AI review.

**Refinement loop:** If you reject the output, you can provide feedback and the system re-generates.

---

### Stage 3: Docker Compose (Option `3`)

Generates `docker-compose.yml` with services for your app + detected databases.

**Input:** `.devops_context.json`
**Output:** `docker-compose.yml`
**Smart detection:** If your app uses MongoDB, Redis, or PostgreSQL, it auto-adds those services.

---

### Stage 4: Kubernetes Manifests (Option `4`)

Generates `deployment.yaml` + `service.yaml`.

**Input:** `.devops_context.json`
**Output:** `manifest.yaml`
**Validation:** Kubeval validates the YAML before AI review.

---

### Stage 5: CI/CD (Option `5`)

Generates GitHub Actions workflow.

**Input:** `.devops_context.json`
**Output:** `.github/workflows/main.yml`
**Steps generated:** Checkout → Lint → Test → Security Scan → Docker Build → Push (placeholder)

---

### Stage 6: Observability (Option `6`)

Generates Helm chart for monitoring stack.

**Input:** `.devops_context.json`
**Output:** `helm/monitoring/Chart.yaml`
**Includes:** Prometheus, Loki, Grafana as Helm dependencies.

---

### Stage 7: Debugging (Option `7`)

Analyzes error logs and generates incident reports.

**Input:** Paste error text OR provide path to a log file.
**Output:** `debug_reports/incident_<timestamp>.md`

**Example interaction:**
```
Provide the error/log to analyze.
Options:
  1. Paste error text directly
  2. Provide path to a log file
Choice (1/2): 1
Paste error (type END on a new line when done):
Error: MongooseServerSelectionError: connect ECONNREFUSED 127.0.0.1:27017
END
```

**3 specialists analyze your error:**
| Specialist | Focus |
|---|---|
| Writer A | Root Cause Analysis |
| Writer B | Security implications |
| Writer C | Performance bottlenecks |

The Lead SRE Reviewer synthesizes all 3 into a structured Incident Report with severity, root cause, and remediation steps.

---

## 📥 How Input & Output Works

### Data Flow Summary

```
Your Codebase
     │
     ▼
[Stage 1: Code Analysis]
     │
     ▼
.devops_context.json  ◄──── Shared cache, read by ALL stages
     │
     ├──► [Stage 2] → Dockerfile
     ├──► [Stage 3] → docker-compose.yml
     ├──► [Stage 4] → manifest.yaml
     ├──► [Stage 5] → .github/workflows/main.yml
     ├──► [Stage 6] → helm/monitoring/Chart.yaml
     └──► [Stage 7] → debug_reports/incident_*.md
```

### The Approval Loop

Every stage asks for your approval before writing files:

```
📄 Proposed Dockerfile:
FROM node:18-alpine
WORKDIR /app
...

✅ Approve and Write? (y/n): _
```

- **`y`** → Writes the file to disk
- **`n`** → Discards and returns to menu
- For Stage 2 (Docker), you also get a **Refine** option to provide feedback

---

## 🌐 LLM Clients

Each client wraps a different AI provider. They all implement the same interface:

```python
class Client:
    def call(self, prompt: str) -> str:
        # Send prompt, return response text
```

| Client | Provider | Model | Role |
|--------|----------|-------|------|
| `GeminiClient` | Google AI | `gemini-flash-latest` | Writer A |
| `GroqClient` | Groq Cloud | `llama-3.3-70b-versatile` | Writer B |
| `NvidiaClient` | NVIDIA NIM | `mistralai/mixtral-8x7b-instruct-v0.1` | Writer C |
| `PerplexityClient` | Perplexity AI | `sonar-pro` | AI Reviewer |
| `MockClient` | Local (no API) | N/A | Offline testing |

### Environment Variables

```bash
GOOGLE_API_KEY=...       # For GeminiClient
GROQ_API_KEY=...         # For GroqClient
NVIDIA_API_KEY=...       # For NvidiaClient
PERPLEXITY_API_KEY=...   # For PerplexityClient
```

---

## 📋 Configuration & Guidelines

Guidelines in `configs/guidelines/` are markdown files that teach the AI agents best practices. The agents read these before generating output.

| File | Used By |
|------|---------|
| `docker-guidelines.md` | Stage 2 (Dockerfile) |
| `k8s-guidelines.md` | Stage 4 (Kubernetes) |
| `ci-guidelines.md` | Stage 5 (CI/CD) |
| `shell-guidelines.md` | General |
| `terraform-guidelines.md` | Future use |
| `test-guidelines.md` | Future use |

### Quality Gate

The `GuidelinesComplianceAgent` automatically learns from AI Reviewer reasoning and updates guidelines with new best practices discovered during reviews.

---

## 🧪 Mock Mode (Offline Testing)

If API keys are missing, the system **automatically falls back** to `MockClient`. This means:

- ✅ The full pipeline flow still works
- ✅ All menu options are functional
- ✅ Files are generated with realistic placeholder content
- ⚠️ Output is pre-defined mock data, not AI-generated

**How to force Mock Mode:**
Simply don't set any API keys. The system will print:
```
⚠️  API Keys missing. Using MOCK clients.
```

This is useful for:
- Testing pipeline logic without spending API credits
- CI/CD environments where keys aren't available
- Learning how the system works

---

## 🔧 Troubleshooting

### "GOOGLE_API_KEY environment variable is not set"

```bash
# Make sure you sourced your .env file
source .env

# Verify it's set
echo $GOOGLE_API_KEY
```

### "ModuleNotFoundError: No module named 'langchain_google_genai'"

```bash
# Install inside the virtual environment
venv/bin/pip install langchain-google-genai
```

### Cache is stale / wrong language detected

```bash
# Delete the cache to force re-scan
rm /path/to/your/app/.devops_context.json
```

### Hadolint/Kubeval not found

The binaries should be in `bin/`. If missing:

```bash
# Hadolint
wget -O bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
chmod +x bin/hadolint

# Kubeval
wget https://github.com/instrumenta/kubeval/releases/download/v0.16.1/kubeval-linux-amd64.tar.gz
tar xf kubeval-linux-amd64.tar.gz -C bin/
chmod +x bin/kubeval
```

> **Note:** If validators are missing, the system gracefully skips linting and continues with AI-only review.

---

## 📄 License

See [LICENSE](LICENSE) for details.
