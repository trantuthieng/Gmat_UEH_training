"""
Test và so sánh các Gemini models khác nhau
Evaluate từng model dựa trên 3 tiêu chí: Tốc độ, Chất lượng, Độ tin cậy
"""

import os
from dotenv import load_dotenv
import time
import json
from datetime import datetime
import requests

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

# ============= CÁC CÂU HỎI TEST =============
# Các câu hỏi mẫu từ GMAT cho test
TEST_QUESTIONS = [
    {
        "id": 1,
        "type": "Reading Comprehension",
        "question": "The author's main purpose in the passage is to:",
        "context": "Scientific research shows that plants communicate through underground fungal networks...",
        "expected_type": "Multiple choice answer with clear reasoning"
    },
    {
        "id": 2,
        "type": "Data Sufficiency",
        "question": "If x is a positive integer, is x divisible by 6? Statement 1: x is divisible by 2. Statement 2: x is divisible by 3.",
        "expected_type": "Clear logic about sufficiency"
    },
    {
        "id": 3,
        "type": "Problem Solving",
        "question": "A container has 2 liters of water and 1 liter of alcohol. If we remove 3/4 liter of the mixture and add 3/4 liter of water back, what is the final ratio of water to alcohol?",
        "expected_type": "Step-by-step solution"
    },
    {
        "id": 4,
        "type": "Critical Reasoning",
        "question": "Which of the following statements is most supported by the passage?",
        "context": "Economic indicators suggest that consumer spending is declining...",
        "expected_type": "Logical inference"
    }
]

# ============= CÁC MODEL CẦN TEST =============
MODELS_TO_TEST = [
    # Text-out models (khuyên dùng cho GMAT)
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.5-pro',
    'gemini-3-flash',
    'gemini-3-pro',
    # Other models (test thêm)
    'gemma-3-1b',
    'gemma-3-12b',
    'gemma-3-27b',
]

# ============= HELPER FUNCTIONS =============

def format_prompt(question_data):
    """Định dạng prompt cho test"""
    prompt = f"Đây là câu hỏi GMAT - {question_data['type']}:\n\n"
    
    if 'context' in question_data:
        prompt += f"Ngữ cảnh: {question_data['context']}\n\n"
    
    prompt += f"Câu hỏi: {question_data['question']}\n\n"
    prompt += "Trả lời chi tiết và rõ ràng. Giải thích từng bước tư duy của bạn."
    
    return prompt

def test_model(model_name, prompt, timeout=30):
    """Test một model với prompt cho trước"""
    try:
        start_time = time.time()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                response_text = data['candidates'][0]['content']['parts'][0]['text']
                return {
                    "success": True,
                    "model": model_name,
                    "response": response_text,
                    "time": elapsed,
                    "length": len(response_text)
                }
            else:
                return {
                    "success": False,
                    "model": model_name,
                    "error": "No candidates in response",
                    "time": elapsed
                }
        else:
            return {
                "success": False,
                "model": model_name,
                "error": f"API Error: {response.status_code} - {response.text[:100]}",
                "time": elapsed
            }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "model": model_name,
            "error": str(e),
            "time": elapsed
        }

def score_response(response_text):
    """
    Đánh giá chất lượng response
    0-100 dựa trên các tiêu chí:
    - Độ dài (không quá ngắn, không quá dài)
    - Có cấu trúc rõ ràng
    - Có giải thích chi tiết
    """
    score = 50  # Base score
    
    # Kiểm tra độ dài
    if 100 < len(response_text) < 2000:
        score += 20
    elif 50 < len(response_text) < 3000:
        score += 10
    
    # Kiểm tra cấu trúc
    if any(keyword in response_text for keyword in ['bước', 'vì', 'do đó', 'kết quả', 'đáp án']):
        score += 15
    
    # Kiểm tra tính logic
    if any(keyword in response_text for keyword in ['logic', 'lý do', 'giải thích', 'phân tích']):
        score += 15
    
    # Kiểm tra không có lỗi cơ bản
    if '<' not in response_text or '>' not in response_text:  # HTML-like tags
        score += 10
    
    return min(score, 100)

# ============= MAIN TEST =============

print("\n" + "="*80)
print("🧪 GEMINI MODELS COMPARISON TEST")
print("="*80)
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total Models: {len(MODELS_TO_TEST)}")
print(f"Test Questions: {len(TEST_QUESTIONS)}")
print("="*80 + "\n")

# Lưu kết quả
results = []

# Test mỗi model với mỗi câu hỏi
for q_idx, question in enumerate(TEST_QUESTIONS[:2], 1):  # Test với 2 câu hỏi đầu để tiết kiệm API
    print(f"\n📝 Question {q_idx}: {question['type']}")
    print("-" * 80)
    
    prompt = format_prompt(question)
    
    question_results = []
    
    for model_idx, model_name in enumerate(MODELS_TO_TEST, 1):
        print(f"  [{model_idx}/{len(MODELS_TO_TEST)}] Testing {model_name}...", end=" ")
        
        result = test_model(model_name, prompt)
        
        if result['success']:
            score = score_response(result['response'])
            result['score'] = score
            print(f"✅ (Score: {score}/100, Time: {result['time']:.2f}s)")
            print(f"       Response preview: {result['response'][:100]}...")
        else:
            print(f"❌ Error: {result['error'][:60]}")
        
        question_results.append(result)
    
    results.append({
        "question_id": question['id'],
        "question_type": question['type'],
        "results": question_results
    })

# ============= PHÂN TÍCH VÀ SO SÁNH =============

print("\n\n" + "="*80)
print("📊 ANALYSIS & RANKING")
print("="*80)

# Tổng hợp điểm từng model
model_scores = {}
model_times = {}
model_successes = {}

for q_result in results:
    for result in q_result['results']:
        model = result['model']
        
        if model not in model_scores:
            model_scores[model] = []
            model_times[model] = []
            model_successes[model] = 0
        
        if result['success']:
            model_scores[model].append(result.get('score', 0))
            model_times[model].append(result['time'])
            model_successes[model] += 1

# Tính trung bình
model_avg_score = {
    model: (sum(scores) / len(scores)) if scores else 0
    for model, scores in model_scores.items()
}

model_avg_time = {
    model: (sum(times) / len(times)) if times else 0
    for model, times in model_times.items()
}

# Sắp xếp theo điểm
ranked_models = sorted(model_avg_score.items(), key=lambda x: x[1], reverse=True)

print("\n🏆 RANKING BY QUALITY SCORE:")
print("-" * 80)
print(f"{'Rank':<6} {'Model':<30} {'Avg Score':<12} {'Avg Time':<12} {'Success Rate':<15}")
print("-" * 80)

for rank, (model, score) in enumerate(ranked_models, 1):
    avg_time = model_avg_time[model]
    success_count = model_successes[model]
    total_tests = len(model_scores[model])
    success_rate = (success_count / len(TEST_QUESTIONS[:2])) * 100 if TEST_QUESTIONS[:2] else 0
    
    print(f"{rank:<6} {model:<30} {score:<12.1f} {avg_time:<12.2f}s {success_rate:<14.0f}%")

print("\n⚡ RANKING BY SPEED:")
print("-" * 80)
speed_ranked = sorted(model_avg_time.items(), key=lambda x: x[1])
for rank, (model, time) in enumerate(speed_ranked, 1):
    score = model_avg_score.get(model, 0)
    print(f"{rank:<6} {model:<30} {time:<12.2f}s (Quality: {score:.1f}/100)")

print("\n" + "="*80)
print("💡 RECOMMENDATION:")
print("="*80)

if ranked_models:
    best_model = ranked_models[0][0]
    best_score = ranked_models[0][1]
    
    fastest_model = speed_ranked[0][0]
    fastest_time = speed_ranked[0][1]
    
    print(f"\n✨ Best Quality: {best_model} (Score: {best_score:.1f}/100)")
    print(f"⚡ Fastest: {fastest_model} (Time: {fastest_time:.2f}s)")
    
    # Recommendation logic
    print("\n🎯 RECOMMENDED MODELS FOR GMAT:")
    print("-" * 80)
    print(f"1. For Production Use: {best_model}")
    print(f"   Reason: Highest quality score, suitable for accurate GMAT answers")
    print(f"\n2. For Fast Response: {fastest_model}")
    print(f"   Reason: Fastest response time, good for real-time interactions")
    
    if best_score >= 70:
        print(f"\n3. Quality Status: ✅ APPROVED (Score >= 70)")
    else:
        print(f"\n3. Quality Status: ⚠️ NEEDS REVIEW (Score < 70)")

# Lưu kết quả vào file
output_file = "test_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "model_rankings": ranked_models,
        "model_scores": model_avg_score,
        "model_times": {k: v for k, v in model_avg_time.items()},
        "detailed_results": results
    }, f, indent=2, ensure_ascii=False)

print(f"\n📁 Results saved to: {output_file}")
print("\n" + "="*80)
