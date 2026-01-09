"""
Simple test for Gemini models using the correct API format
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Get API key
try:
    import streamlit as st
    API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY not found!")
    exit(1)

print(f"✅ API Key found: {API_KEY[:20]}...\n")

# Test với simple requests
import requests
import json
import time

MODELS = [
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-2.5-pro',
    'gemini-3-flash',
]

TEST_PROMPT = "Giải đáp một bài toán GMAT: Nếu x + y = 10 và x - y = 4, x bằng bao nhiêu?"

print("="*80)
print("🧪 TESTING GEMINI MODELS")
print("="*80)

results = {}

for model_name in MODELS:
    print(f"\nTesting: {model_name}")
    print("-" * 80)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": TEST_PROMPT}]}],
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            }
        ]
    }
    
    try:
        start = time.time()
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            params={"key": API_KEY},
            timeout=30
        )
        elapsed = time.time() - start
        
        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                answer = data['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ SUCCESS")
                print(f"Answer: {answer[:200]}...")
                
                results[model_name] = {
                    "status": "success",
                    "time": elapsed,
                    "answer_length": len(answer)
                }
            else:
                print(f"⚠️ No candidates in response")
                print(f"Response: {json.dumps(data, indent=2)[:500]}")
                results[model_name] = {"status": "no_candidates"}
        else:
            error_msg = response.text[:200]
            print(f"❌ ERROR {response.status_code}")
            print(f"Message: {error_msg}")
            results[model_name] = {"status": "error", "code": response.status_code}
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT after 30s")
        results[model_name] = {"status": "timeout"}
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")
        results[model_name] = {"status": "exception", "error": str(e)[:100]}

print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80)

successful = {k: v for k, v in results.items() if v.get('status') == 'success'}
if successful:
    print("\n✅ SUCCESSFUL MODELS:")
    for model, data in successful.items():
        print(f"  - {model}: {data['time']:.2f}s (Answer length: {data['answer_length']})")

failed = {k: v for k, v in results.items() if v.get('status') != 'success'}
if failed:
    print("\n❌ FAILED MODELS:")
    for model, data in failed.items():
        print(f"  - {model}: {data.get('status')} {data.get('code', '')}")

print("\n" + "="*80)
