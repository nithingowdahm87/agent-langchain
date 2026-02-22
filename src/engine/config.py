import os

MAX_RETRIES = 3
TIMEOUT_SECONDS = 120

# Severity thresholds
TRIVY_SEVERITY = ["CRITICAL", "HIGH"]

# File detection mapping
FILE_TYPE_MAP = {
    "Dockerfile": "docker",
    ".dockerignore": "dockerignore",
    ".yml": "yaml",
    ".yaml": "yaml"
}

REPORT_DIR = "reports"
GENERATED_DIR = "generated"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
