"""
GMAT Model Comparison Tool
Comprehensive test for multiple Gemini models
"""

import os
from dotenv import load_dotenv
import requests
import json
import time
from datetime import datetime
from typing import Dict, List

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not API_KEY or len(API_KEY) < 10:
    print("❌ Invalid GEMINI_API_KEY in .env")
    print(f"   Current key: {API_KEY[:20] if API_KEY else 'EMPTY'}...")
    exit(1)

print(f"✅ API Key loaded: {API_KEY[:30]}...\n")

# ============= TEST SETUP =============

# Các model đáng test cho GMAT
MODEL_GROUPS = {
    "🔥 Recommended (Text)": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-3-flash",
        "gemini-3-pro",
    ],
    "📊 Other Models": [
        "gemma-3-1b",
        "gemma-3-12b",
        "gemma-3-27b",
    ]
}

# GMAT test questions
TEST_PROMPTS = [
    {
        "name": "Math Problem",
        "text": "GMAT Math: Nếu một chiếc áo được giảm giá 20% và giá mới là $96, giá gốc là bao nhiêu? Trình bày từng bước.",
        "category": "quantitative"
    },
    {
        "name": "Critical Reasoning",
        "text": "GMAT Critical Reasoning: 'Sản phẩm A có tỷ lệ khách hàng hài lòng cao hơn sản phẩm B. Do đó, sản phẩm A chất lượng tốt hơn.' Lập luận này có vấn đề gì? Giải thích chi tiết.",
        "category": "verbal"
    },
    {
        "name": "Data Sufficiency",
        "text": "GMAT Data Sufficiency: Có đủ thông tin để xác định nếu x là số dương không? (1) x² > 4 (2) x > -3. Phân tích từng statement.",
        "category": "quantitative"
    }
]

# ============= HELPER FUNCTIONS =============

def test_model(model_name: str, prompt: str, timeout: int = 45) -> Dict:
    """Test một model với prompt"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        start = time.time()
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            params={"key": API_KEY},
            timeout=timeout
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and data['candidates']:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return {
                    "success": True,
                    "model": model_name,
                    "response": text,
                    "time": elapsed,
                    "length": len(text)
                }
        
        return {
            "success": False,
            "model": model_name,
            "error": f"Status {response.status_code}: {response.json().get('error', {}).get('message', 'Unknown')}",
            "time": elapsed
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "model": model_name,
            "error": "Timeout",
            "time": timeout
        }
    except Exception as e:
        return {
            "success": False,
            "model": model_name,
            "error": str(e)[:80],
            "time": 0
        }

def score_response(text: str) -> float:
    """Đánh giá chất lượng response (0-100)"""
    score = 50
    
    # Độ dài
    if 100 < len(text) < 3000:
        score += 15
    
    # Cấu trúc
    if any(k in text.lower() for k in ['bước', 'vì', 'do đó', 'kết luận']):
        score += 15
    
    # Toán học
    if any(k in text for k in ['=', '×', '÷', '%', '$']):
        score += 10
    
    # Logic
    if any(k in text.lower() for k in ['logic', 'sai', 'đúng', 'lý do']):
        score += 10
    
    return min(score, 100)

# ============= MAIN TEST =============

print("=" * 100)
print("🎓 GMAT MODEL COMPARISON TEST")
print("=" * 100)
print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Testing 1 question across {sum(len(m) for m in MODEL_GROUPS.values())} models")
print("=" * 100)

# Test chỉ với prompt đầu tiên để tiết kiệm API calls
test_prompt = TEST_PROMPTS[0]["text"]
prompt_name = TEST_PROMPTS[0]["name"]

print(f"\n📝 Testing with: {prompt_name}")
print("-" * 100)

all_results = []
success_count = 0
fail_count = 0

for group_name, models in MODEL_GROUPS.items():
    print(f"\n{group_name}")
    print("─" * 100)
    
    for i, model_name in enumerate(models, 1):
        print(f"  [{i}/{len(models):2}] {model_name:<30}", end=" ... ", flush=True)
        
        result = test_model(model_name, test_prompt)
        
        if result['success']:
            score = score_response(result['response'])
            result['score'] = score
            
            # Summary
            preview = result['response'][:80].replace('\n', ' ')
            print(f"✅ {result['time']:.2f}s | Score: {score:3.0f}/100 | {preview}...")
            success_count += 1
        else:
            print(f"❌ {result['time']:.2f}s | {result['error']}")
            fail_count += 1
        
        all_results.append(result)

# ============= ANALYSIS =============

print("\n\n" + "=" * 100)
print("📊 SUMMARY & ANALYSIS")
print("=" * 100)

successful = [r for r in all_results if r['success']]
failed = [r for r in all_results if not r['success']]

print(f"\n✅ Successful: {len(successful)}/{len(all_results)}")
print(f"❌ Failed:     {len(failed)}/{len(all_results)}")

if successful:
    print("\n🏆 TOP 5 MODELS BY QUALITY SCORE:")
    print("─" * 100)
    ranked = sorted(successful, key=lambda x: x['score'], reverse=True)[:5]
    for rank, r in enumerate(ranked, 1):
        print(f"  {rank}. {r['model']:<30} | Score: {r['score']:3.0f}/100 | Time: {r['time']:6.2f}s")
    
    print("\n⚡ TOP 5 FASTEST MODELS:")
    print("─" * 100)
    fastest = sorted(successful, key=lambda x: x['time'])[:5]
    for rank, r in enumerate(fastest, 1):
        print(f"  {rank}. {r['model']:<30} | Time: {r['time']:6.2f}s | Score: {r['score']:3.0f}/100")
    
    print("\n💡 RECOMMENDATION:")
    print("─" * 100)
    best_quality = ranked[0]
    best_speed = fastest[0]
    
    print(f"\n  🎯 Best for Accuracy:")
    print(f"     Model: {best_quality['model']}")
    print(f"     Score: {best_quality['score']:.0f}/100")
    print(f"     Use for: Production GMAT answer generation")
    
    print(f"\n  ⚡ Best for Speed:")
    print(f"     Model: {best_speed['model']}")
    print(f"     Time: {best_speed['time']:.2f}s")
    print(f"     Use for: Real-time chat/interactions")
    
    # Balanced recommendation
    if best_quality['model'] == best_speed['model']:
        print(f"\n  ✨ Best Overall: {best_quality['model']}")
        print(f"     (Excellent in both quality and speed)")
    else:
        balanced = sorted(successful, 
                         key=lambda x: (x['score']/100) - (x['time']/10), 
                         reverse=True)[0]
        print(f"\n  ⚖️  Best Balanced: {balanced['model']}")
        print(f"     (Good quality + reasonable speed)")

if failed:
    print(f"\n⚠️  FAILED MODELS ({len(failed)}):")
    print("─" * 100)
    for r in failed[:5]:
        error = r['error'][:60]
        print(f"  • {r['model']:<30} | {error}")

# Save results
output_file = "model_test_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "results": all_results,
        "summary": {
            "total_tested": len(all_results),
            "successful": len(successful),
            "failed": len(failed)
        }
    }, f, indent=2, ensure_ascii=False)

print(f"\n📁 Detailed results saved to: {output_file}")
print("=" * 100)
