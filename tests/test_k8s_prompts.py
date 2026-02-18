import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents.k8s_agents import K8sWriterA, K8sWriterB, K8sWriterC

def test_k8s_writer_a_context_includes_istio():
    with patch("src.agents.k8s_agents.GeminiClient") as MockClient:
        mock_llm = MockClient.return_value
        mock_llm.call.return_value = "yaml"
        
        writer = K8sWriterA()
        writer.generate("context")
        
        # Verify prompt contains check for keys
        args, _ = mock_llm.call.call_args
        prompt = args[0]
        assert "Istio" in prompt
        assert "VirtualService" in prompt

def test_k8s_writer_b_context_includes_network_policy():
    with patch("src.agents.k8s_agents.GroqClient") as MockClient:
        mock_llm = MockClient.return_value
        mock_llm.call.return_value = "yaml"
        
        writer = K8sWriterB()
        writer.generate("context")
        
        args, _ = mock_llm.call.call_args
        prompt = args[0]
        assert "NetworkPolicy" in prompt
        assert "Deny-All" in prompt

def test_k8s_writer_c_context_includes_ha():
    with patch("src.agents.k8s_agents.NvidiaClient") as MockClient:
        mock_llm = MockClient.return_value
        mock_llm.call.return_value = "yaml"
        
        writer = K8sWriterC()
        writer.generate("context")
        
        args, _ = mock_llm.call.call_args
        prompt = args[0]
        assert "Topology Spread" in prompt
        assert "highly-available" in prompt
