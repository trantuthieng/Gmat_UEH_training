import google.genai as genai
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
        # Create client with API key for google-genai v1.56+
        client = genai.Client(api_key=key)
        return client
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
    Bạn là chuyên gia ra đề thi GMAT cao cấp.
    Chủ đề: {topic}
    Câu mẫu: "{seed_question['content']}"

    Nhiệm vụ: Tạo 1 câu hỏi trắc nghiệm MỚI dựa trên logic của câu mẫu:
    1. Toán học: Thay đổi số liệu nhưng PHẢI TỰ TÍNH TOÁN LẠI ĐÁP ÁN chính xác.
    2. Logic: Giữ cấu trúc suy luận, thay đổi ngữ cảnh.
    3. Pattern: Tạo quy luật mới rõ ràng.

    YÊU CẦU QUAN TRỌNG (bắt buộc):
    - Hãy suy nghĩ từng bước (Chain of Thought) và ghi rõ phép tính số học cụ thể (không nói chung chung).
    - step_by_step_thinking phải có dạng "Bước 1: ... Bước 2: ..." kèm số liệu, công thức và kết quả trung gian. ĐỦ CHI TIẾT, ĐẦY ĐỦ.
    - explanation: CHỈ ghi kết quả cuối cùng + lý do TẠI SAO là đáp án đúng (KHÔNG lặp lại công thức, KHÔNG lặp lại các bước tính - những cái đó đã có ở step_by_step_thinking).
    - Đáp án đúng (correct_answer) PHẢI nằm trong danh sách lựa chọn (options).
    - Trả về kết quả dưới dạng JSON thuần túy, không có markdown.
    - CHỈ trả về 5 trường: question, options, step_by_step_thinking, correct_answer, explanation. KHÔNG thêm bất kỳ trường hay phần giải thích nào khác.

    OUTPUT JSON FORMAT (Bắt buộc tuân thủ chính xác):
    {{
        "question": "Nội dung câu hỏi...",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "step_by_step_thinking": "Bước 1: ...; Bước 2: ... (ghi rõ phép tính và kết quả trung gian)",
        "correct_answer": "Chép y nguyên text của lựa chọn đúng vào đây",
        "explanation": "Tóm tắt vì sao đáp án đúng, nhắc lại công thức/suy luận chính và số kết quả"
    }}
    """

    for attempt in range(1, max_attempts + 1):
        try:
            # Call generate_content with google-genai Client API
            response = model.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config={
                    'temperature': 0.7,
                    'max_output_tokens': 8192
                }
            )
            clean_text = _clean_response_text(response)
            data = json.loads(clean_text)
            print(f"✅ Tạo câu hỏi thành công (attempt {attempt})")
            
            # --- SỬA LỖI: Giữ nguyên metadata từ câu gốc ---
            data['type'] = seed_question.get('type', 'general')  # Giữ nguyên type của câu gốc (math/logic)
            data['topic'] = topic  # QUAN TRỌNG: Gán lại topic để lưu vào DB
            data['image_url'] = seed_question.get('image_url')  # Giữ link ảnh nếu câu gốc có
            # -------------------------------------------

            # Đảm bảo đáp án khớp với một lựa chọn
            options = data.get('options') or []
            correct = data.get('correct_answer') or ''
            print(f"🔍 Đang kiểm tra đáp án: {correct[:50]}...")
            aligned = _align_correct_answer(options, correct)
            if not aligned:
                raise ValueError("Correct answer does not align with options")
            print(f"✓ Đáp án hợp lệ và khớp với lựa chọn")

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
            print(f"✅ Hoàn tất kiểm tra câu hỏi - Topic: {topic}, Số lựa chọn: {len(cleaned_opts)}")
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
    
    # Giảm concurrency để tránh lỗi 429 (giới hạn ~7 RPM tài khoản hiện tại)
    with ThreadPoolExecutor(max_workers=1) as executor:
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

            # Tăng lên 15s để an toàn hơn với giới hạn API
            # 60s / 15s = 4 requests/phút (rất an toàn, tránh quá tải)
            print(f"⏳ Chờ 15s trước khi tạo câu tiếp theo...")
            time.sleep(15)
            
            if progress_callback:
                progress_callback((start_idx + idx + 1) / (start_idx + len(seeds)))
    
    return results

def generate_full_exam(seed_data, num_questions=30, num_general=0, progress_callback=None, max_retries_per_question=4, user_id=None):
    """
    Tạo bộ đề thi: Trộn 50% câu hỏi cũ từ Cache và 50% câu hỏi mới từ AI.
    Ưu tiên các topic mà user hay trả lời sai (nếu có user_id).
    
    Args:
        user_id: ID của user để lấy weak topics (optional)
    """
    exam_questions = []

    if not seed_data:
        print("❌ Không có seed data")
        return exam_questions

    # 1. CẤU HÌNH TỈ LỆ (50% cũ - 50% mới)
    target_cached = int(num_questions * 0.5)  # 15 câu cũ
    target_new = num_questions - target_cached # 15 câu mới

    print(f"📋 Kế hoạch tạo đề: {target_cached} câu cũ (DB) + {target_new} câu mới (AI)")
    
    # 1.5 LẤY WEAK TOPICS NẾU CÓ USER_ID
    weak_topics = []
    weak_topic_boost_ratio = 0.3  # 30% câu sẽ ưu tiên weak topics
    if user_id:
        try:
            from db import get_weak_topics
            weak_topics_data = get_weak_topics(user_id, limit=5)
            weak_topics = [item['topic'] for item in weak_topics_data]
            if weak_topics:
                print(f"🎯 Phát hiện điểm yếu: {', '.join(weak_topics)}")
        except Exception as e:
            print(f"⚠️ Không thể lấy weak topics: {e}")

    # 2. LẤY CÂU HỎI TỪ CACHE (DB)
    cached_part = get_cached_questions(target_cached, randomize=True)
    if cached_part:
        print(f"✅ Đã lấy {len(cached_part)} câu từ Cache")
        exam_questions.extend(cached_part)
    
    # Tính số câu thực sự cần tạo mới (phòng trường hợp DB chưa có gì thì phải tạo hết)
    actual_needed_new = num_questions - len(exam_questions)
    
    if actual_needed_new > 0:
        print(f"🤖 Đang AI tạo mới {actual_needed_new} câu...")
        print(f"⏱️  Thời gian ước tính: ~{actual_needed_new * 15 / 60:.1f} phút (15s/câu)")
        
        # --- CHỌN SEED DATA VỚI ƯU TIÊN WEAK TOPICS ---
        topic_buckets = {}
        for s in seed_data:
            t = s.get('topic', 'general')
            topic_buckets.setdefault(t, []).append(s)
        
        selected_seeds = []
        
        # Ưu tiên weak topics trước (30% số câu)
        if weak_topics:
            weak_count = int(actual_needed_new * weak_topic_boost_ratio)
            for topic in weak_topics:
                if topic in topic_buckets and len(selected_seeds) < weak_count:
                    # Lấy nhiều câu từ topic yếu
                    available = topic_buckets[topic]
                    take = min(len(available), weak_count - len(selected_seeds))
                    selected_seeds.extend(random.sample(available, take))
            print(f"✅ Đã thêm {len(selected_seeds)} câu từ weak topics")
        
        # Phần còn lại chọn đa dạng từ các topic khác
        remaining_needed = actual_needed_new - len(selected_seeds)
        bucket_list = list(topic_buckets.values())
        random.shuffle(bucket_list)
        
        while len(selected_seeds) < actual_needed_new and bucket_list:
            for bucket in bucket_list:
                if bucket:
                    selected_seeds.append(random.choice(bucket))
                    if len(selected_seeds) >= actual_needed_new:
                        break
        # Fallback
        if len(selected_seeds) < actual_needed_new:
            selected_seeds.extend(random.choices(seed_data, k=actual_needed_new - len(selected_seeds)))

        # --- GỌI API TẠO CÂU MỚI (Dùng hàm batch đã tối ưu ở bước trước) ---
        newly_generated = generate_question_batch(selected_seeds, 0, progress_callback)
        
        # Lưu câu MỚI vào DB ngay lập tức
        if newly_generated:
            try:
                saved = save_questions(newly_generated)
                print(f"💾 Đã lưu {saved} câu mới vào DB")
            except Exception as e:
                print(f"⚠️ Lỗi lưu DB: {e}")
            
            exam_questions.extend(newly_generated)

    # 3. KIỂM TRA VÀ BỔ SUNG NẾU THIẾU (FALLBACK)
    if len(exam_questions) < num_questions:
        missing = num_questions - len(exam_questions)
        print(f"⚠️ Vẫn thiếu {missing} câu, lấy thêm từ Cache bù vào...")
        extra_cached = get_cached_questions(limit=100, randomize=True)
        
        existing_hashes = set()
        for q in exam_questions:
            h = (q.get('question', '') + q.get('correct_answer', '')).strip().lower()
            existing_hashes.add(h)
            
        for q in extra_cached:
            h = (q.get('question', '') + q.get('correct_answer', '')).strip().lower()
            if h not in existing_hashes:
                exam_questions.append(q)
                if len(exam_questions) >= num_questions:
                    break

    # 4. XÁO TRỘN CUỐI CÙNG
    random.shuffle(exam_questions)
    
    print(f"🎉 Hoàn tất đề thi: {len(exam_questions)} câu.")
    return exam_questions[:num_questions]