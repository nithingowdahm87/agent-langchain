import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents.cost_agent import CostEstimator

def test_cost_estimator_uses_prompt_file():
    with patch("src.agents.cost_agent.GeminiClient") as MockClient:
        mock_llm = MockClient.return_value
        mock_llm.call.return_value = "| Resource | Cost |"
        
        estimator = CostEstimator()
        estimator.estimate("kind: Pod\nmetadata:\n  name: test")
        
        args, _ = mock_llm.call.call_args
        prompt = args[0]
        
        # Check if it loaded the role and task from writer.md
        assert "FinOps Engineer" in prompt
        assert "Estimate the monthly cloud cost" in prompt or "Analyze the provided Kubernetes manifests" in prompt
        assert "KUBERNETES MANIFESTS" in prompt

def test_cost_estimator_fallback():
    with patch("src.agents.cost_agent.GeminiClient") as MockClient:
        with patch("src.agents.cost_agent.read_file", side_effect=Exception("File not found")):
            mock_llm = MockClient.return_value
            mock_llm.call.return_value = "Report"
            
            estimator = CostEstimator()
            estimator.estimate("yaml")
            
            args, _ = mock_llm.call.call_args
            prompt = args[0]
            assert "Analyze these K8s manifests" in prompt
