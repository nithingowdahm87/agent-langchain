import requests
import time

api_key = "AIzaSyBTimeZyjMvNwv3AVB9E9o43z9YHctpTxo"
models_to_test = [
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite"
]

print(f"Testing API Key: {api_key[:10]}...")

for model in models_to_test:
    print(f"\n{'='*40}")
    print(f"Testing Model: {model}")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": "Say hello"}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS!")
            print(f"Response: {response.json()['candidates'][0]['content']['parts'][0]['text']}")
        else:
            print("❌ FAILED")
            # print(f"Error: {response.text[:200]}")
            if response.status_code == 429:
                print("Error: Quota Exceeded (429)")
            elif response.status_code == 404:
                print("Error: Model Not Found (404)")
            else:
                print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    time.sleep(1)
