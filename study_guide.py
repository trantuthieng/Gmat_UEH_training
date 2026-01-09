import google.genai as genai
import os
import json
import re
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
            
            topic_guide = json.loads(text)
            
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
            # Fallback đơn giản cho topic này
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

