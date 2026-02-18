import requests
import json

api_key = "AIzaSyBTimeZyjMvNwv3AVB9E9o43z9YHctpTxo"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data.get('models', []))} models.")
        for model in data.get('models', []):
            name = model.get('name')
            methods = model.get('supportedGenerationMethods', [])
            if "generateContent" in methods:
                print(f"✅ {name}")
            else:
                print(f"❌ {name} (Methods: {methods})")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Exception: {e}")
