import google.genai as genai
import json
import os
import time

# --- CẤU HÌNH API ---
from dotenv import load_dotenv
load_dotenv()

# Try multiple sources for API key
try:
    import streamlit as st
    API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in .env file")

# Create client with google-genai
client = genai.Client(api_key=API_KEY)

def process_pdf_to_json(pdf_path, output_path):
    print(f"🚀 Đang tải file '{pdf_path}' lên Gemini...")
    
    # 1. Upload file PDF lên Gemini
    # google-genai v1.56+: set mime_type via config for PDF uploads
    sample_file = client.files.upload(
        file=open(pdf_path, 'rb'),
        config={
            "mime_type": "application/pdf"
        }
    )
    
    # Đợi file xử lý xong (thường mất 1-2 giây)
    while sample_file.state.name == "PROCESSING":
        print("... Đang xử lý file ...")
        time.sleep(2)
        sample_file = client.files.get(sample_file.name)

    if sample_file.state.name == "FAILED":
        print("❌ Lỗi khi xử lý file PDF.")
        return

    print("✅ Upload thành công! Đang trích xuất câu hỏi...")

    # 2. Tạo Prompt để trích xuất dữ liệu
    prompt = """
        Hãy đóng vai trò là một chuyên gia xử lý dữ liệu GMAT.
        Nhiệm vụ: Trích xuất TẤT CẢ câu hỏi trắc nghiệm từ file PDF.

        Yêu cầu định dạng Output (JSON List):
        [
            {
                "id": 1,
                "type": "math" | "data_sufficiency" | "logic" | "visual_logic", 
                "topic": "Chủ đề ngắn gọn (ví dụ: Average, Mixture, Pattern)",
                "content": "Nội dung câu hỏi đầy đủ",
                "options": ["A...", "B...", "C...", "D..."], 
                "data_statements": ["(1) ...", "(2) ..."] (CHỈ DÀNH CHO data_sufficiency, để null nếu không phải),
                "correct_answer": "Đáp án đúng nếu có trong file"
            }
        ]

        Quy tắc phân loại type:
        - "data_sufficiency": Nếu câu hỏi có 2 mệnh đề (1) và (2) và yêu cầu xác định dữ liệu có đủ không (Ví dụ câu 15, 18).
        - "visual_logic": Nếu câu hỏi dựa vào bảng biểu, hình vẽ quy luật (Ví dụ câu 5).
        - "math": Các bài toán đố thông thường.
        - "logic": Các câu hỏi chuỗi số, logic ngôn ngữ.
        """

    # 3. Sử dụng model Gemini 2.5 Pro
    
    # Thử gửi request với retry
    max_retries = 3
    retry_count = 0
    response = None
    
    while retry_count < max_retries:
        try:
            print(f"Đang gửi request đến Gemini... (Lần thử {retry_count + 1}/{max_retries})")
            
            # Call generate_content with google-genai Client API
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=[sample_file, prompt],
                config={
                    'response_mime_type': 'application/json'
                }
            )
            break  # Thành công thì thoát vòng lặp
        except Exception as e:
            retry_count += 1
            if "quota" in str(e).lower() or "429" in str(e):
                wait_time = 10 * retry_count  # Chờ 10s, 20s, 30s...
                print(f"⚠️ Vượt quota. Chờ {wait_time}s trước khi thử lại...")
                time.sleep(wait_time)
            else:
                print(f"❌ Lỗi: {e}")
                break
    
    if response is None:
        print("❌ Không thể kết nối đến Gemini sau nhiều lần thử.")
        return

    # 4. Lưu kết quả
    try:
        # Load string thành json object để đảm bảo tính hợp lệ
        data = json.loads(response.text)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 Thành công! Đã trích xuất được {len(data)} câu hỏi.")
        print(f"📂 Dữ liệu đã lưu tại: {output_path}")
        
    except json.JSONDecodeError:
        print("⚠️ Lỗi định dạng JSON trả về. Đang lưu raw text để kiểm tra...")
        with open("raw_output.txt", "w", encoding='utf-8') as f:
            f.write(response.text)

# --- CHẠY ---
if __name__ == "__main__":
    # Đảm bảo tên file PDF đúng với file bạn có trong thư mục
    pdf_filename = "123.pdf" 
    
    if os.path.exists(pdf_filename):
        process_pdf_to_json(pdf_filename, "seed_data.json")
    else:
        print(f"❌ Không tìm thấy file {pdf_filename}. Hãy kiểm tra lại tên file.")