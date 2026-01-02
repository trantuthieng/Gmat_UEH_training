from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Lấy API key
try:
    import streamlit as st
    API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY not found!")
    exit(1)

print(f"✅ API Key found: {API_KEY[:10]}...")

# Khởi tạo client
client = genai.Client(api_key=API_KEY)

# Test các model đang sử dụng
models_to_test = [
    'gemini-3-flash',      # study guide
    'gemma-3-27b-it',      # question generation
    'gemini-2.5-flash-lite'  # ingest_pdf fallback / long text
]

print("\n🧪 Testing Gemini Models...\n")

for model_name in models_to_test:
    print(f"Testing: {model_name}")
    print("-" * 50)
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Trả lời ngắn gọn: 2+2 bằng bao nhiêu?"
        )
        
        result_text = response.text if hasattr(response, 'text') else str(response)
        print(f"✅ SUCCESS: {result_text[:100]}")
        
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            print(f"❌ FAILED: Model không tồn tại")
        elif "quota" in error_msg.lower() or "429" in error_msg:
            print(f"⚠️  FAILED: Vượt quota/rate limit")
        else:
            print(f"❌ FAILED: {error_msg[:100]}")
    
    print()

print("\n✅ Test hoàn tất!")
