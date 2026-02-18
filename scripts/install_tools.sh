#!/bin/bash
set -e

BIN_DIR="$(pwd)/bin"
mkdir -p "$BIN_DIR"

# Kubeconform (Validation)
KUBECONFORM_VERSION="v0.6.4"
if [ ! -f "$BIN_DIR/kubeconform" ]; then
    echo "⬇️  Installing kubeconform $KUBECONFORM_VERSION..."
    wget -q https://github.com/yannh/kubeconform/releases/download/$KUBECONFORM_VERSION/kubeconform-linux-amd64.tar.gz
    tar xf kubeconform-linux-amd64.tar.gz kubeconform
    mv kubeconform "$BIN_DIR/"
    rm kubeconform-linux-amd64.tar.gz
    chmod +x "$BIN_DIR/kubeconform"
    echo "✅ kubeconform installed to $BIN_DIR/kubeconform"
else
    echo "✅ kubeconform already exists."
fi

# Hadolint (Dockerfile Linting)
if [ ! -f "$BIN_DIR/hadolint" ]; then
    echo "⬇️  Installing hadolint..."
    wget -q -O "$BIN_DIR/hadolint" https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
    chmod +x "$BIN_DIR/hadolint"
    echo "✅ hadolint installed to $BIN_DIR/hadolint"
else
    echo "✅ hadolint already exists."
fi
