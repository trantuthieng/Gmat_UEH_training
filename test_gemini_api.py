#!/usr/bin/env python3
"""Test google-genai API with new Client API"""
import google.genai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

print(f"🔍 API Key loaded: {API_KEY[:20]}..." if API_KEY else "❌ API Key not found")

try:
    # Create client with google-genai v1.56+
    client = genai.Client(api_key=API_KEY)
    print("✅ Client created successfully")
    
    # Test simple API call
    print("\n🧪 Testing generate_content...")
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents="Say 'Hello from Gemini 2.5 Pro!' in exactly 5 words or less."
    )
    
    print(f"✅ Response: {response.text}")
    print("\n✅ API test passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
