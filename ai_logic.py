import google.generativeai as genai
import json
import os
import random
import re
from difflib import SequenceMatcher
from dotenv import load_dotenv
import time
from db import save_questions, get_cached_questions
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# Load environment variables
load_dotenv()

# --- CẤU HÌNH (Lazy init để không gọi Streamlit trước set_page_config) ---

@lru_cache(maxsize=1)
def _get_api_key() -> str | None:
    """Fetch API key from env first; fallback to Streamlit secrets lazily.
    Avoid accessing streamlit at import time to keep set_page_config as first command.
    """
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st  # imported lazily, after app has configured
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


@lru_cache(maxsize=1)
def _get_model():
    key = _get_api_key()
    if not key:
        print("GEMINI_API_KEY not found. Set in environment or Streamlit secrets.")
        return None
    try:
        genai.configure(api_key=key)
        return genai.GenerativeModel('gemma-3-12b-it')
    except Exception as e:
        print(f"Lỗi khởi tạo Gemini: {e}")
        return None

def _clean_response_text(response) -> str:
    """Extracts the first text part and strips code fences/whitespace/control chars."""
    text = None
    try:
        text = response.text
    except Exception:
        pass

    if not text:
        try:
            text = response.candidates[0].content.parts[0].text  # best-effort fallback
        except Exception:
            text = ""

    # Remove markdown code fences
    text = text.replace('```json', '').replace('```', '').strip()
    
    # Remove control characters that break JSON (except \n, \r, \t)
    import re
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text
def _align_correct_answer(options: list, correct_answer: str) -> str | None:
    """Best-effort map correct_answer to one of the provided options.

    - Accept exact match
    - Accept letter prefix match (A/B/C/D)
    - Accept content match after stripping prefixes like "A." or "A)"
    - Fallback to similarity score to handle minor variations
    """
    if not options or not correct_answer:
        return None

    cleaned_opts = []
    seen = set()
    for opt in options:
        if not isinstance(opt, str):
            continue
        opt_clean = opt.strip()
        if opt_clean and opt_clean not in seen:
            cleaned_opts.append(opt_clean)
            seen.add(opt_clean)

    if not cleaned_opts:
        return None

    correct_clean = correct_answer.strip()

    # 1) Exact match
    for opt in cleaned_opts:
        if correct_clean == opt:
            return opt

    # Helper to strip letter prefix
    def strip_prefix(val: str) -> str:
        return re.sub(r'^[A-D][\.\)]\s*', '', (val or '').strip(), flags=re.IGNORECASE)

    # 2) Match by letter prefix (A/B/C/D)
    if correct_clean:
        letter = correct_clean[:1].upper()
        if letter in "ABCD":
            for opt in cleaned_opts:
                if opt.upper().startswith(letter):
                    return opt

    # 3) Match by content after removing prefix
    normalized_correct = strip_prefix(correct_clean).lower()
    if normalized_correct:
        for opt in cleaned_opts:
            if strip_prefix(opt).lower() == normalized_correct:
                return opt

    # 4) Fallback: similarity match
    best_opt, best_ratio = None, 0.0
    for opt in cleaned_opts:
        ratio = SequenceMatcher(None, strip_prefix(opt).lower(), normalized_correct).ratio()
        if ratio > best_ratio:
            best_opt, best_ratio = opt, ratio
    if best_opt and best_ratio >= 0.8:
        return best_opt

    return None


def generate_question_variant(seed_question, max_attempts: int = 3):
    """Tạo 1 biến thể câu hỏi (dùng cho hàm batch bên dưới) với retry khi JSON lỗi."""
    model = _get_model()
    if model is None:
        print("❌ Model không được khởi tạo")
        return None

    topic = seed_question.get('topic', 'Kiến thức tổng hợp')
    is_visual = topic.lower() in ['pattern recognition', 'letter pattern', 'logic puzzle', 'number pattern']
    
    prompt = f"""
    Đóng vai người ra đề thi GMAT.
    Chủ đề: {topic}
    Câu mẫu: "{seed_question['content']}"

    Nhiệm vụ: Tạo 1 câu hỏi trắc nghiệm MỚI:
    - Nếu là toán/logic: giữ nguyên dạng toán/logic nhưng thay số liệu/bối cảnh
    - Nếu là kiến thức: cùng chủ đề nhưng hỏi khía cạnh khác
    - Nếu là IQ/pattern (dãy số, chữ cái, hình học): tạo dãy logic mới, MÔ TẢ bằng text thuần, KHÔNG cần hình ảnh thực
    - TÍNH TOÁN CẨN THẬN: với bài tính phần trăm tăng/giảm, dùng công thức (giá_mới - giá_cũ)/giá_cũ * 100 và kiểm tra lại kết quả trước khi trả lời.

    Ràng buộc định dạng:
    - Chỉ dùng ký tự ASCII, không ký tự đặc biệt phức tạp, không emoji.
    - Không xuống dòng trong giá trị chuỗi.
    - Không dùng Markdown, không bao các block ```json.
    - Trả về DUY NHẤT một JSON object hợp lệ.

    OUTPUT JSON duy nhất:
    {{
        "id": "new_id",
        "type": "general",
        "question": "No newline. Short and clear. For pattern/sequence questions, describe the pattern in text (e.g. 1,2,4,7,11,... (?)).",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "correct_answer": "Copy exact text of the correct option",
        "explanation": "Brief reasoning (show key calculation or pattern rule)"
    }}
    """

    for attempt in range(1, max_attempts + 1):
        try:
            # Add generation config for better JSON output
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 1024
                }
            )
            clean_text = _clean_response_text(response)
            data = json.loads(clean_text)
            data['type'] = 'general'  # Tất cả đều là câu hỏi chung

            # Đảm bảo đáp án khớp với một lựa chọn
            options = data.get('options') or []
            correct = data.get('correct_answer') or ''
            aligned = _align_correct_answer(options, correct)
            if not aligned:
                raise ValueError("Correct answer does not align with options")

            # Chuẩn hóa lại danh sách lựa chọn và đáp án để hiển thị nhất quán
            cleaned_opts = []
            seen = set()
            for opt in options:
                if not isinstance(opt, str):
                    continue
                opt_clean = opt.strip()
                if opt_clean and opt_clean not in seen:
                    cleaned_opts.append(opt_clean)
                    seen.add(opt_clean)

            data['options'] = cleaned_opts
            data['correct_answer'] = aligned
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi JSON (attempt {attempt}/{max_attempts}): {e}")
            print(f"Response text: {clean_text[:200]}")
            if attempt < max_attempts:
                time.sleep(1 * attempt)  # Exponential backoff
        except Exception as e:
            print(f"❌ Lỗi khi tạo câu (attempt {attempt}/{max_attempts}): {e}")
            if attempt < max_attempts:
                time.sleep(2 * attempt)  # Exponential backoff

    return None

def generate_question_batch(seeds, start_idx=0, progress_callback=None):
    """Generate multiple questions concurrently"""
    results = []
    visual_keywords = ['hình', 'shape', 'ảnh', 'diagram', 'figure', 'biểu đồ']

    def _extract_number(text: str) -> float | None:
        nums = re.findall(r"\d+(?:[.,]\d+)?", text or "")
        if len(nums) < 2:
            return None
        try:
            old_v = float(nums[0].replace(',', '.'))
            new_v = float(nums[1].replace(',', '.'))
            if old_v == 0:
                return None
            pct = round((new_v - old_v) / old_v * 100, 2)
            return pct
        except Exception:
            return None

    def _is_percent_increase_question(text: str) -> bool:
        t = (text or '').lower()
        return 'tăng' in t and 'từ' in t and ('lên' in t or 'thành' in t)

    def _percent_answer_matches(q: dict) -> bool:
        question = q.get('question', '')
        if not _is_percent_increase_question(question):
            return True  # not a percent-change question
        expected = _extract_number(question)
        if expected is None:
            return True

        def _first_number(val: str) -> float | None:
            m = re.search(r"-?\d+(?:[.,]\d+)?", val or "")
            if not m:
                return None
            try:
                return float(m.group(0).replace(',', '.'))
            except Exception:
                return None

        options = q.get('options') or []
        correct = q.get('correct_answer') or ''
        correct_num = _first_number(correct)
        # Accept if correct_answer has number close to expected
        if correct_num is not None and abs(correct_num - expected) <= 0.6:
            return True
        # Else check if any option matches expected closely
        for opt in options:
            num = _first_number(opt)
            if num is not None and abs(num - expected) <= 0.6:
                return True
        return False

    def _is_valid(q: dict) -> bool:
        """Basic sanity checks to avoid garbage answers."""
        if not q:
            return False
        options = q.get('options') or []
        if len(options) < 2:
            return False
        correct = q.get('correct_answer') or ''
        has_option_match = False
        # Accept if exact match to an option
        if correct in options:
            has_option_match = True
        # Accept if the letter prefix matches one option's prefix (e.g., 'A.' or 'A ')
        if correct:
            letter = correct.strip()[:2]  # e.g., "A." or "A "
            for opt in options:
                if opt.strip().startswith(letter):
                    has_option_match = True
        if not has_option_match:
            return False
        # Additional semantic check for percent-increase questions
        if not _percent_answer_matches(q):
            return False
        return True
    
    with ThreadPoolExecutor(max_workers=3) as executor:
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
                    elif not _is_valid(new_q):
                        print(f"🚫 Bỏ qua câu hỏi sai định dạng đáp án")
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

def generate_full_exam(seed_data, num_questions=30, num_general=0, progress_callback=None, max_retries_per_question=4):
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
    
    # Diversify seed selection: group by topic, pick from each bucket
    topic_buckets = {}
    for s in seed_data:
        t = s.get('topic', 'general')
        topic_buckets.setdefault(t, []).append(s)
    
    selected_seeds = []
    bucket_list = list(topic_buckets.values())
    random.shuffle(bucket_list)
    while len(selected_seeds) < num_questions and bucket_list:
        for bucket in bucket_list:
            if bucket:
                selected_seeds.append(random.choice(bucket))
                if len(selected_seeds) >= num_questions:
                    break
    # Fallback if not enough
    if len(selected_seeds) < num_questions:
        selected_seeds.extend(random.choices(seed_data, k=num_questions - len(selected_seeds)))
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
    def normalize(txt: str) -> str:
        import string
        return txt.lower().translate(str.maketrans('', '', string.punctuation)).strip()
    
    seen_questions = set()
    unique_questions = []
    
    for q in exam_questions:
        question_text = normalize(q.get('question', ''))
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
            q_text = normalize(q.get('question', ''))
            if q_text and q_text not in seen_questions:
                exam_questions.append(q)
                seen_questions.add(q_text)
                if len(exam_questions) >= num_questions:
                    break

    # Xáo trộn thứ tự câu hỏi NHIỀU LẦN để đảm bảo ngẫu nhiên hoàn toàn
    random.shuffle(exam_questions)
    random.shuffle(exam_questions)  # double shuffle for extra randomness
    
    if len(exam_questions) < num_questions:
        print(f"⚠️ Cảnh báo: Chỉ tạo được {len(exam_questions)}/{num_questions} câu. Vui lòng kiểm tra API key hoặc thử lại.")
    else:
        print(f"🎉 Tạo xong {len(exam_questions)} câu hỏi (không trùng lặp, thứ tự ngẫu nhiên)")
    
    return exam_questions