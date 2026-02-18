import sys
import os
sys.path.append(os.getcwd())

from src.agents.cost_agent import CostEstimator
from unittest.mock import MagicMock, patch

# Mock the LLM for demonstration without API keys
with patch("src.agents.cost_agent.GeminiClient") as MockClient:
    mock_llm = MockClient.return_value
    mock_llm.call.return_value = """
| Resource Type | Details | Estimated Monthly Cost |
|---|---|---|
| **Compute** | 3 Replicas x (0.5 vCPU, 1Gi RAM) -> AWS t3.small (~$20/mo) | ~$60.00 |
| **Storage** | 100Gi gp3 EBS volume | ~$10.00 |
| **LoadBalancer** | 1 AWS ALB | ~$18.00 |

**Total Estimated Monthly Cost**: ~$88.00 - $100.00

**Recommendations**:
- Use Spot instances for backend replicas to save ~50%.
- Review PVC size; 100Gi might be overprovisioned.
"""
    
    print("Running Cost Estimator on Sample Manifest (Mocked Mode)...")
    SAMPLE_MANIFEST = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: backend:v1
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-lb
spec:
  type: LoadBalancer
  ports:
  - port: 80
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
"""

    print("Running Cost Estimator on Sample Manifest...")
    print("-" * 40)
    print(SAMPLE_MANIFEST)
    print("-" * 40)

    try:
        estimator = CostEstimator()
        report = estimator.estimate(SAMPLE_MANIFEST)
        print("\nREPORT GENERATED:\n")
        print(report)
        
        with open("cost_estimate_sample.md", "w") as f:
            f.write(report)
            
    except Exception as e:
        print(f"Error: {e}")
