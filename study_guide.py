from google import genai
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
    """Khởi tạo model Gemini cho ôn tập (dùng model nhanh hơn)"""
    key = _get_api_key()
    if not key:
        print("GEMINI_API_KEY not found")
        return None
    
    try:
        client = genai.Client(api_key=key)
        
        class _StudyModelWrapper:
            def __init__(self, client, model_name: str):
                self._client = client
                self._model = model_name
            
            def generate_content(self, prompt, generation_config=None):
                cfg = None
                if generation_config:
                    try:
                        from google.genai import types as genai_types
                        cfg = genai_types.GenerateContentConfig(**generation_config)
                    except Exception:
                        cfg = generation_config
                return self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=cfg,
                )
        
        # Dùng gemini-2.5-flash-lite (model hỗ trợ generateContent, chi phí thấp)
        return _StudyModelWrapper(client, 'gemini-2.5-flash-lite')
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
    
    # Phân tích câu sai và đúng theo topic
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
                'questions': []
            }
        
        topic_analysis[topic]['total'] += 1
        if is_correct:
            topic_analysis[topic]['correct'] += 1
        else:
            topic_analysis[topic]['wrong'] += 1
        
        topic_analysis[topic]['questions'].append({
            'question': q.get('question', ''),
            'correct_answer': correct_answer,
            'explanation': q.get('explanation', ''),
            'is_correct': is_correct
        })
    
    # Tạo prompt ĐẦY ĐỦ để AI sinh TẤT CẢ nội dung trong 1 lần gọi
    topics_summary = []
    for topic, data in topic_analysis.items():
        accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
        topics_summary.append(f"- {topic}: {data['correct']}/{data['total']} đúng ({accuracy:.0f}%)")
    
    # Tạo danh sách chi tiết các câu hỏi để AI có đủ context
    questions_details = []
    for topic, data in topic_analysis.items():
        for q in data['questions'][:3]:  # Lấy max 3 câu đại diện mỗi topic
            questions_details.append({
                'topic': topic,
                'question': q['question'][:150],  # Cắt ngắn để tiết kiệm token
                'is_correct': q['is_correct']
            })
    
    prompt = f"""
Bạn là giáo viên GMAT chuyên nghiệp. Học sinh vừa hoàn thành bài thi 30 câu với kết quả:

KẾT QUẢ THEO TOPIC:
{chr(10).join(topics_summary)}

NHIỆM VỤ: Tạo tài liệu ôn tập ĐẦY ĐỦ, CHI TIẾT trong 1 lần trả lời duy nhất.

YÊU CẦU OUTPUT (JSON format - PHẢI ĐẦY ĐỦ TẤT CẢ TRƯỜNG):
{{
    "overall_summary": "Nhận xét tổng quan về kết quả học sinh (3-4 câu). Phân tích điểm mạnh, điểm yếu rõ ràng.",
    
    "topics": [
        {{
            "topic": "Tên chủ đề chính xác",
            "accuracy": 60,
            "importance": "high",
            "priority_level": 1,
            
            "key_concepts": [
                "{{Khái niệm 1}}: {{Giải thích chi tiết 2-3 câu với ví dụ cụ thể}}",
                "{{Khái niệm 2}}: {{Giải thích chi tiết 2-3 câu với ví dụ cụ thể}}",
                "{{Khái niệm 3}}: {{Giải thích chi tiết 2-3 câu với ví dụ cụ thể}}"
            ],
            
            "common_mistakes": [
                "{{Lỗi 1}}: {{Mô tả lỗi}} - {{Cách tránh cụ thể}}",
                "{{Lỗi 2}}: {{Mô tả lỗi}} - {{Cách tránh cụ thể}}",
                "{{Lỗi 3}}: {{Mô tả lỗi}} - {{Cách tránh cụ thể}}"
            ],
            
            "study_tips": [
                "{{Mẹo 1}}: {{Chi tiết cách học và luyện tập 2-3 câu}}",
                "{{Mẹo 2}}: {{Chi tiết cách học và luyện tập 2-3 câu}}",
                "{{Mẹo 3}}: {{Chi tiết cách học và luyện tập 2-3 câu}}"
            ],
            
            "practice_approach": "Hướng dẫn chi tiết cách tiếp cận bài tập dạng này. Bao gồm: (1) Cách đọc đề, (2) Các bước giải quyết, (3) Mẹo nhận biết bẫy. Tối thiểu 4-5 câu có ví dụ cụ thể.",
            
            "formulas_or_rules": [
                "{{Công thức/Quy tắc 1 nếu có}}",
                "{{Công thức/Quy tắc 2 nếu có}}"
            ],
            
            "time_management_tip": "Mẹo quản lý thời gian khi làm dạng bài này (1-2 câu)"
        }}
    ],
    
    "recommended_focus": [
        "{{Chủ đề ưu tiên 1}} - Lý do cụ thể tại sao cần ưu tiên",
        "{{Chủ đề ưu tiên 2}} - Lý do cụ thể tại sao cần ưu tiên",
        "{{Chủ đề ưu tiên 3}} - Lý do cụ thể tại sao cần ưu tiên"
    ],
    
    "next_steps": "Kế hoạch học tập CỤ THỂ cho 7 ngày tới. Bao gồm: Ngày 1-2 làm gì, Ngày 3-4 làm gì, Ngày 5-7 làm gì. Tối thiểu 5-6 câu rất chi tiết.",
    
    "practice_resources": [
        "Nguồn học liệu 1: Mô tả và cách sử dụng",
        "Nguồn học liệu 2: Mô tả và cách sử dụng"
    ],
    
    "motivation_message": "Lời khuyên động viên cho học sinh (2-3 câu)"
}}

HƯỚNG DẪN QUAN TRỌNG:
1. Tạo nội dung cho TẤT CẢ các topic có trong kết quả (không bỏ sót)
2. Ưu tiên các topic có accuracy thấp (< 70%) - đánh dấu importance="high"
3. Mỗi phần PHẢI đầy đủ, chi tiết, CÓ VÍ DỤ CỤ THỂ
4. Không dùng placeholder như "...", "etc", phải viết đầy đủ
5. Trả về JSON thuần túy, KHÔNG có markdown formatting (```json)
6. Đảm bảo JSON hợp lệ, đóng mở ngoặc đúng

LƯU Ý: Đây là LẦN DUY NHẤT tôi gọi API, hãy trả về ĐẦY ĐỦ NHẤT có thể!
"""

    try:
        # GỌI API DUY NHẤT với config tối ưu
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7,  # Giảm temperature để ổn định hơn
                'max_output_tokens': 16384,  # Tăng lên tối đa để đảm bảo không bị cắt
                'top_p': 0.9,
                'top_k': 40
            }
        )
        
        # Clean response - xử lý kỹ để đảm bảo JSON hợp lệ
        text = response.text if hasattr(response, 'text') else str(response)
        print(f"📝 Raw response length: {len(text)} characters")
        print(f"📝 First 300 chars: {text[:300]}")
        
        # Remove markdown code fences
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Remove common unwanted prefixes/suffixes
        text = re.sub(r'^[^{]*', '', text)  # Xóa text trước dấu {
        text = text.lstrip()
        text = re.sub(r'[^}]*$', '}', text)  # Giữ chỉ tới dấu } cuối
        
        # Find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            print(f"❌ Không tìm thấy JSON object delimiters")
            return _create_fallback_study_guide(topic_analysis)
        
        text = text[start:end+1]
        print(f"✅ Extracted JSON: {len(text)} characters")
        
        # Try to parse JSON
        try:
            study_data = json.loads(text)
            print(f"✅ JSON parse successful on first attempt")
        except json.JSONDecodeError as parse_error:
            # Attempt basic repair: remove trailing comma before } or ]
            print(f"⚠️ First parse failed at position {parse_error.pos}, attempting repair...")
            text = re.sub(r',\s*([}\]])', r'\1', text)
            try:
                study_data = json.loads(text)
                print(f"✅ JSON repair successful")
            except json.JSONDecodeError:
                print(f"❌ JSON repair failed, using fallback")
                return _create_fallback_study_guide(topic_analysis)
        
        # Validate data structure
        if 'topics' not in study_data or not isinstance(study_data['topics'], list):
            print(f"⚠️ Invalid structure (missing topics array), using fallback")
            return _create_fallback_study_guide(topic_analysis)
        
        print(f"✅ Study guide hoàn chỉnh: {len(study_data['topics'])} topics")
        
        # Thêm thông tin chi tiết từ topic_analysis
        for topic_guide in study_data.get('topics', []):
            topic_name = topic_guide.get('topic', '')
            if topic_name in topic_analysis:
                topic_guide['stats'] = {
                    'total': topic_analysis[topic_name]['total'],
                    'correct': topic_analysis[topic_name]['correct'],
                    'wrong': topic_analysis[topic_name]['wrong']
                }
        
        return study_data
        
    except Exception as e:
        print(f"❌ Lỗi tạo study guide: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simple guide if anything fails
        return _create_fallback_study_guide(topic_analysis)


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
            'key_concepts': [
                f"Khái niệm cơ bản của {topic_name}",
                f"Ứng dụng thực tế trong bài thi GMAT",
                f"Liên kết với các chủ đề khác"
            ],
            'common_mistakes': [
                f"Bạn trả lời sai {data['wrong']} câu ({100-accuracy:.0f}% tỷ lệ sai)",
                f"Các lỗi phổ biến: nhầm lẫn định nghĩa, tính toán sai, hiểu sai đề",
                f"Cách tránh: đọc kỹ đề, kiểm tra lại, ôn lại công thức"
            ],
            'study_tips': [
                f"Ôn tập lại {topic_name} từ sách cơ bản",
                f"Làm thêm {max(5, data['wrong'] * 2)} bài tập thực hành",
                f"Ghi chép lại các lỗi sai và cách giải quyết"
            ],
            'practice_approach': f"Khi gặp câu {topic_name}: (1) Đọc đề kỹ lưỡng, (2) Xác định dạng bài, (3) Áp dụng công thức/quy tắc, (4) Kiểm tra lại kết quả. Tập trung vào các câu sai trước đây để hiểu rõ lý do.",
            'formulas_or_rules': [
                f"Quy tắc chính: Ôn lại định nghĩa cơ bản",
                f"Công thức quan trọng: Xem lại sách giáo khoa"
            ],
            'time_management_tip': f"Dành {max(1, 30 // len(topic_analysis))} phút để làm các câu {topic_name}. Nếu quá khó, bỏ qua và quay lại sau.",
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
    
    html = "<div style='font-family: system-ui;'>"
    
    # Overall Summary
    summary = study_data.get('overall_summary', '')
    if summary:
        html += f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='margin:0 0 10px 0;'>📊 Tổng quan kết quả</h2>
            <p style='margin:0; font-size: 16px; line-height: 1.6;'>{summary}</p>
        </div>
        """
    
    # Topics
    topics = study_data.get('topics', [])
    for topic in topics:
        importance = topic.get('importance', 'medium')
        color_map = {
            'high': '#ff4444',
            'medium': '#ffa500',
            'low': '#4CAF50'
        }
        color = color_map.get(importance, '#666')
        
        stats = topic.get('stats', {})
        accuracy = (stats.get('correct', 0) / stats.get('total', 1) * 100) if stats.get('total', 1) > 0 else 0
        
        html += f"""
        <div style='border: 2px solid {color}; border-radius: 10px; 
                    padding: 20px; margin-bottom: 20px; background: white;'>
            <h3 style='color: {color}; margin-top: 0;'>
                📚 {topic['topic']}
                <span style='font-size: 14px; font-weight: normal;'>
                    ({stats.get('correct', 0)}/{stats.get('total', 0)} đúng - {accuracy:.0f}%)
                </span>
            </h3>
        """
        
        # Key Concepts
        concepts = topic.get('key_concepts', [])
        if concepts:
            html += "<h4>💡 Kiến thức cốt lõi:</h4><ul>"
            for concept in concepts:
                html += f"<li style='margin-bottom: 10px;'>{concept}</li>"
            html += "</ul>"
        
        # Common Mistakes
        mistakes = topic.get('common_mistakes', [])
        if mistakes:
            html += "<h4>⚠️ Lỗi thường gặp:</h4><ul>"
            for mistake in mistakes:
                html += f"<li style='margin-bottom: 10px; color: #d32f2f;'>{mistake}</li>"
            html += "</ul>"
        
        # Study Tips
        tips = topic.get('study_tips', [])
        if tips:
            html += "<h4>✨ Mẹo học tập:</h4><ul>"
            for tip in tips:
                html += f"<li style='margin-bottom: 10px; color: #2e7d32;'>{tip}</li>"
            html += "</ul>"
        
        # Practice Approach
        approach = topic.get('practice_approach', '')
        if approach:
            html += f"""
            <div style='background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 10px;'>
                <h4 style='margin-top: 0;'>🎯 Cách tiếp cận:</h4>
                <p style='margin: 0; line-height: 1.6;'>{approach}</p>
            </div>
            """
        
        # Formulas or Rules (NEW)
        formulas = topic.get('formulas_or_rules', [])
        if formulas:
            html += "<h4>📐 Công thức/Quy tắc:</h4><ul>"
            for formula in formulas:
                html += f"<li style='margin-bottom: 10px; font-family: monospace; background: #fff3cd; padding: 5px; border-radius: 3px;'>{formula}</li>"
            html += "</ul>"
        
        # Time Management Tip (NEW)
        time_tip = topic.get('time_management_tip', '')
        if time_tip:
            html += f"""
            <div style='background: #e3f2fd; padding: 10px; border-radius: 5px; margin-top: 10px; border-left: 4px solid #2196f3;'>
                <strong>⏱️ Quản lý thời gian:</strong> {time_tip}
            </div>
            """
        
        html += "</div>"
    
    # Recommended Focus
    focus = study_data.get('recommended_focus', [])
    if focus:
        html += """
        <div style='background: #fff3cd; border: 2px solid #ffc107; 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='margin-top: 0; color: #856404;'>🎯 Ưu tiên ôn tập:</h3>
            <ol style='margin: 0;'>
        """
        for item in focus:
            html += f"<li style='margin-bottom: 10px;'>{item}</li>"
        html += "</ol></div>"
    
    # Next Steps
    next_steps = study_data.get('next_steps', '')
    if next_steps:
        html += f"""
        <div style='background: #d1f2eb; border: 2px solid #1abc9c; 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='margin-top: 0; color: #117a65;'>📅 Kế hoạch tiếp theo:</h3>
            <p style='margin: 0; line-height: 1.8;'>{next_steps}</p>
        </div>
        """
    
    # Practice Resources (NEW)
    resources = study_data.get('practice_resources', [])
    if resources:
        html += """
        <div style='background: #fff8e1; border: 2px solid #ffc107; 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='margin-top: 0; color: #f57c00;'>📖 Nguồn tài liệu học tập:</h3>
            <ul style='margin: 0;'>
        """
        for resource in resources:
            html += f"<li style='margin-bottom: 10px;'>{resource}</li>"
        html += "</ul></div>"
    
    # Motivation Message (NEW)
    motivation = study_data.get('motivation_message', '')
    if motivation:
        html += f"""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='margin-top: 0;'>💪 Lời động viên</h3>
            <p style='margin: 0; font-size: 16px; line-height: 1.6; font-style: italic;'>{motivation}</p>
        </div>
        """
    
    html += "</div>"
    return html
