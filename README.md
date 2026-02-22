# 🚀 DevOps AI Agent Pipeline v14.0 [Solo-Copilot Edition]

> A highly deterministic, locally-executing DevOps file writer powered by an LLM copilot. It generates production-grade infrastructure files (Docker, Kubernetes, CI/CD), automatically passes them through static linters (`hadolint`, `kubeconform`, `actionlint`), and self-repairs errors. 

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 Table of Contents

- [What Is This?](#-what-is-this)
- [Quick Start](#-quick-start)
- [Architecture & Design](#-architecture--design)
- [The File Writers](#-the-file-writers)
- [Validation & Self-Healing](#-validation--self-healing)
- [Requirements](#-requirements)

---

## 🤔 What Is This?

This tool acts as a **Senior DevOps Engineer's brain extension**. Instead of a bulky multi-agent system, v14 is focused purely on **deterministic file generation**, strict local linting, and automatic healing.

You tell it to generate `docker`, `k8s`, or `ci` files. It parses your local context (Node, Python, Go, Terraform, etc.), generates the boilerplate, and importantly, **refuses to write invalid code**.

| Stage | What It Does | Handled By |
|-------|--------------|------------|
| 1 | Extract Context | Detects language, version, architecture |
| 2 | Generate Files | Uses 1 of 5 "Elite" Prompts |
| 3 | Static Lints | `hadolint`, `kubeconform`, `actionlint` |
| 4 | Auto-Heal | Feeds lint errors back to LLM for patching |
| 5 | Format | Runs `yq` to sort YAML deterministically |

---

## ⚡ Quick Start

### 1. Install Dependencies
You need local strict linters installed for the engine to validate the LLM outputs.
```bash
brew install hadolint    # For Docker
brew install kubeconform # For Kubernetes
brew install yq          # For YAML determinism
npm install -g actionlint # For CI/CD
```

### 2. Configure LLM
```bash
cp .env.example .env
# Ensure GEMINI_API_KEY (or preferred LLM client keys) are set.
```

### 3. Run the Agent
```bash
# Run the local engine against a target directory
python3 agent.py docker
# or 
python3 agent.py k8s
# or
python3 agent.py ci
```

---

## 🧠 Architecture & Design

The repository was drastically simplified in v14 to remove hallucination-prone multi-agent merges.

```
devops-agent/
├── agent.py              ← The single CLI entry point
├── src/engine/
│   ├── context.py        ← Repo metadata extraction
│   ├── llm.py            ← Wraps LLM generation with elite prompts
│   ├── validate.py       ← Subprocess calls to real linters
│   └── heal.py           ← The 3-retry auto-correction loop
└── configs/prompts/      ← 5 Elite Prompts
```

### Why Local Static Linters?
LLMs are bad at syntax perfection. Instead of relying purely on prompt engineering, this tool validates the LLM's output against actual tools. If `hadolint` complains that you aren't pinning a package manager cache, the `heal.py` agent reads that error and fixes the Dockerfile automatically.

---

## 📝 The File Writers ("5 Elite Prompts")

All scattered prompts were consolidated into 5 high-quality, strict templates that enforce consistency and security:

1. **`system_core.md`**: Enforces strict determinism, least privilege, zero `:latest` tags, and fail-closed mentalities.
2. **`docker_production.md`**: Enforces multi-stage, non-root `UID >= 10001`, strict `.dockerignore` parity, and BuildKit.
3. **`k8s_production.md`**: Generates full manifests with `PodDisruptionBudgets`, `HorizontalPodAutoscalers`, `readOnlyRootFilesystem`, and `seccompProfile: RuntimeDefault`.
4. **`cicd_production.md`**: Enforces split jobs, `needs` dependency mapping, OIDC over static secrets, and deep security scanning tools.
5. **`healer.md`**: A precision-diff prompt used when a linter fails, designed to change *only* what is broken.

---

## 🛡 Validation & Self-Healing

The core engine loop (in `agent.py`):
1. **Drafts** a file.
2. **Validates** the file.
3. **Fails?** Takes the `stderr` string and feeds it to `Healer`.
4. **Retries?** Up to 3 times per file.
5. **Success?** Formats keys alphabetically (where applicable) to reduce git diff noise.

---

## 📋 Version History

| Version | Key Features |
|---------|-------------|
| v10–v12 | Parallel writers, V2 Auto-Pilot, multi-agent evaluation. |
| v13.0 | Auto microservice detection, database parsing. |
| **v14.0** | **Massive simplification. Removed multi-agent hallucination. Added Local Engine (`context`, `llm`, `validate`, `heal`). Consolidated 20+ prompts into 5 Elite Prompts. Added strict static linter enforcement.** |

## 📄 License
MIT License.
