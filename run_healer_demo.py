import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())
from src.agents.debugging_agent import SelfHealer

BROKEN_CODE = """
def calculate_sum(a, b)
    return a + b
"""

ERROR_LOG = "SyntaxError: expected ':'"

print("🔥 BROKEN CODE:")
print(BROKEN_CODE)
print(f"❌ ERROR: {ERROR_LOG}")
print("-" * 40)

# Mock GeminiClient to avoid API calls and deterministic output
with patch("src.agents.debugging_agent.GeminiClient") as MockClient:
    mock_llm = MockClient.return_value
    mock_llm.call.return_value = """
def calculate_sum(a, b):
    return a + b
"""
    
    print("🚑 Running SelfHealer...")
    healer = SelfHealer()
    fixed_code = healer.fix_code(BROKEN_CODE, ERROR_LOG)
    
    print("\n✅ FIXED CODE:")
    print(fixed_code)
    
    if ":" in fixed_code and "def calculate_sum(a, b):" in fixed_code:
        print("\nSUCCESS: Syntax error fixed.")
    else:
        print("\nFAILED: Setup error.")
