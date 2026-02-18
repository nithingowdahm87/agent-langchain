#!/usr/bin/env python3
"""Validate API keys for all three services."""
import os
import sys

def test_perplexity():
    """Test Perplexity API key."""
    print("\n=== Testing Perplexity API ===")
    try:
        from src.llm_clients.perplexity_client import PerplexityClient
        client = PerplexityClient()
        response = client.call("Say 'Hello' in one word.")
        print(f"✅ Perplexity API works!")
        print(f"Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Perplexity API failed: {e}")
        return False

def test_google_ai():
    """Test Google AI Studio API key."""
    print("\n=== Testing Google AI Studio API ===")
    try:
        from src.llm_clients.gemini_client import GeminiClient
        client = GeminiClient()
        response = client.call("Say 'Hello' in one word.")
        print(f"✅ Google AI Studio API works!")
        print(f"Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Google AI Studio API failed: {e}")
        return False

def test_github_models():
    """Test GitHub Models API key."""
    print("\n=== Testing GitHub Models API ===")
    try:
        from src.llm_clients.github_models_client import GitHubModelsClient
        client = GitHubModelsClient()
        response = client.call("Say 'Hello' in one word.")
        print(f"✅ GitHub Models API works!")
        print(f"Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ GitHub Models API failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting API key validation...")
    print(f"PPLX_API_KEY: {'SET' if os.getenv('PPLX_API_KEY') else 'NOT SET'}")
    print(f"GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
    print(f"GITHUB_TOKEN: {'SET' if os.getenv('GITHUB_TOKEN') else 'NOT SET'}")
    
    results = {
        "Perplexity": test_perplexity(),
        "Google AI": test_google_ai(),
        "GitHub Models": test_github_models()
    }
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for service, status in results.items():
        status_str = "✅ WORKING" if status else "❌ FAILED"
        print(f"{service}: {status_str}")
    
    all_working = all(results.values())
    if all_working:
        print("\n🎉 All API keys are working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️  Some API keys failed validation.")
        sys.exit(1)
