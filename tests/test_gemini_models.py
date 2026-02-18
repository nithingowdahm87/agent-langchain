#!/usr/bin/env python3
"""Test different Gemini models to check specific quotas."""
import os
import requests

api_key = "AIzaSyBTimeZyjMvNwv3AVB9E9o43z9YHctpTxo"

models = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-1.0-pro"
]

print(f"Testing API Key: {api_key[:10]}...")

for model in models:
    print(f"\n{'='*40}")
    print(f"Testing Model: {model}")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": "Say hello in one word"}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS!")
            print(f"Response: {response.json()['candidates'][0]['content']['parts'][0]['text']}")
        else:
            print("❌ FAILED")
            print(f"Error: {response.text[:300]}")
            
    except Exception as e:
        print(f"Exception: {e}")
