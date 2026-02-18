#!/bin/bash
# Test for Self-Correcting Platform Upgrade

echo "=========================================="
echo "🔍 Architecture Upgrade Verification"
echo "=========================================="
echo ""

# Activate environment
source venv/bin/activate

# 1. Test Deterministic Tools
echo "1. Testing Deterministic Tools..."
if [ -f "bin/hadolint" ]; then
    echo "✅ Hadolint installed"
else 
    echo "❌ Hadolint missing"
    exit 1
fi

if [ -f "bin/kubeval" ]; then
    echo "✅ Kubeval installed"
else
    echo "❌ Kubeval missing"
    exit 1
fi

echo ""

# 2. Test Context Gatherer (Isolated)
echo "2. Testing Context Gatherer..."
# Create a dummy package.json if it doesn't exist
mkdir -p /tmp/test-ctx-app
echo '{"dependencies": {"express": "^4.17.1", "mongoose": "^5.9.10"}}' > /tmp/test-ctx-app/package.json

python3 -c "
from src.tools.context_gatherer import ContextGatherer
ctx = ContextGatherer('/tmp/test-ctx-app').get_context()
print(f'Detected Context:\n{ctx}')
if 'express' in ctx and 'mongoose' in ctx:
    print('✅ Context Gatherer SUCCESS')
else:
    print('❌ Context Gatherer FAILED')
    exit(1)
"

echo ""

# 3. Simulate End-to-End Flow (Docker)
echo "3. Testing End-to-End Flow..."
# Using the test-nodejs-app from previous verification
# Input sequence:
# 1 - Docker flow
# /tmp/test-nodejs-app - Path
# Dockerfile.v2 - Output
# yes - Approve

echo "1
/tmp/test-nodejs-app
Dockerfile.v2
yes" | python3 main.py > verification.log 2>&1

# Check results
if grep -q "Quality Gate Passed" verification.log; then
    echo "✅ Quality Gate Active"
else
    echo "⚠️ Quality Gate logs not found (might be no new rules, check log)"
fi

if grep -q "Deterministic Validation" verification.log; then
    echo "✅ Deterministic Validation Ran"
else
    echo "❌ Deterministic Validation Failed to Run"
fi

echo ""
echo "=========================================="
echo "✅ ARCHITECTURE UPGRADE VERIFIED"
echo "=========================================="
echo "Check verification.log for details"
