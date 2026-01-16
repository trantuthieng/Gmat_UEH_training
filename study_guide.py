import google.genai as genai
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_api_key() -> str | None:
    """Lấy API key từ env hoặc Streamlit secrets"""
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None

@lru_cache(maxsize=1)
def _get_study_model():
    """Khởi tạo model Gemini cho ôn tập"""
    key = _get_api_key()
    if not key:
        print("GEMINI_API_KEY not found")
        return None
    
    try:
        # Create client with API key for google-genai v1.56+
        client = genai.Client(api_key=key)
        return client
    except Exception as e:
        print(f"Lỗi khởi tạo Study Model: {e}")
        return None

@lru_cache(maxsize=1)
def _get_study_model():
    """Khởi tạo model Gemini cho ôn tập"""
    key = _get_api_key()
    if not key:
        print("GEMINI_API_KEY not found")
        return None
    
    try:
        # Create client with API key for google-genai v1.56+
        client = genai.Client(api_key=key)
        return client
    except Exception as e:
        print(f"Lỗi khởi tạo Study Model: {e}")
        return None

def _get_topic_knowledge_base():
    """Cơ sở dữ liệu kiến thức chi tiết cho từng topic GMAT"""
    return {
        'Letter Sequence': {
            'theory': '''LÝ THUYẾT CHI TIẾT VỀ LETTER SEQUENCE (Dãy Chữ Cái)

1. ĐỊNH NGHĨA:
Letter Sequence là dạng bài toán yêu cầu bạn xác định quy luật (pattern) của một dãy các chữ cái, sau đó dự đoán chữ cái tiếp theo hoặc tìm kiếm chữ cái bị thiếu trong dãy. Quy luật có thể dựa trên vị trí chữ cái trong bảng chữ cái, khoảng cách giữa các chữ, hoặc kết hợp của nhiều yếu tố khác nhau.

2. CÁC LOẠI PATTERN PHỔ BIẾN:
- PATTERN CÓ ĐIỀU KIỆN: A, B, C, D, E... (cộng 1 trong bảng chữ cái)
- PATTERN BỎ QUA: A, C, E, G... (bỏ qua 1 chữ cái)
- PATTERN NƯỚC MUỐI: A, A, B, B, C, C... (lặp lại mỗi chữ 2 lần)
- PATTERN NƯỚC KIẾM: A, B, A, B, C, B, C... (lặp lại không đều)
- PATTERN KHOẢNG CÁCH THAY ĐỔI: A, B, D, G, K... (khoảng cách cộng dồn)
- PATTERN NƯỚC NGỢ: A, Z, B, Y, C, X... (từ hai đầu của bảng chữ cái)

3. CÁCH ÁP DỤNG - 4 BƯỚC GIẢI:
Bước 1: Xác định chữ cái đầu tiên và tính vị trí trong bảng chữ cái (A=1, B=2...Z=26)
Bước 2: Tìm khoảng cách/hiệu số giữa các chữ cái liên tiếp (A→B=+1, A→C=+2, v.v.)
Bước 3: Phân tích quy luật khoảng cách (tăng, giảm, lặp lại, hay vô quy tắc)
Bước 4: Áp dụng quy luật để tìm chữ cái tiếp theo

4. VÍ DỤ MINH HỌA CHI TIẾT:
Ví dụ 1 - Pattern tăng đều: A, C, E, G, ?
- A=1, C=3, E=5, G=7
- Quy luật: cộng 2 mỗi lần
- Đáp án: I=9 (7+2)

Ví dụ 2 - Pattern khoảng cách tăng: A, B, D, G, L, ?
- A→B: +1, B→D: +2, D→G: +3, G→L: +5... không phải, G→L là +5, vậy tiếp theo +5? Không đúng
- Phân tích lại: +1, +2, +3, +4... vậy L+5 = Q

Ví dụ 3 - Pattern lặp lại: A, B, B, C, C, C, ?
- Một lần, hai lần, ba lần...
- Đáp án: D (lặp 4 lần, nhưng tính từ vị trí tiếp theo)

5. LƯU Ý QUAN TRỌNG:
- Luôn tính từ vị trí chữ cái trong bảng (A=1 đến Z=26), không phải vị trí trong dãy
- Nếu khoảng cách vượt quá 26 hoặc nhỏ hơn 1, nó quay vòng: Z+1=A, A-1=Z
- Khi không tìm được quy luật tuyến tính, hãy kiểm tra các pattern phức tạp (nước muối, nước kiếm, v.v.)
- Trong bài thi GMAT, thường chỉ có 1-2 loại pattern, không quá phức tạp''',
            'detailed_concepts': [
                {
                    'concept_name': 'Khoảng cách/Hiệu số (Gap Analysis)',
                    'explanation': 'Đây là kỹ thuật cơ bản nhất. Tính hiệu số (số lần cộng thêm) giữa mỗi chữ cái liên tiếp. Nếu hiệu số không đổi, dãy là cấp số cộng. Nếu hiệu số thay đổi theo quy luật (tăng/giảm đều), ta cần xác định quy luật của hiệu số đó.',
                    'example': 'A, D, G, J, M, ? → Hiệu: +3, +3, +3, +3 → Đáp án: P (+3)'
                },
                {
                    'concept_name': 'Các Pattern Đặc Biệt (Special Patterns)',
                    'explanation': 'Ngoài cấp số cộng, còn có các pattern lặp lại (repeating), nước muối (alternating), hay thậm chí kết hợp chữ cái từ hai phía của bảng. Học sinh cần nhận diện nhanh các pattern này để không lãng phí thời gian tìm quy luật tuyến tính.',
                    'example': 'A, Z, C, X, E, V, ? → Nước muối từ hai đầu: A(1)↔Z(26), C(3)↔X(24), E(5)↔V(22) → Đáp án: G(7)'
                },
                {
                    'concept_name': 'Lặp Lại & Tăng Tần Suất (Repetition with Increasing Frequency)',
                    'explanation': 'Dãy bắt đầu với mỗi chữ cái xuất hiện số lần khác nhau theo quy luật. Ví dụ: A xuất hiện 1 lần, B xuất hiện 2 lần, C xuất hiện 3 lần, v.v.',
                    'example': 'A, B, B, C, C, C, D, D, D, D, ? → Tần suất tăng → Đáp án: E (E xuất hiện 5 lần, nhưng câu hỏi chỉ hỏi chữ tiếp theo nên là E)'
                }
            ],
            'step_by_step_method': [
                'Bước 1: Ghi lại vị trí của mỗi chữ cái trong bảng (A=1, B=2...Z=26)',
                'Bước 2: Tính khoảng cách/hiệu số giữa các vị trí liên tiếp',
                'Bước 3: Phân tích quy luật: hiệu số có đều không, hay tăng/giảm, hay lặp lại?',
                'Bước 4: Áp dụng quy luật để tìm chữ cái tiếp theo (lưu ý: quay vòng khi vượt Z hoặc dưới A)'
            ],
            'common_mistakes': [
                'Lỗi 1: Quên rằng Z+1 quay về A. Nếu tìm được chữ số 27, phải convert thành A (27 mod 26 = 1)',
                'Lỗi 2: Nhầm lẫn vị trí chữ cái trong dãy với vị trí trong bảng. Ví dụ: chữ cái thứ 3 trong dãy không phải C',
                'Lỗi 3: Chỉ tìm quy luật tuyến tính mà bỏ qua các pattern đặc biệt như nước muối hay lặp lại',
                'Lỗi 4: Tính nhầm khoảng cách. Ví dụ: từ A(1) đến D(4) là +3, không phải +4'
            ],
            'tips_for_accuracy': [
                'Mẹo 1: Luôn viết ra vị trí số của mỗi chữ cái (A=1...Z=26). Dùng giấy nháp, không cần nhẩm tính',
                'Mẹo 2: Kiểm tra 3 hiệu số đầu tiên. Nếu chúng bằng nhau, rất có thể là cấp số cộng',
                'Mẹo 3: Nếu không tìm được quy luật tuyến tính, nhìn toàn cảnh dãy để phát hiện các pattern đặc biệt',
                'Mẹo 4: Nếu dãy ngắn (3-4 chữ), hãy thử tất cả các pattern cơ bản trước khi bỏ cuộc'
            ],
            'tips_for_speed': [
                'Mẹo tốc độ 1: Dùng các chữ cái đánh dấu (a, b, c) hoặc vẽ mũi tên để theo dõi quy luật nhanh hơn',
                'Mẹo tốc độ 2: Nếu hiệu số cộng dồn (1, 2, 3, 4...), nhận diện ngay, không cần tính thêm'
            ],
            'practice_drills': [
                'Bài tập 1: Thực hành tính vị trí 26 chữ cái một cách nhanh. Lập bảng A=1...Z=26 để ghi nhớ',
                'Bài tập 2: Tìm quy luật cho 10 dãy chữ cái khác nhau, mỗi dãy 5-7 chữ',
                'Bài tập 3: Phân loại các dãy theo pattern (tuyến tính, nước muối, lặp lại)',
                'Bài tập 4: Luyện tập giải 5 bài Letter Sequence dưới áp lực thời gian (30-45 giây/bài)'
            ],
            'key_formulas': [
                'Công thức vị trí: Nếu hiệu số là d, chữ cái tiếp theo = vị trí hiện tại + d',
                'Quay vòng: Nếu kết quả > 26, trừ 26. Nếu < 1, cộng 26',
                'Cấp số cộng: Vị trí = a + (n-1)d, với a = vị trí đầu, d = hiệu số, n = vị trí cần tìm'
            ]
        },
        'Mixture Problems': {
            'theory': '''LÝ THUYẾT ĐẦY ĐỦ VỀ MIXTURE PROBLEMS (Bài Toán Hỗn Hợp)

1. ĐỊNH NGHĨA:
Mixture Problems là dạng bài toán yêu cầu tính toán các thuộc tính (nồng độ, giá trị, tỷ lệ) của một hỗn hợp được tạo bằng cách kết hợp hai hoặc nhiều thành phần khác nhau. Chìa khóa là theo dõi một đại lượng cụ thể (chất tan, thành phần nguyên chất) qua quá trình pha trộn.

2. CÁC CÔNG THỨC CHÍNH:
- Nồng độ (%) = (Lượng chất tan / Tổng lượng dung dịch) × 100
- Lượng chất tan = Nồng độ × Tổng lượng / 100
- Phương trình cân bằng: C₁V₁ + C₂V₂ = C_final × (V₁ + V₂)

3. CÁCH ÁP DỤNG:
Bước 1: Phân tích và tóm tắt đề bài bằng bảng (Tên dung dịch, Khối lượng, Nồng độ %, Lượng chất tan)
Bước 2: Xác định đại lượng cần tìm và đặt ẩn số x
Bước 3: Lập phương trình dựa trên cân bằng chất tan hoặc bất biến
Bước 4: Giải phương trình và kiểm tra tính hợp lý

4. VÍ DỤ MINH HỌA:
Trộn 30L dung dịch muối 10% với 20L dung dịch muối 25%. Nồng độ muối mới?
- Dung dịch 1: 30L × 10% = 3L muối
- Dung dịch 2: 20L × 25% = 5L muối
- Tổng muối: 3 + 5 = 8L, Tổng thể tích: 50L
- Nồng độ mới = 8/50 × 100 = 16%

5. LƯU Ý QUAN TRỌNG:
- Chất nguyên chất (axit, vàng) = 100% nồng độ
- Nước/dung môi nguyên chất = 0% nồng độ
- Khi bay hơi nước: lượng chất tan không đổi, nhưng tổng dung dịch giảm
- Luôn kiểm tra: kết quả phải nằm giữa nồng độ của 2 thành phần ban đầu'''
        },
        'Number Properties': {
            'theory': '''LÝ THUYẾT CHI TIẾT VỀ NUMBER PROPERTIES (Tính Chất Số)

1. ĐỊNH NGHĨA:
Number Properties là các đặc tính cơ bản của số (chẵn/lẻ, nguyên tố, chia hết, v.v.) được sử dụng để giải các bài toán logic và đại số trên GMAT.

2. CÁC KHÁI NIỆM CHÍNH:
- SỐ CHẴN/LẺ: Chẵn chia hết cho 2, lẻ không. Chẵn+Chẵn=Chẵn, Lẻ+Lẻ=Chẵn, Chẵn+Lẻ=Lẻ
- SỐ NGUYÊN TỐ: Chỉ chia hết cho 1 và chính nó (2, 3, 5, 7, 11, 13, 17, 19, 23, 29...)
- CHIA HẾT: a chia hết cho b nếu a = b×k (k là số nguyên)
- ƯỚC CHUNG & BỘI CHUNG: GCD (ước lớn nhất), LCM (bội nhỏ nhất)

3. CÁCH ÁP DỤNG:
Bước 1: Xác định loại bài toán (chẵn/lẻ, chia hết, nguyên tố, hay phân tích thừa số)
Bước 2: Liệt kê các tính chất của các số trong bài
Bước 3: Áp dụng quy tắc phù hợp
Bước 4: Kiểm tra bằng ví dụ cụ thể

4. VÍ DỤ:
Nếu x là số chẵn và y là số lẻ, x+y là?
→ Chẵn + Lẻ = Lẻ'''
        }
    }

def generate_study_guide(questions: List[Dict[str, Any]], user_answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Tạo tài liệu ôn tập chi tiết dựa trên các câu hỏi trong bài thi
    
    Args:
        questions: Danh sách các câu hỏi trong bài thi
        user_answers: Dict chứa câu trả lời của user {q_0: 'A. ...', q_1: 'B. ...'}
    
    Returns:
        Dict chứa nội dung ôn tập theo từng topic
    """
    model = _get_study_model()
    if not model:
        return {
            "error": "Không thể kết nối đến AI. Vui lòng kiểm tra API key.",
            "topics": []
        }
    
    # Phân tích câu sai và đúng theo topic - GIỮ TOÀN BỘ THÔNG TIN
    topic_analysis = {}
    
    for idx, q in enumerate(questions):
        topic = q.get('topic', 'General')
        qtype = q.get('type', 'general')
        user_choice = user_answers.get(f"q_{idx}")
        correct_answer = q.get('correct_answer', '')
        
        is_correct = False
        if user_choice and correct_answer:
            if user_choice.split('.')[0] == correct_answer.split('.')[0]:
                is_correct = True
        
        if topic not in topic_analysis:
            topic_analysis[topic] = {
                'type': qtype,
                'total': 0,
                'correct': 0,
                'wrong': 0,
                'questions': [],
                'wrong_questions': []  # Tách riêng câu sai để ưu tiên phân tích
            }
        
        topic_analysis[topic]['total'] += 1
        if is_correct:
            topic_analysis[topic]['correct'] += 1
        else:
            topic_analysis[topic]['wrong'] += 1
        
        # Lưu TOÀN BỘ thông tin câu hỏi (không cắt ngắn)
        question_data = {
            'question': q.get('question', ''),
            'options': q.get('options', []),
            'user_choice': user_choice,
            'correct_answer': correct_answer,
            'explanation': q.get('explanation', ''),
            'step_by_step_thinking': q.get('step_by_step_thinking', ''),
            'is_correct': is_correct
        }
        
        topic_analysis[topic]['questions'].append(question_data)
        if not is_correct:
            topic_analysis[topic]['wrong_questions'].append(question_data)
    
    # XỬ LÝ TỪNG CHỦ ĐỀ MỘT - ƯU TIÊN CHỦ ĐỀ CÓ NHIỀU CÂU SAI
    sorted_topics = sorted(
        topic_analysis.items(),
        key=lambda x: (x[1]['wrong'], -x[1]['total']),  # Sắp theo số câu sai (nhiều nhất trước)
        reverse=True
    )
    
    all_topics_guides = []
    
    for topic_name, data in sorted_topics:
        accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        wrong_count = data['wrong']
        
        # Chỉ phân tích chi tiết nếu có câu sai HOẶC accuracy < 100%
        if wrong_count == 0 and accuracy == 100:
            # Topic hoàn hảo - tạo guide đơn giản
            all_topics_guides.append({
                'topic': topic_name,
                'accuracy': round(accuracy, 0),
                'importance': 'low',
                'priority_level': 3,
                'key_concepts': [f"Bạn đã nắm vững {topic_name}!"],
                'common_mistakes': [],
                'study_tips': [f"Tiếp tục duy trì hiểu biết về {topic_name}"],
                'practice_approach': f"Bạn không có lỗi nào ở {topic_name}. Tiếp tục!",
                'formulas_or_rules': [],
                'practice_drills': [],
                'time_management_tip': 'Duy trì tốc độ hiện tại',
                'stats': {
                    'total': data['total'],
                    'correct': data['correct'],
                    'wrong': data['wrong']
                }
            })
            continue
    
        # TẠO PROMPT CHI TIẾT CHO TỪNG TOPIC - BAO GỒM CÂU HỎI SAI ĐẦY ĐỦ
        importance = 'high' if accuracy < 60 else ('medium' if accuracy < 80 else 'low')
        priority = 1 if importance == 'high' else (2 if importance == 'medium' else 3)
        
        # Chuẩn bị chi tiết các câu SAI để phân tích
        wrong_details = []
        for q in data['wrong_questions']:
            wrong_details.append({
                'question': q['question'],
                'options': q['options'],
                'user_choice': q['user_choice'],
                'correct_answer': q['correct_answer'],
                'explanation': q['explanation'],
                'step_by_step': q['step_by_step_thinking']
            })
        
        # Prompt chi tiết cho TỪNG topic
        topic_prompt = f"""
Bạn là giáo viên GMAT chuyên nghiệp. Phân tích chi tiết chủ đề "{topic_name}" cho học sinh.

THỐNG KÊ:
- Tổng số câu: {data['total']}
- Số câu đúng: {data['correct']}
- Số câu sai: {wrong_count}
- Độ chính xác: {accuracy:.0f}%

CÁC CÂU HỎI HỌC SINH TRẢ LỜI SAI (cần phân tích chi tiết):
{json.dumps(wrong_details, ensure_ascii=False, indent=2)}

NHIỆM VỤ:
1. **Lý thuyết chi tiết đầy đủ**: Giải thích TOÀN BỘ kiến thức về {topic_name}
2. **Phân tích bài làm**: Đi qua TỪNG câu sai với chi tiết cụ thể
3. **Lỗi phổ biến**: Liệt kê đầy đủ các lỗi thường gặp
4. **Mẹo thực chiến**: Cụ thể, áp dụng ngay được

OUTPUT (JSON format):
{{
    "theory": "LÝ THUYẾT ĐẦY ĐỦ về {topic_name}:\\n\\n1. ĐỊNH NGHĨA: Giải thích rõ ràng khái niệm cơ bản (3-4 câu)\\n\\n2. CÔNG THỨC/QUY TẮC CHÍNH: Liệt kê tất cả công thức quan trọng với giải thích\\n\\n3. CÁCH ÁP DỤNG: Hướng dẫn từng bước cách sử dụng công thức/quy tắc (4-5 bước chi tiết)\\n\\n4. VÍ DỤ MINH HỌA: Ít nhất 1 ví dụ cụ thể với lời giải chi tiết\\n\\n5. LƯU Ý QUAN TRỌNG: Các điểm dễ nhầm lẫn cần chú ý",
    
    "detailed_concepts": [
        {{
            "concept_name": "Khái niệm/Kỹ thuật 1",
            "explanation": "Giải thích chi tiết 3-4 câu với ví dụ cụ thể",
            "example": "Ví dụ minh họa rõ ràng"
        }},
        {{
            "concept_name": "Khái niệm/Kỹ thuật 2",
            "explanation": "Giải thích chi tiết 3-4 câu với ví dụ cụ thể",
            "example": "Ví dụ minh họa rõ ràng"
        }},
        {{
            "concept_name": "Khái niệm/Kỹ thuật 3",
            "explanation": "Giải thích chi tiết 3-4 câu với ví dụ cụ thể",
            "example": "Ví dụ minh họa rõ ràng"
        }}
    ],
    
    "step_by_step_method": [
        "Bước 1: Mô tả chi tiết cách thực hiện bước này",
        "Bước 2: Mô tả chi tiết cách thực hiện bước này",
        "Bước 3: Mô tả chi tiết cách thực hiện bước này",
        "Bước 4: Mô tả chi tiết cách thực hiện bước này"
    ],
    
    "mistake_analysis": [
        {{
            "question_summary": "Tóm tắt ngắn câu hỏi",
            "user_mistake": "Học sinh đã chọn... vì hiểu sai rằng...",
            "why_wrong": "Lý do tại sao sai (chi tiết 2-3 câu)",
            "correct_approach": "Cách suy luận đúng từng bước với giải thích cụ thể"
        }}
    ],
    
    "common_mistakes": [
        "Lỗi 1: Mô tả chi tiết lỗi + Cách nhận biết + Cách tránh cụ thể",
        "Lỗi 2: Mô tả chi tiết lỗi + Cách nhận biết + Cách tránh cụ thể",
        "Lỗi 3: Mô tả chi tiết lỗi + Cách nhận biết + Cách tránh cụ thể",
        "Lỗi 4: Mô tả chi tiết lỗi + Cách nhận biết + Cách tránh cụ thể"
    ],
    
    "tips_for_accuracy": [
        "Mẹo 1: Kỹ thuật cụ thể với ví dụ áp dụng (2-3 câu)",
        "Mẹo 2: Kỹ thuật cụ thể với ví dụ áp dụng (2-3 câu)",
        "Mẹo 3: Kỹ thuật cụ thể với ví dụ áp dụng (2-3 câu)",
        "Mẹo 4: Kỹ thuật cụ thể với ví dụ áp dụng (2-3 câu)"
    ],
    
    "tips_for_speed": [
        "Mẹo tăng tốc 1: Kỹ thuật rút gọn cụ thể (2 câu)",
        "Mẹo tăng tốc 2: Kỹ thuật rút gọn cụ thể (2 câu)",
        "Mẹo tăng tốc 3: Kỹ thuật rút gọn cụ thể (2 câu)"
    ],
    
    "practice_drills": [
        "Bài tập 1: Mô tả bài tập ngắn để rèn kỹ năng cụ thể",
        "Bài tập 2: Mô tả bài tập ngắn để rèn kỹ năng cụ thể",
        "Bài tập 3: Mô tả bài tập ngắn để rèn kỹ năng cụ thể",
        "Bài tập 4: Mô tả bài tập ngắn để rèn kỹ năng cụ thể"
    ],
    
    "key_formulas": [
        "Công thức 1: Diễn giải + Khi nào dùng",
        "Công thức 2: Diễn giải + Khi nào dùng",
        "Công thức 3: Diễn giải + Khi nào dùng"
    ]
}}

YÊU CẦU QUAN TRỌNG:
- Phần "theory" PHẢI có cấu trúc 5 phần như mô tả (ĐỊNH NGHĨA, CÔNG THỨC, CÁCH ÁP DỤNG, VÍ DỤ, LƯU Ý)
- Phần "detailed_concepts" PHẢI có ít nhất 3 khái niệm với ví dụ cụ thể
- Phần "step_by_step_method" PHẢI có ít nhất 4 bước chi tiết
- Phân tích CỤ THỂ dựa trên các câu sai được cung cấp
- MỖI MỤC phải dài, chi tiết, CÓ VÍ DỤ
- Không viết chung chung - phải cụ thể, áp dụng được ngay
- Trả về JSON thuần, không có markdown
"""

        try:
            # Gọi API cho TỪNG topic
            response = model.models.generate_content(
                model='gemini-2.5-pro',
                contents=topic_prompt,
                config={
                    'temperature': 0.3,  # Giảm để tập trung, cụ thể
                    'max_output_tokens': 8192,  # Đủ cho 1 topic chi tiết
                    'top_p': 0.9,
                    'top_k': 30,
                    'response_mime_type': 'application/json'
                }
            )
            
            text = response.text if hasattr(response, 'text') else str(response)
            print(f"✅ Topic '{topic_name}': Generated {len(text)} chars")
            
            # Parse JSON response
            text = text.replace('```json', '').replace('```', '').strip()
            
            # Fix multiple closing braces (common AI error)
            # Replace }}} with }} at end of JSON
            text = re.sub(r'\}\}\}+\s*$', '}}', text)
            # Replace }]}} with }]} 
            text = re.sub(r'\}\]\}\}+', '}]}', text)
            
            # Validate JSON before parsing
            if not text or text == '{}':
                raise ValueError("Empty JSON response from API")
            
            topic_guide = json.loads(text)
            
            # Validate required fields
            required_fields = ['theory', 'detailed_concepts', 'step_by_step_method', 'common_mistakes', 'tips_for_accuracy']
            missing_fields = [f for f in required_fields if f not in topic_guide or not topic_guide[f]]
            if missing_fields:
                print(f"⚠️ Missing fields in response for '{topic_name}': {missing_fields}")
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Thêm metadata
            topic_guide['topic'] = topic_name
            topic_guide['accuracy'] = round(accuracy, 0)
            topic_guide['importance'] = importance
            topic_guide['priority_level'] = priority
            topic_guide['stats'] = {
                'total': data['total'],
                'correct': data['correct'],
                'wrong': data['wrong']
            }
            
            all_topics_guides.append(topic_guide)
            
        except Exception as e:
            print(f"⚠️ Lỗi phân tích topic '{topic_name}': {e}")
            import traceback
            traceback.print_exc()
            
            # Thử lấy từ knowledge base, nếu không có thì tạo fallback
            knowledge_base = _get_topic_knowledge_base()
            if topic_name in knowledge_base:
                kb_data = knowledge_base[topic_name]
                all_topics_guides.append({
                    'topic': topic_name,
                    'accuracy': round(accuracy, 0),
                    'importance': importance,
                    'priority_level': priority,
                    'theory': kb_data['theory'],
                    'detailed_concepts': kb_data.get('detailed_concepts', []),
                    'step_by_step_method': kb_data.get('step_by_step_method', []),
                    'mistake_analysis': [],
                    'common_mistakes': kb_data.get('common_mistakes', [f"Bạn sai {wrong_count} câu ở {topic_name}. Cần ôn lại lý thuyết."]),
                    'tips_for_accuracy': kb_data.get('tips_for_accuracy', []),
                    'tips_for_speed': kb_data.get('tips_for_speed', []),
                    'practice_drills': kb_data.get('practice_drills', []),
                    'key_formulas': kb_data.get('key_formulas', []),
                    'stats': {
                        'total': data['total'],
                        'correct': data['correct'],
                        'wrong': data['wrong']
                    }
                })
            else:
                # Fallback chung chung cho topic không trong knowledge base
                all_topics_guides.append({
                    'topic': topic_name,
                    'accuracy': round(accuracy, 0),
                    'importance': importance,
                    'priority_level': priority,
                    'theory': f"Cần ôn tập lại kiến thức cơ bản về {topic_name}. Hãy xem lại định nghĩa, công thức và cách áp dụng trong các bài toán. Luyện tập thêm để nắm vững.",
                    'detailed_concepts': [
                        {'concept_name': f'Khái niệm cơ bản {topic_name}', 'explanation': 'Cần ôn lại từ đầu', 'example': 'Xem sách giáo khoa'}
                    ],
                    'step_by_step_method': [
                        'Bước 1: Đọc kỹ đề bài',
                        'Bước 2: Xác định dạng bài',
                        'Bước 3: Áp dụng công thức',
                        'Bước 4: Kiểm tra kết quả'
                    ],
                    'mistake_analysis': [],
                    'common_mistakes': [f"Bạn sai {wrong_count} câu ở {topic_name}. Cần ôn lại lý thuyết."],
                    'tips_for_accuracy': [f"Ôn lại lý thuyết {topic_name} từ sách cơ bản"],
                    'tips_for_speed': ["Luyện tập thêm để tăng tốc độ"],
                    'practice_drills': [f"Làm thêm {max(5, wrong_count * 2)} bài tập về {topic_name}"],
                    'key_formulas': ["Xem lại công thức cơ bản"],
                    'stats': {
                        'total': data['total'],
                        'correct': data['correct'],
                        'wrong': data['wrong']
                    }
                })
    
    # Tạo tổng quan
    total_correct = sum(d['correct'] for d in topic_analysis.values())
    total_questions = sum(d['total'] for d in topic_analysis.values())
    total_wrong = sum(d['wrong'] for d in topic_analysis.values())
    overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    return {
        'overall_summary': f"Kết quả: {total_correct}/{total_questions} đúng ({overall_accuracy:.0f}%). Bạn cần tập trung ôn tập {total_wrong} câu sai, đặc biệt các chủ đề: {', '.join([t['topic'] for t in all_topics_guides[:3] if t.get('importance') in ['high', 'medium']])}.",
        'topics': all_topics_guides
    }


def _create_fallback_study_guide(topic_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tạo study guide đơn giản khi AI parse JSON fail hoặc API error
    """
    print(f"📊 Creating fallback study guide...")
    topics = []
    
    for topic_name, data in sorted(
        topic_analysis.items(),
        key=lambda x: x[1]['wrong'],
        reverse=True
    ):
        accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        importance = 'high' if accuracy < 60 else ('medium' if accuracy < 80 else 'low')
        
        topic_guide = {
            'topic': topic_name,
            'accuracy': round(accuracy, 0),
            'importance': importance,
            'priority_level': 1 if importance == 'high' else (2 if importance == 'medium' else 3),
            'theory': f"Ôn tập lại {topic_name} từ cơ bản. Bạn sai {data['wrong']} câu, cần xem lại lý thuyết, công thức và cách áp dụng. Làm thêm bài tập để củng cố.",
            'detailed_concepts': [
                {'concept_name': f'Khái niệm cơ bản {topic_name}', 'explanation': f'Cần nắm vững định nghĩa và ứng dụng của {topic_name}', 'example': 'Xem sách giáo khoa và làm bài tập mẫu'},
                {'concept_name': 'Ứng dụng thực tế', 'explanation': f'Áp dụng {topic_name} trong các bài toán GMAT', 'example': 'Luyện tập các dạng bài thường gặp'},
                {'concept_name': 'Liên kết kiến thức', 'explanation': f'Kết hợp {topic_name} với các chủ đề khác', 'example': 'Hiểu mối quan hệ giữa các topic'}
            ],
            'step_by_step_method': [
                'Bước 1: Đọc đề kỹ lưỡng và xác định yêu cầu',
                'Bước 2: Xác định dạng bài và phương pháp giải',
                'Bước 3: Áp dụng công thức/quy tắc phù hợp',
                'Bước 4: Kiểm tra lại kết quả và logic'
            ],
            'mistake_analysis': [],
            'common_mistakes': [
                f"Bạn trả lời sai {data['wrong']} câu ({100-accuracy:.0f}% tỷ lệ sai)",
                f"Các lỗi phổ biến: nhầm lẫn định nghĩa, tính toán sai, hiểu sai đề",
                f"Cách tránh: đọc kỹ đề, kiểm tra lại, ôn lại công thức"
            ],
            'tips_for_accuracy': [
                f"Ôn tập lại {topic_name} từ sách cơ bản",
                f"Làm thêm {max(5, data['wrong'] * 2)} bài tập thực hành",
                f"Ghi chép lại các lỗi sai và cách giải quyết"
            ],
            'tips_for_speed': [
                f"Dành {max(1, 30 // len(topic_analysis))} phút cho mỗi câu {topic_name}",
                "Nếu quá khó, bỏ qua và quay lại sau"
            ],
            'practice_drills': [
                f"Làm {max(5, data['wrong'] * 2)} bài tập {topic_name}",
                "Làm lại các câu sai để hiểu rõ lý do",
                "Tham khảo lời giải chi tiết"
            ],
            'key_formulas': [
                f"Công thức cơ bản {topic_name}: Xem lại sách giáo khoa",
                "Quy tắc quan trọng: Ôn lại định nghĩa"
            ],
            'stats': {
                'total': data['total'],
                'correct': data['correct'],
                'wrong': data['wrong']
            }
        }
        topics.append(topic_guide)
    
    return {
        'overall_summary': f"Bạn cần ôn tập {sum(d['wrong'] for d in topic_analysis.values())} câu sai. Hãy tập trung vào các topic có tỷ lệ sai cao. Với sự kiên trì và luyện tập thêm, bạn sẽ cải thiện điểm số!",
        'topics': topics,
        'recommended_focus': [f"{t['topic']}" for t in topics[:3]],
        'next_steps': f"Ngày 1-2: Ôn lại lý thuyết các topic dễ sai. Ngày 3-4: Làm bài tập thực hành. Ngày 5-6: Làm lại các câu sai. Ngày 7: Kiểm tra toàn diện.",
        'practice_resources': [
            "Sách GMAT chính thức: Luyện tập các dạng bài",
            "Bài tập online: Làm thêm 50+ bài tập theo topic"
        ],
        'motivation_message': "Hãy nhớ rằng mỗi lần sai là cơ hội để học. Tiếp tục cố gắng và bạn sẽ đạt điểm cao!"
    }

def format_study_guide_html(study_data: Dict[str, Any]) -> str:
    """
    Chuyển study guide data thành HTML đẹp để hiển thị trong Streamlit
    """
    if 'error' in study_data:
        return f"<div style='color:red;'>❌ {study_data['error']}</div>"
    
    html = "<div style='font-family: system-ui; max-width: 1200px;'>"
    
    # Overall Summary - Improved styling
    summary = study_data.get('overall_summary', '')
    if summary:
        html += f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 25px; border-radius: 15px; margin-bottom: 25px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h2 style='margin:0 0 15px 0; font-size: 24px;'>📊 Tổng quan kết quả</h2>
            <p style='margin:0; font-size: 16px; line-height: 1.8; opacity: 0.95;'>{summary}</p>
        </div>
        """
    
    # Topics with improved design
    topics = study_data.get('topics', [])
    for idx, topic in enumerate(topics, 1):
        importance = topic.get('importance', 'medium')
        color_map = {
            'high': '#dc3545',
            'medium': '#fd7e14',
            'low': '#28a745'
        }
        bg_color_map = {
            'high': '#fff5f5',
            'medium': '#fff8f0',
            'low': '#f0f9f4'
        }
        icon_map = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        
        color = color_map.get(importance, '#666')
        bg_color = bg_color_map.get(importance, '#f8f9fa')
        icon = icon_map.get(importance, '⭕')
        
        stats = topic.get('stats', {})
        accuracy = (stats.get('correct', 0) / stats.get('total', 1) * 100) if stats.get('total', 1) > 0 else 0
        
        html += f"""
        <div style='border: 2px solid {color}; border-radius: 12px; 
                    padding: 25px; margin-bottom: 25px; background: {bg_color};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'>
                <h3 style='color: {color}; margin: 0; font-size: 20px;'>
                    {icon} {topic['topic']}
                </h3>
                <div style='background: white; padding: 8px 15px; border-radius: 20px; 
                           border: 2px solid {color}; font-weight: bold; color: {color};'>
                    {stats.get('correct', 0)}/{stats.get('total', 0)} đúng ({accuracy:.0f}%)
                </div>
            </div>
        """
        
        # Priority badge
        priority = topic.get('priority_level', 2)
        if priority == 1:
            html += """
            <div style='background: #ff4444; color: white; display: inline-block; 
                       padding: 5px 15px; border-radius: 15px; font-size: 12px; 
                       font-weight: bold; margin-bottom: 15px;'>
                ⚡ ƯU TIÊN CAO
            </div>
            """
        
        # Key Concepts - Improved
        concepts = topic.get('key_concepts', [])
        if concepts:
            html += """
            <div style='background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                <h4 style='margin: 0 0 10px 0; color: #495057; font-size: 16px;'>💡 Kiến thức cốt lõi</h4>
                <ul style='margin: 0; padding-left: 20px;'>
            """
            for concept in concepts:
                html += f"<li style='margin-bottom: 8px; line-height: 1.6;'>{concept}</li>"
            html += "</ul></div>"
        
        # Common Mistakes - Improved
        mistakes = topic.get('common_mistakes', [])
        if mistakes:
            html += """
            <div style='background: #fff5f5; padding: 15px; border-radius: 8px; 
                       margin-bottom: 15px; border-left: 4px solid #dc3545;'>
                <h4 style='margin: 0 0 10px 0; color: #dc3545; font-size: 16px;'>⚠️ Lỗi thường gặp</h4>
                <ul style='margin: 0; padding-left: 20px;'>
            """
            for mistake in mistakes:
                html += f"<li style='margin-bottom: 8px; line-height: 1.6; color: #721c24;'>{mistake}</li>"
            html += "</ul></div>"
        
        # Study Tips - Improved
        tips = topic.get('study_tips', [])
        if tips:
            html += """
            <div style='background: #f0f9f4; padding: 15px; border-radius: 8px; 
                       margin-bottom: 15px; border-left: 4px solid #28a745;'>
                <h4 style='margin: 0 0 10px 0; color: #28a745; font-size: 16px;'>✨ Mẹo học tập</h4>
                <ul style='margin: 0; padding-left: 20px;'>
            """
            for tip in tips:
                html += f"<li style='margin-bottom: 8px; line-height: 1.6; color: #155724;'>{tip}</li>"
            html += "</ul></div>"
        
        # Practice Approach - Improved
        approach = topic.get('practice_approach', '')
        if approach:
            html += f"""
            <div style='background: linear-gradient(to right, #e3f2fd, #bbdefb); 
                       padding: 15px; border-radius: 8px; margin-bottom: 15px;
                       border-left: 4px solid #2196f3;'>
                <h4 style='margin: 0 0 10px 0; color: #0d47a1; font-size: 16px;'>🎯 Cách tiếp cận</h4>
                <p style='margin: 0; line-height: 1.7; color: #1565c0;'>{approach}</p>
            </div>
            """
        
        # Formulas or Rules - Improved
        formulas = topic.get('formulas_or_rules', [])
        if formulas:
            html += """
            <div style='background: #fff8e1; padding: 15px; border-radius: 8px; 
                       margin-bottom: 15px; border-left: 4px solid #ffa726;'>
                <h4 style='margin: 0 0 10px 0; color: #e65100; font-size: 16px;'>📐 Công thức/Quy tắc</h4>
                <ul style='margin: 0; padding-left: 20px;'>
            """
            for formula in formulas:
                html += f"""
                <li style='margin-bottom: 8px; font-family: "Courier New", monospace; 
                          background: white; padding: 8px; border-radius: 4px; 
                          font-size: 14px; border: 1px solid #ffe0b2;'>{formula}</li>
                """
            html += "</ul></div>"
        
        # Time Management Tip - Improved
        time_tip = topic.get('time_management_tip', '')
        if time_tip:
            html += f"""
            <div style='background: white; padding: 12px 15px; border-radius: 8px; 
                       border: 2px dashed #17a2b8; color: #0c5460;'>
                <strong>⏱️ Quản lý thời gian:</strong> {time_tip}
            </div>
            """
        
        html += "</div>"  # Close topic card
    
    # Recommended Focus - Improved
    focus = study_data.get('recommended_focus', [])
    if focus:
        html += """
        <div style='background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%); 
                    padding: 25px; border-radius: 15px; margin-bottom: 25px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='margin: 0 0 15px 0; color: #6c3483; font-size: 20px;'>
                🎯 Ưu tiên ôn tập ngay
            </h3>
            <ol style='margin: 0; padding-left: 20px; font-size: 16px;'>
        """
        for item in focus:
            html += f"<li style='margin-bottom: 10px; color: #6c3483; font-weight: 500;'>{item}</li>"
        html += "</ol></div>"
    
    # Next Steps - Improved
    next_steps = study_data.get('next_steps', '')
    if next_steps:
        html += f"""
        <div style='background: linear-gradient(135deg, #a8e6cf 0%, #56ccf2 100%); 
                    padding: 25px; border-radius: 15px; margin-bottom: 25px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='margin: 0 0 15px 0; color: #0d47a1; font-size: 20px;'>
                📅 Lộ trình ôn tập 7 ngày
            </h3>
            <p style='margin: 0; line-height: 1.8; color: #1565c0; font-size: 15px; white-space: pre-line;'>{next_steps}</p>
        </div>
        """
    
    # Practice Resources - Improved
    resources = study_data.get('practice_resources', [])
    if resources:
        html += """
        <div style='background: white; border: 2px solid #ffc107; 
                    padding: 25px; border-radius: 15px; margin-bottom: 25px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='margin: 0 0 15px 0; color: #f57c00; font-size: 20px;'>
                📖 Nguồn tài liệu học tập
            </h3>
            <ul style='margin: 0; padding-left: 20px; font-size: 15px;'>
        """
        for resource in resources:
            html += f"<li style='margin-bottom: 12px; line-height: 1.6; color: #e65100;'>{resource}</li>"
        html += "</ul></div>"
    
    # Motivation Message - Improved
    motivation = study_data.get('motivation_message', '')
    if motivation:
        html += f"""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    color: white; padding: 30px; border-radius: 15px; text-align: center;
                    box-shadow: 0 6px 12px rgba(0,0,0,0.15);'>
            <h3 style='margin: 0 0 15px 0; font-size: 22px;'>💪 Lời động viên</h3>
            <p style='margin: 0; font-size: 17px; line-height: 1.8; font-style: italic; opacity: 0.95;'>
                "{motivation}"
            </p>
        </div>
        """
    
    html += "</div>"
    return html


def generate_study_guide_pdf(study_data: Dict[str, Any]) -> bytes:
    """
    Generate a beautifully formatted PDF from study guide data
    
    Args:
        study_data: Study guide dictionary from generate_study_guide()
    
    Returns:
        PDF file as bytes, or None if reportlab not available
    """
    
    def _register_vn_font():
        """Try to register a Unicode font that supports Vietnamese diacritics."""
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            font_candidates = [
                ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                ("NotoSans", "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
                ("ArialUnicode", "C:/Windows/Fonts/ARIALUNI.TTF"),
                ("Arial", "C:/Windows/Fonts/arial.ttf"),
            ]
            for name, path in font_candidates:
                if Path(path).exists():
                    pdfmetrics.registerFont(TTFont(name, path))
                    return name
        except Exception:
            return None
        return None

    def clean_text_for_pdf(text, keep_unicode: bool):
        """Normalize text; optionally keep Unicode if font supports it."""
        if not isinstance(text, str):
            text = str(text)

        # Remove emojis/high codepoints that typical fonts can't render well
        text = ''.join(ch for ch in text if ord(ch) < 0x1F600 or ord(ch) > 0x1F64F)

        if keep_unicode:
            return text

        # Fallback ASCII mapping (old behavior)
        vietnamese_map = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
            'đ': 'd', 'Đ': 'D',
            'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
            'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
            'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
            'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
            'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
            'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
            'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
            'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
            'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
            'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
            'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
            'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
        }
        for viet_char, ascii_char in vietnamese_map.items():
            text = text.replace(viet_char, ascii_char)
        cleaned = ''.join(ch for ch in text if ord(ch) < 128 or ch in '°×÷±')
        return cleaned
    
    try:
        from io import BytesIO
        from datetime import datetime
        
        # Try to import reportlab - if fails, show helpful message
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        except ImportError:
            print("⚠️ ReportLab không được cài đặt trên Streamlit Cloud")
            print("📋 Cách khắc phục:")
            print("  1. Kiểm tra requirements.txt đã có 'reportlab' chưa")
            print("  2. Nếu chưa, thêm dòng: reportlab")
            print("  3. Commit và push code")
            print("  4. Streamlit Cloud sẽ tự động cài đặt")
            return None
        
        # Try register Unicode font for Vietnamese
        font_name = _register_vn_font()
        unicode_font = bool(font_name)
        if not font_name:
            font_name = 'Helvetica'
        bold_font_name = font_name

        # Create PDF buffer
        pdf_buffer = BytesIO()
        
        # Create PDF document with A4 size
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            title="Study Guide GMAT"
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0066cc'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName=bold_font_name
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0066cc'),
            spaceAfter=6,
            spaceBefore=12,
            fontName=bold_font_name
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            fontName=bold_font_name
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14,
            fontName=font_name
        )
        
        # Story to hold all PDF elements
        story = []
        
        # Title
        story.append(Paragraph("TAI LIEU ON TAP GMAT CA NHAN HOA", title_style))
        story.append(Paragraph(f"Duoc tao vao: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Overall summary
        overall = study_data.get('overall_summary', '')
        if overall:
            story.append(Paragraph("Tong Quan Ket Qua", heading_style))
            story.append(Paragraph(clean_text_for_pdf(overall, unicode_font), body_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Topics
        topics = study_data.get('topics', [])
        for idx, topic in enumerate(topics):
            if idx > 0:
                story.append(PageBreak())
            
            topic_name = clean_text_for_pdf(topic.get('topic', 'Chu de'), unicode_font)
            stats = topic.get('stats', {})
            accuracy = (stats.get('correct', 0) / stats.get('total', 1) * 100) if stats.get('total', 1) > 0 else 0
            
            # Topic header
            story.append(Paragraph(topic_name, heading_style))
            
            # Statistics
            stats_text = f"Ket qua: {stats.get('correct', 0)}/{stats.get('total', 0)} dung ({accuracy:.0f}%)"
            story.append(Paragraph(stats_text, styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
            
            # Theory
            theory = topic.get('theory', '')
            if theory:
                story.append(Paragraph("Ly Thuyet", subheading_style))
                # Handle both string and dictionary theory formats
                if isinstance(theory, str):
                    # Clean up theory text for better PDF rendering
                    theory_clean = clean_text_for_pdf(theory, unicode_font).replace('\n\n', '<br/><br/>').replace('\n', ' ')
                    story.append(Paragraph(theory_clean[:2000], body_style))  # Limit length
                elif isinstance(theory, dict):
                    # Convert dictionary theory to formatted text
                    theory_parts = []
                    if 'title' in theory:
                        theory_parts.append(f"<b>{clean_text_for_pdf(theory['title'], unicode_font)}</b>")
                    if 'definition' in theory:
                        theory_parts.append(f"<br/><b>Dinh nghia:</b> {clean_text_for_pdf(theory['definition'][:500], unicode_font)}")
                    if 'main_rules' in theory and theory['main_rules']:
                        theory_parts.append("<br/><b>Quy tac chinh:</b>")
                        for i, rule in enumerate(theory['main_rules'][:3], 1):
                            if isinstance(rule, dict):
                                rule_name = clean_text_for_pdf(rule.get('rule_name', ''), unicode_font)
                                theory_parts.append(f"<br/>{i}. {rule_name}")
                            else:
                                theory_parts.append(f"<br/>{i}. {clean_text_for_pdf(str(rule), unicode_font)}")
                    theory_text = ' '.join(theory_parts)[:2000]  # Limit total length
                    story.append(Paragraph(theory_text, body_style))
                else:
                    # Fallback for other types
                    story.append(Paragraph(clean_text_for_pdf(str(theory), unicode_font)[:2000], body_style))
                story.append(Spacer(1, 0.1*inch))
            
            # Detailed concepts
            concepts = topic.get('detailed_concepts', [])
            if concepts:
                story.append(Paragraph("Cac Khai Niem Chi Tiet", subheading_style))
                for concept in concepts[:3]:  # Limit to 3 concepts
                    concept_name = clean_text_for_pdf(concept.get('concept_name', ''), unicode_font)
                    explanation = clean_text_for_pdf(concept.get('explanation', ''), unicode_font)
                    story.append(Paragraph(f"<b>• {concept_name}:</b>", body_style))
                    story.append(Paragraph(explanation, body_style))
                story.append(Spacer(1, 0.1*inch))
            
            # Step by step method
            steps = topic.get('step_by_step_method', [])
            if steps:
                story.append(Paragraph("Phuong Phap Tung Buoc", subheading_style))
                for i, step in enumerate(steps, 1):
                    story.append(Paragraph(f"<b>Buoc {i}:</b> {clean_text_for_pdf(step, unicode_font)}", body_style))
                story.append(Spacer(1, 0.1*inch))
            
            # Common mistakes
            mistakes = topic.get('common_mistakes', [])
            if mistakes:
                story.append(Paragraph("Loi Pho Bien", subheading_style))
                for mistake in mistakes[:4]:  # Limit to 4 mistakes
                    story.append(Paragraph(f"• {clean_text_for_pdf(mistake, unicode_font)}", body_style))
                story.append(Spacer(1, 0.1*inch))
            
            # Tips
            tips_accuracy = topic.get('tips_for_accuracy', [])
            if tips_accuracy:
                story.append(Paragraph("Meo Tang Ty Le Dung", subheading_style))
                for tip in tips_accuracy[:3]:  # Limit to 3 tips
                    story.append(Paragraph(f"• {clean_text_for_pdf(tip, unicode_font)}", body_style))
            
            tips_speed = topic.get('tips_for_speed', [])
            if tips_speed:
                story.append(Paragraph("Meo Tang Toc Do", subheading_style))
                for tip in tips_speed[:2]:  # Limit to 2 tips
                    story.append(Paragraph(f"• {clean_text_for_pdf(tip, unicode_font)}", body_style))
            
            # Practice drills
            drills = topic.get('practice_drills', [])
            if drills:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("Bai Tap Luyen Tap", subheading_style))
                for drill in drills[:4]:  # Limit to 4 drills
                    story.append(Paragraph(f"• {clean_text_for_pdf(drill, unicode_font)}", body_style))
            
            # Key formulas
            formulas = topic.get('key_formulas', [])
            if formulas:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("Cong Thuc Can Nho", subheading_style))
                for formula in formulas[:4]:  # Limit to 4 formulas
                    story.append(Paragraph(f"• {clean_text_for_pdf(formula, unicode_font)}", body_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        return pdf_bytes
        
    except ImportError as e:
        print(f"⚠️ Lỗi: Cần cài đặt reportlab. Chạy: pip install reportlab")
        print(f"Chi tiết lỗi: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Lỗi tạo PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_study_guide_text_formatted(study_data: Dict[str, Any]) -> str:
    """
    Generate a beautifully formatted text document (alternative to PDF)
    Can be easily converted to PDF using online tools
    
    Args:
        study_data: Study guide dictionary
    
    Returns:
        Formatted text content as string
    """
    from datetime import datetime
    
    text = ""
    
    # Title
    text += "=" * 80 + "\n"
    text += "TÀI LIỆU ÔN TẬP GMAT CÁ NHÂN HÓA\n"
    text += "=" * 80 + "\n\n"
    text += f"Được tạo vào: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
    
    # Overall summary
    overall = study_data.get('overall_summary', '')
    if overall:
        text += "📊 TỔNG QUAN KẾT QUẢ\n"
        text += "-" * 80 + "\n"
        text += overall + "\n\n"
    
    # Topics
    topics = study_data.get('topics', [])
    for idx, topic in enumerate(topics, 1):
        if idx > 1:
            text += "\n" + "=" * 80 + "\n"
        
        topic_name = topic.get('topic', 'Chủ đề')
        stats = topic.get('stats', {})
        accuracy = (stats.get('correct', 0) / stats.get('total', 1) * 100) if stats.get('total', 1) > 0 else 0
        
        # Topic header
        text += f"\nCHỦ ĐỀ {idx}: {topic_name}\n"
        text += "=" * 80 + "\n"
        text += f"Kết quả: {stats.get('correct', 0)}/{stats.get('total', 0)} đúng ({accuracy:.0f}%)\n\n"
        
        # Theory
        theory = topic.get('theory', '')
        if theory:
            text += "LÝ THUYẾT\n"
            text += "-" * 80 + "\n"
            # Handle both string and dictionary theory formats
            if isinstance(theory, str):
                text += theory + "\n\n"
            elif isinstance(theory, dict):
                # Convert dictionary theory to formatted text
                if 'title' in theory:
                    text += f"{theory['title']}\n\n"
                if 'definition' in theory:
                    text += f"ĐỊNH NGHĨA:\n{theory['definition']}\n\n"
                if 'main_rules' in theory and theory['main_rules']:
                    text += "QUY TẮC CHÍNH:\n"
                    for i, rule in enumerate(theory['main_rules'], 1):
                        if isinstance(rule, dict):
                            text += f"{i}. {rule.get('rule_name', '')}\n"
                            if rule.get('formula'):
                                text += f"   Công thức: {rule['formula']}\n"
                            if rule.get('explanation'):
                                text += f"   {rule['explanation']}\n"
                        else:
                            text += f"{i}. {rule}\n"
                    text += "\n"
                if 'application_steps' in theory and theory['application_steps']:
                    steps_data = theory['application_steps']
                    if isinstance(steps_data, dict) and 'steps' in steps_data:
                        text += f"{steps_data.get('title', 'CÁC BƯỚC ÁP DỤNG')}:\n"
                        for i, step in enumerate(steps_data['steps'], 1):
                            text += f"{i}. {step}\n"
                        text += "\n"
                if 'example_analysis' in theory and theory['example_analysis']:
                    example = theory['example_analysis']
                    if isinstance(example, dict):
                        text += "VÍ DỤ MINH HỌA:\n"
                        if 'sequence' in example:
                            text += f"Dãy: {example['sequence']}\n"
                        if 'solution' in example:
                            text += f"Lời giải: {example['solution']}\n"
                        text += "\n"
                if 'important_notes' in theory:
                    text += f"LƯU Ý QUAN TRỌNG:\n{theory['important_notes']}\n\n"
            else:
                text += str(theory) + "\n\n"
        
        # Detailed concepts
        concepts = topic.get('detailed_concepts', [])
        if concepts:
            text += "CÁC KHÁI NIỆM CHI TIẾT\n"
            text += "-" * 80 + "\n"
            for i, concept in enumerate(concepts, 1):
                concept_name = concept.get('concept_name', '')
                explanation = concept.get('explanation', '')
                example = concept.get('example', '')
                text += f"\n{i}. {concept_name}\n"
                text += f"   Giải thích: {explanation}\n"
                if example:
                    text += f"   Ví dụ: {example}\n"
            text += "\n"
        
        # Step by step method
        steps = topic.get('step_by_step_method', [])
        if steps:
            text += "PHƯƠNG PHÁP TỪNG BƯỚC\n"
            text += "-" * 80 + "\n"
            for i, step in enumerate(steps, 1):
                text += f"{i}. {step}\n"
            text += "\n"
        
        # Common mistakes
        mistakes = topic.get('common_mistakes', [])
        if mistakes:
            text += "LỖI PHỔ BIẾN\n"
            text += "-" * 80 + "\n"
            for mistake in mistakes[:5]:
                text += f"• {mistake}\n"
            text += "\n"
        
        # Tips
        tips_accuracy = topic.get('tips_for_accuracy', [])
        if tips_accuracy:
            text += "MẸO TĂNG TỶ LỆ ĐÚNG\n"
            text += "-" * 80 + "\n"
            for tip in tips_accuracy[:4]:
                text += f"• {tip}\n"
            text += "\n"
        
        tips_speed = topic.get('tips_for_speed', [])
        if tips_speed:
            text += "MẸO TĂNG TỐC ĐỘ\n"
            text += "-" * 80 + "\n"
            for tip in tips_speed[:3]:
                text += f"• {tip}\n"
            text += "\n"
        
        # Practice drills
        drills = topic.get('practice_drills', [])
        if drills:
            text += "BÀI TẬP LUYỆN TẬP\n"
            text += "-" * 80 + "\n"
            for drill in drills[:4]:
                text += f"• {drill}\n"
            text += "\n"
        
        # Key formulas
        formulas = topic.get('key_formulas', [])
        if formulas:
            text += "CÔNG THỨC CẦN NHỚ\n"
            text += "-" * 80 + "\n"
            for formula in formulas[:5]:
                text += f"• {formula}\n"
            text += "\n"
    
    text += "\n" + "=" * 80 + "\n"
    text += "HẾT\n"
    text += "=" * 80 + "\n"
    
    return text
