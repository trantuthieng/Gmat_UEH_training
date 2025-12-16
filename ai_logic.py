import google.generativeai as genai
import json
import os
import random
from dotenv import load_dotenv
import time
from db import save_questions, get_cached_questions
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# Load environment variables
load_dotenv()

# --- CẤU HÌNH ---
# Try Streamlit secrets first, then env variable, then fallback
try:
    import streamlit as st
    API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "AIzaSyDRkwgwveGS3sgyJIn77Qh3MW0wo79GfHg"))
except:
    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDRkwgwveGS3sgyJIn77Qh3MW0wo79GfHg")
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemma-3-12b-it') # Dùng Gemma 3 12B Instruction-Tuned
except Exception as e:
    print(f"Lỗi khởi tạo Gemini: {e}")
    model = None

def generate_question_variant(seed_question):
    """Tạo 1 biến thể câu hỏi (dùng cho hàm batch bên dưới)"""
    if model is None: 
        print("❌ Model không được khởi tạo")
        return None
    
    prompt = f"""
    Đóng vai người ra đề thi GMAT.
    Chủ đề: {seed_question.get('topic', 'Kiến thức tổng hợp')}
    Câu mẫu: "{seed_question['content']}"
    
    Nhiệm vụ: Tạo 1 câu hỏi trắc nghiệm MỚI:
    - Nếu là toán/logic: giữ nguyên dạng toán/logic nhưng thay số liệu/bối cảnh
    - Nếu là kiến thức: cùng chủ đề nhưng hỏi khía cạnh khác
    
    OUTPUT JSON (Không Markdown):
    {{
        "id": "new_id",
        "type": "general",
        "question": "Nội dung câu hỏi...",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "correct_answer": "Chép y nguyên nội dung đáp án đúng",
        "explanation": "Giải thích ngắn gọn"
    }}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)
        data['type'] = 'general'  # Tất cả đều là câu hỏi chung
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi JSON: {e}")
        print(f"Response text: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"❌ Lỗi khi tạo câu: {e}")
        return None

def generate_question_batch(seeds, start_idx=0, progress_callback=None):
    """Generate multiple questions concurrently"""
    results = []
    visual_keywords = ['hình', 'shape', 'ảnh', 'diagram', 'figure', 'biểu đồ']
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_idx = {executor.submit(generate_question_variant, seed): (idx, seed) 
                        for idx, seed in enumerate(seeds)}
        
        # Process completed tasks
        for future in as_completed(future_to_idx):
            idx, seed = future_to_idx[future]
            try:
                new_q = future.result()
                if new_q:
                    text = (new_q.get('question') or '').lower()
                    has_image = bool(new_q.get('image_url'))
                    if any(k in text for k in visual_keywords) and not has_image:
                        print(f"🚫 Bỏ qua câu hỏi thiếu hình ảnh: {text[:60]}...")
                    else:
                        results.append(new_q)
                        print(f"✅ Câu {start_idx + idx + 1} - Tạo thành công")
                else:
                    print(f"⚠️ Câu {start_idx + idx + 1} - Thất bại")
            except Exception as e:
                print(f"❌ Lỗi khi tạo câu {start_idx + idx + 1}: {e}")
            
            if progress_callback:
                progress_callback((start_idx + idx + 1) / (start_idx + len(seeds)))
    
    return results

def generate_full_exam(seed_data, num_questions=30, num_general=0, progress_callback=None, max_retries_per_question=2):
    """
    Tạo bộ đề thi hoàn chỉnh với cơ chế concurrent execution và retry để tăng tốc độ.
    - num_questions: Tổng số câu hỏi cần tạo
    - num_general: Tham số cũ để tương thích, bỏ qua
    - max_retries_per_question: Số lần thử lại tối đa cho mỗi câu thất bại
    """
    exam_questions = []

    if not seed_data:
        print("❌ Không có seed data")
        return exam_questions

    print(f"📋 Bắt đầu tạo {num_questions} câu hỏi từ {len(seed_data)} câu mẫu (concurrent mode)...")

    # Try to get from cache first
    cached = get_cached_questions(num_questions, randomize=True)
    if len(cached) >= num_questions:
        print(f"✅ Sử dụng {num_questions} câu từ cache")
        return cached[:num_questions]
    
    selected_seeds = random.choices(seed_data, k=num_questions)
    total_tasks = len(selected_seeds)

    # Concurrent generation - batch processing
    exam_questions = generate_question_batch(selected_seeds, 0, progress_callback)

    # Retry with concurrent processing for failed questions
    if len(exam_questions) < num_questions:
        remaining = num_questions - len(exam_questions)
        print(f"🔁 Bắt đầu thử lại cho {remaining} câu lỗi (concurrent retry)...")
        retry_pool = random.choices(seed_data, k=remaining * 2)  # Generate more to increase success rate
        
        retry_results = generate_question_batch(retry_pool, len(exam_questions), progress_callback)
        exam_questions.extend(retry_results[:remaining])

    # Kiểm tra câu trùng lặp dựa trên nội dung câu hỏi (optimized)
    seen_questions = set()
    unique_questions = []
    
    for q in exam_questions:
        question_text = q.get('question', '').strip().lower()
        if question_text and question_text not in seen_questions:
            unique_questions.append(q)
            seen_questions.add(question_text)
    
    exam_questions = unique_questions
    print(f"✅ Loại bỏ trùng lặp: còn {len(exam_questions)} câu duy nhất")
    
    # Save to cache for future use
    if exam_questions:
        try:
            saved_count = save_questions(exam_questions)
            print(f"💾 Đã lưu {saved_count} câu vào DB cache")
        except Exception as e:
            print(f"⚠️ Không thể lưu DB: {e}")
    
    # Fallback: use cache if still not enough
    if len(exam_questions) < num_questions:
        need_fill = num_questions - len(exam_questions)
        print(f"⚠️ Còn thiếu {need_fill} câu, sử dụng cache để bổ sung...")
        
        cached = get_cached_questions(need_fill * 2, randomize=True)
        for q in cached:
            q_text = q.get('question', '').strip().lower()
            if q_text not in seen_questions:
                exam_questions.append(q)
                seen_questions.add(q_text)
                if len(exam_questions) >= num_questions:
                    break

    # Xáo trộn thứ tự câu hỏi để đảm bảo ngẫu nhiên hoàn toàn
    random.shuffle(exam_questions)
    
    if len(exam_questions) < num_questions:
        print(f"⚠️ Cảnh báo: Chỉ tạo được {len(exam_questions)}/{num_questions} câu. Vui lòng kiểm tra API key hoặc thử lại.")
    else:
        print(f"🎉 Tạo xong {len(exam_questions)} câu hỏi (không trùng lặp, thứ tự ngẫu nhiên)")
    
    return exam_questions