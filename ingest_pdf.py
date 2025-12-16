import google.generativeai as genai
import json
import os
import time

# --- CẤU HÌNH API ---
import os
from dotenv import load_dotenv
load_dotenv()

# Try multiple sources for API key
try:
    import streamlit as st
    API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "AIzaSyDRkwgwveGS3sgyJIn77Qh3MW0wo79GfHg"))
except:
    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDRkwgwveGS3sgyJIn77Qh3MW0wo79GfHg") 
genai.configure(api_key=API_KEY)

def process_pdf_to_json(pdf_path, output_path):
    print(f"🚀 Đang tải file '{pdf_path}' lên Gemini...")
    
    # 1. Upload file PDF lên Gemini
    sample_file = genai.upload_file(path=pdf_path, display_name="GMAT Exam Data")
    
    # Đợi file xử lý xong (thường mất 1-2 giây)
    while sample_file.state.name == "PROCESSING":
        print("... Đang xử lý file ...")
        time.sleep(2)
        sample_file = genai.get_file(sample_file.name)

    if sample_file.state.name == "FAILED":
        print("❌ Lỗi khi xử lý file PDF.")
        return

    print("✅ Upload thành công! Đang trích xuất câu hỏi...")

    # 2. Tạo Prompt để trích xuất dữ liệu
    # Chúng ta yêu cầu Gemini trả về JSON list
    prompt = """
    Hãy đóng vai trò là một chuyên gia xử lý dữ liệu.
    Nhiệm vụ: Đọc toàn bộ file PDF này và trích xuất TẤT CẢ các câu hỏi trắc nghiệm.
    
    Yêu cầu định dạng Output (JSON List):
    [
      {
        "id": 1,
        "type": "math" hoặc "general", (Câu 1-30 là math, 31-90 là general)
        "topic": "Chủ đề ngắn gọn của câu hỏi",
        "content": "Nội dung câu hỏi đầy đủ (không bao gồm các lựa chọn A,B,C,D)"
      },
      ...
    ]
    
    Lưu ý: 
    - Hãy cố gắng trích xuất càng nhiều câu hỏi càng tốt.
    - Chỉ trả về JSON thuần, không có markdown formatting (```json).
    """

    # 3. Gọi model Gemini 2.0 Flash (chuyên xử lý văn bản dài)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')   
    # Thử gửi request với retry
    max_retries = 3
    retry_count = 0
    response = None
    
    while retry_count < max_retries:
        try:
            print(f"Đang gửi request đến Gemini... (Lần thử {retry_count + 1}/{max_retries})")
            # Tăng max_output_tokens để đảm bảo không bị cắt giữa chừng vì file dài
            response = model.generate_content(
                [sample_file, prompt],
                generation_config={"response_mime_type": "application/json"}
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